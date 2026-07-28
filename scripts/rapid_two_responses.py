"""Within-species bimodality in the two touch-stimulated rapid movers.

The cross-species duration rule fails as an AP/VP classifier (report Section 4).
But WITHIN Sensitive Mimosa and Venus flytrap -- the two species that received a
non-damaging tactile stimulus, and the two species for which both an action
potential and a slower response class are documented -- the dominant-event
duration is clearly bimodal, with a 4-6x gap separating a sub-second cluster from
a multi-second one.

For Mimosa this matches the classical picture: a light touch evokes a fast action
potential driving local leaflet folding, whereas a stronger / damaging stimulus
additionally evokes a slow, hydraulically propagated variation potential that
crosses the pulvinus and can drop the whole petiole (Houwink 1935; Sibaoka 1991;
Volkov et al. 2010; Hagihara & Toyota 2020). A probe "strike" of uncontrolled
intensity plausibly straddles that boundary.

This is a NARROWER claim than the withdrawn universal classifier: it applies only
where both response classes are independently documented, and conduction velocity
does NOT separate the two clusters (Mimosa 14.3 vs 10.7 mm/s, p = 0.84).
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIG = os.path.join(ROOT, "results", "figures")
FAST_C, SLOW_C = "#2a9d2a", "#b060c0"
RAPID = ["Sensitive Mimosa", "Venus Flytrap"]


def load():
    pt = pd.read_csv(os.path.join(ROOT, "results", "potential_types.csv"))
    return pt[(pt.species.isin(RAPID)) & (pt.valid == True)]        # noqa: E712


def largest_gap(d):
    """Split point at the largest multiplicative gap in the sorted durations."""
    s = np.sort(d)
    ratios = s[1:] / s[:-1]
    i = int(np.argmax(ratios))
    return float(np.sqrt(s[i] * s[i + 1])), float(ratios[i]), s


def figure(m, out):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))

    # (A) per-species sorted durations, log scale, split at the largest gap
    ax = axes[0]
    for k, sp in enumerate(RAPID):
        d = m[m.species == sp].duration_s.dropna().values
        split, ratio, s = largest_gap(d)
        y = np.full(len(s), k) + np.linspace(-0.16, 0.16, len(s))
        ax.scatter(s, y, s=30, c=[FAST_C if x < split else SLOW_C for x in s],
                   edgecolor="k", lw=0.3, zorder=3)
        ax.plot([split, split], [k - 0.3, k + 0.3], color="#333", ls="--", lw=1.2)
        ax.text(split, k + 0.34, f"×{ratio:.1f} gap", ha="center", fontsize=8, color="#333")
    ax.set_xscale("log")
    ax.set_yticks(range(len(RAPID))); ax.set_yticklabels(RAPID, fontsize=9)
    ax.set_xlabel("dominant-event duration (s, log)")
    ax.set_title("Both touch-stimulated species are bimodal:\na sub-second cluster and a multi-second one", fontsize=10)
    ax.grid(axis="x", ls="--", alpha=0.3)

    # (B) the same split, as counts
    ax = axes[1]
    labels, fast, slow = [], [], []
    for sp in RAPID:
        d = m[m.species == sp].duration_s.dropna().values
        split, _, _ = largest_gap(d)
        labels.append(sp.replace(" ", "\n"))
        fast.append(int((d < split).sum())); slow.append(int((d >= split).sum()))
    x = np.arange(len(labels))
    ax.bar(x - 0.18, fast, 0.34, color=FAST_C, label="fast cluster (sub-second)")
    ax.bar(x + 0.18, slow, 0.34, color=SLOW_C, label="slow cluster (multi-second)")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("recordings"); ax.legend(fontsize=8)
    ax.set_title("Most responses are fast; a minority are slow\n(consistent with stimulus intensity varying)", fontsize=10)

    # (C) conduction velocity does NOT separate the clusters
    ax = axes[2]
    for k, sp in enumerate(RAPID):
        s = m[m.species == sp].dropna(subset=["duration_s", "cv_xcorr_mm_s"])
        split, _, _ = largest_gap(s.duration_s.values) if len(s) > 2 else (2.0, 1, None)
        for grp, c, off in [(s[s.duration_s < split], FAST_C, -0.16),
                            (s[s.duration_s >= split], SLOW_C, 0.16)]:
            if not len(grp):
                continue
            ax.scatter(np.random.normal(k + off, 0.04, len(grp)), grp.cv_xcorr_mm_s,
                       s=28, color=c, alpha=0.8, edgecolor="k", lw=0.3)
            ax.scatter(k + off, grp.cv_xcorr_mm_s.median(), s=130, marker="_", color="k", zorder=5)
    ax.set_xticks(range(len(RAPID))); ax.set_xticklabels([s.replace(" ", "\n") for s in RAPID], fontsize=9)
    ax.set_ylabel("conduction velocity (mm/s)")
    ax.set_title("...but conduction velocity does NOT separate them\n(Mimosa 14.3 vs 10.7 mm/s, p = 0.84)", fontsize=10)
    ax.grid(axis="y", ls="--", alpha=0.3)

    fig.suptitle("Within the two touch-stimulated rapid movers, the duration axis IS bimodal — "
                 "a narrower claim than the withdrawn cross-species classifier (Section 4)", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out, dpi=120); plt.close(fig)
    print("wrote", out)


def main():
    np.random.seed(0)
    m = load()
    for sp in RAPID:
        d = m[m.species == sp].duration_s.dropna().values
        split, ratio, s = largest_gap(d)
        print(f"{sp}: n={len(d)} split at {split:.2f}s (x{ratio:.1f} gap) -> "
              f"{int((d < split).sum())} fast / {int((d >= split).sum())} slow")
    figure(m, os.path.join(FIG, "rapid_two_responses.png"))


if __name__ == "__main__":
    main()
