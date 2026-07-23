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
// pooled figure + AP-only + VP-only variants (co-author request for Figs 7-10,12,13,16,17,18)
function splitfig(file, caption) {
  const base = file.replace(/\.png$/, "");
  const label = caption.split(/[.—]/)[0].trim();
  return [
    ...figure(file, caption),
    ...figure(base + "_AP.png", `${label} — action-potential (AP-like) recordings only.`),
    ...figure(base + "_VP.png", `${label} — variation-potential (VP-like) recordings only.`),
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
  children: [new TextRun({ text: "An automatic two-channel pipeline: from reproducing the manual analysis to predicting the propagation mode", size: 23, color: "555555" })] }));
kids.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
  children: [new TextRun({ text: "13 species · 176 recordings (166 analysed) · github.com/ETigerschuss/conduction-velocity-plants", size: 18, color: "888888" })] }));
kids.push(rule());

// -------- 1. Overview (the 5-part story)
kids.push(h1("Overview: the argument in five steps"));
kids.push(p([t("Two electrodes sit inline downstream of a stimulus; the propagating potential reaches the "), b("near"), t(" electrode first and the "), b("far"), t(" electrode later. Building on the open pipeline of Madariaga et al. (2024), we extend it into an automatic analysis and make five linked claims.")]));
kids.push(p([b("1. A modified pipeline reproduces the manual analysis. "), t("With plant-class-aware peak detection it matches the hand-measured conduction velocities at Pearson r = 0.94 (0.99 excluding one species), and recovers the published per-recording numbers exactly (Section 3).")]));
kids.push(p([b("2. It detects the two potential types. "), t("Recordings separate cleanly into fast action potentials and slow variation potentials — the two signal classes Mimosa and others are known to fire (Section 4).")]));
kids.push(p([b("3. It compares the two channels. "), t("From near to far the signal attenuates (~0.4×) and mildly broadens, while largely preserving its shape (Section 5).")]));
kids.push(p([b("4. It models the waveform and propagation to predict active vs passive. "), t("Using what is known about fast-moving plants as a reference, the fits place each species on an active↔passive spectrum and yield a per-species prediction for the untested species (Section 6). We predict, not conclude.")]));
kids.push(p([b("5. It groups species by every parameter and tests phylogeny. "), t("Clustering on all parameters (CV, attenuation, broadening, waveform fidelity, dispersion, potential type) shows the propagation profile is "), b("not"), t(" phylogenetically structured — e.g. Solanaceae are not internally more similar than average (Section 7).")]));
kids.push(p([it("This is a working report; Section 10 lists which figures are manuscript candidates versus supporting material.")]));

// -------- 2. Methods
kids.push(h1("Methods"));
kids.push(p([t("Each channel is baseline-subtracted and filtered; the earlier-peaking channel is labelled "), b("near"), t(". "), b("Peak detection is plant-class-aware, as in the manual analysis: "), t("slow (variation-potential) recordings are timed on the dominant deflection, while rapid-movement plants (Venus flytrap, Sensitive Mimosa) fire a sharp, often biphasic action potential and are timed on the "), it("first prominent peak"), t(" (≥ 0.5× max) on an AP-preserving 0.15–15 Hz band-pass. Inter-channel delay uses windowed cross-correlation, with a common-mode-robust 2-tap model where the shared soil reference dominates (Section 5). CV = inter-electrode distance / delay; distances come from the “Todo Data Resumen” spreadsheet (166/176 recordings). Transformation metrics: amplitude attenuation, temporal broadening (FWHM), waveform similarity. The pipeline reports three CV columns — "), it("cv_xcorr"), t(", "), it("cv_2tap"), t(", and "), it("cv_manual"), t(" (distance ÷ the experimenters’ manual delay).")]));

