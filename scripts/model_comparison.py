"""Active vs passive model fit, done carefully, for every recording.

For each recording we predict the FAR trace from the NEAR trace with two models,
each optimised to its best parameters, under two amplitude conventions:

  ACTIVE  (regenerative)  far ≈ g · near(t − τ)                 [shape preserved]
  PASSIVE (cable)         far ≈ g · [Gaussian(σ) * near](t − τ)  [+ dispersion]

  * NORMALISED: each channel scaled to unit peak → tests waveform SHAPE only
    (removes electrode-gain / gel / wire-length amplitude differences).
  * RAW: measured (light-filtered, baseline-subtracted) amplitudes → the gain g
    also has to reproduce the amplitude drop.

Care taken on the three things that were wrong before:
  1. Correct data: a LIGHT low-pass (15 Hz) that PRESERVES the fast action
     potentials (the 2 Hz pipeline filter mis-orders the sharp Venus AP).
  2. Correct near/far: the leader is taken from the cross-correlation of the
     light-filtered, common-mode-reduced channels (robust for fast and slow).
  3. Best parameters: τ from full cross-correlation (all lags at once), g in
     closed form, σ over a fine grid, each refined at the optimum.

The ACTIVE model is the PASSIVE model at σ = 0 (nested), so R²_passive ≥ R²_active
by construction; the *gap* is how much dispersion is needed — ~0 = shape-preserving
(active-like), large = dispersive (passive-like). We also report the BIC-preferred
model (which penalises the extra σ parameter) for a genuine per-recording verdict.
"""
from __future__ import annotations

import os
import sys
import glob

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, correlate
from scipy.ndimage import gaussian_filter1d

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cvplants.io import iter_dataset, SPECIES_FAMILY, FAMILY_COLORS   # noqa: E402
from cvplants.analysis import _response_window                        # noqa: E402
from cvplants.preprocessing import baseline_subtract                  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "results", "figures")
SIGMAS = np.concatenate([[0.0], np.linspace(0.05, 4.0, 60)])   # seconds
MAXLAG_S = 8.0
TARGET_FS = 120.0


def _band(x, fs, lo, hi):
    ny = 0.5 * fs
    b, a = butter(2, [lo / ny, min(hi / ny, 0.99)], btype="band")
    return filtfilt(b, a, x)


def load_pair(rec, lo=0.15, hi=15.0):
    """Light band-passed, decimated near/far pair (near = xcorr leader)."""
    fs = rec.fs
    stim = rec.stim_start if rec.stim_start is not None else 1.0
    bl = (max(0.0, stim - 3), stim)
    c0 = _band(baseline_subtract(rec.data[:, 0], fs, bl), fs, lo, hi)
    c1 = _band(baseline_subtract(rec.data[:, 1], fs, bl), fs, lo, hi)
    win = _response_window(rec)
    i0, i1 = int(win[0] * fs), int(win[1] * fs)
    step = max(1, int(round(fs / TARGET_FS)))
    a, b = c0[i0:i1:step], c1[i0:i1:step]
    fse = fs / step
    if len(a) < int(2 * fse):
        return None
    # leader = channel that the other lags (positive xcorr lag of b vs a => a leads)
    aa, bb = a - a.mean(), b - b.mean()
    den = np.sqrt(np.sum(aa * aa) * np.sum(bb * bb))
    if den == 0:
        return None
    xc = correlate(bb, aa, mode="full") / den
    lags = np.arange(-len(a) + 1, len(a)) / fse
    m = np.abs(lags) <= MAXLAG_S
    lag = lags[m][np.argmax(xc[m])]
    near, far = (a, b) if lag >= 0 else (b, a)   # near leads
    return near, far, fse


def _shift(x, k):
    y = np.zeros_like(x)
    if k >= 0:
        if k < len(x):
            y[k:] = x[:len(x) - k]
    elif -k < len(x):
        y[:len(x) + k] = x[-k:]
    return y


