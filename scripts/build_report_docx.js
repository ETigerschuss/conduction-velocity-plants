// Build the Word report for the conduction-velocity-plants project.
// Usage: node scripts/build_report_docx.js
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
const MAXW = 600, MAXH = 720;               // px display caps
const ACCENT = "1f3f66";

function fit(file) {
  const [w, h] = DIMS[file];
  const s = Math.min(MAXW / w, MAXH / h, 1);
  return { width: Math.round(w * s), height: Math.round(h * s) };
}
let FIGN = 0, SECN = 0;
function figure(file, caption) {
  const t = fit(file);
  FIGN += 1;
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 160, after: 40 },
      children: [new ImageRun({ data: fs.readFileSync(path.join(FIG, file)), type: "png", transformation: t })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [new TextRun({ text: `Figure ${FIGN}. ${caption.replace(/^Figure\s+\d+[a-z]?\.\s*/i, "")}`, italics: true, size: 17, color: "555555" })],
    }),
  ];
}
function h1(t) { SECN += 1; return new Paragraph({ text: `${SECN}. ${t.replace(/^\d+\.\s*/, "")}`, heading: HeadingLevel.HEADING_1, spacing: { before: 260, after: 120 } }); }
function h2(t) { return new Paragraph({ text: t, heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 100 } }); }
function p(runs) {
  const children = Array.isArray(runs) ? runs : [new TextRun({ text: runs, size: 22 })];
  return new Paragraph({ children, spacing: { after: 120 }, alignment: AlignmentType.JUSTIFIED });
}
function b(text) { return new TextRun({ text, bold: true, size: 22 }); }
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
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [mk(headers, true), ...rows.map((r) => mk(r, false))],
  });
}
const rule = () => new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "BBBBBB" } }, spacing: { after: 120 } });

// ---------------------------------------------------------------- content
const kids = [];

// title
kids.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 400, after: 60 },
  children: [new TextRun({ text: "Conduction Velocity and Signal Propagation in Plants", bold: true, size: 40, color: ACCENT })] }));
kids.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 },
  children: [new TextRun({ text: "A two-channel electrophysiology deep dive across 13 species", size: 24, color: "555555" })] }));
kids.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
  children: [new TextRun({ text: "BackyardBrains Plant SpikerBox · 176 recordings (165 analysed) · github.com/ETigerschuss/conduction-velocity-plants", size: 18, color: "888888" })] }));
kids.push(rule());

// 1. Introduction
kids.push(h1("1. Overview and dataset"));
kids.push(p([t("Two recording electrodes are placed inline downstream of a wound/flame stimulus on the plant; the propagating electrical potential (a wound / variation potential, or an action potential) reaches the "), b("near"), t(" electrode first and the "), b("far"), t(" electrode later. Recordings are two-channel WAV at 5 kHz; two event markers bracket the stimulation window. Inter-electrode distances were cross-referenced from the “Todo Data Resumen” spreadsheet (166/176 recordings). This report characterises the conduction velocity, how the signal is transformed from the near to the far electrode, whether those properties track evolutionary relationship, and whether propagation is active (regenerative) or passive (decremental).")]));
kids.push(p([b("Three questions, three answers. "), t("(i) Conduction velocity spans ~2–25 mm/s across species, with Venus flytrap fastest. (ii) The near→far signal attenuates (×0.44) and broadens (×1.31) while keeping its shape (r≈0.80). (iii) These properties do "), b("not"), t(" track taxonomy, but they do separate species along an active↔passive continuum — Venus flytrap and Sensitive Mimosa behave as active, shape-preserving conductors, the mints as passive/decremental ones.")]));

// 2. Methods
kids.push(h1("2. Methods (brief)"));
kids.push(p([t("Each channel is baseline-subtracted (pre-stimulus window) and low-pass filtered (<2 Hz; the potentials are slow, so mains hum needs no separate notch). The dominant post-stimulus deflection is detected in each channel; the earlier-peaking channel is labelled "), b("near"), t(". Inter-channel delay is measured two independent ways — windowed cross-correlation (primary) and peak-to-peak (cross-check). Conduction velocity = inter-electrode distance / delay. Signal-transformation metrics: amplitude attenuation (far/near peak), temporal broadening (far/near FWHM), and waveform similarity (max normalised cross-correlation). Recordings are quality-gated (near-synchronous peaks, low waveform similarity, or low SNR → excluded); 165/176 pass.")]));