// ============ PART 1 ============
kids.push(pageBreak());
kids.push(h1("Reproducing the manual analysis (Contreras et al.)"));
kids.push(p([t("We validate against the manual analysis in "), it("Electrical Conduction Velocity Across Species of Rapid Movement and Non-Rapid Movement Plants"), t(" (Contreras, Morales, Rojas, Serbe-Kamp, Marzullo), Table 1. Both analyses use the same recordings.")]));
kids.push(p([b("Strong agreement: Pearson r = 0.94 across 13 species (0.99 excluding Sensitive Mimosa). "), t("The non-rapid group mean matches almost exactly (automatic 8.0 vs manual 7.7 mm/s); Venus flytrap agrees (32.9 vs 35.3). Using the experimenters’ own delays, the "), it("cv_manual"), t(" column reproduces the manuscript exactly (Mimosa 30.6, Venus 35.7 mm/s).")]));
kids.push(...figure("cv_by_species.png", "Conduction velocity by species (resolved-delay recordings). Box = IQR, red = median, dots = recordings."));
kids.push(...figure("compare_to_paper_scatter.png", "Automatic CV vs manual CV, per species (mean ± SD). Points on the identity line agree; only Sensitive Mimosa sits clearly below (see text)."));
kids.push(...figure("delay_validation.png", "The underlying agreement: our measured inter-channel delay vs the manual delay (Tiempo), recording by recording, on the identity line."));
kids.push(p([b("What made this work — plant-class-aware detection. "), t("The rapid-movement plants needed the first-prominent-peak detector (Methods): the default low-pass over-smooths the sharp AP and mistimes it. Switching detectors reproduced the manual delay for most Mimosa/Venus recordings and raised Venus from 29.7 to 32.9 mm/s. For non-rapid plants the default cross-correlation already matched best (a fast-onset estimator and three variants were tested and rejected — median error 0.20 s vs 1.80 s; bakeoff figure).")]));
kids.push(...figure("delay_estimator_bakeoff.png", "Delay-estimator bakeoff for the non-rapid plants (lower = better): the default cross-correlation wins for every species. Rapid plants use first-prominent detection instead (Methods)."));
kids.push(p([b("The residual Sensitive Mimosa gap (automatic 19.9 vs manual 32.4) is a measurement-floor limit, not a code error. "), t("On the fast (July) Mimosa recordings, isolating the sharp AP (high-pass) and cross-correlating gives ≈ 0 s — the AP reaches both closely-spaced electrodes essentially simultaneously — while the same test recovers the slower recordings (1.07 vs manual 1.04 s). Those manual 0.2–0.34 s values sit at the timing floor, which is why Mimosa’s manual SD (21.6) nearly equals its mean. Part of Mimosa’s spread is also that it contains two signal types (Section 4). Metadata corrected from the paper: Hierbabuena = Clinopodium douglasii; Chilean Chile = Capsicum baccatum; amplifier ≈ 0.2–130 Hz.")]));

