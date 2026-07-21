# This pipeline vs the manual analysis (the paper)

Compared against **Contreras, Morales, Rojas, Serbe-Kamp & Marzullo,
"Electrical Conduction Velocity Across Species of Rapid Movement and Non-Rapid
Movement Plants"** (Plant Signaling & Behavior), Table 1 / Figures 1 & 3.

The paper's **accepted-recording counts match this repo's WAV files
species-by-species** (176 total), so the "Selected" folder *is* their accepted
set and we are analysing the same recordings. They report a per-species CV
**mean**; comparison is mean-to-mean on the resolved-delay subset
(`scripts/compare_to_paper.py`).

## Headline: strong agreement

- **Pearson r = 0.94 across all 13 species; r = 0.98 excluding Sensitive Mimosa**
  (`compare_to_paper_scatter.png`, `compare_to_paper_bars.png`). Almost every
  species sits on the identity line within error bars.
- **Rapid vs non-rapid separation reproduced.** Non-rapid group mean:
  **mine 8.0 ± 6.3 mm/s vs paper 7.7 ± 6.5** — essentially identical. Venus
  flytrap: **mine ~30 vs paper 35.3**.

| species | paper mean | mine (resolved) |   | species | paper mean | mine (resolved) |
|---|---|---|---|---|---|---|
| Argentian Dollar | 4.8 | 4.4 | | Ornamental Chile | 6.4 | 6.5 |
| Mint | 5.1 | 4.6 | | Rosemary | 6.6 | 6.1 |
| Tomato | 7.0 | 8.6 | | Basil | 7.4 | 10.1 |
| Creeping Inchplant | 7.4 | 8.0 | | Marijuana | 8.3 | 7.6 |
| Hierbabuena | 9.4 | 8.0 | | Ruda | 10.0 | 11.3 |
| Chilean Chile | 11.9 | 12.9 | | Venus flytrap | 35.3 | 29.7 |
| **Sensitive Mimosa** | **32.4** | **18.9** | | | | |

(My earlier per-species medians ran lower than these means because CV is
right-skewed; the paper reports means, so mean-to-mean is the fair comparison.)

## The one real discrepancy: Sensitive Mimosa (paper 32.4, mine 18.9)

Not a disagreement in principle — a **detector limitation on fast, small-delay
events**. Comparing my delay to the spreadsheet's own manual delay (Tiempo)
recording-by-recording:

- On most Mimosa recordings my delay matches theirs closely (1.01 vs 1.04,
  0.94 vs 0.94, 0.69 vs 0.64, 0.44 vs 0.48 …) — and there the CV matches.
- On ~5 *fast* recordings (their delay ~0.2–0.4 s, CV 40–75 mm/s) my
  cross-correlation/peak detector locks onto a **slower secondary feature**
  (e.g. one recording: my 12.3 s vs their 0.37 s → my CV 0.8 vs their 25). Those
  failures, plus three I flagged unresolved, pull my Mimosa mean down.

Mimosa was tactile-stimulated and fires a sharp, fast AP with a small
inter-electrode delay; my detector, tuned for the broad slow potentials of the
other species, mis-picks it. **Fix:** a fast-event-aware delay (sharp-onset /
first-derivative peak, or a narrower analysis window around the initial
deflection) would recover the small delay and bring Mimosa in line — the machinery
already exists in the 2-tap fit. Venus is largely unaffected because its spike is
even sharper and its delay slightly larger.

## Metadata corrected from the paper

- **Hierbabuena = *Clinopodium douglasii*** (not *Mentha spicata*). So Mint and
  Hierbabuena are same-family (Lamiaceae) but **different genera** — the earlier
  "two *Mentha* congeners" statement was wrong and is removed. The only true
  congeners are the two chiles (*Capsicum baccatum* vs *C. annuum*), which
  diverge — reinforcing the "not phylogenetic" conclusion.
- **Chilean Chile = *Capsicum baccatum***, Argentian Dollar = *Plectranthus
  purpuratus*, Mint = *Mentha spicata* (`cvplants/io.py` updated).
- **Amplifier = 0.2–130 Hz, gain ~55×, 10 kHz** (prototype; some final runs on a
  0.1–20000 Hz "SpikeStation"), not a 0.07–8.8 Hz SpikerBox. The 130 Hz upper
  cutoff preserves waveform shape, so the earlier shape-smearing caveat is
  withdrawn (`docs/active_vs_passive.md`).
- The shared **soil ground** (map pin in the moist pot) is confirmed in the paper
  — consistent with the expected common-mode discussed in §0b there.

## What this pipeline adds beyond the manual analysis

The paper reports CV and the rapid/non-rapid difference and leaves active-vs-
passive open. This pipeline reproduces the CV (r=0.94) and adds, on the same
recordings: the **near→far signal transformation** (attenuation, dispersion,
waveform fidelity), a **comparative/phylogenetic test** (CV/shape are convergent,
not inherited), **active-vs-passive discriminators + a common-mode-robust delay**,
an **ion-channel synthesis**, and **forward simulations** (cable vs FitzHugh–
Nagumo) that predict individual far traces.