// 3. Conduction velocity
kids.push(h1("3. Conduction velocity"));
kids.push(p([t("Median CV per species ranges from ~2 to ~12 mm/s (resolved-delay recordings; see Section 4), within the 1–40 mm/s range of earlier hand measurements. The velocity estimate is validated three ways: our automatic delay agrees with the experimenters’ manual delay (Spearman ρ = 0.80), delay scales with distance (ρ = 0.36, p = 3×10⁻⁶), and CV is independent of the electrode spacing used (ρ ≈ 0), as a true velocity must be.")]));
kids.push(...figure("cv_by_species.png", "Figure 1. Conduction velocity by species, restricted to recordings with a resolved (non-common-mode-dominated) delay — see Section 4. Box = IQR, red = median, dots = recordings."));
kids.push(...figure("delay_validation.png", "Figure 2. Validation: our measured inter-channel delay vs the experimenters’ manual delay (Tiempo). Points fall on the identity line for both exact and order-inferred spreadsheet matches."));
kids.push(...figure("cannabis_distance_delay.png", "Figure 3. Cannabis: electrode distance vs propagation delay; slope is an aggregate conduction velocity."));

// 4. Channel integrity
kids.push(new Paragraph({ children: [new PageBreak()] }));
kids.push(h1("4. Channel integrity: the shared reference and how the delay is recovered"));
kids.push(p([t("Near/far is assigned per recording as the earlier-peaking channel (ch0 leads in ~76%); the delay magnitude, hence CV, does not depend on that label. The two channels are "), b("correlated, and that is expected"), t(": both electrodes share a soil/earth reference, so any whole-plant potential or reference fluctuation appears in both. The pre-stimulus baseline correlation is high (pooled r ≈ 0.66) precisely because of this shared ground — a normal referential montage, not amplifier crosstalk. A large event on a small, Ca²⁺-rich leaf (Venus flytrap) is also volume-conducted to both nearby electrodes. "), b("Correlation does not mean there is no delay.")]));
kids.push(p([b("Recovering the delay. "), t("A common-mode-robust model — far(t) = a·near(t) + b·near(t−τ) — loads the shared/instantaneous part onto a and the propagated part onto b at lag τ. Across species the delayed fraction is 0.68–0.90 and τ is sign-consistent (75–100%): a real, directional delay survives once the shared component is separated. 151/165 recordings resolve. "), b("Venus flytrap's fast CV is real"), t(" — its 2-tap delay (~0.3 s, 14/16 resolved) gives CV ≈ 28–30 mm/s, consistent with the known fast Dionaea action potential. A small electrode spacing on the trap gives a small but genuine delay plus strong volume-conduction correlation. (An earlier draft over-flagged the fast species with a hard time-floor and wrongly called this an artifact; corrected here.)")]));
kids.push(...figure("crosstalk_raw_examples.png", "Figure 4. Both channels, full trace and pre-stimulus baseline zoom. Mimosa: baseline r = 0.96 (shared slow wave via the common ground). Cannabis: r = 0.20 (weakly coupled, clean delay). Venus: a sharp spike appears in both channels close together — a small real delay plus volume conduction."));
kids.push(...figure("self_aligned_channels.png", "Figure 5. Each physical channel self-aligned on its OWN peak, drawn with an arbitrary gap; thin = recordings, thick = mean ± SD. Self-alignment removes the delay-smearing of the far average and sidesteps the near/far label. baseline r annotates the shared-reference coupling."));
kids.push(...figure("sim_vs_real_examples.png", "Figure 6. Simulated far trace predicting the real far trace. The active model (delayed copy + shared component, blue dashed) tracks the real far (red) — capturing Venus's sharp biphasic spike and the slow species' 3–4.5 s delays — and out-predicts the passive cable (green dotted)."));
kids.push(...figure("sim_prediction_r2.png", "Figure 7. Median prediction R² of each simulation (far from near), per species. The active/delay model beats the passive cable almost everywhere: the far trace is a delayed copy of the near trace, not a dispersed one."));
kids.push(...figure("cv_2tap_by_species.png", "Figure 8. Conduction velocity re-derived from the common-mode-robust 2-tap delay. Venus flytrap is fastest (~30 mm/s), as expected biologically; the fast species are retained rather than discarded."));