// ============ PART 2 ============
kids.push(pageBreak());
kids.push(h1("Two potential types: action potentials and variation potentials"));
kids.push(p([t("Mimosa pudica and other plants fire "), b("two"), t(" kinds of electrical signal: a fast, often biphasic "), b("action potential"), t(" (non-damaging stimuli; ~1 s; ~2–3 cm/s) and a slow, long-lasting "), b("variation potential"), t(" (wounding; tens–hundreds of seconds; decremental) — Volkov 2010; Fromm & Lautner 2007.")]));
kids.push(p([b("We do not assume which species fire which — we infer the type per recording. "), t("Classifying each recording by the duration of its dominant deflection gives a bimodal split (113 AP-like < 2 s, 53 VP-like). Crucially, "), b("no species is purely one type"), t(": the AP-like fraction runs from 0.36 (Mint, VP-dominant) to 0.88 (Hierbabuena, AP-dominant), so most species show a mixture. "), it("Caveat: "), t("this is a proxy — the type is read from the waveform, and the amplifier’s ~0.2 Hz high-pass removes the slow DC that defines a VP, so 'duration' captures how sharp/fast the recorded transient is, not the full VP timescale. We therefore present the active↔passive character as a "), b("continuum"), t(", not a hard dichotomy.")]));
kids.push(p([b("Treated as two populations, the types propagate differently — two mechanisms. "), t("Longer-duration signals are more dispersive (σ vs duration ρ = +0.22, p = 0.004), lower waveform fidelity (ρ = −0.20, p = 0.009) and slightly slower — so AP-like recordings are faster, less dispersive and more shape-preserving (active-like) while VP-like are the opposite (passive-like). The right model therefore differs by type: the biophysical action-potential model (Section 6) fits the AP-type; a passive/hydraulic model would fit the VP-type. This is a real but "), b("modest"), t(" trend, consistent with — not proof of — two distinct mechanisms.")]));
kids.push(p([b("What the stimulus predicts, and what the literature actually demonstrates. "), t("The type is set by the stimulus: non-damaging stimuli (touch, cold) evoke fast action potentials, whereas wounding (flame/burn) evokes slow variation potentials (Fromm & Lautner 2007; Sukhov et al. 2019). "), b("This study used a flame,"), t(" so on first principles most recordings should be variation potentials — except the rapid-movement plants (Venus flytrap, Sensitive Mimosa), whose sharp biphasic signals are genuine, well-characterised APs (Sibaoka 1991; Hodick & Sievers 1988; Pavlović et al. 2017). A literature audit (docs/references) shows the AP/VP distinction is only firmly "), it("demonstrated"), t(" for a few of our species — tomato (Wildon et al. 1992; Rhodes, Thain & Wildon 1996, 1999), Mimosa and Venus — while for basil, Plectranthus and Ruda the flame response is reported merely as a "), it("“putative wound potential,”"), t(" and for Capsicum, mint, rosemary, Cannabis and Callisia no propagating AP or VP has been recorded at all. Two consequences follow: (i) our per-recording label is a waveform "), b("proxy"), t(" — the ~0.2 Hz high-pass strips the slow DC that defines a true VP, so a short 'AP-like' transient is not proof of a regenerative AP; and (ii) the flame stimulus makes the VP-only panels below the more physiologically expected case for the non-rapid species, with the AP-only panels dominated by the rapid movers.")]));
kids.push(...figure("two_mechanisms.png", "The two potential types treated as separate populations. Left: every species is a mixture (AP-like green, VP-like purple; fraction inferred per recording). Middle: the active↔passive character (dispersion σ) varies continuously with duration — a spectrum, not a switch. Right: AP-like recordings are faster, less dispersive and higher-fidelity (active-like); VP-like the opposite (passive-like)."));

// ============ PART 3 ============
kids.push(pageBreak());
kids.push(h1("From near to far: comparing the two channels"));
kids.push(p([t("The two channels are "), b("correlated by design"), t(" — both electrodes share a soil/earth reference, so any whole-plant potential appears in both (baseline r ≈ 0.66). This is a normal referential montage, not crosstalk, and it does not prevent measuring the delay (a common-mode-robust 2-tap model separates the shared part from the propagated part).")]));
kids.push(...figure("crosstalk_raw_examples.png", "Both channels, full trace and pre-stimulus baseline. Mimosa: baseline r = 0.96 (shared slow wave via the common ground). Cannabis: r = 0.20 (clean delay). Venus: a sharp spike in both channels close together."));
kids.push(p([b("From near to far the potential attenuates and broadens, while largely preserving its shape "), t("(far/near amplitude median ≈ 0.44, FWHM ratio ≈ 1.31, waveform correlation ≈ 0.80). Within-species spread exceeds between-species differences.")]));
kids.push(...splitfig("self_aligned_channels.png", "Near vs far response per species, each self-aligned on its own peak (arbitrary gap), both normalised to the near peak so the far amplitude drop is visible. Thin traces coloured by potential type (AP-like green, VP-like purple); thick = median, band = IQR; far/near ratio printed per panel."));
kids.push(...splitfig("near_to_far_transformation.png", "The three metrics pooled across all recordings: amplitude ratio (median 0.44), width ratio (1.31), waveform similarity (0.80)."));
kids.push(...splitfig("attenuation_vs_broadening.png", "Attenuation vs broadening co-vary: signals that lose amplitude also disperse (passive low-pass filtering); those that keep amplitude keep their shape."));

