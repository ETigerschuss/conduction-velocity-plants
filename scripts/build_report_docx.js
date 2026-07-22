// Build the Word report for the conduction-velocity-plants project.
// Usage: NODE_PATH=<global node_modules> node scripts/build_report_docx.js
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  ImageRun, Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType,
  PageBreak, LevelFormat,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const FIG = path.join(ROOT, "results", "figures");
const DIMS = JSON.parse(fs.readFileSync(path.join(FIG, "_dims.json"), "utf8"));
const MAXW = 600, MAXH = 720;
const ACCENT = "1f3f66";

function fit(file) {
  const [w, h] = DIMS[file];
  const s = Math.min(MAXW / w, MAXH / h, 1);
  return { width: Math.round(w * s), height: Math.round(h * s) };
}
let FIGN = 0, SECN = 0;
function figure(file, caption) {
  FIGN += 1;
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160, after: 40 },
      children: [new ImageRun({ data: fs.readFileSync(path.join(FIG, file)), type: "png", transformation: fit(file) })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
      children: [new TextRun({ text: `Figure ${FIGN}. ${caption}`, italics: true, size: 17, color: "555555" })] }),
  ];
}
function h1(txt) { SECN += 1; return new Paragraph({ text: `${SECN}. ${txt}`, heading: HeadingLevel.HEADING_1, spacing: { before: 260, after: 120 } }); }
function p(runs) {
  const children = Array.isArray(runs) ? runs : [new TextRun({ text: runs, size: 22 })];
  return new Paragraph({ children, spacing: { after: 120 }, alignment: AlignmentType.JUSTIFIED });
}
function b(text) { return new TextRun({ text, bold: true, size: 22 }); }
function it(text) { return new TextRun({ text, italics: true, size: 22 }); }
function t(text) { return new TextRun({ text, size: 22 }); }
function bullet(text) {
  return new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 60 },
    children: [new TextRun({ text, size: 22 })] });
}
function cell(text, { header = false, w } = {}) {
  return new TableCell({
    width: { size: w, type: WidthType.DXA },
    shading: header ? { type: ShadingType.CLEAR, fill: ACCENT } : undefined,
    margins: { top: 60, bottom: 60, left: 90, right: 90 },
    children: [new Paragraph({ children: [new TextRun({ text, bold: header, color: header ? "FFFFFF" : "000000", size: 19 })] })],
  });
}
function table(headers, rows, widths) {
  const total = widths.reduce((a, c) => a + c, 0);
  const mk = (cells, header) => new TableRow({ children: cells.map((c, i) => cell(c, { header, w: widths[i] })) });
  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [mk(headers, true), ...rows.map((r) => mk(r, false))] });
}
const rule = () => new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "BBBBBB" } }, spacing: { after: 120 } });
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

const kids = [];

// -------- title
kids.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 400, after: 60 },
  children: [new TextRun({ text: "Conduction Velocity and Signal Propagation in Plants", bold: true, size: 40, color: ACCENT })] }));
kids.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 },
  children: [new TextRun({ text: "An automatic two-channel analysis pipeline, validated against the manual analysis", size: 24, color: "555555" })] }));
kids.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
  children: [new TextRun({ text: "13 species · 176 recordings (165 analysed) · github.com/ETigerschuss/conduction-velocity-plants", size: 18, color: "888888" })] }));
kids.push(rule());

