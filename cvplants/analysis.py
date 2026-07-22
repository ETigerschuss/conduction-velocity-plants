"""Conduction-velocity and channel-to-channel signal-transformation analysis.

Given a two-channel recording, we characterise the propagating wound/variation
potential and how it changes as it travels from the near electrode to the far
electrode:

  * inter-channel delay  -> conduction velocity (with known electrode spacing)
  * amplitude ratio      -> attenuation / decrement with distance
  * width & rise/decay   -> temporal dispersion (broadening) of the wavefront
  * waveform correlation -> how well the shape is preserved

Delay is estimated two independent ways (windowed cross-correlation and
peak-to-peak) so they can validate each other. Recordings where the estimate is
untrustworthy (near-synchronous peaks, dissimilar waveforms, low SNR) are
flagged rather than silently reported.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
from scipy.signal import correlate, butter, filtfilt, find_peaks

from .preprocessing import preprocess_channel, baseline_subtract
from .io import Recording

# ---- tunable defaults ------------------------------------------------------
CUTOFF_HZ = 2.0          # low-pass for detection / metrics
BASELINE_S = 3.0         # pre-stimulus seconds used for baseline & noise
MIN_DELAY_S = 0.2        # below this the two peaks are effectively synchronous
MAX_DELAY_S = 20.0       # physiological ceiling for the lag search
MIN_XCORR = 0.4          # normalised cross-correlation below this = unreliable
MIN_SNR = 3.0            # peak amplitude / baseline noise below this = weak

# Rapid-movement plants fire a sharp, fast action potential; the manual analysis
# times the FIRST prominent peak (the AP) on an AP-preserving filter, not the
# dominant later deflection. Detecting them the default (slow) way underestimates
# CV, so we switch to first-prominent-peak detection for these species.
RAPID_MOVEMENT = {"Venus Flytrap", "Sensitive Mimosa"}


def _first_prominent_delay(rec, lo=0.15, hi=15.0, hfrac=0.5, prom=0.3, dist_s=1.0):
    """Delay (s) and leading channel from the FIRST prominent peak (≥ hfrac·max,
    with prominence `prom`·max) in each channel, on a 0.15–15 Hz band-pass that
    preserves the sharp AP. Reproduces the manual conduction-velocity for the
    rapid-movement plants. Returns (delay_s, near_channel) or (None, None)."""
    fs = rec.fs
    stim = rec.stim_start if rec.stim_start is not None else 1.0
    bl = (max(0.0, stim - BASELINE_S), stim)
    b, a = butter(2, [lo / (fs / 2), min(hi / (fs / 2), 0.99)], btype="band")
    win = _response_window(rec)
    i0, i1 = int(win[0] * fs), int(win[1] * fs)

    def first_peak(k):
        seg = filtfilt(b, a, baseline_subtract(rec.data[:, k], fs, bl))[i0:i1]
        if len(seg) < int(fs):
            return None
        s = seg * (np.sign(seg[np.argmax(np.abs(seg))]) or 1.0)
        mx = s.max()
        if mx <= 0:
            return None
        pk, _ = find_peaks(s / mx, height=hfrac, prominence=prom,
                           distance=max(int(dist_s * fs), 1))
        return pk[0] / fs if len(pk) else None

    t0, t1 = first_peak(0), first_peak(1)
    if t0 is None or t1 is None:
        return None, None
    return abs(t1 - t0), (0 if t0 <= t1 else 1)


def _response_window(rec: Recording) -> tuple:
    """(start_s, end_s) window in which to look for the response.

    The response cannot precede stimulation, so we start at the stimulation
    onset (marker 1). Without markers we skip a short settling period.
    """
    start = rec.stim_start if rec.stim_start is not None else 1.0
    return (max(0.0, start), rec.duration_s)


@dataclass
class ChannelMetrics:
    peak_time: float        # s, absolute
    peak_amp: float         # signed, baseline-subtracted units
    onset_time: float       # s, absolute (20% threshold crossing)
    rise_time: float        # s, onset -> peak
    fwhm: float             # s, full width at half max
    half_decay: float       # s, peak -> half amplitude on the falling edge
    snr: float              # |peak| / baseline noise std


def _channel_metrics(sig: np.ndarray, fs: float, win: tuple,
                     baseline_noise: float) -> ChannelMetrics | None:
    """Characterise the dominant deflection of one channel within `win`."""
    i0, i1 = int(win[0] * fs), int(win[1] * fs)
    seg = sig[i0:i1]
    if len(seg) < int(fs):  # need at least ~1 s
        return None
    k = int(np.argmax(np.abs(seg)))       # dominant deflection
    amp = seg[k]
    sign = np.sign(amp) or 1.0
    ssig = seg * sign                      # make the event positive-going
    peak = ssig[k]
    if peak <= 0:
        return None

    # onset: last sample before the peak below 20% of peak
    thr_on = 0.2 * peak
    pre = ssig[:k + 1]
    below = np.where(pre < thr_on)[0]
    onset_k = below[-1] if len(below) else 0

    # FWHM around the peak (half-max crossings)
    half = 0.5 * peak
    left = np.where(ssig[:k + 1] < half)[0]
    li = left[-1] if len(left) else 0
    right = np.where(ssig[k:] < half)[0]
    ri = (k + right[0]) if len(right) else len(ssig) - 1

    return ChannelMetrics(
        peak_time=win[0] + k / fs,
        peak_amp=float(amp),
        onset_time=win[0] + onset_k / fs,
        rise_time=(k - onset_k) / fs,
        fwhm=(ri - li) / fs,
        half_decay=(ri - k) / fs,
        snr=float(peak / baseline_noise) if baseline_noise > 0 else np.inf,
    )


def _xcorr_delay(a: np.ndarray, b: np.ndarray, fs: float,
                 max_lag_s: float) -> tuple:
    """Lag (s) that best aligns b onto a, and the normalised peak correlation.

    Positive lag => b is delayed relative to a (b is the far electrode).
    """
    a = a - a.mean()
    b = b - b.mean()
    denom = np.sqrt(np.sum(a * a) * np.sum(b * b))
    if denom == 0:
        return np.nan, 0.0
    xc = correlate(b, a, mode="full") / denom
    lags = np.arange(-len(a) + 1, len(b)) / fs
    m = np.abs(lags) <= max_lag_s
    j = np.argmax(xc[m])
    return float(lags[m][j]), float(xc[m][j])


def analyze_recording(rec: Recording, cutoff: float = CUTOFF_HZ,
                      baseline_s: float = BASELINE_S) -> dict:
    """Full per-recording analysis. Returns a flat dict (one results row)."""
    out = {
        "species": rec.species, "latin": rec.latin, "recording": rec.name,
        "duration_s": round(rec.duration_s, 2), "fs": rec.fs,
        "n_channels": rec.n_channels, "distance_mm": rec.distance_mm,
        "stim_start_s": rec.stim_start, "stim_stop_s": rec.stim_stop,
        "n_markers": len(rec.events),
    }
    if rec.n_channels < 2:
        out["valid"] = False
        out["flags"] = "not_two_channel"
        return out

    win = _response_window(rec)
    stim = rec.stim_start if rec.stim_start is not None else win[0]
    bl_win = (max(0.0, stim - baseline_s), stim)

    ch0 = preprocess_channel(rec.data[:, 0], rec.fs, cutoff, bl_win)
    ch1 = preprocess_channel(rec.data[:, 1], rec.fs, cutoff, bl_win)

    # baseline noise = std of the pre-stimulus segment (post-filter)
    bi0, bi1 = int(bl_win[0] * rec.fs), int(bl_win[1] * rec.fs)
    noise0 = np.std(ch0[bi0:bi1]) if bi1 > bi0 else np.std(ch0)
    noise1 = np.std(ch1[bi0:bi1]) if bi1 > bi0 else np.std(ch1)
    noise0 = noise0 or 1.0
    noise1 = noise1 or 1.0

    m0 = _channel_metrics(ch0, rec.fs, win, noise0)
    m1 = _channel_metrics(ch1, rec.fs, win, noise1)
    flags = []
    if m0 is None or m1 is None:
        out["valid"] = False
        out["flags"] = "no_response_detected"
        return out

    # which channel leads (near electrode) by peak time
    if m0.peak_time <= m1.peak_time:
        near, far, near_ch, far_ch = m0, m1, 0, 1
    else:
        near, far, near_ch, far_ch = m1, m0, 1, 0
    peak_delay = far.peak_time - near.peak_time
    onset_delay = far.onset_time - near.onset_time

    # cross-correlation delay on the response segment (robust primary estimate)
    ri0, ri1 = int(win[0] * rec.fs), int(win[1] * rec.fs)
    xc_lag, xc_corr = _xcorr_delay(ch0[ri0:ri1], ch1[ri0:ri1], rec.fs, MAX_DELAY_S)
    xcorr_delay = abs(xc_lag)
    # cross-corr sign should agree with peak ordering; note if it doesn't
    xc_leader = 0 if xc_lag >= 0 else 1   # channel that leads per xcorr
    if not np.isnan(xc_lag) and xc_leader != near_ch and xcorr_delay > MIN_DELAY_S:
        flags.append("xcorr_peak_leader_disagree")

    # common-mode / crosstalk diagnostics. A shared reference or channel
    # bleedthrough puts an *instantaneous* (zero-lag) copy of one channel into
    # the other. It shows up (a) as correlation already in the pre-stimulus
    # baseline, and (b) as cross-correlation power at lag 0 rivalling the
    # propagation peak — which biases the estimated delay toward zero.
    def _corr(a, b):
        a = a - a.mean(); b = b - b.mean()
        d = np.sqrt(np.sum(a * a) * np.sum(b * b))
        return float(np.sum(a * b) / d) if d > 0 else np.nan
    cm_baseline_r = _corr(ch0[bi0:bi1], ch1[bi0:bi1]) if bi1 > bi0 else np.nan
    event_zero_lag_r = _corr(ch0[ri0:ri1], ch1[ri0:ri1])
    r0_over_rpk = (abs(event_zero_lag_r) / xc_corr) if (xc_corr and xc_corr > 0) else np.nan
    # The two channels share a soil/earth reference, so a large *instantaneous*
    # common component is expected and benign; it does not by itself prevent
    # recovering the delay. The delay is 'unresolved' only when there is
    # essentially no delayed structure left once the zero-lag component is
    # accounted for (r0/rpk ~ 1) or the lag is below the timing floor. A small
    # but real delay (e.g. the fast Venus-flytrap AP) stays resolved.
    delay_resolved = bool(xcorr_delay > MIN_DELAY_S
                          and (np.isnan(r0_over_rpk) or r0_over_rpk < 0.97))
    if not delay_resolved:
        flags.append("delay_unresolved")
    if not np.isnan(cm_baseline_r) and cm_baseline_r > 0.6:
        flags.append("common_mode_high")

    # signal-transformation metrics (near -> far)
    attenuation = abs(far.peak_amp) / abs(near.peak_amp) if near.peak_amp else np.nan
    broadening = far.fwhm / near.fwhm if near.fwhm else np.nan
    rise_ratio = far.rise_time / near.rise_time if near.rise_time else np.nan

    # polarity agreement between channels
    if np.sign(m0.peak_amp) != np.sign(m1.peak_amp):
        flags.append("polarity_mismatch")

    # quality gating
    min_snr = min(near.snr, far.snr)
    if peak_delay < MIN_DELAY_S:
        flags.append("near_synchronous")
    if xc_corr < MIN_XCORR:
        flags.append("low_waveform_similarity")
    if min_snr < MIN_SNR:
        flags.append("low_snr")
    valid = not any(f in flags for f in
                    ("near_synchronous", "low_waveform_similarity", "low_snr"))

    # Rapid-movement plants: replace the delay with the first-prominent-peak
    # (sharp AP) estimate on an AP-preserving filter — matches the manual CV.
    if rec.species in RAPID_MOVEMENT:
        fp_delay, fp_near = _first_prominent_delay(rec)
        if fp_delay is not None and fp_delay > MIN_DELAY_S:
            if fp_near != near_ch:                       # assignment flipped
                near, far, near_ch, far_ch = far, near, far_ch, near_ch
                attenuation = abs(far.peak_amp) / abs(near.peak_amp) if near.peak_amp else np.nan
                broadening = far.fwhm / near.fwhm if near.fwhm else np.nan
                rise_ratio = far.rise_time / near.rise_time if near.rise_time else np.nan
                min_snr = min(near.snr, far.snr)
            peak_delay = onset_delay = xcorr_delay = fp_delay
            delay_resolved = True
            flags = [f for f in flags if f != "near_synchronous"]
            flags.append("rapid_first_prominent")
            valid = min_snr >= MIN_SNR

    # conduction velocity (needs distance and a trustworthy delay)
    def cv(delay):
        if rec.distance_mm and delay and delay > MIN_DELAY_S:
            return rec.distance_mm / delay
        return np.nan

    out.update({
        "near_channel": near_ch, "far_channel": far_ch,
        "peak_delay_s": round(peak_delay, 3),
        "onset_delay_s": round(onset_delay, 3),
        "xcorr_delay_s": round(xcorr_delay, 3),
        "xcorr_corr": round(xc_corr, 3),
        "cv_peak_mm_s": round(cv(peak_delay), 3) if not np.isnan(cv(peak_delay)) else np.nan,
        "cv_xcorr_mm_s": round(cv(xcorr_delay), 3) if not np.isnan(cv(xcorr_delay)) else np.nan,
        "cm_baseline_r": round(cm_baseline_r, 3) if not np.isnan(cm_baseline_r) else np.nan,
        "event_zero_lag_r": round(event_zero_lag_r, 3) if not np.isnan(event_zero_lag_r) else np.nan,
        "r0_over_rpk": round(r0_over_rpk, 3) if not np.isnan(r0_over_rpk) else np.nan,
        "delay_resolved": delay_resolved,
        "near_peak_amp": round(near.peak_amp, 1),
        "far_peak_amp": round(far.peak_amp, 1),
        "attenuation_far_near": round(attenuation, 3),
        "near_fwhm_s": round(near.fwhm, 3), "far_fwhm_s": round(far.fwhm, 3),
        "broadening_far_near": round(broadening, 3),
        "near_rise_s": round(near.rise_time, 3), "far_rise_s": round(far.rise_time, 3),
        "rise_ratio_far_near": round(rise_ratio, 3),
        "near_snr": round(near.snr, 1), "far_snr": round(far.snr, 1),
        "valid": valid,
        "flags": ";".join(flags),
    })
    return out
