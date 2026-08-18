"""T4-T6 (design.md §17) plus the pre-registered arm and secondary-policy logic.

T4: the full ZNE pipeline returns the noiseless value exactly at zero noise.
T5: fold_all at lambda=3 gives exactly 3x the cx count.
T6: the §10 fidelities dict folds NO single-qubit gate, cx counts land on the
    EXACT §10 grid values, and every instruction in the folded circuit is either
    rz or carries a §8 noise channel. Seed threading is tested structurally.
Arms: the three pre-registered regressions (§10) — realized-lambda_r primary,
    nominal comparison, lambda_eff diagnostic — including odd-n off-grid targets.
Secondary: the §11 ExpFactory clamp/avoid_log ensemble policy.
"""

import math

import numpy as np
import pytest

from zne_scars.executors import make_density_matrix_executor, statevector_expectation
from zne_scars.noise import (
    CLEAN_GATES,
    NoiseConfig,
    build_noise_model,
    noisy_instruction_names,
)
from zne_scars.observables import staggered_magnetization_density_op
from zne_scars.trotter import build_circuit, transpile_to_basis
from zne_scars.zne_runner import (
    FIDELITIES,
    SCALE_FACTORS,
    effective_scale,
    exp_clamp_flag,
    exposure_weights,
    fold_full,
    fold_two_qubit,
    realized_scale,
    run_seed_arms,
    run_zne_arms,
    secondary_ensemble,
    two_qubit_count,
    zne_estimate,
)

L = 4
STEPS = 2  # base cx = 2(L-1)*STEPS = 12; fold grid spacing in lambda = 2/12 = 1/6


@pytest.fixture(scope="module")
def transpiled_circuit():
    return transpile_to_basis(build_circuit(L, STEPS))


@pytest.fixture(scope="module")
def one_step_circuit():
    # Odd n: base cx = 6, grid spacing 1/3 — nominal lambda=1.5 is OFF-grid (§10).
    return transpile_to_basis(build_circuit(L, 1))


def _expected_grid_cx(base_cx: int, scale: float) -> tuple[int, ...]:
    """Achievable folded cx counts nearest the target, from the §10 grid:
    counts are base_cx + 2m; the target fold count is m* = (scale-1)*base_cx/2.
    Returns (exact,) when m* is an integer, else the two neighbours."""
    m_target = (scale - 1.0) * base_cx / 2.0
    if abs(m_target - round(m_target)) < 1e-12:
        return (base_cx + 2 * round(m_target),)
    return (
        base_cx + 2 * math.floor(m_target),
        base_cx + 2 * math.ceil(m_target),
    )


# ------------------------------------------------------------------ T4

def test_t4_zne_recovers_exact_value_at_zero_noise(transpiled_circuit):
    """T4: with a noiseless executor, the ZNE estimate equals the exact statevector
    value (every scale factor produces the same expectation; the linear intercept
    is that value)."""
    observable = staggered_magnetization_density_op(L)
    exact = statevector_expectation(transpiled_circuit, observable)
    executor = make_density_matrix_executor(observable, noise=None)
    for seed in (1000, 1003):
        estimate = zne_estimate(transpiled_circuit, executor, fold_seed=seed)
        assert estimate == pytest.approx(exact, abs=1e-8)


# ------------------------------------------------------------------ T5

def test_t5_fold_all_triples_cx_count(transpiled_circuit):
    """T5: folded circuit at lambda=3 with fold_all has exactly 3x the cx count."""
    base_cx = two_qubit_count(transpiled_circuit)
    folded = fold_full(transpiled_circuit, 3.0)
    assert base_cx > 0
    assert two_qubit_count(folded) == 3 * base_cx


# ------------------------------------------------------------------ T6

