"""Cover-art candidates for the manuscript submission.

Ten visualisations of the two-channel dataset, in the style of a stacked
peak-aligned trace cascade, rendered A4 portrait on black for a journal cover.

The recurring design problem is how to show that every recording is TWO
channels (near and far electrode). Each design solves it differently:
  * by colour            (near vs far in two hues)
  * by concatenation     (near and far joined into one continuous gradient line)
  * by mirroring         (near above the axis, far below)
  * by ribbon            (the near->far gap filled, so attenuation is the shape)

Species identity is carried by a 13-colour palette where the design allows.

Usage:
    python scripts/cover_art.py            # build cache if needed, render all 10
    python scripts/cover_art.py --rebuild  # force re-extract traces from WAVs
"""
from __future__ import annotations

import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, to_rgba, to_rgb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

OUT = os.path.join(ROOT, "results", "figures", "cover")
CACHE = os.path.join(
    os.environ.get("CLAUDE_SCRATCH", os.path.join(ROOT, "results")), "cover_traces.npz")
A4 = (8.27, 11.69)
DPI = 300

# Grid the traces are resampled onto (seconds, relative to each channel's peak)
PRE, POST, FS = 2.0, 5.0, 50.0

# Vivid palette that reads on black; ordered to keep neighbours distinguishable.
SPECIES_COLORS = [
    "#ff3b6b", "#ffb400", "#3ddc84", "#38bdf8", "#c084fc",
    "#f97316", "#22d3ee", "#a3e635", "#fb7185", "#818cf8",
    "#facc15", "#2dd4bf", "#f472b6",
]
NEAR_C, FAR_C = "#4cc9f0", "#f72585"


# --------------------------------------------------------------------------- data

def build_cache(path=CACHE):
    """Extract peak-aligned, normalised near/far traces for every valid recording."""
    from cvplants.io import iter_dataset
    from cvplants.analysis import _response_window
    from cvplants.preprocessing import lowpass, baseline_subtract
    import pandas as pd

    rec_csv = pd.read_csv(os.path.join(ROOT, "results", "recordings.csv"))
    ok = {(r.species, r.recording): r.cv_xcorr_mm_s
          for r in rec_csv[rec_csv["valid"] == True].itertuples()}   # noqa: E712

    grid = np.arange(-PRE, POST, 1.0 / FS)
    near, far, species, cvs = [], [], [], []
    for rec in iter_dataset(os.path.join(ROOT, "data")):
        if rec.n_channels < 2 or (rec.species, rec.name) not in ok:
            continue
        fs = rec.fs
        stim = rec.stim_start if rec.stim_start is not None else 1.0
        bl = (max(0.0, stim - PRE), stim)
        # 15 Hz keeps the sharp biphasic AP of the rapid movers intact
        chans = [lowpass(baseline_subtract(rec.data[:, i], fs, bl), fs, 15.0) for i in (0, 1)]
        w = _response_window(rec)
        i0, i1 = int(w[0] * fs), int(w[1] * fs)
        step = max(1, int(round(fs / FS)))
        segs = [c[i0:i1:step] for c in chans]
        fse = fs / step
        if min(len(s) for s in segs) < int(fse):
            continue
        info = []
        for s in segs:
            sign = np.sign(s[np.argmax(np.abs(s))]) or 1.0
            s = s * sign
            pk = int(np.argmax(s))
            info.append((s, pk, s[pk] if s[pk] else 1.0))
        ni = 0 if info[0][1] <= info[1][1] else 1
        amp = info[ni][2]
        pair = []
        for ci in (ni, 1 - ni):
            s, pk, _ = info[ci]
            tt = (np.arange(len(s)) - pk) / fse
            pair.append(np.interp(grid, tt, s / amp, left=np.nan, right=np.nan))
        if np.all(np.isnan(pair[0])):
            continue
        near.append(pair[0]); far.append(pair[1])
        species.append(rec.species); cvs.append(ok[(rec.species, rec.name)])

    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez_compressed(path, grid=grid, near=np.array(near), far=np.array(far),
                        species=np.array(species), cv=np.array(cvs, dtype=float))
    print(f"cached {len(near)} recordings -> {path}")


def load(path=CACHE, rebuild=False):
    if rebuild or not os.path.exists(path):
        build_cache(path)
    d = np.load(path, allow_pickle=True)
    sp = d["species"].astype(str)
    order = sorted(set(sp))
    cmap = {s: SPECIES_COLORS[i % len(SPECIES_COLORS)] for i, s in enumerate(order)}
    return dict(grid=d["grid"], near=d["near"], far=d["far"], species=sp,
                cv=d["cv"], order=order, cmap=cmap)


