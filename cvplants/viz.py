"""Figures for the conduction-velocity deep dive."""
from __future__ import annotations

import os

import numpy as np
import matplotlib.pyplot as plt

from .io import Recording
from .preprocessing import preprocess_channel
from .analysis import analyze_recording, _response_window, CUTOFF_HZ, BASELINE_S

NEAR_C, FAR_C = "#1f77b4", "#d62728"


def processed_channels(rec: Recording, cutoff: float = CUTOFF_HZ,
                       baseline_s: float = BASELINE_S):
    """Return (t, ch0, ch1) baseline-subtracted + low-passed for plotting."""
    stim = rec.stim_start if rec.stim_start is not None else 1.0
    bl = (max(0.0, stim - baseline_s), stim)
    ch0 = preprocess_channel(rec.data[:, 0], rec.fs, cutoff, bl)
    ch1 = preprocess_channel(rec.data[:, 1], rec.fs, cutoff, bl)
    t = np.arange(len(ch0)) / rec.fs
    return t, ch0, ch1


def plot_recording(rec: Recording, ax=None, cutoff: float = CUTOFF_HZ):
    """Detail view of one recording: near vs far channel, stim window, delay."""
    res = analyze_recording(rec, cutoff=cutoff)
    t, ch0, ch1 = processed_channels(rec, cutoff)
    chans = {0: ch0, 1: ch1}
    if ax is None:
        _, ax = plt.subplots(figsize=(11, 4))

    if res.get("near_channel") is not None:
        nc, fc = res["near_channel"], res["far_channel"]
        ax.plot(t, chans[nc], color=NEAR_C, lw=0.9, label=f"near (ch{nc})")
        ax.plot(t, chans[fc], color=FAR_C, lw=0.9, label=f"far (ch{fc})")
    else:
        ax.plot(t, ch0, color=NEAR_C, lw=0.9, label="ch0")
        ax.plot(t, ch1, color=FAR_C, lw=0.9, label="ch1")

    if rec.stim_start is not None and rec.stim_stop is not None:
        ax.axvspan(rec.stim_start, rec.stim_stop, color="gold", alpha=0.25,
                   label="stimulation")
    elif rec.stim_start is not None:
        ax.axvline(rec.stim_start, color="gold", lw=1.5)

    title = f"{rec.species}  |  {rec.name}"
    bits = []
    if res.get("distance_mm"):
        bits.append(f"d={res['distance_mm']}mm")
    if res.get("xcorr_delay_s") == res.get("xcorr_delay_s"):
        bits.append(f"delay={res['xcorr_delay_s']:.2f}s")
    cv = res.get("cv_xcorr_mm_s")
    if cv is not None and cv == cv:
        bits.append(f"CV={cv:.1f}mm/s")
    if res.get("attenuation_far_near") == res.get("attenuation_far_near"):
        bits.append(f"att={res['attenuation_far_near']:.2f}")
    if res.get("flags"):
        bits.append(f"[{res['flags']}]")
    ax.set_title(title + ("\n" + "  ".join(bits) if bits else ""), fontsize=9)
    ax.set_xlabel("time (s)"); ax.set_ylabel("amplitude (a.u.)")
    ax.legend(fontsize=7, loc="upper right")
    return res


def plot_species_grid(recs, out_path, cutoff: float = CUTOFF_HZ, per_species=1):
    """One example recording per species, stacked, for a quick visual overview."""
    by_sp = {}
    for r in recs:
        by_sp.setdefault(r.species, []).append(r)
    species = sorted(by_sp)
    n = len(species) * per_species
    fig, axes = plt.subplots(n, 1, figsize=(11, 2.4 * n))
    axes = np.atleast_1d(axes)
    i = 0
    for sp in species:
        # prefer a recording that yields a valid result
        chosen, fallback = [], by_sp[sp]
        for r in fallback:
            if analyze_recording(r, cutoff=cutoff).get("valid"):
                chosen.append(r)
            if len(chosen) >= per_species:
                break
        if not chosen:
            chosen = fallback[:per_species]
        for r in chosen:
            plot_recording(r, ax=axes[i], cutoff=cutoff)
            i += 1
    for j in range(i, n):
        axes[j].axis("off")
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)
    return out_path


def plot_cv_by_species(df, out_path):
    """Boxplot + jittered points of xcorr CV per species (valid recordings)."""
    v = df[(df["valid"] == True) & df["cv_xcorr_mm_s"].notna()]  # noqa: E712
    if v.empty:
        return None
    order = (v.groupby("species")["cv_xcorr_mm_s"].median()
             .sort_values().index.tolist())
    data = [v[v["species"] == s]["cv_xcorr_mm_s"].values for s in order]
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.boxplot(data, vert=True, showfliers=False, patch_artist=True,
               boxprops=dict(facecolor="#cfe3f5"),
               medianprops=dict(color="#d62728"))
    for i, d in enumerate(data, 1):
        x = np.random.normal(i, 0.05, size=len(d))
        ax.scatter(x, d, s=18, color="#25507a", alpha=0.7, edgecolor="k", lw=0.3)
    labels = [f"{s}\n(n={len(d)})" for s, d in zip(order, data)]
    ax.set_xticks(range(1, len(order) + 1)); ax.set_xticklabels(labels, rotation=40, ha="right")
    ax.set_ylabel("conduction velocity (mm/s)")
    ax.set_title("Conduction velocity by species (cross-correlation delay, valid recordings)")
    ax.grid(axis="y", ls="--", alpha=0.4)
    fig.tight_layout(); fig.savefig(out_path, dpi=120); plt.close(fig)
    return out_path


