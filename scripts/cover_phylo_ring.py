"""Cover candidate: a circular phylogram with the flame stimulus at the origin.

Reading outward from the centre:
    1. the flame          - the stimulus, at the exact centre
    2. the tree           - a circular cladogram (APG IV topology) placing the
                            13 species by descent, so neighbouring sectors are
                            evolutionary neighbours
    3. the near ring      - the electrode closest to the stimulus
    4. the far ring       - the downstream electrode, same hue, tinted

So the composition follows the physics: the stimulus is at the centre and every
signal propagates outward through the near electrode and then the far one, while
the angular position of each trace is the species' place in the tree.

Angular sector width is proportional to a species' recording count; leaf order
comes from the topology, so families occupy contiguous arcs.

Usage:  python scripts/cover_phylo_ring.py   (add --labels-inside to move the
        species names into the middle band instead of the outer rim)
"""
from __future__ import annotations

import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
import matplotlib.patheffects as pe

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from cover_art import load, _fit_pair, _tint, SPECIES_COLORS      # noqa: E402
from cvplants.io import SPECIES_LATIN                             # noqa: E402
from plant_icons import draw_icon                                 # noqa: E402

OUT = os.path.join(ROOT, "results", "figures", "cover")
A4 = (8.27, 11.69)
DPI = 300

# ---------------------------------------------------------------- the topology
# APG IV. Tuples are (clade label, [children]); strings are leaf species.
TREE = ("angiosperms", [
    ("monocots", ["Creeping Inchplant"]),
    ("eudicots", [
        ("Caryophyllales", ["Venus Flytrap"]),
        ("rosids", [
            ("fabids", [
                ("Fabales", ["Sensitive Mimosa"]),
                ("Rosales", ["Marijuana"]),
            ]),
            ("Sapindales", ["Ruda"]),
        ]),
        ("asterids", [
            ("Solanaceae", [
                ("Capsicum", ["Chilean Chile", "Ornamental Chile"]),
                ("Solanum", ["Tomato"]),
            ]),
            ("Lamiaceae", [
                ("Ocimeae", ["Basil", "Argentian Dollar"]),
                ("Mentheae", [
                    ("Salvia", ["Rosemary"]),
                    ("Menthinae", ["Mint", "Hierbabuena"]),
                ]),
            ]),
        ]),
    ]),
])

# Radii of the concentric bands
R_FLAME = 0.32
R_TREE0, R_TREE1 = 0.44, 1.02      # root -> leaves (the tree must read clearly)
R_SPOKE = 1.10                      # leaf -> its own traces
R_NEAR0, R_NEAR1 = 1.14, 1.64
R_FAR0, R_FAR1 = 1.72, 2.22
R_RIM = 2.29                        # species colour rim, OUTSIDE the data
GAP_DEG = 1.1                       # blank angle between species sectors


def leaves(node):
    if isinstance(node, str):
        return [node]
    return [l for c in node[1] for l in leaves(c)]


def depth_map(node, d=0, out=None):
    """Maximum depth of every internal node, for its radius."""
    out = {} if out is None else out
    if isinstance(node, str):
        return out
    out[id(node)] = d
    for c in node[1]:
        depth_map(c, d + 1, out)
    return out


def polar(theta, r):
    return r * np.cos(theta), r * np.sin(theta)


def arc(ax, t0, t1, r, **kw):
    t = np.linspace(t0, t1, max(8, int(abs(t1 - t0) * 120)))
    ax.plot(*polar(t, r), **kw)