// -------- 1. Overview
kids.push(h1("Overview and dataset"));
kids.push(p([t("Two recording electrodes are placed inline downstream of a wound / touch / flame stimulus; the propagating electrical potential (an action potential, AP, or a slow variation potential, VP) reaches the "), b("near"), t(" electrode first and the "), b("far"), t(" electrode later. Recordings are two-channel WAV; two event markers bracket the stimulation window. Inter-electrode distances were cross-referenced from the “Todo Data Resumen” spreadsheet (166/176 recordings). This report presents an automatic analysis pipeline that reproduces the manual conduction-velocity results, characterises how the signal is transformed from near to far, tests whether those properties track evolutionary relationship, asks whether propagation is active or passive, and simulates it with cable and biophysical models.")]));
kids.push(p([b("Headline results. "), t("(i) Automatic CV agrees with the manual analysis at "), b("Pearson r = 0.94 across 13 species"), t(" (0.98 excluding one species). (ii) Near→far, the signal attenuates (×0.44) and broadens (×1.31) while preserving its shape (r ≈ 0.80). (iii) These properties do "), b("not"), t(" track taxonomy. (iv) Venus flytrap and Sensitive Mimosa behave as fast, shape-preserving (active) conductors; the mints as slow, decremental (passive) ones. (v) A Hodgkin-Huxley-type Ca²⁺/Cl⁻/K⁺ plant-AP model, filtered like the recordings, reproduces the observed Venus waveform.")]));

// -------- 2. Methods
kids.push(h1("Methods"));
kids.push(p([t("Each channel is baseline-subtracted (pre-stimulus window) and low-pass filtered for detection. The dominant post-stimulus deflection is detected in each channel; the earlier-peaking channel is labelled "), b("near"), t(". Inter-channel delay is measured by windowed cross-correlation (primary) with a peak-to-peak cross-check, and — because the two electrodes share a soil/earth reference — also by a common-mode-robust 2-tap model (Section 5). Conduction velocity = inter-electrode distance / delay. Transformation metrics: amplitude attenuation (far/near peak), temporal broadening (far/near FWHM), and waveform similarity (max normalised cross-correlation). Recordings are quality-gated (near-synchronous peaks, low waveform similarity, or low SNR); 165/176 pass. The pipeline (Python: cvplants/) reports three CV columns per recording: "), it("cv_xcorr"), t(" (default), "), it("cv_2tap"), t(" (common-mode-robust), and "), it("cv_manual"), t(" (distance ÷ the experimenters’ manual delay).")]));

// -------- 3. Conduction velocity
kids.push(h1("Conduction velocity"));
kids.push(p([t("Median CV per species ranges from ~2 mm/s (Argentian Dollar) to ~28 mm/s (Venus flytrap). The estimate is internally validated three ways: our automatic delay matches the experimenters’ manual delay (Spearman ρ = 0.80), the delay scales with electrode distance (ρ = 0.36, p = 3×10⁻⁶), and CV is independent of the spacing used (ρ ≈ 0) — as a true velocity must be.")]));
kids.push(...figure("cv_by_species.png", "Conduction velocity by species (resolved-delay recordings). Box = IQR, red = median, dots = recordings."));
kids.push(...figure("delay_validation.png", "Our measured inter-channel delay vs the experimenters’ manual delay (Tiempo): points on the identity line, for exact and order-inferred spreadsheet matches."));
kids.push(...figure("cannabis_distance_delay.png", "Cannabis: electrode distance vs propagation delay; slope is an aggregate conduction velocity."));

