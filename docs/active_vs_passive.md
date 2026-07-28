# Active vs passive propagation: analyses, ion channels, and simulation

Three questions: (1) what else can distinguish active (regenerative) from
passive (electrotonic / decremental / hydraulic) propagation of these
potentials, (2) which ion channels are involved, and (3) can we simulate it.
This note answers all three — the data analyses are implemented in
`cvplants/propagation.py` + `cvplants/simulate.py` (run `scripts/active_passive.py`);
the biology is distilled (with citations) in `docs/references/`.

---

## 0. The signal classes we are discriminating

Plant electrical signals come in three kinds (Fromm & Lautner 2007, *Plant Cell
Environ*; Vodeneev, Akinchits & Sukhov 2015, *Plant Signal Behav*):

| class | rule | velocity | mechanism | active/passive |
|---|---|---|---|---|
| **Action potential (AP)** | all-or-none | ~5–200 mm/s | self-regenerating Ca²⁺→Cl⁻→K⁺ currents | **active** |
| **Variation potential (VP)** | graded, decremental | ~1–10 mm/s | H⁺-ATPase inactivation driven by a xylem hydraulic/chemical wave | **passive** (courier not even electrical) |
| **System potential (SP)** | graded, hyperpolarising | ~5–10 cm/min | H⁺-ATPase *activation* | passive |

> **Hardware note (corrected against the paper).** The recordings were made with
> a 2-channel prototype amplifier at **0.2–130 Hz band-pass, gain ~55×, 10 kHz**
> (a few final Mimosa/Venus/Tomato measurements used a next-gen "SpikeStation" at
> 0.1–20000 Hz, 10×). The FigShare WAVs here are 5 kHz. The 130 Hz upper cutoff
> **preserves waveform shape** (an earlier draft wrongly assumed a Plant
> SpikerBox 0.07–8.8 Hz front end and over-warned about shape smearing — removed).
> The 0.2 Hz high-pass does attenuate the slow DC component of a variation
> potential, so absolute VP amplitude is under-represented; the analyses below
> still lean on *distance-scaling* of the near→far transformation, which is robust
> to that.

---

## 0b. Channel integrity: near/far assignment and the shared reference

- **Near/far is assigned per recording** as "whichever channel peaks first."
  This is consistent for most species (ch0 leads in ~76% of recordings) but
  flips where the delay is small; the delay *magnitude* (hence CV) is unaffected
  by which label a channel gets.
- **The two channels are correlated, and that is expected.** Both electrodes
  share a soil/earth reference, so any whole-plant potential or reference
  fluctuation appears in *both* — a normal referential montage, not amplifier
  crosstalk. The pre-stimulus baseline correlation is high (pooled r ≈ 0.66;
  `baseline_common_mode.png`, `crosstalk_raw_examples.png`) precisely because of
  this shared ground. A large event on a small, Ca²⁺-rich leaf (Venus flytrap)
  is also volume-conducted to both nearby electrodes, adding an instantaneous
  shared component. **Correlation ≠ no delay.**
- **The delay is recovered with a common-mode-robust model.** far(t) =
  a·near(t) + b·near(t−τ) loads the shared/instantaneous part onto `a` and the
  propagated part onto `b` at lag τ (`cvplants.propagation.two_component_fit`).
  Across species the delayed fraction |b|/(|a|+|b|) is 0.68–0.90 and τ is
  sign-consistent (75–100%) — i.e. a *real, directional* delay survives once the
  shared component is separated. So the shared ground does not prevent measuring
  which channel's event is later. The pipeline records `cm_baseline_r`,
  `event_zero_lag_r`, `r0_over_rpk`, `delay_resolved`; 151/165 recordings resolve.
- **Venus flytrap's fast CV is real.** Its 2-tap delay (~0.3 s, delayed-fraction
  0.82, 14/16 resolved) gives CV ≈ 28–30 mm/s — consistent with the known fast
  Dionaea AP. A small electrode spacing on the trap gives a *small but genuine*
  delay, plus strong volume-conduction correlation; it is not "no delay." (An
  earlier draft over-flagged the fast species with a hard time-floor and wrongly
  called this an artifact — corrected.)

**Simulation vs real (`scripts/sim_vs_real.py`, `sim_vs_real_examples.png`).**
Predicting the far trace from the near trace, the **active model (delayed copy +
shared component) out-predicts the passive cable** for almost every species
(median R² 0.4–0.87 vs 0.2–0.79). The far trace really is a *delayed* copy of the
near trace, not a dispersed one — direct evidence for propagation with a
resolvable delay. For the fast species this supports genuinely fast conduction;
the montage still cannot, on its own, prove the fast event is *regeneratively*
(rather than passively) propagated, but the delay itself is real.

