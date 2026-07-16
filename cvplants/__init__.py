"""cvplants - conduction velocity analysis for two-channel plant electrophysiology.

Data: BackyardBrains Plant SpikerBox recordings (2-channel WAV, ~5 kHz, int16)
of slow propagating wound / variation potentials. Two recording electrodes are
placed inline downstream of a stimulation site; the propagating potential reaches
the near electrode first and the far electrode later. Conduction velocity is the
inter-electrode distance divided by the inter-channel arrival delay.

Stimulation is bracketed by two event markers (start / stop) in the -events.txt
sidecar; the response is analysed in the post-stimulus window.
"""
from .io import (
    load_recording, parse_events, parse_distance_mm, iter_dataset,
    Recording, SPECIES_LATIN,
)
from .analysis import analyze_recording
from .batch import build_results

__all__ = [
    "load_recording", "parse_events", "parse_distance_mm", "iter_dataset",
    "Recording", "SPECIES_LATIN", "analyze_recording", "build_results",
]
