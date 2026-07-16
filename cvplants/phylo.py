"""Comparative analysis: do the signal-transformation metrics track taxonomy?

The three near->far metrics (amplitude attenuation, temporal broadening,
waveform similarity) are dimensionless ratios, so they are the most defensible
traits to compare across species. We build a per-species functional profile,
cluster species by it, and test whether functional distance is associated with
taxonomic distance (Mantel test).

Caveats (kept explicit because they bound every conclusion):
  * Attenuation and broadening also grow with electrode spacing, which was not
    standardised / recorded for most species -> cross-species differences are
    partly confounded by geometry.
  * 13 species, only two families replicated (Lamiaceae n=5, Solanaceae n=3):
    low power. Treat as exploratory.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import kruskal, spearmanr
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage

from .io import (SPECIES_FAMILY, SPECIES_ORDER, SPECIES_CLADE,
                 taxonomic_distance)

METRICS = ["attenuation_far_near", "broadening_far_near", "xcorr_corr"]


def species_profiles(df: pd.DataFrame, metrics=METRICS) -> pd.DataFrame:
    """Per-species median of each metric plus taxonomy and sample size."""
    v = df[df["valid"] == True]  # noqa: E712
    prof = v.groupby("species")[metrics].median()
    prof["n"] = v.groupby("species")["recording"].count()
    prof["family"] = [SPECIES_FAMILY.get(s, "?") for s in prof.index]
    prof["order"] = [SPECIES_ORDER.get(s, "?") for s in prof.index]
    prof["clade"] = [SPECIES_CLADE.get(s, "?") for s in prof.index]
    return prof


def functional_distance(prof: pd.DataFrame, metrics=METRICS):
    """Z-score the metric medians across species, return (labels, dist matrix)."""
    X = prof[metrics].to_numpy(dtype=float)
    X = (X - X.mean(0)) / X.std(0)
    D = squareform(pdist(X, metric="euclidean"))
    return list(prof.index), D


def taxonomic_distance_matrix(labels):
    n = len(labels)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            D[i, j] = taxonomic_distance(labels[i], labels[j])
    return D


def mantel(D1, D2, n_perm=9999, method="spearman", seed=0):
    """Mantel test between two distance matrices (upper-triangle correlation
    with row/column permutations). Returns (r, p_one_sided_positive)."""
    rng = np.random.default_rng(seed)
    iu = np.triu_indices_from(D1, k=1)
    a, b = D1[iu], D2[iu]
    corr = spearmanr if method == "spearman" else lambda x, y: (np.corrcoef(x, y)[0, 1], 0)
    r_obs = corr(a, b)[0]
    idx = np.arange(D1.shape[0])
    count = 0
    for _ in range(n_perm):
        p = rng.permutation(idx)
        rp = corr(D1[np.ix_(p, p)][iu], b)[0]
        if rp >= r_obs:
            count += 1
    p_val = (count + 1) / (n_perm + 1)
    return float(r_obs), float(p_val)


def kruskal_by_family(df: pd.DataFrame, col: str, min_species=2):
    """Kruskal-Wallis of `col` across families that have >= min_species species.

    Uses species-median values (one value per species) to avoid pseudoreplication
    from many recordings per plant.
    """
    v = df[df["valid"] == True].copy()  # noqa: E712
    med = v.groupby("species")[col].median().rename("val").reset_index()
    med["family"] = [SPECIES_FAMILY.get(s, "?") for s in med["species"]]
    fam_species = med.groupby("family").filter(lambda g: len(g) >= min_species)
    groups = [g["val"].dropna().values for _, g in fam_species.groupby("family")]
    groups = [g for g in groups if len(g) >= 2]
    if len(groups) < 2:
        return None
    stat, p = kruskal(*groups)
    return {"col": col, "families": len(groups), "H": float(stat), "p": float(p)}


def crossvar_correlations(df: pd.DataFrame):
    """Recording-level Spearman correlations between the transformation metrics.

    Attenuation vs broadening in particular tests the cable-filtering idea: a
    tissue that attenuates more should also broaden (low-pass) more.
    """
    v = df[df["valid"] == True]  # noqa: E712
    out = {}
    pairs = [("attenuation_far_near", "broadening_far_near"),
             ("attenuation_far_near", "xcorr_corr"),
             ("broadening_far_near", "xcorr_corr")]
    for a, b in pairs:
        sub = v[[a, b]].dropna()
        r, p = spearmanr(sub[a], sub[b])
        out[f"{a} vs {b}"] = {"rho": float(r), "p": float(p), "n": len(sub)}
    return out


def linkage_matrix(prof: pd.DataFrame, metrics=METRICS):
    X = prof[metrics].to_numpy(dtype=float)
    X = (X - X.mean(0)) / X.std(0)
    return linkage(X, method="average", metric="euclidean")
