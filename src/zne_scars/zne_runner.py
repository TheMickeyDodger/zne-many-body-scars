"""ZNE plumbing (design.md §9-§11, §16): fidelity-restricted seeded folding,
the three pre-registered regression arms, and the §11 secondary-estimator policy.

Arms (design §10, pre-registered):
  PRIMARY    — degree-one OLS on the realized abscissas lambda_r (measured from
               folded gate counts; OLS weights recomputed from those abscissas,
               which differ from nominal at off-grid targets, e.g. odd n).
  NOMINAL    — the source-faithful comparison arm: same data, OLS on nominal lambda
               (identical to mitiq's LinearFactory result on the same values).
  EFFECTIVE  — diagnostic: OLS on lambda_eff = (G2*lambda_r + G1)/(G2 + G1) with
               exposure weights G_k = N_k * gamma_k, gamma_k = -ln(1 - p_k) (§10).

Secondary estimator (design §11): ExpFactory(asymptote=0.0), log mode; clamp
detection mirrors mitiq v1.0.0 exactly (sign from a degree-one fit, clamp when
sign*(y - asymptote) <= eps = 1e-6); per step, if ANY seed is clamp-flagged the
ensemble estimate switches to avoid_log mode for ALL seeds — clamped and
unclamped estimates are never averaged together; both modes are always recorded.

Folding policy (design §10): fold_gates_at_random with
fidelities = {"single": 1.0, "double": 0.99} — zero-weight (single-qubit) gates
are never folded, so only self-inverse cx gates are folded, matching the Paper.
Empirically verified (M2, C3): the qiskit->cirq->qiskit round trip preserves
instruction names on {rz, sx, x, cx} circuits; only the cx count changes.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import partial

import numpy as np
from qiskit import QuantumCircuit

from mitiq.zne import execute_with_zne
from mitiq.zne.inference import ExpFactory, Factory, LinearFactory
from mitiq.zne.scaling import fold_all, fold_gates_at_random

from .metrics import seed_band
from .noise import (
    ONE_QUBIT_NOISY_GATES,
    P1_DEFAULT,
    P2_DEFAULT,
    TWO_QUBIT_NOISY_GATES,
    NoiseConfig,
)

FIDELITIES = {"single": 1.0, "double": 0.99}  # design §10
SCALE_FACTORS = (1.0, 1.5, 2.0)  # design §9 (Paper Fig. 4)
FOLD_SEEDS = tuple(range(1000, 1008))  # design §16
EXP_CLAMP_EPS = 1.0e-6  # mitiq v1.0.0 inference.py default, mirrored (design §11)


# ---------------------------------------------------------------- folding

def fold_two_qubit(
    circuit: QuantumCircuit, scale_factor: float, seed: int
) -> QuantumCircuit:
    """Seeded random folding restricted to two-qubit gates (design §10)."""
    return fold_gates_at_random(
        circuit, scale_factor, seed=seed, fidelities=dict(FIDELITIES)
    )


def fold_full(circuit: QuantumCircuit, scale_factor: float) -> QuantumCircuit:
    """fold_all wrapper (every gate folded) — used by test T5."""
    return fold_all(circuit, scale_factor)


def two_qubit_count(circuit: QuantumCircuit) -> int:
    return int(circuit.count_ops().get("cx", 0))


def realized_scale(base: QuantumCircuit, folded: QuantumCircuit) -> float:
    """Realized two-qubit scale lambda_r = N_cx(folded)/N_cx(base) (design §10),
    measured from the circuits, never inferred from mitiq's rounding."""
    n_base = two_qubit_count(base)
    if n_base == 0:
        raise ValueError("base circuit has no cx gates")
    return two_qubit_count(folded) / n_base


# ---------------------------------------------------- exposure / abscissas

def exposure_weights(
    base_circuit: QuantumCircuit, p1: float = P1_DEFAULT, p2: float = P2_DEFAULT
) -> tuple[float, float]:
    """(Gamma_1, Gamma_2) of design §10-§11: Gamma_k = N_k * gamma_k with
    gamma_k = -ln(1 - p_k); N_k counted from the base transpiled circuit."""
    ops = base_circuit.count_ops()
    n1 = sum(int(ops.get(g, 0)) for g in ONE_QUBIT_NOISY_GATES)
    n2 = sum(int(ops.get(g, 0)) for g in TWO_QUBIT_NOISY_GATES)
    return n1 * -math.log1p(-p1), n2 * -math.log1p(-p2)


