"""Compare this pipeline's CV to the manual analysis in the paper.

Contreras, Morales, Rojas, Serbe-Kamp, Marzullo (Plant Signaling & Behavior),
Table 1 / Figure 3. Their per-species CV is a MEAN (mm/s) over accepted
recordings; their accepted counts match this repo's WAV files species-by-species
(176 total). We compare mean-to-mean on the resolved-delay subset.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cvplants.io import SPECIES_FAMILY, FAMILY_COLORS   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "results", "figures")

# Paper Table 1: common name -> (CV mean mm/s, CV SD)
PAPER = {
    "Argentian Dollar": (4.8, 4.3), "Basil": (7.4, 5.2), "Chilean Chile": (11.9, 7.5),
    "Creeping Inchplant": (7.4, 6.5), "Hierbabuena": (9.4, 10.8), "Marijuana": (8.3, 6.0),
    "Mint": (5.1, 3.0), "Ornamental Chile": (6.4, 3.3), "Rosemary": (6.6, 4.7),
    "Ruda": (10.0, 7.8), "Sensitive Mimosa": (32.4, 21.6), "Tomato": (7.0, 4.9),
    "Venus Flytrap": (35.3, 13.7),
}
RAPID = {"Sensitive Mimosa", "Venus Flytrap"}


def main():
    df = pd.read_csv(os.path.join(ROOT, "results", "recordings.csv"))
    res = df[(df["valid"] == True) & (df["delay_resolved"] == True)]  # noqa: E712
    rows = []
    for sp, (tm, tsd) in PAPER.items():
        r = res[res["species"] == sp]["cv_xcorr_mm_s"].dropna()
        rows.append(dict(species=sp, paper_mean=tm, paper_sd=tsd,
                         mine_mean=r.mean(), mine_sd=r.std(), n=len(r)))
    c = pd.DataFrame(rows)
    c.to_csv(os.path.join(ROOT, "results", "comparison_to_paper.csv"), index=False)
    pr = pearsonr(c["paper_mean"], c["mine_mean"])[0]
    m = c["species"] != "Sensitive Mimosa"
    pr_nm = pearsonr(c[m]["paper_mean"], c[m]["mine_mean"])[0]
    print(c.round(2).to_string(index=False))
    print(f"Pearson r = {pr:.3f} (all), {pr_nm:.3f} (excl. Mimosa)")

    # scatter: mine vs paper
    fig, ax = plt.subplots(figsize=(7.5, 7))
    hi = 40
    ax.plot([0, hi], [0, hi], "k--", lw=1, label="identity")
    for _, row in c.iterrows():
        col = "#d62728" if row["species"] in RAPID else FAMILY_COLORS.get(SPECIES_FAMILY.get(row["species"], ""), "#1f77b4")
        ax.errorbar(row["paper_mean"], row["mine_mean"], xerr=row["paper_sd"], yerr=row["mine_sd"],
                    fmt="o", ms=7, color=col, ecolor=col, elinewidth=0.8, capsize=2, alpha=0.85)
        ax.annotate(row["species"], (row["paper_mean"], row["mine_mean"]),
                    fontsize=7, xytext=(4, 3), textcoords="offset points")
    ax.set_xlabel("paper CV mean ± SD (mm/s)")
    ax.set_ylabel("this pipeline CV mean ± SD (mm/s), resolved delays")
    ax.set_title(f"CV: this pipeline vs manual analysis\nPearson r = {pr:.2f} (all), {pr_nm:.2f} (excl. Mimosa)")
    ax.legend(); ax.grid(ls="--", alpha=0.3); ax.set_xlim(0, hi); ax.set_ylim(0, hi)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "compare_to_paper_scatter.png"), dpi=120); plt.close(fig)

    # grouped bars
    order = c.sort_values("paper_mean")["species"].tolist()
    x = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(12, 5.5))
    cm = c.set_index("species")
    ax.bar(x - 0.2, [cm.loc[s, "paper_mean"] for s in order], 0.4, yerr=[cm.loc[s, "paper_sd"] for s in order],
           capsize=3, label="paper (manual)", color="#bbb")
    ax.bar(x + 0.2, [cm.loc[s, "mine_mean"] for s in order], 0.4, yerr=[cm.loc[s, "mine_sd"] for s in order],
           capsize=3, label="this pipeline (resolved)", color="#1f3f66")
    ax.set_xticks(x); ax.set_xticklabels(order, rotation=40, ha="right", fontsize=8)
    ax.set_ylabel("conduction velocity (mm/s)")
    ax.set_title("Per-species CV: manual analysis vs automatic pipeline (mean ± SD)")
    ax.legend(); ax.grid(axis="y", ls="--", alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "compare_to_paper_bars.png"), dpi=120); plt.close(fig)
    print("wrote compare_to_paper_scatter.png, compare_to_paper_bars.png, comparison_to_paper.csv")


if __name__ == "__main__":
    main()
