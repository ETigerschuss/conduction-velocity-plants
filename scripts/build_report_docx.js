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
kids.push(h1("Overview and what to take from this report"));
kids.push(p([t("Two recording electrodes sit inline downstream of a wound / touch / flame stimulus; the propagating potential reaches the "), b("near"), t(" electrode first and the "), b("far"), t(" electrode later. We built an automatic analysis pipeline and asked four questions.")]));
kids.push(p([b("1. Does the automatic pipeline reproduce the manual conduction-velocity result? "), t("Yes — Pearson r = 0.94 across 13 species (0.98 excluding one species), and the manual per-recording numbers are recoverable exactly (Section 4).")]));
kids.push(p([b("2. How does the signal change from the near to the far electrode? "), t("It "), b("attenuates"), t(" (far ≈ 0.4× the near amplitude) and mildly "), b("broadens"), t(", while largely keeping its shape (Section 6).")]));
kids.push(p([b("3. Do these properties track evolutionary relationship? "), t("No — congeners differ as much as unrelated species (Section 7).")]));
kids.push(p([b("4. Is propagation active or passive? "), t("This cannot be settled cleanly with two surface electrodes, but the fast, rapid-movement species (Venus flytrap, Sensitive Mimosa) preserve waveform shape best and the slow species disperse most (Section 8). A biophysical AP model reproduces the recorded Venus waveform (Section 9).")]));
kids.push(p([it("A note on figures. This is a working report; not every figure belongs in the manuscript. Section 12 lists which figures we consider manuscript candidates versus supporting / diagnostic material.")]));

// -------- 2. Methods
kids.push(h1("Methods"));
kids.push(p([t("Each channel is baseline-subtracted and low-pass filtered for detection; the earlier-peaking channel is labelled "), b("near"), t(". Inter-channel delay is measured by windowed cross-correlation (primary), with a peak-to-peak cross-check and — because the two electrodes share a soil/earth reference — a common-mode-robust 2-tap model (Section 5). CV = inter-electrode distance / delay; distances are cross-referenced from the “Todo Data Resumen” spreadsheet (166/176 recordings). Transformation metrics: amplitude attenuation (far/near peak), temporal broadening (far/near FWHM), waveform similarity (max normalised cross-correlation). Recordings are quality-gated; 165/176 pass. The pipeline reports three CV columns per recording — "), it("cv_xcorr"), t(" (default), "), it("cv_2tap"), t(" (common-mode-robust), and "), it("cv_manual"), t(" (distance ÷ the experimenters’ manual delay).")]));

// -------- 3. Conduction velocity
kids.push(h1("Conduction velocity"));
kids.push(p([t("Median CV ranges from ~2 mm/s (Argentian Dollar) to ~28 mm/s (Venus flytrap). The estimate is internally consistent: the delay scales with electrode distance (ρ = 0.36, p = 3×10⁻⁶) and CV is independent of the spacing used (ρ ≈ 0), as a true velocity must be.")]));
kids.push(...figure("cv_by_species.png", "Conduction velocity by species (resolved-delay recordings). Box = IQR, red = median, dots = recordings."));

