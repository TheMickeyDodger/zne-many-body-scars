"""Load a cell's raw shot record from a bundle into the count tensor the estimator consumes."""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

SCALES = (1.0, 1.25, 1.5, 1.75, 2.0)
SEEDS = tuple(range(1000, 1008))


def load_cell_counts(bundle: Path, cell_index: int, L: int, n_steps: int = 48):
    """counts[n, k, j, 2^L], shots[n, k, j], lambda_r[n, k, j] for one cell."""
    counts = np.zeros((n_steps, 8, 5, 2**L), dtype=np.int64)
    shots = np.zeros((n_steps, 8, 5), dtype=np.int64)
    seen = np.zeros((n_steps, 8, 5), dtype=bool)
    with open(bundle / "phase2b" / "raw_shots.csv") as f:
        for r in csv.DictReader(f):
            if int(r["cell_index"]) != cell_index:
                continue
            n, k, j = int(r["n"]) - 1, SEEDS.index(int(r["fold_seed"])), SCALES.index(float(r["lambda_nominal"]))
            counts[n, k, j, int(r["outcome"], 2)] += int(r["count"])
            shots[n, k, j] = int(r["shots_actual"]); seen[n, k, j] = True
    X = np.full((n_steps, 8, 5), np.nan)
    with open(bundle / "phase2b" / "folded_circuits.csv") as f:
        for r in csv.DictReader(f):
            if int(r["cell_index"]) != cell_index:
                continue
            X[int(r["n"]) - 1, SEEDS.index(int(r["fold_seed"])), SCALES.index(float(r["lambda_nominal"]))] = float(r["lambda_r"])
    return counts, shots, X, seen


def load_schedule(bundle: Path, L: int):
    rows = []
    with open(bundle / "phase2b" / "peak_schedule.csv") as f:
        for r in csv.DictReader(f):
            if int(r["L"]) == L and r["obs"] == "ZPI":
                rows.append({"n_ref": int(r["n_ref"]), "points": list(range(int(r["w_lo"]), int(r["w_hi"]) + 1)),
                             "flags": [x for x in r["flags"].split(";") if x], "timing_testable": bool(int(r["timing_testable"]))})
    return rows
