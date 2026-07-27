"""The fast<->slow WAVEFORM axis: split recordings by dominant-event duration and
ask whether the two groups propagate differently.

This is a DESCRIPTIVE waveform axis, NOT an AP/VP classification. Four tests in
the report (Section 4) show the duration rule does not identify action potentials:
  * the per-species ordering is biologically inverted (mints/chiles outrank Venus
    and Mimosa, the only species with established APs);
  * under a flame (a WOUNDING stimulus, which evokes variation potentials) it
    still labels 113/166 = 68% of analysed recordings "short/AP-like" — the
    inverse of the biological prediction;
  * the ~0.2 Hz hardware high-pass plus the 0.15 Hz analysis filter differentiate
    away the sustained DC plateau that DEFINES a variation potential, pushing true
    VPs below the 2 s threshold;
  * the duration distribution is unimodal on a log scale (Sarle 0.31), and within
    a movement class the label does not change conduction velocity (p ~ 0.9-1.0).
Labels below are therefore "short (< 2 s)" / "long (> 2 s)", never AP/VP.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cvplants.io import SPECIES_FAMILY, FAMILY_COLORS   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "results", "figures")
AP_C, VP_C = "#2a9d2a", "#b060c0"


def load():
    pt = pd.read_csv(os.path.join(ROOT, "results", "potential_types.csv"))[
        ["species", "recording", "duration_s", "potential_type"]]
    sim = pd.read_csv(os.path.join(ROOT, "results", "model_comparison.csv"))
    sim = sim[sim["norm"] == "norm"][["species", "recording", "sigma"]]
    rec = pd.read_csv(os.path.join(ROOT, "results", "recordings.csv"))[
        ["species", "recording", "cv_xcorr_mm_s", "xcorr_corr", "peak_delay_s", "valid"]]
    m = pt.merge(sim, on=["species", "recording"], how="left").merge(rec, on=["species", "recording"], how="left")
    return m[m["valid"] == True]  # noqa: E712


def figure(m, out):
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))

    # (A) per-species AP-like fraction (stacked) — no species is purely one type
    ax = axes[0]
    frac = m.groupby("species")["potential_type"].apply(lambda s: (s == "AP-like").mean()).sort_values()
    n = m.groupby("species")["recording"].count()
    y = np.arange(len(frac))
    ax.barh(y, frac.values, color=AP_C, label="short (< 2 s)")
    ax.barh(y, 1 - frac.values, left=frac.values, color=VP_C, label="long (> 2 s)")
    ax.set_yticks(y); ax.set_yticklabels([f"{s} (n={n[s]})" for s in frac.index], fontsize=7)
    ax.set_xlabel("fraction of recordings"); ax.set_title("Fraction of SHORT-duration recordings per species\n(ordering does NOT track the known-AP species)", fontsize=10)
    ax.legend(fontsize=8, loc="lower right")

    # (B) the active↔passive character as a continuum in duration
    ax = axes[1]
    s = m.dropna(subset=["duration_s", "sigma"])
    for ty, c, lab in [("AP-like", AP_C, "short (< 2 s)"), ("VP-like", VP_C, "long (> 2 s)")]:
        d = s[s.potential_type == ty]
        ax.scatter(d["duration_s"], d["sigma"], s=16, color=c, alpha=0.6, edgecolor="none", label=lab)
    r, p = spearmanr(s["duration_s"], s["sigma"])
    ax.axvline(2.0, color="#888", ls="--", lw=1)
    ax.set_xscale("log"); ax.set_xlabel("dominant-event duration (s)")
    ax.set_ylabel("passive dispersion σ (s)")
    ax.set_title(f"Longer signals are more dispersive\nSpearman ρ={r:.2f}, p={p:.1e} — a continuum, not a switch", fontsize=10)
    ax.legend(fontsize=8)

    # (C) AP vs VP population, key metrics (z-scored so they share an axis)
    ax = axes[2]
    cols = {"cv_xcorr_mm_s": "CV", "sigma": "dispersion", "xcorr_corr": "waveform fidelity", "peak_delay_s": "peak-onset lag"}
    labels, ap_meds, vp_meds = [], [], []
    for col, lab in cols.items():
        z = (m[col] - m[col].mean()) / m[col].std()
        ap_meds.append(np.nanmedian(z[m.potential_type == "AP-like"]))
        vp_meds.append(np.nanmedian(z[m.potential_type == "VP-like"]))
        labels.append(lab)
    x = np.arange(len(labels))
    ax.bar(x - 0.2, ap_meds, 0.38, color=AP_C, label="short (< 2 s)")
    ax.bar(x + 0.2, vp_meds, 0.38, color=VP_C, label="long (> 2 s)")
    ax.axhline(0, color="k", lw=0.6)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("median (z-score)")
    ax.set_title("Short: faster, less dispersion, higher fidelity;\nlong the opposite (a waveform trend, not a mechanism)", fontsize=10)
    ax.legend(fontsize=8)

    fig.suptitle("The fast↔slow WAVEFORM axis (duration of the dominant deflection) — "
                 "a descriptive split, NOT an AP/VP classification (see Section 4)", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig(out, dpi=120); plt.close(fig)


def main():
    m = load()
    print("AP-like fraction per species:")
    print(m.groupby("species")["potential_type"].apply(lambda s: (s == "AP-like").mean()).round(2).to_string())
    figure(m, os.path.join(FIG, "two_mechanisms.png"))
    print("\nwrote two_mechanisms.png")


if __name__ == "__main__":
    main()