// -------- 4. Comparison with the manual analysis
kids.push(pageBreak());
kids.push(h1("Validation against the manual analysis (Contreras et al.)"));
kids.push(p([t("Validated against "), it("Electrical Conduction Velocity Across Species of Rapid Movement and Non-Rapid Movement Plants"), t(" (Contreras, Morales, Rojas, Serbe-Kamp, Marzullo; Plant Signaling & Behavior), Table 1. The accepted-recording counts match this repo’s WAV files species-by-species, so both analyses use the same recordings; the paper reports a per-species CV mean, so we compare mean-to-mean.")]));
kids.push(p([b("Strong agreement: Pearson r = 0.94 across 13 species (0.98 excluding Sensitive Mimosa). "), t("The non-rapid group mean matches almost exactly (automatic 8.0 ± 6.3 vs manual 7.7 ± 6.5 mm/s), and Venus flytrap agrees (automatic ~30 vs manual 35.3). Almost every species sits on the identity line within error.")]));
kids.push(...figure("compare_to_paper_scatter.png", "Automatic CV vs the manual CV, per species (mean ± SD). On the dashed identity line = agreement; only Sensitive Mimosa sits clearly below."));
kids.push(...figure("compare_to_paper_bars.png", "Per-species CV, manual analysis vs automatic pipeline (mean ± SD)."));
kids.push(p([b("Reproducing the manual numbers exactly. "), t("Using the experimenters’ own per-recording delays, the "), it("cv_manual"), t(" column reproduces the paper exactly (Sensitive Mimosa 30.6, Venus 35.7 mm/s). So the manuscript figures are recoverable from the pipeline; the automatic estimators agree for every species except Mimosa’s fast batch.")]));
kids.push(p([b("The Sensitive Mimosa discrepancy (manual 32.4, automatic 18.9) is understood. "), t("Recording-by-recording, the two delays match on the slow Mimosa recordings; the gap is a handful of fast recordings (their delay ~0.2–0.4 s) that carry a "), b("sharp fast AP plus large, slower bumps"), t(". The manual analyst tracked the fast AP (high CV); the automatic cross-correlation tracks the larger slow bump. We implemented and tested a fast-onset estimator (and three variants) against the manual delays: all were "), b("less"), t(" accurate — the default cross-correlation already matches the manual delays best (median error 0.20 s vs 1.80 s for fast-onset; Figure below). Mimosa’s manual SD (21.6) nearly equals its mean, so the exact value is intrinsically uncertain; both analyses agree it and Venus are the fast, rapid-movement outliers.")]));
kids.push(...figure("delay_estimator_bakeoff.png", "Delay-estimator bakeoff against the manual per-recording delays (lower = better). The default cross-correlation wins for every species; fast-onset variants were rejected on this evidence."));
kids.push(p([b("Metadata corrected from the paper: "), t("Hierbabuena = Clinopodium douglasii (not Mentha); Chilean Chile = Capsicum baccatum; Argentian Dollar = Plectranthus purpuratus. The amplifier passband is ~0.2–130 Hz (a custom rig), not the 0.07–8.8 Hz of the stock SpikerBox — which matters below.")]));

// -------- 5. Channel integrity
kids.push(pageBreak());
kids.push(h1("Channel integrity: the shared reference and how the delay is recovered"));
kids.push(p([t("Near/far is assigned per recording as the earlier-peaking channel (ch0 leads in ~76%); the delay magnitude, hence CV, does not depend on that label. The two channels are "), b("correlated, and that is expected"), t(": both electrodes share a soil/earth reference, so any whole-plant potential or reference fluctuation appears in both. The pre-stimulus baseline correlation is high (pooled r ≈ 0.66) precisely because of this shared ground — a normal referential montage. A large event on a small, Ca²⁺-rich leaf (Venus flytrap) is also volume-conducted to both nearby electrodes. "), b("Correlation does not mean there is no delay.")]));
kids.push(p([b("Recovering the delay robustly. "), t("A 2-tap model — far(t) = a·near(t) + b·near(t−τ) — loads the shared/instantaneous part onto a and the propagated part onto b at lag τ. Across species the delayed fraction is 0.68–0.90 and τ is sign-consistent (75–100%): a real, directional delay survives once the shared component is separated (151/165 resolve). This is why Venus flytrap’s fast CV is genuine — a small electrode spacing on the trap gives a small "), it("but real"), t(" delay plus strong volume-conduction correlation, not “no delay.”")]));
kids.push(...figure("crosstalk_raw_examples.png", "Both channels, full trace and pre-stimulus baseline zoom. Mimosa: baseline r = 0.96 (shared slow wave via the common ground). Cannabis: r = 0.20 (weakly coupled, clean delay). Venus: a sharp spike in both channels close together — a small real delay plus volume conduction."));
kids.push(...figure("self_aligned_channels.png", "Each physical channel self-aligned on its OWN peak, drawn with an arbitrary gap; thin = recordings, thick = mean ± SD. Removes delay-smearing of the far average and sidesteps the near/far label."));

