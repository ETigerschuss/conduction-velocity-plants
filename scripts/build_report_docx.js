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
    ...figure(base + "_AP.png", `${label} — short-duration (< 2 s) recordings only. A waveform subset, not an action-potential subset (Section 4).`),
    ...figure(base + "_VP.png", `${label} — long-duration (> 2 s) recordings only. A waveform subset, not a variation-potential subset (Section 4).`),
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
  children: [new TextRun({ text: "An automatic two-channel pipeline: reproducing the manual analysis, characterising the near→far transformation, and what two surface electrodes can and cannot resolve", size: 23, color: "555555" })] }));
kids.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
  children: [new TextRun({ text: "13 species · 176 recordings (166 analysed) · github.com/ETigerschuss/conduction-velocity-plants", size: 18, color: "888888" })] }));
kids.push(rule());

// -------- 1. Overview (the 5-part story)
kids.push(h1("Overview: the argument in five steps"));
kids.push(p([t("Two electrodes sit inline downstream of a stimulus; the propagating potential reaches the "), b("near"), t(" electrode first and the "), b("far"), t(" electrode later. Building on the open pipeline of Madariaga et al. (2024), we extend it into an automatic analysis and make five linked claims.")]));
kids.push(p([b("1. A modified pipeline reproduces the manual analysis. "), t("With plant-class-aware peak detection it matches the hand-measured conduction velocities at Pearson r = 0.94 (0.99 excluding one species), and recovers the published per-recording numbers exactly (Section 3).")]));
kids.push(p([b("2. It resolves a fast↔slow waveform axis — which is "), it("not"), b(" an AP/VP classification. "), t("Recordings differ systematically in how sharp the transient is, and we quantify that. But we tested whether this axis identifies action potentials versus variation potentials, and it does "), b("not"), t(" (Section 4). Under a flame — a wounding stimulus — the honest description of the signals in the non-rapid species is "), b("variation / wound potentials"), t(".")]));
kids.push(p([b("3. It compares the two channels. "), t("From near to far the signal attenuates (~0.4×) and mildly broadens, while largely preserving its shape (Section 5).")]));
kids.push(p([b("4. Modelling shows this montage cannot adjudicate active vs passive — and everything we record is consistent with passive spread. "), t("A passive (delayed + dispersed) model out-fits an active (delayed copy) model in "), b("176 of 176 recordings"), t(" on waveform R², and still wins 153/176 under BIC, which penalises its extra parameter — including in Venus flytrap and Mimosa, whose action potentials are independently established. We therefore report this as a "), b("negative / methodological result"), t(", not a per-species propagation-mode prediction (Section 6).")]));
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
kids.push(h1("A fast↔slow waveform axis — and why it is not an AP/VP classification"));
kids.push(p([t("Plants fire two mechanistically distinct signals: a fast, often biphasic "), b("action potential"), t(" (AP; non-damaging stimuli — touch, cold; all-or-none, non-decremental) and a slow, long-lasting "), b("variation potential"), t(" (VP; wounding; tens–hundreds of seconds; graded and decremental) — Volkov 2010; Fromm & Lautner 2007. We asked whether our recordings can be sorted into these two classes automatically. "), b("They cannot"), t(", and reporting the attempt honestly is more useful than reporting a classification that does not hold.")]));
kids.push(p([b("The attempt. "), t("Each recording was labelled by the duration of its dominant deflection (time above 40 % of peak on a 0.15–15 Hz band): short (< 2 s) = “AP-like”, long (> 2 s) = “VP-like”. Across the 166 analysed recordings this yields 113 short and 53 long, and every species appears as a mixture (short-duration fraction 0.36–0.93). Taken at face value that would suggest all thirteen species fire both signal types. "), b("Four tests show that reading is wrong.")]));
kids.push(p([b("1. The ranking is biologically inverted. "), t("If the rule detected APs, the two species with independently established action potentials should top the list. They do not: Hierbabuena (0.93), Ornamental Chile (0.80) and Chilean Chile (0.78) rank above "), it("Sensitive Mimosa"), t(" (0.76, 4th) and "), it("Venus flytrap"), t(" (0.71, 8th of 13). The two mints land at opposite extremes (Hierbabuena 1st at 0.93, Mint last at 0.36), so taxonomy and biology are not driving the split.")]));
kids.push(p([b("2. The proportion is inverted relative to the stimulus. "), t("Wounding evokes VPs; non-damaging stimuli evoke APs (Fromm & Lautner 2007; Sukhov et al. 2019). "), b("This study used a flame"), t(" — a wounding stimulus — so nearly every recording should be a VP. The rule instead labels "), b("113/166 (68 %) as “AP-like”"), t(", the inverse of the biological prediction.")]));
kids.push(p([b("3. The recording chain destroys the feature that defines a VP. "), t("A VP is defined by a sustained, decremental DC plateau lasting tens to hundreds of seconds. The BackyardBrains amplifier’s ~0.2 Hz hardware high-pass, stacked with the 0.15 Hz analysis filter (τ ≈ 0.8 s each), differentiates that plateau into a ~1–2 s edge transient. A genuine VP is therefore pushed "), b("below"), t(" the 2 s threshold and mislabelled “AP-like”. This mechanistically explains the 68 % inflation in test 2.")]));
kids.push(p([b("4. The distribution is not bimodal, and the label predicts nothing. "), t("On a log scale the duration distribution is unimodal (Sarle bimodality coefficient 0.33; > 0.555 would indicate bimodality), so the 2 s cut is an arbitrary line through a continuum (13 recordings sit in the 1.5–2.5 s band alone). Decisively, "), b("within a movement class the label does not change conduction velocity"), t(": non-rapid species 5.58 mm/s (short) vs 5.92 mm/s (long), p = 0.99; rapid species 23.3 vs 20.9 mm/s, p = 0.91. What "), it("does"), t(" separate cleanly is the species axis the labels cross-cut — rapid movers 22.2 mm/s vs non-rapid 5.6 mm/s, p = 7 × 10⁻¹⁰.")]));
kids.push(p([b("Conclusion, and what we call the signals. "), t("The duration axis is a real "), b("waveform-sharpness descriptor"), t(" — it correlates with dispersion (σ vs duration ρ = +0.22, p = 0.004) and tracks the rapid/non-rapid distinction — but it is "), b("not"), t(" an AP-versus-VP diagnosis: it applies no all-or-none, refractory, non-decremental or pharmacological test. A literature audit (docs/references) reinforces this: a propagating AP is "), it("demonstrated"), t(" only for Mimosa, Venus flytrap and tomato (the last under non-damaging excision, not flame); for basil, Plectranthus and Ruda the only recorded flame response is a “putative wound potential”, whose authors explicitly decline to classify it; and for both chiles, mint, hierbabuena, rosemary, Cannabis and Callisia "), b("no propagating signal of either class has ever been recorded"), t(". Accordingly we describe the flame-evoked signals in the ten non-rapid species as "), b("variation / wound potentials"), t(", reserve “action potential” for the rapid movers, and treat the short/long split throughout this report as a descriptive waveform axis (“short-” and “long-duration” recordings), not a mechanism label.")]));
kids.push(...figure("two_mechanisms.png", "The fast↔slow waveform axis. Left: per-species fraction of short-duration recordings — note the ordering does not track the known-AP species. Middle: dispersion σ varies continuously with duration — a spectrum, not a switch. Right: short-duration recordings are faster, less dispersive and higher-fidelity. This is a waveform descriptor; it is not an AP/VP classification (see tests 1–4)."));

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
kids.push(h1("Active or passive? What two surface electrodes cannot decide"));
kids.push(p([t("Plant signals span a spectrum from self-regenerating action potentials (active; all-or-none, non-decremental, shape-preserving) to decremental variation potentials (passive; graded, dispersive). We set out to place each species on that spectrum. The result is a "), b("negative one"), t(", and we report it as such: this montage cannot adjudicate active versus passive, and every recording we have is consistent with passive spread of a wound-evoked response — which is exactly what a flame stimulus predicts.")]));
kids.push(p([b("How we fit. "), t("For every recording we predict the far trace from the near trace with an "), b("active"), t(" model (delayed copy, far ≈ g·near(t−τ)) and a "), b("passive"), t(" model (delayed + dispersed, far ≈ g·[Gaussian(σ)*near](t−τ)), each optimised to its best parameters. We fit the "), it("waveform"), t(" (gain free — shape only). We "), b("dropped the amplitude fit"), t(" (gain fixed = 1) as uninterpretable: the active model collapses (R² < −50) because far amplitude is not preserved, but that drop is confounded by electrode coupling, so amplitude cannot discriminate the two. The passive model "), b("contains"), t(" the active model as the special case σ = 0, so it cannot fit worse; the honest comparison is therefore BIC, which penalises its extra parameter.")]));
kids.push(p([b("The passive model wins everywhere — including where APs are certain. "), t("Active R² exceeds passive R² in "), b("0 of the 176 fitted recordings"), t(" (median R² 0.46 active vs 0.60 passive). Under BIC the passive model still wins "), b("153/176 (87 %)"), t(". Critically this includes "), it("Venus flytrap"), t(" (0.78 vs 0.88) and "), it("Sensitive Mimosa"), t(" (0.80 vs 0.84) — two species whose action potentials are established beyond doubt in the primary literature. The smallest active–passive gap belongs to "), it("Mint"), t(". A test that cannot recover regenerative propagation in Venus flytrap cannot be used to infer it, or its absence, in an untested species. We therefore "), b("withdraw any per-species active/passive prediction"), t(".")]));
kids.push(...splitfig("model_comparison_bars.png", "Active vs passive waveform fit per species (each recording a dot, bar = median). The passive model is never out-fit — including in Venus flytrap and Mimosa, whose APs are independently established. Interpret the bars as “how much dispersion is needed”, not as evidence of propagation mode."));
kids.push(...figure("model_fit_examples.png", "Example fits (near/far corrected): near (grey), real far (red), best active (blue dashed) and passive (green dotted) predictions."));
kids.push(p([b("Why the montage is blind here. "), t("The true active/passive signature is "), b("amplitude"), t(": an AP propagates without decrement, a VP decays with distance. In these recordings amplitude is dominated by electrode–tissue coupling, not by the biology. Venus’s asymmetric hook/stake montage yields far/near ratios scattered from 0.12 to 7.3 — frequently "), b("above 1"), t(", which no propagation mechanism explains but a montage artifact does. With amplitude unusable, only shape and timing remain, and both are compatible with a dispersed passive copy. This is the central methodological caution of the study, and it applies to any two-electrode surface montage of this kind.")]));
kids.push(...splitfig("venus_electrode_asymmetry.png", "The amplitude confound, made explicit: Venus’s far/near amplitude ratio is scattered and often > 1 (asymmetric electrodes), unlike the consistent decrement of symmetric-electrode plants. This is why amplitude — the true active/passive signature — cannot be used here."));
kids.push(p([b("What the timing does support. "), t("Two amplitude-independent observations remain solid and are worth reporting in their own right: peak−onset asymmetry (dispersion) is smallest in Venus/Mimosa and largest in the mints, and the delay scales linearly with distance (exponent ≈ 0.99), i.e. "), b("constant-velocity propagation rather than diffusion"), t(". Linear delay-vs-distance rules out a purely diffusive process; it does not by itself distinguish a regenerative wave from electrotonic spread along a cable.")]));
kids.push(...splitfig("peak_onset_asymmetry.png", "Peak−onset asymmetry (amplitude-independent): small = near-rigid translation, large = dispersion."));
kids.push(...splitfig("delay_vs_distance.png", "Delay vs distance: linear through ~origin (exponent ≈ 0.99) = constant-velocity propagation, not diffusion."));
kids.push(p([b("The simulations are illustrations, not findings. "), it("We state this plainly because the figures are easy to over-read. "), t("The cable-versus-FitzHugh–Nagumo panel is a textbook contrast between standard cable theory and a generic excitable medium, drawn to define the signatures we then looked for — it contains no data. The Hodgkin–Huxley-type plant AP model (Ca²⁺→Cl⁻→K⁺, no Na⁺) uses "), b("illustrative, not fitted, conductances"), t(" and is matched by eye to a single Venus waveform; reproducing a known shape from a pre-existing published model is a sanity check on our filtering, not evidence that any recorded far-electrode signal was regenerated. Neither simulation was fit across the dataset, and neither constitutes a result. They are retained as didactic/supplementary material.")]));
kids.push(...figure("cable_vs_fhn_sim.png", "ILLUSTRATIVE (no data): passive cable (decays and broadens with distance) vs FitzHugh–Nagumo active wave (constant amplitude and velocity). Drawn to define the signatures, not to fit the recordings."));
kids.push(...figure("venus_ap_model.png", "ILLUSTRATIVE (published model, illustrative conductances, matched by eye to one Venus AP): HH-type plant AP model (Ca²⁺→Cl⁻→K⁺). Left: V and Ca²⁺. Middle: all-or-none behaviour. Right: the band-passed model AP resembles a real Venus AP — a sanity check on the filter chain, not a fitted result."));
kids.push(p([b("A descriptive dispersion profile — deliberately not a mode prediction. "), t("Combining the amplitude-independent handles (dispersion, peak−onset asymmetry, waveform fidelity) orders the species from least to most dispersive. We present this ranking as a "), b("descriptive profile of the near→far transformation"), t(" only. It is reassuring that Venus and Mimosa sit at the low-dispersion end, but given the model comparison above we explicitly do "), b("not"), t(" convert this ordering into an “active” or “passive” verdict for any species. Section 9 lists the experiments that could.")]));
kids.push(...splitfig("predicted_propagation_mode.png", "Descriptive dispersion profile per species (score = dispersion + peak−onset asymmetry − waveform fidelity, z-scored). Low = the transformation is closest to rigid translation; high = most dispersive. NOT a propagation-mode classification — see the model comparison above."));

