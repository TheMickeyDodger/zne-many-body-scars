"""Tests for tools/phase2_contract_check.py (the Phase 2 offline contract checker).

Everything here is synthetic. No experiment runs, nothing from zne_scars is
imported, no network is touched, and every file the tests write lives under
tmp_path. The checker's reference implementations are exercised on inputs
with closed-form answers, the declared edge-case policies are triggered one by
one, and the cross-field checks are shown to reject deliberately corrupted
copies of the real contract while accepting the real tree.
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "tools" / "phase2_contract_check.py"

spec = importlib.util.spec_from_file_location("phase2_contract_check", CHECKER)
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)

TREE_FILES = [
    "tools/phase2_contract.json",
    "tools/phase2_contract_check.py",
    "docs/prereg-phase2.md",
    "docs/phase2-analysis-contract.md",
    "docs/design.md",
    "docs/prereg-p2zero-outline.md",
    "docs/followup-study-draft.md",
    "tests/test_phase2_contract.py",
]


# Rank minima per phase (amendment A-1, 2026-09-08): Phase 2B EXP 3, Phase 2C EXP 2. Read from the JSON so the
# tests follow the single source of truth; the checker's own module values are cross-checked below.
_CONTRACT = json.loads((ROOT / "tools/phase2_contract.json").read_text(encoding="utf-8"))
M2B = _CONTRACT["phase2b"]["rank_rule"]["EXP"]
M2C = _CONTRACT["phase2c"]["transpilation"]["rank_rule"]["EXP"]
PRE_AMENDMENT_IDENTITIES = {
    "docs/prereg-phase2.md": "913831adf38828f9802fd55fb94f560cc4f7e16e48c3a62afe6336f3cffc19d4",
    "docs/phase2-analysis-contract.md": "97e67e68e0368c621393af118b7c0dc1f8f2018c04c9cfd0eef01c01ab14cdeb",
    "tools/phase2_contract.json": "f77e15326baf9012c2799d0b7417556ff156ffb4e5d275cedd7be02a49e5b266",
    "tools/phase2_contract_check.py": "8d20d8c7d776e4c9b2f4ff8a69f671419c72a549bc73afe990a9cd6bc426a503",
    "tests/test_phase2_contract.py": "6d5dc35a397db5708eabb4b34a92f75476f8405622dfaf5d975f5f8301a2f19b",
}


def _results_by_name(results):
    return {name: (ok, detail) for name, ok, detail in results}


def _copy_tree(tmp_path: Path) -> Path:
    """Copy the real deliverables into a synthetic root so they can be corrupted safely."""
    root = tmp_path / "tree"
    for rel in TREE_FILES:
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, dst)
    return root


def _run_on(root: Path):
    return _results_by_name(cc.Checker(root).run())


# ---------------------------------------------------------------------------
# closed-form algebra
# ---------------------------------------------------------------------------


def test_interaction_is_identically_zero_on_exactly_additive_input():
    e00 = [0.9, -0.7, 0.5, -0.3, 0.2, -0.6]
    r10 = [0.95, 0.9, 0.85, 0.8, 0.75, 0.7]
    r01 = [0.8, 0.7, 0.6, 0.5, 0.45, 0.4]
    rows = [cc.phase2a_step(e, e * a, e * b, e * a * b) for e, a, b in zip(e00, r10, r01)]
    assert max(abs(r["i_n"]) for r in rows) < 1e-12
    assert all(r["flags"] == [] for r in rows)


def test_interaction_equals_known_value_on_interacting_input():
    rows = [cc.phase2a_step(e, e * 0.9, e * 0.7, e * 0.9 * 0.7 * math.exp(-0.2)) for e in (0.9, -0.5, 0.3)]
    assert all(abs(r["i_n"] - 0.2) < 1e-12 for r in rows)
    verdict, _, stats = cc.phase2a_verdict(rows)
    assert verdict == "INTERACTION"
    assert stats["s_max_lo"] > math.log(1.10)


def test_a00_term_present_and_negative_interaction_gives_signed_band():
    assert cc.interaction(0.5, 0.2, 0.1, 0.0) == pytest.approx(0.2)
    # a negative I with a budget: signed band must sit around I, magnitude bounds around |I|
    i_n, eta_i = -0.2, 0.01
    assert (i_n - eta_i, i_n + eta_i) == pytest.approx((-0.21, -0.19))
    assert (max(0.0, abs(i_n) - eta_i), abs(i_n) + eta_i) == pytest.approx((0.19, 0.21))


def test_budget_propagation_closed_form():
    eta_r, eta_a = cc.eta_propagation(0.5, 0.25, 1e-9)
    assert eta_r == pytest.approx(1e-9 * 1.5 / (0.25 - 1e-9), rel=1e-12)
    assert eta_a == pytest.approx(eta_r / (0.5 - eta_r), rel=1e-12)
    assert cc.eta_propagation(1e-12, 0.25, 1e-9)[1] is None  # unresolved ratio


def test_ols_slope_and_intercept_exact():
    xs = list(range(1, 11))
    a, b = cc.ols(xs, [0.3 - 0.05 * x for x in xs])
    assert -b == pytest.approx(0.05, abs=1e-12)
    assert a == pytest.approx(0.3, abs=1e-12)


def test_peak_extractor_and_parabolic_timing():
    y = [0.0] + [-math.cos(2 * math.pi * n / 20) for n in range(1, 49)]
    assert cc.find_peaks(y) == [10, 30]
    par = {n: 1 - (n - 20.3) ** 2 for n in (19, 20, 21)}
    m = cc.match_peak(par, [19, 20, 21])
    assert m["matched_n"] == 20 and m["timing"] == pytest.approx(20.3, abs=1e-12)
    off, fallback = cc.parabolic_timing(1.0, 1.0, 1.0)  # flat: not concave
    assert fallback and off == 0.0


def test_trapezoid_quadrature_closed_form():
    assert cc.tiae([1, 2, 3, 4, 5], [0] * 5) == pytest.approx(12.0)
    assert cc.tiae([0.5] * 48, [0.0] * 48) == pytest.approx(0.5 * 47)


def test_percentile_interval_known_quantiles_and_fixed_seed_resampling():
    vals = [float(i) for i in range(1, 2001)]
    lo, hi, u, flags = cc.percentile_interval(vals, 0.025, 0.975)
    assert (lo, hi) == pytest.approx((50.975, 1950.025)) and u == 0 and flags == []
    # frozen resampling reference: numpy default_rng([20260907, phase, cell_index, b]) + multinomial (§C4.5)
    c1 = cc.resample_counts([300, 300, 300, 124], 1024, cc.bootstrap_rng(2, 1, 0))
    c2 = cc.resample_counts([300, 300, 300, 124], 1024, cc.bootstrap_rng(2, 1, 0))
    c3 = cc.resample_counts([300, 300, 300, 124], 1024, cc.bootstrap_rng(2, 1, 1))
    assert c1 == c2 == [316, 306, 297, 105] and c1 != c3 and sum(c3) == 1024
    assert cc.resample_counts([1024, 0, 0, 0], 1024, cc.bootstrap_rng(3, 0, 5)) == [1024, 0, 0, 0]
    with pytest.raises(ValueError):
        cc.resample_counts([0, 0], 10, cc.bootstrap_rng(2, 1, 0))


def test_global_folding_arithmetic():
    ops = ["sx", "rz", "cx", "sx", "cx", "rz", "cx", "x", "cx", "rz"]
    folded, lam_r, lam_1 = cc.fold_global_counts(ops, 1.5)
    assert len(folded) == 14 and lam_r == pytest.approx(1.5) and lam_1 == pytest.approx(1.0)
    folded3, lam_r3, _ = cc.fold_global_counts(ops, 3.0)
    assert len(folded3) == 30 and lam_r3 == pytest.approx(3.0)
    # lambda = 2: divmod(1, 2) = (0, 1), so no full fold and a partial fold of round(1 * 2 / 2) = 1 suffix
    # operation; the operation count doubles (4 vs 2) while the cx-count scale is 3, which is exactly why
    # lambda_r is measured from the folded circuit rather than taken from the nominal value
    folded2, lam_r2, lam_1_2 = cc.fold_global_counts(["sx", "cx"], 2.0)
    assert folded2 == ["sx", "cx", "cx", "cx"] and lam_r2 == pytest.approx(3.0) and lam_1_2 == pytest.approx(1.0)


def test_polynomial_and_exponential_fits_recover_exact_parameters():
    xs = [1.0, 1.25, 1.5, 1.75, 2.0]
    assert cc.poly_intercept(xs, [0.8 - 0.3 * x for x in xs], 1) == pytest.approx(0.8, abs=1e-12)
    assert cc.poly_intercept(xs, [0.7 - 0.2 * x + 0.05 * x * x for x in xs], 2) == pytest.approx(0.7, abs=1e-10)
    val, clamped = cc.exp_fit_fixed(xs, [0.9 * math.exp(-0.4 * x) for x in xs], 0.0, min_distinct=M2B)
    assert val == pytest.approx(0.9, abs=1e-10) and not clamped
    assert cc.poly_intercept([1, 1.5, 2], [0.9, 0.6, 0.3], 1) == pytest.approx(1.5)  # unphysical, kept


def test_exponential_estimator_matches_the_pinned_mitiq_algebra_on_non_exact_data():
    # Reviewer round-03 finding 2: sign from the linear intercept, sqrt(shifted) weights in the log fit
    val, clamped = cc.exp_fit_fixed([1, 1.5, 2], [0.9, 0.6, 0.2], 0.0, min_distinct=M2B)
    assert val == pytest.approx(3.4834832, abs=2e-7) and not clamped
    assert val != pytest.approx(4.5459713, abs=1e-3)  # the unweighted mean-sign estimator is rejected
    np = pytest.importorskip("numpy")
    xs, ys = np.array([1, 1.5, 2.0]), np.array([0.9, 0.6, 0.2])
    sg = np.sign(np.polyfit(xs, ys, 1)[-1])
    sh = np.maximum(sg * ys, 1e-6)
    ref = sg * np.exp(np.polyfit(xs, np.log(sh), 1, w=np.sqrt(sh))[-1])
    assert val == pytest.approx(float(ref), abs=1e-12)
    # weighted OLS convention: w multiplies the residual (numpy.polyfit), so the normal equations use w^2
    a, b = cc.weighted_ols([1, 2, 3], [1, 2, 3], [1, 1, 1])
    assert (a, b) == pytest.approx((0.0, 1.0))


def test_exponential_clamp_homogeneity_and_avoid_log_fallback():
    val, clamped = cc.exp_fit_fixed([1, 1.5, 2], [0.1, 0.2, 0.8], 0.0, min_distinct=M2B)
    assert clamped  # rising data: the declared clamp branch triggers
    agg, mode, flags = cc.exp_step_aggregate([([1, 1.5, 2], [0.9, 0.6, 0.2]), ([1, 1.5, 2], [0.1, 0.2, 0.8])], 0.0, min_distinct=M2B)
    # the declared homogeneity branch: every seed of the step is refitted with the mitiq avoid_log solver;
    # either all converge (mode avoid_log) or the step is undefined with no partial mean (avoid_log_failed)
    assert (mode == "avoid_log" and agg is not None and "CLAMP_RERUN" in flags) or (mode == "avoid_log_failed" and agg is None and "EXP_FIT_FAILED" in flags)
    # Reviewer round-04 fixture: y = 0.05 exp(x) clamps in log mode; the pinned mitiq fallback recovers 0.05
    rising = [0.05 * math.exp(x) for x in (1, 1.5, 2)]
    assert cc.exp_fit_fixed([1, 1.5, 2], rising, 0.0, min_distinct=M2B)[1] is True
    agg3, mode3, _ = cc.exp_step_aggregate([([1, 1.5, 2], rising)] * 8, 0.0, min_distinct=M2B)
    assert mode3 == "avoid_log" and agg3 == pytest.approx(0.05, abs=1e-9)
    assert cc.exp_fit_avoid_log([1, 1.5, 2], rising, 0.0, min_distinct=M2B) == pytest.approx(0.05, abs=1e-9)
    agg2, mode2, flags2 = cc.exp_step_aggregate([([1, 1.5, 2], [0.9, 0.6, 0.2]), ([1, 1.5, 2], [0.85, 0.55, 0.25])], 0.0, min_distinct=M2B)
    assert mode2 == "log" and flags2 == [] and agg2 == pytest.approx(0.5 * (3.483483195 + cc.exp_fit_fixed([1, 1.5, 2], [0.85, 0.55, 0.25], 0.0, min_distinct=M2B)[0]), abs=1e-8)
    xs = [1.0, 1.25, 1.5, 1.75, 2.0]
    assert cc.exp_fit_avoid_log(xs, [0.9 * math.exp(-0.4 * x) for x in xs], 0.0, min_distinct=M2B) == pytest.approx(0.9, abs=1e-8)
    with pytest.raises(ValueError):
        cc.exp_fit_avoid_log([1, 1], [0.5, 0.4], 0.0, min_distinct=M2B)
    with pytest.raises(ValueError):
        cc.exp_fit_avoid_log([1, 1], [0.5, 0.4], 0.0, min_distinct=M2C)


def test_nonlinear_aggregation_order_fixture_from_the_reviewer():
    seeds = [(0.5, 0.5, 0.25), (-0.5, -0.5, 0.25)]
    assert cc.aggregate_frozen_order(seeds) == 0.0
    assert cc.aggregate_wrong_order(seeds) == pytest.approx(0.25)
    assert cc.aggregate_frozen_order(seeds) != cc.aggregate_wrong_order(seeds)


def test_seed_simulator_unique_over_the_declared_ranges():
    seeds = {cc.seed_simulator(c, n, k, j) for c in (1, 2, 162) for n in range(1, 49) for k in range(8) for j in range(5)}
    assert len(seeds) == 3 * 48 * 8 * 5


# ---------------------------------------------------------------------------
# edge-case policies, each triggered and producing the declared verdict
# ---------------------------------------------------------------------------


def test_sign_flip_blocks_the_primary_verdict():
    r = cc.phase2a_step(0.5, 0.45, -0.3, 0.2)
    assert "SIGN_FLIP" in r["flags"] and r["i_n"] is None
    verdict, reason, _ = cc.phase2a_verdict([r, r, r])
    assert verdict == "INCONCLUSIVE" and "SIGN_FLIP" in reason


def test_ratio_above_one_keeps_primary_but_blocks_secondary():
    hi = dict(cc.phase2a_step(0.5, 0.55, 0.4, 0.3), n=1)
    good = dict(cc.phase2a_step(0.5, 0.45, 0.4, 0.36), n=2)
    good2 = dict(good, n=3)
    assert "RATIO_ABOVE_ONE" in hi["flags"] and hi["i_n"] is not None
    assert cc.phase2a_verdict([hi, good, good2])[0] != "INCONCLUSIVE"
    sec = cc.secondary_fit([hi, good, good2], "10", [])
    assert sec["fit_available"] == 0 and "FIT_UNAVAILABLE" in sec["flags"] and sec["violating_steps"] == [0]


def test_below_mask_step_is_tabulated_but_excluded():
    below = cc.phase2a_step(0.05, 0.04, 0.03, 0.02)
    assert "BELOW_MASK" in below["flags"] and below["in_mask"] == 0 and below["r10"] is not None
    good = cc.phase2a_step(0.5, 0.45, 0.4, 0.36)
    _, _, stats = cc.phase2a_verdict([good, good, good, below])
    assert stats["s_max_hi"] < 1e-6  # the below-mask step did not enter


def test_too_few_points_is_blocking():
    good = cc.phase2a_step(0.5, 0.45, 0.4, 0.36)
    verdict, reason, stats = cc.phase2a_verdict([good, good])
    assert verdict == "INCONCLUSIVE" and "TOO_FEW_POINTS" in reason
    assert stats is None  # amendment A-2: the statistics are undefined below k_min, not merely the verdict blocked


def test_fit_failure_on_singular_or_rank_deficient_design():
    with pytest.raises(ValueError):
        cc.ols([2, 2, 2], [1, 2, 3])
    with pytest.raises(ValueError):
        cc.poly_intercept([1, 1, 2], [0.1, 0.2, 0.3], 2)
    with pytest.raises(ValueError):
        cc.exp_fit_fixed([1, 1], [0.5, 0.4], 0.0, min_distinct=M2B)
    with pytest.raises(ValueError):
        cc.exp_fit_fixed([1, 1], [0.5, 0.4], 0.0, min_distinct=M2C)


# ---------------------------------------------------------------------------
# Amendment A-1 (2026-09-08): Phase 2B EXP minimum three distinct realized abscissas; Phase 2C keeps two.
# Every test below fails on the pre-amendment checker (single hard-coded guard at two, used for both phases).
# ---------------------------------------------------------------------------

def _decay(x):
    return 0.9 * math.exp(-0.4 * x)


def _rising(x):
    return 0.05 * math.exp(x)  # clamps in log mode -> forces the avoid_log rerun


def _exp_outcome(fn, xs, ys, m):
    try:
        return "fit", fn(xs, ys, 0.0, min_distinct=m)
    except ValueError as e:
        return ("FIT_FAILURE" if str(e).startswith("FIT_FAILURE") else "EXP_FIT_FAILED"), None


def test_amendment_minima_are_three_for_phase_2b_and_two_for_phase_2c():
    assert M2B == 3 and M2C == 2
    assert cc.RANK_RULE_2B == {"LIN": 2, "QUAD": 3, "EXP": 3}
    assert cc.RANK_RULE_2C == {"LIN": 2, "QUAD": 3, "EXP": 2}
    assert _CONTRACT["constants"]["C-EXP-MIN-2B"]["value"] == 3 and _CONTRACT["constants"]["C-EXP-MIN-2C"]["value"] == 2
    assert _CONTRACT["phase2b"]["rank_rule"] == {**_CONTRACT["phase2b"]["rank_rule"], "LIN": 2, "QUAD": 3, "EXP": 3}
    a1 = next(a for a in _CONTRACT["amendments"] if a["id"] == "A-1")
    assert a1["date"] == "2026-09-08" and a1["pre_data"] is True
    assert a1["historical_identities"] == PRE_AMENDMENT_IDENTITIES
    assert "REJECT" in a1["trigger"]


def test_exp_rank_minimum_is_a_required_parameter_so_no_phase_is_applied_silently():
    xs = [1.0, 1.5, 2.0]
    ys = [_decay(x) for x in xs]
    with pytest.raises(TypeError):
        cc.exp_fit_fixed(xs, ys, 0.0)  # positional/default minimum is not allowed
    with pytest.raises(TypeError):
        cc.exp_fit_avoid_log(xs, ys, 0.0)
    with pytest.raises(TypeError):
        cc.exp_step_aggregate([(xs, ys)] * 8, 0.0)


@pytest.mark.parametrize("mode_fn", [cc.exp_fit_fixed, cc.exp_fit_avoid_log], ids=["log", "avoid_log"])
def test_exp_rank_boundary_one_two_three_distinct_in_both_modes_and_both_phases(mode_fn):
    one = ([1.0, 1.0, 1.0], [0.5, 0.4, 0.3])
    two = ([1.0, 2.0], [_decay(1.0), _decay(2.0)])
    three = ([1.0, 1.5, 2.0], [_decay(x) for x in (1.0, 1.5, 2.0)])
    # one distinct abscissa: FIT_FAILURE under both phases
    assert _exp_outcome(mode_fn, *one, M2B)[0] == "FIT_FAILURE"
    assert _exp_outcome(mode_fn, *one, M2C)[0] == "FIT_FAILURE"
    # two distinct: FIT_FAILURE under the Phase 2B minimum (3), a fit under the Phase 2C minimum (2)
    assert _exp_outcome(mode_fn, *two, M2B)[0] == "FIT_FAILURE"
    st, val = _exp_outcome(mode_fn, *two, M2C)
    assert st == "fit"
    v2 = val[0] if isinstance(val, tuple) else val
    assert v2 == pytest.approx(0.9, abs=1e-6)  # exact data through two points recovers b = 0.9
    # three distinct: a fit under both
    for m in (M2B, M2C):
        st, val = _exp_outcome(mode_fn, *three, m)
        v3 = val[0] if isinstance(val, tuple) else val
        assert st == "fit" and v3 == pytest.approx(0.9, abs=1e-6)
    # the recorded distinct count is what the rule sees
    assert cc.n_distinct(one[0]) == 1 and cc.n_distinct(two[0]) == 2 and cc.n_distinct(three[0]) == 3


@pytest.mark.parametrize("mode_fn", [cc.exp_fit_fixed, cc.exp_fit_avoid_log], ids=["log", "avoid_log"])
def test_duplicate_abscissas_are_retained_as_recorded_and_count_once(mode_fn):
    # four recorded points, two distinct: still below the Phase 2B minimum, admitted under Phase 2C
    two_dup = ([1.0, 1.0, 2.0, 2.0], [_decay(1.0), _decay(1.0) + 0.02, _decay(2.0), _decay(2.0) - 0.02])
    assert cc.n_distinct(two_dup[0]) == 2
    assert _exp_outcome(mode_fn, *two_dup, M2B)[0] == "FIT_FAILURE"
    assert _exp_outcome(mode_fn, *two_dup, M2C)[0] == "fit"
    # four recorded points, three distinct: admitted under Phase 2B, and the duplicate point changes the regression,
    # which shows it is kept as recorded rather than dropped
    three_dup = ([1.0, 1.0, 1.5, 2.0], [_decay(1.0), _decay(1.0) + 0.02, _decay(1.5), _decay(2.0)])
    three = ([1.0, 1.5, 2.0], [_decay(x) for x in (1.0, 1.5, 2.0)])
    assert cc.n_distinct(three_dup[0]) == 3
    st4, v4 = _exp_outcome(mode_fn, *three_dup, M2B)
    st3, v3 = _exp_outcome(mode_fn, *three, M2B)
    v4 = v4[0] if isinstance(v4, tuple) else v4
    v3 = v3[0] if isinstance(v3, tuple) else v3
    assert st4 == "fit" and st3 == "fit" and abs(v4 - v3) > 1e-9


def test_one_rank_deficient_seed_nulls_the_phase_2b_step_with_no_surviving_seed_mean():
    three = ([1.0, 1.5, 2.0], [_decay(x) for x in (1.0, 1.5, 2.0)])
    two = ([1.0, 2.0], [_decay(1.0), _decay(2.0)])
    # log mode
    agg_b, mode_b, fl_b = cc.exp_step_aggregate([three] * 7 + [two], 0.0, min_distinct=M2B)
    assert agg_b is None and mode_b == "fit_failure" and fl_b == ["FIT_FAILURE"]
    agg_c, mode_c, fl_c = cc.exp_step_aggregate([three] * 7 + [two], 0.0, min_distinct=M2C)
    assert agg_c == pytest.approx(0.9, abs=1e-6) and mode_c == "log" and fl_c == []
    agg_ok, mode_ok, _ = cc.exp_step_aggregate([three] * 8, 0.0, min_distinct=M2B)
    assert agg_ok == pytest.approx(0.9, abs=1e-9) and mode_ok == "log"
    # a surviving-seed mean would have been 0.9; the rule returns None, not 0.9
    assert agg_b != pytest.approx(0.9)
    # avoid_log mode (a clamped seed forces the rerun; the rank-deficient seed still fails the step)
    rise = ([1.0, 1.5, 2.0], [_rising(x) for x in (1.0, 1.5, 2.0)])
    rise2 = ([1.0, 2.0], [_rising(1.0), _rising(2.0)])
    agg_r, mode_r, fl_r = cc.exp_step_aggregate([rise] * 7 + [rise2], 0.0, min_distinct=M2B)
    assert agg_r is None and mode_r == "fit_failure" and fl_r == ["FIT_FAILURE"]
    agg_r2, mode_r2, _ = cc.exp_step_aggregate([rise] * 8, 0.0, min_distinct=M2B)
    assert mode_r2 == "avoid_log" and agg_r2 == pytest.approx(0.05, abs=1e-9)
    agg_rc, mode_rc, _ = cc.exp_step_aggregate([rise] * 7 + [rise2], 0.0, min_distinct=M2C)
    assert mode_rc == "avoid_log" and agg_rc == pytest.approx(0.05, abs=1e-6)


def test_bootstrap_cannot_repair_a_structural_rank_failure():
    xs = [1.0, 1.0, 2.0, 2.0, 2.0]  # five recorded scale points, two distinct realized abscissas, fixed under resampling
    recorded = [[7000, 1192], [6900, 1292], [5000, 3192], [5100, 3092], [4900, 3292]]
    B = 120
    reps_b, reps_c = [], []
    for b in range(B):
        rng = cc.bootstrap_rng(2, 7, b)
        ys = []
        for cnt in recorded:
            r = cc.resample_counts(cnt, 8192, rng)
            ys.append((r[0] - r[1]) / 8192)
        reps_b.append(cc.exp_step_aggregate([(xs, ys)] * 8, 0.0, min_distinct=M2B)[0])
        reps_c.append(cc.exp_step_aggregate([(xs, ys)] * 8, 0.0, min_distinct=M2C)[0])
    assert reps_b == [None] * B  # every replicate undefined: the abscissas never change
    lo, hi, u, flags = cc.percentile_interval(reps_b, 0.025, 0.975)
    assert u == B and "UNDEFINED" in flags and math.isinf(lo) and math.isinf(hi)
    assert cc.three_way(lo, hi, -1, 1, undefined=True) == "INDETERMINATE"
    assert cc.beta_hat(reps_b, 0.5) == (None, "BETA_UNDEFINED")  # no survivor mean for the bias either
    lo_c, hi_c, u_c, flags_c = cc.percentile_interval(reps_c, 0.025, 0.975)
    assert u_c == 0 and "UNDEFINED" not in flags_c and math.isfinite(lo_c) and math.isfinite(hi_c)


def _mutate_text(root: Path, rel: str, old: str, new: str):
    p = root / rel
    t = p.read_text(encoding="utf-8")
    assert t.count(old) >= 1, old
    p.write_text(t.replace(old, new, 1), encoding="utf-8")


_RANK_JSON = "rank: JSON phase2b.rank_rule = {LIN 2, QUAD 3, EXP 3} and phase2c.transpilation.rank_rule = {LIN 2, QUAD 3, EXP 2} (numeric, phase-scoped), C-EXP-MIN-2B = 3, C-EXP-MIN-2C = 2, all equal to the checker's RANK_RULE_2B / RANK_RULE_2C"
_RANK_PROSE_JSON = "rank: JSON prose agrees with the numeric rules (phase2c.transpilation.extrapolators say >= 2/3/2; phase2b.extrapolators.EXP says >= 3 distinct realized abscissas; the estimator order names phase2b.rank_rule with EXP 3)"
_RANK_DRIVEN = "rank: driven by the JSON minima, both EXP reference implementations reject two distinct abscissas under phase2b.rank_rule and accept them under phase2c.transpilation.rank_rule"
_RANK_AMEND = "rank: dated pre-data amendment A-1 (2026-09-08) is recorded in the JSON with the five historical identities and the canonical Reviewer REJECT that triggered it, and both documents carry the amendment record"
_BINDING = "cross: every constant is bound to a named definition site (anchor + render, non-digit boundary); a mutated value or render fails here"


def _rank_prereg_name(res):
    return next(k for k in res if k.startswith("rank: prereg §4.3"))


def _rank_contract_name(res):
    return next(k for k in res if k.startswith("rank: contract §C4.2"))


def test_reverting_the_phase_2b_exp_minimum_to_two_in_the_json_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    _mutate_json(root, lambda d: d["phase2b"]["rank_rule"].__setitem__("EXP", 2))
    res = _run_on(root)
    assert res[_RANK_JSON][0] is False and res[_RANK_DRIVEN][0] is False


def test_raising_the_phase_2c_exp_minimum_to_three_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    _mutate_json(root, lambda d: d["phase2c"]["transpilation"]["rank_rule"].__setitem__("EXP", 3))
    res = _run_on(root)
    assert res[_RANK_JSON][0] is False and res[_RANK_DRIVEN][0] is False


def test_constant_c_exp_min_2b_mutated_to_two_is_rejected_by_binding_and_rank_checks(tmp_path):
    root = _copy_tree(tmp_path)

    def mutate(d):
        d["constants"]["C-EXP-MIN-2B"]["value"] = 2
        d["constants"]["C-EXP-MIN-2B"]["render"] = "2"

    _mutate_json(root, mutate)
    res = _run_on(root)
    assert res[_BINDING][0] is False and "C-EXP-MIN-2B" in res[_BINDING][1]
    assert res[_RANK_JSON][0] is False


def test_json_prose_saying_two_for_phase_2b_exp_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    _mutate_json(root, lambda d: d["phase2b"]["extrapolators"].__setitem__("EXP", d["phase2b"]["extrapolators"]["EXP"].replace(">= 3 distinct realized abscissas", ">= 2 distinct realized abscissas")))
    res = _run_on(root)
    assert res[_RANK_PROSE_JSON][0] is False
    root2 = _copy_tree(tmp_path / "b")
    _mutate_json(root2, lambda d: d["statistics"]["bootstrap"]["estimator_order"].__setitem__(1, "per fold seed: LIN/QUAD/EXP fits with rank requirements and per-seed EXP clamp rule"))
    assert _run_on(root2)[_RANK_PROSE_JSON][0] is False


def test_contract_c42_reverted_to_two_for_exp_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    _mutate_text(root, "docs/phase2-analysis-contract.md", "`EXP` (two parameters with the asymptote fixed) at least 3", "`EXP` (two parameters with the asymptote fixed) at least 2")
    res = _run_on(root)
    assert res[_rank_contract_name(res)][0] is False
    root2 = _copy_tree(tmp_path / "b")
    _mutate_text(root2, "docs/phase2-analysis-contract.md", "§C4.2 for Phase 2B (`LIN` 2, `QUAD` 3, `EXP` 3 distinct realized abscissas)", "§C4.2 for Phase 2B (`LIN` 2, `QUAD` 3, `EXP` 2 distinct realized abscissas)")
    res2 = _run_on(root2)
    assert res2[_rank_contract_name(res2)][0] is False


def test_prereg_43_or_62_reverted_to_two_for_exp_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    _mutate_text(root, "docs/prereg-phase2.md", "exponential fit needs at least three distinct realized abscissas as well", "exponential fit needs at least two distinct realized abscissas as well")
    res = _run_on(root)
    assert res[_rank_prereg_name(res)][0] is False
    root2 = _copy_tree(tmp_path / "b")
    _mutate_text(root2, "docs/prereg-phase2.md", "`LIN` two, `QUAD` three, `EXP` three distinct realized abscissas,\n   amendment A-1", "`LIN` two, `QUAD` three, `EXP` two distinct realized abscissas,\n   amendment A-1")
    res2 = _run_on(root2)
    assert res2[_rank_prereg_name(res2)][0] is False
    root3 = _copy_tree(tmp_path / "c")
    _mutate_text(root3, "docs/prereg-phase2.md", "$n^{\\mathrm{EXP}}_{\\min,\\mathrm{2B}} = 3$", "$n^{\\mathrm{EXP}}_{\\min,\\mathrm{2B}} = 2$")
    res3 = _run_on(root3)
    assert res3[_rank_prereg_name(res3)][0] is False and res3[_BINDING][0] is False


def test_prereg_54_phase_2c_changed_to_three_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    _mutate_text(root, "docs/prereg-phase2.md", "requires at least two distinct abscissas, with the design.md §11 clamp", "requires at least three distinct abscissas, with the design.md §11 clamp")
    res = _run_on(root)
    assert res[_rank_prereg_name(res)][0] is False


def test_amendment_record_removed_or_falsified_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    _mutate_json(root, lambda d: d.__setitem__("amendments", []))
    assert _run_on(root)[_RANK_AMEND][0] is False
    root2 = _copy_tree(tmp_path / "b")
    _mutate_json(root2, lambda d: d["amendments"][0]["historical_identities"].__setitem__("docs/prereg-phase2.md", "0" * 64))
    assert _run_on(root2)[_RANK_AMEND][0] is False


def test_checker_minima_are_bound_to_the_json(monkeypatch):
    # if the checker's own module value drifted from the JSON, the rank check must fail on the real tree
    monkeypatch.setitem(cc.RANK_RULE_2B, "EXP", 2)
    res = _run_on(ROOT)
    assert res[_RANK_JSON][0] is False


def _load_mutant_checker(tmp_path: Path, mutate_src):
    """A temporary candidate copy of the checker with one deliberate implementation mutation, loaded as a module."""
    src = CHECKER.read_text(encoding="utf-8")
    mutated = mutate_src(src)
    assert mutated != src, "mutation did not apply"
    mp = tmp_path / "mutant_checker.py"
    mp.write_text(mutated, encoding="utf-8")
    mspec = importlib.util.spec_from_file_location("mutant_checker", mp)
    mod = importlib.util.module_from_spec(mspec)
    mspec.loader.exec_module(mod)
    return mod


_GUARD = 'if n_distinct(xs) < min_distinct:\n        raise ValueError(f"FIT_FAILURE: rank ({n_distinct(xs)} distinct abscissas < {min_distinct})")'
_GUARD_AT_TWO = 'if n_distinct(xs) < 2:  # MUTANT: pre-amendment guard, phase parameter ignored\n        raise ValueError(f"FIT_FAILURE: rank ({n_distinct(xs)} distinct abscissas < {min_distinct})")'
_AGG_FAIL = '            if str(e).startswith("FIT_FAILURE"):\n                return None, "fit_failure", ["FIT_FAILURE"]\n            raise\n        fits.append(v)'
_AGG_SURVIVOR = '            if str(e).startswith("FIT_FAILURE"):\n                continue  # MUTANT: survivor averaging\n            raise\n        fits.append(v)'


@pytest.mark.parametrize("mode", ["log", "avoid_log"])
def test_mutant_exp_guard_reverted_to_two_is_caught_by_the_exactly_two_boundary(tmp_path, mode):
    # Implementation mutation evidence: keep the new API (min_distinct required) but revert only the EXP guard of
    # the mode under test to the pre-amendment `< 2`. The exactly-two boundary assertion must then fail for that
    # mode (the mutant admits two distinct abscissas under the Phase 2B minimum) and nothing else changes.
    assert CHECKER.read_text(encoding="utf-8").count(_GUARD) == 2  # one guard per EXP mode
    fn_name = "exp_fit_fixed" if mode == "log" else "exp_fit_avoid_log"

    def mutate(src):
        head, _, tail = src.partition(f"def {fn_name}(")
        return head + f"def {fn_name}(" + tail.replace(_GUARD, _GUARD_AT_TWO, 1)

    mut = _load_mutant_checker(tmp_path, mutate)
    two = ([1.0, 2.0], [_decay(1.0), _decay(2.0)])
    good, bad = (cc.exp_fit_fixed, mut.exp_fit_fixed) if mode == "log" else (cc.exp_fit_avoid_log, mut.exp_fit_avoid_log)
    other_good, other_bad = (cc.exp_fit_avoid_log, mut.exp_fit_avoid_log) if mode == "log" else (cc.exp_fit_fixed, mut.exp_fit_fixed)
    # the real checker rejects two under Phase 2B; the mutant admits them -> the boundary assertion fails on the mutant
    assert _exp_outcome(good, *two, M2B)[0] == "FIT_FAILURE"
    with pytest.raises(AssertionError):
        assert _exp_outcome(bad, *two, M2B)[0] == "FIT_FAILURE"
    assert _exp_outcome(bad, *two, M2B)[0] == "fit"
    # the untouched mode still rejects, so the test discriminates which guard was weakened
    assert _exp_outcome(other_bad, *two, M2B)[0] == _exp_outcome(other_good, *two, M2B)[0] == "FIT_FAILURE"
    # one distinct abscissa is still rejected by the mutant (its guard is 2, not 0), and Phase 2C behaviour is unchanged
    assert _exp_outcome(bad, [1.0, 1.0], [0.5, 0.4], M2B)[0] == "FIT_FAILURE"
    assert _exp_outcome(bad, *two, M2C)[0] == "fit"
    # failed-seed propagation: with the log guard weakened, a rank-deficient seed no longer nulls the Phase 2B step
    if mode == "log":
        three = ([1.0, 1.5, 2.0], [_decay(x) for x in (1.0, 1.5, 2.0)])
        assert cc.exp_step_aggregate([three] * 7 + [two], 0.0, min_distinct=M2B)[0] is None
        assert mut.exp_step_aggregate([three] * 7 + [two], 0.0, min_distinct=M2B)[0] == pytest.approx(0.9, abs=1e-6)


def test_mutant_step_aggregate_that_averages_surviving_seeds_is_caught(tmp_path):
    # Implementation mutation evidence for §C4.3 step 4: a candidate that skips the failed seed and averages the rest
    assert CHECKER.read_text(encoding="utf-8").count(_AGG_FAIL) == 1
    mut = _load_mutant_checker(tmp_path, lambda src: src.replace(_AGG_FAIL, _AGG_SURVIVOR, 1))
    three = ([1.0, 1.5, 2.0], [_decay(x) for x in (1.0, 1.5, 2.0)])
    two = ([1.0, 2.0], [_decay(1.0), _decay(2.0)])
    assert cc.exp_step_aggregate([three] * 7 + [two], 0.0, min_distinct=M2B) == (None, "fit_failure", ["FIT_FAILURE"])
    agg, mode, _ = mut.exp_step_aggregate([three] * 7 + [two], 0.0, min_distinct=M2B)
    assert agg == pytest.approx(0.9, abs=1e-6) and mode == "log"  # the survivor mean the contract forbids
    with pytest.raises(AssertionError):
        assert mut.exp_step_aggregate([three] * 7 + [two], 0.0, min_distinct=M2B)[0] is None


# ---------------------------------------------------------------------------
# Amendment A-2 (2026-09-08): pinned EXP sign/linear-fit convention, small-mask nulls, DM seed range,
# exact primary tail 1/9600. Every test below fails on the pre-A-2 checker.
# ---------------------------------------------------------------------------

_XS5 = [1.0, 1.25, 1.5, 1.75, 2.0]


def test_a2_exp_sign_exact_zero_five_zero_observations_give_exactly_the_asymptote():
    np = pytest.importorskip("numpy")
    for mode_fn in (cc.exp_fit_fixed,):
        v, clamped = mode_fn(_XS5, [0.0] * 5, 0.0, min_distinct=M2B)
        assert v == 0.0 and clamped                      # old checker: ~1e-6 (sign +1 via '>= 0')
    assert cc.exp_sign(_XS5, [0.0] * 5, 0.0) == 0.0
    assert cc.pinned_linear_intercept(_XS5, [0.0] * 5) == 0.0
    # avoid_log with sign 0: p0 = [0, -1]; the mode is reached through the clamp, and it uses the same sign
    assert cc.exp_fit_avoid_log(_XS5, [0.0] * 5, 0.0, min_distinct=M2B) == pytest.approx(0.0, abs=1e-8)


def test_a2_reviewer_oracle_y_equals_x_over_4_eight_seeds_goes_through_the_clamp_fallback():
    np = pytest.importorskip("numpy")
    ys = [x / 4 for x in _XS5]
    lin = cc.pinned_linear_intercept(_XS5, ys)
    assert lin == float(np.polyfit(np.array(_XS5), np.array(ys), 1)[-1])   # the pinned linear-fit convention
    assert lin < 0 and abs(lin) < 1e-15                                     # -4.97e-17 on the pinned numpy
    assert cc.exp_sign(_XS5, ys, 0.0) == -1.0                               # np.sign of the pinned intercept; the '>= 0' ternary said +1
    v, clamped = cc.exp_fit_fixed(_XS5, ys, 0.0, min_distinct=M2B)
    assert clamped
    agg, mode, flags = cc.exp_step_aggregate([(_XS5, ys)] * 8, 0.0, min_distinct=M2B)
    assert mode == "avoid_log" and agg == pytest.approx(0.1353653348, abs=1e-9)
    assert agg != pytest.approx(0.1325890835, abs=1e-6)                     # the former log-mode value


def test_a2_near_zero_and_nonzero_asymptote_follow_np_sign_of_the_pinned_intercept():
    np = pytest.importorskip("numpy")
    below = [x / 4 - 1e-9 for x in _XS5]; above = [x / 4 + 1e-9 for x in _XS5]
    assert cc.exp_sign(_XS5, below, 0.0) == -1.0 and cc.exp_sign(_XS5, above, 0.0) == 1.0
    a = 0.25
    for ys in ([a] * 5, [a + 1e-9 * x for x in _XS5], [a - 1e-9 * x for x in _XS5], [a + 0.9 * math.exp(-0.4 * x) for x in _XS5]):
        s = cc.exp_sign(_XS5, ys, a)
        assert s == float(np.sign(-(a - np.polyfit(np.array(_XS5), np.array(ys), 1)[-1])))
        v, clamped = cc.exp_fit_fixed(_XS5, ys, a, min_distinct=M2B)
        if s == 0.0:
            assert v == a and clamped
    # nonzero asymptote, clean decay: recovers a + b
    v, clamped = cc.exp_fit_fixed(_XS5, [a + 0.9 * math.exp(-0.4 * x) for x in _XS5], a, min_distinct=M2B)
    assert v == pytest.approx(a + 0.9, abs=1e-9) and not clamped


def test_a2_both_exp_modes_use_one_sign_and_the_homogeneity_branch_follows_a_sign_zero_seed():
    np = pytest.importorskip("numpy")
    rng = np.random.default_rng(5)
    for _ in range(50):
        ys = list(rng.normal(0, 0.3, 5))
        s = cc.exp_sign(_XS5, ys, 0.0)
        assert s in (-1.0, 0.0, 1.0)
        assert s == float(np.sign(-(0.0 - np.polyfit(np.array(_XS5), np.array(ys), 1)[-1])))
    clean = ([1.0, 1.5, 2.0], [0.9 * math.exp(-0.4 * x) for x in (1.0, 1.5, 2.0)])
    zero = (_XS5, [0.0] * 5)                                                # sign 0 -> every point clamped
    agg, mode, flags = cc.exp_step_aggregate([clean] * 7 + [zero], 0.0, min_distinct=M2B)
    assert mode == "avoid_log" and "CLAMP_RERUN" in flags and agg == pytest.approx(7 * 0.9 / 8, abs=1e-6)
    agg2, mode2, _ = cc.exp_step_aggregate([clean] * 8, 0.0, min_distinct=M2B)
    assert mode2 == "log" and agg2 == pytest.approx(0.9, abs=1e-9)


def test_a2_masks_of_0_1_2_and_3_steps_check_values_not_only_status():
    good = cc.phase2a_step(0.5, 0.45, 0.4, 0.36)
    below = cc.phase2a_step(0.05, 0.04, 0.03, 0.02)
    for k in (0, 1, 2):
        v, reason, stats = cc.phase2a_verdict([good] * k + [below] * (3 - k))
        assert v == "INCONCLUSIVE" and "TOO_FEW_POINTS" in reason
        assert stats is None                                                 # old checker: four finite numbers for k = 1, 2
    v3, reason3, stats3 = cc.phase2a_verdict([good] * 3)
    assert stats3 is not None and set(stats3) == {"s_rms_lo", "s_rms_hi", "s_max_lo", "s_max_hi"}
    assert stats3["s_rms_hi"] >= stats3["s_rms_lo"] >= 0 and stats3["s_max_hi"] >= stats3["s_max_lo"] >= 0
    assert "TOO_FEW_POINTS" not in reason3
    # per-step records are kept regardless of the mask size
    assert below["in_mask"] == 0 and below["r10"] is not None and good["in_mask"] == 1


def _spike(pts, peak_n, amp):
    return {n: (amp if n == peak_n else 0.0) for n in pts}


def test_a2_dm_seed_range_reviewer_counterexample_amplitude_at_the_aggregate_step():
    pts = list(range(15, 24))
    seeds = [_spike(pts, 19, 1.0)] * 4 + [_spike(pts, 21, 1.0)] * 4
    r = cc.dm_seed_range(seeds, pts, +1.0)
    assert r["matched_n"] == 19                       # aggregate 0.5 at 19 and 21: earliest tie
    assert r["amp_range"] == (0.0, 1.0)              # values at the aggregate step, not own peaks (1, 1)
    assert cc.three_way(0.0, 1.0, 0.95, 1.05) == "OVERLAP" and cc.three_way(1.0, 1.0, 0.95, 1.05) == "PASS"
    assert r["timing_range"] == (19.0, 21.0)         # each seed's own peak inside the same window
    assert r["flags"] == []


def test_a2_dm_seed_range_ties_windows_and_separate_amplitude_timing():
    pts = list(range(15, 24))
    # tie inside one seed: earliest step wins for that seed's own timing; aggregate tie also earliest
    tie = {n: (1.0 if n in (18, 20) else 0.0) for n in pts}
    r = cc.dm_seed_range([tie] * 8, pts, +1.0)
    assert r["matched_n"] == 18 and r["timing_range"] == (18.0, 18.0) and r["amp_range"] == (1.0, 1.0)
    # window restriction: a seed whose global peak lies outside the window is matched inside the window only
    outside = {n: 0.2 for n in pts}; outside[16] = 0.3
    r2 = cc.dm_seed_range([_spike(pts, 19, 1.0)] * 7 + [outside], pts, +1.0)
    assert r2["matched_n"] == 19 and r2["amp_range"] == (0.2, 1.0) and r2["timing_range"] == (16.0, 19.0)
    # polarity -1 (ZPI, MLOC): minima are peaks
    neg = {n: -v for n, v in _spike(pts, 20, 1.0).items()}
    r3 = cc.dm_seed_range([neg] * 8, pts, -1.0)
    assert r3["matched_n"] == 20 and r3["amp_range"] == (-1.0, -1.0) and r3["timing_range"] == (20.0, 20.0)
    # parabolic per-seed timings, min and max over seeds
    def para(peak, shift):
        return {n: 1.0 - 0.1 * (n - peak - shift) ** 2 for n in pts}
    r4 = cc.dm_seed_range([para(19, 0.2)] * 4 + [para(19, -0.3)] * 4, pts, +1.0)
    assert r4["timing_range"] == pytest.approx((18.7, 19.2)) and r4["amp_range"] == pytest.approx((0.991, 0.996))


def test_a2_dm_seed_range_undefined_seed_nulls_the_whole_range_never_partial():
    pts = list(range(15, 24))
    base = [_spike(pts, 19, 1.0)] * 7
    # undefined at the matched step: aggregate undefined there -> everything null
    r = cc.dm_seed_range(base + [{**_spike(pts, 19, 1.0), 19: None}], pts, +1.0)
    assert r == {"matched_n": None, "amp_range": None, "timing_range": None, "flags": ["UNDEFINED"]}
    # undefined elsewhere in the window: aggregate undefined at that step -> null (no matching on a partial aggregate)
    r2 = cc.dm_seed_range(base + [{**_spike(pts, 19, 1.0), 22: None}], pts, +1.0)
    assert r2["amp_range"] is None and r2["timing_range"] is None
    # a seed with its own peak on the window edge: NO_INTERIOR_PEAK -> timing range null, amplitude range intact
    r3 = cc.dm_seed_range(base + [_spike(pts, 23, 1.0)], pts, +1.0)
    assert r3["amp_range"] == (0.0, 1.0) and r3["timing_range"] is None and "NO_INTERIOR_PEAK" in r3["flags"]
    # seven defined seeds never form a range on their own
    assert r3["timing_range"] != (19.0, 19.0)


def test_a2_dm_seed_range_non_finite_seed_values_null_the_whole_range_like_none():
    # amendment A-2 correction (2026-09-08): +inf, -inf and NaN are undefined exactly like a missing (None) value;
    # the pre-correction checker used a None sentinel only, so float('inf') flowed through as a real value
    pts = list(range(15, 24))
    base = [_spike(pts, 19, 1.0)] * 7
    null = {"matched_n": None, "amp_range": None, "timing_range": None, "flags": ["UNDEFINED"]}
    for v in (math.inf, -math.inf, math.nan, None):
        # at the aggregate-matched step (amplitude read-out step)
        assert cc.dm_seed_range(base + [{**_spike(pts, 19, 1.0), 19: v}], pts, +1.0) == null, v
        # elsewhere in the window (aggregate step, timing path of that seed)
        assert cc.dm_seed_range(base + [{**_spike(pts, 19, 1.0), 22: v}], pts, +1.0) == null, v
        assert cc.dm_seed_range(base + [{**_spike(pts, 19, 1.0), 15: v}], pts, +1.0) == null, v
    # mixed +inf / -inf across two seeds
    mixed = base[:6] + [{**_spike(pts, 19, 1.0), 16: math.inf}, {**_spike(pts, 19, 1.0), 22: -math.inf}]
    assert cc.dm_seed_range(mixed, pts, +1.0) == null
    # a single infinite seed inside a parabolic (interpolated-timing) window
    def para(peak, shift):
        return {n: 1.0 - 0.1 * (n - peak - shift) ** 2 for n in pts}
    for v in (math.inf, -math.inf):
        assert cc.dm_seed_range([para(19, 0.2)] * 4 + [para(19, -0.3)] * 3 + [{**para(19, -0.3), 18: v}], pts, +1.0) == null
    # the surviving seven seeds alone would form (1.0, 1.0) / (19.0, 19.0): that range is never reported
    assert cc.dm_seed_range(base, pts, +1.0)["amp_range"] == (1.0, 1.0)
    # a non-finite value OUTSIDE the window is not a required value
    r = cc.dm_seed_range(base + [{**_spike(pts, 19, 1.0), 40: math.inf}], pts, +1.0)
    assert r["matched_n"] == 19 and r["amp_range"] == (1.0, 1.0) and r["timing_range"] == (19.0, 19.0)
    assert cc.seed_value_undefined(True) and cc.seed_value_undefined("1.0") and not cc.seed_value_undefined(0.0)


def test_a2_exact_primary_tail_probability_tolerates_four_undefined_not_five():
    B = 48000
    base = [0.01 * math.sin(i) for i in range(B)]
    for u, ok in ((4, True), (5, False)):
        vals = [None] * u + base[u:]
        lo, hi, uu, fl = cc.percentile_interval(vals, 1.0 / 9600.0, 1.0 - 1.0 / 9600.0)
        assert uu == u and (("UNDEFINED" not in fl) == ok)
    # the rounded prose value would wrongly tolerate five
    lo, hi, uu, fl = cc.percentile_interval([None] * 5 + base[5:], 1.0417e-4, 1 - 1.0417e-4)
    assert "UNDEFINED" not in fl
    assert 0.05 / 480 == 1.0 / 9600.0


# ---- mutants restoring each rejected behaviour -------------------------------------------------

_SIGN_SRC = 'return float(np.sign(-(asymptote - pinned_linear_intercept(xs, ys))))'
_SIGN_OLD = 'return 1.0 if poly_intercept(xs, ys, 1) - asymptote >= 0 else -1.0  # MUTANT: the rejected ternary on the closed-form intercept'
_GATE_SRC = 'if len(masked) >= k_min and all(r["i_n"] is not None and r["eta_i"] is not None for r in masked):'
_GATE_OLD = 'if masked and all(r["i_n"] is not None and r["eta_i"] is not None for r in masked):  # MUTANT: non-empty gate'
_AGG_SRC = '        agg[n] = None if any(seed_value_undefined(v) for v in vals) else sum(vals) / K'
_AGG_OLD = '        _d = [v for v in vals if not seed_value_undefined(v)]; agg[n] = sum(_d) / len(_d) if _d else None  # MUTANT: survivor aggregate'
_RANGE_SRC = '    amp_range = None if any(seed_value_undefined(a) for a in amps) else (min(amps), max(amps))'
_RANGE_OLD = '    _d = [a for a in amps if not seed_value_undefined(a)]; amp_range = (min(_d), max(_d)) if _d else None  # MUTANT: survivor range'
_TIMING_SRC = '    timing_range = None if any(t is None for t in ts) else (min(ts), max(ts))'
_TIMING_OLD = '    _t = [t for t in ts if t is not None]; timing_range = (min(_t), max(_t)) if _t else None  # MUTANT: survivor timing range'
_FINITE_SRC = 'return v is None or isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)'
_FINITE_OLD = 'return v is None  # MUTANT: the pre-correction None sentinel; infinities pass as values'


def test_a2_mutant_ternary_sign_is_caught_by_the_exact_zero_and_oracle_tests(tmp_path):
    # the pre-A-2 behaviour had two parts: the '>= 0' ternary AND the closed-form (normal-equation) intercept;
    # restoring both at the ONE shared sign site (exp_sign, called by both EXP modes) reproduces the Reviewer's
    # rejected values exactly. Coverage actually demonstrated: mutant checker versus corrected checker on the
    # exact-zero and y = x/4 oracles. NOT demonstrated (and not claimed): a disagreement between the mutant's own
    # two modes; since both modes call the shared exp_sign, the mutant changes both of them together.
    src = CHECKER.read_text(encoding="utf-8")
    assert src.count(_SIGN_SRC) == 1
    mut = _load_mutant_checker(tmp_path, lambda s: s.replace(_SIGN_SRC, _SIGN_OLD, 1))
    v, _ = mut.exp_fit_fixed(_XS5, [0.0] * 5, 0.0, min_distinct=M2B)
    assert v != 0.0 and v == pytest.approx(1e-6, abs=1e-9)                 # the old ~1e-6
    ys = [x / 4 for x in _XS5]
    agg, mode, _ = mut.exp_step_aggregate([(_XS5, ys)] * 8, 0.0, min_distinct=M2B)
    assert mode == "log" and agg == pytest.approx(0.1325890835, abs=1e-9)   # the old log-mode value
    with pytest.raises(AssertionError):
        assert mut.exp_sign(_XS5, ys, 0.0) == cc.exp_sign(_XS5, ys, 0.0)
    # exact zero: the mutant's shared sign is +1 where the corrected checker's is 0 (mutant vs corrected, not mode vs mode)
    assert mut.exp_sign(_XS5, [0.0] * 5, 0.0) == 1.0 and cc.exp_sign(_XS5, [0.0] * 5, 0.0) == 0.0
    # both mutant modes route through the single mutated site, so the mutation reaches log mode AND avoid_log
    msrc = (tmp_path / "mutant_checker.py").read_text(encoding="utf-8")
    assert msrc.count("sigma = exp_sign(xs, ys, asymptote)") == 1 and msrc.count("sign = exp_sign(xs, ys, asymptote)") == 1
    assert "MUTANT: the rejected ternary" in msrc


def test_a2_mutant_non_empty_mask_gate_is_caught_by_the_value_assertions(tmp_path):
    src = CHECKER.read_text(encoding="utf-8")
    assert src.count(_GATE_SRC) == 1
    mut = _load_mutant_checker(tmp_path, lambda s: s.replace(_GATE_SRC, _GATE_OLD, 1))
    good = mut.phase2a_step(0.5, 0.45, 0.4, 0.36); below = mut.phase2a_step(0.05, 0.04, 0.03, 0.02)
    v, reason, stats = mut.phase2a_verdict([good, good, below])
    assert v == "INCONCLUSIVE" and "TOO_FEW_POINTS" in reason                # status alone would not catch it
    assert stats is not None                                                # the mutant reports four numbers
    with pytest.raises(AssertionError):
        assert stats is None


def test_a2_mutant_survivor_aggregate_and_amplitude_range_is_caught(tmp_path):
    # Survivor mutation with REACHABLE behaviour change (replaces the ineffective 2026-09-08 test that asserted
    # r_ok == r_mut). The amplitude-range line alone is unreachable: the aggregate is defined at n_hat only when
    # every seed is defined there, so that single-line mutant never changes an output and is NOT counted as
    # coverage. Survivor averaging has to enter at the aggregate step for a survivor amplitude range to exist,
    # so the mutant is the two-line "average / range over the defined seeds" rule; the contract-required
    # output is the null range, the mutant reports the forbidden survivor range.
    src = CHECKER.read_text(encoding="utf-8")
    assert src.count(_AGG_SRC) == 1 and src.count(_RANGE_SRC) == 1
    mut = _load_mutant_checker(tmp_path, lambda s: s.replace(_AGG_SRC, _AGG_OLD, 1).replace(_RANGE_SRC, _RANGE_OLD, 1))
    pts = list(range(15, 24))
    for v in (None, math.inf, -math.inf, math.nan):
        seeds = [_spike(pts, 19, 1.0)] * 7 + [{**_spike(pts, 19, 1.0), 19: v}]
        r_ok = cc.dm_seed_range(seeds, pts, +1.0)
        r_mut = mut.dm_seed_range(seeds, pts, +1.0)
        assert r_ok == {"matched_n": None, "amp_range": None, "timing_range": None, "flags": ["UNDEFINED"]}
        assert r_mut["matched_n"] == 19 and r_mut["amp_range"] == (1.0, 1.0), (v, r_mut)   # the forbidden survivor range
        assert r_ok != r_mut
        with pytest.raises(AssertionError):
            assert r_mut["amp_range"] is None                                    # the oracle assertion the mutant fails
    # with every seed defined the mutant and the checker coincide, so only the undefined-seed inputs discriminate
    full = [_spike(pts, 19, 1.0)] * 4 + [_spike(pts, 21, 1.0)] * 4
    assert cc.dm_seed_range(full, pts, +1.0) == mut.dm_seed_range(full, pts, +1.0)


def test_a2_mutant_survivor_timing_range_is_caught(tmp_path):
    # single-line survivor mutation on the timing branch: reachable through a seed whose own matched peak sits on
    # the window edge (NO_INTERIOR_PEAK), because the aggregate and every amplitude stay defined there
    src = CHECKER.read_text(encoding="utf-8")
    assert src.count(_TIMING_SRC) == 1
    mut = _load_mutant_checker(tmp_path, lambda s: s.replace(_TIMING_SRC, _TIMING_OLD, 1))
    pts = list(range(15, 24))
    seeds = [_spike(pts, 19, 1.0)] * 7 + [_spike(pts, 23, 1.0)]
    r_ok = cc.dm_seed_range(seeds, pts, +1.0); r_mut = mut.dm_seed_range(seeds, pts, +1.0)
    assert r_ok["timing_range"] is None and "NO_INTERIOR_PEAK" in r_ok["flags"] and r_ok["amp_range"] == (0.0, 1.0)
    assert r_mut["timing_range"] == (19.0, 19.0)                                # the forbidden seven-seed survivor range
    assert r_ok != r_mut
    with pytest.raises(AssertionError):
        assert r_mut["timing_range"] is None


def test_a2_mutant_none_sentinel_lets_infinities_through_and_is_caught(tmp_path):
    # the pre-correction rule (None sentinel only): +inf / -inf flow through as values; the corrected checker nulls them
    src = CHECKER.read_text(encoding="utf-8")
    assert src.count(_FINITE_SRC) == 1
    mut = _load_mutant_checker(tmp_path, lambda s: s.replace(_FINITE_SRC, _FINITE_OLD, 1))
    pts = list(range(15, 24))
    base = [_spike(pts, 19, 1.0)] * 7
    null = {"matched_n": None, "amp_range": None, "timing_range": None, "flags": ["UNDEFINED"]}
    pos = base + [{**_spike(pts, 19, 1.0), 19: math.inf}]
    r_mut = mut.dm_seed_range(pos, pts, +1.0)
    assert cc.dm_seed_range(pos, pts, +1.0) == null
    assert r_mut["matched_n"] == 19 and r_mut["amp_range"] == (1.0, math.inf)      # an infinite "range"
    neg = base + [{**_spike(pts, 19, 1.0), 19: -math.inf}]
    r_mut2 = mut.dm_seed_range(neg, pts, +1.0)
    assert cc.dm_seed_range(neg, pts, +1.0) == null
    assert r_mut2["matched_n"] == 15 and r_mut2["amp_range"] == (0.0, 0.0)        # -inf drags the aggregate; a wrong finite range
    for r in (r_mut, r_mut2):
        with pytest.raises(AssertionError):
            assert r == null


def test_a2_json_and_document_regressions_are_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    _mutate_json(root, lambda d: d.__setitem__("amendments", [a for a in d["amendments"] if a["id"] != "A-2"]))
    res = _run_on(root)
    assert res[next(k for k in res if k.startswith("a2: dated amendment A-2"))][0] is False
    root2 = _copy_tree(tmp_path / "b")
    _mutate_text(root2, "docs/phase2-analysis-contract.md", "the sign $\\sigma$ is `np.sign` of the linear intercept minus $a$", "the sign $\\sigma$ is the sign of the linear intercept minus $a$")
    res2 = _run_on(root2)
    assert res2[next(k for k in res2 if k.startswith("a2: EXP sign convention"))][0] is False
    root3 = _copy_tree(tmp_path / "c")
    _mutate_text(root3, "docs/phase2-analysis-contract.md", "and the mask holds at least $k_{\\min} = 3$ steps (amendment A-2", "and the mask is non-empty (amendment A-2")
    res3 = _run_on(root3)
    assert res3[next(k for k in res3 if k.startswith("a2: small-mask rule"))][0] is False
    root4 = _copy_tree(tmp_path / "d")
    _mutate_json(root4, lambda d: d["constants"]["C-CI-Q-PRIMARY"].__setitem__("value", [1.0417e-4, 1 - 1.0417e-4]))
    res4 = _run_on(root4)
    assert res4[next(k for k in res4 if k.startswith("a2: the primary tail probability"))][0] is False
    root5 = _copy_tree(tmp_path / "e")
    _mutate_json(root5, lambda d: d["phase2b"].__setitem__("dm_companion", "deterministic seed range [min_s, max_s]"))
    res5 = _run_on(root5)
    assert res5[next(k for k in res5 if k.startswith("a2: DM companion seed range"))][0] is False


def test_degenerate_bootstrap_and_saturated_counts_never_pass():
    lo, hi, _, flags = cc.percentile_interval([0.3] * 2000, 0.025, 0.975)
    assert "DEGENERATE_CONSTANT" in flags and lo == hi == 0.3
    assert cc.three_way(lo, hi, 0.2, 0.4, undefined=True) == "INDETERMINATE"
    assert cc.resample_counts([4096, 0], 4096, cc.bootstrap_rng(3, 0, 7)) == [4096, 0]
    # Reviewer round-03 finding 1: the collapse rule is on the half-width (prereg §6.7)
    span = [1.5e-12 * i / 1999 for i in range(2000)]
    lo2, hi2, _, fl2 = cc.percentile_interval(span, 0.025, 0.975)
    assert 0.5 * (hi2 - lo2) < 1e-12 and "DEGENERATE_COLLAPSED" in fl2


def test_decision_functions_reject_invalid_or_incomplete_input():
    # Reviewer round-03 finding 1
    for bad in ([], ["PASS"] * 3, ["PASS"] * 5, ["PASS", "PASS", "PASS", "MAYBE"],
                {"ZPI_AMP": "PASS", "ZPI_TIME": "PASS", "PRET_AMP": "PASS"}):
        with pytest.raises(ValueError):
            cc.condition_status(bad)
    assert cc.condition_status({"ZPI_AMP": "PASS", "ZPI_TIME": "PASS", "PRET_AMP": "PASS", "PRET_TIME": "PASS"}) == "PASS"
    g = [0.25, 0.5, 1.0, 2.0, 4.0]
    for bad in ([], ["PASS"], {0.25: "PASS", 0.5: "PASS"}, ["PASS", "PASS", "PASS", "PASS", "WHAT"]):
        with pytest.raises(ValueError):
            cc.boundary(bad, g)
    with pytest.raises(ValueError):
        cc.boundary([], [])
    assert cc.boundary({k: "PASS" for k in g}, g)["kappa_star"] == "AT_OR_ABOVE_MAX"
    with pytest.raises(ValueError):
        cc.three_way(0.8, 0.2, 0.0, 1.0)  # inverted interval never passes
    with pytest.raises(ValueError):
        cc.three_way(0.2, 0.8, 1.0, 0.0)
    with pytest.raises(ValueError):
        cc.three_way(float("nan"), 0.8, 0.0, 1.0)


def test_mask_boundary_reference_blocks_verdict_and_operative_secondary_fit():
    ambiguous = dict(cc.phase2a_step(0.1 + 1e-10, 0.09, 0.08, 0.07), n=1)
    good = dict(cc.phase2a_step(0.5, 0.45, 0.4, 0.36), n=2)
    good2 = dict(good, n=3)
    assert "MASK_BOUNDARY" in ambiguous["flags"] and ambiguous["in_mask"] == 1  # membership untouched
    verdict, reason, _ = cc.phase2a_verdict([ambiguous, good, good2])
    assert verdict == "INCONCLUSIVE" and "MASK_BOUNDARY" in reason
    sec = cc.secondary_fit([ambiguous, good, good2], "10", ["MASK_BOUNDARY"])
    assert sec["fit_available"] == 0 and sec["reason"] == ["MASK_BOUNDARY"]
    exactly_at = cc.phase2a_step(0.1, 0.09, 0.08, 0.07)
    assert exactly_at["in_mask"] == 1 and "MASK_BOUNDARY" in exactly_at["flags"]


def test_timing_floor_three_point_bound_and_five_point_testability():
    worst = 0.0
    for a in (0.001, 0.01, 0.1, 0.5, 1.0, 2.0, 10.0):
        for b in (0.0, 0.001, 0.01, 0.1, 0.5, 1.0, 2.0, 10.0):
            off, fallback = cc.parabolic_timing(1 - a, 1.0, 1 - b)
            if not fallback:
                worst = max(worst, abs(off))
                assert off == pytest.approx((a - b) / (2 * (a + b)))
    assert worst <= 0.5 + 1e-12
    assert cc.timing_testable([19, 20, 21], 20) is False
    assert cc.timing_testable([18, 19, 20, 21, 22], 20) is True
    # Supervisor's informative alternative: values [0, 0, 0, 3, 2] on 18..22 -> matched 21, offset +0.25, timing 21.25
    curve = dict(zip([18, 19, 20, 21, 22], [0.0, 0.0, 0.0, 3.0, 2.0]))
    m = cc.match_peak(curve, [18, 19, 20, 21, 22])
    assert m["matched_n"] == 21 and m["timing"] == pytest.approx(21.25)
    assert cc.three_way(21.2, 21.3, 19.0, 21.0) == "FAIL"  # disjoint from 20 ± 1
    # on a three-point window the same excursion is not even observable
    m3 = cc.match_peak({19: 0.0, 20: 0.0, 21: 3.0}, [19, 20, 21])
    assert "NO_INTERIOR_PEAK" in m3["flags"] and m3["timing"] is None


def test_undefined_replicate_tail_counts_at_reported_and_adjusted_levels():
    cases = {(48000, 1.0 / 9600.0): 4, (2000, 0.00625): 12, (2000, 0.025): 49}
    for (B, q), allowed in cases.items():
        base = [0.01 * math.sin(i) for i in range(B)]
        ok_lo, ok_hi, _, fl_ok = cc.percentile_interval(base[: B - allowed] + [None] * allowed, q, 1 - q)
        assert "UNDEFINED" not in fl_ok and math.isfinite(ok_lo) and math.isfinite(ok_hi)
        _, _, _, fl_bad = cc.percentile_interval(base[: B - allowed - 1] + [None] * (allowed + 1), q, 1 - q)
        assert "UNDEFINED" in fl_bad
        # alternating placement (rejected) would still yield a finite interval with twice as many unknowns
        alt = base[: B - 2 * allowed] + [None] * (2 * allowed)
        alo, ahi = cc.alternating_interval(alt, q, 1 - q)
        _, _, _, fl_cons = cc.percentile_interval(alt, q, 1 - q)
        assert math.isfinite(alo) and math.isfinite(ahi) and "UNDEFINED" in fl_cons


def test_reviewer_counts_8_of_48000_and_24_of_2000_are_rejected_by_the_conservative_rule():
    base = [0.01 * math.sin(i) for i in range(48000)]
    assert "UNDEFINED" in cc.percentile_interval(base[:-8] + [None] * 8, 0.05 / 480, 1 - 0.05 / 480)[3]
    base2 = [0.01 * math.sin(i) for i in range(2000)]
    assert "UNDEFINED" in cc.percentile_interval(base2[:-24] + [None] * 24, 0.00625, 1 - 0.00625)[3]


def test_three_way_rule_and_physical_range():
    assert cc.three_way(0.0, 0.1, 0.0, 0.1) == "PASS"  # closed edges
    assert cc.three_way(0.05, 0.15, 0.0, 0.1) == "OVERLAP"
    assert cc.three_way(0.2, 0.3, 0.0, 0.1) == "FAIL"
    assert cc.three_way(1.4, 1.6, 0.95, 1.05, 0.0, 1.0) == "FAIL"
    assert cc.three_way(0.98, 1.02, 0.95, 1.05, 0.0, 1.0) == "OVERLAP"  # unphysical interval never passes
    assert cc.three_way(0.98, 1.0, 0.95, 1.05, 0.0, 1.0) == "PASS"
    assert cc.three_way(0.0, 0.1, 0.0, 0.1, untestable=True) == "INDETERMINATE"


def test_condition_status_truth_table():
    assert cc.condition_status(["FAIL", "INDETERMINATE", "PASS", "PASS"]) == "FAIL"
    assert cc.condition_status(["PASS"] * 4) == "PASS"
    assert cc.condition_status(["PASS", "OVERLAP", "PASS", "PASS"]) == "OVERLAP"
    assert cc.condition_status(["PASS", "OVERLAP", "INDETERMINATE", "PASS"]) == "INDETERMINATE"
    assert cc.condition_status(["PASS"] * 4, unavailable=True) == "UNAVAILABLE"


def test_boundary_classification():
    g = [0.25, 0.5, 1.0, 2.0, 4.0]
    assert cc.boundary(["PASS", "PASS", "FAIL", "FAIL", "FAIL"], g) == {"kappa_star": 0.5, "located": 1, "non_monotone": 0}
    assert cc.boundary(["PASS", "PASS", "OVERLAP", "FAIL", "FAIL"], g)["located"] == 0
    b = cc.boundary(["FAIL", "FAIL", "PASS", "FAIL", "FAIL"], g)
    assert b["kappa_star"] == "BELOW_MIN_FAIL" and b["non_monotone"] == 1
    assert cc.boundary(["INDETERMINATE"] + ["FAIL"] * 4, g)["kappa_star"] == "UNRESOLVED_AT_MIN"
    assert cc.boundary(["PASS"] * 5, g)["kappa_star"] == "AT_OR_ABOVE_MAX"


def test_three_near_tied_projector_weights_have_a_deterministic_total_order():
    ws = [0.5, 0.5 + 0.75e-12, 0.5 + 1.5e-12]
    idx, marginal = cc.order_weights(ws, [1.0, 2.0, 3.0])
    assert idx == [2, 1, 0] and len(marginal) == 2
    # exact ties fall back to energy then index, still a total order
    idx2, _ = cc.order_weights([0.5, 0.5, 0.5], [3.0, 1.0, 2.0])
    assert idx2 == [1, 2, 0]
    # a within-tolerance "tie" relation would be non-transitive: 0 ~ 1 and 1 ~ 2 but not 0 ~ 2
    assert abs(ws[0] - ws[1]) <= 1e-12 and abs(ws[1] - ws[2]) <= 1e-12 and abs(ws[0] - ws[2]) > 1e-12


def test_ratio_rule_cases():
    assert cc.ratio_rule(0.2, 0.4) == (pytest.approx(0.5), "")
    assert cc.ratio_rule(0.2, 1e-10)[1] == "RATIO_LOWER_BOUND"
    assert cc.ratio_rule(1e-10, 1e-10) == (None, "RATIO_ZERO_OVER_ZERO")
    assert cc.ratio_rule(float("nan"), 1.0) == (None, "RATIO_UNDEFINED")


def test_windows_truncate_at_the_midpoint_and_stay_disjoint():
    wins = cc.make_windows([19, 26], w=4, n_max=48)
    assert "WINDOW_TRUNCATED" in wins[0]["flags"] and not set(wins[0]["points"]) & set(wins[1]["points"])
    assert wins[0]["points"][-1] == 22 and wins[1]["points"][0] == 23
    far = cc.make_windows([19, 39], w=4, n_max=48)
    assert far[0]["flags"] == [] and far[0]["timing_testable"] and far[1]["points"][-1] == 43


# ---------------------------------------------------------------------------
# executable hardware, lifecycle, root-policy and selector rules (Reviewer round-03 finding 4, 5, 8)
# ---------------------------------------------------------------------------


def test_fit_predicate_and_gate_conditions_from_the_contract_parameters():
    K = json.loads((ROOT / "tools/phase2_contract.json").read_text(encoding="utf-8"))["constants"]
    t_lim, t_cap, t_open = K["C-T-LIM"]["value"], K["C-QPU-CAP"]["value"], K["C-OPEN-ALLOWANCE"]["value"]
    assert (t_lim, t_cap, t_open) == (479, 480, 600) and K["C-MAX-EXEC"]["value"] == t_lim
    assert not cc.fits(479.0, t_lim) and not cc.fits(479.5, t_lim) and cc.fits(478.99, t_lim)
    g = cc.gate_conditions(340.0, 0.0, 1.0, t_lim, t_cap, t_open)
    assert g["submit"] and g["reserve_after_s"] == 120
    assert not cc.gate_conditions(340.0, 0.5, 0.6, t_lim, t_cap, t_open)["condition_b"]
    assert not cc.gate_conditions(479.0, 0.0, 0.0, t_lim, t_cap, t_open)["condition_a"]
    assert not cc.gate_conditions(340.0, 0.0, 0.0, t_lim, t_cap, t_open, nothing_else_planned=False)["submit"]
    est = cc.usage_estimate([220e-6] * 144, 4096, 250e-6, 10e-6)
    assert est["t_est_1_s"] == pytest.approx(341.7, abs=0.06) and est["t_est_cons_s"] == pytest.approx(627.7, abs=0.06)
    assert not cc.fits(est["t_est_cons_s"], t_lim)


def test_schedule_and_reduction_keep_both_revival_one_windows_testable():
    sch = cc.hardware_schedule(19, 19, 39, 39, 10)
    assert sch["points"] == [1, 10, 17, 18, 19, 20, 21, 37, 38, 39, 40, 41] and sch["e1_subset_ok"]
    assert all(sch["windows"][k]["timing_testable"] for k in ("ZPI_1", "PRET_1"))
    sch2 = cc.hardware_schedule(19, 21, 39, 39, 10)
    assert len(sch2["points"]) <= 12 and set(sch2["C1"]) <= set(sch2["points"]) and sch2["windows"]["PRET_1"]["timing_testable"]
    dur = lambda n, lam: 220e-6 * (0.5 + 0.5 * lam)
    red = cc.reduction_policy(sch["points"], sch["E1"], sch["E2"], [38, 39, 40], 10, 4, 4096, dur, 250e-6, 10e-6, 479.0)
    assert not red["abandoned"] and set(sch["E1"]) <= set(red["points"]) and cc.fits(red["t_est_cons_s"])
    red2 = cc.reduction_policy(sch["points"], sch["E1"], sch["E2"], [38, 39, 40], 10, 4, 4096, lambda n, lam: 5e-2, 250e-6, 10e-6, 479.0)
    assert red2["abandoned"] and set(sch["E1"]) <= set(red2["points"]) and red2["shots"] == 1024 and red2["folds"] == 2
    # a step that would remove a revival-1 extended-window point is skipped, never applied
    assert not any(s.get("applied") and not set(sch["E1"]) <= set(red2["points"]) for s in red2["applied"])


def test_frozen_mask_survives_missing_noisy_values_and_no_survivor_fit():
    # Reviewer round-05 finding 1: E00 = 0.5 throughout, E10 missing at step 3
    rows = [dict(cc.phase2a_step(0.5, None if n == 3 else 0.5 * math.exp(-0.05 * n), 0.5 * math.exp(-0.1 * n), 0.5 * math.exp(-0.15 * n)), n=n) for n in range(1, 6)]
    assert [r["in_mask"] for r in rows] == [1] * 5            # mask from the reference only; step 3 stays masked
    assert rows[2]["flags_by_cell"] == {"10": ["MISSING_OR_NONFINITE"], "01": [], "11": []}
    assert rows[2]["r01"] is not None and rows[2]["r11"] is not None  # the other cells' values are preserved
    f10 = cc.secondary_fit(rows, "10", [])
    assert f10["fit_available"] == 0 and f10["violating_steps"] == [2]   # its own cell only, no four-point survivor fit
    f01, f11 = cc.secondary_fit(rows, "01", []), cc.secondary_fit(rows, "11", [])
    assert f01["fit_available"] == 1 and f11["fit_available"] == 1
    assert f01["g_raw"] == pytest.approx(0.1, abs=1e-12) and f01["residual_status"] == "RESIDUAL_ADEQUATE"
    assert cc.phase2a_verdict(rows)[0] == "INCONCLUSIVE"  # the primary is blocked by MISSING_OR_NONFINITE
    # non-finite input behaves the same as missing
    rows_nan = [dict(cc.phase2a_step(0.5, float("nan") if n == 3 else 0.5, 0.5 * math.exp(-0.1 * n), 0.4), n=n) for n in range(1, 6)]
    assert [r["in_mask"] for r in rows_nan] == [1] * 5 and rows_nan[2]["flags_by_cell"]["10"] == ["MISSING_OR_NONFINITE"]
    assert cc.secondary_fit(rows_nan, "10", [])["fit_available"] == 0 and cc.secondary_fit(rows_nan, "01", [])["fit_available"] == 1
    # a missing reference is a size-wide loss: no cell can fit, and the mask is undefined at that step
    rows_ref = [dict(cc.phase2a_step(None if n == 3 else 0.5, 0.45, 0.4, 0.36), n=n) for n in range(1, 6)]
    assert rows_ref[2]["in_mask"] == 0 and "00" in rows_ref[2]["flags_by_cell"]
    assert all(cc.secondary_fit(rows_ref, ce, [])["fit_available"] == 0 for ce in ("10", "01", "11"))


def test_residual_concealment_fixture_from_the_reviewer():
    # Reviewer round-05 finding 1: with E10 missing at step 3, halving the valid E01 at that step must NOT
    # be hidden: the five-point fit of cell 01 has maximum residual 0.5545177444 and is RESIDUAL_INADEQUATE
    rows = [dict(cc.phase2a_step(0.5, None if n == 3 else 0.5 * math.exp(-0.05 * n),
                                 0.5 * math.exp(-0.1 * n) * (0.5 if n == 3 else 1.0), 0.5 * math.exp(-0.15 * n)), n=n) for n in range(1, 6)]
    f01 = cc.secondary_fit(rows, "01", [])
    assert f01["fit_available"] == 1 and len(f01["residuals"]) == 5
    assert f01["max_abs_residual"] == pytest.approx(0.5545177444, abs=1e-9)
    assert f01["residual_status"] == "RESIDUAL_INADEQUATE"


def test_calibration_changes_are_typed_per_field_and_never_compared_across_units():
    pre = {"qubit[3].T1": 100e-6, "gate[ecr][3,4].error": 0.010, "qubit[4].readout_error": 0.0}
    post = {"qubit[3].T1": 120e-6, "gate[ecr][3,4].error": 0.011, "qubit[4].readout_error": 0.02}
    units = {"qubit[3].T1": "s", "gate[ecr][3,4].error": "dimensionless", "qubit[4].readout_error": "dimensionless"}
    rows, summary = cc.calibration_changes(pre, post, units)
    by = {r["field"]: r for r in rows}
    assert by["qubit[3].T1"]["abs_change"] == pytest.approx(2e-5) and by["qubit[3].T1"]["rel_change"] == pytest.approx(0.2) and by["qubit[3].T1"]["unit"] == "s"
    assert by["gate[ecr][3,4].error"]["abs_change"] == pytest.approx(0.001) and by["gate[ecr][3,4].error"]["rel_change"] == pytest.approx(0.1)
    assert by["qubit[4].readout_error"]["rel_change"] is None and by["qubit[4].readout_error"]["zero_pre"] == 1
    assert summary["calib_max_abs_by_unit"]["s"]["field"] == "qubit[3].T1" and summary["calib_max_abs_by_unit"]["dimensionless"]["field"] == "qubit[4].readout_error"
    assert summary["calib_max_rel_field"] == "qubit[3].T1" and summary["calib_zero_pre_fields"] == ["qubit[4].readout_error"]
    assert "calib_max_abs_change" not in summary  # no maximum across incommensurable quantities exists
    assert by["qubit[4].readout_error"]["status"] == "ZERO_PRE" and by["qubit[3].T1"]["status"] == "PRESENT"


def test_chart_coordinates_and_x_binding_mutations_are_rejected(tmp_path):
    root = _copy_tree(tmp_path)

    def wrong_x(d):
        for ch in d["charts"]:
            if ch["id"] == "CH-B9":
                for p in ch["panels"]:
                    p["x"]["column"] = "cx"

    _mutate_json(root, wrong_x)
    res = _run_on(root)
    assert res[next(k for k in res if k.startswith("schema: every panel x column is bound"))][0] is False
    root2 = _copy_tree(tmp_path / "b")

    def wrong_y(d):
        for ch in d["charts"]:
            if ch["id"] == "CH-B1":
                ch["panels"][0]["series"][2]["column"] = "flags"  # a string column plotted as a value

    _mutate_json(root2, wrong_y)
    res2 = _run_on(root2)
    assert res2[next(k for k in res2 if k.startswith("schema: chart coordinates extracted"))][0] is False
    root3 = _copy_tree(tmp_path / "c")

    def broken_join(d):
        for ch in d["charts"]:
            if ch["id"] == "CH-B9":
                for p in ch["panels"]:
                    p["x"]["join_on"] = ["cell_index", "n"]  # ambiguous join: several fold seeds and scale factors per (cell, n)

    _mutate_json(root3, broken_join)
    res3 = _run_on(root3)
    assert res3[next(k for k in res3 if k.startswith("schema: chart coordinates extracted"))][0] is False


def test_prose_output_lists_are_compared_inside_the_entrypoint_section(tmp_path):
    root = _copy_tree(tmp_path)
    p = root / "docs/phase2-analysis-contract.md"
    text = p.read_text(encoding="utf-8")
    text = text.replace("Outputs: B-RAWSHOTOBS, B-SEEDFIT,", "Outputs: B-SEEDFIT,", 1)
    p.write_text(text, encoding="utf-8")
    res = _run_on(root)
    assert res[next(k for k in res if k.startswith("schema: each future entrypoint's operative prose output list"))][0] is False


def test_chart_paths_are_distinct_across_the_complete_family_expansion(tmp_path):
    import itertools
    d = json.loads((ROOT / "tools/phase2_contract.json").read_text(encoding="utf-8"))
    paths = []
    for ch in d["charts"]:
        fam = ch["family_params"]
        keys = list(fam)
        for k in keys:
            assert "{%s}" % k in ch["file_pattern"], (ch["id"], k)
        for combo in (itertools.product(*[fam[k] for k in keys]) if keys else [()]):
            for fmt in ch["formats"]:
                paths.append(ch["file_pattern"].format(**dict(zip(keys, combo)), fmt=fmt))
    assert len(paths) == len(set(paths)) == 2 * d["charts_total_files_per_format"] == 1692
    # Reviewer round-06 finding 2: a pattern that drops a family parameter must be rejected
    root = _copy_tree(tmp_path)
    _mutate_json(root, lambda dd: next(c for c in dd["charts"] if c["id"] == "CH-A5").__setitem__("file_pattern", "figures-phase2/CH-A5_{L}.{fmt}"))
    res = _run_on(root)
    assert res[next(k for k in res if k.startswith("schema: expanding every chart family"))][0] is False


def test_lower_bound_values_are_drawn_at_their_bound_not_lost():
    # Reviewer round-06 finding 1: er = None with RATIO_LOWER_BOUND and er_bound = 2e8 -> triangle at 2e8
    d = json.loads((ROOT / "tools/phase2_contract.json").read_text(encoding="utf-8"))
    ch = next(c for c in d["charts"] if c["id"] == "CH-B5")
    pnl = ch["panels"][0]
    ser = next(s for s in pnl["series"] if s["name"] == "er_lin")
    cells = d["phase2b"]["matrix_cells"]
    cell = next(x for x in cells if x["L"] == 6 and x["noise_model"] == "DEP" and x["folding"] == "LOCAL" and x["kappa"] == 1.0)
    base = {"cell_index": cell["cell_index"], "extrapolator": "LIN", "obs": "ZPI"}
    rows = [dict(base, n=19, er=None, er_flag="RATIO_LOWER_BOUND", er_bound=200000000),
            dict(base, n=20, er=None, er_flag="RATIO_ZERO_OVER_ZERO", er_bound=None),
            dict(base, n=21, er=None, er_flag="RATIO_UNDEFINED", er_bound=None),
            dict(base, n=22, er=0.3, er_flag="", er_bound=None)]
    params = {"L": 6, "model": "DEP", "folding": "LOCAL", "kappa": 1.0, "obs": "ZPI"}
    pts = {p["x"]: p for p in cc.chart_points(ser, pnl, params, {"B-STEPMET": rows}, cells, [], {})}
    assert pts[19] == {"x": 19, "y": 200000000, "marker": "triangle_up", "flag": "RATIO_LOWER_BOUND", "value_state": "bound"}
    assert pts[20]["y"] is None and pts[20]["marker"] == "hollow_floor" and pts[20]["value_state"] == "unavailable" and pts[21]["marker"] == "hollow_floor"
    assert pts[22] == {"x": 22, "y": 0.3, "marker": "filled", "flag": "", "value_state": "value"}
    ur = next(s for p in ch["panels"] for s in p["series"] if s["name"] == "ur_lin")
    ur_pnl = next(p for p in ch["panels"] if any(s["name"] == "ur_lin" for s in p["series"]))
    upts = cc.chart_points(ur, ur_pnl, params, {"B-STEPMET": [dict(base, n=19, ur=None, ur_flag="RATIO_LOWER_BOUND", ur_bound=7.5)]}, cells, [], {})
    assert upts == [{"x": 19, "y": 7.5, "marker": "triangle_up", "flag": "RATIO_LOWER_BOUND", "value_state": "bound"}]
    with pytest.raises(ValueError):
        cc.chart_points(ser, pnl, params, {"B-STEPMET": [dict(base, n=19, er=None, er_flag="NOT_A_FLAG", er_bound=1.0)]}, cells, [], {})


def _chart(cid):
    d = json.loads((ROOT / "tools/phase2_contract.json").read_text(encoding="utf-8"))
    return d, next(c for c in d["charts"] if c["id"] == cid)


def test_every_value_rule_reference_is_validated_and_every_branch_exercised(tmp_path):
    # Reviewer round-07 finding 2: an undeclared column inside ANY series' value rules must fail
    root = _copy_tree(tmp_path)

    def bad_rule(d):
        ch = next(c for c in d["charts"] if c["id"] == "CH-B5")
        s = next(s for p in ch["panels"] for s in p["series"] if s["name"] == "ur_exp")
        s["value_rules"]["rules"]["RATIO_LOWER_BOUND"]["y"] = "undeclared_bound"

    _mutate_json(root, bad_rule)
    res = _run_on(root)
    assert res[next(k for k in res if k.startswith("schema: every mask, band and value-rule column reference"))][0] is False
    root2 = _copy_tree(tmp_path / "b")

    def missing_branch(d):
        ch = next(c for c in d["charts"] if c["id"] == "CH-B5")
        s = next(s for p in ch["panels"] for s in p["series"] if s["name"] == "er_quad")
        del s["value_rules"]["rules"]["RATIO_ZERO_OVER_ZERO"]  # a declared flag value without a rule

    _mutate_json(root2, missing_branch)
    res2 = _run_on(root2)
    assert res2[next(k for k in res2 if k.startswith("schema: every mask, band and value-rule column reference"))][0] is False
    root3 = _copy_tree(tmp_path / "c")

    def wrong_marker_target(d):
        ch = next(c for c in d["charts"] if c["id"] == "CH-B7")
        s = next(s for p in ch["panels"] for s in p["series"] if s["name"] == "gif_exp")
        s["value_rules"]["rules"]["1"]["y"] = "gif_is_lower_bound"  # exists but is the flag, not a value: branch exercise catches the non-numeric value

    _mutate_json(root3, wrong_marker_target)
    res3 = _run_on(root3)
    assert res3[next(k for k in res3 if k.startswith("schema: every declared value-rule branch"))][0] is False
    root4 = _copy_tree(tmp_path / "d")
    _mutate_json(root4, lambda d: next(s for p in next(c for c in d["charts"] if c["id"] == "CH-B6")["panels"] for s in p["series"] if s["name"] == "if_lin")["mask"].__setitem__("hollow_when", {"nonexistent": 0}))
    res4 = _run_on(root4)
    assert res4[next(k for k in res4 if k.startswith("schema: every mask, band and value-rule column reference"))][0] is False


def test_constants_resolve_to_numeric_lines_under_when_conditions():
    d, ch = _chart("CH-B2")
    pnl = ch["panels"][0]
    got = {s["name"]: cc.chart_points(s, pnl, {"L": 6, "model": "DEP", "folding": "LOCAL", "k": 1, "obs": "PRET"}, {}, d["phase2b"]["matrix_cells"], [], {}, d["constants"])
           for s in pnl["series"] if s.get("source") == "constant"}
    assert got["tol_pret"] == [{"x": "line", "y": 0.05, "kind": "hline"}, {"x": "line", "y": -0.05, "kind": "hline"}]
    assert got["tol_zpi"] == []
    got_z = {s["name"]: cc.chart_points(s, pnl, {"L": 6, "model": "DEP", "folding": "LOCAL", "k": 1, "obs": "ZPI"}, {}, d["phase2b"]["matrix_cells"], [], {}, d["constants"])
             for s in pnl["series"] if s.get("source") == "constant"}
    assert got_z["tol_zpi"] == [{"x": "line", "y": 0.10, "kind": "hline"}, {"x": "line", "y": -0.10, "kind": "hline"}] and got_z["tol_pret"] == []
    d3, ch3 = _chart("CH-A3")
    tau = next(s for s in ch3["panels"][0]["series"] if s["name"] == "tau_max")
    assert cc.chart_points(tau, ch3["panels"][0], {"L": 4}, {}, [], [], {}, d3["constants"])[0]["y"] == pytest.approx(math.log(1.10))
    with pytest.raises(ValueError):
        cc.constant_value(d["constants"], "C-L-VALUES")  # a list constant has no single plotted value


def test_valid_reporting_states_compose_on_three_axes():
    # Reviewer round-07 finding 1
    d, ch = _chart("CH-B6")
    pnl = ch["panels"][0]
    ser = next(s for s in pnl["series"] if s["name"] == "if_lin")
    cells = d["phase2b"]["matrix_cells"]
    cell = next(x for x in cells if x["L"] == 6 and x["noise_model"] == "DEP" and x["folding"] == "LOCAL" and x["kappa"] == 1.0)
    params = {"L": 6, "model": "DEP", "folding": "LOCAL", "kappa": 1.0, "obs": "ZPI"}
    base = {"cell_index": cell["cell_index"], "extrapolator": "LIN", "obs": "ZPI"}
    rows = [dict(base, n=19, eps_dm_noisy=0.001, eps_dm_mit=0.0005, if_value=2, if_is_lower_bound=0, reportable=0),
            dict(base, n=20, eps_dm_noisy=None, eps_dm_mit=None, if_value=None, if_is_lower_bound=0, reportable=0),
            dict(base, n=21, eps_dm_noisy=0.5, eps_dm_mit=1e-12, if_value=5e8, if_is_lower_bound=1, reportable=1),
            dict(base, n=22, eps_dm_noisy=0.5, eps_dm_mit=0.1, if_value=5.0, if_is_lower_bound=0, reportable=1)]
    pts = {p["x"]: p for p in cc.chart_points(ser, pnl, params, {"B-STEPMET": rows}, cells, [], {}, d["constants"])}
    assert pts[19]["y"] == 2 and pts[19]["marker"] == "hollow" and pts[19]["value_state"] == "value"   # below the reportability threshold: hollow, value kept
    assert pts[20]["y"] is None and pts[20]["value_state"] == "unavailable" and pts[20]["marker"] == "hollow_floor"  # undefined IF: explicit, no exception
    assert pts[21]["y"] == 5e8 and pts[21]["marker"] == "triangle_up"                                   # lower bound at its value
    assert pts[22]["y"] == 5.0 and pts[22]["marker"] == "filled"
    d1, ch1 = _chart("CH-B1")
    p1 = ch1["panels"][0]
    s1 = next(s for s in p1["series"] if s["name"] == "lin_shot")
    row1 = {"cell_index": cell["cell_index"], "pipeline": "SHOT", "n": 19, "extrapolator": "LIN", "obs": "ZPI", "estimate": 0.5, "ci95_lo": None, "ci95_hi": None, "flags": "UNDEFINED"}
    pts1 = cc.chart_points(s1, p1, {"L": 6, "model": "DEP", "folding": "LOCAL"}, {"B-MIT": [row1]}, cells, [], {}, d1["constants"])
    assert pts1 == [{"x": 19, "marker": "filled", "y": 0.5, "value_state": "value", "band_state": "unavailable"}]
    row2 = dict(row1, ci95_lo=0.4, ci95_hi=0.6, flags="")
    assert cc.chart_points(s1, p1, {"L": 6, "model": "DEP", "folding": "LOCAL"}, {"B-MIT": [row2]}, cells, [], {}, d1["constants"])[0]["band_state"] == "band"
    with pytest.raises(ValueError):  # a structurally impossible state still raises: inverted band
        cc.chart_points(s1, p1, {"L": 6, "model": "DEP", "folding": "LOCAL"}, {"B-MIT": [dict(row1, ci95_lo=0.6, ci95_hi=0.4)]}, cells, [], {}, d1["constants"])


def test_calibration_missing_and_new_fields_are_reported_and_units_never_mixed():
    pre = {"qubit[3].T1": 100e-6, "gate[ecr][3,4].error": 0.010}
    post = {"qubit[3].T1": 120e-6, "qubit[5].frequency": 5.1e9}
    rows, summary = cc.calibration_changes(pre, post, {"qubit[3].T1": "s", "gate[ecr][3,4].error": "dimensionless", "qubit[5].frequency": "Hz"})
    st = {r["field"]: r["status"] for r in rows}
    assert st == {"gate[ecr][3,4].error": "MISSING_POST", "qubit[3].T1": "PRESENT", "qubit[5].frequency": "NEW_POST"}
    assert summary["calib_missing_fields"] == ["gate[ecr][3,4].error"] and summary["calib_new_fields"] == ["qubit[5].frequency"]
    assert set(summary["calib_max_abs_by_unit"]) == {"s"}  # nothing to compare in the other units; no cross-unit maximum exists
    missing = next(r for r in rows if r["status"] == "MISSING_POST")
    assert missing["post"] is None and missing["abs_change"] is None and missing["rel_change"] is None


def test_lifecycle_of_gate_approved_artifacts():
    approved = {"usage_estimate.json": b"a", "schedule.json": b"b", "authorization_ledger_approved.json": b"c"}
    post = {"pre_submit_recheck.json": b"d", "usage_actual.json": b"e"}
    life = cc.lifecycle(approved, post)
    assert life["approved_verified"] and set(life["added"]) == set(post) and set(life["manifest"]) == set(approved) | set(post)
    assert not cc.lifecycle(approved, post, tamper=("schedule.json", b"B"))["approved_verified"]


def test_output_root_policy():
    assert cc.root_allowed("results/phase2") and cc.root_allowed("results/phase2/phase2a") and cc.root_allowed("figures-phase2")
    assert cc.root_allowed("results/phase2-repro", "results/phase2") and cc.root_allowed("results/my-run")
    for bad in ("results/minimal", "results/MINIMAL", "results/minimal/phase2a", "figures", "figures/", "figures/phase2", "figures/x", "results/", "results/phase2/other", ""):
        assert not cc.root_allowed(bad), bad
    assert not cc.root_allowed("results/phase2", "results/phase2") and not cc.root_allowed("results/phase2/phase2a", "results/phase2")


def test_chart_selectors_resolve_parameters_and_joins():
    cells = json.loads((ROOT / "tools/phase2_contract.json").read_text(encoding="utf-8"))["phase2b"]["matrix_cells"]
    sched = [{"L": 6, "state": "Z2", "obs": "ZPI", "k": 1, "n_ref": 19}, {"L": 6, "state": "Z2", "obs": "ZPI", "k": 2, "n_ref": 39}]
    sel = {"cell_index": {"from": "matrix", "where": {"L": "{L}", "noise_model": "{model}", "folding": "{folding}", "kappa": "{kappa}"}},
           "n": {"from": "schedule", "where": {"L": "{L}", "state": "Z2", "obs": "ZPI"}}, "extrapolator": "LIN", "obs": "{obs}"}
    res = cc.resolve_selector(sel, {"L": 6, "model": "DEP", "folding": "LOCAL", "kappa": 1, "obs": "PRET"}, cells, sched)
    assert res["cell_index"] == {55} and res["n"] == {19, 39} and res["obs"] == "PRET"   # kappa 1 matches the cell's 1.0 numerically
    rows = [{"cell_index": ci, "n": n, "extrapolator": e, "obs": o} for ci in (55, 56) for n in (19, 20, 39) for e in ("LIN", "EXP") for o in ("ZPI", "PRET")]
    picked = cc.select_rows(rows, res)
    assert {(r["cell_index"], r["n"]) for r in picked} == {(55, 19), (55, 39)} and all(r["obs"] == "PRET" and r["extrapolator"] == "LIN" for r in picked)
    with pytest.raises(ValueError):
        cc.resolve_selector({"k": "cells matching the family"}, {})  # descriptive text is not a selector
    with pytest.raises(ValueError):
        cc.resolve_selector({"obs": "{obs}"}, {})  # unbound parameter
    # a family instance that differs in observable, revival or step selects different rows
    res2 = cc.resolve_selector(sel, {"L": 6, "model": "DEP", "folding": "LOCAL", "kappa": 1, "obs": "ZPI"}, cells, sched)
    assert {r["obs"] for r in cc.select_rows(rows, res2)} == {"ZPI"}


# ---------------------------------------------------------------------------
# the real tree passes; corrupted copies fail the right check
# ---------------------------------------------------------------------------


def test_real_tree_passes_every_check():
    results = cc.Checker(ROOT).run()
    failed = [(n, d) for n, ok, d in results if not ok]
    assert failed == [], failed
    assert len(results) >= 50


def test_cli_exit_code_zero_on_the_real_tree_and_two_on_a_missing_input(tmp_path):
    r = subprocess.run([sys.executable, str(CHECKER)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0 and "checks passed" in r.stdout
    broken = tmp_path / "empty"
    broken.mkdir()
    r2 = subprocess.run([sys.executable, str(CHECKER), "--root", str(broken)], capture_output=True, text=True)
    assert r2.returncode == 2, (r2.returncode, r2.stderr[-200:])
    assert "missing input file" in r2.stderr and str(broken) in r2.stderr and r2.stdout == ""


def test_cli_exit_code_two_on_unparseable_json_and_one_on_a_failing_check(tmp_path):
    bad = _copy_tree(tmp_path / "bad")
    (bad / "tools/phase2_contract.json").write_text("{not json", encoding="utf-8")
    r = subprocess.run([sys.executable, str(CHECKER), "--root", str(bad)], capture_output=True, text=True)
    assert r.returncode == 2 and "unreadable input file" in r.stderr and r.stdout == ""
    failing = _copy_tree(tmp_path / "failing")
    _mutate_json(failing, lambda d: d["charts"][0].__setitem__("formats", ["png"]))
    r1 = subprocess.run([sys.executable, str(CHECKER), "--root", str(failing)], capture_output=True, text=True)
    assert r1.returncode == 1 and "[FAIL] schema: every chart has both a png and a pdf entry" in r1.stdout
    r3 = subprocess.run([sys.executable, str(CHECKER), "--root"], capture_output=True, text=True)
    assert r3.returncode == 2


def _mutate_json(root: Path, fn):
    p = root / "tools/phase2_contract.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    fn(d)
    p.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")


def test_copied_tree_passes_before_mutation(tmp_path):
    root = _copy_tree(tmp_path)
    res = _run_on(root)
    assert all(ok for ok, _ in res.values()), [n for n, (ok, _) in res.items() if not ok]


def test_chart_missing_pdf_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    _mutate_json(root, lambda d: d["charts"][0].__setitem__("formats", ["png"]))
    res = _run_on(root)
    assert res["schema: every chart has both a png and a pdf entry"][0] is False


def test_undeclared_column_reference_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    _mutate_json(root, lambda d: d["charts"][0]["panels"][0]["series"][0].__setitem__("column", "no_such_column"))
    res = _run_on(root)
    assert res["schema: every chart- or equation-referenced column and equation is declared"][0] is False


def test_silently_unused_column_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)

    def add_col(d):
        d["artifacts"][0].setdefault("columns", d["artifacts"][0].get("keys"))
        d["artifacts"][0]["keys"].append({"name": "orphan", "dtype": "float", "units": "x", "null_policy": "never null"})

    _mutate_json(root, add_col)
    res = _run_on(root)
    assert res["schema: no declared column is silently unused (referenced or carries a usage note)"][0] is False


def test_ed_series_removed_from_a_mitigated_chart_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)

    def drop_ed(d):
        ch = next(c for c in d["charts"] if c["id"] == "CH-B1")
        for p in ch["panels"]:
            p["series"] = [s for s in p["series"] if s["column"] != "e_ed"]

    _mutate_json(root, drop_ed)
    res = _run_on(root)
    assert res["schema: every panel plotting a mitigated observable carries the E^ED series"][0] is False


def test_constant_render_mismatch_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    _mutate_json(root, lambda d: d["constants"]["C-TAU-RMS"].__setitem__("value", 0.06))
    res = _run_on(root)
    assert res["cross: every numeric constant's render matches its JSON value"][0] is False
    root2 = _copy_tree(tmp_path / "b")
    _mutate_json(root2, lambda d: d["constants"]["C-TAU-MAX"].__setitem__("render", "0.09999"))
    res2 = _run_on(root2)
    assert res2["cross: every constant's render string appears in each document it is required in"][0] is False


def test_reviewer_constant_mutation_is_rejected_by_the_binding_check(tmp_path):
    root = _copy_tree(tmp_path)

    def mutate(d):
        d["constants"]["C-TAU-A-PRET"]["value"] = 0.5
        d["constants"]["C-TAU-A-PRET"]["render"] = "0.5"

    _mutate_json(root, mutate)
    res = _run_on(root)
    name = "cross: every constant is bound to a named definition site (anchor + render, non-digit boundary); a mutated value or render fails here"
    assert res[name][0] is False and "C-TAU-A-PRET" in res[name][1]


def test_hardware_parameter_mutations_are_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    _mutate_json(root, lambda d: (d["constants"]["C-MAX-EXEC"].__setitem__("value", 480), d["phase2c"].__setitem__("max_execution_time", 480)))
    res = _run_on(root)
    assert res["hardware: T_lim < T_cap, T_open - T_cap = reserve = 120, max_execution_time = T_lim, all from the JSON"][0] is False
    root2 = _copy_tree(tmp_path / "b")
    _mutate_json(root2, lambda d: d["phase2c"]["estimate"]["illustration"].__setitem__("T_est_cons_s", 341.7))
    res2 = _run_on(root2)
    assert res2["hardware: illustration recomputed from the JSON: T_est^(1) = 341.7, T_est^cons = 627.7, and the binding value does not fit"][0] is False
    root3 = _copy_tree(tmp_path / "c")
    _mutate_json(root3, lambda d: d["constants"]["C-PEAK-EXPECTED-L6"].__setitem__("value", [19, 24]))
    res3 = _run_on(root3)
    assert res3["hardware: schedule from the expected L=6 peaks gives 12 points {1,10,17..21,37..41}, both revival-1 windows timing-testable, E_1 subset of P"][0] is False


def test_chart_selector_and_file_count_mutations_are_rejected(tmp_path):
    root = _copy_tree(tmp_path)

    def loosen(d):
        ch = next(c for c in d["charts"] if c["id"] == "CH-B11")
        for s in ch["panels"][0]["series"]:
            s["rows"] = {"pipeline": "SHOT"}

    _mutate_json(root, loosen)
    res = _run_on(root)
    assert res[next(k for k in res if k.startswith("schema: CH-B11 selects PRIMARY only"))][0] is False
    root2 = _copy_tree(tmp_path / "b")
    _mutate_json(root2, lambda d: d.__setitem__("charts_total_files_per_format", 611))
    res2 = _run_on(root2)
    assert res2[next(k for k in res2 if k.startswith("schema: chart file counts"))][0] is False


def test_root_policy_example_mutation_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    _mutate_json(root, lambda d: d["entrypoints"]["output_root_guard"]["accepted_examples"].append(["figures/phase2", None]))
    res = _run_on(root)
    assert res[next(k for k in res if k.startswith("roots:"))][0] is False


def test_joint_pass_rule_without_overlap_or_with_fail_suppression_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    _mutate_json(root, lambda d: d["phase2b"]["joint_pass"].__setitem__("endpoint_statuses", ["PASS", "FAIL", "INDETERMINATE"]))
    res = _run_on(root)
    assert res["cross: JSON joint-pass rule carries OVERLAP, does not suppress FAIL, and does not decide on 95% intervals"][0] is False
    root2 = _copy_tree(tmp_path / "b")
    _mutate_json(root2, lambda d: d["phase2b"]["joint_pass"].__setitem__(
        "rule", "PASS iff all four PASS; FAIL if any FAIL and no INDETERMINATE; OVERLAP otherwise"))
    res2 = _run_on(root2)
    assert res2["cross: JSON joint-pass rule carries OVERLAP, does not suppress FAIL, and does not decide on 95% intervals"][0] is False


def test_tolerance_based_tie_order_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    _mutate_json(root, lambda d: d["phase2b"]["control_selection"].__setitem__(
        "weight_tie_order", "weights within 1e-12 are ties ordered by tolerance"))
    res = _run_on(root)
    assert res["cross: JSON tie orders are exact total orders (no tolerance-based ordering)"][0] is False


def test_mask_boundary_removed_from_secondary_blockers_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    _mutate_json(root, lambda d: d["phase2a"]["secondary"].__setitem__("L_level_blockers", ["REFERENCE_MISMATCH"]))
    res = _run_on(root)
    assert res["cross: JSON Phase 2A secondary blockers include MASK_BOUNDARY"][0] is False


def test_matrix_total_or_duplicate_seed_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    _mutate_json(root, lambda d: d["phase2b"]["matrix_summary"].__setitem__("grand_total_if_everything_runs", 350064))
    res = _run_on(root)
    assert res["cross: matrix totals recomputed (150 cells: 72/72/6; 12 conditional; 280,080 unconditional; 350,208 all)"][0] is False
    root2 = _copy_tree(tmp_path / "b")
    _mutate_json(root2, lambda d: d["phase2b"]["control_cells"][0].__setitem__("cell_index", 1))
    res2 = _run_on(root2)
    assert res2["cross: every seed_simulator value is unique across all enumerated cells"][0] is False


def test_dangling_cross_reference_in_prose_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    p = root / "docs/prereg-phase2.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n\nSee §99.7 for nothing.\n", encoding="utf-8")
    res = _run_on(root)
    assert res["cross: every § cross-reference in the two Phase 2 documents resolves to a heading"][0] is False


def test_checkpoint_marker_in_a_deliverable_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    p = root / "docs/phase2-analysis-contract.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n\n" + "TO" + "DO: finish later\n", encoding="utf-8")
    res = _run_on(root)
    assert res["cross: no checkpoint marker (TO-DO) in any deliverable"][0] is False


def test_trailing_whitespace_in_a_deliverable_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    p = root / "docs/prereg-phase2.md"
    p.write_text(p.read_text(encoding="utf-8") + "\ntrailing space here \n", encoding="utf-8")
    res = _run_on(root)
    assert res["whitespace: git diff --check --no-index /dev/null <file> clean for every deliverable (index untouched)"][0] is False


def test_accepted_risk_wording_reintroduced_is_rejected(tmp_path):
    root = _copy_tree(tmp_path)
    _mutate_json(root, lambda d: d["phase2c"].__setitem__("cap_rule", "submission permitted with an accepted-risk statement above 480"))
    res = _run_on(root)
    assert res["cross: JSON phase2c carries TIMING_UNTESTABLE, fits(T) < 479, binding conservative estimate and no accepted-risk exception"][0] is False


def test_traceability_rows_resolve_to_declared_artifacts():
    ck = cc.Checker(ROOT)
    ck.load()
    rows = ck.traceability_rows()
    assert len(rows) > 100
    assert all(r[3] != "?" and r[6] != "?, EP-FIGURES" for r in rows)
    assert ("CH-A1", "ratios", "r10", "results/phase2/phase2a/interaction.csv", "r10 [L={L}]", "EQ-A1", "EP-2A, EP-FIGURES") in rows
    assert any(r[0] == "CH-A6" and r[4] == "constants.C-TAU-HIST" for r in rows)
    assert any(r[0] == "CH-B11" and "family=PRIMARY" in r[4] for r in rows)


def test_checker_writes_nothing_and_imports_no_experiment_code():
    src = CHECKER.read_text(encoding="utf-8")
    import_lines = [line for line in src.splitlines() if line.startswith("import ") or line.startswith("from ")]
    joined = "\n".join(import_lines)
    assert "zne_scars" not in joined and "qiskit" not in joined and "mitiq" not in joined
    assert "import numpy" not in joined  # numpy is imported lazily inside the resampling reference only
    assert "requests" not in joined and "urllib" not in joined and "socket" not in joined
    # the only file access is read_text on inputs and a read-only git subprocess; nothing is opened for writing
    assert ".write_text(" not in src and "open(" not in src.replace("open(", "", 0)


# ---------------------------------------------------------------------------
# Reviewer round-08: masks against their prose meaning; bound columns bound to their quantity
# ---------------------------------------------------------------------------


def test_mask_conditions_literal_null_and_comparison():
    assert cc.mask_condition_holds(0, 0) and not cc.mask_condition_holds(1, 0)
    assert cc.mask_condition_holds(None, "__null__") and not cc.mask_condition_holds(0, "__null__")
    assert cc.mask_condition_holds(3, {">": 0}) and not cc.mask_condition_holds(0, {">": 0})
    assert not cc.mask_condition_holds(None, {">": 0})            # a comparison is false for a null, never an error
    assert cc.mask_condition_holds(1.0, {">=": 1, "<": 2}) and not cc.mask_condition_holds(2, {">=": 1, "<": 2})
    assert cc.mask_condition_holds(1.0, {"==": 1}) and cc.mask_condition_holds(1.0, {"!=": 0})


def test_ch_b11_boundary_fixture_unresolved_is_hollow_and_non_monotone_carries_an_edge():
    # Reviewer's fixture: OVERLAP, PASS, PASS, PASS, PASS -> UNRESOLVED_AT_MIN with located = 0 and non_monotone = 1
    d, ch = _chart("CH-B11")
    pnl = ch["panels"][0]
    ser = next(s for s in pnl["series"] if s["name"] == "kstar")
    base = {"L": 6, "noise_model": "DEP", "folding": "LOCAL", "extrapolator": "LIN", "pipeline": "SHOT", "k": 1, "family": "PRIMARY", "hypothesis_component": "not evaluable"}
    rows = [dict(base, kappa_star="UNRESOLVED_AT_MIN", located=0, non_monotone=1),
            dict(base, k=2, kappa_star="0.5", located=1, non_monotone=0),
            dict(base, k=3, kappa_star="1", located=1, non_monotone=1),
            dict(base, k=4, kappa_star="UNRESOLVED_AT_MAX", located=0, non_monotone=0)]
    pts = cc.chart_points(ser, pnl, {}, {"B-BOUND": rows}, d["phase2b"]["matrix_cells"], [], {})
    assert [p["marker"] for p in pts] == ["hollow+edge", "filled", "filled+edge", "hollow"]
    assert pts[0]["y"] == "UNRESOLVED_AT_MIN" and pts[0]["annotate"] == "not evaluable"


def test_ch_a6_zero_on_a_log_axis_is_hollow_at_the_floor_and_counted():
    d, ch = _chart("CH-A6")
    pnl = ch["panels"][0]
    ser = next(s for s in pnl["series"] if s["name"] == "d00")
    rows = [{"n": 1, "d00": 0.0, "within_tau_hist": 1, "within_eta_e": 1}, {"n": 2, "d00": 3e-13, "within_tau_hist": 1, "within_eta_e": 1},
            {"n": 3, "d00": 5e-11, "within_tau_hist": 0, "within_eta_e": 1}, {"n": 4, "d00": 2e-8, "within_tau_hist": 0, "within_eta_e": 0}]
    pts = {p["x"]: p for p in cc.chart_points(ser, pnl, {}, {"A-HIST": rows}, [], [], {})}
    assert pts[1]["marker"] == "hollow_floor+edge" and pts[1]["value_state"] == "nonpositive_on_log" and pts[1]["log_floor"] is True
    assert pts[2]["marker"] == "filled+edge" and pts[3]["marker"] == "hollow+edge" and pts[4]["marker"] == "hollow"
    assert sum(1 for p in pts.values() if p.get("log_floor")) == 1  # the annotated count


def test_ch_c2_status_styles_and_ch_b8_count_annotation():
    d, ch = _chart("CH-C2")
    pnl = ch["panels"][0]
    ser = next(s for s in pnl["series"] if s["name"] == "dec")
    base = {"family": "CF-2C", "extrapolator": "LIN", "k": 1, "ref": "E0", "obs": "ZPI", "dec_hi": 0.2, "dec_level": 0.9875}
    rows = [dict(base, endpoint=e, dec_lo=0.1, status=s) for e, s in (("A", "PASS"), ("B", "FAIL"), ("C", "OVERLAP"), ("D", "INDETERMINATE"))]
    rows.append(dict(base, endpoint="E", dec_lo=None, dec_hi=None, status="UNAVAILABLE"))
    pts = cc.chart_points(ser, pnl, {}, {"C-END": rows}, [], [], {})
    assert [p["marker"] for p in pts] == ["filled", "cross", "half", "hollow", "hollow_floor"]
    with pytest.raises(ValueError):
        cc.chart_points(ser, pnl, {}, {"C-END": [dict(base, endpoint="F", dec_lo=0.1, status="NOT_A_STATUS")]}, [], [], {})
    d8, ch8 = _chart("CH-B8")
    p8 = ch8["panels"][0]
    s8 = next(s for s in p8["series"] if s["name"] == "tiae_lin")
    cell = next(x for x in d8["phase2b"]["matrix_cells"] if x["L"] == 6 and x["noise_model"] == "DEP" and x["folding"] == "LOCAL" and x["kappa"] == 1.0)
    r8 = {"cell_index": cell["cell_index"], "pipeline": "SHOT", "extrapolator": "LIN", "obs": "ZPI", "ref": "E0", "tiae": None, "n_undefined_steps": 3, "kappa": 1.0}
    pts8 = cc.chart_points(s8, p8, {"L": 6, "model": "DEP", "folding": "LOCAL", "obs": "ZPI"}, {"B-CURVEMET": [r8]}, d8["phase2b"]["matrix_cells"], [], {})
    assert pts8[0]["marker"] == "hollow_floor" and pts8[0]["value_state"] == "unavailable" and pts8[0]["annotate"] == 3
    pts8b = cc.chart_points(s8, p8, {"L": 6, "model": "DEP", "folding": "LOCAL", "obs": "ZPI"}, {"B-CURVEMET": [dict(r8, tiae=0.4, n_undefined_steps=1)]}, d8["phase2b"]["matrix_cells"], [], {})
    assert pts8b[0]["marker"] == "hollow"  # any positive count hollows the point


def test_reviewer_declared_but_wrong_column_mutation_fails(tmp_path):
    # Reviewer round-08 finding 2: ur_exp's RATIO_LOWER_BOUND drawn from er_bound (declared, wrong quantity) must fail
    root = _copy_tree(tmp_path)

    def wrong_quantity(d):
        ch = next(c for c in d["charts"] if c["id"] == "CH-B5")
        s = next(s for p in ch["panels"] for s in p["series"] if s["name"] == "ur_exp")
        s["value_rules"]["rules"]["RATIO_LOWER_BOUND"]["y"] = "er_bound"

    _mutate_json(root, wrong_quantity)
    res = _run_on(root)
    assert res[next(k for k in res if k.startswith("schema: with distinct ER and UR bounds"))][0] is False
    assert res[next(k for k in res if k.startswith("schema: every declared value-rule branch"))][0] is False
    assert res[next(k for k in res if k.startswith("schema: every mask, band and value-rule column reference"))][0] is False
    # tampering with the declaration itself (er_bound declared as a bound for ur) is caught by the same checks
    root2 = _copy_tree(tmp_path / "b")

    def tamper(d):
        wrong_quantity(d)
        col = next(c for a in d["artifacts"] if a["id"] == "B-STEPMET" for c in a["columns"] if c["name"] == "er_bound")
        col["bound_for"] = "ur"

    _mutate_json(root2, tamper)
    res2 = _run_on(root2)
    assert res2[next(k for k in res2 if k.startswith("schema: with distinct ER and UR bounds"))][0] is False
    assert res2[next(k for k in res2 if k.startswith("schema: every declared value-rule branch"))][0] is False


def test_mask_meaning_mutations_fail(tmp_path):
    # Reviewer round-08 finding 1: a mask that contradicts its prose meaning must fail, for every mask, not only CH-B11 and CH-A6
    def b11_vacuous(d):
        s = next(s for c in d["charts"] if c["id"] == "CH-B11" for p in c["panels"] for s in p["series"] if s["name"] == "kstar")
        s["mask"] = {"column": "B-BOUND.non_monotone", "hollow_when": {"non_monotone": "__null__"}}

    def a6_edge_dropped(d):
        for s in (s for c in d["charts"] if c["id"] == "CH-A6" for p in c["panels"] for s in p["series"]):
            s["mask"] = {"column": "A-HIST.within_tau_hist", "hollow_when": {"within_tau_hist": 0}}

    def c2_swap(d):
        for s in (s for c in d["charts"] if c["id"] == "CH-C2" for p in c["panels"] for s in p["series"] if s.get("mask")):
            sw = s["mask"]["style_when"]["status"]
            sw["PASS"], sw["FAIL"] = sw["FAIL"], sw["PASS"]

    def b8_threshold(d):
        for s in (s for c in d["charts"] if c["id"] == "CH-B8" for p in c["panels"] for s in p["series"] if s.get("mask")):
            s["mask"]["hollow_when"] = {"n_undefined_steps": {">": 5}}

    def a1_polarity(d):
        for s in (s for c in d["charts"] if c["id"] == "CH-A1" for p in c["panels"] for s in p["series"] if s.get("mask")):
            s["mask"]["hollow_when"] = {"in_mask": 1}

    def b10_not_distinguishable_filled(d):
        for s in (s for c in d["charts"] if c["id"] == "CH-B10" for p in c["panels"] for s in p["series"] if s.get("value_rules")):
            s["value_rules"]["rules"]["NOT_DISTINGUISHABLE"]["marker"] = "filled"

    for i, (mut, check) in enumerate([(b11_vacuous, "schema: every mask is composed"), (a6_edge_dropped, "schema: every mask is composed"),
                                      (c2_swap, "schema: every mask is composed"), (b8_threshold, "schema: every mask is composed"),
                                      (a1_polarity, "schema: every mask is composed"), (b10_not_distinguishable_filled, "schema: every declared value-rule branch")]):
        root = _copy_tree(tmp_path / f"m{i}")
        _mutate_json(root, mut)
        res = _run_on(root)
        assert res[next(k for k in res if k.startswith(check))][0] is False, mut.__name__
    assert cc.Checker(ROOT).run() and all(ok for _, ok, _ in cc.Checker(ROOT).run() if _.startswith("schema: every mask"))


def test_every_mask_and_value_rule_series_has_an_oracle_entry():
    d = json.loads((ROOT / "tools/phase2_contract.json").read_text(encoding="utf-8"))
    for ch in d["charts"]:
        for p in ch["panels"]:
            for s in p["series"]:
                if s.get("mask"):
                    assert (s["artifact"], s["mask"]["column"].split(".", 1)[1]) in cc.MASK_ORACLE, (ch["id"], s["name"])
                if s.get("value_rules"):
                    fc = s["value_rules"]["flag_column"]
                    assert (s["artifact"], fc, s["column"]) in cc.VALUE_RULE_ORACLE or (s["artifact"], fc) in cc.VALUE_RULE_ORACLE, (ch["id"], s["name"])


# ---------------------------------------------------------------------------
# Task 20260908-100250-316d3f: fork safety of the whitespace check
# ---------------------------------------------------------------------------

WHITESPACE_KEY = "whitespace: git diff --check --no-index /dev/null <file> clean for every deliverable (index untouched)"
# git diff --check --no-index <file> vs /dev/null: bit 1 = content differs (always, the file is non-empty),
# bit 2 = --check found a whitespace problem. Observed with git 2.39.5: clean file 1, trailing whitespace 3.
GIT_CLEAN_RC = 1
GIT_WHITESPACE_RC = 3


def _whitespace_git_calls(mod, root: Path):
    """Run mod.Checker.check_whitespace on root, recording every subprocess.run call it makes, the
    CompletedProcess each returned, and the CPython launch primitive each call actually used.

    The real subprocess.run still executes, so the recorded results are genuine. Only the
    module-level ``subprocess`` name is swapped for a recording proxy, and the two launch
    primitives (``os.posix_spawn`` and ``subprocess._fork_exec``, where present) are wrapped
    so the route taken is observed rather than inferred; everything is restored in ``finally``.
    """
    real = mod.subprocess
    spawns, calls = [], []
    hooks = []  # (owner, attribute, original)

    def _hook(owner, attribute, label):
        original = getattr(owner, attribute, None)
        if original is None:
            return

        def shim(*args, **kwargs):
            spawns.append(label)
            return original(*args, **kwargs)

        hooks.append((owner, attribute, original))
        setattr(owner, attribute, shim)

    class _Recording:
        def __getattr__(self, name):
            return getattr(real, name)

        def run(self, *args, **kwargs):
            before = len(spawns)
            r = real.run(*args, **kwargs)
            calls.append({"argv": list(args[0]), "kwargs": dict(kwargs), "spawn": spawns[before:],
                          "returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr})
            return r

    _hook(os, "posix_spawn", "posix_spawn")
    _hook(real, "_fork_exec", "fork_exec")
    mod.subprocess = _Recording()
    try:
        ck = mod.Checker(root)
        ck.check_whitespace()
    finally:
        mod.subprocess = real
        for owner, attribute, original in hooks:
            setattr(owner, attribute, original)
    return calls, _results_by_name(ck.results)


def test_whitespace_check_uses_git_dash_c_and_never_passes_cwd(tmp_path):
    """Call-shape half of the no-fork contract, and the half that rejects the old implementation
    on every platform. CPython takes its posix_spawn path only when several preconditions hold
    at once: the executable has a nonempty directory component, close_fds is False and no cwd is
    given, among others. Omitting cwd alone is necessary but not sufficient. The checker's own
    guarantee is stronger than CPython's condition: the launched executable is absolute. The
    spawn-path test below pins the route actually taken where the fast path exists."""
    root = _copy_tree(tmp_path)
    calls, res = _whitespace_git_calls(cc, root)
    present = [rel for rel in cc.DELIVERABLES if (root / rel).exists()]
    assert len(present) == 5
    assert len(calls) == len(present)
    git = shutil.which("git")
    assert git is not None
    expected = str(Path(git).absolute())
    for call in calls:
        argv, kwargs = call["argv"], call["kwargs"]
        assert argv[0] == expected, argv
        assert Path(argv[0]).is_absolute() and Path(argv[0]).parent != Path(""), argv
        assert argv[1:3] == ["-C", str(root)], argv
        assert argv[3:7] == ["diff", "--check", "--no-index", "/dev/null"], argv
        assert Path(argv[7]).is_relative_to(root), argv
        assert "cwd" not in kwargs, kwargs
        assert kwargs.get("close_fds") is False, kwargs
        assert call["stderr"] == "", call
        assert call["returncode"] == GIT_CLEAN_RC and call["stdout"] == "", call
    assert res[WHITESPACE_KEY][0] is True


def test_whitespace_check_launches_git_via_posix_spawn_not_fork(tmp_path):
    """Route half of the no-fork contract: every git launch must go through os.posix_spawn and
    subprocess._fork_exec must not be called for any of them, observed directly and independent
    of whether a fork ever aborts. Where the fast path exists this rejects the old implementation
    (bare ``git``, default close_fds, cwd=) deterministically because it records fork_exec. Where
    the fast path is absent the test skips, and only the call-shape test above rejects old code."""
    if not getattr(subprocess, "_USE_POSIX_SPAWN", False) or not hasattr(os, "posix_spawn") or not hasattr(subprocess, "_fork_exec"):
        pytest.skip("this interpreter has no posix_spawn fast path to assert on")
    root = _copy_tree(tmp_path)
    calls, res = _whitespace_git_calls(cc, root)
    assert len(calls) == 5
    for call in calls:
        assert call["spawn"] == ["posix_spawn"], call
        assert "fork_exec" not in call["spawn"], call
    assert res[WHITESPACE_KEY][0] is True


def test_whitespace_check_makes_a_bare_which_result_absolute_without_resolving_symlinks(tmp_path, monkeypatch):
    """shutil.which returns a bare name when PATH holds an empty component and the calling
    directory contains git; a bare name has no directory component, so CPython would fall back
    to fork(). The checker must launch an absolute path built from the lookup, keeping the
    lookup's own spelling rather than resolving symlinks, which the condition does not need."""
    real_git = shutil.which("git")
    assert real_git is not None
    root = _copy_tree(tmp_path)
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    os.symlink(Path(real_git).absolute(), cwd / "git")
    monkeypatch.chdir(cwd)
    monkeypatch.setenv("PATH", os.pathsep + os.environ.get("PATH", ""))
    assert shutil.which("git") == "git"  # the hazard is real on this interpreter
    calls, res = _whitespace_git_calls(cc, root)
    assert len(calls) == 5
    for call in calls:
        launched = Path(call["argv"][0])
        assert launched == cwd / "git", call
        assert launched.is_absolute() and launched.parent != Path(""), call
        assert launched.is_symlink(), call  # the symlink itself was launched, not its target
        if getattr(subprocess, "_USE_POSIX_SPAWN", False) and hasattr(os, "posix_spawn"):
            assert call["spawn"] == ["posix_spawn"], call
        assert call["stderr"] == "" and call["returncode"] == GIT_CLEAN_RC, call
    assert res[WHITESPACE_KEY][0] is True


