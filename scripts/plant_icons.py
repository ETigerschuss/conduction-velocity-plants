"""Vector botanical silhouettes for the 13 study species.

Drawn as parametric paths rather than bitmaps so they stay sharp at print
resolution and can be recoloured per species. Each icon is built in a local
frame roughly spanning [-1, 1] with the plant growing along +y, then placed by
draw_icon() with a rotation and scale.

The silhouettes are chosen so the species are told apart by SHAPE alone at small
size: palmate for Cannabis, bipinnate for Mimosa, needles for rosemary, a coin
for Plectranthus, a trap for Dionaea, pods for the two Capsicum, and so on.
"""
from __future__ import annotations

import numpy as np
import matplotlib.transforms as mtransforms
from matplotlib.patches import Polygon


# ------------------------------------------------------------------ primitives

def blade(L=1.0, W=0.30, base=0.6, point=0.9, serr=0.0, nserr=12, n=160):
    """A leaf blade along +y: rounded base, tapering tip, optional serration."""
    u = np.linspace(0.0, 1.0, n)
    w = (u ** base) * ((1.0 - u) ** point)
    w = w / max(w.max(), 1e-9) * W
    if serr:
        w = w * (1.0 + serr * np.sin(nserr * np.pi * u))
    x = np.concatenate([w, -w[::-1]])
    y = np.concatenate([L * u, L * u[::-1]])
    return np.column_stack([x, y])


def ellipse(rx, ry, cx=0.0, cy=0.0, n=60):
    t = np.linspace(0, 2 * np.pi, n)
    return np.column_stack([cx + rx * np.cos(t), cy + ry * np.sin(t)])


def rot(pts, deg):
    a = np.deg2rad(deg)
    R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    return pts @ R.T


def shift(pts, dx, dy):
    return pts + np.array([dx, dy])


# ----------------------------------------------------------------- the species
# Each returns (polys, lines): filled silhouettes and stroked lines.

def _cannabis():
    polys, n = [], 7
    lens = [0.62, 0.82, 0.98, 1.06, 0.98, 0.82, 0.62]
    for k, L in enumerate(lens):
        a = -78 + k * (156 / (n - 1))
        lf = blade(L=L, W=0.085, base=0.75, point=1.5, serr=0.16, nserr=9)
        polys.append(shift(rot(lf, a), 0, -0.10))
    return polys, [np.array([[0, -0.10], [0, -0.42]])]


def _venus():
    """The open trap: two lobes hinged at the base, teeth on the outer margins."""
    polys, lines = [], []
    t = np.linspace(-np.pi / 2, np.pi / 2, 70)          # the curved outer margin
    for sgn in (1, -1):
        rx, ry = 0.34, 0.40
        lobe = np.column_stack([sgn * rx * np.cos(t), ry * np.sin(t)])
        lobe = np.vstack([lobe, [0, ry * np.sin(t[0])]])   # close on the hinge
        lobe = shift(rot(lobe, sgn * 24), sgn * 0.045, 0.42)
        polys.append(lobe)
        # teeth: short spikes along the curved edge, angled outward
        for k in range(7):
            tt = -np.pi / 2 + (k + 0.5) * np.pi / 7
            pt = np.array([sgn * rx * np.cos(tt), ry * np.sin(tt)])
            nrm = np.array([sgn * np.cos(tt) / rx, np.sin(tt) / ry])
            nrm = nrm / np.linalg.norm(nrm) * 0.15
            seg = np.vstack([pt, pt + nrm])
            seg = shift(rot(seg, sgn * 24), sgn * 0.045, 0.42)
            lines.append(seg)
    lines.append(np.array([[0, 0.10], [0, -0.52]]))        # petiole
    return polys, lines


def _mimosa():
    polys, lines = [], [np.array([[0, -0.45], [0, 0.05]])]
    for pin in range(4):
        a = -52 + pin * 35
        rach = np.array([[0, 0.05], [0, 0.78]])
        rach = shift(rot(rach - [0, 0.05], a), 0, 0.05)
        lines.append(rach)
        d = (rach[1] - rach[0]) / 9.0
        for k in range(1, 10):
            base = rach[0] + d * k
            for sgn in (1, -1):
                lf = ellipse(0.028, 0.055)
                lf = rot(lf, a + sgn * 62)
                polys.append(shift(lf, *(base + sgn * 0.045 * np.array([-d[1], d[0]]) / np.linalg.norm(d))))
    return polys, lines


def _rosemary():
    """A sprig: short linear needles, offset left/right so it does not read as
    a chevron, with the stem running past the last pair."""
    lines = [np.array([[0, -0.62], [0, 0.88]])]
    for k in range(16):
        sgn = 1 if k % 2 == 0 else -1
        y = -0.50 + k * 0.088
        L = 0.30 - 0.055 * abs(k - 8) / 8.0
        a = np.deg2rad(38 + 6 * ((k % 3) - 1))
        lines.append(np.array([[0, y], [sgn * L * np.cos(a), y + L * np.sin(a)]]))
    return [], lines


def _pod(curve=0.16, L=0.95, W=0.20, upright=False):
    u = np.linspace(0, 1, 120)
    w = (u ** 0.35) * ((1 - u) ** 0.85)
    w = w / w.max() * W
    bend = curve * np.sin(np.pi * u)
    x = np.concatenate([bend + w, (bend - w)[::-1]])
    y = np.concatenate([L * u, L * u[::-1]]) - L * 0.5
    p = np.column_stack([x, y])
    if not upright:
        p = rot(p, 180)
    return p