# ------------------------------------------------------------------------ helpers

def _canvas(facecolor="black", margin=0.0):
    fig = plt.figure(figsize=A4)
    fig.patch.set_facecolor(facecolor)
    ax = fig.add_axes([margin, margin, 1 - 2 * margin, 1 - 2 * margin])
    ax.set_facecolor(facecolor)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    return fig, ax


def _save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("  wrote", os.path.basename(p))


def _clean(y):
    return np.nan_to_num(y, nan=0.0)


def _gradient_line(ax, x, y, c0, c1, lw=0.8, alpha=1.0, zorder=2, power=1.0):
    """One polyline whose colour sweeps c0 -> c1 along its length.

    power > 1 holds c0 for longer and then fades hard, so on a concatenated
    near|far line the near half keeps its species colour and the fade lands
    almost entirely on the far half.
    """
    pts = np.array([x, y]).T.reshape(-1, 1, 2)
    segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
    cm = LinearSegmentedColormap.from_list("g", [c0, c1])
    lc = LineCollection(segs, cmap=cm, linewidth=lw, alpha=alpha, zorder=zorder)
    lc.set_array(np.linspace(0, 1, len(segs)) ** power)
    ax.add_collection(lc)


def _fit_pair(near, far):
    """Scale a near/far pair by their JOINT max so neither can leave the canvas.

    The cache normalises both channels by the NEAR peak, so a recording whose far
    electrode read larger (electrode coupling; up to 15x here) would shoot far off
    the top and be clipped. Dividing both by the joint max bounds everything to
    [-1, 1] while preserving the far/near ratio that makes attenuation visible.
    """
    a, b = _clean(near), _clean(far)
    m = max(np.max(np.abs(a)), np.max(np.abs(b)), 1e-9)
    return a / m, b / m


def _tint(c, amount=0.62):
    """Lighten toward white (keeps hue, raises luminance)."""
    r, g, b = to_rgb(c)
    return (r + (1 - r) * amount, g + (1 - g) * amount, b + (1 - b) * amount)


def _shade(c, amount=0.55):
    """Darken toward black (keeps hue, drops luminance)."""
    r, g, b = to_rgb(c)
    return (r * (1 - amount), g * (1 - amount), b * (1 - amount))


def _by_species(d):
    """Indices grouped by species, species ordered by median CV (slow -> fast)."""
    med = {s: np.nanmedian(d["cv"][d["species"] == s]) for s in d["order"]}
    order = sorted(d["order"], key=lambda s: med[s])
    return order, {s: np.where(d["species"] == s)[0] for s in order}


def _by_calm(d):
    """Same grouping, but species ordered by how much vertical room they need.

    The quietest species goes FIRST so it sits at the top of the page. Weight is
    RMS over the drawn (jointly-normalised) pair, not peak height: after
    normalisation every trace peaks at exactly 1, so peak height cannot rank them
    -- RMS captures how much ink a species actually puts on the page.
    """
    idx = {s: np.where(d["species"] == s)[0] for s in d["order"]}
    weight = {}
    for s_, ii in idx.items():
        r = []
        for i in ii:
            a, b = _fit_pair(d["near"][i], d["far"][i])
            r.append(float(np.sqrt(np.mean(np.concatenate([a, b]) ** 2))))
        weight[s_] = float(np.median(r)) if r else 0.0
    return sorted(d["order"], key=lambda s_: weight[s_]), idx


# ------------------------------------------------------------------------- designs

def v01_waterfall_channels(d):
    """Classic cascade; near and far in two hues, offset so the delay is visible."""
    fig, ax = _canvas()
    g, n, f = d["grid"], d["near"], d["far"]
    ys, xs = -0.052, 0.006
    for i in range(len(n)):
        ax.plot(g + i * xs, _clean(n[i]) + i * ys, lw=0.7, color=NEAR_C, alpha=0.95)
        ax.plot(g + i * xs, _clean(f[i]) + i * ys, lw=0.7, color=FAR_C, alpha=0.8)
    ax.set_xlim(-1.6, 4.2); ax.set_ylim(len(n) * ys - 0.6, 1.4)
    _save(fig, "01_waterfall_channels.png")


