"""Generate AP-only and VP-only variants of the splittable figures (report Figs
7-10, 12, 13, 16, 17, 18), keeping the pooled versions. Reuses the existing plot
functions with recordings filtered by potential type.
"""
from __future__ import annotations

import os
import sys
import traceback

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from cvplants import viz                       # noqa: E402
from cvplants.io import SPECIES_FAMILY         # noqa: E402
import active_passive as ap                    # noqa: E402
import model_comparison as mc                  # noqa: E402
import venus_analysis as va                    # noqa: E402
import synthesis as syn                        # noqa: E402
import channel_diagnostics as cd               # noqa: E402

FIG = os.path.join(ROOT, "results", "figures")
PT = pd.read_csv(os.path.join(ROOT, "results", "potential_types.csv"))[
    ["species", "recording", "potential_type"]]
REC = pd.read_csv(os.path.join(ROOT, "results", "recordings.csv")).merge(
    PT, on=["species", "recording"], how="left")
MC = pd.read_csv(os.path.join(ROOT, "results", "model_comparison.csv")).merge(
    PT, on=["species", "recording"], how="left")
TYPES = [("AP-like", "_AP"), ("VP-like", "_VP")]


def matrix_subset(ptype):
    v = REC[(REC["valid"] == True) & (REC["potential_type"] == ptype)]  # noqa: E712
    g = v.groupby("species").agg(
        CV=("cv_xcorr_mm_s", "median"), attenuation=("attenuation_far_near", "median"),
        broadening=("broadening_far_near", "median"), waveform_sim=("xcorr_corr", "median"),
        peak_onset=("peak_delay_s", "median"))
    sim = MC[(MC["norm"] == "norm") & (MC["potential_type"] == ptype)]
    g["dispersion"] = sim.groupby("species")["sigma"].median()
    g["AP_fraction"] = 1.0 if ptype == "AP-like" else 0.0
    g["family"] = [SPECIES_FAMILY.get(s, "?") for s in g.index]
    return g.dropna(subset=["CV", "attenuation", "broadening", "waveform_sim", "dispersion"])


def run(name, fn):
    try:
        fn(); print("  ok:", name)
    except Exception as e:
        print("  FAIL:", name, "->", repr(e))
        traceback.print_exc()


def main():
    np.random.seed(0)
    for ptype, suf in TYPES:
        print(f"[{ptype}]")
        d = REC[REC["potential_type"] == ptype]
        run(f"near_to_far_transformation{suf}", lambda d=d, suf=suf: viz.plot_transformation(d, os.path.join(FIG, f"near_to_far_transformation{suf}.png")))
        run(f"attenuation_vs_broadening{suf}", lambda d=d, suf=suf: viz.plot_attn_broadening(d, os.path.join(FIG, f"attenuation_vs_broadening{suf}.png")))
        run(f"peak_onset_asymmetry{suf}", lambda d=d, suf=suf: ap.peak_onset_fig(d, os.path.join(FIG, f"peak_onset_asymmetry{suf}.png")))
        run(f"delay_vs_distance{suf}", lambda d=d, suf=suf: ap.delay_fig(d, os.path.join(FIG, f"delay_vs_distance{suf}.png")))
        run(f"venus_electrode_asymmetry{suf}", lambda d=d, suf=suf: va.electrode_asymmetry(d, os.path.join(FIG, f"venus_electrode_asymmetry{suf}.png")))
        run(f"model_comparison_bars{suf}", lambda ptype=ptype, suf=suf: mc.bars(MC[MC["potential_type"] == ptype], os.path.join(FIG, f"model_comparison_bars{suf}.png")))
        g = matrix_subset(ptype)
        run(f"predicted_propagation_mode{suf}", lambda g=g, suf=suf: syn.active_passive_prediction(g, os.path.join(FIG, f"predicted_propagation_mode{suf}.png")))
        run(f"parameter_clustermap{suf}", lambda g=g, suf=suf: syn.parameter_clustermap(g, os.path.join(FIG, f"parameter_clustermap{suf}.png")))


if __name__ == "__main__":
    main()