// -------- 6. Near->far transformation
kids.push(pageBreak());
kids.push(h1("Near → far signal transformation"));
kids.push(p([t("As the potential travels from the near to the far electrode it "), b("attenuates"), t(" (far/near amplitude median ≈ 0.44), "), b("broadens"), t(" (FWHM ratio ≈ 1.31), yet largely "), b("preserves its shape"), t(" (waveform correlation ≈ 0.80). Within-species spread is large — it exceeds between-species differences.")]));
kids.push(...figure("near_to_far_transformation.png", "Pooled near→far transformation: amplitude ratio, width ratio, and waveform similarity across all valid recordings."));
kids.push(...figure("near_to_far_by_species.png", "Per-species transformation metrics (bar = median ± IQR, dots = recordings, tinted by family)."));
kids.push(...figure("aligned_overlays_by_species.png", "Aligned near (blue) and far (red) responses per species: thin = recordings, thick = mean ± shaded SD, normalised to and aligned on the near peak. Ordered active/shape-preserving → passive/dispersive."));

// -------- 7. Comparative
kids.push(pageBreak());
kids.push(h1("Does the transformation track evolutionary relationship?"));
kids.push(p([t("No. A Mantel test between functional distance (the three transformation metrics) and taxonomic distance gives r = −0.02, p = 0.50; Kruskal–Wallis by family is non-significant (p > 0.29). Congeners diverge as much as unrelated species — the two "), b("Capsicum"), t(" chiles are among the most different pairs, and the two mints differ in broadening and shape. The dominant axis is instead a convergent decremental↔regenerative continuum: attenuation co-varies with broadening, and broadening degrades waveform fidelity (ρ = −0.37, p < 10⁻⁶).")]));
kids.push(...figure("functional_dendrogram.png", "Species clustered by their near→far transformation profile; leaf colour = taxonomic family. Families are scattered, not clustered."));
kids.push(...figure("metrics_by_family.png", "Transformation metrics grouped by family (faint = recordings, bold = species medians)."));
kids.push(...figure("attenuation_vs_broadening.png", "Attenuation vs broadening: signals that lose amplitude also disperse (passive filtering); those that keep amplitude keep shape."));

// -------- 8. Active vs passive
kids.push(pageBreak());
kids.push(h1("Active vs passive propagation"));
kids.push(p([t("Plant electrical signals come in three kinds, of which only the action potential is a true self-regenerating (active) electrical wave:")]));
kids.push(table(
  ["Class", "Rule", "Velocity", "Mechanism / nature"],
  [
    ["Action potential (AP)", "all-or-none", "~5–200 mm/s", "active: self-regenerating Ca²⁺→Cl⁻→K⁺ currents"],
    ["Variation potential (VP)", "graded, decremental", "~1–10 mm/s", "passive: H⁺-ATPase inactivation behind a xylem hydraulic/chemical wave"],
    ["System potential (SP)", "graded, hyperpolarising", "~5–10 cm/min", "passive: H⁺-ATPase activation"],
  ],
  [1900, 1900, 1700, 3860]));