def flame(ax, scale=R_FLAME):
    """A stylised flame, drawn as nested bezier silhouettes."""
    verts = [(0.00, -1.00),
             (0.62, -0.72), (0.70, 0.02), (0.30, 0.34),
             (0.22, 0.60), (0.12, 0.82), (0.00, 1.00),
             (-0.12, 0.82), (-0.22, 0.60), (-0.30, 0.34),
             (-0.70, 0.02), (-0.62, -0.72), (0.00, -1.00)]
    codes = [Path.MOVETO] + [Path.CURVE4] * 12
    for s, col, a in [(1.00, "#ff5a1f", 1.0), (0.62, "#ffa62b", 1.0), (0.30, "#ffe66d", 1.0)]:
        v = [(x * scale * s, y * scale * s + scale * (1 - s) * 0.35) for x, y in verts]
        ax.add_patch(PathPatch(Path(v, codes), facecolor=col, edgecolor="none",
                               zorder=6, alpha=a))
    # a soft halo so the flame sits in the black rather than on it
    for rr, aa in [(scale * 1.55, 0.13), (scale * 1.30, 0.10), (scale * 1.08, 0.08)]:
        t = np.linspace(0, 2 * np.pi, 200)
        ax.fill(*polar(t, rr), color="#ff7a1f", alpha=aa, zorder=2, lw=0)