def test_t6_restricted_folding_exact_grid_counts(transpiled_circuit):
    """T6a: single-qubit gate counts unchanged at every scale factor, and the cx
    count equals the EXACT grid value derived from §10 (all of 1.5, 2.0, 3.0 are
    exactly achievable on base_cx=12: m = 3, 6, 12)."""
    base_ops = dict(transpiled_circuit.count_ops())
    base_cx = base_ops["cx"]
    assert base_cx == 2 * (L - 1) * STEPS  # 12: precondition for the grid numbers
    for scale in (1.5, 2.0, 3.0):
        expected = _expected_grid_cx(base_cx, scale)
        assert len(expected) == 1, f"lambda={scale} should be exactly achievable"
        folded = fold_two_qubit(transpiled_circuit, scale, seed=1000)
        folded_ops = dict(folded.count_ops())
        for gate in ("rz", "sx", "x"):
            assert folded_ops.get(gate, 0) == base_ops.get(gate, 0), (
                f"single-qubit gate {gate} was folded at scale {scale} "
                f"(fidelities={FIDELITIES})"
            )
        assert folded_ops["cx"] == expected[0]
        assert realized_scale(transpiled_circuit, folded) == pytest.approx(
            expected[0] / base_cx, abs=1e-12
        )


def test_t6_off_grid_target_lands_on_nearest_grid_point(transpiled_circuit):
    """Off-grid target: lambda=1.25 on base_cx=12 wants m=1.5 folds — impossible;
    the folded count must be one of the two specific neighbours (14 or 16 cx)."""
    base_cx = two_qubit_count(transpiled_circuit)
    expected = _expected_grid_cx(base_cx, 1.25)
    assert expected == (14, 16)
    folded = fold_two_qubit(transpiled_circuit, 1.25, seed=1000)
    assert two_qubit_count(folded) in expected


def test_t6_every_folded_instruction_is_clean_or_noise_covered(transpiled_circuit):
    """T6b: every instruction name in every folded circuit is either rz (clean by
    design §8) or carries a noise channel in the §8 model — no silent noiseless
    instruction can enter via folding or conversion round trips."""
    covered = noisy_instruction_names(build_noise_model()) | set(CLEAN_GATES)
    for scale in (1.5, 2.0, 3.0):
        folded = fold_two_qubit(transpiled_circuit, scale, seed=1000)
        names = set(folded.count_ops())
        assert names <= covered, f"uncovered instructions at scale {scale}: {names - covered}"


def test_t6_seed_threading_is_real(transpiled_circuit):
    """§16: same seed -> structurally identical folded circuit; different seed ->
    different fold LOCATIONS (circuit differs) but the same grid point (same cx
    count). Catches a dropped/ignored seed."""
    a = fold_two_qubit(transpiled_circuit, 1.5, seed=1000)
    b = fold_two_qubit(transpiled_circuit, 1.5, seed=1000)
    c = fold_two_qubit(transpiled_circuit, 1.5, seed=1001)
    assert a == b, "same seed must reproduce the identical folded circuit"
    assert a != c, "different seeds must fold different gate locations"
    assert two_qubit_count(a) == two_qubit_count(c)


# ------------------------------------------------- three arms (§10, M1)

def test_arms_odd_step_realized_abscissas_differ_from_nominal(one_step_circuit):
    """Odd n: lambda=1.5 is off-grid (base cx=6, spacing 1/3), so the primary arm
    must regress on measured lambda_r != 1.5 while 1.0 and 2.0 stay exact."""
    observable = staggered_magnetization_density_op(L)
    executor = make_density_matrix_executor(observable, NoiseConfig())
    arms = run_seed_arms(one_step_circuit, executor, fold_seed=1000)
    assert arms.realized_scales[0] == pytest.approx(1.0, abs=1e-12)
    assert arms.realized_scales[2] == pytest.approx(2.0, abs=1e-12)
    assert arms.realized_scales[1] != pytest.approx(1.5, abs=1e-6)
    assert arms.realized_scales[1] in (
        pytest.approx(4 / 3, abs=1e-12),
        pytest.approx(5 / 3, abs=1e-12),
    )
    # With distinct abscissas the recomputed-OLS primary differs from nominal.
    assert arms.primary_intercept != pytest.approx(arms.nominal_intercept, abs=1e-12)


