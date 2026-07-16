"""Filtering and baseline handling for slow plant potentials.

Wound / variation potentials evolve over seconds, so the informative band is
well below 5 Hz. A low-pass at a few Hz removes mains hum (50/60 Hz) and
electrode noise while preserving the propagating waveform, which makes a
separate notch filter unnecessary.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, filtfilt


def lowpass(x: np.ndarray, fs: float, cutoff: float = 2.0, order: int = 2) -> np.ndarray:
    """Zero-phase Butterworth low-pass. Zero-phase keeps event timing unbiased,
    which matters because we measure inter-channel delays from these traces."""
    ny = 0.5 * fs
    b, a = butter(order, min(cutoff / ny, 0.99), btype="low")
    return filtfilt(b, a, x)


def baseline_subtract(x: np.ndarray, fs: float, ref_window: tuple | None = None) -> np.ndarray:
    """Subtract the mean of a reference window (default: whole trace median)."""
    if ref_window is None:
        return x - np.median(x)
    i0 = max(0, int(ref_window[0] * fs))
    i1 = min(len(x), int(ref_window[1] * fs))
    if i1 <= i0:
        return x - np.median(x)
    return x - np.mean(x[i0:i1])


def preprocess_channel(x: np.ndarray, fs: float, cutoff: float,
                       baseline_window: tuple | None) -> np.ndarray:
    """Baseline-subtract then low-pass a single channel."""
    return lowpass(baseline_subtract(x, fs, baseline_window), fs, cutoff)