def build(labels_inside=False, icons=True):
    d = load()
    order = leaves(TREE)
    missing = set(order) ^ set(d["order"])
    if missing:
        raise SystemExit(f"tree/species mismatch: {missing}")
    idx = {s: np.where(d["species"] == s)[0] for s in order}
    # palette follows the tree order so neighbours differ
    cmap = {s: SPECIES_COLORS[i % len(SPECIES_COLORS)] for i, s in enumerate(order)}

    # --- angular sectors, proportional to recording count
    n = np.array([len(idx[s]) for s in order], float)
    gaps = np.deg2rad(GAP_DEG) * len(order)
    widths = n / n.sum() * (2 * np.pi - gaps)
    starts, a = {}, np.deg2rad(90.0)     # start at 12 o'clock, go clockwise
    for s, w in zip(order, widths):
        starts[s] = (a - w, a)           # (t0, t1)
        a -= w + np.deg2rad(GAP_DEG)
    mid = {s: 0.5 * (starts[s][0] + starts[s][1]) for s in order}

    fig = plt.figure(figsize=A4)
    fig.patch.set_facecolor("black")
    m = 0.045
    ax = fig.add_axes([m, m, 1 - 2 * m, 1 - 2 * m])
    ax.set_facecolor("black")
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)

    # --- the tree
    dm = depth_map(TREE)
    dmax = max(dm.values()) + 1
    TREE_C = "#c8d2d4"
    # internal nodes worth naming on the cover (the rest stay unlabelled)
    CLADES = {"monocots", "eudicots", "rosids", "asterids",
              "Solanaceae", "Lamiaceae", "Capsicum"}

    def draw(node):
        """Returns the angle of this node; draws its arc and radial spokes.
        Terminal branches take the species colour so the tree and the traces
        are visibly the same object."""
        if isinstance(node, str):
            return mid[node]
        r_node = R_TREE0 + (R_TREE1 - R_TREE0) * (dm[id(node)] / dmax)
        angs = [draw(c) for c in node[1]]
        for c, ang in zip(node[1], angs):
            leaf = isinstance(c, str)
            r_child = (R_TREE1 if leaf
                       else R_TREE0 + (R_TREE1 - R_TREE0) * (dm[id(c)] / dmax))
            ax.plot(*polar(np.array([ang, ang]), np.array([r_node, r_child])),
                    color=cmap[c] if leaf else TREE_C,
                    lw=1.5 if leaf else 1.25, alpha=0.95 if leaf else 0.9, zorder=3)
        if len(angs) > 1:
            arc(ax, min(angs), max(angs), r_node, color=TREE_C, lw=1.25, alpha=0.9, zorder=3)
        if node[0] in CLADES and len(angs) > 1:
            th = float(np.mean(angs))
            # tangential text: the flip test is on the TEXT angle (deg-90),
            # not the radial angle, or half the labels come out upside down
            rot = (np.degrees(th) - 90.0) % 360.0
            flip = 90.0 < rot < 270.0
            ax.text(*polar(th, r_node + 0.040), node[0],
                    color="#eaf0f1", fontsize=5.6, alpha=0.95,
                    ha="center", va="top" if flip else "bottom",
                    rotation=rot + 180.0 if flip else rot,
                    rotation_mode="anchor", style="italic", zorder=6,
                    path_effects=[pe.withStroke(linewidth=1.6, foreground="black")])
        return float(np.mean(angs))

    root_ang = draw(TREE)
    ax.plot(*polar(np.array([root_ang, root_ang]), np.array([R_FLAME * 1.2, R_TREE0])),
            color=TREE_C, lw=1.25, alpha=0.7, zorder=3)

    # --- the traces
    for s in order:
        col = cmap[s]
        far_c = _tint(col, 0.62)
        t0, t1 = starts[s]
        ii = idx[s]
        # spread the recordings across the species' sector
        offs = (np.linspace(0.12, 0.88, len(ii)) if len(ii) > 1 else np.array([0.5]))
        for k, i in enumerate(ii):
            a_, b_ = _fit_pair(d["near"][i], d["far"][i])
            th0 = t0 + (t1 - t0) * offs[k]
            u = np.linspace(0, 1, len(a_))
            kk = (t1 - t0) * 0.30          # deflection scaled to the sector
            ax.plot(*polar(th0 + a_ * kk, R_NEAR0 + (R_NEAR1 - R_NEAR0) * u),
                    lw=0.7, color=col, alpha=0.95, zorder=4)
            ax.plot(*polar(th0 + b_ * kk, R_FAR0 + (R_FAR1 - R_FAR0) * u),
                    lw=0.65, color=far_c, alpha=0.8, zorder=4)
        # fan the leaf out to its own sector, so tree and data are one object
        for e in (t0, t1):
            ax.plot(*polar(np.array([mid[s], e]), np.array([R_TREE1, R_SPOKE])),
                    color=col, lw=0.8, alpha=0.32, zorder=3)
        arc(ax, t0, t1, R_SPOKE, color=col, lw=1.2, alpha=0.6, zorder=3)
        # colour rim OUTSIDE the data (it used to sit on the tree and hide it)
        arc(ax, t0, t1, R_RIM, color=col, lw=2.6, alpha=0.95, zorder=5)

    # --- species marks: silhouettes by default, Latin names with --names
    if icons:
        r_ico = R_RIM + 0.40
        for s_ in order:
            th = mid[s_]
            # kept UPRIGHT: rotating them radially made the leaves read sideways
            # or upside down around the bottom of the ring
            draw_icon(ax, s_, *polar(th, r_ico), size=0.40, rot_deg=0.0,
                      color=cmap[s_], alpha=0.96, zorder=8, lw=1.1)
        r_lab = r_ico + 0.42
    else:
        r_lab = 0.96 if labels_inside else R_RIM + 0.10
        for s_ in order:
            th = mid[s_]
            deg = np.degrees(th) % 360
            flip = 90 < deg < 270
            ax.text(*polar(th, r_lab), SPECIES_LATIN.get(s_, s_),
                    color=cmap[s_], fontsize=6.6 if labels_inside else 7.4,
                    ha="right" if flip else "left", va="center",
                    rotation=deg + 180 if flip else deg,
                    rotation_mode="anchor", style="italic", zorder=7)

    lim = (r_lab + 0.04) if icons else ((r_lab + 0.80) if not labels_inside else (R_RIM + 0.10))
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
    flame(ax)

    name = "13_phylo_ring%s.png" % ("" if icons else ("_labels_inside" if labels_inside else "_names"))
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("wrote", p)
    print("  leaf order:", " | ".join(order))


if __name__ == "__main__":
    build(labels_inside="--labels-inside" in sys.argv,
          icons="--names" not in sys.argv)