---

## 1. What the data can say (analyses implemented here)

The structural advantage of this dataset: both electrodes sit on the same
conduction path, so the only thing differing between near and far is the *known*
inter-electrode distance `d`. Every near→far change is therefore anchored to a
measured distance — the axis on which active and passive actually separate.

**Three independent metrics place the same species at the active end and the
same species at the passive end:**

1. **Passive-kernel dispersion** (`fit_passive_kernel`): can `far(t)` be
   reproduced as a delayed, gained, low-pass-smoothed copy of `near(t)`? The
   extra Gaussian width σ needed is the "passive filtering." Median σ (s):
   Sensitive Mimosa 0.10 and Venus flytrap 0.15 (little filtering, shape kept)
   → **active-like**; Creeping Inchplant 1.90, Mint 1.05, Argentian Dollar 1.00
   (heavy low-pass) → **passive-like**. See `active_passive_space.png`.

2. **Peak−onset asymmetry** (rigid-translation test): a ballistic wave shifts
   onset and peak by the *same* delay (difference ≈ 0); a dispersive wave lets
   the peak lag the onset (difference > 0). Median (s): Sensitive Mimosa 0.03,
   Venus flytrap 0.09 (rigid → active) vs Ornamental Chile 0.75, Argentian
   Dollar 0.55, Mint 0.52 (dispersive → passive). Independent of amplitude and
   of the kernel fit, yet it reproduces the same ordering. See
   `peak_onset_asymmetry.png`.

3. **Delay–distance scaling** (`velocity_fit` + log-log exponent): delay ∝ dᵇ
   with **b = 1.09** (95% CI ±0.37, n = 151, p = 3×10⁻⁸) — i.e. **ballistic, constant
   velocity** (b≈1), *not* diffusive (b≈2). A hydraulic/diffusive courier would
   give b≈2 with an apparent D near the xylem turbulent-diffusion range
   (0.05–0.12 cm²/s; Vodeneev et al. 2015); we see b≈1, v≈4.9 mm/s, intercept≈0.
   See `delay_vs_distance.png`.

Two weaker/inconclusive tests, reported honestly:

4. **Amplitude decrement vs distance** (`decrement_fit`): pooled slope ≈ 0
   (λ≈109 mm, p=0.49) — amplitude is decremented (far/near median ~0.44) but the
   decrement does **not** scale with inter-electrode distance in the 6–40 mm
   range. Underpowered here (narrow spacing range, contact-gain scatter); it is
   *not* clean evidence either way. See `decrement_vs_distance.png`.

5. **All-or-none proxy** (amplitude↔CV / amplitude↔attenuation coupling):
   amp–CV is weakly coupled (median |ρ|≈0.25); amp–attenuation is uniformly
   negative (ρ≈−0.63) but that is partly the near-amplitude appearing in the
   denominator plus electrode-contact scatter — treat as confounded, suggestive
   only.

**Reading of the ensemble.** No single metric is decisive under the SpikerBox
filter + contact-gain confounds. But the **joint decremental↔regenerative axis**
is coherent and convergent: **Venus flytrap and Sensitive Mimosa sit at the
active/regenerative end** (shape preserved, rigid translation, gain≈1) — exactly
the two textbook action-potential plants — while the **mints, Argentian Dollar
and Creeping Inchplant sit at the passive/decremental (VP-like) end**. That this
active cluster spans *different families* (Droseraceae, Fabaceae) is the same
convergence seen in `REPORT.md`: fast regenerative signalling is a functional,
not a phylogenetic, trait. Species should be classified on this axis *before*
pooling — do not average an AP plant with a VP plant.

---

## 2. Ion channels (see `docs/references/ion_channels.md` for the full account)

Plant excitation is **Ca²⁺/Cl⁻/K⁺-based, not Na⁺-based** (Fromm & Lautner 2007;
Sukhov & Vodeneev 2009, *J Membr Biol*):

- **Depolarisation — Ca²⁺ influx via GLUTAMATE-RECEPTOR-LIKE channels (GLRs).**
  Clade-3 **GLR3.3 / GLR3.6** (and GLR3.2) carry the wound-induced, systemic
  Ca²⁺/electrical signal (Mousavi et al. 2013, *Nature*; Toyota et al. 2018,
  *Science*; Nguyen et al. 2018, *PNAS* — GLRs localised to phloem sieve elements
  and xylem contact cells).
