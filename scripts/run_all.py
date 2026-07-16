"""Run the full conduction-velocity analysis and write tables + figures.

Usage:
    python scripts/run_all.py [--data DATA_DIR] [--out RESULTS_DIR] [--cutoff HZ]
"""
from __future__ import annotations

import os
import sys
import argparse

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cvplants.io import iter_dataset            # noqa: E402
from cvplants.batch import build_results, species_summary  # noqa: E402
from cvplants import viz                        # noqa: E402


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(root, "data"))
    ap.add_argument("--out", default=os.path.join(root, "results"))
    ap.add_argument("--cutoff", type=float, default=2.0)
    args = ap.parse_args()
    np.random.seed(0)
    os.makedirs(args.out, exist_ok=True)
    fig_dir = os.path.join(args.out, "figures")
    os.makedirs(fig_dir, exist_ok=True)

    print(f"[1/4] analysing recordings under {args.data} ...")
    df = build_results(args.data, cutoff=args.cutoff)
    df.to_csv(os.path.join(args.out, "recordings.csv"), index=False)
    n_valid = int((df["valid"] == True).sum())  # noqa: E712
    print(f"      {len(df)} recordings, {n_valid} valid for delay/CV")

    print("[2/4] per-species summary ...")
    summary = species_summary(df)
    summary.to_csv(os.path.join(args.out, "species_summary.csv"), index=False)
    with __import__("pandas").option_context("display.width", 160,
                                             "display.max_columns", 20):
        print(summary.to_string(index=False))

    print("[3/4] summary figures ...")
    viz.plot_cv_by_species(df, os.path.join(fig_dir, "cv_by_species.png"))
    viz.plot_transformation(df, os.path.join(fig_dir, "near_to_far_transformation.png"))
    viz.plot_transformation_by_species(
        df, os.path.join(fig_dir, "near_to_far_by_species.png"))
    viz.plot_distance_delay(df, os.path.join(fig_dir, "cannabis_distance_delay.png"))

    print("[4/4] per-species example traces ...")
    recs = list(iter_dataset(args.data))
    viz.plot_species_grid(recs, os.path.join(fig_dir, "species_overview.png"))

    print(f"done -> {args.out}")


if __name__ == "__main__":
    main()