def _fit_delay_gain(pred, far, fse, free_gain=True, maxlag=MAXLAG_S):
    """Best far ≈ g · pred(t − τ). free_gain=True: g by least squares (waveform /
    shape fit, scale-invariant). free_gain=False: g fixed = 1 (the model must also
    reproduce the measured amplitude, e.g. a regenerative AP predicts no decrement)."""
    f = far
    sst = np.sum((f - f.mean()) ** 2)
    if sst == 0:
        return dict(r2=-np.inf, g=np.nan, tau=0.0)
    p = pred - pred.mean(); fc = f - f.mean()
    den = np.sqrt(np.sum(p * p) * np.sum(fc * fc))
    lags = np.arange(-len(pred) + 1, len(pred))
    m = np.abs(lags / fse) <= maxlag
    if den > 0:
        xc = correlate(fc, p, mode="full") / den
        cand = lags[m][np.argsort(xc[m])[::-1][:7]]
    else:
        cand = lags[m][::max(1, len(lags[m]) // 20)]
    best = dict(r2=-np.inf)
    for k in cand:
        s = _shift(pred, int(k))
        if free_gain:
            d = np.dot(s, s)
            if d == 0:
                continue
            g = np.dot(far, s) / d
        else:
            g = 1.0
        r2 = 1.0 - np.sum((far - g * s) ** 2) / sst
        if r2 > best["r2"]:
            best = dict(r2=float(r2), g=float(g), tau=float(k / fse))
    return best


def fit_models(near, far, fse, free_gain):
    active = _fit_delay_gain(near, far, fse, free_gain=free_gain)
    passive = dict(r2=-np.inf)
    for sig in SIGMAS:
        pred = gaussian_filter1d(near, sig * fse) if sig > 0 else near
        r = _fit_delay_gain(pred, far, fse, free_gain=free_gain)
        if r["r2"] > passive["r2"]:
            passive = {**r, "sigma": float(sig)}
    return active, passive


def analyse():
    rows = []
    for rec in iter_dataset(os.path.join(ROOT, "data")):
        pr = load_pair(rec)
        if pr is None:
            continue
        near, far, fse = pr
        # 'norm' = waveform fit (gain free, scale-invariant → normalise for clarity)
        # 'raw'  = amplitude fit (gain fixed = 1 → model must reproduce the drop)
        for cond, free_gain in (("norm", True), ("raw", False)):
            if cond == "norm":
                nn = near / (np.max(np.abs(near)) or 1.0)
                ff = far / (np.max(np.abs(far)) or 1.0)
            else:
                nn, ff = near, far
            a, p = fit_models(nn, ff, fse, free_gain)
            npar = len(ff)
            ka, kp = (2, 3) if free_gain else (1, 2)   # params: (τ[,g]) / (τ,σ[,g])

            def bic(r2, k):
                ssr = (1 - max(r2, -0.999)) * np.sum((ff - ff.mean()) ** 2)
                return npar * np.log(max(ssr, 1e-12) / npar) + k * np.log(npar)
            rows.append(dict(species=rec.species, recording=rec.name, norm=cond,
                             r2_active=a["r2"], r2_passive=p["r2"],
                             sigma=p.get("sigma", np.nan),
                             gain_active=a["g"], gain_passive=p["g"], tau=a["tau"],
                             bic_active=bic(a["r2"], ka), bic_passive=bic(p["r2"], kp)))
    df = pd.DataFrame(rows)
    df["passive_gap"] = df["r2_passive"] - df["r2_active"]
    df["winner"] = np.where(df["bic_active"] <= df["bic_passive"], "active", "passive")
    return df


def bars(df, out):
    order = (df[df.norm == "norm"].groupby("species")["passive_gap"].median()
             .sort_values().index.tolist())
    fig, axes = plt.subplots(2, 1, figsize=(13, 10), sharex=True)
    specs = [("norm", "WAVEFORM fit — gain free (shape only; the trustworthy comparison)", (0, 1.02), None),
             ("raw", "AMPLITUDE fit — gain fixed = 1 (must also reproduce the far amplitude)", (-2, 1.02), -2)]
    for ax, (norm, title, ylim, floor) in zip(axes, specs):
        sub = df[df.norm == norm]
        x = np.arange(len(order))
        for off, key, col, lab in [(-0.2, "r2_active", "#1f77b4", "active (delay [+ gain])"),
                                   (0.2, "r2_passive", "#d1495b", "passive (+ dispersion)")]:
            meds = [np.nanmedian(sub[sub.species == s][key]) for s in order]
            if floor is not None:
                meds = [max(v, floor) for v in meds]
            ax.bar(x + off, meds, 0.38, color=col, label=lab, zorder=1)
            for i, s in enumerate(order):
                vals = sub[sub.species == s][key].values
                yv = np.clip(vals, floor, None) if floor is not None else vals
                ax.scatter(np.full(len(vals), i + off) + np.random.normal(0, 0.03, len(vals)),
                           yv, s=10, color="#222", alpha=0.5, zorder=3)
        ax.set_ylabel("prediction R²"); ax.set_title(title, fontsize=11)
        ax.set_ylim(*ylim); ax.axhline(0, color="k", lw=0.6)
        ax.grid(axis="y", ls="--", alpha=0.3); ax.legend(fontsize=8, loc="lower right")
        if floor is not None:
            ax.text(0.01, 0.03, "active R² falls far below the floor for most species: a non-decremental "
                    "(g=1) model cannot hold — but the amplitude drop is confounded by electrode coupling, "
                    "so amplitude is not a reliable active/passive discriminator.",
                    transform=ax.transAxes, fontsize=7.5, color="#7a2020", va="bottom")
    axes[1].set_xticks(range(len(order)))
    axes[1].set_xticklabels(order, rotation=40, ha="right", fontsize=8)
    fig.suptitle("Active (delay+gain) vs passive (delay+gain+dispersion) fit of far from near, per species\n"
                 "(each recording a dot, bar = median). Top: waveform shape only. Bottom: must also match the "
                 "measured amplitude.\nPassive ≥ active by construction (nested); a SMALL gap = shape/amplitude "
                 "already explained without dispersion (active-like), a LARGE gap = dispersion needed (passive-like).",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.96)); fig.savefig(out, dpi=120); plt.close(fig)


def examples(out, species_list):
    """Representative recordings: near, far, and the best active & passive
    (waveform, gain-free) predictions — with the corrected near/far."""
    recs = {r.name: r for r in iter_dataset(os.path.join(ROOT, "data"))
            if r.species in species_list}
    picks = {}
    for sp in species_list:
        cand = []
        for r in recs.values():
            if r.species != sp:
                continue
            pr = load_pair(r)
            if pr is None:
                continue
            near, far, fse = pr
            a, p = fit_models(near, far, fse, free_gain=True)
            cand.append((a["r2"], r.name, near, far, fse, a, p))
        if cand:
            cand.sort()
            picks[sp] = cand[len(cand) // 2]        # median-R² recording
    fig, axes = plt.subplots(len(picks), 1, figsize=(11, 2.6 * len(picks)))
    axes = np.atleast_1d(axes)
    for ax, (sp, (r2, name, near, far, fse, a, p)) in zip(axes, picks.items()):
        t = np.arange(len(near)) / fse
        pa = a["g"] * _shift(near, int(round(a["tau"] * fse)))
        sm = gaussian_filter1d(near, p["sigma"] * fse) if p["sigma"] > 0 else near
        pp = p["g"] * _shift(sm, int(round(p["tau"] * fse)))
        ax.plot(t, near, color="#666", lw=1.0, label="near")
        ax.plot(t, far, color="#d62728", lw=1.8, label="far (real)")
        ax.plot(t, pa, color="#1f77b4", lw=1.3, ls="--", label=f"active fit R²={a['r2']:.2f}")
        ax.plot(t, pp, color="#2a9d8f", lw=1.2, ls=":", label=f"passive fit R²={p['r2']:.2f} (σ={p['sigma']:.2f}s)")
        ax.set_title(f"{sp} — {name}", fontsize=9); ax.legend(fontsize=7, loc="upper right")
        ax.set_ylabel("amp")
    axes[-1].set_xlabel("time (s)")
    fig.suptitle("Active vs passive waveform fit of the far trace (near/far corrected; light 15 Hz filter)", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.98)); fig.savefig(out, dpi=120); plt.close(fig)


def main():
    np.random.seed(0)
    df = analyse()
    df.to_csv(os.path.join(ROOT, "results", "model_comparison.csv"), index=False)
    g = (df.groupby(["species", "norm"])[["r2_active", "r2_passive", "passive_gap", "sigma"]]
         .median().round(2))
    print(g.to_string())
    print("\nBIC-preferred model (raw): ",
          df[df.norm == "raw"].groupby("species")["winner"].agg(lambda s: s.value_counts().to_dict()).to_dict())
    bars(df, os.path.join(FIG, "model_comparison_bars.png"))
    examples(os.path.join(FIG, "model_fit_examples.png"),
             ["Venus Flytrap", "Sensitive Mimosa", "Marijuana", "Mint", "Ornamental Chile"])
    print("wrote model_comparison_bars.png, model_fit_examples.png, model_comparison.csv")


if __name__ == "__main__":
    main()
