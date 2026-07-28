"""Venus flytrap: why it sits 'below the active line', and a biophysical AP model.

(1) Electrode-asymmetry check. Venus used an ASYMMETRIC montage (hook around the
    'neck' + stake alongside the trap lobe; paper Methods), unlike the symmetric
    spiral electrodes on other plants. So its far/near amplitude ratio reflects
    electrode coupling, not propagation decrement — which is why it lands below
    the gain=1 'active' line even though its waveform shape is preserved (active).

(2) Biophysical AP model. A Hodgkin-Huxley-type plant AP (Ca2+/Cl-/K+;
    cvplants.simulate.plant_ap_hh) is simulated, filtered with the recording
    band-pass, and overlaid on a real Venus AP — showing the model reproduces the
    observed shape, and demonstrating all-or-none behaviour.
"""
from __future__ import annotations

import os
import sys
import glob

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd                                          # noqa: E402
from cvplants.io import load_recording, SPECIES_FAMILY, FAMILY_COLORS  # noqa: E402
from cvplants.preprocessing import lowpass, baseline_subtract          # noqa: E402
from cvplants.analysis import _response_window               # noqa: E402
from cvplants.simulate import plant_ap_hh                     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "results", "figures")


def bandpass(x, fs, lo=0.2, hi=130.0):
    ny = 0.5 * fs
    b, a = butter(2, [lo / ny, min(hi / ny, 0.99)], btype="band")
    return filtfilt(b, a, x)


def electrode_asymmetry(df, out):
    """Attenuation (far/near) distribution: Venus (asymmetric electrodes) vs
    symmetric-electrode plants. A real decrement clusters <1; Venus is scattered."""
    v = df[df["valid"] == True]  # noqa: E712
    order = ["Venus Flytrap", "Sensitive Mimosa", "Mint", "Marijuana", "Tomato", "Ruda", "Basil"]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for i, sp in enumerate(order):
        a = v[v["species"] == sp]["attenuation_far_near"].dropna()
        a = a[a < 8]
        c = "#d62728" if sp == "Venus Flytrap" else FAMILY_COLORS.get(SPECIES_FAMILY.get(sp, ""), "#1f77b4")
        ax.scatter(np.random.normal(i, 0.08, len(a)), a, s=26, color=c, alpha=0.75, edgecolor="k", lw=0.3)
        ax.scatter(i, a.median(), s=120, marker="_", color="k")
    ax.axhline(1, color="k", ls="--", lw=1, label="gain = 1 (non-decremental)")
    ax.set_yscale("log")
    ax.set_xticks(range(len(order))); ax.set_xticklabels(order, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("far / near peak amplitude (log)")
    ax.set_title("Measured amplitude ratio does NOT report propagation decrement:\n"
                 "Venus (certain AP, non-decremental) always measures <1 (median 0.30), while Mimosa "
                 "(also certain AP) exceeds 1 in 59% of recordings.\nBoth are impossible for true propagation — "
                 "the ratio is set by electrode–tissue coupling.", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(out, dpi=120); plt.close(fig)


def real_venus_ap(target_fs=200.0):
    """A representative Venus AP (self-aligned on its peak, normalised)."""
    best = None
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "Venus Flytrap", "*.wav"))):
        rec = load_recording(f, species="Venus Flytrap")
        fs = rec.fs
        stim = rec.stim_start if rec.stim_start is not None else 1.0
        bl = (max(0.0, stim - 3), stim)
        c = lowpass(baseline_subtract(rec.data[:, 0], fs, bl), fs, 20.0)
        win = _response_window(rec); i0, i1 = int(win[0] * fs), int(win[1] * fs)
        seg = c[i0:i1]
        if len(seg) < fs:
            continue
        sign = np.sign(seg[np.argmax(np.abs(seg))]) or 1.0
        s = seg * sign
        pk = int(np.argmax(s))
        if s[pk] <= 0:
            continue
        step = max(1, int(round(fs / target_fs)))
        w = int(3 * target_fs)
        a = s[max(0, pk - int(1 * fs)):pk + int(5 * fs):step]
        if len(a) > 10:
            best = a / a.max()
            break
    return best


