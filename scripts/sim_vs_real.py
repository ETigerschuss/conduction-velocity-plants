"""How well can a simulated far trace predict the real one?

For every recording we predict the far channel from the near channel two ways:
  * ACTIVE (2-tap): far = a*near(t) + b*near(t-tau) — an instantaneous shared
    component (common-mode / soil-ground / volume conduction, expected here) plus
    a delayed, regenerated copy. tau is the propagation delay.
  * PASSIVE (cable): far = gain * cable_greens(near; D, tau, x) — electrotonic
    spread that decays and disperses with distance.
We report the prediction R^2 of each, overlay predicted vs real far for examples,
and re-derive CV from the common-mode-robust 2-tap delay (which, unlike a hard
time-floor, keeps genuinely fast species such as Venus flytrap).
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cvplants.io import iter_dataset, SPECIES_FAMILY, FAMILY_COLORS   # noqa: E402
from cvplants.propagation import (near_far_traces, two_component_fit,   # noqa: E402
                                  passive_cable_fit, _shift)
from cvplants.simulate import passive_cable_propagate                  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "results", "figures")


def fit_all():
    rows, traces = [], {}
    for rec in iter_dataset(os.path.join(ROOT, "data")):
        nf = near_far_traces(rec)
        if nf is None:
            continue
        t, near, far, fse, res = nf
        A = two_component_fit(near, far, fse)
        P = passive_cable_fit(near, far, fse)
        dist = res.get("distance_mm")
        tau = abs(A["tau"]) if A["tau"] == A["tau"] else np.nan
        resolved = bool(A["delayed_fraction"] and A["delayed_fraction"] > 0.30 and tau > 0.1)
        rows.append(dict(species=rec.species, recording=rec.name, distance_mm=dist,
                         a=A["a"], b=A["b"], tau=A["tau"], delayed_fraction=A["delayed_fraction"],
                         r2_active=A["r2"], r2_passive=P.get("r2", np.nan),
                         delay_resolved2=resolved,
                         cv_2tap=(dist / tau) if (dist and tau and resolved) else np.nan))
        traces[(rec.species, rec.name)] = (t, near, far, fse, A, P)
    return pd.DataFrame(rows), traces


def overlay_examples(df, traces, species_list, out):
    fig, axes = plt.subplots(len(species_list), 1, figsize=(11, 2.7 * len(species_list)))
    axes = np.atleast_1d(axes)
    for ax, sp in zip(axes, species_list):
        sub = df[(df["species"] == sp) & df["r2_active"].notna()]
        if sub.empty:
            continue
        rec = sub.iloc[(sub["r2_active"] - sub["r2_active"].median()).abs().argsort().iloc[0]]["recording"]
        t, near, far, fse, A, P = traces[(sp, rec)]
        pred_a = A["a"] * near + A["b"] * _shift(near, int(round(A["tau"] * fse)))
        fp = passive_cable_propagate(near, fse, D=P.get("D", 4), tau=P.get("tau", 3), x=P.get("x", 1))
        pred_p = P.get("gain", 0) * fp
        ax.plot(t, near, color="#444", lw=1.0, label="near")
        ax.plot(t, far, color="#d62728", lw=1.8, label="far (real)")
        ax.plot(t, pred_a, color="#1f77b4", lw=1.4, ls="--", label=f"active sim (R²={A['r2']:.2f}, τ={A['tau']:.2f}s)")
        ax.plot(t, pred_p, color="#2a9d8f", lw=1.2, ls=":", label=f"passive sim (R²={P.get('r2',float('nan')):.2f})")
        ax.set_title(f"{sp} — {rec}", fontsize=9)
        ax.legend(fontsize=7, loc="upper right"); ax.set_ylabel("amp")
    axes[-1].set_xlabel("time (s)")
    fig.suptitle("Simulated far trace predicting the real far trace (near → far)", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.98)); fig.savefig(out, dpi=120); plt.close(fig)


def r2_by_species(df, out):
    v = df.dropna(subset=["r2_active", "r2_passive"])
    order = v.groupby("species")["r2_active"].median().sort_values(ascending=False).index.tolist()
    x = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(x - 0.2, [v[v.species == s]["r2_active"].median() for s in order], 0.4, label="active (2-tap) sim", color="#1f77b4")
    ax.bar(x + 0.2, [v[v.species == s]["r2_passive"].median() for s in order], 0.4, label="passive (cable) sim", color="#2a9d8f")
    ax.set_xticks(x); ax.set_xticklabels(order, rotation=40, ha="right", fontsize=8)
    ax.set_ylabel("median prediction R²  (far from near)")
    ax.set_title("How well each simulation predicts the real far trace, per species")
    ax.legend(); ax.grid(axis="y", ls="--", alpha=0.3)
    fig.tight_layout(); fig.savefig(out, dpi=120); plt.close(fig)


def cv_2tap_by_species(df, out):
    v = df[df["cv_2tap"].notna()]
    order = v.groupby("species")["cv_2tap"].median().sort_values().index.tolist()
    data = [v[v.species == s]["cv_2tap"].values for s in order]
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.boxplot(data, showfliers=False, patch_artist=True,
               boxprops=dict(facecolor="#cfe3f5"), medianprops=dict(color="#d62728"))
    for i, d in enumerate(data, 1):
        ax.scatter(np.random.normal(i, 0.05, len(d)), d, s=16, color="#25507a", alpha=0.7, edgecolor="k", lw=0.3)
    ax.set_xticks(range(1, len(order) + 1))
    ax.set_xticklabels([f"{s}\n(n={len(d)})" for s, d in zip(order, data)], rotation=40, ha="right", fontsize=8)
    ax.set_ylabel("CV from common-mode-robust 2-tap delay (mm/s)")
    ax.set_title("Conduction velocity re-derived from the 2-tap delay (keeps fast species)")
    ax.grid(axis="y", ls="--", alpha=0.3)
    fig.tight_layout(); fig.savefig(out, dpi=120); plt.close(fig)


def main():
    np.random.seed(0)
    df, traces = fit_all()
    df.to_csv(os.path.join(ROOT, "results", "sim_fits.csv"), index=False)
    g = df.groupby("species").agg(
        n=("recording", "count"), r2_active=("r2_active", "median"),
        r2_passive=("r2_passive", "median"), tau=("tau", "median"),
        delayed_fraction=("delayed_fraction", "median"),
        n_resolved=("delay_resolved2", "sum"), cv_2tap=("cv_2tap", "median"))
    print(g.round(2).to_string())
    overlay_examples(df, traces, ["Venus Flytrap", "Sensitive Mimosa", "Marijuana",
                                  "Mint", "Ornamental Chile", "Tomato"],
                     os.path.join(FIG, "sim_vs_real_examples.png"))
    r2_by_species(df, os.path.join(FIG, "sim_prediction_r2.png"))
    cv_2tap_by_species(df, os.path.join(FIG, "cv_2tap_by_species.png"))
    print("wrote sim_vs_real_examples.png, sim_prediction_r2.png, cv_2tap_by_species.png, sim_fits.csv")


if __name__ == "__main__":
    main()
