"""Bakeoff: does a fast-onset delay estimator beat the default cross-correlation?

Motivation: the Sensitive Mimosa CV differs from the manual analysis (mine ~19,
paper ~32). Hypothesis: my default cross-correlation delay mis-handles fast,
multi-peak Mimosa recordings, and a first-arrival ("fast onset") estimator would
do better. We test that directly against the experimenters' own per-recording
delays (spreadsheet "Tiempo"), which are the ground truth for this comparison.

Result (see printout / figure): the fast-onset estimator is LESS accurate than
the default for every species — the default already matches the manual delays
closely (median error ~0.1-0.5 s). So the fast-onset idea is rejected; the Mimosa
gap is a handful of genuinely ambiguous multi-peak recordings plus the large
intrinsic variance of manual Mimosa CV (their own SD ~= mean), not a fixable
estimator flaw.
"""
from __future__ import annotations

import os
import sys
import glob

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cvplants.io import load_recording                       # noqa: E402
from cvplants.propagation import fast_onset_delay            # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "results", "figures")


def main():
    # recordings.csv already carries sheet_delay_s (merged in by cvplants.batch.
    # augment_cv). Re-merging data/distances.csv here suffixed it to
    # sheet_delay_s_x/_y, silently dropped every row and crashed on the empty
    # frame — so read the column straight off recordings.csv.
    m = pd.read_csv(os.path.join(ROOT, "results", "recordings.csv"))

    rows = []
    for _, r in m.iterrows():
        their = r.get("sheet_delay_s")
        if pd.isna(their):
            continue
        f = os.path.join(ROOT, "data", r["species"], r["recording"] + ".wav")
        if not os.path.exists(f):
            continue
        rec = load_recording(f, species=r["species"])
        onset = fast_onset_delay(rec)
        rows.append(dict(species=r["species"], their=their,
                         default=r.get("xcorr_delay_s"), onset=onset))
    b = pd.DataFrame(rows).dropna(subset=["their"])

    def summary(col):
        v = b.dropna(subset=[col])
        err = (v[col] - v["their"]).abs()
        rho = spearmanr(v[col], v["their"])[0]
        return len(v), err.median(), rho

    print(f"{'estimator':12s} {'n':>4} {'median|err|(s)':>14} {'Spearman vs manual':>20}")
    for col in ["default", "onset"]:
        n, med, rho = summary(col)
        print(f"{col:12s} {n:4d} {med:14.2f} {rho:20.2f}")

    print("\nper-species median |error| (s):  default   onset")
    for sp, g in b.groupby("species"):
        ed = (g["default"] - g["their"]).abs().median()
        eo = (g.dropna(subset=["onset"])["onset"] - g.dropna(subset=["onset"])["their"]).abs().median()
        print(f"  {sp:18s} {ed:6.2f}   {eo:6.2f}")

    # figure: default vs onset error per species
    order = sorted(b["species"].unique())
    x = np.arange(len(order))
    ed = [(b[b.species == s]["default"] - b[b.species == s]["their"]).abs().median() for s in order]
    eo = [(b[b.species == s].dropna(subset=["onset"])["onset"] - b[b.species == s].dropna(subset=["onset"])["their"]).abs().median() for s in order]
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(x - 0.2, ed, 0.4, label="default (cross-correlation)", color="#1f3f66")
    ax.bar(x + 0.2, eo, 0.4, label="fast-onset (first arrival)", color="#d1495b")
    ax.set_xticks(x); ax.set_xticklabels(order, rotation=40, ha="right", fontsize=8)
    ax.set_ylabel("median |delay − manual delay| (s)")
    ax.set_title("Delay-estimator bakeoff vs manual per-recording delays\n(lower = better; the default cross-correlation wins everywhere)")
    ax.legend(); ax.grid(axis="y", ls="--", alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "delay_estimator_bakeoff.png"), dpi=120); plt.close(fig)
    b.to_csv(os.path.join(ROOT, "results", "delay_bakeoff.csv"), index=False)
    print("\nwrote delay_estimator_bakeoff.png, delay_bakeoff.csv")


if __name__ == "__main__":
    main()
