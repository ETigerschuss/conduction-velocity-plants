"""Active vs passive propagation tests from two-channel near/far waveforms.

The question: is the propagating potential regenerated at each point (ACTIVE,
action-potential-like: non-decremental, constant velocity, shape preserved) or
does it spread electrotonically / decay hydraulically (PASSIVE / decremental:
amplitude falls with distance, wavefront disperses, "velocity" ill-defined)?

Three data-only discriminators (no new experiments needed):

  1. decrement vs distance  -> space constant lambda from ln(A_far/A_near) = -d/lambda
  2. velocity constancy      -> delay vs distance linearity; is v independent of d?
  3. passive-kernel fit      -> can far(t) be reproduced as a delayed, gained,
                                low-pass-smoothed copy of near(t)? A passive cable
                                REQUIRES gain<1 and extra smoothing (sigma>0);
                                active regeneration needs only a pure delay.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d
from scipy.stats import linregress

from .io import Recording
from .analysis import analyze_recording, _response_window
from .viz import processed_channels


def near_far_traces(rec: Recording, cutoff: float = 2.0, target_fs: float = 50.0):
    """Return (t, near, far, fs_eff, result) for the response window, near/far
    oriented by the analysis (near = leading electrode). Signals are slow
    (<2 Hz), so we decimate to target_fs for efficiency. None if invalid."""
    res = analyze_recording(rec, cutoff=cutoff)
    if not res.get("valid"):
        return None
    t, ch0, ch1 = processed_channels(rec, cutoff)
    chans = {0: ch0, 1: ch1}
    win = _response_window(rec)
    i0, i1 = int(win[0] * rec.fs), int(win[1] * rec.fs)
    near = chans[res["near_channel"]][i0:i1]
    far = chans[res["far_channel"]][i0:i1]
    step = max(1, int(round(rec.fs / target_fs)))   # already low-passed, safe to stride
    near, far = near[::step], far[::step]
    fs_eff = rec.fs / step
    tt = np.arange(len(near)) / fs_eff
    sign = np.sign(near[np.argmax(np.abs(near))]) or 1.0
    return tt, near * sign, far * sign, fs_eff, res


def fit_passive_kernel(near, far, fs, max_delay_s=15.0,
                       sigma_grid=None):
    """Best (gain, sigma, delay, r2) for far ≈ gain * smooth(near, sigma) shifted.

    sigma is the Gaussian SD (s) of extra low-pass smoothing the far trace needs
    beyond a pure delay. gain is the amplitude ratio. r2 is the fit quality.
    Passive cable -> sigma>0 and gain<1; active regeneration -> sigma≈0, gain≈1.
    """
    if sigma_grid is None:
        sigma_grid = np.linspace(0.0, 3.0, 31)   # seconds
    far = np.asarray(far, float)
    fden = np.sum((far - far.mean()) ** 2)
    if fden == 0:
        return dict(gain=np.nan, sigma_s=np.nan, delay_s=np.nan, r2=np.nan)
    n = len(near)
    max_lag = int(max_delay_s * fs)
    best = dict(r2=-np.inf)
    for sigma in sigma_grid:
        sm = gaussian_filter1d(near, max(sigma * fs, 1e-6)) if sigma > 0 else np.asarray(near, float)
        # best delay by cross-correlation (far vs smoothed near), lags 0..max_lag
        a = sm - sm.mean(); b = far - far.mean()
        xc = np.correlate(b, a, mode="full")
        lags = np.arange(-n + 1, n)
        msk = (lags >= 0) & (lags <= max_lag)
        if not msk.any():
            continue
        lag = lags[msk][np.argmax(xc[msk])]
        shifted = np.zeros_like(sm)
        if lag < n:
            shifted[lag:] = sm[:n - lag]
        # least-squares gain
        denom = np.sum(shifted * shifted)
        if denom == 0:
            continue
        gain = float(np.sum(far * shifted) / denom)
        resid = far - gain * shifted
        r2 = 1.0 - np.sum(resid ** 2) / fden
        if r2 > best["r2"]:
            best = dict(gain=gain, sigma_s=float(sigma), delay_s=lag / fs, r2=float(r2))
    return best


def kernel_table(recs, cutoff: float = 2.0) -> pd.DataFrame:
    """Passive-kernel fit for every valid recording."""
    rows = []
    for rec in recs:
        nf = near_far_traces(rec, cutoff)
        if nf is None:
            continue
        t, near, far, fs_eff, res = nf
        k = fit_passive_kernel(near, far, fs_eff)
        # normalise dispersion by the near half-width for a scale-free measure
        rows.append(dict(
            species=rec.species, recording=rec.name, distance_mm=res.get("distance_mm"),
            gain=k["gain"], sigma_s=k["sigma_s"], kernel_delay_s=k["delay_s"], kernel_r2=k["r2"],
            attenuation=res.get("attenuation_far_near"), broadening=res.get("broadening_far_near"),
            cv=res.get("cv_xcorr_mm_s"),
        ))
    return pd.DataFrame(rows)


def decrement_fit(df: pd.DataFrame, species=None):
    """Fit ln(A_far/A_near) = -d/lambda across recordings (pooled or per species).

    Returns dict with lambda_mm (space constant), slope, r, p, n. A finite,
    significantly-negative slope => decremental (passive-like). Slope ~0 =>
    non-decremental (active-like), lambda -> inf.
    """
    v = df[(df["valid"] == True)].copy()  # noqa: E712
    if species:
        v = v[v["species"] == species]
    v = v[(v["attenuation_far_near"] > 0) & v["distance_mm"].notna()]
    if len(v) < 4:
        return None
    d = v["distance_mm"].to_numpy()
    y = np.log(v["attenuation_far_near"].to_numpy())
    lr = linregress(d, y)
    lam = -1.0 / lr.slope if lr.slope < 0 else np.inf
    return dict(species=species or "ALL", n=len(v), slope=float(lr.slope),
                lambda_mm=float(lam), r=float(lr.rvalue), p=float(lr.pvalue))


def delay_distance_exponent(df: pd.DataFrame):
    """Fit log(delay) = log k + b*log(distance). b≈1 => ballistic/constant-velocity
    (active-like); b≈2 => diffusive (passive/hydraulic-like)."""
    v = df[(df["valid"] == True)].copy()  # noqa: E712
    v = v[v["distance_mm"].notna() & (v["xcorr_delay_s"] > 0.05)]
    if len(v) < 6:
        return None
    lr = linregress(np.log(v["distance_mm"]), np.log(v["xcorr_delay_s"]))
    return dict(n=len(v), exponent_b=float(lr.slope), ci95=float(1.96 * lr.stderr),
                r=float(lr.rvalue), p=float(lr.pvalue))


def peak_onset_asymmetry(df: pd.DataFrame):
    """peak_delay - onset_delay per recording. ~0 = rigid translation (active);
    >0 = peak lags onset = dispersion (passive). Returns per-species medians +
    a pooled Wilcoxon vs 0."""
    from scipy.stats import wilcoxon
    v = df[df["valid"] == True].dropna(subset=["peak_delay_s", "onset_delay_s"]).copy()  # noqa: E712
    v["asym"] = v["peak_delay_s"] - v["onset_delay_s"]
    per = v.groupby("species")["asym"].median().sort_values()
    w = wilcoxon(v["asym"])
    return dict(pooled_median=float(v["asym"].median()), pooled_p=float(w.pvalue),
                n=len(v), per_species=per)


def amplitude_coupling(df: pd.DataFrame):
    """All-or-none proxy: per-species Spearman of near amplitude vs CV and vs
    attenuation. Active (all-or-none) => amplitude decoupled (~0). Confounded by
    electrode-contact amplitude scatter — suggestive only."""
    from scipy.stats import spearmanr
    v = df[df["valid"] == True]  # noqa: E712
    rows = []
    for sp, g in v.groupby("species"):
        a = g.dropna(subset=["near_peak_amp", "cv_xcorr_mm_s"])
        b = g.dropna(subset=["near_peak_amp", "attenuation_far_near"])
        r_cv = spearmanr(a["near_peak_amp"].abs(), a["cv_xcorr_mm_s"])[0] if len(a) >= 5 else np.nan
        r_at = spearmanr(b["near_peak_amp"].abs(), b["attenuation_far_near"])[0] if len(b) >= 5 else np.nan
        rows.append(dict(species=sp, n=len(g), amp_cv_rho=r_cv, amp_atten_rho=r_at))
    return pd.DataFrame(rows)


def velocity_fit(df: pd.DataFrame, species=None):
    """Fit delay = d / v (i.e. delay vs distance). Constant velocity (active)
    predicts a linear delay-distance relation; report slope (1/v), r, intercept."""
    v = df[(df["valid"] == True)].copy()  # noqa: E712
    if species:
        v = v[v["species"] == species]
    v = v[v["distance_mm"].notna() & v["xcorr_delay_s"].notna()]
    if len(v) < 4:
        return None
    d = v["distance_mm"].to_numpy()
    delay = v["xcorr_delay_s"].to_numpy()
    lr = linregress(d, delay)
    vel = 1.0 / lr.slope if lr.slope > 0 else np.nan
    return dict(species=species or "ALL", n=len(v), slope_s_per_mm=float(lr.slope),
                velocity_mm_s=float(vel), intercept_s=float(lr.intercept),
                r=float(lr.rvalue), p=float(lr.pvalue))