// ============ PART 4 ============
kids.push(pageBreak());
kids.push(h1("Active or passive? Modelling and predicting the propagation mode"));
kids.push(p([t("Plant signals span a spectrum from self-regenerating action potentials (active; all-or-none, non-decremental, shape-preserving) to decremental variation potentials (passive; graded, dispersive). "), b("Two surface electrodes cannot settle this definitively"), t(", so we make a "), b("prediction"), t(", not a conclusion, using two amplitude-independent handles.")]));
kids.push(p([b("How we fit — and what we discarded. "), t("For every recording we predict the far trace from the near trace with an "), b("active"), t(" model (delayed copy, far ≈ g·near(t−τ)) and a "), b("passive"), t(" model (delayed + dispersed, far ≈ g·[Gaussian(σ)*near](t−τ)), each optimised to its best parameters. We fit the "), it("waveform"), t(" (gain free — shape only), which is the trustworthy comparison. We "), b("dropped the amplitude fit"), t(" (gain fixed = 1): it is uninterpretable — the active model collapses (R² < −50) because the far amplitude is not preserved, but that drop is confounded by electrode coupling (Venus’s asymmetric hook/stake montage gives far/near ratios scattered 0.12–7.3), so amplitude cannot discriminate active from passive. The passive model contains the active model (σ = 0), so the "), b("gap"), t(" between them is how much dispersion is needed.")]));
kids.push(...splitfig("model_comparison_bars.png", "Active vs passive waveform fit per species (each recording a dot, bar = median). Venus flytrap and Sensitive Mimosa have the highest R² and smallest gap (shape-preserving, active-like); the mints need the most dispersion (passive-like)."));
kids.push(...figure("model_fit_examples.png", "Example fits (near/far corrected): near (grey), real far (red), best active (blue dashed) and passive (green dotted) predictions."));
kids.push(p([b("Two amplitude-independent discriminators agree. "), t("Peak−onset asymmetry (dispersion) is ≈ 0 for Venus/Mimosa and large for the mints; the delay scales linearly with distance (exponent ≈ 0.99 — constant velocity, not diffusion).")]));
kids.push(...splitfig("peak_onset_asymmetry.png", "Peak−onset asymmetry (amplitude-independent): ≈ 0 = rigid translation (active), large = dispersion (passive)."));
kids.push(...splitfig("delay_vs_distance.png", "Delay vs distance: linear through ~origin (exponent ≈ 0.99) = constant-velocity propagation, not diffusion."));
kids.push(p([b("Simulations reproduce the waveforms. "), t("A passive cable makes the far signal a delayed, decayed, dispersed copy of the near one; a FitzHugh–Nagumo active cable gives a constant-amplitude travelling pulse. A Hodgkin–Huxley-type plant AP model (Ca²⁺→Cl⁻→K⁺, no Na⁺), passed through the recording band-pass, reproduces the recorded Venus waveform and fires all-or-none — a concrete active model for the AP-type recordings.")]));
kids.push(...figure("cable_vs_fhn_sim.png", "Passive cable (decays and broadens with distance) vs FitzHugh–Nagumo active wave (constant amplitude and velocity)."));
kids.push(...figure("venus_ap_model.png", "HH-type plant AP model (Ca²⁺→Cl⁻→K⁺). Left: V and Ca²⁺. Middle: all-or-none. Right: the band-passed model AP matches a real Venus AP."));
kids.push(p([b("The prediction. "), t("Combining the amplitude-independent handles (dispersion, peak−onset asymmetry, waveform fidelity) into a single score classifies each species as active-leaning, passive-leaning or ambiguous. Venus flytrap and Sensitive Mimosa — the known action-potential plants — come out active-leaning, validating the score; Ornamental Chile and most mints are passive-leaning; the rest are intermediate. This is our prediction for the untested species, to be confirmed by the experiments in Section 9.")]));
kids.push(...splitfig("predicted_propagation_mode.png", "Predicted propagation mode per species (passiveness score = dispersion + peak−onset asymmetry − waveform fidelity, z-scored). Green = active-leaning, red = passive-leaning; the known AP plants (Venus, Mimosa) score most active."));
kids.push(...splitfig("venus_electrode_asymmetry.png", "Control: Venus’s far/near amplitude ratio is scattered and often > 1 (asymmetric electrodes), unlike the consistent decrement of symmetric-electrode plants — why amplitude is not used above."));

