# Discriminating actively (regenerative, all-or-none) from passively (electrotonic / decremental / hydraulic) propagated electrical signals in plants

## 0. Framing — why plants need a two-family test

In animal axons the only real question is *regenerative vs electrotonic*. In plants there is a second, equally important ambiguity: the travelling entity may not be electrical at all. A wound-induced depolarization can be a purely **local transducer response** to a **hydraulic pressure wave** or a **xylem-borne chemical (Ricca's factor)** that is what actually moves through the plant. So a rigorous discrimination program has **two families of tests**:

- **Family A — regenerative vs decremental electrical propagation** (the classical cable-theory question): amplitude/distance, all-or-none, refractory period, velocity constancy, Q10, ion/pharmacology, waveform preservation.
- **Family B — is the propagating agent electrical at all, or hydraulic/chemical** (Ricca-factor tests, xylem pressure, girdling, mass-flow tracking).

Mapped onto the three plant signal classes (nomenclature and canonical parameters below are from Zimmermann et al. 2009, *Plant Physiol*; Vodeneev, Katicheva & Sukhov 2015/2016; Fromm & Lautner 2007, *Plant Cell Environ*):

| Class | Trigger | Polarity (intracellular) | Rule | Canonical velocity | Core mechanism |
|---|---|---|---|---|---|
| **AP** (action potential) | non-damaging, above threshold | depolarizing | **all-or-none** | ~20–400 cm min⁻¹ (0.3–7 cm s⁻¹) in higher plants; 11–44 mm s⁻¹ in Characeae | regenerative: voltage-gated Ca²⁺ influx → Cl⁻ efflux (depolarizing inward-equivalent current) → K⁺ efflux (repolarization) |
| **VP** (variation / slow-wave potential) | wounding, burning, heat | depolarizing | **graded, decremental** | ~0.8–3 mm s⁻¹ (velocity *variable*, declines with distance) | H⁺-ATPase **inactivation**, driven by a hydraulic/chemical trigger; electrical event is partly a *local response* |
| **SP** (system potential) | wounding + apoplastic ion/substance change | **hyperpolarizing** | graded, **concentration/type-dependent** | ~5–10 cm min⁻¹ | H⁺-ATPase **activation** (P-type; blocked by vanadate, mimicked by fusicoccin) |

The single most useful heuristic: **an AP is the only one of the three that is a true self-regenerating electrical wave.** VP and SP are, to first order, *decremental / graded* by their own defining literature, and the VP's propagation is very likely carried by a non-electrical (hydraulic/chemical) agent. Everything below operationalizes that.

---

## 1. Amplitude decrement vs distance — the space constant λ

**(a) Observable.** Peak deflection amplitude recorded at a series of electrodes at increasing distance *x* from the excitation site.

**(b) Active predicts.** Amplitude **invariant with distance** (the wave is re-created at each point). Any apparent decline is due to tissue geometry/electrode coupling, not signal decay. Diagnostic of regeneration.

**(c) Passive predicts.** Exponential decay set by cable theory, `V(x) = V₀·exp(−x/λ)`, with `λ = √(r_m/r_i)` (membrane vs axial resistance). A *pure electrotonic* potential falls to 1/e over one λ (typically millimetres to low centimetres in plant tissue) and is undetectable beyond a few λ. A **VP is explicitly decremental**: amplitude falls ~**10% per cm** in pumpkin and wheat, and the decrement itself scales with damage intensity (Vodeneev et al. 2011, 2012). SP is graded but its size is set by the apoplastic stimulus, not by distance decay per se (Zimmermann et al. 2009).

**(d) How to measure (incl. extracellular multi-electrode).** Place ≥4–6 surface Ag/AgCl electrodes (or metal micro-pins 0.4–1.0 mm, accepting the wound artifact) in a **linear array** along the stem/petiole/midrib at known spacings; reference to a distant/root electrode; high-input-impedance (≥10¹² Ω) DC-coupled amplifier (Sukhov et al. 2021 protocol, *MethodsX/Bio-protocol*; Fromm & Lautner 2007). Fit `ln(amplitude)` vs `x`; a straight line with slope `−1/λ` = decremental; a flat line = regenerative. **Caveat for surface recording:** extracellular surface amplitude *always* attenuates with electrode-tissue geometry and shunting even for a regenerative AP, so a modest surface decrement is **not** by itself diagnostic — you must show the *intracellular* or normalized-source amplitude is constant, or compare the decrement slope against the passive λ predicted from independent `r_m`, `r_i` measurements. **Diagnostic strength: strong for "non-decremental ⇒ active"; weak for "decremental ⇒ passive" from surface data alone.**

---

## 2. All-or-none vs graded threshold behaviour

**(a) Observable.** Peak amplitude and waveform as a function of stimulus strength, at fixed recording site.

**(b) Active predicts.** A sharp **threshold**: sub-threshold → no propagated event; supra-threshold → a **stereotyped, fixed-amplitude** spike whose size and shape are **independent of stimulus magnitude**. AP amplitude is set by the ionic battery (Cl⁻/K⁺ reversal), not the stimulus.

**(c) Passive predicts.** **Graded** amplitude that scales continuously with stimulus intensity, with no discrete threshold. **VP amplitude scales with wound/heat intensity** (Vodeneev et al. 2011); **SP amplitude and even polarity depend on the concentration and chemical identity of the applied substance** — "graded signals of variable size" that "do not obey the all-or-none rule" (Zimmermann et al. 2009).

**(d) How to measure.** Deliver a graded stimulus series (electrical current steps, or graded cooling/heating/pressure) and plot peak amplitude vs stimulus. All-or-none = step/plateau function with a knee at threshold; passive/VP/SP = monotonic continuous curve. Extracellularly this is fully accessible: hold surface-electrode geometry constant and vary only the stimulus. **This is one of the most diagnostic single tests** — a genuine plateau (constant amplitude over a range of supra-threshold stimuli) is hard to fake by a passive process.

---

## 3. Refractory period — paired-pulse protocol

**(a) Observable.** Response to a second stimulus delivered at interval Δt after a conditioning stimulus.

**(b) Active predicts.** An **absolute refractory period** (no second event possible, channels inactivated) followed by a **relative refractory period** (higher threshold / reduced amplitude), then full recovery. This is a hallmark of voltage-gated regeneration. In plants these are *long*: absolute ~2–4 min and relative ~6–8 min in the liverwort *Conocephalum*; Venus flytrap re-excitability returns after ~2–10 s for the touch AP, with a distinct ~3-min refractory period for the heat-induced Ca²⁺-AP (values from the *Conocephalum* electrophysiology literature reviewed in Sukhov et al.; Dionaea values from the trap-closure/counting literature, e.g. Current Biology 2023). Refractoriness is also what enforces **unidirectional / non-summating** propagation.

**(c) Passive predicts.** **No refractory period.** A decremental electrotonic potential, a hydraulic wave, or a chemically driven VP can be re-evoked immediately and will **summate**; a second stimulus during the first response simply adds. VPs notably lack a true refractory period and can overlap.

**(d) How to measure (incl. extracellular).** Paired identical stimuli at systematically varied Δt (e.g., 1 s → 10 min), record at a downstream surface electrode, plot second-response amplitude/probability vs Δt. A recovery curve rising from 0 (absolute) through a graded zone (relative) to 100% = active. Flat 100% at all Δt with summation = passive. **Diagnostic strength: strong.** A clean absolute-refractory window is essentially incompatible with pure electrotonic or hydraulic spread.

---

## 4. Conduction-velocity constancy, and independence from stimulus strength and from amplitude

**(a) Observable.** Propagation velocity `v` (from arrival-time differences across the electrode array) as a function of (i) distance travelled, (ii) stimulus strength, (iii) event amplitude.

**(b) Active predicts.** `v` **constant along the path** and **independent of stimulus strength** and of the (fixed) amplitude — velocity is a property of the excitable cable, not the stimulus. AP velocities: higher plants ~0.3–7 cm s⁻¹ (e.g., tomato 3.6 cm min⁻¹; sunflower ~0.09 cm s⁻¹); Characean algae 11–44 mm s⁻¹ (species-dependent); Dionaea AP ~5–25 cm s⁻¹ (fast, myelin-free, phloem/excitable-tissue conducted).

**(c) Passive predicts.** No well-defined constant velocity. An **electrotonic** potential has effectively "instantaneous" foot-spread with a distance-dependent apparent delay (RC charging), so apparent `v` *falls* with distance. A **VP slows and its velocity varies** with distance, stimulus type and species (Vodeneev et al. 2011); a **hydraulic** wave would instead be near-sonic and a **mass-flow chemical** signal tracks sap-flow velocity (~mm s⁻¹; see §8). SP travels at a characteristic ~5–10 cm min⁻¹ set by the H⁺-pump kinetics, not by excitable-cable properties.

**(d) How to measure.** Cross-correlate arrival times at ≥3 collinear surface electrodes; compute segment-wise velocities. Constant across segments and across a graded stimulus series ⇒ active. Systematic slowing with distance, or velocity scaling with stimulus, ⇒ passive/decremental. **Independence of v from amplitude is diagnostic**; **velocity magnitude alone is only suggestive** (some plant APs are slower than some VPs are fast, so ranges overlap).

---

## 5. Temperature dependence (Q10) of velocity and kinetics

**(a) Observable.** Velocity and AP rise/decay time constants vs temperature; compute `Q10` and Arrhenius activation energy.

**(b) Active predicts.** Strong temperature sensitivity of a **rate-limited, enzyme/channel-gated** process: `Q10 ≳ 2–3`, i.e., high activation energy, because regeneration depends on channel gating kinetics. In *Nitella flexilis*, cooling 28 → 3 °C lengthens AP rise and decay times by ~**two orders of magnitude**, with Arrhenius activation energy ~**24 kcal mol⁻¹** and a slope break near 13.5 °C, while spike **shape is preserved** and amplitude falls from ~125 mV to ~65 mV (Hogg/Williams-type BBA study, 1974). High Q10 of *velocity* specifically points to a gating-limited regenerative wave.

**(c) Passive predicts.** Weak temperature dependence approaching that of **electrical/physical conduction** (`Q10 ≈ 1`) for a purely electrotonic or hydraulic pressure signal — a pressure wave's speed depends on bulk modulus/geometry, essentially temperature-flat over physiological ranges. A **mass-flow chemical** VP would track the temperature dependence of *sap viscosity/flow*, an intermediate and distinctly non-channel signature. Note VP *generation* (the local membrane response) is metabolically temperature-sensitive even though VP *propagation* may be hydraulic — so measure Q10 **of velocity**, not of amplitude.

**(d) How to measure.** Clamp a defined path segment in a temperature-controlled jacket; vary segment temperature independently of stimulus site; measure velocity across that segment only. Q10 ≳ 2 with a channel-like activation energy ⇒ active gating-limited; Q10 ≈ 1 ⇒ physical/electrotonic/hydraulic. **Diagnostic strength: strong for separating channel-gated propagation from hydraulic**, because the predicted Q10s differ several-fold.

---

## 6. Ion substitution and pharmacology

**(a) Observable.** AP/VP/SP presence, amplitude and velocity after bathing/perfusing with ion-substituted media or channel/pump blockers.

**(b) Active predicts (AP).** Abolition or graded modification by blockers of the **specific regenerative currents**: in plants the depolarizing phase is **Ca²⁺-influx-gated Cl⁻ efflux** (anion-channel block, e.g. via anthracene-9-carboxylic acid / DIDS, or Cl⁻-substitution, abolishes the AP), Ca²⁺-channel block (La³⁺, Gd³⁺, verapamil, EGTA) removes the trigger, and K⁺-channel block (TEA) slows repolarization. Chara/Nitella AP inward current is carried by **Cl⁻ efflux**, not Na⁺/Ca²⁺ entry directly — a plant-specific signature (reviewed in the Characean/liverwort AP evolution literature, PMC9510943). Removal of the regenerative ion ⇒ loss of the all-or-none event = diagnostic that those channels *generate* propagation.

**(c) Passive predicts.** A purely electrotonic potential is **insensitive to channel blockers** (it is passive RC spread). A **VP** is suppressed by **Ca²⁺ removal/EGTA** and by **metabolic/H⁺-ATPase inhibitors (CN⁻, NaN₃, vanadate)** because its membrane component is a **pump-inactivation** response (Katicheva et al. 2014; Vodeneev et al. 2011) — but crucially the VP can still **propagate through a zone where generation is pharmacologically blocked** (cold, CN⁻, EGTA segment), revealing that the travelling agent bypasses the membrane machinery (Vodeneev et al. 2015). **SP** is defined by **P-type H⁺-ATPase activation**: **vanadate abolishes it, fusicoccin mimics/enhances it** (Zimmermann et al. 2009).

**(d) How to measure (incl. extracellular).** Localized perfusion of a defined path segment (agar bridge / cuvette) so you can dissociate *generation* from *conduction*. Key experiment: block the **middle** segment and test whether the signal still arrives downstream. If it crosses a channel-blocked/killed zone ⇒ the propagating agent is **not** the membrane-regenerative wave in that zone (points to hydraulic/chemical, §8). If it is stopped ⇒ conduction requires living excitable membrane = active. **This "block-the-bridge" design is among the most diagnostic**, because it directly separates the machinery of generation from the identity of the courier.

---

## 7. Waveform-shape preservation vs progressive low-pass dispersion

**(a) Observable.** Rise time, half-width and spectral content of the recorded transient at successive electrodes.

**(b) Active predicts.** **Shape invariance** with distance: because the wave is regenerated at each point, rise time and half-width stay ≈constant; the high-frequency content is restored at every step. (In *Nitella*, changing temperature changes kinetics but *shape is conserved* — the regenerative signature.)

**(c) Passive predicts.** A passive cable is a **distributed RC low-pass filter**: as an electrotonic transient spreads, it **loses high-frequency content, its rise time lengthens, its half-width broadens, and its peak falls** — progressive **dispersion**. A hydraulic-triggered VP likewise **broadens and slows** downstream (long-duration, irregular waveform with superimposed spikes vs the clean AP spike).

**(d) How to measure.** From the multi-electrode array, plot rise time and half-width vs distance, and compute the transfer function (FFT ratio) between successive electrodes. Flat rise time + white-ish transfer ratio = regenerative. Monotonic rise-time increase + low-pass transfer ratio (high-freq attenuation growing with distance) = passive electrotonic/hydraulic. **Diagnostic strength: strong.** Progressive low-pass dispersion is a near-unique fingerprint of passive spread; its *absence* over many λ argues for regeneration. (Watch the artifact: surface electrodes themselves low-pass filter, so use identical electrodes and normalize.)

---

## 8. Separating hydraulic / chemical propagation from true electrical propagation (VP-specific; Family B)

This is the plant-specific crux, focused on the **VP**. The candidate couriers are: (i) a true propagated electrical wave, (ii) a **hydraulic pressure wave** (Ricca 1916 originally; near-sonic), and (iii) a **chemical "Ricca's factor" carried by xylem mass flow**. Current evidence favors (iii) for the VP.

**8.1 Ricca-factor / dead-tissue transmission test.**
- *Observable:* does the signal cross a **killed or steam-girdled** zone?
- *Active-electrical predicts:* **no** — a regenerative membrane wave cannot cross dead tissue.
- *Hydraulic/chemical predicts:* **yes** — a pressure wave or a xylem-borne chemical crosses dead xylem, because xylem conduits are dead at maturity. Ricca's classic result (chemical crossing a killed gap in *Mimosa*) is the original such test.
- *Measure:* localized heat-kill or steam-girdle a stem segment, wound distally, record proximally. Transmission through dead tissue ⇒ courier is hydraulic/chemical.

**8.2 Xylem-severing / flow-interruption test.**
- Cut or clamp the xylem (or block phloem separately) between wound and electrode. VP loss on xylem interruption but survival on phloem interruption ⇒ **xylem-borne** courier.
- Evans & Morris (2017, *Plant Journal*) showed VP speed in wheat (~1.7 mm s⁻¹; "average 1.66 mm s⁻¹") matches a **leaky-pipe xylem mass-flow model**, with background xylem flow ~0.8 mm s⁻¹ (wheat), ~0.4 mm s⁻¹ (*Ricinus*); phloem and epidermal VP velocities were *similar* (~0.8–2.5 mm s⁻¹), **contradicting** the pure-hydraulic prediction that phloem should be 5–10× faster.

**8.3 Timing / velocity signature.**
- A **hydraulic pressure wave** propagates near the speed of sound in water (orders of magnitude faster than any observed VP) — so an observed VP velocity of ~mm s⁻¹ **excludes a pure pressure wave as the carrier of the slow VP front**, though a fast pressure transient can still be the *trigger*.
- A **mass-flow chemical** signal should travel at **sap-flow velocity** and be **direction-biased** (basipetal/acropetal with transpiration). Turbulent/shear-enhanced dispersion gives effective diffusion coefficients ~0.05–0.12 cm² s⁻¹, ~2000× molecular diffusion (Vodeneev et al. 2012; Evans & Morris 2017; shear-dispersion model, *Front. Plant Sci.* 2019) — a distinctive intermediate regime.

**8.4 Direct pressure measurement.**
- Insert a **pressure probe / xylem-pressure sensor** (or turgor probe) alongside the electrodes. **Temporal coincidence** of a xylem/turgor pressure transient with the depolarization front, and its propagation with the VP, is the positive signature of a hydraulic trigger. Mechanosensitive-channel blockers (e.g. Gd³⁺) that uncouple pressure from depolarization further implicate a hydraulic→mechanoreceptor transduction step.

**8.5 Cut-and-block timing (upper-bound velocity).**
- Sectioning the leaf a fixed time after wounding and asking whether the VP had already passed sets an **upper velocity bound**: Vodeneev et al. (2012) — sectioning 1 s post-wound blocked transmission, bounding the axial signal at ≲3 cm s⁻¹, far below pressure-wave speed.

**8.6 Tracer / dye co-transport.**
- Introduce a dye or radiotracer at the wound; if the VP front **co-migrates with the tracer** in the xylem, the courier is mass-flow chemical (radiotracer translocation was enhanced by wounding; Vodeneev et al. 2012).

**Verdict for Family B:** the combination of (dead-tissue transmission) + (xylem dependence) + (velocity = sap-flow, not sonic) + (tracer co-migration) is **diagnostic of hydraulic/chemical (non-electrical) courier**. Any single one is only suggestive.

---

## 9. Diagnostic vs merely suggestive — summary

**Diagnostic (hard to counterfeit):**
- **All-or-none amplitude plateau** across supra-threshold stimuli (§2) → active.
- **Absolute refractory window** with a graded recovery curve, paired-pulse (§3) → active.
- **Velocity independence from stimulus strength and from amplitude** (§4) → active.
- **Absence of progressive low-pass dispersion / rise-time constancy over many λ** (§7) → active; **its presence** → passive.
- **Transmission across dead/steam-girdled tissue** and **xylem-dependence with sap-flow velocity + tracer co-migration** (§8) → hydraulic/chemical, i.e., *not* a regenerative electrical wave.
- **Q10 of velocity** separating channel-gated (~2–3) from physical/hydraulic (~1) (§5).
- **"Block-the-bridge" pharmacology**: signal crossing a channel-blocked segment (§6) → non-membrane courier.

**Merely suggestive (necessary but not sufficient / range-overlapping):**
- **Absolute velocity magnitude** (AP and fast-VP ranges overlap) (§4).
- **Surface-electrode amplitude decrement** alone (surface geometry always attenuates) (§1).
- **Polarity** (hyperpolarizing ⇒ SP; but depolarizing is shared by AP and VP) — useful for *classifying* SP, weak for active/passive.
- **Sensitivity to Ca²⁺/anion-channel blockers** (blocks both AP generation *and* VP membrane response) (§6) — informative only when combined with the generation/conduction dissociation design.
- **Waveform "cleanliness"** (spike vs long irregular deflection) — strongly associated with AP vs VP but not by itself mechanistic.

**Practical minimal battery for a real recording rig:** a linear surface Ag/AgCl multi-electrode array (≥4 sites) + high-Z DC amplifier, run through (i) graded-stimulus amplitude/velocity curves (§2, §4), (ii) paired-pulse (§3), (iii) a temperature-clamped middle segment (§5), (iv) a "block/kill/sever the bridge" segment with a co-located pressure probe and tracer (§6, §8). That set jointly resolves AP (active/regenerative) vs VP (hydraulic-chemical + local pump-inactivation) vs SP (graded pump-activation).

---

### Confidence notes
- **High confidence** (directly fetched primary/review text): SP parameters and mechanism (Zimmermann et al. 2009); VP decrement ~10%/cm, graded, H⁺-ATPase inactivation, chemical/hydraulic (Vodeneev et al. 2011/2012/2015; Katicheva et al. 2014; Sukhov et al. 2014); Evans & Morris 2017 mass-flow numbers; surface vs metal electrode methodology.
- **Medium confidence** (from search snippets of the primary source, not full-text-verified here): *Conocephalum* refractory 2–4 / 6–8 min; *Nitella flexilis* 24 kcal mol⁻¹ activation energy and 13.5 °C break (BBA 1974); Characean AP 11–44 mm s⁻¹; Dionaea AP 5–25 cm s⁻¹ and refractory 2–10 s / 3-min heat-AP.
- **Theory-grounded, not plant-measured here** (low confidence on plant-specific λ values): explicit numeric space-constant λ for higher-plant phloem — cable theory is standard, but I did not verify a specific published plant λ value, so treat §1's λ magnitude as order-of-magnitude only.