// ============ PART 5 ============
kids.push(pageBreak());
kids.push(h1("Grouping by all parameters: is propagation phylogenetically structured?"));
kids.push(p([t("Finally we group species using every parameter found along the way — CV, attenuation, broadening, waveform fidelity, dispersion σ, and short-duration fraction. If signal transmission were phylogenetically constrained, congeners and same-family species would cluster. They do "), b("not"), t(".")]));
kids.push(...splitfig("parameter_clustermap.png", "Species clustered by all propagation parameters (label colour = family). Families are scattered across the tree — no phylogenetic structure. Venus flytrap and Sensitive Mimosa cluster together as the two fast, low-dispersion movers."));
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
kids.push(p([b("Limitations, stated plainly. "), t("(i) "), b("Amplitude is unusable"), t(", and amplitude is the true active/passive signature. Far/near ratios are dominated by electrode–tissue coupling rather than biology — Venus’s asymmetric montage gives ratios from 0.12 to 7.3, frequently above 1, which propagation cannot explain. (ii) Consequently "), b("this montage cannot distinguish a regenerative action potential from electrotonic spread"), t(": a passive model out-fits an active one in 176/176 recordings, including in Venus flytrap and Mimosa where APs are certain. No propagation-mode claim — for any species — should be drawn from these data. (iii) The "), b("~0.2 Hz high-pass removes the sustained DC plateau that defines a variation potential"), t(", so measured durations are lower bounds and cannot be used to type signals mechanistically. (iv) Signal type was set by our "), b("single flame (wounding) stimulus"), t("; we never applied a non-damaging stimulus, so we sample one arm of the AP/VP dichotomy only. (v) Species labels come from the recording metadata; ten of the thirteen species have "), b("no propagating electrical signal demonstrated in the primary literature"), t(" at all, so our recordings describe a wound response without independently establishing its class. None of this affects the conduction velocities, the near→far transformation metrics, or the phylogeny result, which rest on timing and shape rather than amplitude or signal type.")]));
kids.push(table(
  ["Open question", "Minimal new experiment"],
  [
    ["Active vs passive propagation (unresolvable here)", "Bipolar/differential montage with matched, symmetric electrodes so far/near amplitude reports decrement rather than coupling"],
    ["True AP vs VP identity of the flame response", "Paired stimuli in the same plant: non-damaging (touch/cold) vs flame, DC-coupled amplifier (no 0.2 Hz high-pass) to retain the VP plateau"],
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
kids.push(p([b("Headline figures — the defensible results: "), t("(1) CV by species (Fig. 1) — the comparative dataset, thirteen species on low-cost two-channel hardware; (2) validation against the manual analysis (Fig. 2) — the automatic pipeline reproduces hand measurement at r = 0.94; (3) the near→far transformation (Fig. 10) — attenuation ≈ 0.44, broadening ≈ 1.31, shape preserved ≈ 0.80, the passive electrotonic signature; (4) the all-parameter clustering / phylogeny null (Fig. 34) — propagation profile is not phylogenetically structured, and Solanaceae are not internally more similar.")]));
kids.push(p([b("Recommended as a fifth headline — the honest negative result: "), t("the amplitude confound (Fig. 31) together with the model comparison (Fig. 16). That two surface electrodes cannot adjudicate active versus passive propagation — demonstrated by the passive model out-fitting the active one even in Venus flytrap — is a genuine methodological contribution for the low-cost/citizen-science electrophysiology community, and more useful than a mode prediction we cannot support.")]));
kids.push(p([b("Supporting / diagnostic: "), t("delay validation and estimator bakeoff (Figs. 3–4); the fast↔slow waveform axis (Fig. 5, to be presented with its four failure tests, not as an AP/VP classification); shared-reference raw traces (Fig. 6); the self-aligned near/far matrix (Fig. 7); attenuation–broadening (Fig. 13); example model fits (Fig. 19); the amplitude-independent discriminators (Figs. 20, 23); and the descriptive dispersion profile (Fig. 28). The short- and long-duration companion panels (Figs. 8–9, 11–12, 14–15, 17–18, 21–22, 24–25, 29–30, 32–33, 35–36) show each result holds within each waveform subset.")]));
kids.push(p([b("Supplementary / didactic only: "), t("the cable-vs-FitzHugh–Nagumo concept panel (Fig. 26) and the HH-type Venus AP model (Fig. 27). Both are illustrations — no data are fit in either — and must be captioned as such so they are not read as evidence of propagation mode.")]));
kids.push(p([it("Removed or demoted in revision: the amplitude (gain = 1) model fit (uninterpretable — confounded by electrode coupling); the per-species active/passive prediction (withdrawn — the test fails on Venus and Mimosa, where APs are certain); the claim that all species fire both APs and VPs (withdrawn — see Section 4); a Cannabis-only distance–delay scatter; near-aligned overlays that smeared the far channel; and the gain-vs-dispersion “space”.")]));

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
