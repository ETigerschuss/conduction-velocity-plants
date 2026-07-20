## Active vs passive propagation: what THIS dataset can and cannot decide

**Setup recap.** Two inline surface electrodes (near, far), both *downstream* of one wound/flame stimulus, 5 kHz sampling, known inter-electrode spacing d (mm), two event markers bracketing stimulation, 13 species / ~165 usable recordings. A companion pipeline already computes per-recording attenuation, broadening, waveform correlation, inter-channel delay and CV (`C:\Users\serbe\conduction-velocity-plants\cvplants\analysis.py`; species medians in `C:\Users\serbe\conduction-velocity-plants\REPORT.md`).

**The one structural advantage to exploit.** Because both electrodes lie on the same conduction path and see the *same* travelling wave, the only thing that differs between them is the extra propagation distance = the *known* spacing d. So every **near→far transformation** metric (decrement, dispersion, delay) is anchored to a measured distance, which sidesteps the fact that the *wound-to-electrode* distance is unknown. That is the axis on which active vs passive actually separates. Any metric that needs the wound-to-electrode distance (absolute amplitude, absolute latency) is much weaker here.

**The physiology being discriminated (grounded).**
- *Active* propagation = self-regenerating, ion-channel-mediated action potential (AP): all-or-none, **non-decremental** amplitude, roughly **constant velocity**, shape-preserving, with a refractory period. **[CORRECTED]** Fromm & Lautner (2007, *Plant, Cell & Environment* 30:249–257) report that most plant APs propagate at **0.005–0.2 m/s (i.e. ~5–200 mm/s)**; the frequently quoted **~20–30 mm/s is their value for the *Mimosa* leaf pinna specifically**, not a universal plant-AP figure. The CVs actually observed in *this* dataset fall in a narrower ~1–40 mm/s band (see REPORT.md) — that band is the dataset's own range, not Fromm & Lautner's stated range. The fast-movement plants (Venus flytrap, *Mimosa pudica*) fire textbook all-or-none APs tied to a Ca²⁺ threshold (Hedrich 2023, *New Phytologist*, "Demystifying the Venus flytrap action potential"; note Hedrich frames the *critical* Ca²⁺ threshold chiefly in the context of trap-closure counting, while each AP carries its own Ca²⁺ transient).
- *Passive* propagation here means the **variation potential (VP) / slow-wave / hydraulic-chemical** regime: **decremental** (amplitude falls ~10 % cm⁻¹ in pumpkin and wheat), velocity and amplitude both **graded with stimulus intensity and distance from the wound**, irregular multi-component shape, driven by a xylem pressure/mass-flow wave carrying wound chemicals (**[CORRECTED author name]** Vodeneev, **Akinchits** & Sukhov 2015, *Plant Signaling & Behavior*, "Variation potential in higher plants: mechanisms of generation and propagation" — the draft's "Katicheva" is wrong; Katicheva is a Vodeneev co-author on *other* AP papers, not this 2015 PSB review; Malone & Stankovic 1991, *Plant, Cell & Environment*; Evans et al. 2017, *The Plant Journal*). Xylem "turbulent diffusion" coefficients are ~0.05–0.12 cm² s⁻¹ (D ≈ 0.05 for wheat, ≈ 0.12 for pumpkin; Vodeneev et al. 2015) — this sets a quantitative diffusive benchmark used in Analysis 2 below.
- The source dataset itself reports information-transfer speeds of ~2–9 mm/s and responses in ~60 % of plants, ~3–6 s after stimulus ("A library of electrophysiological responses in plants," *Plant Signaling & Behavior* 2024, PubMed 38493508; biorxiv 2023.09.29.560074) — i.e. squarely in the ambiguous band where AP and VP overlap, which is exactly why waveform-transformation analyses (not raw speed) are needed.

**One dataset-wide confound that reframes everything (flag first).** The Plant SpikerBox analog front end is a **0.07–8.8 Hz band-pass** (confirmed in BYB's official Plant SpikerBox documentation; gain 72×, two-silver-wire electrode cable). The 0.07 Hz high-pass removes the slow DC depolarization that *is* the defining feature of a VP, and differentiates the signal. So a slow passive VP can appear on the surface trace as a **spiky AC-coupled derivative** that superficially resembles an AP. Sample rate (5 kHz) is not the binding limit — the ~8.8 Hz low-pass is: it caps rise-time resolution at ~0.1 s and smears all events toward similar smooth shapes, which **inflates waveform-similarity and compresses rise-time contrasts** (Analyses 4, 3). Every "it looks like a spike, therefore active" argument is defeated by this filter. This is why the discriminators below lean on *distance-scaling* of transformation metrics rather than on shape alone.

---

## Ranked analyses (discriminating power × feasibility)

### 1. Amplitude decrement per unit distance (the classic active/passive test)
- **Quantity.** Per recording, attenuation ratio A_far/A_near (already computed as `attenuation_far_near`). Convert to a distance-normalized decrement: fractional loss per mm = (1 − A_far/A_near)/d, or a length constant λ = d / ln(A_near/A_far). Then **regress ln(A_far/A_near) on spacing d** across recordings (pooled, and within the multi-spacing species such as Marijuana, 16–29 mm).
- **Statistical test.** (a) One-sample Wilcoxon signed-rank on A_far/A_near vs 1 (per species). (b) Linear mixed model / OLS of ln(ratio) ~ d with species as random effect; test slope < 0. (c) Compare species medians of per-mm decrement to the literature VP value (~10 % cm⁻¹ = ~1 % mm⁻¹).
- **ACTIVE prediction.** Ratio ≈ 1, **no** systematic dependence on d (slope ≈ 0); λ effectively infinite. Non-decremental.
- **PASSIVE prediction.** Ratio < 1 and **more attenuation at larger d** (slope significantly negative), decrement on the order of ~1 % mm⁻¹ (Vodeneev et al. 2015).
- **Dominant confounds.** *Electrode contact variability is the killer for the single-recording ratio* — unequal near/far coupling changes A_far/A_near with no biology involved. Mitigation: contact noise is *distance-independent*, so the **slope vs d** (not the raw ratio) is the confound-robust statistic. Surface amplitude ≠ intracellular amplitude; the 0.07 Hz high-pass distorts absolute amplitude of slow components. Wound-to-electrode distance is unknown, so this tests decrement over the *inter-electrode* interval only, not the full decay curve.
- **Why ranked #1.** Highest textbook discriminating power, already implemented, and the distance-regression form neutralizes its worst confound.

### 2. Delay-vs-distance scaling: ballistic (∝ d) vs diffusive (∝ d²)
- **Quantity.** Inter-channel delay Δt from windowed cross-correlation (`xcorr_delay_s`) and peak delay (`peak_delay_s`), paired with known spacing d. Fit pooled Δt vs d to **both** a linear model (Δt = d/v, ballistic conduction) and a diffusive model (Δt ∝ d²/D, giving apparent D to compare against the xylem 0.05–0.12 cm² s⁻¹ benchmark).
- **Statistical test.** Model comparison by AIC/BIC and adjusted R² between Δt ~ d and Δt ~ d²; bootstrap CI on the exponent b in log Δt = log k + b·log d (test b = 1 vs b = 2).
- **ACTIVE prediction.** b ≈ 1 (constant velocity, delay linear in distance); implied v in the mm/s–cm/s ion-channel band, independent of medium.
- **PASSIVE prediction.** If transport-limited diffusion/hydraulic dispersion, b ≈ 2 and the fitted D lands near the xylem turbulent-diffusion range; a pure pressure wave would instead give implausibly high, near-constant speed.
- **Dominant confounds.** Only **one (d, Δt) point per recording** (single wound, two electrodes) → the exponent must be estimated by *pooling across recordings with different spacings*, which mixes plants, wounds and hydration. Best done within one species that has a spacing spread (Marijuana) or by many recordings per species. Wound-to-electrode distance unknown means we test scaling over the inter-electrode gap, assuming the wave is in steady state there.
- **Why ranked #2.** Mechanistically decisive (ballistic vs diffusive is the crux of active vs passive), feasible from existing fields, but power is limited by the one-point-per-recording geometry.

### 3. Temporal broadening / dispersion per unit distance
- **Quantity.** FWHM_far/FWHM_near (`broadening_far_near`) and rise-time ratio (`rise_ratio_far_near`); normalize per mm and regress on d.
- **Statistical test.** Wilcoxon signed-rank on broadening ratio vs 1; OLS of broadening ~ d (slope > 0 ⇒ dispersive).
- **ACTIVE prediction.** Shape restored at each point → ratio ≈ 1, rise time preserved, **no** growth with distance.
- **PASSIVE prediction.** Cable/diffusive low-pass → far waveform broadened (ratio > 1), slower rise, high-frequency content lost, broadening increasing with d.
- **Dominant confounds.** The ~8.8 Hz analog low-pass already broadens *both* channels and compresses the contrast (both share the filter, so the *ratio* is still fair, but the dynamic range is small). Contact/SNR differences add noise. **Orthogonal to the contact-gain confound of Analysis 1** (broadening is amplitude-independent), so it is the ideal cross-check: the REPORT already finds attenuation and broadening co-vary (ρ ≈ −0.26) — the decremental↔regenerative fingerprint.
- **Why ranked #3.** Strong, implemented, and independent of the amplitude/contact confound that weakens #1.

### 4. Peak-minus-onset delay asymmetry (rigid-translation test)
- **Quantity.** (peak_delay_s − onset_delay_s) per recording — both already computed.
- **Statistical test.** One-sample Wilcoxon on the difference vs 0.
- **ACTIVE prediction.** A ballistic wave translates rigidly: onset and peak shift by the *same* Δt ⇒ difference ≈ 0.
- **PASSIVE prediction.** Dispersive/diffusive spread makes the peak lag more than the leading edge ⇒ peak_delay > onset_delay systematically (> 0).
- **Dominant confounds.** Onset detection is noise-sensitive (20 % threshold); low SNR inflates the difference. Cheap corroborator, not a standalone verdict.
- **Why ranked #4.** Nearly free (uses existing fields), amplitude-independent, and captures dispersion in a way that complements #3.

### 5. Amplitude ↔ velocity / amplitude ↔ decrement coupling (all-or-none proxy)
- **Quantity.** Within each species, Spearman correlations: corr(near_peak_amp, CV) and corr(near_peak_amp, A_far/A_near).
- **Statistical test.** Per-species Spearman with permutation p; combine across species (Fisher / sign test on the correlation signs).
- **ACTIVE prediction.** All-or-none ⇒ amplitude **decoupled** from velocity and from decrement (correlations ≈ 0): once threshold is crossed, size doesn't set speed.
- **PASSIVE prediction.** VP is graded by stimulus/pressure intensity ⇒ bigger responses travel faster and decrement less: **positive** amp–velocity, **negative** amp–attenuation coupling.
- **Dominant confounds.** This is the *closest in-data substitute for the missing threshold ladder*, but it is fragile: unknown stimulus intensity means the natural amplitude variation is uncontrolled, and **electrode contact variability injects amplitude scatter that is biologically meaningless**, potentially masking or faking coupling. Interpret as suggestive only.
- **Why ranked #5.** Medium power (it partially proxies all-or-none, which otherwise needs a new experiment) but confound-heavy.

### 6. Waveform self-similarity between channels
- **Quantity.** Max normalized cross-correlation near vs far (`xcorr_corr`).
- **Statistical test.** Compare distributions across the fast-movement plants vs the rest (Mann–Whitney); rank species.
- **ACTIVE prediction.** High similarity (≈0.9), shape invariant with distance (Venus flytrap, Mimosa in the REPORT sit at ≈0.90–0.93).
- **PASSIVE prediction.** Lower similarity as dispersion distorts the multi-component VP shape.
- **Dominant confounds.** The 8.8 Hz low-pass smooths everything toward similar shapes, **inflating** similarity for all recordings and shrinking the contrast; SNR-sensitive. Corroborator, not decisive.
- **Why ranked #6.** Useful for the species ranking/clustering already in the REPORT, but the filter confound caps its power.

### 7. Velocity magnitude vs mechanistic benchmarks
- **Quantity.** CV distribution (`cv_xcorr_mm_s`) per species vs reference bands: molecular diffusion (far too slow), plant AP **~5–200 mm/s per Fromm & Lautner 2007 (the dataset's own CVs fall in ~1–40 mm/s)**, VP ~mm/s, hydraulic pressure wave (near speed of sound, far too fast).
- **Statistical test.** Descriptive banding + between-species Kruskal–Wallis (REPORT: Venus flytrap 24.7 mm/s, Mimosa 12.8, slow mints ~2–4 mm/s).
- **ACTIVE prediction.** mm/s–cm/s, medium-independent, clustered per species.
- **PASSIVE prediction.** Either tracks bulk-flow velocity or shows the diffusive d² scaling of Analysis 2.
- **Dominant confounds.** CV = d/Δt inherits the wound-to-electrode ambiguity (a wave decelerating away from the wound will read differently depending on where the pair sits); most species have a narrow spacing range, so "constant CV" and "constant Δt" are hard to separate. Weak on its own — its value is as context for #1–#3.

**Recommended reading of the ensemble.** No single metric is decisive under these confounds. The defensible claim comes from the **joint decremental↔regenerative axis**: a recording is *active-like* when attenuation ≈ 1 AND broadening ≈ 1 AND peak−onset ≈ 0 AND amp is decoupled from CV AND delay scales linearly with d; *passive-like* when the opposite co-occurs. The REPORT's finding that this axis is convergent (Venus flytrap + Mimosa cluster together across families) is the strongest in-data signature of genuine active conduction. Classify each *event* on this axis before pooling — do not average an AP plant with a VP plant.

---

## Questions that CANNOT be answered from this data, and the minimal new experiment for each

1. **True all-or-none vs graded (threshold behaviour).** One wound per recording and unknown stimulus intensity make a stimulus–response curve impossible; Analysis 5 only proxies it. **Minimal experiment — threshold/intensity ladder:** apply graded stimuli (increasing flame duration/heat dose or touch force) to one fixed site, measure response amplitude and CV vs intensity. Active ⇒ step function (no response below threshold, fixed amplitude above); passive ⇒ smoothly graded amplitude ∝ intensity (Vodeneev, Akinchits & Sukhov 2015).

2. **Refractory period.** A single stimulus per recording precludes any inter-stimulus-interval test. **Minimal experiment — paired-pulse refractory:** two stimuli at the same site separated by Δt spanning ~0.5–20 min, measure whether the second response is abolished/reduced. Active APs show absolute then relative refractoriness (in liverwort *Conocephalum* ~2–4 min absolute, ~6–8 min relative; Fromm & Lautner 2007); a purely hydraulic/passive wave shows little or no refractoriness.

3. **Regenerative (ion-channel) mechanism.** Surface AC-coupled traces cannot prove that voltage-gated channels regenerate the signal. **Minimal experiment — pharmacology / ion substitution:** apply Ca²⁺-channel blockers (La³⁺, Gd³⁺), anion-channel blockers (A-9-C, DIDS) or K⁺ blockers (TEA), or remove external Ca²⁺, on the stem segment *between* wound and electrodes; compare amplitude/CV before vs after. Active AP is abolished or slowed (Ca²⁺-dependent; Hedrich 2023); a hydraulic pressure/mass-flow VP is comparatively insensitive.

4. **Active vs passive conduction machinery via temperature (Q10).** Only single-temperature records exist. **Minimal experiment — temperature/Q10 series:** repeat at controlled temperatures (e.g. 15/25/35 °C) and compute Q10 of CV. Active, enzyme/channel-gated conduction ⇒ Q10 ≈ 2–3; passive electrotonic/hydraulic conduction ⇒ Q10 ≈ 1 (or set by water viscosity). *(**[UNVERIFIABLE — FLAGGED]** These Q10 magnitudes are a standard general-biophysics expectation; no plant-conduction-specific measured Q10 primary source was located. Treat as a hypothesis-generating design rationale, not a cited fact.)*

5. **Hydraulic vs electrical primacy.** Cannot separate a pressure wave from a membrane wave with electrical channels alone. **Minimal experiment — simultaneous mechanical readout:** co-record stem strain / leaf-thickness (or xylem pressure) with the two electrodes; if the electrical event tracks the pressure/thickness wave it is hydraulic/passive, if it outruns or decouples from it, it is active (Malone & Stankovic 1991; Evans et al. 2017).

6. **Bidirectionality / antidromic propagation.** Both electrodes are downstream and inline, so direction-independence is untestable. **Minimal experiment — electrodes proximal AND distal to a non-wounding stimulus site:** a regenerative AP propagates in both directions and can be initiated anywhere above threshold; a wound-driven hydraulic VP propagates directionally from the damage.

7. **Amplitude/velocity decay vs true wound-to-electrode distance.** Inter-electrode spacing is known but wound-to-electrode distance is not, so the full decay curve is inaccessible. **Minimal experiment — wound-distance series:** on one plant, wound at several *measured* distances from a fixed electrode pair; a passive VP decrements ~1 %/mm and slows with distance, an active AP does neither.

**Feasibility note.** Analyses 1–7 in the ranked list require no new data and are largely already coded in `C:\Users\serbe\conduction-velocity-plants\cvplants\analysis.py`; what is missing is (i) distance-normalization of attenuation/broadening, (ii) the Δt∝d vs d² model comparison (Analysis 2), (iii) the peak−onset asymmetry test (Analysis 4), and (iv) the within-species amplitude–CV/attenuation coupling (Analysis 5).

**Sources:** [Fromm & Lautner 2007, Plant Cell Environ (general plant-AP velocity 0.005–0.2 m/s; Mimosa pinna ~20–30 mm/s; Conocephalum refractory 2–4 / 6–8 min)](https://onlinelibrary.wiley.com/doi/10.1111/j.1365-3040.2006.01614.x) · [Vodeneev, Akinchits & Sukhov 2015, Plant Signal Behav — 10%/cm decrement, D 0.05–0.12 cm²/s](https://pmc.ncbi.nlm.nih.gov/articles/PMC4883923/) · [Malone & Stankovic 1991, Plant Cell Environ](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1365-3040.1991.tb00953.x) · [Evans et al. 2017, Plant J](https://pmc.ncbi.nlm.nih.gov/articles/PMC5601289/) · [Hedrich 2023, New Phytologist](https://nph.onlinelibrary.wiley.com/doi/full/10.1111/nph.19113) · [BYB plant library 2024, Plant Signal Behav](https://pubmed.ncbi.nlm.nih.gov/38493508/) · [BYB Plant SpikerBox documentation — 0.07–8.8 Hz, gain 72×, silver wires](https://docs.backyardbrains.com/plant/plant-spikerbox/) · [BYB conduction-velocity blog](https://blog.backyardbrains.com/2024/01/conduction-velocity-in-different-plants/)