_THREADED_CHILD = r"""
import concurrent.futures, importlib.util, json, os, sys, threading, time
from pathlib import Path

checker, clean, dirty, key = sys.argv[1:5]
spec = importlib.util.spec_from_file_location("phase2_contract_check_child", checker)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

real = mod.subprocess
spawns, git_calls = [], []


def hook(owner, attribute, label):
    original = getattr(owner, attribute, None)
    if original is None:
        return

    def shim(*args, **kwargs):
        spawns.append(label)
        return original(*args, **kwargs)

    setattr(owner, attribute, shim)


class Recording:
    def __getattr__(self, name):
        return getattr(real, name)

    def run(self, *args, **kwargs):
        before = len(spawns)
        r = real.run(*args, **kwargs)
        git_calls.append({"file": Path(args[0][-1]).name, "spawn": spawns[before:], "returncode": r.returncode,
                          "stdout": r.stdout, "stderr": r.stderr, "cwd": "cwd" in kwargs,
                          "close_fds": kwargs.get("close_fds", True), "absolute": Path(args[0][0]).is_absolute()})
        return r


hook(os, "posix_spawn", "posix_spawn")
hook(real, "_fork_exec", "fork_exec")
mod.subprocess = Recording()

stop = threading.Event()


def hold():
    stop.wait()


def spin():
    x = 0
    while not stop.is_set():
        x = (x * 31 + 7) % 1000003
    return x


def live_workers():
    return sum(1 for t in threading.enumerate() if t.name.startswith("ThreadPoolExecutor") and t.is_alive())


out = {"git": {}, "fast_path": bool(getattr(real, "_USE_POSIX_SPAWN", False))}
pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)
try:
    futures = [pool.submit(hold), pool.submit(hold), pool.submit(spin)]
    deadline = time.monotonic() + 10
    while live_workers() < 3 and time.monotonic() < deadline:
        time.sleep(0.01)
    out["workers_before"] = live_workers()
    for label, root in (("clean", clean), ("dirty", dirty)):
        del git_calls[:]
        ck = mod.Checker(Path(root))
        ck.check_whitespace()
        results = {name: (ok, detail) for name, ok, detail in ck.results}
        out[label] = results[key]
        out["git"][label] = list(git_calls)
    out["workers_after"] = live_workers()
finally:
    stop.set()
    pool.shutdown(wait=True)
print(json.dumps(out))
"""