kids.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
kids.push(p([b("Recording-band caveat. "), t("The ~0.2 Hz high-pass AC-couples the signal, so the slow DC depolarisation that defines a VP is removed and a slow VP can appear as a spiky, differentiated waveform; the ~130 Hz low-pass, however, faithfully preserves the sub-second AP. Absolute VP amplitude/DC is therefore lost, but fast APs are captured well. Accordingly the discriminators below rely on the distance-scaling of the near→far transformation, not on raw shape alone.")]));
kids.push(p([b("Three independent metrics converge. "), t("(1) A passive-cable kernel fit — how much extra low-pass smoothing turns near into far — gives least dispersion for Sensitive Mimosa and Venus flytrap, most for Creeping Inchplant and the mints. (2) Peak−onset asymmetry (rigid translation vs dispersion) is ≈0 for Mimosa/Venus, large for the mints. (3) Delay scales as distance^0.99 — ballistic constant-velocity propagation, not diffusive (exponent 2). All three place Venus flytrap and Sensitive Mimosa at the active end and the mints at the passive end, across family lines.")]));
kids.push(...figure("active_passive_space.png", "Active↔passive space from near→far kernel fits: amplitude preservation (gain) vs extra dispersion (σ). Active corner top-left; passive bottom-right."));
kids.push(...figure("peak_onset_asymmetry.png", "Peak−onset delay asymmetry, an amplitude-independent discriminator: ≈0 = rigid translation (active), large positive = dispersion (passive)."));
kids.push(...figure("delay_vs_distance.png", "Delay vs distance: linear through ~origin (exponent 0.99) indicates constant-velocity propagation."));
kids.push(...figure("kernel_example_active.png", "Representative active example (Venus flytrap): the sharp near waveform is reproduced at the far electrode by a near-pure delay (small σ)."));
kids.push(...figure("kernel_example_passive.png", "Representative passive example (Creeping Inchplant): the sharp near transient is smeared into a broad, attenuated far bump (large σ)."));
kids.push(p([b("Why Venus flytrap sits below the “active” (gain = 1) line. "), t("Its far/near amplitude ratio is scattered 0.12–7.33 and is >1 in 31% of recordings — nothing like the tight, <1 decrement of the symmetric-electrode plants. Venus used an "), b("asymmetric montage"), t(" (a hook electrode around the trap “neck” plus a stake alongside the lobe), so the amplitude ratio reflects electrode coupling, not propagation decrement. On the axis that actually discriminates active from passive — waveform-shape preservation / dispersion — Venus is firmly active.")]));
kids.push(...figure("venus_electrode_asymmetry.png", "Amplitude ratio (far/near, log scale) per species. Venus is scattered and often >1 (asymmetric hook/stake electrodes), unlike the consistent <1 decrement of symmetric-electrode plants."));

// -------- 9. Simulation
kids.push(pageBreak());
kids.push(h1("Simulating propagation"));
kids.push(p([b("Passive cable (null model). "), t("τ ∂V/∂t = λ² ∂²V/∂x² − V, with space constant λ = √(r_m/r_i). The infinite-cable Green’s function G(x,t) = e^(−t/τ)/√(4πDt)·e^(−x²/4Dt) makes a distal signal a delayed, exponentially decayed (×e^(−x/λ)) and low-pass-dispersed copy of the proximal one — exactly the kernel fitted in Section 8.")]));
kids.push(p([b("Active excitable cable. "), t("A FitzHugh–Nagumo reaction-diffusion cable launches a travelling pulse of constant amplitude and velocity (v ∝ √D). Passive spread decays and broadens with distance; the active wave holds its amplitude and shape — the amplitude-vs-distance panel is the single cleanest signature.")]));
kids.push(...figure("cable_vs_fhn_sim.png", "Simulation: passive cable (decays and broadens with distance) vs FitzHugh–Nagumo active wave (constant amplitude and velocity)."));
kids.push(p([b("Do the simulations predict the real traces? "), t("For every recording we predict the far channel from the near channel two ways — an active model (delayed copy + shared component) and a passive cable. The "), b("active model out-predicts the passive cable for almost every species"), t(" (median R² 0.4–0.87 vs 0.2–0.79), and the fitted delays are sign-consistent. The far trace really is a "), it("delayed"), t(" copy of the near trace, not a dispersed one.")]));
kids.push(...figure("sim_vs_real_examples.png", "Simulated far trace predicting the real far trace. Active model (blue dashed) tracks the real far (red) — Venus’s sharp spike and the slow species’ 3–4.5 s delays — beating the passive cable (green dotted)."));
kids.push(...figure("sim_prediction_r2.png", "Median prediction R² of each simulation (far from near), per species: active/delay beats passive cable almost everywhere."));
kids.push(p([b("A biophysical Venus-flytrap AP model. "), t("A Hodgkin-Huxley-type plant AP (cvplants.simulate.plant_ap_hh) uses the established plant ionic mechanism — a stimulus admits Ca²⁺; Ca²⁺ gates a depolarising anion (Cl⁻) efflux; the depolarisation opens voltage-gated Ca²⁺ (positive feedback → an all-or-none regenerative spike); voltage-gated K⁺ and Ca²⁺ removal repolarise. Plants use Cl⁻/K⁺, "), b("not"), t(" Na⁺, and the AP lasts ~1–2 s. Passed through the recording band-pass, the model AP reproduces the biphasic waveform we record from Venus flytrap (right panel), and it fires all-or-none (middle panel). Parameters are illustrative (Hedrich & Neher 2018 / Sukhov-Vodeneev framework), not fitted conductances — surface, band-passed recordings cannot constrain those.")]));
kids.push(...figure("venus_ap_model.png", "HH-type plant AP model (Ca²⁺→Cl⁻→K⁺). Left: membrane potential and Ca²⁺. Middle: all-or-none (a fixed-size spike only above threshold). Right: the model AP, band-passed like the recordings, matches a real Venus AP."));