// 4. Near-far transformation
kids.push(new Paragraph({ children: [new PageBreak()] }));
kids.push(h1("4. Near → far signal transformation"));
kids.push(p([t("As the potential travels from the near to the far electrode it "), b("attenuates"), t(" (far/near amplitude median ≈ 0.44), "), b("broadens"), t(" (FWHM ratio ≈ 1.31), yet largely "), b("preserves its shape"), t(" (waveform correlation ≈ 0.80). The individual-recording spread is large — within-species variability exceeds between-species differences.")]));
kids.push(...figure("near_to_far_transformation.png", "Figure 4. Pooled near→far transformation: amplitude ratio, width ratio, and waveform similarity across all valid recordings."));
kids.push(...figure("near_to_far_by_species.png", "Figure 5. Per-species transformation metrics (bar = median ± IQR, dots = recordings, tinted by family)."));
kids.push(...figure("aligned_overlays_by_species.png", "Figure 6. Aligned near (blue) and far (red) responses per species: thin = individual recordings, thick = mean ± shaded SD, normalised to the near peak and aligned on it. Ordered active/shape-preserving → passive/dispersive."));

// 5. Comparative
kids.push(new Paragraph({ children: [new PageBreak()] }));
kids.push(h1("5. Does the transformation track evolutionary relationship?"));
kids.push(p([t("No. A Mantel test between functional distance (the three transformation metrics) and taxonomic distance gives r = −0.02, p = 0.50; Kruskal–Wallis by family is non-significant (p > 0.29). Congeners diverge as much as unrelated species — the two "), b("Capsicum"), t(" chiles are among the most different pairs, and the two "), b("Mentha"), t(" mints differ in broadening and shape. The dominant axis is instead a convergent decremental↔regenerative continuum: attenuation co-varies with broadening, and broadening degrades waveform fidelity (ρ = −0.37, p < 10⁻⁶).")]));
kids.push(...figure("functional_dendrogram.png", "Figure 7. Species clustered by their near→far transformation profile; leaf colour = taxonomic family. Families are scattered, not clustered."));
kids.push(...figure("metrics_by_family.png", "Figure 8. Transformation metrics grouped by family (faint = recordings, bold = species medians)."));
kids.push(...figure("attenuation_vs_broadening.png", "Figure 9. Attenuation vs broadening: signals that lose amplitude also disperse (passive filtering); those that keep amplitude keep shape."));

// 6. Active vs passive
kids.push(new Paragraph({ children: [new PageBreak()] }));
kids.push(h1("6. Active vs passive propagation"));
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
kids.push(p([b("Hardware caveat. "), t("The Plant SpikerBox front end is a 0.07–8.8 Hz band-pass. The 0.07 Hz high-pass removes the slow DC depolarisation that defines a VP (so a passive VP can look like a spiky AP), and the 8.8 Hz low-pass smears events toward similar shapes. Shape alone is therefore unsafe; the discriminators below rely on distance-scaling of the near→far transformation.")]));
kids.push(p([b("Three independent metrics converge. "), t("(1) A passive-cable kernel fit — how much extra low-pass smoothing turns near into far — gives least dispersion for Sensitive Mimosa and Venus flytrap, most for Creeping Inchplant and the mints. (2) Peak−onset asymmetry (rigid translation vs dispersion) is ≈0 for Mimosa/Venus and large for the mints. (3) Delay scales as distance^0.99 — ballistic constant-velocity propagation, not diffusive (which would give exponent 2). All three place Venus flytrap and Sensitive Mimosa at the active/regenerative end and the mints at the passive/decremental end, across family lines.")]));
kids.push(...figure("active_passive_space.png", "Figure 10. Active↔passive space from near→far kernel fits: amplitude preservation (gain) vs extra dispersion (σ). Active corner top-left; passive bottom-right."));
kids.push(...figure("peak_onset_asymmetry.png", "Figure 11. Peak−onset delay asymmetry, an amplitude-independent discriminator: ≈0 = rigid translation (active), large positive = dispersion (passive)."));
kids.push(...figure("delay_vs_distance.png", "Figure 12. Delay vs distance: linear through ~origin (exponent 0.99) indicates constant-velocity propagation."));
kids.push(...figure("kernel_example_active.png", "Figure 13a. Representative active example (Venus flytrap): the sharp near waveform is reproduced at the far electrode by a near-pure delay (small σ)."));
kids.push(...figure("kernel_example_passive.png", "Figure 13b. Representative passive example (Creeping Inchplant): the sharp near transient is smeared into a broad, attenuated far bump (large σ)."));