def _threaded_child_whitespace(checker_path: Path, tmp_path: Path):
    """Run the real check_whitespace from checker_path inside a child interpreter that has live
    concurrent.futures worker threads, with the launch primitive and every nested git result
    (return code, stdout, stderr) recorded. Returns (returncode, stdout, stderr, parsed_json_or_None)."""
    clean = _copy_tree(tmp_path / "clean")
    dirty = _copy_tree(tmp_path / "dirty")
    p = dirty / "docs/prereg-phase2.md"
    p.write_text(p.read_text(encoding="utf-8") + "\ntrailing space here \n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-c", _THREADED_CHILD, str(checker_path), str(clean), str(dirty), WHITESPACE_KEY],
        capture_output=True, timeout=120,
    )
    parsed = None
    if proc.returncode == 0:
        try:
            parsed = json.loads(proc.stdout.decode("utf-8"))
        except ValueError:
            parsed = None
    return proc.returncode, proc.stdout, proc.stderr, parsed


def test_whitespace_check_is_clean_and_accurate_under_live_worker_threads(tmp_path):
    """Real threaded behavior. With worker threads alive in the calling process the interpreter
    must exit 0 with nothing on its own stderr, every nested git child (whose stderr the checker
    captures, so it is inspected per call here) must write nothing to stderr and exit with the
    observed clean or whitespace-error code, every launch must use posix_spawn where the fast
    path exists, and the check must still tell a clean deliverable set from one carrying
    trailing whitespace."""
    rc, out, err, parsed = _threaded_child_whitespace(CHECKER, tmp_path)
    assert rc == 0, (rc, out, err)
    assert err == b"", err
    assert parsed is not None, out
    assert parsed["workers_before"] >= 3 and parsed["workers_after"] >= 3, parsed
    assert parsed["clean"][0] is True, parsed
    assert parsed["dirty"][0] is False, parsed
    assert "docs/prereg-phase2.md" in parsed["dirty"][1], parsed
    for label in ("clean", "dirty"):
        git = parsed["git"][label]
        assert len(git) == 5, git
        for call in git:
            assert call["absolute"] and call["close_fds"] is False and call["cwd"] is False, call
            if parsed["fast_path"]:
                assert call["spawn"] == ["posix_spawn"], call
            assert call["stderr"] == "", call
            if label == "dirty" and call["file"] == "prereg-phase2.md":
                assert call["returncode"] == GIT_WHITESPACE_RC and "trailing whitespace" in call["stdout"], call
            else:
                assert call["returncode"] == GIT_CLEAN_RC and call["stdout"] == "", call