def v02_waterfall_species(d):
    """The same cascade, grouped and coloured by species (slow -> fast down the page)."""
    fig, ax = _canvas()
    g = d["grid"]
    order, idx = _by_species(d)
    ys, xs, row = -0.055, 0.006, 0
    for s in order:
        for i in idx[s]:
            ax.plot(g + row * xs, _clean(d["near"][i]) + row * ys,
                    lw=0.8, color=d["cmap"][s], alpha=0.95)
            row += 1
        row += 1.5   # breathing room between species
    ax.set_xlim(-1.6, 4.4); ax.set_ylim(row * ys - 0.6, 1.4)
    _save(fig, "02_waterfall_species.png")


def v03_concatenated(d):
    """THE two-channel answer: near and far joined into ONE continuous line whose
    colour sweeps from the near hue to the far hue at the join."""
    fig, ax = _canvas()
    g = d["grid"]
    span = g[-1] - g[0]
    gap = 0.45
    order, idx = _by_species(d)
    ys, row = -0.058, 0
    for s in order:
        for i in idx[s]:
            x = np.concatenate([g, g + span + gap])
            y = np.concatenate([_clean(d["near"][i]), _clean(d["far"][i])]) + row * ys
            _gradient_line(ax, x, y, NEAR_C, FAR_C, lw=0.75)
            row += 1
        row += 1.5
    ax.set_xlim(g[0] - 0.3, g[0] + 2 * span + gap + 0.3)
    ax.set_ylim(row * ys - 0.6, 1.4)
    _save(fig, "03_concatenated_two_channel.png")


def v04_radial(d):
    """Polar burst: each recording a spoke, hue = species. Inner ring = near,
    outer ring = far in a heavily tinted version of the same hue, so the fade
    reads the same way as the fused design. Pairs are jointly normalised so one
    large-far recording cannot swing across its neighbours."""
    fig = plt.figure(figsize=A4)
    fig.patch.set_facecolor("black")
    m = 0.055
    ax = fig.add_axes([m, m, 1 - 2 * m, 1 - 2 * m], projection="polar")
    ax.set_facecolor("black")
    ax.set_xticks([]); ax.set_yticks([])
    ax.spines["polar"].set_visible(False)
    order, idx = _by_calm(d)
    total = sum(len(idx[s_]) for s_ in order)
    k, rmax = 0, 0.0
    for s_ in order:
        col = d["cmap"][s_]
        far_c = _tint(col, 0.62)
        for i in idx[s_]:
            a, b = _fit_pair(d["near"][i], d["far"][i])
            th = 2 * np.pi * k / total
            u = np.linspace(0, 1, len(a))
            r_in = 0.66 + 0.60 * u
            r_out = 1.40 + 0.60 * u
            ax.plot(th + a * 0.17, r_in, lw=0.85, color=col, alpha=0.95)
            ax.plot(th + b * 0.17, r_out, lw=0.8, color=far_c, alpha=0.75)
            rmax = max(rmax, r_out.max())
            k += 1
    ax.set_ylim(0, rmax * 1.06)     # headroom so no spoke touches the edge
    _save(fig, "04_radial_burst.png")


def v05_butterfly(d):
    """Mirror: near traces rise above the spine, far traces fall below it."""
    fig, ax = _canvas()
    g = d["grid"]
    order, idx = _by_species(d)
    xs, row = 0.0, 0
    n_tot = len(d["near"])
    for s in order:
        for i in idx[s]:
            x = g + (row - n_tot / 2) * 0.004
            base = 0.0
            ax.plot(x, base + _clean(d["near"][i]) * 0.9, lw=0.5, color=NEAR_C, alpha=0.22)
            ax.plot(x, base - _clean(d["far"][i]) * 0.9, lw=0.5, color=FAR_C, alpha=0.22)
            row += 1
    ax.axhline(0, color="white", lw=0.4, alpha=0.5)
    ax.set_xlim(-1.8, 4.6); ax.set_ylim(-1.5, 1.5)
    _save(fig, "05_butterfly_mirror.png")