// 7. Ion channels
kids.push(new Paragraph({ children: [new PageBreak()] }));
kids.push(h1("7. Ion channels and molecular basis"));
kids.push(p([t("Plant excitation is Ca²⁺/Cl⁻/K⁺-based, "), b("not"), t(" Na⁺-based as in animal axons (Fromm & Lautner 2007; Sukhov & Vodeneev 2009).")]));
kids.push(bullet("Depolarisation — Ca²⁺ influx via GLUTAMATE-RECEPTOR-LIKE channels (clade-3 GLR3.3 / GLR3.6), the genetic basis of systemic wound signalling (Mousavi et al. 2013, Nature; Toyota et al. 2018, Science; Nguyen et al. 2018, PNAS)."));
kids.push(bullet("Sustained depolarisation — anion (Cl⁻/NO₃⁻/malate) efflux via S-type SLAC1/SLAH3 and R-type QUAC1/ALMT12 (established in guard cells, extrapolated to the propagating spike)."));
kids.push(bullet("Repolarisation — K⁺ efflux via the outward rectifier GORK, which shapes AP amplitude and duration (Salvador-Recatalà 2018)."));
kids.push(bullet("Resting potential & active repolarisation — the P-type plasma-membrane H⁺-ATPase (AHA family)."));
kids.push(bullet("Variation potential — driven by transient H⁺-ATPase inactivation behind a xylem hydraulic/chemical “Ricca factor” wave carried by mass flow (Vodeneev/Sukhov; Evans et al. 2017, Plant J). The initiating mechanosensor (OSCA1, MSL10, MCA1/2, PIEZO candidates) is the field’s clearest open question."));
kids.push(bullet("Venus flytrap — trigger-hair micronewton mechanosensing → all-or-none Ca²⁺ AP; candidate sensor FLYC1/MSL10, K⁺ channel KDM1; AP “counting” gates jasmonate signalling and DmHKT1 Na⁺ uptake (Böhm et al. 2016; Hedrich & Neher 2018; Jaślan/Hedrich 2022)."));
kids.push(bullet("Mimosa pudica — touch → Ca²⁺ → Cl⁻ efflux → K⁺ + water efflux collapses pulvinar turgor (Allen 1969); channel genes inferred by homology, not cloned."));

// 8. Simulation
kids.push(h1("8. Simulating propagation"));
kids.push(p([b("Passive cable (null model). "), t("τ ∂V/∂t = λ² ∂²V/∂x² − V, with space constant λ = √(r_m/r_i) and time constant τ = r_m c_m. The infinite-cable Green’s function G(x,t) = e^(−t/τ)/√(4πDt)·e^(−x²/4Dt) makes a distal signal a delayed, exponentially decayed (×e^(−x/λ)) and low-pass-dispersed copy of the proximal one — which is exactly the kernel fitted in Section 6.")]));
kids.push(p([b("Active excitable cable. "), t("A FitzHugh–Nagumo reaction-diffusion cable (u_t = D u_xx + u − u³/3 − w + I; w_t = ε(u − a − b w)) launches a travelling pulse of constant amplitude and constant velocity (v ∝ √D). For a plant-specific active model, the Hodgkin–Huxley-type Ca²⁺/Cl⁻/K⁺ membrane model of Sukhov & Vodeneev (2009) and its cable extension (Sukhov et al. 2011, J Theor Biol) reproduce a cm/s AP.")]));
kids.push(...figure("cable_vs_fhn_sim.png", "Figure 14. Simulation: passive cable (decays and broadens with distance) vs FitzHugh–Nagumo active wave (constant amplitude and velocity). Right panel: amplitude-vs-distance is the single cleanest signature."));

// 9. New experiments
kids.push(h1("9. What this dataset cannot decide — and the minimal new experiment"));
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

