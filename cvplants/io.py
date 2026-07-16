"""Loading BackyardBrains plant recordings and their event/metadata sidecars."""
from __future__ import annotations

import os
import re
import glob
import wave
from dataclasses import dataclass, field

import numpy as np

# Common (folder) name -> Latin name. Recovered from the CABG_Plantas library
# notebook and the hardcoded CV table. Entries marked "approx" are genus-level
# best guesses where the exact cultivar was not recorded.
SPECIES_LATIN = {
    "Argentian Dollar":   "Plectranthus verticillatus",   # money/dollar plant (approx)
    "Basil":              "Ocimum basilicum",
    "Chilean Chile":      "Capsicum annuum",               # approx
    "Creeping Inchplant": "Callisia repens",
    "Hierbabuena":        "Mentha spicata",                # spearmint
    "Marijuana":          "Cannabis sativa",
    "Mint":               "Mentha x piperita",             # approx
    "Ornamental Chile":   "Capsicum annuum",
    "Rosemary":           "Salvia rosmarinus",
    "Ruda":               "Ruta graveolens",
    "Sensitive Mimosa":   "Mimosa pudica",
    "Tomato":             "Solanum lycopersicum",
    "Venus Flytrap":      "Dionaea muscipula",
}


@dataclass
class Recording:
    """One two-channel recording plus its markers and metadata."""
    path: str
    species: str
    latin: str
    data: np.ndarray        # shape (n_samples, n_channels), float
    fs: float               # sampling rate (Hz)
    events: list            # list of (marker_id, time_s)
    distance_mm: float | None  # inter-electrode distance if encoded in filename
    name: str = field(init=False)

    def __post_init__(self):
        self.name = os.path.splitext(os.path.basename(self.path))[0]

    @property
    def n_channels(self) -> int:
        return self.data.shape[1]

    @property
    def duration_s(self) -> float:
        return self.data.shape[0] / self.fs

    @property
    def stim_start(self) -> float | None:
        return self.events[0][1] if len(self.events) >= 1 else None

    @property
    def stim_stop(self) -> float | None:
        return self.events[1][1] if len(self.events) >= 2 else None


def parse_distance_mm(path: str) -> float | None:
    """Extract inter-electrode distance from a filename like '...-28.8mm.wav'."""
    m = re.search(r"[-_](\d+(?:\.\d+)?)\s*mm", os.path.basename(path), re.IGNORECASE)
    return float(m.group(1)) if m else None


def parse_events(wav_path: str) -> list:
    """Read the '<name>-events.txt' sidecar -> list of (marker_id, time_s).

    Tolerates missing files (returns []) and the BackyardBrains
    'ID,<tab> time' format with '#'-prefixed comment lines.
    """
    stem = wav_path[:-4] if wav_path.lower().endswith(".wav") else wav_path
    candidates = [stem + "-events.txt"]
    # fall back to any sidecar that shares the stem (guards odd suffixes)
    candidates += glob.glob(stem + "*events.txt")
    events = []
    for cand in candidates:
        if not os.path.exists(cand):
            continue
        with open(cand, "r", errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.replace("\t", " ").split(",")
                if len(parts) < 2:
                    continue
                try:
                    events.append((parts[0].strip(), float(parts[1])))
                except ValueError:
                    continue
        break
    events.sort(key=lambda e: e[1])
    return events


def load_recording(path: str, species: str | None = None) -> Recording:
    """Load a WAV recording into a Recording object (channels as float columns)."""
    with wave.open(path, "rb") as w:
        n, sr, ch, width = (w.getnframes(), w.getframerate(),
                            w.getnchannels(), w.getsampwidth())
        raw = w.readframes(n)
    dtype = {1: np.int8, 2: np.int16, 4: np.int32}[width]
    data = np.frombuffer(raw, dtype=dtype).reshape(-1, ch).astype(float)
    if species is None:
        # infer from parent directory name
        species = os.path.basename(os.path.dirname(path))
    return Recording(
        path=path,
        species=species,
        latin=SPECIES_LATIN.get(species, species),
        data=data,
        fs=float(sr),
        events=parse_events(path),
        distance_mm=parse_distance_mm(path),
    )


def iter_dataset(data_dir: str):
    """Yield Recording objects for every WAV under data_dir/<species>/*.wav."""
    for species in sorted(os.listdir(data_dir)):
        sp_dir = os.path.join(data_dir, species)
        if not os.path.isdir(sp_dir):
            continue
        for wav in sorted(glob.glob(os.path.join(sp_dir, "*.wav"))):
            yield load_recording(wav, species=species)
