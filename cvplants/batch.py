"""Batch processing: walk the dataset and assemble a results table."""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

from .io import iter_dataset
from .analysis import analyze_recording


def build_results(data_dir: str, cutoff: float = 2.0) -> pd.DataFrame:
    """Analyse every recording under data_dir; return one row per recording."""
    rows = []
    for rec in iter_dataset(data_dir):
        try:
            rows.append(analyze_recording(rec, cutoff=cutoff))
        except Exception as exc:  # keep going; record the failure
            rows.append({
                "species": rec.species, "recording": rec.name,
                "valid": False, "flags": f"error:{type(exc).__name__}:{exc}",
            })
    return pd.DataFrame(rows)


def augment_cv(df: pd.DataFrame, root: str) -> pd.DataFrame:
    """Add two alternative CV columns to the results:

    * cv_manual  = distance / the experimenters' manual delay (spreadsheet
      "Tiempo"); reproduces the paper's per-recording CV exactly where available.
    * cv_2tap / tau_2tap = the common-mode-robust 2-tap delay
      (far = a*near + b*near(t-tau)); keeps the fast species (Venus) that a
      zero-lag common component would otherwise wash out.

    Both are merged from files if present (data/distances.csv, results/sim_fits.csv)
    so the default analysis stays fast; missing sources are skipped silently.
    """
    dpath = os.path.join(root, "data", "distances.csv")
    if os.path.exists(dpath):
        d = pd.read_csv(dpath)[["species", "recording", "distance_mm", "sheet_delay_s"]]
        df = df.merge(d, on=["species", "recording"], how="left", suffixes=("", "_d"))
        with np.errstate(divide="ignore", invalid="ignore"):
            df["cv_manual"] = df["distance_mm"].where(df["distance_mm"].notna(),
                                                      df.get("distance_mm_d")) / df["sheet_delay_s"]
    spath = os.path.join(root, "results", "sim_fits.csv")
    if os.path.exists(spath):
        s = pd.read_csv(spath)[["species", "recording", "tau", "cv_2tap"]].rename(
            columns={"tau": "tau_2tap"})
        df = df.merge(s, on=["species", "recording"], how="left")
    return df


def species_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per-species summary over the valid recordings."""
    v = df[df["valid"] == True].copy()  # noqa: E712
    g = v.groupby(["species", "latin"])
    agg = dict(
        n_valid=("recording", "count"),
        cv_xcorr_median=("cv_xcorr_mm_s", "median"),
        cv_xcorr_mean=("cv_xcorr_mm_s", "mean"),
        cv_xcorr_std=("cv_xcorr_mm_s", "std"),
    )
    if "cv_manual" in v.columns:
        agg["cv_manual_mean"] = ("cv_manual", "mean")
    if "cv_2tap" in v.columns:
        agg["cv_2tap_median"] = ("cv_2tap", "median")
    summary = g.agg(
        **agg,
        delay_median_s=("xcorr_delay_s", "median"),
        attenuation_median=("attenuation_far_near", "median"),
        broadening_median=("broadening_far_near", "median"),
        waveform_corr_median=("xcorr_corr", "median"),
    ).reset_index()
    total = df.groupby("species")["recording"].count().rename("n_total")
    summary = summary.merge(total, on="species", how="left")
    return summary.sort_values("cv_xcorr_median", na_position="last")