def _chile_baccatum():
    return [_pod(curve=0.20, L=1.0, W=0.19)], [np.array([[0, 0.50], [0.05, 0.78]])]


def _chile_annuum():
    return [_pod(curve=0.05, L=0.92, W=0.22, upright=True)], [np.array([[0, -0.46], [0, -0.72]])]


def _tomato():
    polys = [ellipse(0.42, 0.37, 0, 0.05)]
    lines = [np.array([[0, 0.42], [0, 0.72]])]
    for k in range(5):
        a = 90 + k * 72
        tip = np.array([0.40 * np.cos(np.deg2rad(a)), 0.05 + 0.36 * np.sin(np.deg2rad(a))])
        lines.append(np.vstack([[0, 0.42], tip * 1.15]))
    return polys, lines


def _basil():
    polys = [shift(blade(L=0.98, W=0.34, base=0.55, point=0.8, serr=0.05, nserr=7), 0, -0.05)]
    return polys, [np.array([[0, -0.05], [0, -0.42]])]


def _plectranthus():
    t = np.linspace(0, 2 * np.pi, 200)
    r = 0.46 * (1.0 + 0.085 * np.sin(9 * t))
    coin = np.column_stack([r * np.cos(t), 0.08 + r * np.sin(t) * 0.92])
    return [coin], [np.array([[0, -0.36], [0, -0.70]])]


def _mint():
    polys = [shift(blade(L=1.02, W=0.26, base=0.6, point=1.0, serr=0.16, nserr=13), 0, -0.05)]
    return polys, [np.array([[0, -0.05], [0, -0.45]])]


def _clinopodium():
    """Small opposite ovate leaves -- larger and clearly separated so the pair
    reads as two leaves rather than one blob."""
    polys = []
    for sgn in (1, -1):
        lf = blade(L=0.60, W=0.225, base=0.5, point=0.72, serr=0.09, nserr=6)
        # near-horizontal, pointing AWAY from each other off a central stem --
        # at steeper angles the two bases overlap and read as one blob
        polys.append(shift(rot(lf, sgn * 80), -sgn * 0.045, 0.06))
    return polys, [np.array([[0, -0.58], [0, 0.34]])]


def _callisia():
    polys, lines = [], [np.array([[-0.62, -0.22], [0.62, 0.20]])]
    for k in range(5):
        f = k / 4.0
        base = np.array([-0.62 + 1.24 * f, -0.22 + 0.42 * f])
        sgn = 1 if k % 2 == 0 else -1
        lf = blade(L=0.44, W=0.17, base=0.55, point=0.75)
        polys.append(shift(rot(lf, sgn * 55 + 18), *base))
    return polys, lines


def _ruta():
    polys, lines = [], [np.array([[0, -0.52], [0, 0.72]])]
    for k in range(4):
        y = -0.32 + k * 0.30
        for sgn in (1, -1):
            lob = ellipse(0.105, 0.155)
            polys.append(shift(rot(lob, sgn * 28), sgn * 0.26, y + 0.10))
            lines.append(np.array([[0, y], [sgn * 0.20, y + 0.06]]))
    return polys, lines


ICONS = {
    "Marijuana": _cannabis,
    "Venus Flytrap": _venus,
    "Sensitive Mimosa": _mimosa,
    "Rosemary": _rosemary,
    "Chilean Chile": _chile_baccatum,
    "Ornamental Chile": _chile_annuum,
    "Tomato": _tomato,
    "Basil": _basil,
    "Argentian Dollar": _plectranthus,
    "Mint": _mint,
    "Hierbabuena": _clinopodium,
    "Creeping Inchplant": _callisia,
    "Ruda": _ruta,
}


def draw_icon(ax, species, x, y, size=1.0, rot_deg=0.0, color="#ffffff",
              alpha=0.95, zorder=8, lw=0.9):
    """Place a species silhouette at (x, y), scaled and rotated."""
    polys, lines = ICONS[species]()
    tr = (mtransforms.Affine2D().rotate_deg(rot_deg).scale(size).translate(x, y)
          + ax.transData)
    for p in polys:
        ax.add_patch(Polygon(p, closed=True, facecolor=color, edgecolor="none",
                             alpha=alpha, zorder=zorder, transform=tr))
    for ln in lines:
        ax.plot(ln[:, 0], ln[:, 1], color=color, lw=lw, alpha=alpha,
                solid_capstyle="round", zorder=zorder, transform=tr)


def contact_sheet(out):
    """Render all 13 icons in a grid to check they read at small size."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from cvplants.io import SPECIES_LATIN
    names = list(ICONS)
    fig, axes = plt.subplots(3, 5, figsize=(15, 9.6))
    fig.patch.set_facecolor("black")
    for ax, sp in zip(axes.ravel(), names):
        ax.set_facecolor("black"); ax.set_aspect("equal")
        ax.set_xlim(-1.1, 1.1); ax.set_ylim(-1.1, 1.1)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_color("#333")
        draw_icon(ax, sp, 0, 0, size=0.95, color="#8ee36b")
        ax.set_title(f"{sp}\n{SPECIES_LATIN.get(sp,'')}", color="white", fontsize=7.5, pad=4)
    for ax in axes.ravel()[len(names):]:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(out, dpi=140, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    import os, sys
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, ROOT)
    contact_sheet(os.path.join(ROOT, "results", "figures", "cover", "_icons_sheet.png"))
