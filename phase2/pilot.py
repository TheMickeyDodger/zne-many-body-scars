"""Stage 1 micro-pilot acquisition into the labelled bundle root results/phase2-pilot.

Writes contract-format raw rows (B-FOLD, B-RAWDM, B-RAWSHOT, B-REF, B-SCHED, B-CELLLOG) for a
declared subset of cells and steps, plus per-execution timings. This bundle is a measurement
artefact only: its raw data are never carried into the final bundle.
"""
from __future__ import annotations

import csv
import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
PILOT_ROOT = REPO / "results" / "phase2-pilot"
SCALES = (1.0, 1.25, 1.5, 1.75, 2.0)
SEEDS = tuple(range(1000, 1008))
SHOTS = 8192
RAW = ("ZPI", "PRET", "M_I", "M_J", "M_IJ")


def guard_root(root: Path) -> None:
    r = root.resolve()
    if r.name.lower() == "minimal" or "figures" == r.parent.name.lower() or str(r).lower().startswith(str((REPO / "figures").resolve()).lower()):
        raise SystemExit(3)
    if not str(r).startswith(str((REPO / "results").resolve())):
        raise SystemExit(3)


def work_unit(args):
    """One (L, folding, n): fold once per (seed, lambda), execute for every cell in the group."""
    L, folding, n, cells = args  # cells: list of (cell dict, want_dm, want_shot)
    sys.path.insert(0, str(REPO))
    from phase2 import circuits as C, noise as N, simulate as S
    from phase2.observables import values_from_probabilities, weight_matrix
    from phase2.contract import seed_simulator
    W = weight_matrix(L)
    t0 = time.perf_counter()
    base = C.base_circuit(L, n)
    t_base = time.perf_counter() - t0
    folded, fold_rows, t_fold = {}, [], []
    for k, seed in enumerate(SEEDS):
        for j, lam in enumerate(SCALES):
            t0 = time.perf_counter()
            fc = C.fold(base, folding, lam, seed)
            t_fold.append((lam, time.perf_counter() - t0))
            folded[(k, j)] = fc
            lr, lr1 = C.realized_scales(base, fc)
            ops = C.op_counts(fc)
            fold_rows.append({"n": n, "fold_seed": seed, "lambda_nominal": lam, "lambda_r": lr, "lambda_r_1q": lr1,
                              "cx": ops.get("cx", 0), "sx": ops.get("sx", 0), "sxdg": ops.get("sxdg", 0),
                              "x": ops.get("x", 0), "rz": ops.get("rz", 0), "n_ops": sum(ops.values())})
    dm_rows, shot_rows, timings = [], [], []
    for cell, want_dm, want_shot in cells:
        ci = cell["cell_index"]
        model, kappa, p1, p2 = cell["noise_model"], cell["kappa"], cell["p1"], cell["p2"]
        if want_dm:
            nm, ro = N.model_for(model, kappa, "DM", p1, p2)
            t0 = time.perf_counter(); p = S.dm_probabilities(base, nm); dt = time.perf_counter() - t0
            if ro is not None:
                p = N.classical_readout_transform(L, ro) @ p
            timings.append(("DM", L, folding, model, kappa, 1.0, -1, n, dt))
            for q, v in zip(RAW, values_from_probabilities(p, W)):
                dm_rows.append({"cell_index": ci, "n": n, "fold_seed": -1, "lambda_nominal": 1.0, "obs": q, "value": float(v)})
            for k, seed in enumerate(SEEDS):
                for j, lam in enumerate(SCALES):
                    t0 = time.perf_counter(); p = S.dm_probabilities(folded[(k, j)], nm); dt = time.perf_counter() - t0
                    if ro is not None:
                        p = N.classical_readout_transform(L, ro) @ p
                    timings.append(("DM", L, folding, model, kappa, lam, seed, n, dt))
                    for q, v in zip(RAW, values_from_probabilities(p, W)):
                        dm_rows.append({"cell_index": ci, "n": n, "fold_seed": seed, "lambda_nominal": lam, "obs": q, "value": float(v)})
        if want_shot:
            nm, _ = N.model_for(model, kappa, "SHOT", p1, p2)
            for k, seed in enumerate(SEEDS):
                for j, lam in enumerate(SCALES):
                    ss = seed_simulator(ci, n, k, j)
                    t0 = time.perf_counter(); vec, actual, used = S.shot_counts(folded[(k, j)], nm, ss, SHOTS, method="density_matrix"); dt = time.perf_counter() - t0
                    timings.append(("SHOT", L, folding, model, kappa, lam, seed, n, dt))
                    for idx in np.nonzero(vec)[0]:
                        shot_rows.append({"cell_index": ci, "n": n, "fold_seed": seed, "lambda_nominal": lam, "seed_simulator": ss,
                                          "shots_requested": SHOTS, "shots_actual": actual,
                                          "outcome": format(int(idx), f"0{L}b"), "count": int(vec[idx])})
    return {"L": L, "folding": folding, "n": n, "t_base": t_base, "t_fold": t_fold, "fold_rows": fold_rows,
            "dm_rows": dm_rows, "shot_rows": shot_rows, "timings": timings, "pid": os.getpid()}


