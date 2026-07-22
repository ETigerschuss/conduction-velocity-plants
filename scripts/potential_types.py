"""Classify each recording's potential type (fast AP vs slow VP) and show that the
active/passive model fit differs by type.

Mimosa pudica (and other plants) fire two kinds of electrical signal: a fast,
often biphasic ACTION POTENTIAL (non-damaging stimuli; ~1 s; propagates at
~2–3 cm/s) and a slow, long-lasting VARIATION POTENTIAL (wounding; tens–hundreds
of seconds; decremental) — see Volkov 2010, Plant Cell Environ; the Mimosa
mechanical-signalling review (PMC7284940); Fromm & Lautner 2007. A single peak
detector cannot serve both, and the two types should — and do — fit the active
vs passive models differently.

We classify each recording by the DURATION of its dominant deflection (time above
40% of peak, on an AP-preserving 0.15–15 Hz band-pass): AP-like if < 2 s, else
VP-like. We then relate the type to the fitted passive dispersion σ (how much
low-pass smoothing the far trace needs beyond a pure delay) and to CV.
"""
from __future__ import annotations

import os
import sys
import glob

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cvplants.io import load_recording, SPECIES_FAMILY, FAMILY_COLORS   # noqa: E402
from cvplants.preprocessing import baseline_subtract                    # noqa: E402
from cvplants.analysis import _response_window                          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "results", "figures")
DUR_THRESH = 2.0        # s; below = AP-like, above = VP-like


def _band(x, fs, lo=0.15, hi=15.0):
    b, a = butter(2, [lo / (fs / 2), min(hi / (fs / 2), 0.99)], btype="band")
    return filtfilt(b, a, x)


def event_duration(rec, frac=0.4, target_fs=200.0):
    fs = rec.fs
    stim = rec.stim_start if rec.stim_start is not None else 1.0
    bl = (max(0.0, stim - 3), stim)
    c = _band(baseline_subtract(rec.data[:, 0], fs, bl), fs)
    win = _response_window(rec)
    step = max(1, int(round(fs / target_fs)))
    seg = c[int(win[0] * fs):int(win[1] * fs):step]
    fse = fs / step
    if len(seg) < fse:
        return np.nan
    s = seg * (np.sign(seg[np.argmax(np.abs(seg))]) or 1.0)
    pk = int(np.argmax(s))
    if s[pk] <= 0:
        return np.nan
    thr = frac * s[pk]
    # span of the depolarised phase: first to last sample above threshold. A
    # sharp AP is brief; a slow VP holds the membrane depolarised for much longer.
    above = np.where(s >= thr)[0]
    return (above[-1] - above[0]) / fse if len(above) > 1 else np.nan


def build():
    rows = []
    for rec in (load_recording(f, os.path.basename(os.path.dirname(f)))
                for f in glob.glob(os.path.join(ROOT, "data", "*", "*.wav"))):
        rows.append(dict(species=rec.species, recording=rec.name,
                         duration_s=event_duration(rec)))
    d = pd.DataFrame(rows).dropna(subset=["duration_s"])
    d["potential_type"] = np.where(d["duration_s"] < DUR_THRESH, "AP-like", "VP-like")
    sim = pd.read_csv(os.path.join(ROOT, "results", "model_comparison.csv"))
    sim = sim[sim["norm"] == "norm"][["species", "recording", "sigma", "r2_active", "r2_passive", "passive_gap"]]
    rec = pd.read_csv(os.path.join(ROOT, "results", "recordings.csv"))[["species", "recording", "cv_xcorr_mm_s", "valid"]]
    d = d.merge(sim, on=["species", "recording"], how="left").merge(rec, on=["species", "recording"], how="left")
    d.to_csv(os.path.join(ROOT, "results", "potential_types.csv"), index=False)
    return d


def figure(d, out):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    ap = d[d.potential_type == "AP-like"]; vp = d[d.potential_type == "VP-like"]

    # (A) duration distribution
    ax = axes[0]
    bins = np.logspace(np.log10(0.05), np.log10(60), 30)
    ax.hist(d["duration_s"], bins=bins, color="#8aa", edgecolor="k", lw=0.3)
    ax.axvline(DUR_THRESH, color="#d62728", ls="--", label=f"{DUR_THRESH}s split")
    ax.set_xscale("log"); ax.set_xlabel("dominant-event duration (s)")
    ax.set_ylabel("recordings"); ax.set_title(f"Two populations\nAP-like {len(ap)}, VP-like {len(vp)}")
    ax.legend(fontsize=8)

    # (B) dispersion sigma by type (passive filtering needed)
    ax = axes[1]
    data = [ap["sigma"].dropna(), vp["sigma"].dropna()]
    ax.boxplot(data, labels=["AP-like", "VP-like"], showfliers=False, patch_artist=True,
               boxprops=dict(facecolor="#cfe3f5"), medianprops=dict(color="#d62728"))
    for i, g in enumerate(data, 1):
        ax.scatter(np.random.normal(i, 0.05, len(g)), g, s=12, color="#25507a", alpha=0.5)
    from scipy.stats import mannwhitneyu
    pval = mannwhitneyu(data[0], data[1]).pvalue
    ax.set_ylabel("passive dispersion σ needed (s)")
    ax.set_title(f"VP-like need more dispersion\n(passive-like)  p={pval:.1e}")

    # (C) CV by type
    ax = axes[2]
    cv_ap = ap["cv_xcorr_mm_s"].dropna(); cv_vp = vp["cv_xcorr_mm_s"].dropna()
    cv_ap = cv_ap[cv_ap < 80]; cv_vp = cv_vp[cv_vp < 80]
    ax.boxplot([cv_ap, cv_vp], labels=["AP-like", "VP-like"], showfliers=False, patch_artist=True,
               boxprops=dict(facecolor="#d5efd5"), medianprops=dict(color="#d62728"))
    for i, g in enumerate([cv_ap, cv_vp], 1):
        ax.scatter(np.random.normal(i, 0.05, len(g)), g, s=12, color="#2a7a2a", alpha=0.5)
    ax.set_ylabel("conduction velocity (mm/s)")
    ax.set_title(f"AP-like faster\nmedian {cv_ap.median():.1f} vs {cv_vp.median():.1f} mm/s")

    fig.suptitle("Potential type (fast AP vs slow VP) classified per recording, and how it changes the model fit",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig(out, dpi=120); plt.close(fig)


def main():
    np.random.seed(0)
    d = build()
    print("overall:", d.potential_type.value_counts().to_dict())
    print("\nby type (median):")
    print(d.groupby("potential_type")[["duration_s", "sigma", "passive_gap", "cv_xcorr_mm_s"]].median().round(2).to_string())
    for sp in ["Sensitive Mimosa", "Venus Flytrap"]:
        s = d[d.species == sp]
        print(f"\n{sp}: {s.potential_type.value_counts().to_dict()}; "
              f"AP-like CV median={s[s.potential_type=='AP-like']['cv_xcorr_mm_s'].median():.1f}")
    figure(d, os.path.join(FIG, "potential_types.png"))
    print("wrote potential_types.png, potential_types.csv")


if __name__ == "__main__":
    main()
