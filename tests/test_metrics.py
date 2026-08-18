"""§13 metric guarantees (M3): the baseline-relevance filter is numerator-only,
the delta denominator rule yields flagged lower bounds and never a non-finite
value or an exception, RMS/GIF run over ALL steps regardless of the filter,
bands are ddof=1, the m=0 majority edge case is vacuous-and-flagged, and the
shot baseline is the mean of the seeded lambda=1 executions."""

import numpy as np
import pytest

from zne_scars.metrics import (
    DELTA_DENSITY_MATRIX,
    DELTA_SHOT,
    EPS_MIN,
    experiment_verdict,
    global_improvement_factor,
    improvement_factor,
    is_reportable,
    majority_outcome,
    rms,
    seed_band,
    shot_baseline,
)


def test_baseline_relevance_filter_is_numerator_only():
    assert not is_reportable(EPS_MIN - 1e-9)
    assert is_reportable(EPS_MIN)
    assert is_reportable(0.5)


def test_improvement_factor_point_value():
    f = improvement_factor(0.2, 0.1, DELTA_DENSITY_MATRIX)
    assert f.value == pytest.approx(2.0)
    assert not f.is_lower_bound
    assert f.exceeds_one


def test_denominator_rule_zero_and_subdelta_never_raise_or_return_nonfinite():
    for eps_m in (0.0, DELTA_DENSITY_MATRIX / 2, DELTA_DENSITY_MATRIX):
        f = improvement_factor(0.3, eps_m, DELTA_DENSITY_MATRIX)
        assert f.is_lower_bound
        assert np.isfinite(f.value)
        assert f.value == pytest.approx(0.3 / DELTA_DENSITY_MATRIX)
    zero_over_zero = improvement_factor(0.0, 0.0, DELTA_SHOT)
    assert zero_over_zero.is_lower_bound and np.isfinite(zero_over_zero.value)
    assert zero_over_zero.value == 0.0


def test_gif_zero_denominator_is_flagged_lower_bound_not_exception():
    """The reviewer's reproduction: global_improvement_factor(1.0, 0.0) must not
    raise ZeroDivisionError; it returns the flagged lower bound."""
    g = global_improvement_factor(1.0, 0.0, DELTA_DENSITY_MATRIX)
    assert g.is_lower_bound
    assert np.isfinite(g.value)
    assert g.value == pytest.approx(1.0 / DELTA_DENSITY_MATRIX)


def test_rms_and_gif_use_all_steps_regardless_of_filter():
    """Sub-eps_min errors are excluded from the majority test only; RMS keeps them."""
    errors = [0.001] * 20 + [0.5] * 20  # half the steps are below EPS_MIN
    expected = float(np.sqrt(np.mean(np.asarray(errors) ** 2)))
    assert rms(errors) == pytest.approx(expected, abs=1e-15)
    assert len(errors) == 40  # the §13 window


def test_majority_strictness_and_ties():
    up = improvement_factor(0.2, 0.1, DELTA_SHOT)  # IF = 2 > 1
    down = improvement_factor(0.1, 0.2, DELTA_SHOT)  # IF = 0.5 < 1
    assert majority_outcome([up, up, down]).passes is True  # 2 of 3 > 1.5
    assert majority_outcome([up, up, down, down]).passes is False  # tie at even m fails
    assert majority_outcome([up, up, up, down]).passes is True  # 3 of 4 > 2


def test_m_zero_is_vacuous_and_flagged_never_an_exception():
    outcome = majority_outcome([])
    assert outcome.is_vacuous and outcome.passes is None
    gif = improvement_factor(0.5, 0.25, DELTA_DENSITY_MATRIX)  # GIF = 2 > 1
    verdict = experiment_verdict(gif, outcome)
    assert verdict.m_zero_flagged
    assert verdict.passes is True  # verdict rests on GIF alone (§13)
    failing = experiment_verdict(
        improvement_factor(0.1, 0.2, DELTA_DENSITY_MATRIX), outcome
    )
    assert failing.m_zero_flagged and failing.passes is False


def test_verdict_requires_both_clauses_when_m_positive():
    gif_up = improvement_factor(0.4, 0.2, DELTA_SHOT)
    gif_down = improvement_factor(0.2, 0.4, DELTA_SHOT)
    up = improvement_factor(0.2, 0.1, DELTA_SHOT)
    down = improvement_factor(0.1, 0.2, DELTA_SHOT)
    majority_pass = majority_outcome([up, up, down])
    majority_fail = majority_outcome([up, down, down])
    assert experiment_verdict(gif_up, majority_pass).passes
    assert not experiment_verdict(gif_up, majority_fail).passes
    assert not experiment_verdict(gif_down, majority_pass).passes


def test_seed_band_is_ddof_one():
    values = [0.1, 0.2, 0.4, 0.7]
    mean, std, sem = seed_band(values)
    assert mean == pytest.approx(float(np.mean(values)))
    assert std == pytest.approx(float(np.std(values, ddof=1)))
    assert sem == pytest.approx(std / np.sqrt(len(values)))


def test_shot_baseline_is_mean_of_seeded_lambda_one_runs():
    values = [-0.91, -0.93, -0.92, -0.90, -0.94, -0.92, -0.91, -0.93]  # 8 seeds
    mean, std = shot_baseline(values)
    assert mean == pytest.approx(float(np.mean(values)))
    assert std == pytest.approx(float(np.std(values, ddof=1)))