def plot_transformation(df, out_path):
    """How the signal changes near -> far: attenuation, broadening, similarity."""
    v = df[df["valid"] == True]  # noqa: E712
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.3))

    a = v["attenuation_far_near"].dropna()
    axes[0].hist(a[a < 5], bins=25, color="#4a90d9", edgecolor="k", lw=0.3)
    axes[0].axvline(1, color="k", ls="--"); axes[0].axvline(a.median(), color="#d62728")
    axes[0].set_title(f"Amplitude ratio far/near\nmedian={a.median():.2f}")
    axes[0].set_xlabel("far peak / near peak")

    b = v["broadening_far_near"].dropna()
    axes[1].hist(b[(b > 0) & (b < 5)], bins=25, color="#4a90d9", edgecolor="k", lw=0.3)
    axes[1].axvline(1, color="k", ls="--"); axes[1].axvline(b.median(), color="#d62728")
    axes[1].set_title(f"Width ratio far/near (FWHM)\nmedian={b.median():.2f}")
    axes[1].set_xlabel("far FWHM / near FWHM")

    c = v["xcorr_corr"].dropna()
    axes[2].hist(c, bins=25, color="#4a90d9", edgecolor="k", lw=0.3)
    axes[2].axvline(c.median(), color="#d62728")
    axes[2].set_title(f"Waveform similarity (max r)\nmedian={c.median():.2f}")
    axes[2].set_xlabel("normalised cross-correlation")

    for ax in axes:
        ax.set_ylabel("recordings"); ax.grid(axis="y", ls="--", alpha=0.4)
    fig.suptitle("Signal transformation from near to far electrode", fontsize=12)
    fig.tight_layout(); fig.savefig(out_path, dpi=120); plt.close(fig)
    return out_path


def plot_transformation_by_species(df, out_path, order_by="attenuation_far_near"):
    """Bar (mean ± std) + per-recording scatter for the three near->far metrics,
    with species on the x-axis. Species are ordered by median `order_by` and the
    same order is used across all three panels so they line up."""
    v = df[df["valid"] == True]  # noqa: E712
    metrics = [
        ("attenuation_far_near", "Amplitude ratio  far / near", 1.0),
        ("broadening_far_near",  "Width ratio  far / near (FWHM)", 1.0),
        ("xcorr_corr",           "Waveform similarity  (max r)", None),
    ]
    order = (v.groupby("species")[order_by].median()
             .sort_values().index.tolist())
    x = np.arange(len(order))

    fig, axes = plt.subplots(3, 1, figsize=(12, 13), sharex=True)
    for ax, (col, title, ref) in zip(axes, metrics):
        means, stds, groups = [], [], []
        for s in order:
            vals = v[v["species"] == s][col].dropna().values
            groups.append(vals)
            means.append(np.mean(vals) if len(vals) else np.nan)
            stds.append(np.std(vals) if len(vals) else np.nan)
        ax.bar(x, means, yerr=stds, capsize=4, color="#cfe3f5",
               edgecolor="#25507a", linewidth=1.0, zorder=1,
               error_kw=dict(ecolor="#555", lw=1.2))
        for i, vals in enumerate(groups):
            if len(vals):
                jx = np.random.normal(i, 0.06, size=len(vals))
                ax.scatter(jx, vals, s=22, color="#25507a", alpha=0.75,
                           edgecolor="k", linewidth=0.3, zorder=3)
        if ref is not None:
            ax.axhline(ref, color="k", ls="--", lw=1, zorder=0)
        ax.set_ylabel(title, fontsize=10)
        ax.grid(axis="y", ls="--", alpha=0.4)
    counts = [len(v[v["species"] == s]) for s in order]
    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels([f"{s}\n(n={c})" for s, c in zip(order, counts)],
                             rotation=40, ha="right")
    fig.suptitle("Near→far signal transformation by species "
                 "(bar = mean ± SD, dots = recordings)", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.99))
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def plot_distance_delay(df, out_path, species="Marijuana"):
    """For a species with known electrode spacing: distance vs delay (slope=CV)."""
    v = df[(df["species"] == species) & (df["valid"] == True)  # noqa: E712
           & df["distance_mm"].notna() & df["xcorr_delay_s"].notna()]
    if len(v) < 2:
        return None
    fig, ax = plt.subplots(figsize=(6.5, 5))
    ax.scatter(v["xcorr_delay_s"], v["distance_mm"], s=45, color="#25507a",
               edgecolor="k", zorder=3)
    # CV as slope through origin (distance = CV * delay)
    slope = np.sum(v["distance_mm"] * v["xcorr_delay_s"]) / np.sum(v["xcorr_delay_s"] ** 2)
    xs = np.linspace(0, v["xcorr_delay_s"].max() * 1.05, 50)
    ax.plot(xs, slope * xs, color="#d62728", label=f"CV ≈ {slope:.1f} mm/s (slope)")
    ax.set_xlabel("inter-channel delay (s)"); ax.set_ylabel("electrode distance (mm)")
    ax.set_title(f"{species}: distance vs propagation delay")
    ax.legend(); ax.grid(ls="--", alpha=0.4)
    fig.tight_layout(); fig.savefig(out_path, dpi=120); plt.close(fig)
    return out_path