// -------- 4. Validation
kids.push(pageBreak());
kids.push(h1("Validation against the manual analysis (Contreras et al.)"));
kids.push(p([t("Validated against "), it("Electrical Conduction Velocity Across Species of Rapid Movement and Non-Rapid Movement Plants"), t(" (Contreras, Morales, Rojas, Serbe-Kamp, Marzullo; Plant Signaling & Behavior), Table 1. Both analyses use the same recordings.")]));
kids.push(p([b("Strong agreement: Pearson r = 0.94 across 13 species (0.98 excluding Sensitive Mimosa). "), t("The non-rapid group mean matches almost exactly (automatic 8.0 ± 6.3 vs manual 7.7 ± 6.5 mm/s), and Venus flytrap agrees (~30 vs 35.3). Using the experimenters’ own delays, the "), it("cv_manual"), t(" column reproduces the manuscript exactly (Mimosa 30.6, Venus 35.7 mm/s).")]));
kids.push(...figure("compare_to_paper_scatter.png", "Automatic CV vs the manual CV, per species (mean ± SD). Points on the dashed identity line agree; only Sensitive Mimosa sits clearly below."));
kids.push(...figure("delay_validation.png", "The underlying agreement: our measured inter-channel delay vs the experimenters’ manual delay (Tiempo), recording by recording, on the identity line."));
kids.push(p([b("The one discrepancy — Sensitive Mimosa (manual 32.4, automatic 18.9) — is understood, not a real disagreement. "), t("The delays match on the slow Mimosa recordings; the gap is a few fast recordings that carry a "), b("sharp fast AP plus larger, slower bumps"), t(". The manual analyst tracked the fast AP (high CV); the automatic cross-correlation tracks the larger slow bump. We implemented and tested a fast-onset estimator (and three variants) against the manual delays — all were "), b("less"), t(" accurate (median error 0.20 s for the default vs 1.80 s for fast-onset), so we kept the default. Mimosa’s manual SD (21.6) nearly equals its mean, so the exact value is intrinsically uncertain; both analyses agree Mimosa and Venus are the fast, rapid-movement outliers. To match the manuscript number exactly, use "), it("cv_manual"), t(".")]));
kids.push(...figure("delay_estimator_bakeoff.png", "Delay-estimator bakeoff against the manual per-recording delays (lower = better). The default cross-correlation wins for every species; the fast-onset variants were rejected on this evidence."));
kids.push(p([b("Metadata corrected from the paper: "), t("Hierbabuena = Clinopodium douglasii (not Mentha); Chilean Chile = Capsicum baccatum; Argentian Dollar = Plectranthus purpuratus. Amplifier passband ~0.2–130 Hz (a custom rig), not the 0.07–8.8 Hz stock SpikerBox.")]));

// -------- 5. Channel integrity
kids.push(pageBreak());
kids.push(h1("Channel integrity: the shared reference and how the delay is recovered"));
kids.push(p([t("The two channels are "), b("correlated, and that is expected"), t(": both electrodes share a soil/earth reference, so any whole-plant potential or reference fluctuation appears in both (baseline correlation pooled r ≈ 0.66). This is a normal referential montage, not amplifier crosstalk — and it does "), b("not"), t(" prevent measuring the delay. A common-mode-robust 2-tap model, far(t) = a·near(t) + b·near(t−τ), separates the shared/instantaneous part (a) from the propagated part (b) at lag τ; across species the delayed fraction is 0.68–0.90 and τ is sign-consistent (75–100%). This is why Venus flytrap’s fast CV is genuine — a small electrode spacing gives a small "), it("but real"), t(" delay plus strong volume-conduction correlation.")]));
kids.push(...figure("crosstalk_raw_examples.png", "Both channels, full trace and pre-stimulus baseline zoom. Mimosa: baseline r = 0.96 (shared slow wave via the common ground). Cannabis: r = 0.20 (weakly coupled, clean delay). Venus: a sharp spike in both channels close together — a small real delay plus volume conduction."));

// -------- 6. Near->far transformation
kids.push(pageBreak());
kids.push(h1("How the signal changes from near to far"));
kids.push(p([t("From the near to the far electrode the potential "), b("attenuates"), t(" (far/near amplitude median ≈ 0.44), "), b("broadens"), t(" (FWHM ratio ≈ 1.31), yet largely "), b("preserves its shape"), t(" (waveform correlation ≈ 0.80). Within-species spread is large — it exceeds the between-species differences.")]));
kids.push(...figure("self_aligned_channels.png", "Near vs far response per species, each self-aligned on its own peak (arbitrary gap), BOTH normalised to the near peak so the far amplitude drop is visible. Thick = median, band = IQR. The far/near amplitude ratio is printed per panel (e.g. Argentian Dollar 0.15, Ornamental Chile 0.19; Tomato and the chiles preserve amplitude best)."));
kids.push(...figure("near_to_far_transformation.png", "The same three metrics pooled across all recordings: amplitude ratio (median 0.44), width ratio (1.31), and waveform similarity (0.80)."));
kids.push(...figure("attenuation_vs_broadening.png", "Attenuation vs broadening co-vary: signals that lose amplitude also disperse (passive low-pass filtering); those that keep amplitude keep their shape."));