// Comparison with the manual analysis
kids.push(new Paragraph({ children: [new PageBreak()] }));
kids.push(h1("Comparison with the manual analysis (Contreras et al.)"));
kids.push(p([t("Validated against the paper "), new TextRun({ text: "Electrical Conduction Velocity Across Species of Rapid Movement and Non-Rapid Movement Plants", italics: true, size: 22 }), t(" (Contreras, Morales, Rojas, Serbe-Kamp, Marzullo; Plant Signaling & Behavior), Table 1. Their accepted-recording counts match this repo's WAV files species-by-species (176 total), so we analyse the same recordings; they report a per-species CV mean, so we compare mean-to-mean on the resolved-delay subset.")]));
kids.push(p([b("Strong agreement: Pearson r = 0.94 across 13 species (0.98 excluding Sensitive Mimosa). "), t("The non-rapid group mean matches almost exactly (mine 8.0 ± 6.3 vs paper 7.7 ± 6.5 mm/s), and Venus flytrap agrees (~30 vs 35.3). Almost every species sits on the identity line within error.")]));
kids.push(...figure("compare_to_paper_scatter.png", "This pipeline's CV vs the paper's manual CV, per species (mean ± SD). Points on the dashed identity line agree; only Sensitive Mimosa sits clearly below."));
kids.push(...figure("compare_to_paper_bars.png", "Per-species CV, manual analysis vs automatic pipeline (mean ± SD)."));
kids.push(p([b("The one discrepancy — Sensitive Mimosa (paper 32.4, mine 18.9) — is a detector limitation, not a real disagreement. "), t("Comparing my delay to their manual delay recording-by-recording, they match on the slow Mimosa recordings; on ~5 fast recordings (their delay ~0.2–0.4 s) my cross-correlation detector locks onto a slower secondary feature (one case: my 12.3 s vs their 0.37 s), pulling my mean down. Mimosa fires a sharp fast AP with a small inter-electrode delay; a fast-onset-aware delay estimate would bring it in line. Corrected metadata from the paper: Hierbabuena = Clinopodium douglasii (not Mentha), Chilean Chile = Capsicum baccatum; amplifier 0.2–130 Hz / ~55× / 10 kHz (not a 0.07–8.8 Hz SpikerBox).")]));

// 10. References
kids.push(new Paragraph({ children: [new PageBreak()] }));
kids.push(h1("10. Key references"));
const refs = [
  "Contreras C, Morales M, Rojas P, Serbe-Kamp E, Marzullo T. Electrical Conduction Velocity Across Species of Rapid Movement and Non-Rapid Movement Plants. Plant Signaling & Behavior (the manual analysis compared here).",
  "Madariaga D, et al. (2024). A library of electrophysiological responses in plants — a model of transversal education and open science. Plant Signal Behav 19(1):2310977.",
  "Fromm J, Lautner S (2007). Electrical signals and their physiological significance in plants. Plant, Cell & Environment 30:249–257.",
  "Mousavi SAR, Chauvin A, Pascaud F, Kellenberger S, Farmer EE (2013). GLUTAMATE RECEPTOR-LIKE genes mediate leaf-to-leaf wound signalling. Nature 500:422–426.",
  "Toyota M, Spencer D, Sawai-Toyota S, et al. (2018). Glutamate triggers long-distance, calcium-based plant defense signaling. Science 361:1112–1115.",
  "Nguyen CT, Kurenda A, Stolz S, Chételat A, Farmer EE (2018). Identification of cell populations necessary for leaf-to-leaf electrical signaling. PNAS 115:10178–10183.",
  "Salvador-Recatalà V (2018). The AKT2/GORK potassium channels shape the plant action potential. Int. J. Mol. Sci. 19:926.",
  "Böhm J, Scherzer S, Krol E, et al. (2016). The Venus flytrap counts prey-induced action potentials to induce sodium uptake. Current Biology 26:286–295.",
  "Hedrich R, Neher E (2018). Venus flytrap: how an excitable, carnivorous plant works. Trends in Plant Science 23:220–234.",
  "Allen RD (1969). Mechanism of the seismonastic reaction in Mimosa pudica. Plant Physiology 44:1101–1107.",
  "Vodeneev V, Akinchits E, Sukhov V (2015). Variation potential in higher plants: mechanisms of generation and propagation. Plant Signaling & Behavior 10:e1057365.",
  "Evans MJ, Choi W-G, Gilroy S, Morris RJ (2017). A chemical agent transported by xylem mass flow propagates variation potentials. The Plant Journal 91:1029–1037.",
  "Sukhov V, Vodeneev V (2009). A mathematical model of action potential in cells of vascular plants. J. Membrane Biology 232:59–67.",
  "Sukhov V, Nerush V, Orlova L, Vodeneev V (2011). Simulation of action potential propagation in plants. J. Theoretical Biology 291:47–55.",
  "FitzHugh R (1961). Impulses and physiological states in theoretical models of nerve membrane. Biophysical Journal 1:445–466.",
  "BackyardBrains (2024). A library of electrophysiological responses in plants. Plant Signaling & Behavior (PMID 38493508); Plant SpikerBox documentation (0.07–8.8 Hz band-pass).",
];
refs.forEach((r) => kids.push(new Paragraph({ numbering: { reference: "refs", level: 0 }, spacing: { after: 80 },
  children: [new TextRun({ text: r, size: 19 })] })));

// ---------------------------------------------------------------- doc
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
  console.log("wrote", out);
});
