"""Extract inter-electrode distances from the 'Todo Data Resumen' spreadsheet
and cross-reference them to each recording -> data/distances.csv.

The spreadsheet has one sheet per species; each row keys a recording by
Fecha (date) + Documento (the HH.MM.SS in the WAV filename) and carries
Distancia (mm), plus the experimenters' own Tiempo (s) delay and velocity.

Matching is three-tier and every non-exact match is flagged for audit:
  1. exact    - date + clean HH.MM.SS time
  2. coerced  - Excel turned "HH.MM.SS" into a date; recover by matching the
                digit multiset against the WAV time, unique within that date
  3. order    - align remaining same-date recordings by chronological order

Validation (see scripts/validate_distances.py): the experimenters' Tiempo (s)
agrees with our independently measured inter-channel delay at Spearman ~0.8 for
both exact and order matches, confirming the cross-reference.

Usage:
    python scripts/extract_distances.py [XLSX_PATH]
"""
from __future__ import annotations

import os
import re
import sys
import csv
import datetime
from collections import defaultdict, Counter

import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
DEFAULT_XLSX = os.path.join(
    os.path.expanduser("~"), "Downloads",
    "Velocidad de conducción - Todo Data Resumen.xlsx")

SHEET2FOLDER = {
    "Menta": "Mint", "Ají Ornamental": "Ornamental Chile", "Albahaca": "Basil",
    "Ruda": "Ruda", "Callisia repens": "Creeping Inchplant", "Tomate": "Tomato",
    "Ají Chileno": "Chilean Chile", "Hierba Buena": "Hierbabuena",
    "Romero": "Rosemary", "Dólar": "Argentian Dollar", "Venus": "Venus Flytrap",
    "Mimosa": "Sensitive Mimosa", "Clandestine": "Marijuana",
}


def norm_date(v):
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, str):
        for f in ("%Y-%m-%d", "%m/%d/%y", "%m/%d/%Y"):
            try:
                return datetime.datetime.strptime(v.strip(), f).strftime("%Y-%m-%d")
            except ValueError:
                pass
    return None


def clean_time(v):
    if isinstance(v, str):
        m = re.match(r"^(\d{1,2})[.:](\d{2})[.:](\d{2})", v.strip())
        if m:
            return f"{int(m.group(1)):02d}.{m.group(2)}.{m.group(3)}"
    if isinstance(v, datetime.time):
        return f"{v.hour:02d}.{v.minute:02d}.{v.second:02d}"
    if isinstance(v, datetime.datetime) and (v.hour, v.minute, v.second) != (0, 0, 0):
        return f"{v.hour:02d}.{v.minute:02d}.{v.second:02d}"
    return None


def coerced_set(v):
    if isinstance(v, (datetime.datetime, datetime.date)):
        return tuple(sorted([v.year % 100, v.month, v.day]))
    return None


def time_set(t):
    h, m, s = t.split(".")
    return tuple(sorted([int(h), int(m), int(s)]))


def fnum(x):
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        try:
            return float(x.replace(",", "."))
        except ValueError:
            return None
    return None


def parse_sheets(xlsx):
    wb = openpyxl.load_workbook(xlsx, data_only=True)
    rows = []
    for sheet, folder in SHEET2FOLDER.items():
        ws = wb[sheet]
        raw = list(ws.iter_rows(values_only=True))
        hi = None
        for i, r in enumerate(raw):
            cells = [str(c).strip() if c is not None else "" for c in r]
            if "Documento" in cells and "Distancia (mm)" in cells:
                hi, header = i, cells
                break
        if hi is None:
            continue
        ci = {k: header.index(k) for k in
              ["Documento", "Distancia (mm)", "Fecha", "Tiempo (s)",
               "Velocidad (mm/s)"] if k in header}
        last = None
        for j, r in enumerate(raw[hi + 1:]):
            d = norm_date(r[ci["Fecha"]]) if "Fecha" in ci else None
            if d:
                last = d
            dist = fnum(r[ci["Distancia (mm)"]])
            if dist is None or last is None:
                continue
            rows.append(dict(
                folder=folder, date=last, ct=clean_time(r[ci["Documento"]]),
                cs=coerced_set(r[ci["Documento"]]), dist=dist, order=j,
                tiempo=fnum(r[ci["Tiempo (s)"]]) if "Tiempo (s)" in ci else None,
                vel=fnum(r[ci["Velocidad (mm/s)"]]) if "Velocidad (mm/s)" in ci else None))
    return rows


def list_wavs():
    out = []
    for sp in sorted(os.listdir(DATA)):
        d = os.path.join(DATA, sp)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".wav"):
                continue
            m = re.search(r"(\d{4}-\d{2}-\d{2})_(\d{2}\.\d{2}\.\d{2})", fn)
            if m:
                out.append((sp, m.group(1), m.group(2), os.path.splitext(fn)[0]))
    return out


def match(rows, wavs):
    exact, bydate = defaultdict(list), defaultdict(list)
    for r in rows:
        if r["ct"]:
            exact[(r["folder"], r["date"], r["ct"])].append(r)
        bydate[(r["folder"], r["date"])].append(r)
    used, out = set(), {}

    def take(r):
        used.add(id(r))
        return r

    for sp, dt, tm, name in wavs:                       # tier 1: exact
        hit = [r for r in exact.get((sp, dt, tm), []) if id(r) not in used]
        out[(sp, name)] = (take(hit[0]), "exact") if hit else (None, None)
    for sp, dt, tm, name in wavs:                       # tier 2: coerced digits
        if out[(sp, name)][0] is not None:
            continue
        cand = [r for r in bydate.get((sp, dt), [])
                if id(r) not in used and r["cs"] == time_set(tm)]
        if len(cand) == 1:
            out[(sp, name)] = (take(cand[0]), "coerced")
    rem = defaultdict(list)                              # tier 3: order
    for sp, dt, tm, name in wavs:
        if out[(sp, name)][0] is None:
            rem[(sp, dt)].append((tm, name))
    for key, lst in rem.items():
        cand = sorted([r for r in bydate.get(key, []) if id(r) not in used],
                      key=lambda r: r["order"])
        for (tm, name), r in zip(sorted(lst), cand):
            out[(key[0], name)] = (take(r), "order")
    return out


def main():
    xlsx = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_XLSX
    rows = parse_sheets(xlsx)
    wavs = list_wavs()
    out = match(rows, wavs)
    path = os.path.join(DATA, "distances.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["species", "recording", "distance_mm", "sheet_delay_s",
                    "sheet_cv_mm_s", "match_method"])
        for sp, dt, tm, name in wavs:
            r, meth = out[(sp, name)]
            if r:
                w.writerow([sp, name, r["dist"], r["tiempo"], r["vel"], meth])
            else:
                w.writerow([sp, name, "", "", "", "unmatched"])
    meths = Counter(v[1] or "unmatched" for v in out.values())
    got = sum(1 for v in out.values() if v[0])
    print(f"wrote {path}")
    print(f"matched {got}/{len(wavs)}  methods={dict(meths)}")


if __name__ == "__main__":
    main()