// -------- 10. Ion channels
kids.push(pageBreak());
kids.push(h1("Ion channels and molecular basis"));
kids.push(p([t("Plant excitation is Ca²⁺/Cl⁻/K⁺-based, "), b("not"), t(" Na⁺-based as in animal axons (Fromm & Lautner 2007; Sukhov & Vodeneev 2009).")]));
kids.push(bullet("Depolarisation — Ca²⁺ influx via GLUTAMATE-RECEPTOR-LIKE channels (clade-3 GLR3.3 / GLR3.6), the genetic basis of systemic wound signalling (Mousavi et al. 2013; Toyota et al. 2018; Nguyen et al. 2018)."));
kids.push(bullet("Sustained depolarisation — anion (Cl⁻/NO₃⁻/malate) efflux via S-type SLAC1/SLAH3 and R-type QUAC1/ALMT12 (established in guard cells, extrapolated to the propagating spike)."));
kids.push(bullet("Repolarisation — K⁺ efflux via the outward rectifier GORK, which shapes AP amplitude and duration (Salvador-Recatalà 2018)."));
kids.push(bullet("Resting potential & active repolarisation — the P-type plasma-membrane H⁺-ATPase (AHA family)."));
kids.push(bullet("Variation potential — transient H⁺-ATPase inactivation behind a xylem hydraulic/chemical “Ricca factor” wave (Vodeneev/Sukhov; Evans et al. 2017). The initiating mechanosensor (OSCA1, MSL10, MCA1/2, PIEZO) is the field’s clearest open question."));
kids.push(bullet("Venus flytrap — trigger-hair micronewton mechanosensing → all-or-none Ca²⁺ AP; candidate sensor FLYC1/MSL10; AP “counting” gates jasmonate signalling (Böhm et al. 2016; Hedrich & Neher 2018)."));
kids.push(bullet("Mimosa pudica — touch → Ca²⁺ → Cl⁻ efflux → K⁺ + water efflux collapses pulvinar turgor (Allen 1969); channel genes inferred by homology."));