def effective_scale(lambda_r: float, gamma1: float, gamma2: float) -> float:
    """lambda_eff = (Gamma_2*lambda_r + Gamma_1)/(Gamma_2 + Gamma_1) <= lambda_r,
    equality at lambda_r = 1 (design §10).

    Zero-total-exposure convention (Gamma_1 = Gamma_2 = 0, i.e. p1 = p2 = 0):
    the §11 heuristic exponent Gamma_2*lambda_r + Gamma_1 vanishes identically,
    so every abscissa fits the constant noiseless data equally; lambda_eff is
    DEFINED as the identity relabeling lambda_r — deliberate, not a crash
    (§20 M2-6). NoiseConfig(0.0, 0.0) therefore behaves like the declared
    noiseless path rather than raising ZeroDivisionError."""
    total = gamma1 + gamma2
    if total == 0.0:
        return lambda_r
    return (gamma2 * lambda_r + gamma1) / total


def linear_intercept(scale_factors: Sequence[float], values: Sequence[float]) -> float:
    """Degree-one OLS zero-noise intercept; the abscissas may be nominal,
    realized, or effective — the weights are recomputed from whatever abscissas
    are passed (design §10-§11)."""
    slope, intercept = np.polyfit(
        np.asarray(scale_factors, dtype=float), np.asarray(values, dtype=float), 1
    )
    return float(intercept)


# ---------------------------------------------------------- factories

def linear_factory(scale_factors: Sequence[float] = SCALE_FACTORS) -> LinearFactory:
    return LinearFactory(scale_factors=list(scale_factors))


def exp_factory(
    scale_factors: Sequence[float] = SCALE_FACTORS, avoid_log: bool = False
) -> ExpFactory:
    """Secondary: exponential with asymptote fixed at the maximally-mixed value 0
    (design §11)."""
    return ExpFactory(
        scale_factors=list(scale_factors), asymptote=0.0, avoid_log=avoid_log
    )


def zne_estimate(
    circuit: QuantumCircuit,
    executor: Callable[[QuantumCircuit], float],
    fold_seed: int,
    scale_factors: Sequence[float] = SCALE_FACTORS,
    factory: Factory | None = None,
) -> float:
    """One seeded ZNE estimate via mitiq's execute_with_zne (nominal-lambda arm)."""
    if factory is None:
        factory = linear_factory(scale_factors)
    return execute_with_zne(
        circuit,
        executor,
        factory=factory,
        scale_noise=partial(fold_two_qubit, seed=fold_seed),
    )


# ------------------------------------------------- three linear arms (§10)

@dataclass(frozen=True)
class SeedArms:
    """One seed's folded data and the three linear zero-noise intercepts."""

    fold_seed: int
    nominal_scales: tuple[float, ...]
    realized_scales: tuple[float, ...]  # lambda_r, measured from gate counts
    effective_scales: tuple[float, ...]  # lambda_eff (§10)
    expectations: tuple[float, ...]
    instruction_counts: tuple[dict[str, int], ...]  # per-lambda count_ops of the folded circuit (§15 output spec)
    primary_intercept: float  # OLS on realized lambda_r (PRIMARY, §10)
    nominal_intercept: float  # OLS on nominal lambda (comparison arm)
    effective_intercept: float  # OLS on lambda_eff (diagnostic arm)


_UNTAGGED = object()  # sentinel: distinguishes "no declaration" from "declared noiseless"


def resolve_noise_config(
    executor: Callable[[QuantumCircuit], float], noise: NoiseConfig | None
) -> NoiseConfig:
    """Single-source-of-truth rule for the lambda_eff rates (F9, both paths closed):
    lambda_eff is computed only from rates KNOWN to match the simulation, or not
    at all. Knowledge is a declaration — either the executor's `.noise_config`
    tag (set by make_density_matrix_executor or declare_noise) or an explicit
    `noise` argument:

    The uniform rule: an explicit `noise` argument that CONTRADICTS an existing
    declaration raises, on every branch.

      * tag = NoiseConfig(...): use it; an explicit argument that differs raises.
      * tag = None (executor DECLARED noiseless): every folded expectation is
        identical, so the lambda_eff abscissa is provably inert; the §8 defaults
        serve only as a relabeling. An explicit argument is accepted only if it
        agrees with the declaration, i.e. zero total exposure (p1 = p2 = 0);
        nonzero explicit rates contradict declared noiselessness and raise.
      * no tag at all: an explicit `noise` argument is REQUIRED — the caller is
        asserting the simulated rates. With neither, this raises: the runner
        never invents default rates for an executor whose noise it cannot know.

    Residual honesty note: a caller who declares rates that do not match what
    their custom executor actually simulates defeats the check — a closure's
    true noise is not introspectable. For module-built executors the tag and the
    simulated model come from the same NoiseConfig object, so no gap exists there.
    """
    tagged = getattr(executor, "noise_config", _UNTAGGED)
    if tagged is _UNTAGGED:
        if noise is None:
            raise ValueError(
                "cannot compute lambda_eff: the executor does not declare its "
                "noise configuration and no explicit NoiseConfig was passed. "
                "Build the executor with make_density_matrix_executor, tag it "
                "with declare_noise(executor, NoiseConfig(...)) — or "
                "declare_noise(executor, None) if it is genuinely noiseless — "
                "or pass noise=NoiseConfig(...) matching what it simulates."
            )
        return noise
    if tagged is None:
        if noise is not None and (noise.p1 != 0.0 or noise.p2 != 0.0):
            raise ValueError(
                f"explicit lambda_eff rates {noise} contradict the executor's "
                "declared noiselessness (noise_config=None); declarations must "
                "agree — pass a zero-exposure NoiseConfig or omit the argument"
            )
        return noise if noise is not None else NoiseConfig()
    if noise is not None and noise != tagged:
        raise ValueError(
            f"lambda_eff rates {noise} disagree with the executor's noise "
            f"configuration {tagged}; the §10 diagnostic abscissa must be "
            "computed from the rates actually simulated"
        )
    return tagged


