"""Active vs passive propagation: data discriminators + simulation figures.

Writes to results/figures/:
  active_passive_space.png     gain vs dispersion per species (the classifier)
  decrement_vs_distance.png    ln(far/near) vs distance (space constant)
  delay_vs_distance.png        delay vs distance (constant-velocity test)
  cable_vs_fhn_sim.png         passive cable vs FitzHugh-Nagumo travelling wave
  kernel_example_*.png         real near/far with passive-cable / delay fits
and results/kernel_fits.csv, results/propagation_summary.csv.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cvplants.io import iter_dataset, SPECIES_FAMILY, FAMILY_COLORS  # noqa: E402
from cvplants import propagation as pp                                # noqa: E402
from cvplants import simulate as sim                                  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "results", "figures")


def active_passive_space(kt, out):
    """gain (amplitude preservation) vs sigma (dispersion). Active = top-left."""
    fig, ax = plt.subplots(figsize=(9, 7))
    med = kt.groupby("species")[["gain", "sigma_s"]].median()
    for sp, row in med.iterrows():
        sub = kt[kt["species"] == sp]
        c = FAMILY_COLORS.get(SPECIES_FAMILY.get(sp, ""), "#888")
        ax.scatter(sub["sigma_s"], sub["gain"], s=16, color=c, alpha=0.25, edgecolor="none")
        ax.scatter(row["sigma_s"], row["gain"], s=90, color=c, edgecolor="k", zorder=5)
        ax.annotate(sp, (row["sigma_s"], row["gain"]), fontsize=8,
                    xytext=(4, 4), textcoords="offset points")
    ax.axhline(1, color="k", ls=":", lw=0.8)
    ax.set_xlabel("extra dispersion needed, σ (s)  →  more passive (low-pass) filtering")
    ax.set_ylabel("amplitude preservation, gain (far/near)  →  up = non-decremental")
    ax.text(0.02, 0.97, "ACTIVE-like\n(shape preserved,\nnon-decremental)",
            transform=ax.transAxes, va="top", fontsize=9, color="#2a7a2a")
    ax.text(0.98, 0.05, "PASSIVE / decremental\n(dispersed, attenuated)",
            transform=ax.transAxes, va="bottom", ha="right", fontsize=9, color="#b03030")
    ax.set_title("Active↔passive space from near→far kernel fits (species medians)")
    ax.grid(ls="--", alpha=0.3)
    ax.set_ylim(-0.4, 2.2)   # focus on the median region (a few recordings sit higher)
    fig.tight_layout(); fig.savefig(out, dpi=120); plt.close(fig)


def peak_onset_fig(df, out):
    v = df[df["valid"] == True].copy()  # noqa: E712
    v["asym"] = v["peak_delay_s"] - v["onset_delay_s"]
    order = v.groupby("species")["asym"].median().sort_values().index.tolist()
    fig, ax = plt.subplots(figsize=(12, 5.5))
    for i, sp in enumerate(order):
        s = v[v["species"] == sp]
        c = FAMILY_COLORS.get(SPECIES_FAMILY.get(sp, ""), "#888")
        ax.scatter(np.random.normal(i, 0.07, len(s)), s["asym"], s=16, color=c, alpha=0.35, edgecolor="none")
        ax.scatter(i, s["asym"].median(), s=90, color=c, edgecolor="k", zorder=5)
    ax.axhline(0, color="k", ls="--", lw=1)
    ax.set_xticks(range(len(order))); ax.set_xticklabels(order, rotation=40, ha="right", fontsize=8)
    ax.set_ylabel("peak delay − onset delay (s)"); ax.set_ylim(-1.5, 3)
    ax.text(0.01, 0.97, "≈0 : near-rigid translation", transform=ax.transAxes, va="top", color="#2a7a2a", fontsize=9)
    ax.text(0.99, 0.97, "large + : peak lags onset (dispersive)", transform=ax.transAxes, va="top", ha="right", color="#b03030", fontsize=9)
    ax.set_title("Peak−onset delay asymmetry: an amplitude-independent measure of dispersion\n"
                 "(a descriptive metric — it does not by itself identify active vs passive propagation)",
                 fontsize=11)
    ax.grid(axis="y", ls="--", alpha=0.3)
    fig.tight_layout(); fig.savefig(out, dpi=120); plt.close(fig)


def decrement_fig(df, out):
    v = df[(df["valid"] == True) & (df["attenuation_far_near"] > 0)  # noqa: E712
           & df["distance_mm"].notna()]
    fit = pp.decrement_fit(df)
    fig, ax = plt.subplots(figsize=(7.5, 6))
    for sp in sorted(v["species"].unique()):
        s = v[v["species"] == sp]
        ax.scatter(s["distance_mm"], np.log(s["attenuation_far_near"]), s=22,
                   color=FAMILY_COLORS.get(SPECIES_FAMILY.get(sp, ""), "#888"),
                   alpha=0.8, edgecolor="k", linewidth=0.3)
    xs = np.linspace(v["distance_mm"].min(), v["distance_mm"].max(), 50)
    ax.plot(xs, fit["slope"] * xs + np.log(v["attenuation_far_near"]).mean()
            - fit["slope"] * v["distance_mm"].mean(), "r--",
            label=f"slope={fit['slope']:+.3f}/mm (λ≈{fit['lambda_mm']:.0f} mm), p={fit['p']:.2f}")
    ax.axhline(0, color="k", ls=":", lw=0.8)
    ax.set_xlabel("inter-electrode distance (mm)")
    ax.set_ylabel("ln(far / near amplitude)")
    ax.set_title("Amplitude decrement vs distance\n(steep negative slope = passive/decremental; flat = non-decremental)")
    ax.legend(); ax.grid(ls="--", alpha=0.3)
    fig.tight_layout(); fig.savefig(out, dpi=120); plt.close(fig)


def delay_fig(df, out):
    v = df[(df["valid"] == True) & df["distance_mm"].notna()  # noqa: E712
           & df["xcorr_delay_s"].notna()]
    fit = pp.velocity_fit(df)
    fig, ax = plt.subplots(figsize=(7.5, 6))
    for sp in sorted(v["species"].unique()):
        s = v[v["species"] == sp]
        ax.scatter(s["distance_mm"], s["xcorr_delay_s"], s=22,
                   color=FAMILY_COLORS.get(SPECIES_FAMILY.get(sp, ""), "#888"),
                   alpha=0.8, edgecolor="k", linewidth=0.3)
    xs = np.linspace(0, v["distance_mm"].max(), 50)
    ax.plot(xs, fit["slope_s_per_mm"] * xs + fit["intercept_s"], "r--",
            label=f"v≈{fit['velocity_mm_s']:.1f} mm/s, r={fit['r']:.2f}, p={fit['p']:.1e}")
    ax.set_xlabel("inter-electrode distance (mm)")
    ax.set_ylabel("inter-channel delay (s)")
    ax.set_title("Delay vs distance\n(linear through ~origin = constant-velocity propagation)")
    ax.legend(); ax.grid(ls="--", alpha=0.3)
    fig.tight_layout(); fig.savefig(out, dpi=120); plt.close(fig)


def sim_fig(out):
    """Passive cable vs FitzHugh-Nagumo active wave, side by side."""
    fs = 50.0
    t = np.arange(int(12 * fs)) / fs
    near = np.exp(-((t - 3.0) ** 2) / (2 * 0.6 ** 2))       # a proximal bump
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

    # passive: three increasing distances
    for x, c in zip([0.6, 1.2, 2.0], ["#6aa9e0", "#3d78b5", "#1f3f66"]):
        far = sim.passive_cable_propagate(near, fs, D=4.0, tau=3.0, x=x)
        axes[0].plot(t, far, color=c, label=f"far, x={x}")
    axes[0].plot(t, near, "k", lw=2, label="near")
    axes[0].set_title("Passive cable\n(decays + broadens with distance)")
    axes[0].legend(fontsize=8)

    # active: FHN travelling wave at two probes
    tv, (r0, r1), vel = sim.fitzhugh_nagumo_1d()
    axes[1].plot(tv, r0, "k", lw=2, label="near probe")
    axes[1].plot(tv, r1, "#c0392b", lw=2, label="far probe")
    axes[1].set_title(f"FitzHugh–Nagumo active wave\n(constant amplitude & velocity, v≈{vel:.2f} units)")
    axes[1].legend(fontsize=8)

    # signature comparison: amplitude ratio vs distance
    xs = np.linspace(0.3, 2.5, 12)
    ratios = [sim.passive_cable_propagate(near, fs, D=4.0, tau=3.0, x=x).max() / near.max()
              for x in xs]
    axes[2].plot(xs, ratios, "o-", color="#1f3f66", label="passive cable")
    axes[2].axhline(1.0, color="#c0392b", lw=2, label="active (non-decremental)")
    axes[2].set_xlabel("distance (cable units)"); axes[2].set_ylabel("far/near amplitude")
    axes[2].set_title("Amplitude vs distance:\nthe key signature")
    axes[2].legend(fontsize=8)

    for ax in axes[:2]:
        ax.set_xlabel("time (s / model units)"); ax.set_ylabel("amplitude")
    for ax in axes:
        ax.grid(ls="--", alpha=0.3)
    fig.suptitle("ILLUSTRATIVE (no data): what active vs passive propagation would look like — the signatures we then looked for",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.97)); fig.savefig(out, dpi=120); plt.close(fig)


def kernel_example(recs, species, out, kt):
    """Show a representative near/far pair (closest to the species median fit)."""
    sub = kt[(kt["species"] == species) & kt["gain"].notna()]
    if sub.empty:
        return
    gm, sm_ = sub["gain"].median(), sub["sigma_s"].median()
    gsd = sub["gain"].std() or 1.0
    ssd = sub["sigma_s"].std() or 1.0
    sub = sub.assign(_d=((sub["gain"] - gm) / gsd) ** 2 + ((sub["sigma_s"] - sm_) / ssd) ** 2)
    target = sub.sort_values("_d").iloc[0]["recording"]
    for rec in recs:
        if rec.species != species or rec.name != target:
            continue
        nf = pp.near_far_traces(rec)
        if nf is None:
            continue
        t, near, far, fs_eff, res = nf
        k = pp.fit_passive_kernel(near, far, fs_eff)
        from scipy.ndimage import gaussian_filter1d
        sm = gaussian_filter1d(near, max(k["sigma_s"] * fs_eff, 1e-6))
        lag = int(k["delay_s"] * fs_eff)
        pred = np.zeros_like(sm)
        if lag < len(sm):
            pred[lag:] = k["gain"] * sm[:len(sm) - lag]
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(t, near, "k", label="near")
        ax.plot(t, far, "#c0392b", label="far (measured)")
        ax.plot(t, pred, "b--", label=f"far predicted: gain={k['gain']:.2f}, σ={k['sigma_s']:.2f}s, R²={k['r2']:.2f}")
        ax.set_title(f"{species}: {rec.name}")
        ax.set_xlabel("time (s)"); ax.set_ylabel("amplitude"); ax.legend(fontsize=8)
        ax.grid(ls="--", alpha=0.3)
        fig.tight_layout(); fig.savefig(out, dpi=120); plt.close(fig)
        return


def main():
    np.random.seed(0)
    os.makedirs(FIG, exist_ok=True)
    df = pd.read_csv(os.path.join(ROOT, "results", "recordings.csv"))
    recs = list(iter_dataset(os.path.join(ROOT, "data")))

    print("[1] kernel fits ...")
    kt = pp.kernel_table(recs)
    kt.to_csv(os.path.join(ROOT, "results", "kernel_fits.csv"), index=False)
    active_passive_space(kt, os.path.join(FIG, "active_passive_space.png"))

    print("[2] decrement & velocity ...")
    rows = []
    for sp in [None] + sorted(df["species"].unique()):
        d = pp.decrement_fit(df, sp); v = pp.velocity_fit(df, sp)
        if d and v:
            rows.append(dict(species=d["species"], n=d["n"], lambda_mm=round(d["lambda_mm"], 1),
                             decrement_slope=round(d["slope"], 4), decrement_p=round(d["p"], 3),
                             velocity_mm_s=round(v["velocity_mm_s"], 2),
                             delay_dist_r=round(v["r"], 2), delay_dist_p=v["p"]))
    summ = pd.DataFrame(rows)
    summ.to_csv(os.path.join(ROOT, "results", "propagation_summary.csv"), index=False)
    print(summ.to_string(index=False))
    decrement_fig(df, os.path.join(FIG, "decrement_vs_distance.png"))
    delay_fig(df, os.path.join(FIG, "delay_vs_distance.png"))

    print("[2b] independent discriminators ...")
    print("  delay~distance^b :", pp.delay_distance_exponent(df))
    asym = pp.peak_onset_asymmetry(df)
    print(f"  peak-onset asymmetry: pooled median={asym['pooled_median']:.2f}s p={asym['pooled_p']:.1e}")
    print(asym["per_species"].round(2).to_string())
    peak_onset_fig(df, os.path.join(FIG, "peak_onset_asymmetry.png"))

    print("[3] simulation ...")
    sim_fig(os.path.join(FIG, "cable_vs_fhn_sim.png"))

    print("[4] real-example kernel fits ...")
    kernel_example(recs, "Venus Flytrap", os.path.join(FIG, "kernel_example_active.png"), kt)
    kernel_example(recs, "Creeping Inchplant", os.path.join(FIG, "kernel_example_passive.png"), kt)
    print("done")


if __name__ == "__main__":
    main()
