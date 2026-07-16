"""Comparative / phylogenetic analysis of the transformation metrics.

Writes figures to results/figures and prints the statistics used in REPORT.md.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cvplants.batch import build_results          # noqa: E402
from cvplants import phylo, viz                    # noqa: E402
from cvplants.io import SPECIES_FAMILY             # noqa: E402


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = os.path.join(root, "data")
    fig_dir = os.path.join(root, "results", "figures")
    os.makedirs(fig_dir, exist_ok=True)
    np.random.seed(0)

    df = build_results(data)

    prof = phylo.species_profiles(df)
    prof.to_csv(os.path.join(root, "results", "species_profiles.csv"))
    print("=== species functional profiles (median) ===")
    with pd.option_context("display.width", 160):
        print(prof.round(3).to_string())

    print("\n=== Mantel: functional distance vs taxonomic distance ===")
    labels, Dfun = phylo.functional_distance(prof)
    Dtax = phylo.taxonomic_distance_matrix(labels)
    r, p = phylo.mantel(Dfun, Dtax, n_perm=9999)
    print(f"Mantel Spearman r = {r:.3f}, p = {p:.4f}  (n={len(labels)} species)")

    print("\n=== Kruskal-Wallis across families (species medians) ===")
    for col in phylo.METRICS:
        res = phylo.kruskal_by_family(df, col)
        print(res)

    print("\n=== conduction velocity by species (now that distances are in) ===")
    cvmed = (df[df["valid"] == True].groupby("species")["cv_xcorr_mm_s"]  # noqa: E712
             .median().sort_values())
    print(cvmed.round(2).to_string())
    print("\nKruskal-Wallis of CV across families:",
          phylo.kruskal_by_family(df, "cv_xcorr_mm_s"))

    print("\n=== genus-pair check (same genus should be similar) ===")
    cols = phylo.METRICS + ["cv_xcorr_mm_s"]
    cvsp = df[df["valid"] == True].groupby("species")["cv_xcorr_mm_s"].median()  # noqa: E712
    for a, b in [("Mint", "Hierbabuena"), ("Chilean Chile", "Ornamental Chile")]:
        print(f"{a} vs {b} (both {SPECIES_FAMILY[a]}):")
        sub = prof.loc[[a, b], phylo.METRICS].copy()
        sub["cv_mm_s"] = [cvsp[a], cvsp[b]]
        print(sub.round(3).to_string())

    print("\n=== cross-variable correlations (recording level) ===")
    for k, val in phylo.crossvar_correlations(df).items():
        print(f"  {k}: rho={val['rho']:.3f} p={val['p']:.1e} n={val['n']}")

    print("\n=== fast vs slow signalling (inter-channel delay, s) ===")
    v = df[df["valid"] == True]  # noqa: E712
    delay = v.groupby("species")["xcorr_delay_s"].median().sort_values()
    print(delay.round(2).to_string())

    print("\n[figures]")
    viz.plot_transformation_by_species(
        df, os.path.join(fig_dir, "near_to_far_by_species.png"),
        central="median", color_by_family=True)
    Z = phylo.linkage_matrix(prof)
    viz.plot_functional_dendrogram(prof, Z, os.path.join(fig_dir, "functional_dendrogram.png"))
    viz.plot_family_strip(df, os.path.join(fig_dir, "metrics_by_family.png"))
    viz.plot_attn_broadening(df, os.path.join(fig_dir, "attenuation_vs_broadening.png"))
    viz.plot_delay_validation(df, os.path.join(root, "data", "distances.csv"),
                              os.path.join(fig_dir, "delay_validation.png"))
    print("done")


if __name__ == "__main__":
    main()