def run_seed_arms(
    base_circuit: QuantumCircuit,
    executor: Callable[[QuantumCircuit], float],
    fold_seed: int,
    scale_factors: Sequence[float] = SCALE_FACTORS,
    noise: NoiseConfig | None = None,
) -> SeedArms:
    """Fold once per scale factor, execute each folded circuit once, and fit all
    three arms on the same data (design §10: same measurements, three abscissas).
    The lambda_eff rates are resolved against the executor's own NoiseConfig
    (mismatch raises — F9)."""
    config = resolve_noise_config(executor, noise)
    gamma1, gamma2 = exposure_weights(base_circuit, config.p1, config.p2)
    realized, effective, values, op_counts = [], [], [], []
    for scale in scale_factors:
        folded = fold_two_qubit(base_circuit, scale, seed=fold_seed)
        lam_r = realized_scale(base_circuit, folded)
        realized.append(lam_r)
        effective.append(effective_scale(lam_r, gamma1, gamma2))
        values.append(executor(folded))
        op_counts.append({str(k): int(v) for k, v in folded.count_ops().items()})
    return SeedArms(
        fold_seed=fold_seed,
        nominal_scales=tuple(scale_factors),
        realized_scales=tuple(realized),
        effective_scales=tuple(effective),
        expectations=tuple(values),
        instruction_counts=tuple(op_counts),
        primary_intercept=linear_intercept(realized, values),
        nominal_intercept=linear_intercept(list(scale_factors), values),
        effective_intercept=linear_intercept(effective, values),
    )


@dataclass(frozen=True)
class ArmEnsemble:
    """Seed-ensemble statistics for the three linear arms (§13 ddof=1 bands)."""

    seeds: tuple[SeedArms, ...]
    primary_mean: float
    primary_std: float
    nominal_mean: float
    nominal_std: float
    effective_mean: float
    effective_std: float


def run_zne_arms(
    base_circuit: QuantumCircuit,
    executor: Callable[[QuantumCircuit], float],
    fold_seeds: Sequence[int] = FOLD_SEEDS,
    scale_factors: Sequence[float] = SCALE_FACTORS,
    noise: NoiseConfig | None = None,
) -> ArmEnsemble:
    """The full pre-registered ensemble: all three arms over the fold-seed set."""
    seeds = tuple(
        run_seed_arms(base_circuit, executor, s, scale_factors, noise)
        for s in fold_seeds
    )
    p_mean, p_std, _ = seed_band([s.primary_intercept for s in seeds])
    n_mean, n_std, _ = seed_band([s.nominal_intercept for s in seeds])
    e_mean, e_std, _ = seed_band([s.effective_intercept for s in seeds])
    return ArmEnsemble(
        seeds=seeds,
        primary_mean=p_mean,
        primary_std=p_std,
        nominal_mean=n_mean,
        nominal_std=n_std,
        effective_mean=e_mean,
        effective_std=e_std,
    )


# ------------------------------------- secondary estimator policy (§11)