def test_arms_effective_scale_identity_and_bounds(one_step_circuit):
    """§10 algebra: (G1+G2)*lambda_eff == G2*lambda_r + G1 exactly;
    lambda_eff <= lambda_r with equality at lambda_r = 1."""
    gamma1, gamma2 = exposure_weights(one_step_circuit)
    assert gamma1 > 0 and gamma2 > 0
    for lam_r in (1.0, 4 / 3, 2.0):
        lam_eff = effective_scale(lam_r, gamma1, gamma2)
        assert (gamma1 + gamma2) * lam_eff == pytest.approx(
            gamma2 * lam_r + gamma1, abs=1e-12
        )
        if lam_r == 1.0:
            assert lam_eff == pytest.approx(1.0, abs=1e-12)
        else:
            assert lam_eff < lam_r


def test_effective_scale_zero_exposure_is_identity_relabeling(transpiled_circuit):
    """p1 = p2 = 0 (zero total exposure): lambda_eff is DEFINED as lambda_r —
    the identity relabeling, deliberate, never ZeroDivisionError. End-to-end,
    NoiseConfig(0.0, 0.0) behaves like the declared-noiseless path."""
    assert effective_scale(1.5, 0.0, 0.0) == 1.5
    assert effective_scale(1.0, 0.0, 0.0) == 1.0
    observable = staggered_magnetization_density_op(L)
    exact = statevector_expectation(transpiled_circuit, observable)
    executor = make_density_matrix_executor(observable, NoiseConfig(0.0, 0.0))
    arms = run_seed_arms(transpiled_circuit, executor, fold_seed=1000)
    assert arms.effective_scales == arms.realized_scales
    for value in (arms.primary_intercept, arms.nominal_intercept, arms.effective_intercept):
        assert value == pytest.approx(exact, abs=1e-8)


def test_arms_noiseless_invariance(transpiled_circuit):
    """At zero noise every folded circuit implements the same unitary, so all
    three arms must return the exact noiseless value."""
    observable = staggered_magnetization_density_op(L)
    exact = statevector_expectation(transpiled_circuit, observable)
    executor = make_density_matrix_executor(observable, noise=None)
    arms = run_seed_arms(transpiled_circuit, executor, fold_seed=1002)
    for value in (arms.primary_intercept, arms.nominal_intercept, arms.effective_intercept):
        assert value == pytest.approx(exact, abs=1e-8)


def test_arms_nominal_intercept_matches_mitiq_linear_factory(transpiled_circuit):
    """Cross-validation: the nominal arm's OLS intercept equals mitiq's
    LinearFactory result on the same seeded folds (identical circuits, identical
    executor)."""
    observable = staggered_magnetization_density_op(L)
    executor = make_density_matrix_executor(observable, NoiseConfig())
    seed = 1004
    arms = run_seed_arms(transpiled_circuit, executor, fold_seed=seed)
    mitiq_value = zne_estimate(transpiled_circuit, executor, fold_seed=seed)
    assert arms.nominal_intercept == pytest.approx(mitiq_value, abs=1e-9)


def test_arms_ensemble_bands_are_ddof_one(transpiled_circuit):
    """run_zne_arms returns means AND ddof=1 standard deviations, verified against
    numpy directly for all three arms (F10: isfinite alone would accept ddof=0)."""
    observable = staggered_magnetization_density_op(L)
    executor = make_density_matrix_executor(observable, NoiseConfig())
    ensemble = run_zne_arms(transpiled_circuit, executor, fold_seeds=(1000, 1001, 1002))
    assert len(ensemble.seeds) == 3
    per_arm = {
        "primary": ([s.primary_intercept for s in ensemble.seeds],
                    ensemble.primary_mean, ensemble.primary_std),
        "nominal": ([s.nominal_intercept for s in ensemble.seeds],
                    ensemble.nominal_mean, ensemble.nominal_std),
        "effective": ([s.effective_intercept for s in ensemble.seeds],
                      ensemble.effective_mean, ensemble.effective_std),
    }
    for arm, (values, mean, std) in per_arm.items():
        assert mean == pytest.approx(float(np.mean(values)), abs=1e-12), arm
        assert std == pytest.approx(float(np.std(values, ddof=1)), abs=1e-12), (
            f"{arm} std is not the ddof=1 sample standard deviation"
        )
        assert np.isfinite(mean) and np.isfinite(std)