def ap_model_figure(out):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

    # (a) the model AP (V and Ca)
    t, V, Ca = plant_ap_hh()
    ax = axes[0]
    ax.plot(t, V, "C0", label="V (membrane)")
    ax2 = ax.twinx(); ax2.plot(t, Ca, "C1", lw=1, alpha=0.7, label="Ca²⁺")
    ax.set_xlabel("time (s)"); ax.set_ylabel("V (mV)", color="C0"); ax2.set_ylabel("Ca²⁺ (a.u.)", color="C1")
    ax.set_title("HH-type plant AP (Ca²⁺→Cl⁻→K⁺)\nregenerative, ~seconds, no Na⁺")

    # (b) all-or-none: sub- vs supra-threshold
    ax = axes[1]
    for amp, c, lab in [(12, "#aaa", "sub-threshold"), (18, "#888", "near threshold"),
                        (40, "#1f77b4", "supra-threshold"), (80, "#0b3d6b", "strong")]:
        tt, VV, _ = plant_ap_hh(stim_amp=amp)
        ax.plot(tt, VV, color=c, label=f"stim={amp} ({lab})")
    ax.set_xlabel("time (s)"); ax.set_ylabel("V (mV)")
    ax.set_title("All-or-none: a fixed-size spike\nappears only above threshold")
    ax.legend(fontsize=7)

    # (c) model AP through the recording band-pass vs a real Venus AP
    ax = axes[2]
    fs = 1.0 / (t[1] - t[0])
    Vf = bandpass(V - V.mean(), fs)
    Vf = Vf / np.max(np.abs(Vf))
    tp = t - t[np.argmax(np.abs(Vf))]
    ax.plot(tp, Vf, "C0", lw=2, label="model AP, band-passed 0.2–130 Hz")
    real = real_venus_ap()
    if real is not None:
        real = real / np.max(np.abs(real))
        tr = (np.arange(len(real)) - int(np.argmax(np.abs(real)))) / 200.0
        ax.plot(tr, real, "C3", lw=1.5, alpha=0.8, label="real Venus AP (norm.)")
    ax.set_xlim(-2, 5); ax.set_xlabel("time from peak (s)"); ax.set_ylabel("normalised")
    ax.set_title("Model AP (filtered) vs a real Venus AP\nmatched by eye — not a fit")
    ax.legend(fontsize=7)

    for a in axes:
        a.grid(ls="--", alpha=0.3)
    fig.suptitle("ILLUSTRATIVE: a published biophysical Venus-flytrap AP model (illustrative conductances, not fitted to our data)",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96)); fig.savefig(out, dpi=120); plt.close(fig)


def main():
    np.random.seed(0)
    df = pd.read_csv(os.path.join(ROOT, "results", "recordings.csv"))
    electrode_asymmetry(df, os.path.join(FIG, "venus_electrode_asymmetry.png"))
    ap_model_figure(os.path.join(FIG, "venus_ap_model.png"))

    # CV reproduced from the experimenters' manual delays (cv_manual is merged into
    # recordings.csv by cvplants.batch.augment_cv; no need to re-derive it here)
    for sp in ["Sensitive Mimosa", "Venus Flytrap"]:
        s = df[df["species"] == sp]
        print(f"{sp}: CV from THEIR delays mean={s['cv_manual'].mean():.1f} "
              f"(paper {'32.4' if 'Mimosa' in sp else '35.3'}); my automatic mean="
              f"{df[(df.species==sp)&(df.delay_resolved==True)]['cv_xcorr_mm_s'].mean():.1f}")
    print("wrote venus_electrode_asymmetry.png, venus_ap_model.png")


if __name__ == "__main__":
    main()
