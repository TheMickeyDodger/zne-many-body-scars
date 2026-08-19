#!/usr/bin/env python
"""Execute the minimal experiment of docs/design.md §15 EXACTLY.

Orchestration only: every physical/statistical definition lives in src/zne_scars/.
Outputs are deterministic (no timestamps, no absolute paths); wall-clock timing
goes to stdout only. Run:  .venv/bin/python scripts/run_minimal.py [--out DIR]

Writing into either frozen canonical directory (results/minimal/ or figures/) is
refused — adding files included — unless --allow-canonical-overwrite is passed
explicitly; the default --out is a fresh reproduction directory. The shared
guard lives in scripts/_canonical_guard.py.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
import time
from importlib.metadata import distributions
from pathlib import Path

import numpy as np

from _canonical_guard import CANONICAL_RESULTS, resolve_out_dir

from zne_scars.executors import (
    SHOTS_DEFAULT,
    make_density_matrix_executor,
    shot_expectation,
    statevector_expectation,
)
from zne_scars.hamiltonian import OMEGA_DEFAULT, V_DEFAULT, continuous_time_expectation
from zne_scars.metrics import (
    DELTA_DENSITY_MATRIX,
    DELTA_SHOT,
    EPS_MIN,
    abs_error,
    experiment_verdict,
    global_improvement_factor,
    improvement_factor,
    is_reportable,
    majority_outcome,
    rms,
    seed_band,
    shot_baseline,
)
from zne_scars.noise import NoiseConfig
from zne_scars.observables import staggered_magnetization_density_op, z_pi_matrix
from zne_scars.trotter import (
    BASIS_GATES,
    DT_DEFAULT,
    SEED_TRANSPILER,
    build_circuit,
    transpile_to_basis,
)
from zne_scars.zne_runner import (
    FIDELITIES,
    FOLD_SEEDS,
    SCALE_FACTORS,
    fold_two_qubit,
    linear_intercept,
    run_seed_arms,
    secondary_ensemble,
)

L = 6
N_MAX = 40


def shot_seed(n: int, seed_index: int, scale_index: int) -> int:
    """design §16: seed_simulator = 9000 + 100*n + 10*k + j."""
    return 9000 + 100 * n + 10 * seed_index + scale_index


def fmt(x: float) -> str:
    """Shortest round-trip float representation: deterministic and lossless."""
    return repr(float(x))


def fmt_opt(x: float | None) -> str:
    """As fmt, but a failed/invalid value (None) is recorded as an empty field."""
    return "" if x is None else fmt(x)


def source_tree_hash() -> str:
    """Immutable source identifier: sha256 over the sorted relative paths and
    contents of src/, scripts/, pyproject.toml, requirements.txt. A content
    hash, NOT a VCS revision — it identifies the exact source that produced a
    run independent of version-control state."""
    root = Path(__file__).resolve().parent.parent
    files = sorted(
        [*root.glob("src/**/*.py"), *root.glob("scripts/*.py"),
         root / "pyproject.toml", root / "requirements.txt"]
    )
    digest = hashlib.sha256()
    for path in files:
        digest.update(str(path.relative_to(root)).encode() + b"\0")
        digest.update(path.read_bytes() + b"\0")
    return digest.hexdigest()


# Emitted verbatim into environment.json; tools/verify_reproduction.py validates
# recorded values against this constant, so keep it importable as a constant.
SOURCE_IDENTIFIER_NOTE = (
    "content hash over sorted src/**/*.py, scripts/*.py, pyproject.toml, "
    "requirements.txt — not a VCS revision; identifies the exact source "
    "that produced this run independent of version-control state"
)


def environment_record() -> dict:
    packages = dict(
        sorted((dist.metadata["Name"], dist.version) for dist in distributions())
    )
    try:
        blas = np.show_config(mode="dicts")["Build Dependencies"]["blas"]
        blas_info = {k: str(blas.get(k, "")) for k in ("name", "version")}
    except Exception:  # pragma: no cover - introspection best-effort
        blas_info = {"name": "unavailable", "version": "unavailable"}
    return {
        "design_section": "docs/design.md §15",
        "parameters": {
            "L": L, "V": V_DEFAULT, "Omega": OMEGA_DEFAULT, "dt": DT_DEFAULT,
            "n_steps": list(range(1, N_MAX + 1)),
            "basis_gates": list(BASIS_GATES), "optimization_level": 0,
            "seed_transpiler": SEED_TRANSPILER,
            "noise": {"p1": NoiseConfig().p1, "p2": NoiseConfig().p2,
                      "one_qubit_gates": ["sx", "sxdg", "x"], "two_qubit_gates": ["cx"],
                      "clean_gates": ["rz"]},
            "scale_factors": list(SCALE_FACTORS),
            "fold_seeds": list(FOLD_SEEDS),
            "fidelities": FIDELITIES,
            "shots": SHOTS_DEFAULT,
            "seed_simulator_formula": "9000 + 100*n + 10*seed_index + scale_index",
            "eps_min": EPS_MIN,
            "delta_density_matrix": DELTA_DENSITY_MATRIX,
            "delta_shot": DELTA_SHOT,
        },
        "versions": {"python": platform.python_version(), "packages": packages},
        "source_tree_sha256": source_tree_hash(),
        "source_identifier_note": SOURCE_IDENTIFIER_NOTE,
        "platform": {"system": platform.system(), "machine": platform.machine(),
                     "blas": blas_info},
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="results/repro")
    parser.add_argument(
        "--allow-canonical-overwrite", action="store_true",
        help="explicitly permit writing into a frozen canonical directory "
             "(results/minimal/ or figures/); never used by the documented "
             "reproduction procedure",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    out = resolve_out_dir(args.out, args.allow_canonical_overwrite)
    out.mkdir(parents=True, exist_ok=True)

    t_start = time.monotonic()
    observable = staggered_magnetization_density_op(L)
    z_pi_density = z_pi_matrix(L) / L
    config = NoiseConfig()
    dm_executor = make_density_matrix_executor(observable, config)
    noise_model = config.build_model()

    steps_rows, seed_rows, folded_rows, shot_rows = [], [], [], []
    eps_u_all, eps_m_all, if_reportable = [], [], []
    shot_eps_u_all, shot_eps_m_all, shot_if_reportable = [], [], []

    for n in range(1, N_MAX + 1):
        circuit = transpile_to_basis(build_circuit(L, n))
        ed_ref = continuous_time_expectation(L, n * DT_DEFAULT, z_pi_density)
        e0 = statevector_expectation(circuit, observable)
        e_noisy = dm_executor(circuit)

        seeds = [run_seed_arms(circuit, dm_executor, s, noise=config) for s in FOLD_SEEDS]
        primary_mean, primary_std, _ = seed_band([s.primary_intercept for s in seeds])
        nominal_mean, nominal_std, _ = seed_band([s.nominal_intercept for s in seeds])
        effective_mean, effective_std, _ = seed_band([s.effective_intercept for s in seeds])
        secondary = secondary_ensemble(
            [list(SCALE_FACTORS)] * len(FOLD_SEEDS), [s.expectations for s in seeds]
        )

        eps_u = abs_error(e_noisy, e0)
        eps_m = abs_error(primary_mean, e0)
        per_seed_eps_m = [abs_error(s.primary_intercept, e0) for s in seeds]
        _, eps_m_band, _ = seed_band(per_seed_eps_m)
        step_if = improvement_factor(eps_u, eps_m, DELTA_DENSITY_MATRIX)
        reportable = is_reportable(eps_u)
        eps_u_all.append(eps_u)
        eps_m_all.append(eps_m)
        if reportable:
            if_reportable.append(step_if)

        # ---- shot-based secondary pipeline (§15/§16), same folded circuits ----
        per_seed_shot_values = []
        for k, fold_seed in enumerate(FOLD_SEEDS):
            values = []
            for j, scale in enumerate(SCALE_FACTORS):
                folded = fold_two_qubit(circuit, scale, seed=fold_seed)
                value = shot_expectation(
                    folded, noise_model, seed_simulator=shot_seed(n, k, j)
                )
                values.append(value)
                shot_rows.append([n, fold_seed, fmt(scale), fmt(value),
                                  shot_seed(n, k, j)])
            per_seed_shot_values.append(values)
        shot_lambda_one = [vals[0] for vals in per_seed_shot_values]
        shot_base_mean, shot_base_std = shot_baseline(shot_lambda_one)
        shot_primary = [
            linear_intercept(seeds[k].realized_scales, per_seed_shot_values[k])
            for k in range(len(FOLD_SEEDS))
        ]
        shot_nominal = [
            linear_intercept(SCALE_FACTORS, per_seed_shot_values[k])
            for k in range(len(FOLD_SEEDS))
        ]
        shot_effective = [
            linear_intercept(seeds[k].effective_scales, per_seed_shot_values[k])
            for k in range(len(FOLD_SEEDS))
        ]
        shot_primary_mean, shot_primary_std, shot_primary_sem = seed_band(shot_primary)
        shot_nominal_mean, shot_nominal_std, _ = seed_band(shot_nominal)
        shot_effective_mean, shot_effective_std, _ = seed_band(shot_effective)
        shot_secondary = secondary_ensemble(
            [list(SCALE_FACTORS)] * len(FOLD_SEEDS), per_seed_shot_values
        )
        shot_eps_u = abs_error(shot_base_mean, e0)
        shot_eps_m = abs_error(shot_primary_mean, e0)
        _, shot_eps_m_band, _ = seed_band(
            [abs_error(v, e0) for v in shot_primary]
        )
        shot_if = improvement_factor(shot_eps_u, shot_eps_m, DELTA_SHOT)
        shot_rep = is_reportable(shot_eps_u)
        shot_eps_u_all.append(shot_eps_u)
        shot_eps_m_all.append(shot_eps_m)
        if shot_rep:
            shot_if_reportable.append(shot_if)

        steps_rows.append([
            n, fmt(ed_ref), fmt(e0), fmt(e_noisy),
            fmt(primary_mean), fmt(primary_std),
            fmt(nominal_mean), fmt(nominal_std),
            fmt(effective_mean), fmt(effective_std),
            fmt_opt(secondary.estimate), secondary.mode, fmt_opt(secondary.std),
            fmt(eps_u), fmt(eps_m), fmt(eps_m_band),
            fmt(step_if.value), int(step_if.is_lower_bound), int(reportable),
            fmt(shot_base_mean), fmt(shot_base_std),
            fmt(shot_primary_mean), fmt(shot_primary_std), fmt(shot_primary_sem),
            fmt(shot_nominal_mean), fmt(shot_nominal_std),
            fmt(shot_effective_mean), fmt(shot_effective_std),
            fmt_opt(shot_secondary.estimate), shot_secondary.mode,
            fmt_opt(shot_secondary.std),
            fmt(shot_eps_u), fmt(shot_eps_m), fmt(shot_eps_m_band),
            fmt(shot_if.value), int(shot_if.is_lower_bound), int(shot_rep),
        ])
        for idx, (s, clamp_flag, log_est, avoid_est) in enumerate(zip(
            seeds, secondary.clamp_flags, secondary.log_estimates,
            secondary.avoid_log_estimates,
        )):
            seed_rows.append([
                n, s.fold_seed,
                fmt(s.primary_intercept), fmt(s.nominal_intercept),
                fmt(s.effective_intercept),
                int(clamp_flag), fmt(log_est), fmt_opt(avoid_est),
                int(secondary.avoid_log_failed[idx]),
                int(shot_secondary.clamp_flags[idx]),
                fmt(shot_secondary.log_estimates[idx]),
                fmt_opt(shot_secondary.avoid_log_estimates[idx]),
                int(shot_secondary.avoid_log_failed[idx]),
            ])
            for scale, lam_r, lam_eff, value, ops in zip(
                s.nominal_scales, s.realized_scales, s.effective_scales,
                s.expectations, s.instruction_counts,
            ):
                folded_rows.append([
                    n, s.fold_seed, fmt(scale), fmt(lam_r), fmt(lam_eff), fmt(value),
                    ops.get("cx", 0), ops.get("sx", 0), ops.get("x", 0),
                    ops.get("rz", 0), ops.get("sxdg", 0),
                ])
        print(f"n={n:2d} done: E0={e0:+.4f} noisy={e_noisy:+.4f} "
              f"ZNE(primary)={primary_mean:+.4f} IF={step_if.value:.3f} "
              f"secondary_mode={secondary.mode}", flush=True)

    # ---------------- aggregates and the pre-registered verdict (§13) ----------------
    rms_u, rms_m = rms(eps_u_all), rms(eps_m_all)
    gif = global_improvement_factor(rms_u, rms_m, DELTA_DENSITY_MATRIX)
    majority = majority_outcome(if_reportable)
    verdict = experiment_verdict(gif, majority)
    shot_rms_u, shot_rms_m = rms(shot_eps_u_all), rms(shot_eps_m_all)
    shot_gif = global_improvement_factor(shot_rms_u, shot_rms_m, DELTA_SHOT)
    shot_majority = majority_outcome(shot_if_reportable)
    shot_verdict = experiment_verdict(shot_gif, shot_majority)

    metrics = {
        "primary_pipeline": "density_matrix (exact under the noise model; zero sampling variance)",
        "rms_u": rms_u, "rms_m": rms_m,
        "gif_value": gif.value, "gif_is_lower_bound": gif.is_lower_bound,
        "reportable_steps_m": majority.reportable_steps,
        "if_wins": majority.wins,
        "majority_passes": majority.passes,
        "m_zero_flagged": verdict.m_zero_flagged,
        "verdict_passes": verdict.passes,
        "excluded_steps": [i + 1 for i, e in enumerate(eps_u_all) if not is_reportable(e)],
        "shot_pipeline": {
            "rms_u": shot_rms_u, "rms_m": shot_rms_m,
            "gif_value": shot_gif.value, "gif_is_lower_bound": shot_gif.is_lower_bound,
            "reportable_steps_m": shot_majority.reportable_steps,
            "if_wins": shot_majority.wins,
            "majority_passes": shot_majority.passes,
            "m_zero_flagged": shot_verdict.m_zero_flagged,
            "verdict_passes": shot_verdict.passes,
            "excluded_steps": [i + 1 for i, e in enumerate(shot_eps_u_all)
                               if not is_reportable(e)],
            "note": "full §13 secondary pipeline, reported ALONGSIDE the "
                    "density-matrix primary's pre-registered verdict above, "
                    "not replacing it",
        },
    }

    (out / "environment.json").write_text(
        json.dumps(environment_record(), indent=2, sort_keys=True) + "\n"
    )
    (out / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True, default=str) + "\n"
    )
    with (out / "steps.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "n", "ed_reference", "e0_trotter", "e_noisy_dm",
            "zne_primary_mean", "zne_primary_std",
            "zne_nominal_mean", "zne_nominal_std",
            "zne_effective_mean", "zne_effective_std",
            "secondary_estimate", "secondary_mode", "secondary_std",
            "eps_u", "eps_m", "eps_m_band",
            "if_value", "if_is_lower_bound", "reportable",
            "shot_baseline_mean", "shot_baseline_std",
            "shot_primary_mean", "shot_primary_std", "shot_primary_sem",
            "shot_nominal_mean", "shot_nominal_std",
            "shot_effective_mean", "shot_effective_std",
            "shot_secondary_estimate", "shot_secondary_mode", "shot_secondary_std",
            "shot_eps_u", "shot_eps_m", "shot_eps_m_band",
            "shot_if_value", "shot_if_is_lower_bound", "shot_reportable",
        ])
        writer.writerows(steps_rows)
    with (out / "seed_arms.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["n", "fold_seed", "primary_intercept", "nominal_intercept",
                         "effective_intercept", "clamp_flag", "secondary_log",
                         "secondary_avoid_log", "secondary_avoid_log_failed",
                         "shot_clamp_flag", "shot_secondary_log",
                         "shot_secondary_avoid_log", "shot_secondary_avoid_log_failed"])
        writer.writerows(seed_rows)
    with (out / "folded_circuits.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["n", "fold_seed", "lambda_nominal", "lambda_r", "lambda_eff",
                         "expectation_dm", "cx", "sx", "x", "rz", "sxdg"])
        writer.writerows(folded_rows)
    with (out / "shot_values.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["n", "fold_seed", "lambda_nominal", "expectation_shot",
                         "seed_simulator"])
        writer.writerows(shot_rows)

    elapsed = time.monotonic() - t_start
    print(f"\nVERDICT (§13, density-matrix primary): "
          f"{'PASS' if verdict.passes else 'FAIL'} | GIF={gif.value:.4f}"
          f"{' (lower bound)' if gif.is_lower_bound else ''} | "
          f"m={majority.reportable_steps} wins={majority.wins}")
    print(f"shot pipeline (§13 secondary, alongside): "
          f"{'PASS' if shot_verdict.passes else 'FAIL'} | GIF={shot_gif.value:.4f} | "
          f"m={shot_majority.reportable_steps} wins={shot_majority.wins}")
    print(f"wall clock: {elapsed:.1f} s (stdout only; not recorded in results files)")


if __name__ == "__main__":
    sys.exit(main())
