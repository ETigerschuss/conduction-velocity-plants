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


def plant_ap_hh(t_end=8.0, dt=0.0005, stim_t=1.0, stim_dur=0.1, stim_amp=40.0,
                Cm=1.0, EL=-130.0, ECl=-15.0, EK=-100.0,
                gL=0.04, gCl=2.2, gK=6.0, gCaV=2.0,
                tau_ca=0.5, tau_n=0.5, kCa=1.5, nCa=3,
                vhalf_ca=-55.0, kslope_ca=9.0, vhalf_k=-80.0):
    """Hodgkin-Huxley-type single-cell PLANT action potential (regenerative).

    Ionic basis follows the established plant AP mechanism (Hedrich & Neher 2018;
    Fromm & Lautner 2007; computational framework of Sukhov & Vodeneev 2009):
    a stimulus admits Ca2+; Ca2+ gates a depolarising anion (Cl-) efflux; the
    depolarisation opens *voltage-gated* Ca2+ influx (positive feedback → an
    all-or-none, regenerative spike); a voltage-gated K+ efflux and Ca2+ removal
    repolarise. Plants use Cl-/K+, NOT Na+, and the AP lasts ~1 s (vs ms in
    animals). Parameters are illustrative (tuned to a flytrap-like AP), NOT fitted
    conductances — surface, band-passed recordings cannot constrain those.
    Returns (t, V, Ca).
    """
    n = int(t_end / dt)
    t = np.arange(n) * dt
    V = np.full(n, EL); Ca = np.zeros(n)
    v, ca, nk = EL, 0.0, 0.0
    for i in range(n):
        V[i], Ca[i] = v, ca
        stim = stim_amp if (stim_t <= t[i] < stim_t + stim_dur) else 0.0
        mCl = ca ** nCa / (kCa ** nCa + ca ** nCa)                 # Ca-gated anion channel
        mCaV = 1.0 / (1.0 + np.exp(-(v - vhalf_ca) / kslope_ca))   # V-gated Ca influx (regeneration)
        ninf = 1.0 / (1.0 + np.exp(-(v - vhalf_k) / 10.0))         # V-gated K+ activation
        iL = gL * (v - EL); iCl = gCl * mCl * (v - ECl); iK = gK * nk * (v - EK)
        v += dt * (-(iL + iCl + iK)) / Cm
        ca += dt * (stim + gCaV * mCaV - ca / tau_ca)
        nk += dt * (ninf - nk) / tau_n
    return t, V, Ca


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