def v06_species_grid(d):
    """Small multiples: one cell per species, its recordings stacked inside."""
    order, idx = _by_species(d)
    ncol, nrow = 3, int(np.ceil(len(order) / 3))
    fig = plt.figure(figsize=A4); fig.patch.set_facecolor("black")
    g = d["grid"]
    for k, s in enumerate(order):
        ax = fig.add_subplot(nrow, ncol, k + 1)
        ax.set_facecolor("black"); ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
        ys = -0.16
        for j, i in enumerate(idx[s]):
            ax.plot(g, _clean(d["near"][i]) + j * ys, lw=0.7, color=d["cmap"][s], alpha=0.95)
            ax.plot(g, _clean(d["far"][i]) + j * ys, lw=0.6, color="white", alpha=0.30)
        ax.set_xlim(-1.5, 4.0); ax.set_ylim(len(idx[s]) * ys - 0.5, 1.3)
        ax.set_title(s, color=d["cmap"][s], fontsize=7, pad=3)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.97, bottom=0.02, wspace=0.08, hspace=0.22)
    _save(fig, "06_species_grid.png")


def v07_ribbon(d):
    """Fill the near->far gap: the ribbon's thickness IS the attenuation."""
    fig, ax = _canvas()
    g = d["grid"]
    order, idx = _by_species(d)
    # wider spacing + low fill alpha: the ribbon should read as a gap, not a wash
    # amplitude scaled down: at full scale each trace spans ~1.0 while rows sit
    # ~0.1 apart, so the fills stacked into an opaque wash
    amp, ys, row = 0.42, -0.088, 0
    for s in order:
        col = d["cmap"][s]
        for i in idx[s]:
            a = _clean(d["near"][i]) * amp + row * ys
            b = _clean(d["far"][i]) * amp + row * ys
            ax.fill_between(g, a, b, color=to_rgba(col, 0.22), lw=0)
            ax.plot(g, a, lw=0.65, color=col, alpha=0.95)
            ax.plot(g, b, lw=0.45, color="white", alpha=0.35)
            row += 1
        row += 0.8
    ax.set_xlim(-1.6, 4.2); ax.set_ylim(row * ys - 0.6, 1.4)
    _save(fig, "07_attenuation_ribbon.png")


def v08_spiral(d):
    """Traces laid along an Archimedean spiral, near hue into far hue."""
    fig, ax = _canvas()
    g = d["grid"]
    n = len(d["near"])
    turns, k = 2.4, 0
    order, idx = _by_species(d)
    for s in order:
        for i in idx[s]:
            frac = k / n
            th0 = 2 * np.pi * turns * frac
            rad = 0.25 + 1.55 * frac
            u = np.linspace(0, 1, len(g))
            dth = (u - 0.5) * 0.30
            th = th0 + dth
            amp = _clean(d["near"][i]) * 0.26
            x = (rad + amp) * np.cos(th)
            y = (rad + amp) * np.sin(th)
            _gradient_line(ax, x, y, d["cmap"][s], "#ffffff", lw=1.05, alpha=0.92)
            k += 1
    ax.set_xlim(-2.0, 2.0); ax.set_ylim(-2.6, 2.6); ax.set_aspect("equal")
    _save(fig, "08_spiral.png")


def v09_velocity_cascade(d):
    """Sorted by conduction velocity, coloured on a continuous speed ramp:
    the slow wound potentials at the top, the fast action potentials at the bottom."""
    fig, ax = _canvas()
    g = d["grid"]
    cv = np.nan_to_num(d["cv"], nan=0.0)
    idx = np.argsort(cv)
    lo, hi = np.percentile(cv[cv > 0], [5, 95])
    cm = LinearSegmentedColormap.from_list("v", ["#1e3a8a", "#22d3ee", "#a3e635", "#facc15", "#ff3b6b"])
    ys, xs = -0.055, 0.005
    for row, i in enumerate(idx):
        c = cm(np.clip((cv[i] - lo) / (hi - lo + 1e-9), 0, 1))
        ax.plot(g + row * xs, _clean(d["near"][i]) + row * ys, lw=0.8, color=c, alpha=0.95)
        ax.plot(g + row * xs, _clean(d["far"][i]) + row * ys, lw=0.55, color=c, alpha=0.4)
    ax.set_xlim(-1.6, 4.4); ax.set_ylim(len(idx) * ys - 0.6, 1.4)
    _save(fig, "09_velocity_cascade.png")