def exp_clamp_flag(
    scale_factors: Sequence[float],
    values: Sequence[float],
    asymptote: float = 0.0,
    eps: float = EXP_CLAMP_EPS,
) -> bool:
    """True iff mitiq's log-mode exponential fit would clamp any shifted value.
    Mirrors mitiq v1.0.0 inference.py exactly: sign is inferred from a degree-one
    fit as sign(intercept - asymptote); a value is clamped when
    sign*(y - asymptote) <= eps (wrong sign or magnitude <= eps)."""
    slope, intercept = np.polyfit(
        np.asarray(scale_factors, dtype=float), np.asarray(values, dtype=float), 1
    )
    sign = np.sign(-(asymptote - intercept))
    return bool(any(sign * (y - asymptote) <= eps for y in values))


def _exp_fit(
    scale_factors: Sequence[float], values: Sequence[float], avoid_log: bool
) -> float | None:
    """One exponential fit. Returns None when mitiq's nonlinear avoid_log fit
    raises ExtrapolationError (non-convergence, observed on near-zero shot data);
    the caller records the failure explicitly — it is never substituted."""
    from mitiq.zne.inference import ExtrapolationError

    lookup = {float(s): float(v) for s, v in zip(scale_factors, values)}
    factory = exp_factory(scale_factors, avoid_log=avoid_log)
    factory.run_classical(lambda s: lookup[float(s)])
    try:
        return float(factory.reduce())
    except ExtrapolationError:
        return None


@dataclass(frozen=True)
class SecondaryEnsemble:
    """§11 secondary estimator over the seed ensemble, homogeneous by mode.

    Fit-failure policy (M3 extension, §20 M3-3): mitiq's avoid_log nonlinear fit
    can fail to converge; a failed fit is recorded as None with its flag set.
    If the chosen mode is "log", the estimate is unaffected (the failure is a
    recorded diagnostic only). If the chosen mode is "avoid_log" and ANY seed's
    avoid_log fit failed, the step's secondary estimate is marked invalid
    (mode="avoid_log_failed", estimate=None) — never a partial or mixed average.
    """

    log_estimates: tuple[float, ...]  # per seed, log mode (always recorded)
    avoid_log_estimates: tuple[float | None, ...]  # per seed; None = fit failed
    avoid_log_failed: tuple[bool, ...]  # per seed
    clamp_flags: tuple[bool, ...]  # per seed
    mode: str  # "log" | "avoid_log" | "avoid_log_failed"
    estimate: float | None  # mean within the single mode used; None if invalid
    std: float | None  # ddof=1 within the single mode used; None if invalid


def secondary_ensemble(
    per_seed_scale_factors: Sequence[Sequence[float]],
    per_seed_values: Sequence[Sequence[float]],
    expected_seeds: int | None = len(FOLD_SEEDS),
) -> SecondaryEnsemble:
    """§11 policy: clamped and unclamped estimates are never averaged together.
    If ANY seed is clamp-flagged, ALL seeds contribute their avoid_log fit;
    otherwise all contribute their log fit. Both modes are recorded regardless.

    §11's homogeneity guarantee is stated over the full seed ensemble, so length
    mismatches are ERRORS, never truncations (F8): the two inputs must have the
    same length, and by default exactly len(FOLD_SEEDS) = 8 seeds are required
    (the experiment-facing protocol). Unit tests may relax with expected_seeds.
    """
    if len(per_seed_scale_factors) != len(per_seed_values):
        raise ValueError(
            f"per-seed inputs disagree: {len(per_seed_scale_factors)} scale-factor "
            f"rows vs {len(per_seed_values)} value rows — refusing to truncate"
        )
    if expected_seeds is not None and len(per_seed_values) != expected_seeds:
        raise ValueError(
            f"§11 requires the full {expected_seeds}-seed ensemble; got "
            f"{len(per_seed_values)} seeds"
        )
    flags, logs, avoids = [], [], []
    for scales, values in zip(per_seed_scale_factors, per_seed_values, strict=True):
        flags.append(exp_clamp_flag(scales, values))
        log_fit = _exp_fit(scales, values, avoid_log=False)
        if log_fit is None:  # log-mode fit is a linear regression; cannot fail
            raise RuntimeError("log-mode exponential fit unexpectedly failed")
        logs.append(log_fit)
        avoids.append(_exp_fit(scales, values, avoid_log=True))
    failures = tuple(a is None for a in avoids)
    if not any(flags):
        mode = "log"
        mean, std, _ = seed_band(logs)
    elif any(failures):
        mode, mean, std = "avoid_log_failed", None, None
    else:
        mode = "avoid_log"
        mean, std, _ = seed_band([a for a in avoids])  # all floats here
    return SecondaryEnsemble(
        log_estimates=tuple(logs),
        avoid_log_estimates=tuple(avoids),
        avoid_log_failed=failures,
        clamp_flags=tuple(flags),
        mode=mode,
        estimate=mean,
        std=std,
    )