def test_arms_noise_config_mismatch_raises(transpiled_circuit):
    """F9: lambda_eff rates that disagree with the executor's simulated noise must
    be an error, never a silently miscalibrated diagnostic abscissa."""
    observable = staggered_magnetization_density_op(L)
    executor = make_density_matrix_executor(observable, NoiseConfig(p1=1e-3, p2=1e-2))
    with pytest.raises(ValueError, match="disagree"):
        run_seed_arms(
            transpiled_circuit, executor, fold_seed=1000,
            noise=NoiseConfig(p1=5e-3, p2=1e-2),
        )
    # Matching explicit rates are accepted.
    arms = run_seed_arms(
        transpiled_circuit, executor, fold_seed=1000,
        noise=NoiseConfig(p1=1e-3, p2=1e-2),
    )
    assert np.isfinite(arms.effective_intercept)


def test_arms_undeclared_executor_raises_instead_of_default_rates(transpiled_circuit):
    """F9 (round-3 hole): a bare callable that declares nothing must NOT silently
    acquire the §8 default rates for lambda_eff — the runner refuses to invent
    rates it cannot know."""
    observable = staggered_magnetization_density_op(L)

    def rogue_executor(circuit):  # simulates some unknown noise; no declaration
        return statevector_expectation(circuit, observable)

    with pytest.raises(ValueError, match="does not declare its noise"):
        run_seed_arms(transpiled_circuit, rogue_executor, fold_seed=1000)
    # An explicit argument is the caller's assertion of the simulated rates: accepted.
    arms = run_seed_arms(
        transpiled_circuit, rogue_executor, fold_seed=1000, noise=NoiseConfig()
    )
    assert np.isfinite(arms.effective_intercept)


def test_arms_declared_noiseless_executor_is_accepted(transpiled_circuit):
    """declare_noise(executor, None) is the explicit opt-in for the genuinely
    noiseless case; the abscissa relabeling is inert on constant data."""
    from zne_scars.executors import declare_noise

    observable = staggered_magnetization_density_op(L)
    exact = statevector_expectation(transpiled_circuit, observable)
    executor = declare_noise(
        lambda circuit: statevector_expectation(circuit, observable), None
    )
    arms = run_seed_arms(transpiled_circuit, executor, fold_seed=1000)
    for value in (arms.primary_intercept, arms.nominal_intercept, arms.effective_intercept):
        assert value == pytest.approx(exact, abs=1e-8)


def test_arms_contradicting_declarations_raise(transpiled_circuit):
    """(c): declared-noiseless executor + explicit NONZERO rates is a contradiction
    between two declarations and must raise; a zero-exposure explicit config
    AGREES with declared noiselessness and is accepted."""
    from zne_scars.executors import declare_noise

    observable = staggered_magnetization_density_op(L)
    executor = declare_noise(
        lambda circuit: statevector_expectation(circuit, observable), None
    )
    with pytest.raises(ValueError, match="contradict"):
        run_seed_arms(
            transpiled_circuit, executor, fold_seed=1000,
            noise=NoiseConfig(p1=1e-3, p2=1e-2),
        )
    arms = run_seed_arms(
        transpiled_circuit, executor, fold_seed=1000, noise=NoiseConfig(0.0, 0.0)
    )
    assert np.isfinite(arms.effective_intercept)


# ------------------------------------- secondary policy (§11, M2)

SCALES = list(SCALE_FACTORS)
CLEAN_VALUES = [0.8 * np.exp(-0.5 * s) for s in SCALES]
CLAMPED_VALUES = [0.5, 0.2, 1e-7]  # third value <= eps: mitiq's log fit clamps it