// -------- 11. New experiments
kids.push(h1("What this dataset cannot decide — and the minimal new experiment"));
kids.push(table(
  ["Open question", "Minimal new experiment"],
  [
    ["True all-or-none threshold", "Stimulus-intensity ladder at one site: step response (active) vs graded (passive)"],
    ["Refractory period", "Paired-pulse Δt = 0.5–20 min: is the second response abolished/reduced?"],
    ["Regenerative ion mechanism", "Pharmacology (La³⁺/Gd³⁺, A-9-C/DIDS, TEA) on the segment between wound and electrodes"],
    ["Channel-gated vs physical conduction", "Q10 series (15/25/35 °C): active ≈ 2–3, passive ≈ 1"],
    ["Hydraulic vs electrical primacy", "Co-record xylem pressure / stem strain with the electrodes"],
    ["Bidirectionality", "Electrodes proximal AND distal to a non-wounding stimulus site"],
  ],
  [3200, 6160]));

// -------- 12. References
kids.push(pageBreak());
kids.push(h1("Key references"));
const refs = [
  "Contreras C, Morales M, Rojas P, Serbe-Kamp E, Marzullo T. Electrical Conduction Velocity Across Species of Rapid Movement and Non-Rapid Movement Plants. Plant Signaling & Behavior (the manual analysis compared here).",
  "Madariaga D, et al. (2024). A library of electrophysiological responses in plants. Plant Signal Behav 19(1):2310977.",
  "Fromm J, Lautner S (2007). Electrical signals and their physiological significance in plants. Plant, Cell & Environment 30:249–257.",
  "Mousavi SAR, Chauvin A, Pascaud F, Kellenberger S, Farmer EE (2013). GLUTAMATE RECEPTOR-LIKE genes mediate leaf-to-leaf wound signalling. Nature 500:422–426.",
  "Toyota M, et al. (2018). Glutamate triggers long-distance, calcium-based plant defense signaling. Science 361:1112–1115.",
  "Nguyen CT, Kurenda A, Stolz S, Chételat A, Farmer EE (2018). Identification of cell populations necessary for leaf-to-leaf electrical signaling. PNAS 115:10178–10183.",
  "Salvador-Recatalà V (2018). The AKT2/GORK potassium channels shape the plant action potential. Int. J. Mol. Sci. 19:926.",
  "Böhm J, et al. (2016). The Venus flytrap counts prey-induced action potentials to induce sodium uptake. Current Biology 26:286–295.",
  "Hedrich R, Neher E (2018). Venus flytrap: how an excitable, carnivorous plant works. Trends in Plant Science 23:220–234.",
  "Allen RD (1969). Mechanism of the seismonastic reaction in Mimosa pudica. Plant Physiology 44:1101–1107.",
  "Vodeneev V, Akinchits E, Sukhov V (2015). Variation potential in higher plants. Plant Signaling & Behavior 10:e1057365.",
  "Evans MJ, Choi W-G, Gilroy S, Morris RJ (2017). A chemical agent transported by xylem mass flow propagates variation potentials. The Plant Journal 91:1029–1037.",
  "Sukhov V, Vodeneev V (2009). A mathematical model of action potential in cells of vascular plants. J. Membrane Biology 232:59–67.",
  "Sukhov V, Nerush V, Orlova L, Vodeneev V (2011). Simulation of action potential propagation in plants. J. Theoretical Biology 291:47–55.",
  "FitzHugh R (1961). Impulses and physiological states in theoretical models of nerve membrane. Biophysical Journal 1:445–466.",
];
refs.forEach((r) => kids.push(new Paragraph({ numbering: { reference: "refs", level: 0 }, spacing: { after: 80 },
  children: [new TextRun({ text: r, size: 19 })] })));

// -------- doc
const doc = new Document({
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 460, hanging: 260 } } } }] },
    { reference: "refs", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.START, style: { paragraph: { indent: { left: 460, hanging: 260 } } } }] },
  ] },
  styles: { default: { document: { run: { font: "Calibri", size: 22 } } } },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 } } },
    children: kids,
  }],
});
Packer.toBuffer(doc).then((buf) => {
  const out = path.join(ROOT, "results", "Plant_conduction_velocity_report.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote", out, "-", FIGN, "figures,", SECN, "sections");
});
