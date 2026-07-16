# Conduction velocity in plants — two-channel deep dive

Analysis of propagating electrical signals (wound / variation potentials) in
plants, recorded with a two-electrode BackyardBrains Plant SpikerBox. The
central question: **how does the signal change as it travels from the near
electrode (channel 1) to the far electrode (channel 2)**, and what conduction
velocity does that imply.

## Experiment

- A stimulus (wound / touch / flame) is applied at one site on the plant.
- Two recording electrodes sit **inline downstream** of the stimulus at
  different distances. The propagating potential reaches the **near** electrode
  first and the **far** electrode later.
- Recordings are 2-channel WAV, **5 kHz**, 16-bit (`data/<species>/*.wav`).
- The `<name>-events.txt` sidecar holds two markers that bracket the
  **stimulation window** (start / stop) — they are *not* the electrode arrival
  times. The response is analysed in the post-stimulus window.
- Where the inter-electrode distance was recorded it is encoded in the filename
  (e.g. `...-28.8mm.wav`). This is present for all *Cannabis* recordings and a
  few *Venus flytrap* recordings; other species carry the waveform-transformation
  measurements but need a distance to convert a delay into an absolute velocity.

Conduction velocity is

```
CV = inter-electrode distance / (arrival delay from near to far electrode)
```

The arrival delay is measured from the two response **waveforms**, not from the
stimulation markers.

## What the pipeline measures

For every recording (`cvplants/analysis.py`):

| quantity | meaning |
|---|---|
| `xcorr_delay_s` | near→far delay from windowed cross-correlation (primary) |
| `peak_delay_s`, `onset_delay_s` | independent cross-checks on the delay |
| `cv_xcorr_mm_s`, `cv_peak_mm_s` | conduction velocity (needs known distance) |
| `attenuation_far_near` | far-peak / near-peak amplitude — decrement with distance |
| `broadening_far_near` | far / near FWHM — temporal dispersion of the wavefront |
| `rise_ratio_far_near` | far / near rise time |
| `xcorr_corr` | max normalised cross-correlation — how well the shape is preserved |
| `near_snr`, `far_snr` | peak amplitude / pre-stimulus noise |
| `valid`, `flags` | quality gate (see below) |

**Delay** is estimated two independent ways — a windowed cross-correlation of
the whole response and a peak-to-peak time difference — so they validate each
other. On the *Cannabis* set the two agree closely, which is the evidence that
the automatic delay is trustworthy.

**Quality gating.** A recording is marked invalid (and excluded from the CV /
transformation summaries) if any of:
- `near_synchronous` — peaks < 0.2 s apart (no measurable propagation; likely a
  shared stimulus artifact),
- `low_waveform_similarity` — cross-correlation < 0.4 (the two channels are not
  seeing the same event),
- `low_snr` — response peak < 3× pre-stimulus noise.

## Key findings

From `results/` over 176 recordings (165 valid):

- **The signal attenuates with distance.** Far/near amplitude ratio has a
  median of ~0.44 — the potential loses roughly half its amplitude between
  electrodes (decremental conduction), consistent with variation potentials.
- **The wavefront broadens.** Far/near FWHM median ~1.31 — the far waveform is
  ~30% wider, i.e. the wave disperses as it travels.
- **The shape is largely preserved.** Waveform cross-correlation median ~0.80,
  so the two channels record recognisably the same event with a lag.
- **Conduction velocity (where distance is known):** *Cannabis sativa* median
  ~6 mm/s per recording (aggregate distance-vs-delay slope ~3 mm/s; the two
  differ because per-recording CV is highly variable and distance alone does not
  predict the delay within this plant). *Dionaea muscipula* (Venus flytrap)
  shows shorter delays / higher and more variable velocities — its signals are
  fast action potentials rather than slow variation potentials, so treat those
  numbers as a different signal class.

These velocities sit in the same 1–40 mm/s range as the earlier hand-measured
values for these species.

## Layout

```
cvplants/
  io.py            load WAV + events + distance; species→Latin map
  preprocessing.py baseline subtraction and low-pass (slow potentials, <2 Hz)
  analysis.py      event detection, delay, CV, transformation metrics, gating
  batch.py         walk the dataset → results table + per-species summary
  viz.py           per-recording, per-species and summary figures
  phylo.py         comparative analysis: functional profiles, clustering,
                   Mantel test vs taxonomy, cross-variable correlations
scripts/run_all.py     end-to-end: writes results/*.csv and results/figures/*.png
scripts/comparative.py taxonomy analysis -> stats + comparative figures (REPORT.md)
notebooks/conduction_velocity_deep_dive.ipynb   narrative walk-through
REPORT.md          does signal transformation track evolutionary relationship?
data/<species>/   recordings (WAV + events.txt); manifest.csv is committed
results/          recordings.csv, species_summary.csv, figures/
```

## Run

```bash
pip install -r requirements.txt
# place the FigShare recordings under data/<species>/  (see data/manifest.csv)
python scripts/run_all.py            # --data / --out / --cutoff to override
```

## Notes & limitations

- Amplitudes are in raw ADC units (a.u.); channel-to-channel ratios and timing
  are unaffected, but absolute microvolt calibration would need the SpikerBox
  gain.
- Absolute CV requires the inter-electrode distance; add it to filenames as
  `-<mm>mm` (or extend `cvplants.io.parse_distance_mm`) to unlock CV for the
  remaining species.
- *Sensitive Mimosa* recordings have no event markers and *Venus flytrap* mostly
  one; for those the response window falls back to the whole trace after a short
  settling period.
