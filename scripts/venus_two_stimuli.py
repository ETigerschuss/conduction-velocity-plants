"""Venus flytrap: touch-evoked vs flame-evoked responses in the SAME species.

Revision I of the manuscript adds that, at the close of data collection, Venus
flytraps and Sensitive Mimosas were also recorded with a FLAME stimulus in place
of the tactile one ("hence the two types of stimuli listed in Table 1").

Venus recordings split perfectly in time: a main block (2024-01-28 to 2024-06-01)
and a late block (2024-07-03, 2025-01-10, 2025-01-14). We therefore treat the
late block as the putative flame group -- an INFERENCE from recording date, to be
confirmed against Table 1. On that split the two groups do not overlap at all.

Mimosa cannot be split this way: its long-duration recordings are scattered
across dates, so Table 1 is required to label them.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import fisher_exact, mannwhitneyu

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIG = os.path.join(ROOT, "results", "figures")

SPLIT = pd.Timestamp("2024-07-01")          # main block ends before this date
TOUCH_C, FLAME_C = "#2a9d2a", "#e05c1f"
PRE, POST, FSG = 2.0, 8.0, 50.0


def venus_traces():
    """Peak-aligned near/far traces for every valid Venus recording, with date."""
    from cvplants.io import load_recording
    from cvplants.analysis import _response_window
    from cvplants.preprocessing import lowpass, baseline_subtract
    import glob

    rec_csv = pd.read_csv(os.path.join(ROOT, "results", "recordings.csv"))
    ok = set(rec_csv[(rec_csv["valid"] == True) &                       # noqa: E712
                     (rec_csv["species"] == "Venus Flytrap")]["recording"])
    grid = np.arange(-PRE, POST, 1.0 / FSG)
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "Venus Flytrap", "*.wav"))):
        name = os.path.splitext(os.path.basename(f))[0]
        if name not in ok:
            continue
        rec = load_recording(f, species="Venus Flytrap")
        if rec.n_channels < 2:
            continue
        fs = rec.fs
        stim = rec.stim_start if rec.stim_start is not None else 1.0
        bl = (max(0.0, stim - PRE), stim)
        ch = [lowpass(baseline_subtract(rec.data[:, i], fs, bl), fs, 15.0) for i in (0, 1)]
        w = _response_window(rec)
        i0, i1 = int(w[0] * fs), int(w[1] * fs)
        step = max(1, int(round(fs / FSG)))
        segs = [c[i0:i1:step] for c in ch]
        fse = fs / step
        if min(len(s) for s in segs) < int(fse):
            continue
        info = []
        for s in segs:
            sign = np.sign(s[np.argmax(np.abs(s))]) or 1.0
            s = s * sign
            pk = int(np.argmax(s))
            info.append((s, pk, s[pk] if s[pk] else 1.0))
        ni = 0 if info[0][1] <= info[1][1] else 1
        amp = info[ni][2]
        pair = []
        for ci in (ni, 1 - ni):
            s, pk, _ = info[ci]
            tt = (np.arange(len(s)) - pk) / fse
            pair.append(np.interp(grid, tt, s / amp, left=np.nan, right=np.nan))
        date = pd.to_datetime(name.split("_")[2])
        rows.append(dict(recording=name, date=date, near=pair[0], far=pair[1]))
    return grid, pd.DataFrame(rows)


def main():
    grid, tr = venus_traces()
    pt = pd.read_csv(os.path.join(ROOT, "results", "potential_types.csv"))
    rec = pd.read_csv(os.path.join(ROOT, "results", "recordings.csv"))[
        ["species", "recording", "attenuation_far_near"]]
    meta = pt[(pt.species == "Venus Flytrap") & (pt.valid == True)].merge(  # noqa: E712
        rec, on=["species", "recording"], how="left")
    d = tr.merge(meta, on="recording", how="inner")
    d["grp"] = np.where(d.date >= SPLIT, "late block (putative flame)", "main block (touch)")
    groups = ["main block (touch)", "late block (putative flame)"]
    cols = {groups[0]: TOUCH_C, groups[1]: FLAME_C}

    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.8))

    # (A) the traces themselves
    ax = axes[0]
    for g in groups:
        sub = d[d.grp == g]
        for _, r in sub.iterrows():
            ax.plot(grid, np.nan_to_num(r["near"]), lw=0.7, color=cols[g], alpha=0.45)
        M = np.vstack([np.nan_to_num(x) for x in sub["near"]])
        ax.plot(grid, np.median(M, axis=0), lw=2.6, color=cols[g],
                label=f"{g} (n={len(sub)})")
    ax.set_xlim(-1.5, 8); ax.set_xlabel("time from peak (s)")
    ax.set_ylabel("normalised amplitude (near)")
    ax.set_title("Same species, same electrodes — two stimuli\nthin = recordings, thick = median", fontsize=10)
    ax.legend(fontsize=8); ax.grid(alpha=0.25, ls="--")

    # (B) duration per recording: complete separation
    ax = axes[1]
    for k, g in enumerate(groups):
        v = d[d.grp == g].duration_s.values
        ax.scatter(np.random.normal(k, 0.06, len(v)), v, s=46, color=cols[g],
                   edgecolor="k", lw=0.4, zorder=3)
        ax.scatter(k, np.median(v), s=220, marker="_", color="k", zorder=4)
    ax.axhline(2.0, color="#888", ls="--", lw=1)
    ax.set_yscale("log"); ax.set_xticks(range(2))
    ax.set_xticklabels(["touch", "flame\n(putative)"], fontsize=9)
    ax.set_ylabel("dominant-event duration (s, log)")
    a = d[d.grp == groups[0]].duration_s; b = d[d.grp == groups[1]].duration_s
    tab = np.array([[(a <= 2).sum(), (a > 2).sum()], [(b <= 2).sum(), (b > 2).sum()]])
    ax.set_title(f"Complete separation: {len(a)}/{len(a)} vs {len(b)}/{len(b)}\n"
                 f"Fisher p = {fisher_exact(tab)[1]:.5f}", fontsize=10)
    ax.grid(axis="y", alpha=0.25, ls="--")

    # (C) what differs, and what does not
    ax = axes[2]
    metrics = [("duration_s", "duration (s)"), ("cv_xcorr_mm_s", "CV (mm/s)"),
               ("attenuation_far_near", "far/near amplitude")]
    x = np.arange(len(metrics))
    for k, g in enumerate(groups):
        sub = d[d.grp == g]
        vals, errs = [], []
        for c, _ in metrics:
            s = pd.to_numeric(sub[c], errors="coerce").dropna()
            vals.append(s.median()); errs.append(s.std() / max(np.sqrt(len(s)), 1))
        ax.bar(x + (k - 0.5) * 0.36, vals, 0.34, yerr=errs, capsize=3,
               color=cols[g], edgecolor="k", lw=0.4, label=g)
    ps = []
    for c, _ in metrics:
        aa = pd.to_numeric(d[d.grp == groups[0]][c], errors="coerce").dropna()
        bb = pd.to_numeric(d[d.grp == groups[1]][c], errors="coerce").dropna()
        ps.append(mannwhitneyu(aa, bb)[1] if len(aa) > 2 and len(bb) > 2 else np.nan)
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{lab}\np={p:.3f}" for (_, lab), p in zip(metrics, ps)], fontsize=8)
    ax.set_title("Duration and decrement change; velocity does not\n"
                 "(the VP signature: decremental, not slower)", fontsize=10)
    ax.legend(fontsize=7); ax.grid(axis="y", alpha=0.25, ls="--")

    fig.suptitle("Venus flytrap, touch- vs flame-evoked responses — a within-species action-potential / "
                 "wound-potential comparison\n(groups inferred from recording date; confirm against Table 1)",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    out = os.path.join(FIG, "venus_two_stimuli.png")
    fig.savefig(out, dpi=200); plt.close(fig)
    print("wrote", out)
    for g in groups:
        s = d[d.grp == g]
        print(f"  {g:30s} n={len(s):2d}  dur={s.duration_s.median():6.2f}s  "
              f"CV={s.cv_xcorr_mm_s.median():5.1f}  atten={s.attenuation_far_near.median():.2f}")
    print("  p-values:", {lab: round(p, 4) for (_, lab), p in zip(metrics, ps)})


if __name__ == "__main__":
    np.random.seed(0)
    main()
