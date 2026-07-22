"""Channel diagnostics: self-aligned per-channel averages + common-mode check.

Two problems with aligning both channels on the NEAR peak (the previous figure):
  * it smears the far average, because the near->far delay varies recording to
    recording, and
  * it presupposes the near/far assignment, which flips for the fast species.

Here each PHYSICAL channel (ch0, ch1 — unambiguous) is aligned on its OWN peak
and averaged, then the two are drawn with a fixed horizontal gap so both mean
waveforms are visible and comparable. Thin = recordings, thick = mean ± SD.
A companion panel reports the pre-stimulus (baseline) zero-lag correlation, which
is high only when the two channels share a common-mode / reference signal.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cvplants.io import iter_dataset, SPECIES_FAMILY, FAMILY_COLORS   # noqa: E402
from cvplants.analysis import _response_window                        # noqa: E402
from cvplants.preprocessing import lowpass, baseline_subtract         # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "results", "figures")
C0, C1 = "#1f77b4", "#d62728"


def _type_lookup():
    f = os.path.join(ROOT, "results", "potential_types.csv")
    if not os.path.exists(f):
        return {}
    d = pd.read_csv(f)
    return {(r.species, r.recording): r.potential_type for r in d.itertuples()}


def channel_segments(pre=3.0, post=6.0, target_fs=50.0, cutoff=2.0):
    grid = np.arange(-pre, post, 1.0 / target_fs)
    per = {}          # species -> ([near self-aligned], [far self-aligned])
    ptypes = {}       # species -> [AP-like / VP-like per recording]
    base_r = {}       # species -> [pre-stim zero-lag r]
    tlook = _type_lookup()
    for rec in iter_dataset(os.path.join(ROOT, "data")):
        if rec.n_channels < 2:
            continue
        ptypes.setdefault(rec.species, []).append(tlook.get((rec.species, rec.name), "AP-like"))
        fs = rec.fs
        stim = rec.stim_start if rec.stim_start is not None else 1.0
        bl = (max(0.0, stim - pre), stim)
        c0 = lowpass(baseline_subtract(rec.data[:, 0], fs, bl), fs, cutoff)
        c1 = lowpass(baseline_subtract(rec.data[:, 1], fs, bl), fs, cutoff)
        win = _response_window(rec)
        i0, i1 = int(win[0] * fs), int(win[1] * fs)
        step = max(1, int(round(fs / target_fs)))
        seg0, seg1 = c0[i0:i1:step], c1[i0:i1:step]
        fse = fs / step
        per.setdefault(rec.species, ([], []))
        if len(seg0) < int(fse) or len(seg1) < int(fse):
            per[rec.species][0].append(np.full_like(grid, np.nan))
            per[rec.species][1].append(np.full_like(grid, np.nan))
            continue
        # sign-correct each channel and find its own peak
        info = []
        for seg in (seg0, seg1):
            sign = np.sign(seg[np.argmax(np.abs(seg))]) or 1.0
            s = seg * sign
            pk = int(np.argmax(s))
            info.append((s, pk, s[pk] if s[pk] != 0 else 1.0))
        # near = earlier-peaking channel; normalise BOTH by the NEAR peak so the
        # far channel's amplitude drop (attenuation) is visible, then align each
        # channel on its own peak in time.
        near_i = 0 if info[0][1] <= info[1][1] else 1
        near_amp = info[near_i][2]
        for role, ci in enumerate((near_i, 1 - near_i)):   # 0 = near, 1 = far
            s, pk, _ = info[ci]
            tt = (np.arange(len(s)) - pk) / fse
            per[rec.species][role].append(np.interp(grid, tt, s / near_amp, left=np.nan, right=np.nan))
        bi0, bi1 = int(bl[0] * fs), int(bl[1] * fs)
        if bi1 - bi0 > 10:
            a, b = c0[bi0:bi1], c1[bi0:bi1]
            base_r.setdefault(rec.species, []).append(float(np.corrcoef(a, b)[0, 1]))
    return grid, per, base_r, ptypes


def main():
    df = pd.read_csv(os.path.join(ROOT, "results", "recordings.csv"))
    grid, per, base_r, ptypes = channel_segments()
    AP_C, VP_C = "#2a9d2a", "#b060c0"   # thin-trace colour by potential type
    v = df[df["valid"] == True].copy()  # noqa: E712
    v["asym"] = v["peak_delay_s"] - v["onset_delay_s"]
    order = [s for s in v.groupby("species")["asym"].median().sort_values().index if s in per]

    gap = (grid[-1] - grid[0]) + 2.0
    ncol = 3
    nrow = int(np.ceil(len(order) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(15, 3.0 * nrow), sharey=True)
    axes = np.atleast_1d(axes).ravel()
    for ax, sp in zip(axes, order):
        A0 = np.array(per[sp][0]); A1 = np.array(per[sp][1])
        types = ptypes.get(sp, ["AP-like"] * len(A0))
        for M, xoff, c, lab in [(A0, 0.0, C0, "near"), (A1, gap, C1, "far")]:
            for row, ty in zip(M, types):    # thin traces coloured by potential type
                tc = AP_C if ty == "AP-like" else VP_C
                ax.plot(grid + xoff, np.clip(row, -0.7, 1.5), color=tc, lw=0.35, alpha=0.35)
            # median + IQR band: robust to the few far>>near electrode-coupling outliers
            med = np.nanmedian(M, axis=0)
            q1 = np.nanpercentile(M, 25, axis=0); q3 = np.nanpercentile(M, 75, axis=0)
            ax.fill_between(grid + xoff, q1, q3, color=c, alpha=0.25, lw=0)
            ax.plot(grid + xoff, med, color=c, lw=2.3, label=lab)
        br = np.nanmedian(base_r.get(sp, [np.nan]))
        att = np.nanmedian(np.nanmax(A1, axis=1)) if len(A1) else np.nan
        ax.set_title(f"{sp}  (far/near ≈ {att:.2f})", fontsize=9)
        ax.axvline(0, color=C0, ls=":", lw=0.6); ax.axvline(gap, color=C1, ls=":", lw=0.6)
        ax.axhline(1.0, color="#888", ls="--", lw=0.6); ax.axhline(0, color="#888", lw=0.5)
        ax.set_ylim(-0.7, 1.5)
        ax.legend(fontsize=7, loc="upper right")
    for j in range(len(order), len(axes)):
        axes[j].axis("off")
    from matplotlib.lines import Line2D
    axes[0].legend(handles=[Line2D([0], [0], color=AP_C, lw=2, label="AP-like recording"),
                            Line2D([0], [0], color=VP_C, lw=2, label="VP-like recording"),
                            Line2D([0], [0], color=C0, lw=2.3, label="near median"),
                            Line2D([0], [0], color=C1, lw=2.3, label="far median")],
                   fontsize=7, loc="upper left")
    fig.suptitle("Near vs far response, each self-aligned on its own peak (arbitrary gap between them),\n"
                 "both normalised to the NEAR peak (far amplitude drop visible). Thin traces coloured by "
                 "potential type (AP-like green / VP-like purple); thick = near/far median, band = IQR.",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    out = os.path.join(FIG, "self_aligned_channels.png")
    fig.savefig(out, dpi=120); plt.close(fig)
    print("wrote", out)

    # common-mode summary figure: baseline r per species
    fig2, ax = plt.subplots(figsize=(11, 5))
    sp_order = sorted(base_r, key=lambda s: np.nanmedian(base_r[s]), reverse=True)
    for i, sp in enumerate(sp_order):
        vals = np.array(base_r[sp]); c = FAMILY_COLORS.get(SPECIES_FAMILY.get(sp, ""), "#888")
        ax.scatter(np.random.normal(i, 0.07, len(vals)), vals, s=18, color=c, alpha=0.5, edgecolor="none")
        ax.scatter(i, np.nanmedian(vals), s=90, color=c, edgecolor="k", zorder=5)
    ax.axhline(0, color="k", lw=0.6); ax.axhline(0.5, color="r", ls="--", lw=1)
    ax.set_xticks(range(len(sp_order))); ax.set_xticklabels(sp_order, rotation=40, ha="right", fontsize=8)
    ax.set_ylabel("pre-stimulus zero-lag correlation ch0↔ch1")
    ax.set_title("Baseline common-mode coupling per species (r>0.5 dashed = shared-reference / crosstalk regime)")
    ax.grid(axis="y", ls="--", alpha=0.3)
    fig2.tight_layout(); fig2.savefig(os.path.join(FIG, "baseline_common_mode.png"), dpi=120); plt.close(fig2)
    print("wrote baseline_common_mode.png")


if __name__ == "__main__":
    main()