def v10_overlay(d):
    """Every recording superimposed: the population envelope, near over far."""
    fig, ax = _canvas()
    g = d["grid"]
    for i in range(len(d["near"])):
        ax.plot(g, _clean(d["far"][i]), lw=0.5, color=FAR_C, alpha=0.13)
    for i in range(len(d["near"])):
        ax.plot(g, _clean(d["near"][i]), lw=0.5, color=NEAR_C, alpha=0.16)
    for arr, c, lw in [(d["far"], FAR_C, 2.4), (d["near"], NEAR_C, 2.4)]:
        ax.plot(g, np.nanmedian(arr, axis=0), lw=lw, color="white", alpha=0.95, zorder=5)
        ax.plot(g, np.nanmedian(arr, axis=0), lw=lw * 2.6, color=c, alpha=0.25, zorder=4)
    ax.set_xlim(-1.6, 4.2); ax.set_ylim(-0.85, 1.35)
    _save(fig, "10_population_overlay.png")


def _species_concat(d, out, mode="tint", divider=True):
    """2 x 3: the concatenated near|far line of design 03, carrying the species
    palette of design 02. Hue = species; luminance sweeps along the line so the
    near->far join reads without spending a second hue on it.

    Both channels are scaled by their joint max (_fit_pair) so nothing can leave
    the canvas, species are ordered quietest-first so the top of the page stays
    clear, and the axis limits are taken from the drawn data plus a margin -- so
    no trace is cropped.
    """
    fig, ax = _canvas(margin=0.055)
    g = d["grid"]
    span = g[-1] - g[0]
    gap = 0.5
    order, idx = _by_calm(d)
    ys, row = -0.058, 0
    lo, hi = 0.0, 0.0
    for s_ in order:
        col = d["cmap"][s_]
        if mode == "tint":
            c0, c1 = col, _tint(col, 0.70)          # full colour -> pale, hue kept
        else:
            c0, c1 = _tint(col, 0.25), _shade(col, 0.72)
        for i in idx[s_]:
            a, b = _fit_pair(d["near"][i], d["far"][i])
            x = np.concatenate([g, g + span + gap])
            y = np.concatenate([a, b]) + row * ys
            # power=2.2 keeps the near half saturated and drops the fade on the far half
            _gradient_line(ax, x, y, c0, c1, lw=0.8, power=1.9)
            lo = min(lo, float(y.min())); hi = max(hi, float(y.max()))
            row += 1
        row += 1.6
    if divider:
        xm = g[-1] + gap / 2
        ax.axvline(xm, color="#4a4a4a", lw=0.6, alpha=0.6, zorder=0)
    padx, pady = 0.35, 0.12 * (hi - lo) / 10.0 + 0.25
    ax.set_xlim(g[0] - padx, g[0] + 2 * span + gap + padx)
    ax.set_ylim(lo - pady, hi + pady)
    _save(fig, out)


def v11_species_concat_tint(d):
    """Near = full species colour, far = the same hue tinted toward white."""
    _species_concat(d, "11_species_concat_tint.png", mode="tint")


def v12_species_concat_deep(d):
    """Near = pale species tint, far = the same hue deepened (reads as attenuation)."""
    _species_concat(d, "12_species_concat_deep.png", mode="deep")


DESIGNS = [v01_waterfall_channels, v02_waterfall_species, v03_concatenated,
           v04_radial, v05_butterfly, v06_species_grid, v07_ribbon,
           v08_spiral, v09_velocity_cascade, v10_overlay,
           v11_species_concat_tint, v12_species_concat_deep]


def main():
    d = load(rebuild="--rebuild" in sys.argv)
    print(f"{len(d['near'])} recordings, {len(d['order'])} species -> {OUT}")
    for fn in DESIGNS:
        fn(d)
    contact_sheet()




def contact_sheet():
    """One landscape sheet with all ten candidates as labelled thumbnails."""
    from PIL import Image
    files = sorted(f for f in os.listdir(OUT) if f.endswith(".png") and f[0].isdigit())
    ncol = 5
    nrow = int(np.ceil(len(files) / ncol))
    fig = plt.figure(figsize=(16.5, 5.5 * nrow))
    fig.patch.set_facecolor("#0b0b0b")
    for k, f in enumerate(files):
        ax = fig.add_subplot(nrow, ncol, k + 1)
        ax.imshow(Image.open(os.path.join(OUT, f)))
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_color("#333")
        name = f[:-4].replace("_", " ")
        ax.set_title(name, color="white", fontsize=8, pad=4)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.01, wspace=0.06, hspace=0.12)
    fig.suptitle(f"Cover-art candidates ({len(files)}) — 13 species, 166 two-channel recordings",
                 color="white", fontsize=13, y=0.99)
    p = os.path.join(OUT, "_contact_sheet.png")
    fig.savefig(p, dpi=110, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("  wrote", os.path.basename(p))


if __name__ == "__main__":
    main()
