"""Forward models of passive and active propagation, for comparison to data.

passive_cable_propagate : linear cable — a distal signal is the proximal one
    delayed, exponentially decayed and dispersed (low-pass). Green's function of
    dV/dt = D d2V/dx2 - V/tau.
fitzhugh_nagumo_1d      : an excitable reaction-diffusion cable — a stimulus at
    one end launches a self-regenerating travelling pulse with constant amplitude
    and constant velocity (the active signature).

These make the discriminators concrete: passive => amplitude falls and the wave
broadens with distance; active => amplitude and shape are held constant.
"""
from __future__ import annotations

import numpy as np


def cable_greens_function(x, fs, D, tau, n):
    """Discretised Green's function G(x, t) of the passive cable equation
    dV/dt = D d2V/dx2 - V/tau, sampled at fs for n samples (t > 0)."""
    t = (np.arange(n) + 0.5) / fs
    G = np.exp(-t / tau) / np.sqrt(4 * np.pi * D * t) * np.exp(-(x ** 2) / (4 * D * t))
    s = G.sum()
    return G / s if s > 0 else G


def passive_cable_propagate(near, fs, D=4.0, tau=3.0, x=1.0):
    """Predict the far trace from the near trace under passive cable spread.

    D  diffusion coeff (mm^2/s-ish, sets dispersion + speed),
    tau membrane time constant (s, sets decay),
    x  electrode separation in cable units. Returns a decayed, dispersed copy.
    """
    near = np.asarray(near, float)
    G = cable_greens_function(x, fs, D, tau, len(near))
    far = np.convolve(near, G, mode="full")[: len(near)]
    # exponential amplitude decrement with distance (space constant lam = sqrt(D*tau))
    lam = np.sqrt(D * tau)
    return far * np.exp(-x / lam)


def fitzhugh_nagumo_1d(nx=400, dx=0.5, dt=0.01, t_end=200.0, D=1.0,
                       a=0.7, b=0.8, eps=0.08, I=0.5, stim_len=10,
                       probes=(120, 280)):
    """Integrate the FitzHugh-Nagumo cable and record v at two probe sites.

    dv/dt = D d2v/dx2 + v - v^3/3 - w + I_stim ; dw/dt = eps (v + a - b w).
    A brief current at the left end launches a travelling pulse. Returns
    (t, [v_probe0, v_probe1], velocity_estimate).
    """
    nt = int(t_end / dt)
    v = np.full(nx, -1.2)
    w = np.full(nx, -0.62)
    rec = [[], []]
    tvec = np.arange(nt) * dt
    lap = np.zeros(nx)
    for it in range(nt):
        lap[1:-1] = (v[2:] - 2 * v[1:-1] + v[:-2]) / dx**2
        lap[0] = (v[1] - v[0]) / dx**2
        lap[-1] = (v[-2] - v[-1]) / dx**2
        stim = I if (it * dt < 5.0) else 0.0
        istim = np.zeros(nx)
        istim[:stim_len] = stim
        v = v + dt * (D * lap + v - v**3 / 3 - w + istim)
        w = w + dt * (eps * (v + a - b * w))
        rec[0].append(v[probes[0]]); rec[1].append(v[probes[1]])
    r0, r1 = np.array(rec[0]), np.array(rec[1])
    # velocity from peak-time difference over probe separation
    dtp = (np.argmax(r1) - np.argmax(r0)) * dt
    dist = (probes[1] - probes[0]) * dx
    vel = dist / dtp if dtp > 0 else np.nan
    return tvec, (r0, r1), vel