// ============ PART 5 ============
kids.push(pageBreak());
kids.push(h1("Grouping by all parameters: is propagation phylogenetically structured?"));
kids.push(p([t("Finally we group species using every parameter found along the way — CV, attenuation, broadening, waveform fidelity, dispersion σ, and AP-like fraction. If signal transmission were phylogenetically constrained, congeners and same-family species would cluster. They do "), b("not"), t(".")]));
kids.push(...splitfig("parameter_clustermap.png", "Species clustered by all propagation parameters (label colour = family). Families are scattered across the tree — no phylogenetic structure. Venus flytrap and Sensitive Mimosa cluster as the active pair."));
kids.push(p([b("Solanaceae are not internally more similar. "), t("A Mantel test between functional distance and taxonomic distance is null (r = −0.02, p = 0.50). Breaking it down by family: Lamiaceae (5 species) are marginally more similar within (mean within-distance 2.35 vs 2.89 to others), but "), b("Solanaceae (3 species) are not"), t(" — the two Capsicum chiles and Tomato are more different from each other (3.72) than from species in other families (3.00). Congeners diverge as much as unrelated species. The propagation profile reflects the biophysics of each conduction event and the signal type, not the species’ ancestry.")]));

// -------- Ion channels
kids.push(pageBreak());
kids.push(h1("Ion channels and molecular basis (context)"));
kids.push(p([t("Plant excitation is Ca²⁺/Cl⁻/K⁺-based, "), b("not"), t(" Na⁺-based (Fromm & Lautner 2007; Sukhov & Vodeneev 2009).")]));
kids.push(bullet("Depolarisation — Ca²⁺ influx via GLUTAMATE-RECEPTOR-LIKE channels (GLR3.3 / GLR3.6) (Mousavi 2013; Toyota 2018; Nguyen 2018)."));
kids.push(bullet("Sustained depolarisation — anion (Cl⁻) efflux via SLAC1/SLAH3 and QUAC1/ALMT12."));
kids.push(bullet("Repolarisation — K⁺ efflux via GORK (Salvador-Recatalà 2018); resting potential set by the P-type H⁺-ATPase (AHA)."));
kids.push(bullet("Variation potential — transient H⁺-ATPase inactivation behind a xylem “Ricca factor” wave (Evans 2017)."));
kids.push(bullet("Venus flytrap — trigger-hair mechanosensing → all-or-none Ca²⁺ AP; AP counting gates jasmonate signalling (Böhm 2016; Hedrich & Neher 2018). Mimosa pudica — Ca²⁺-mediated Cl⁻/K⁺ efflux collapses pulvinar turgor; fires both APs and VPs (Volkov 2010)."));

// -------- Limitations / new experiments
kids.push(h1("What this dataset cannot decide — and the minimal new experiment"));
kids.push(table(
  ["Open question", "Minimal new experiment"],
  [
    ["True all-or-none threshold", "Stimulus-intensity ladder: step response (active) vs graded (passive)"],
    ["Refractory period", "Paired-pulse Δt = 0.5–20 min: is the second response abolished?"],
    ["Regenerative ion mechanism", "Pharmacology (La³⁺/Gd³⁺, A-9-C/DIDS, TEA) between wound and electrodes"],
    ["Channel-gated vs physical conduction", "Q10 series (15/25/35 °C): active ≈ 2–3, passive ≈ 1"],
    ["Unresolvable fast delays (Mimosa AP)", "Wider electrode spacing so the small AP delay clears the timing floor"],
    ["Clean delays for the fast species", "Bipolar (differential) recording to cancel the shared-reference common mode"],
  ],
  [3200, 6160]));

