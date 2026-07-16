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
from scipy.signal import correlate

from .preprocessing import preprocess_channel
from .io import Recording

# ---- tunable defaults ------------------------------------------------------
CUTOFF_HZ = 2.0          # low-pass for detection / metrics
BASELINE_S = 3.0         # pre-stimulus seconds used for baseline & noise
MIN_DELAY_S = 0.2        # below this the two peaks are effectively synchronous
MAX_DELAY_S = 20.0       # physiological ceiling for the lag search
MIN_XCORR = 0.4          # normalised cross-correlation below this = unreliable
MIN_SNR = 3.0            # peak amplitude / baseline noise below this = weak


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