- **Sustained depolarisation — anion (Cl⁻/NO₃⁻/malate) efflux.** S-type
  **SLAC1/SLAH3** and R-type **QUAC1/ALMT12** (established in guard cells;
  extrapolated to the propagating spike).
- **Repolarisation — K⁺ efflux via the outward rectifier GORK** (Salvador-Recatalà
  2018 showed GORK shapes the plant AP), plus reactivation of the
- **P-type plasma-membrane H⁺-ATPase (AHA)** that sets the (pump-dominated)
  resting potential.
- **Variation potential:** driven by **transient H⁺-ATPase inactivation** behind
  a **xylem hydraulic/chemical ("Ricca factor") wave** (Sukhov/Vodeneev; Evans
  et al. 2017, *Plant J* — xylem mass-flow-transported chemical agent). The
  mechanosensor that initiates it (candidates OSCA1, MSL10, MCA1/2, PIEZO) is the
  field's clearest open question.
- **Venus flytrap:** trigger-hair micronewton mechanosensing → receptor potential
  → all-or-none Ca²⁺-based AP; candidate mechanosensor **FLYC1/MSL10**, K⁺
  channel **KDM1**, AP "counting" gates jasmonate signalling and DmHKT1 Na⁺
  uptake (Böhm et al. 2016; Hedrich & Neher 2018; Jaślan/Hedrich 2022).
- **Mimosa pudica:** touch → Ca²⁺ → Cl⁻ efflux → K⁺ + water efflux collapses
  pulvinar turgor (Allen 1969); channel genes inferred by homology, not cloned.

*Provenance:* the ion-channel section's dedicated fact-check agent did not finish
(session limit), but its citations match the primary literature and the core
AP mechanism (Ca²⁺/Cl⁻/K⁺, not Na⁺) was independently confirmed by the simulation
verifier. The established/speculative split in `ion_channels.md` is preserved.

---

## 3. Simulation (`cvplants/simulate.py`; see `docs/references/simulation_methods.md`)

- **Passive cable (the null model).** `τ ∂V/∂t = λ² ∂²V/∂x² − V`, with the
  Green's function `G(x,t) = e^{−t/τ}/√(4πD t)·e^{−x²/4Dt}`, `λ=√(rm/ri)`,
  `D=λ²/τ`. A distal signal is the proximal one **delayed, exponentially decayed
  (×e^{−x/λ}) and low-pass dispersed**. `passive_cable_propagate()` forward-models
  far from near this way — the near→far kernel fit in §1 is exactly this transfer
  function `H_d(s)=exp[−(d/λ)√(1+sτ)]`.
- **Active excitable cable.** `fitzhugh_nagumo_1d()` integrates
  `u_t = D u_xx + u − u³/3 − w + I`, `w_t = ε(u − a − b w)`; a brief stimulus at
  one end launches a **travelling pulse of constant amplitude and constant
  velocity** (v ∝ √D). For a plant-specific active model use the Hodgkin-Huxley-
  type Ca²⁺/Cl⁻/K⁺ membrane model of **Sukhov & Vodeneev 2009** and its cable
  extension **Sukhov et al. 2011, *J Theor Biol*** (AP propagating at cm/s).
- `cable_vs_fhn_sim.png` contrasts the two: passive decays+broadens with
  distance; active holds amplitude and shape — the "amplitude vs distance" panel
  is the single cleanest signature.

---

## 4. What this dataset **cannot** decide — and the minimal new experiment

| question | why not now | minimal experiment |
|---|---|---|
| true all-or-none threshold | one wound/recording, unknown intensity | **stimulus-intensity ladder** at one site → step (active) vs graded (passive) |
| refractory period | single stimulus | **paired-pulse** Δt = 0.5–20 min → second-response recovery curve |
| regenerative ion mechanism | AC-coupled surface trace | **pharmacology** (La³⁺/Gd³⁺, A-9-C/DIDS, TEA) on the segment *between* wound and electrodes |
| channel-gated vs physical conduction | single temperature | **Q10 series** (15/25/35 °C): active ≈2–3, passive ≈1 |
| hydraulic vs electrical primacy | electrical channels only | **co-record xylem pressure / stem strain** with the electrodes |
| bidirectionality | both electrodes downstream | electrodes **proximal and distal** to a non-wounding stimulus |

The decisive, cheap wins are the **intensity ladder** and **paired-pulse
refractory** tests — a two-electrode multi-stimulus protocol on the same rig
would move the active/passive call from "strongly suggested" to "demonstrated."