// -------- 7. Comparative
kids.push(pageBreak());
kids.push(h1("Do these properties track evolutionary relationship?"));
kids.push(p([t("No. A Mantel test between functional distance (the three transformation metrics) and taxonomic distance gives r = −0.02, p = 0.50; Kruskal–Wallis by family is non-significant (p > 0.29). Congeners diverge as much as unrelated species — the two "), b("Capsicum"), t(" chiles are among the most different pairs. The transformation reflects the biophysics of each conduction event, not species identity.")]));
kids.push(...figure("functional_dendrogram.png", "Species clustered by their near→far transformation profile; leaf colour = taxonomic family. Families are scattered, not clustered — no phylogenetic signal."));

// -------- 8. Active vs passive
kids.push(pageBreak());
kids.push(h1("Active or passive propagation? (what the data can and cannot say)"));
kids.push(p([t("Plant signals span a spectrum from self-regenerating action potentials (AP; all-or-none, non-decremental, shape-preserving) to decremental variation potentials (VP; graded, dispersive, carried by a xylem hydraulic/chemical wave). "), b("Two surface electrodes cannot settle this cleanly"), t(", and two tempting metrics are confounded: (i) amplitude/gain reflects "), it("electrode coupling"), t(" as much as decrement — Venus’s far/near ratio is scattered 0.12–7.33 because of its asymmetric hook/stake montage (below); and (ii) a flexible delayed-copy model will always out-fit a cable model because it has an extra free parameter. We therefore rely on "), b("amplitude-independent, shape-based"), t(" signals.")]));
kids.push(p([b("On those robust signals, a consistent spectrum emerges. "), t("The peak−onset asymmetry (does the peak lag the onset, i.e. dispersion?) is ≈0 for Venus flytrap and Sensitive Mimosa and large for the mints; the propagation delay scales linearly with distance (exponent ≈ 0.99, i.e. constant velocity, not diffusive). Together these place the fast rapid-movement species at the shape-preserving (AP-like) end and the mints at the dispersive (VP-like) end — a spectrum of waveform fidelity that crosses family lines. This is consistent with, but not proof of, active vs passive conduction; the definitive tests need new experiments (Section 11).")]));
kids.push(...figure("peak_onset_asymmetry.png", "Peak−onset delay asymmetry (amplitude-independent): ≈0 = rigid translation / shape-preserving (Venus, Mimosa), large positive = dispersion (mints)."));
kids.push(...figure("delay_vs_distance.png", "Delay vs distance across recordings: linear through ~origin (exponent ≈ 0.99) indicates constant-velocity (ballistic) propagation, not diffusion (which would give exponent 2)."));
kids.push(...figure("kernel_example_active.png", "Illustrative shape-preserving example (Venus flytrap): the far trace is a near-pure delayed copy of the near trace (little extra dispersion)."));
kids.push(...figure("kernel_example_passive.png", "Illustrative dispersive example (Creeping Inchplant): the sharp near transient is smeared into a broad, attenuated far bump."));
kids.push(p([b("Why Venus flytrap’s amplitude looks decremental but is not diagnostic. "), t("Its far/near amplitude ratio is scattered and >1 in 31% of recordings — unlike the consistent <1 decrement of the symmetric-electrode plants — because Venus used an asymmetric montage (hook around the trap neck + stake alongside the lobe). The amplitude ratio therefore reflects electrode coupling, not decrement; on the shape axis Venus is firmly shape-preserving.")]));
kids.push(...figure("venus_electrode_asymmetry.png", "Amplitude ratio (far/near, log scale) per species. Venus is scattered and often >1 (asymmetric electrodes), unlike the consistent <1 decrement of symmetric-electrode plants."));