def test_secondary_clamp_detection_mirrors_mitiq():
    assert exp_clamp_flag(SCALES, CLEAN_VALUES) is False
    assert exp_clamp_flag(SCALES, CLAMPED_VALUES) is True


def test_secondary_log_mode_when_no_seed_flagged():
    result = secondary_ensemble(
        [SCALES, SCALES], [CLEAN_VALUES, CLEAN_VALUES], expected_seeds=2
    )
    assert result.mode == "log"
    assert result.clamp_flags == (False, False)
    # Pure exponential data: the log-mode fit recovers the amplitude exactly.
    assert result.estimate == pytest.approx(0.8, abs=1e-9)
    assert result.estimate == pytest.approx(float(np.mean(result.log_estimates)), abs=1e-12)


def test_secondary_any_flag_switches_all_seeds_to_avoid_log():
    """§11: if ANY seed is flagged, ALL eight (here two) contribute avoid_log fits;
    clamped and unclamped estimates are never averaged together."""
    result = secondary_ensemble(
        [SCALES, SCALES], [CLEAN_VALUES, CLAMPED_VALUES], expected_seeds=2
    )
    assert result.clamp_flags == (False, True)
    assert result.mode == "avoid_log"
    assert result.estimate == pytest.approx(
        float(np.mean(result.avoid_log_estimates)), abs=1e-12
    )
    # The clamped seed's LOG value must not enter the estimate: the homogeneous
    # avoid_log mean differs from the all-log mean, which contains it.
    all_log_mean = float(np.mean(result.log_estimates))
    assert result.estimate != pytest.approx(all_log_mean, abs=1e-9)
    # Both modes recorded for every seed regardless of the mode used.
    assert len(result.log_estimates) == len(result.avoid_log_estimates) == 2


def test_secondary_avoid_log_fit_failure_is_flagged_never_substituted(monkeypatch):
    """M3 policy extension (§20 M3-3): a non-convergent avoid_log fit is recorded
    as a flagged failure. In log mode the estimate is unaffected; in avoid_log
    mode any failure invalidates the step's secondary (no partial averages)."""
    import zne_scars.zne_runner as zr

    real_fit = zr._exp_fit

    def failing_avoid_log(scales, values, avoid_log):
        return None if avoid_log else real_fit(scales, values, avoid_log=False)

    monkeypatch.setattr(zr, "_exp_fit", failing_avoid_log)
    log_mode = zr.secondary_ensemble(
        [SCALES, SCALES], [CLEAN_VALUES, CLEAN_VALUES], expected_seeds=2
    )
    assert log_mode.mode == "log"
    assert log_mode.estimate == pytest.approx(0.8, abs=1e-9)
    assert log_mode.avoid_log_failed == (True, True)
    assert log_mode.avoid_log_estimates == (None, None)

    failed_mode = zr.secondary_ensemble(
        [SCALES, SCALES], [CLEAN_VALUES, CLAMPED_VALUES], expected_seeds=2
    )
    assert failed_mode.mode == "avoid_log_failed"
    assert failed_mode.estimate is None and failed_mode.std is None
    assert failed_mode.log_estimates and all(
        isinstance(v, float) for v in failed_mode.log_estimates
    )


def test_secondary_length_mismatch_raises_not_truncates():
    """F8: unequal per-seed inputs are an error — §11's homogeneity guarantee is
    over the full ensemble, so silent zip-truncation would be a protocol violation."""
    with pytest.raises(ValueError, match="refusing to truncate"):
        secondary_ensemble(
            [SCALES, SCALES, SCALES],
            [CLEAN_VALUES] * 8,
            expected_seeds=None,
        )


def test_secondary_requires_full_eight_seed_ensemble_by_default():
    """F8: the experiment-facing default demands exactly the eight-seed ensemble."""
    with pytest.raises(ValueError, match="8-seed ensemble"):
        secondary_ensemble([SCALES, SCALES], [CLEAN_VALUES, CLEAN_VALUES])
    result = secondary_ensemble([SCALES] * 8, [CLEAN_VALUES] * 8)
    assert result.mode == "log"
    assert len(result.clamp_flags) == 8
