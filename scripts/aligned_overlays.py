"""Per-species aligned overlays: thin raw traces + mean ± shaded SD (thick).

Each valid recording's near and far response is aligned on the near-channel peak
(t=0) and normalised to the near peak amplitude, then interpolated onto a common
time grid. Thin lines = individual recordings; thick line + shaded band = mean ±
SD. Species are ordered active→passive (by peak-onset asymmetry) so the grid
reads from shape-preserving (Venus, Mimosa) to dispersive (mints, Inchplant).
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cvplants.io import iter_dataset                     # noqa: E402
from cvplants.propagation import near_far_traces         # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "results", "figures")
NEAR_C, FAR_C = "#1f77b4", "#d62728"


def collect(recs, pre=3.0, post=8.0, target_fs=50.0):
    grid = np.arange(-pre, post, 1.0 / target_fs)
    data = {}
    for rec in recs:
        nf = near_far_traces(rec, target_fs=target_fs)
        if nf is None:
            continue
        t, near, far, fs_eff, res = nf
        pk = int(np.argmax(near))
        amp = near[pk] if near[pk] != 0 else 1.0
        tt = (np.arange(len(near)) - pk) / fs_eff
        ni = np.interp(grid, tt, near / amp, left=np.nan, right=np.nan)
        fi = np.interp(grid, tt, far / amp, left=np.nan, right=np.nan)
        data.setdefault(rec.species, ([], []))
        data[rec.species][0].append(ni)
        data[rec.species][1].append(fi)
    return grid, data


def order_species(df):
    v = df[df["valid"] == True].copy()  # noqa: E712
    v["asym"] = v["peak_delay_s"] - v["onset_delay_s"]
    return v.groupby("species")["asym"].median().sort_values().index.tolist()


def main():
    df = pd.read_csv(os.path.join(ROOT, "results", "recordings.csv"))
    recs = list(iter_dataset(os.path.join(ROOT, "data")))
    grid, data = collect(recs)
    order = [s for s in order_species(df) if s in data]

    ncol = 3
    nrow = int(np.ceil(len(order) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(15, 3.1 * nrow), sharex=True)
    axes = np.atleast_1d(axes).ravel()
    for ax, sp in zip(axes, order):
        N = np.array(data[sp][0]); F = np.array(data[sp][1])
        for row in N:
            ax.plot(grid, row, color=NEAR_C, lw=0.3, alpha=0.25)
        for row in F:
            ax.plot(grid, row, color=FAR_C, lw=0.3, alpha=0.25)
        for M, c, lab in [(N, NEAR_C, "near"), (F, FAR_C, "far")]:
            mean = np.nanmean(M, axis=0); sd = np.nanstd(M, axis=0)
            ax.fill_between(grid, mean - sd, mean + sd, color=c, alpha=0.22, lw=0)
            ax.plot(grid, mean, color=c, lw=2.2, label=lab)
        ax.axvline(0, color="k", ls=":", lw=0.7)
        ax.axhline(0, color="k", lw=0.5)
        ax.set_title(f"{sp}  (n={len(N)})", fontsize=9)
        ax.set_ylim(-1.2, 1.4)
        ax.legend(fontsize=7, loc="upper right")
    for j in range(len(order), len(axes)):
        axes[j].axis("off")
    for ax in axes[-ncol:]:
        ax.set_xlabel("time relative to near peak (s)")
    for k in range(0, len(axes), ncol):
        axes[k].set_ylabel("amplitude\n(norm. to near peak)")
    fig.suptitle("Aligned near→far responses per species (thin = recordings, thick = mean ± SD)\n"
                 "ordered active/shape-preserving → passive/dispersive",
                 fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    out = os.path.join(FIG, "aligned_overlays_by_species.png")
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    main()