// -------- 9. Simulation
kids.push(pageBreak());
kids.push(h1("Simulating propagation"));
kids.push(p([b("Passive cable vs active wave. "), t("A passive cable (Green’s function of τ ∂V/∂t = λ² V_xx − V) makes the far signal a delayed, decayed and dispersed copy of the near one; a FitzHugh–Nagumo active cable launches a travelling pulse of constant amplitude and velocity. The amplitude-vs-distance panel is the single cleanest conceptual discriminator.")]));
kids.push(...figure("cable_vs_fhn_sim.png", "Passive cable (decays and broadens with distance) vs FitzHugh–Nagumo active wave (constant amplitude and velocity)."));
kids.push(p([b("A biophysical Venus-flytrap AP model. "), t("A Hodgkin-Huxley-type plant AP (cvplants.simulate.plant_ap_hh) uses the established plant ionic mechanism: a stimulus admits Ca²⁺; Ca²⁺ gates a depolarising anion (Cl⁻) efflux; the depolarisation opens voltage-gated Ca²⁺ (positive feedback → an all-or-none spike); voltage-gated K⁺ and Ca²⁺ removal repolarise. Plants use Cl⁻/K⁺, "), b("not"), t(" Na⁺, and the AP lasts ~1–2 s. Passed through the recording band-pass, the model AP reproduces the biphasic waveform recorded from Venus flytrap (right panel), and it fires all-or-none. Parameters are illustrative (Hedrich & Neher 2018 / Sukhov-Vodeneev framework), not fitted conductances — surface, band-passed recordings cannot constrain those.")]));
kids.push(...figure("venus_ap_model.png", "HH-type plant AP model (Ca²⁺→Cl⁻→K⁺). Left: membrane potential and Ca²⁺. Middle: all-or-none (fixed-size spike only above threshold). Right: the model AP, band-passed like the recordings, matches a real Venus AP."));
kids.push(p([it("Supporting: for each recording we also predicted the far trace from the near trace with a delayed-copy model (below) — a qualitative check that the far trace is a delayed copy of the near one. It is not a fair active-vs-passive test (see Section 8) and is shown only as an illustration.")]));
kids.push(...figure("sim_vs_real_examples.png", "Qualitative: a delayed-copy model (blue dashed) predicting the real far trace (red) for one recording per species."));

// -------- 10. Ion channels
kids.push(pageBreak());
kids.push(h1("Ion channels and molecular basis (context)"));
kids.push(p([t("Plant excitation is Ca²⁺/Cl⁻/K⁺-based, "), b("not"), t(" Na⁺-based as in animal axons (Fromm & Lautner 2007; Sukhov & Vodeneev 2009).")]));
kids.push(bullet("Depolarisation — Ca²⁺ influx via GLUTAMATE-RECEPTOR-LIKE channels (clade-3 GLR3.3 / GLR3.6) (Mousavi et al. 2013; Toyota et al. 2018; Nguyen et al. 2018)."));
kids.push(bullet("Sustained depolarisation — anion (Cl⁻) efflux via SLAC1/SLAH3 and QUAC1/ALMT12 (established in guard cells)."));
kids.push(bullet("Repolarisation — K⁺ efflux via the outward rectifier GORK (Salvador-Recatalà 2018); resting potential set by the P-type H⁺-ATPase (AHA)."));
kids.push(bullet("Variation potential — transient H⁺-ATPase inactivation behind a xylem “Ricca factor” wave (Vodeneev/Sukhov; Evans et al. 2017)."));
kids.push(bullet("Venus flytrap — trigger-hair mechanosensing → all-or-none Ca²⁺ AP; AP “counting” gates jasmonate signalling (Böhm et al. 2016; Hedrich & Neher 2018). Mimosa pudica — touch → Ca²⁺ → Cl⁻/K⁺ + water efflux collapses pulvinar turgor (Allen 1969)."));

// -------- 11. New experiments
kids.push(h1("What this dataset cannot decide — and the minimal new experiment"));
kids.push(table(
  ["Open question", "Minimal new experiment"],
  [
    ["True all-or-none threshold", "Stimulus-intensity ladder at one site: step response (active) vs graded (passive)"],
    ["Refractory period", "Paired-pulse Δt = 0.5–20 min: is the second response abolished/reduced?"],
    ["Regenerative ion mechanism", "Pharmacology (La³⁺/Gd³⁺, A-9-C/DIDS, TEA) between wound and electrodes"],
    ["Channel-gated vs physical conduction", "Q10 series (15/25/35 °C): active ≈ 2–3, passive ≈ 1"],
    ["Hydraulic vs electrical primacy", "Co-record xylem pressure / stem strain with the electrodes"],
    ["Clean delays for fast species", "Bipolar (differential) recording to cancel the shared-reference common mode"],
  ],
  [3200, 6160]));