// -------- Figure guidance
kids.push(h1("Figure selection guidance for the manuscript"));
kids.push(p([b("Manuscript candidates (one per step of the argument): "), t("CV by species (Fig. 1); validation vs the manual analysis (Fig. 2); the two potential types (Fig. 5); the near→far transformation (Fig. 10); the active-vs-passive model comparison (Fig. 16) with the predicted propagation mode (Fig. 28); the biophysical Venus AP model (Fig. 27); and the all-parameter clustering / phylogeny result (Fig. 34). The AP-only and VP-only companion panels (Figs. 8–9, 11–12, 14–15, 17–18, 21–22, 24–25, 29–30, 32–33, 35–36) are supporting material showing each result holds within each potential type.")]));
kids.push(p([b("Supporting / diagnostic: "), t("delay validation and estimator bakeoff (Figs. 3–4); shared-reference raw traces (Fig. 6); pooled transformation and attenuation–broadening (Figs. 10, 13); example model fits (Fig. 19) and the amplitude-independent discriminators (Figs. 20, 23); the passive-vs-active simulation concept (Fig. 26); and the Venus electrode-asymmetry control (Fig. 31).")]));
kids.push(p([it("Removed in revision: the amplitude (gain = 1) model fit (uninterpretable — confounded by electrode coupling); a Cannabis-only distance–delay scatter; near-aligned overlays that smeared the far channel; and the gain-vs-dispersion “space”. Superseded by the corrected, optimised comparisons here.")]));

// -------- References
kids.push(pageBreak());
kids.push(h1("Key references"));
const refs = [
  "Contreras C, Morales M, Rojas P, Serbe-Kamp E, Marzullo T. Electrical Conduction Velocity Across Species of Rapid Movement and Non-Rapid Movement Plants. Plant Signaling & Behavior (the manual analysis compared here).",
  "Madariaga D, et al. (2024). A library of electrophysiological responses in plants — open-science model. Plant Signaling & Behavior 19(1):2310977 (the base pipeline).",
  "Volkov AG, et al. (2010). Signal transduction in Mimosa pudica: biologically closed electrical circuits. Plant, Cell & Environment 33:816–827.",
  "Fromm J, Lautner S (2007). Electrical signals and their physiological significance in plants. Plant, Cell & Environment 30:249–257.",
  "Mousavi SAR, et al. (2013). GLUTAMATE RECEPTOR-LIKE genes mediate leaf-to-leaf wound signalling. Nature 500:422–426.",
  "Toyota M, et al. (2018). Glutamate triggers long-distance, calcium-based plant defense signaling. Science 361:1112–1115.",
  "Nguyen CT, et al. (2018). Cell populations necessary for leaf-to-leaf electrical signaling. PNAS 115:10178–10183.",
  "Böhm J, et al. (2016). The Venus flytrap counts prey-induced action potentials to induce sodium uptake. Current Biology 26:286–295.",
  "Hedrich R, Neher E (2018). Venus flytrap: how an excitable, carnivorous plant works. Trends in Plant Science 23:220–234.",
  "Evans MJ, et al. (2017). A chemical agent transported by xylem mass flow propagates variation potentials. The Plant Journal 91:1029–1037.",
  "Sukhov V, Vodeneev V (2009). A mathematical model of action potential in cells of vascular plants. J. Membrane Biology 232:59–67.",
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
  try { fs.writeFileSync(out, buf); }
  catch (e) {
    if (e.code === "EBUSY" || e.code === "EPERM") {
      out = path.join(ROOT, "results", "Plant_conduction_velocity_report_revised.docx");
      fs.writeFileSync(out, buf);
      console.log("(primary open/locked; wrote revised copy)");
    } else throw e;
  }
  console.log("wrote", out, "-", FIGN, "figures,", SECN, "sections");
});
