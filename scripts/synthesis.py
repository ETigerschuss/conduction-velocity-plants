"""Synthesis: predict active/passive propagation per species (Part 4), and group
all species by every parameter to test for phylogenetic structure (Part 5).

Parameters per species (medians): conduction velocity, amplitude attenuation
(far/near), broadening (FWHM far/near), waveform similarity, passive dispersion σ
(from the model fit), peak−onset asymmetry, and AP-like fraction.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, dendrogram

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cvplants.io import SPECIES_FAMILY, FAMILY_COLORS   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "results", "figures")


def matrix():
    rec = pd.read_csv(os.path.join(ROOT, "results", "recordings.csv"))
    v = rec[rec["valid"] == True]  # noqa: E712
    sim = pd.read_csv(os.path.join(ROOT, "results", "model_comparison.csv"))
    sim = sim[sim["norm"] == "norm"]
    pt = pd.read_csv(os.path.join(ROOT, "results", "potential_types.csv"))
    g = v.groupby("species").agg(
        CV=("cv_xcorr_mm_s", "median"),
        attenuation=("attenuation_far_near", "median"),
        broadening=("broadening_far_near", "median"),
        waveform_sim=("xcorr_corr", "median"),
        peak_onset=("peak_delay_s", "median"),
    )
    g["dispersion"] = sim.groupby("species")["sigma"].median()
    g["AP_fraction"] = pt.groupby("species")["potential_type"].apply(lambda s: (s == "AP-like").mean())
    g["family"] = [SPECIES_FAMILY.get(s, "?") for s in g.index]
    g.to_csv(os.path.join(ROOT, "results", "species_parameters.csv"))
    return g


def active_passive_prediction(g, out):
    """Passiveness score = z(dispersion) + z(peak_onset) − z(waveform_sim).
    Low = active-leaning, high = passive-leaning."""
    z = lambda c: (c - c.mean()) / c.std()
    score = (z(g["dispersion"]) + z(g["peak_onset"]) - z(g["waveform_sim"])) / 3.0
    order = score.sort_values().index.tolist()
    pred = pd.Series(np.where(score < -0.35, "active-leaning",
                     np.where(score > 0.35, "passive-leaning", "ambiguous")), index=g.index)
    colmap = {"active-leaning": "#2a7a2a", "passive-leaning": "#b03030", "ambiguous": "#999"}
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(range(len(order)), score[order], color=[colmap[pred[s]] for s in order], edgecolor="k", lw=0.4)
    ax.axhline(0, color="k", lw=0.6)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([f"{s}\n(AP {g.loc[s,'AP_fraction']:.0%})" for s in order], rotation=40, ha="right", fontsize=8)
    ax.set_ylabel("passiveness score  (← active   passive →)")
    ax.set_title("Predicted propagation mode per species\n(active-leaning = low dispersion, rigid translation, high waveform fidelity)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=colmap[k]) for k in colmap]
    ax.legend(handles, colmap.keys(), fontsize=8, loc="upper left")
    fig.tight_layout(); fig.savefig(out, dpi=120); plt.close(fig)
    g["passiveness_score"] = score
    g["predicted_mode"] = pred
    return g


def parameter_clustermap(g, out):
    """Species × parameter heatmap, clustered; row labels coloured by family.
    Tests whether species group by their functional parameters — and by family."""
    cols = ["CV", "attenuation", "broadening", "waveform_sim", "dispersion", "AP_fraction"]
    Z = (g[cols] - g[cols].mean()) / g[cols].std()
    link = linkage(Z.values, method="average", metric="euclidean")
    order = dendrogram(link, no_plot=True, labels=list(Z.index))["ivl"]
    Zo = Z.loc[order]

    fig, (axd, axh) = plt.subplots(1, 2, figsize=(13, 6.5),
                                   gridspec_kw={"width_ratios": [1, 3]})
    dendrogram(link, ax=axd, orientation="left", labels=list(Z.index), color_threshold=0,
               above_threshold_color="#888")
    axd.set_xticks([]); axd.invert_yaxis()
    for lbl in axd.get_ymajorticklabels():
        lbl.set_color(FAMILY_COLORS.get(SPECIES_FAMILY.get(lbl.get_text(), ""), "#000"))
    im = axh.imshow(Zo.values, aspect="auto", cmap="RdBu_r", vmin=-2, vmax=2)
    axh.set_xticks(range(len(cols))); axh.set_xticklabels(cols, rotation=30, ha="right", fontsize=9)
    axh.set_yticks(range(len(order)))
    axh.set_yticklabels(order, fontsize=8)
    for lbl in axh.get_ymajorticklabels():
        lbl.set_color(FAMILY_COLORS.get(SPECIES_FAMILY.get(lbl.get_text(), ""), "#000"))
    fig.colorbar(im, ax=axh, shrink=0.6, label="z-score")
    fig.suptitle("Species grouped by all propagation parameters (leaf/label colour = family)\n"
                 "families do not form clusters — functional profile is not phylogenetically structured", fontsize=12)
    fig.tight_layout(); fig.savefig(out, dpi=120); plt.close(fig)


def family_similarity(g):
    cols = ["CV", "attenuation", "broadening", "waveform_sim", "dispersion"]
    Z = (g[cols] - g[cols].mean()) / g[cols].std()
    D = pd.DataFrame(squareform(pdist(Z.values)), index=g.index, columns=g.index)
    out = {}
    for fam in sorted(set(g["family"])):
        members = [s for s in g.index if g.loc[s, "family"] == fam]
        if len(members) < 2:
            continue
        within = np.mean([D.loc[i, j] for i in members for j in members if i < j])
        between = np.mean([D.loc[i, j] for i in members for j in g.index if g.loc[j, "family"] != fam])
        out[fam] = (len(members), within, between)
    return out


def main():
    np.random.seed(0)
    g = matrix()
    g = active_passive_prediction(g, os.path.join(FIG, "predicted_propagation_mode.png"))
    parameter_clustermap(g, os.path.join(FIG, "parameter_clustermap.png"))
    print(g.round(2).to_string())
    print("\nWithin- vs between-family functional distance:")
    for fam, (n, w, b) in family_similarity(g).items():
        print(f"  {fam:14s} (n={n}): within={w:.2f} between={b:.2f} -> "
              f"{'more similar' if w < b else 'NOT more similar'}")
    g.to_csv(os.path.join(ROOT, "results", "species_parameters.csv"))
    print("wrote predicted_propagation_mode.png, parameter_clustermap.png, species_parameters.csv")


if __name__ == "__main__":
    main()