// -------- 12. Figure guidance
kids.push(h1("Figure selection guidance for the manuscript"));
kids.push(p([b("Manuscript candidates (the core story): "), t("conduction velocity by species (Fig. 1); validation vs the manual analysis (Fig. 2); the near→far transformation, self-aligned and normalised to show the amplitude drop (Fig. 6); no phylogenetic signal (Fig. 9); the passive-vs-active simulation concept (Fig. 15); and the biophysical Venus AP model (Fig. 16).")]));
kids.push(p([b("Supporting / diagnostic (methods, reviewer questions, or the repository): "), t("the per-recording delay validation and the estimator bakeoff (Figs. 3–4, explaining the Mimosa case); the shared-reference raw traces (Fig. 5); the pooled transformation metrics and attenuation–broadening co-variation (Figs. 7–8); the shape-based active/passive discriminators, illustrative kernel examples, and the Venus electrode-asymmetry control (Figs. 10–14); and the qualitative far-trace prediction (Fig. 17).")]));
kids.push(p([it("Deliberately removed from an earlier draft: a Cannabis-only distance–delay scatter (unclear); a near-aligned overlay that smeared the far channel (superseded by Fig. 6); a gain-vs-dispersion “active/passive space” and a model-R² comparison (both confounded — the amplitude/gain axis reflects electrode coupling, and the delayed-copy model has an unfair extra parameter).")]));

// -------- 13. References
kids.push(pageBreak());
kids.push(h1("Key references"));
const refs = [
  "Contreras C, Morales M, Rojas P, Serbe-Kamp E, Marzullo T. Electrical Conduction Velocity Across Species of Rapid Movement and Non-Rapid Movement Plants. Plant Signaling & Behavior (the manual analysis compared here).",
  "Fromm J, Lautner S (2007). Electrical signals and their physiological significance in plants. Plant, Cell & Environment 30:249–257.",
  "Mousavi SAR, et al. (2013). GLUTAMATE RECEPTOR-LIKE genes mediate leaf-to-leaf wound signalling. Nature 500:422–426.",
  "Toyota M, et al. (2018). Glutamate triggers long-distance, calcium-based plant defense signaling. Science 361:1112–1115.",
  "Nguyen CT, et al. (2018). Identification of cell populations necessary for leaf-to-leaf electrical signaling. PNAS 115:10178–10183.",
  "Salvador-Recatalà V (2018). The AKT2/GORK potassium channels shape the plant action potential. Int. J. Mol. Sci. 19:926.",
  "Böhm J, et al. (2016). The Venus flytrap counts prey-induced action potentials to induce sodium uptake. Current Biology 26:286–295.",
  "Hedrich R, Neher E (2018). Venus flytrap: how an excitable, carnivorous plant works. Trends in Plant Science 23:220–234.",
  "Allen RD (1969). Mechanism of the seismonastic reaction in Mimosa pudica. Plant Physiology 44:1101–1107.",
  "Vodeneev V, Akinchits E, Sukhov V (2015). Variation potential in higher plants. Plant Signaling & Behavior 10:e1057365.",
  "Evans MJ, et al. (2017). A chemical agent transported by xylem mass flow propagates variation potentials. The Plant Journal 91:1029–1037.",
  "Sukhov V, Vodeneev V (2009). A mathematical model of action potential in cells of vascular plants. J. Membrane Biology 232:59–67.",
  "Sukhov V, et al. (2011). Simulation of action potential propagation in plants. J. Theoretical Biology 291:47–55.",
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
  const primary = path.join(ROOT, "results", "Plant_conduction_velocity_report.docx");
  let out = primary;
  try {
    fs.writeFileSync(out, buf);
  } catch (e) {
    if (e.code === "EBUSY" || e.code === "EPERM") {
      out = path.join(ROOT, "results", "Plant_conduction_velocity_report_revised.docx");
      fs.writeFileSync(out, buf);
      console.log("(primary file was open/locked; wrote revised copy instead)");
    } else { throw e; }
  }
  console.log("wrote", out, "-", FIGN, "figures,", SECN, "sections");
});
