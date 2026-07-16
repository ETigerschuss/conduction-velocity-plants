"""Batch processing: walk the dataset and assemble a results table."""
from __future__ import annotations

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


def species_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per-species summary over the valid recordings."""
    v = df[df["valid"] == True].copy()  # noqa: E712
    g = v.groupby(["species", "latin"])
    summary = g.agg(
        n_valid=("recording", "count"),
        cv_xcorr_median=("cv_xcorr_mm_s", "median"),
        cv_xcorr_mean=("cv_xcorr_mm_s", "mean"),
        cv_xcorr_std=("cv_xcorr_mm_s", "std"),
        delay_median_s=("xcorr_delay_s", "median"),
        attenuation_median=("attenuation_far_near", "median"),
        broadening_median=("broadening_far_near", "median"),
        waveform_corr_median=("xcorr_corr", "median"),
    ).reset_index()
    total = df.groupby("species")["recording"].count().rename("n_total")
    summary = summary.merge(total, on="species", how="left")
    return summary.sort_values("cv_xcorr_median", na_position="last")