def write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main(argv=None):
    import argparse
    from phase2.contract import load, cells_by_index
    from phase2 import references as R
    from phase2.observables import weight_matrix
    from phase2.identity import environment_record, write_json
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, help="JSON: list of {cell_index, steps: [...] , dm: bool, shot: bool}")
    ap.add_argument("--out", default=str(PILOT_ROOT))
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args(argv)
    root = Path(a.out); guard_root(root)
    plan = json.loads(Path(a.plan).read_text())
    c = load(); cells = cells_by_index(c)
    (root / "phase2b").mkdir(parents=True, exist_ok=True)
    write_json(root / "environment_phase2.json", environment_record())
    # references and schedule (noiseless, before any noisy value)
    ref_rows, sched_rows, sched = [], [], {}
    from phase2.estimators import find_peaks, windows, POLARITY
    t_ref = {}
    for L in sorted({cells[p["cell_index"]]["L"] for p in plan}):
        t0 = time.perf_counter(); e0 = R.e0_curve(L, 48); t_ref[f"e0_L{L}"] = time.perf_counter() - t0
        t0 = time.perf_counter(); ed, resid, orth = R.ed_curve(L, 48); t_ref[f"ed_L{L}"] = time.perf_counter() - t0
        t_ref[f"ed_residual_L{L}"] = resid; t_ref[f"ed_orth_defect_L{L}"] = orth
        for n in range(1, 49):
            for qi, q in enumerate(RAW):
                ref_rows.append({"L": L, "state": "Z2", "n": n, "obs": q, "e_ed": float(ed[n - 1, qi]), "e0_sv": float(e0[n - 1, qi])})
        zpi = np.concatenate([[np.nan], POLARITY["ZPI"] * e0[:, 0]])
        peaks = find_peaks(zpi)
        sched[L] = windows(peaks)
        for k, w in enumerate(sched[L], start=1):
            sched_rows.append({"L": L, "state": "Z2", "obs": "ZPI", "k": k, "n_ref": w["n_ref"], "w_lo": w["points"][0], "w_hi": w["points"][-1],
                               "timing_testable": int(w["timing_testable"]), "flags": ";".join(w["flags"])})
    write_csv(root / "phase2b" / "reference_curves.csv", ref_rows, ["L", "state", "n", "obs", "e_ed", "e0_sv"])
    write_csv(root / "phase2b" / "peak_schedule.csv", sched_rows, ["L", "state", "obs", "k", "n_ref", "w_lo", "w_hi", "timing_testable", "flags"])
    # work units grouped by (L, folding, n)
    groups = {}
    for p in plan:
        cell = cells[p["cell_index"]]
        for n in p["steps"]:
            key = (cell["L"], cell["folding"], n)
            groups.setdefault(key, []).append((cell, bool(p["dm"]), bool(p["shot"])))
    units = [(L, f, n, cs) for (L, f, n), cs in groups.items()]
    units.sort(key=lambda u: (-u[0], u[2]))
    fold_rows, dm_rows, shot_rows, timings, fold_t, base_t = [], [], [], [], [], []
    t_start = time.perf_counter()
    ctx = mp.get_context("spawn")
    with ctx.Pool(a.workers) as pool:
        for res in pool.imap_unordered(work_unit, units):
            L, f, n = res["L"], res["folding"], res["n"]
            for cell, _, _ in groups[(L, f, n)]:
                for r in res["fold_rows"]:
                    fold_rows.append({"cell_index": cell["cell_index"], **r})
            dm_rows += res["dm_rows"]; shot_rows += res["shot_rows"]; timings += res["timings"]
            fold_t += [(L, f, lam, t) for lam, t in res["t_fold"]]; base_t.append((L, n, res["t_base"]))
            print(f"done L={L} {f} n={n} shots_rows={len(res['shot_rows'])}", flush=True)
    wall = time.perf_counter() - t_start
    key = lambda r: (r["cell_index"], r["n"], r["fold_seed"], r["lambda_nominal"])
    fold_rows.sort(key=key); dm_rows.sort(key=lambda r: key(r) + (RAW.index(r["obs"]),)); shot_rows.sort(key=lambda r: key(r) + (r["outcome"],))
    write_csv(root / "phase2b" / "folded_circuits.csv", fold_rows, ["cell_index", "n", "fold_seed", "lambda_nominal", "lambda_r", "lambda_r_1q", "cx", "sx", "sxdg", "x", "rz", "n_ops"])
    write_csv(root / "phase2b" / "raw_dm.csv", dm_rows, ["cell_index", "n", "fold_seed", "lambda_nominal", "obs", "value"])
    write_csv(root / "phase2b" / "raw_shots.csv", shot_rows, ["cell_index", "n", "fold_seed", "lambda_nominal", "seed_simulator", "shots_requested", "shots_actual", "outcome", "count"])
    log = []
    for p in plan:
        log.append({"cell_index": p["cell_index"], "status": "pilot_partial" if len(p["steps"]) < 48 else "pilot_full",
                    "executions_dm": 41 * len(p["steps"]) if p["dm"] else 0, "executions_shot": 40 * len(p["steps"]) if p["shot"] else 0, "steps": len(p["steps"])})
    write_csv(root / "phase2b" / "cell_log.csv", log, ["cell_index", "status", "executions_dm", "executions_shot", "steps"])
    write_json(root / "pilot_timings.json", {"wall_seconds_acquisition": wall, "workers": a.workers, "n_units": len(units),
                                            "timings": timings, "fold_timings": fold_t, "base_timings": base_t, "reference_timings": t_ref,
                                            "rows": {"fold": len(fold_rows), "dm": len(dm_rows), "shot": len(shot_rows)}})
    (root / "deviations.md").write_text("DEVIATIONS: NONE\n\nPilot measurement bundle (stage 1B); not a contracted result bundle.\n")
    print(f"acquisition wall {wall:.1f}s; rows fold={len(fold_rows)} dm={len(dm_rows)} shot={len(shot_rows)}")


if __name__ == "__main__":
    main()
