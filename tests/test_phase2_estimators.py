"""The vectorised phase2.estimators implementation is compared with the checker's reference implementations
(post A-1 / A-2, corrected 2026-09-08) on synthetic data: LIN/QUAD intercepts, EXP sign (the scalar pinned
numpy.polyfit + np.sign for EVERY element, zero included) in both modes, the homogeneity rule, and the DM
companion seed range including non-finite seed values. The value-level agreements asserted here hold on
these fixtures; the EXP sign and log-mode fit are the same scalar numpy.polyfit calls as the checker's (A-2
corrections), while the LIN/QUAD intercepts are ordinary least squares by normal equations on both sides and are
not claimed equivalent to numpy.polyfit (see the outside-guard-band regression below). No experiment, nothing written outside tmp_path."""
from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phase2 import estimators as E  # noqa: E402

spec = importlib.util.spec_from_file_location("phase2_contract_check", ROOT / "tools/phase2_contract_check.py")
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)
XS = np.array([1.0, 1.25, 1.5, 1.75, 2.0])


def test_batched_polyfit_agrees_with_the_scalar_pinned_call_only_to_rounding():
    # documents why pinned_signs uses the scalar numpy.polyfit call: the multi-column call may differ in the last bits
    # (it does on macOS/Accelerate and does not on the Linux CI build, so bit-identity is NOT asserted either way)
    rng = np.random.default_rng(0)
    Y = rng.normal(size=(5, 40)); Y[:, 0] = XS / 4
    batched = np.polyfit(XS, Y, 1)[-1]
    scalar = np.array([np.polyfit(XS, Y[:, i], 1)[-1] for i in range(40)])
    assert np.abs(batched - scalar).max() < 1e-14


def test_pinned_signs_equal_the_scalar_polyfit_sign_for_every_element_including_zero():
    rng = np.random.default_rng(11)
    X = np.tile(XS, (3, 2, 1)); X[1, 0] = [1.0, 1.0, 1.5, 2.0, 2.0]; X[2, 1] = [1.0, 1.25, 1.5, 1.5, 2.0]
    d = E.design(X)
    B = 400
    V = rng.normal(0, 0.3, size=(B, 3, 2, 5, 5))
    V[:8, 0, 0, :, 0] = XS / 4                                       # reviewer oracle columns (intercept -4.97e-17)
    V[8:12, 0, 0, :, 1] = 0.0                                        # exact zeros -> sign 0
    V[12:20, 0, 0, :, 2] = XS / 4 + rng.normal(0, 1e-12, size=(8, 5))  # tiny offsets around the asymptote
    V[20:28, 0, 0, :, 3] = (XS / 4)[None, :] + np.linspace(-3e-9, 3e-9, 8)[:, None]
    a = np.array([0.0, 0.0, 0.0, 0.0, 0.25])
    got = E.pinned_signs(d, V, a)
    assert not hasattr(E, "SIGN_GUARD")                              # the hybrid guard band is gone
    for b in range(B):
        for n in range(3):
            for k in range(2):
                if not d.ok_exp[n, k]:
                    assert (got[b, n, k] == 0.0).all()
                    continue
                for q in range(5):
                    assert got[b, n, k, q] == cc.exp_sign(list(X[n, k]), list(V[b, n, k, :, q]), float(a[q])), (b, n, k, q)
    assert (got[:8, 0, 0, 0] == 0.0).all() and (got[8:12, 0, 0, 1] == 0.0).all()   # A-3: y = x/4 columns are sign 0 (both recorded platform intercepts lie within tau)


# ---- regression oracle: the rejected guard-band hybrid versus the pinned scalar call under A-3 ----------------------------
# History. The round-04 fixture (three abscissas clustered within 2e-4 of 1.5, y = -3e-8 + 0.58 x, a = 0) showed the closed-form
# intercept (+3.003e-8, outside the old band 1.87e-8) disagreeing in SIGN with the scalar numpy.polyfit intercept (-3.000e-8).
# Under amendment A-3 (2026-09-09) that fixture's intercept lies far inside the scale-aware tolerance (tau ~ 1e-2 there: cond(V)
# 4.3e4 and lever 3e8), so its sign is 0 by the approved rule; and its degree-2 normal equations are numerically singular on the
# Linux CI build (cond(A^T A) ~ 3e16), where design() raises LinAlgError. The fixture is therefore re-expressed at spread 3e-3
# (cond(A^T A) for QUAD ~ 7e12, well inside double precision on every platform) with the same construction: the closed-form
# intercept (-3.0009e-8) is still OUTSIDE the old band (1.87e-8), so the rejected hybrid takes its closed-form fast path and
# returns a NONZERO sign, while the A-3 rule returns 0 because |intercept| = 3.0e-8 <= tau = 5.0e-7. Provenance: reconstructed
# by the implementer, not a reviewer's original case.
_BREAK_X = np.array([1.5, 1.503, 1.506, 1.5, 1.503])
_BREAK_Y = np.array([0.8699999699999998, 0.8717399699999998, 0.8734799699999999, 0.8699999699999998, 0.8717399699999998])
_BREAK_A = 0.0
_OLD_BAND = 1e-8  # the rejected SIGN_GUARD

_HYBRID_MUTANT = """
def pinned_signs(d, V, a):
    # MUTANT: the rejected guard-band hybrid (closed-form sign outside the band, scalar polyfit inside)
    SIGN_GUARD = 1e-8
    B, N, K, J, Q = V.shape
    lin_closed = np.einsum("nkj,bnkjq->bnkq", np.nan_to_num(d.w_lin), V)
    scale = 1.0 + np.abs(a) + np.abs(V).max(axis=3)
    diff = lin_closed - a
    sign = np.sign(diff)
    near = np.abs(diff) <= SIGN_GUARD * scale
    for b, n, k, q in zip(*np.nonzero(near)):
        sign[b, n, k, q] = np.sign(-(a[q] - float(np.polyfit(d.X[n, k], V[b, n, k, :, q], 1)[-1])))
    sign[:, ~d.ok_exp] = 0.0
    return sign
"""


def _load_estimators_with_guard_band_mutant(tmp_path):
    """phase2/estimators.py with pinned_signs replaced by the rejected hybrid, loaded as a module in package phase2."""
    src = (ROOT / "phase2" / "estimators.py").read_text(encoding="utf-8")
    start = src.index("def pinned_signs(")
    end = src.index("def fit_exp_log(")
    mutated = src[:start] + _HYBRID_MUTANT.lstrip("\n") + "\n\n" + src[end:]
    assert mutated != src
    mp = tmp_path / "estimators_guard_band_mutant.py"
    mp.write_text(mutated, encoding="utf-8")
    name = "phase2._estimators_guard_band_mutant"
    spec_m = importlib.util.spec_from_file_location(name, mp)
    mod = importlib.util.module_from_spec(spec_m)
    mod.__package__ = "phase2"
    sys.modules[name] = mod                       # dataclasses resolve annotations through sys.modules
    try:
        spec_m.loader.exec_module(mod)
    finally:
        sys.modules.pop(name, None)
    return mod


def _breaking_case_arrays():
    d = E.design(_BREAK_X[None, None, :])
    V = _BREAK_Y[None, None, None, :, None].repeat(5, axis=4)
    return d, V, np.full(5, _BREAK_A)


def test_pinned_sign_regression_outside_the_rejected_guard_band():
    d, V, a = _breaking_case_arrays()
    assert E.n_distinct(_BREAK_X) == 3 and np.isfinite(_BREAK_Y).all()            # admitted finite domain (A-1)
    closed = float(E.intercept_weights(_BREAK_X, 1) @ _BREAK_Y)
    pinned = float(np.polyfit(_BREAK_X, _BREAK_Y, 1)[-1])
    band = _OLD_BAND * (1.0 + abs(_BREAK_A) + np.abs(_BREAK_Y).max())
    assert abs(closed - _BREAK_A) > band                                          # OUTSIDE the old guard band: the hybrid used the closed form
    assert abs(pinned - _BREAK_A) <= E.exp_sign_tolerance(_BREAK_X, _BREAK_Y)      # ... but within the A-3 tolerance: the sign is 0
    got = E.pinned_signs(d, V, a)
    assert (got == 0.0).all()
    assert cc.exp_sign(list(_BREAK_X), list(_BREAK_Y), _BREAK_A) == 0.0 == got[0, 0, 0, 0]
    val, clamp, sigma = E.fit_exp_log(d, V, got, a)
    ref_val, ref_clamp = cc.exp_fit_fixed(list(_BREAK_X), list(_BREAK_Y), _BREAK_A, min_distinct=3)
    assert bool(clamp[0, 0, 0, 0]) is ref_clamp is True and val[0, 0, 0, 0] == ref_val == _BREAK_A   # sign 0 clamps to exactly a


def test_guard_band_mutant_fails_the_regression_oracle(tmp_path):
    mut = _load_estimators_with_guard_band_mutant(tmp_path)
    d, V, a = _breaking_case_arrays()
    dm = mut.design(_BREAK_X[None, None, :])
    mutant_sign = mut.pinned_signs(dm, V, a)
    assert (mutant_sign != 0.0).all() and set(mutant_sign.ravel().tolist()) <= {-1.0, 1.0}   # the rejected hybrid: closed-form fast path, nonzero
    assert (E.pinned_signs(d, V, a) == 0.0).all()
    assert mutant_sign[0, 0, 0, 0] != cc.exp_sign(list(_BREAK_X), list(_BREAK_Y), _BREAK_A)
    with pytest.raises(AssertionError):
        assert (mutant_sign == 0.0).all()                                         # the oracle assertion the mutant fails
    # on well-spread abscissas with a clearly nonzero intercept the mutant and the corrected code coincide
    dd = E.design(XS[None, None, :])
    VV = (0.9 * np.exp(-0.4 * XS))[None, None, None, :, None].repeat(5, axis=4)
    assert (mut.pinned_signs(dd, VV, np.zeros(5)) == E.pinned_signs(dd, VV, np.zeros(5))).all()


# ---- F-1 regression (round 05): the pinned weighted log-mode fit, unclamped, at aggregate level ----------------------------
# History. The round-05 reviewer's case (three abscissas clustered within 2e-7 of 1.5, y = 0.9 exp(-0.4 x), asymptote 0, eight
# identical seeds) had the rejected closed-form implementation aggregate to 0.9700957396765513 against the pinned
# 0.8999999988615335. Under amendment A-3 that abscissa set has lever ~ 3e14 and cond(V) ~ 4e7, so tau exceeds every value and
# the sign is 0 by the approved rule: the fit clamps and goes to avoid_log, so log mode is never reached there; and its degree-2
# normal equations are numerically singular on the Linux CI build (cond(A^T A) ~ 7e17). The requirement is unchanged and is
# re-expressed at spread 1e-2 (cond(A^T A) for QUAD ~ 6e10; sign +1 under A-3, unclamped, log mode): the implementation's
# log-mode aggregate must EQUAL the checker's pinned value, and the normal-equation mutant must diverge (4.8e-12 relative here).
_F1_X = 1.5 + 1e-2 * np.array([0.0, 1.0, 2.0, 0.0, 1.0])
_F1_Y = 0.9 * np.exp(-0.4 * _F1_X)

_NORMAL_EQUATION_LOG_MUTANT = """
def fit_exp_log(d, V, sigma, a):
    # MUTANT: the rejected closed-form weighted normal equations in place of the pinned numpy.polyfit fit
    raw = sigma[..., None, :] * (V - a)
    clamp = np.any(raw <= EXP_EPS, axis=3)
    sh = np.maximum(raw, EXP_EPS)
    w2 = sh
    x = d.X[None, :, :, :, None]
    ly = np.log(sh)
    s = w2.sum(3); sx = (w2 * x).sum(3); sy = (w2 * ly).sum(3)
    sxx = (w2 * x * x).sum(3); sxy = (w2 * x * ly).sum(3)
    den = s * sxx - sx * sx
    with np.errstate(divide="ignore", invalid="ignore"):
        bfit = (s * sxy - sx * sy) / den
        afit = (sy - bfit * sx) / s
    val = a + sigma * np.exp(afit)
    val[:, ~d.ok_exp] = np.nan
    clamp[:, ~d.ok_exp] = False
    return val, clamp, sigma
"""


def _load_estimators_with_source_mutant(tmp_path, start_marker, end_marker, replacement, name):
    src = (ROOT / "phase2" / "estimators.py").read_text(encoding="utf-8")
    start = src.index(start_marker); end = src.index(end_marker)
    mutated = src[:start] + replacement.lstrip("\n") + "\n\n" + src[end:]
    assert mutated != src
    mp = tmp_path / f"{name}.py"
    mp.write_text(mutated, encoding="utf-8")
    modname = f"phase2._{name}"
    spec_m = importlib.util.spec_from_file_location(modname, mp)
    mod = importlib.util.module_from_spec(spec_m)
    mod.__package__ = "phase2"
    sys.modules[modname] = mod
    try:
        spec_m.loader.exec_module(mod)
    finally:
        sys.modules.pop(modname, None)
    return mod


def _f1_arrays(mod):
    X = np.tile(_F1_X, (1, 8, 1))
    d = mod.design(X)
    V = np.tile(_F1_Y[None, None, None, :, None], (1, 1, 8, 1, 5))
    return d, V


def test_log_mode_regression_unclamped_clustered_abscissas():
    d, V = _f1_arrays(E)
    assert E.n_distinct(_F1_X) == 3 and bool(d.ok_exp[0, 0])
    res = E.aggregate(d, V, 4)
    sig = E.pinned_signs(d, V, np.zeros(5))
    val, clamp, _ = E.fit_exp_log(d, V, sig, np.zeros(5))
    assert (sig[0, 0, :, 0] == 1.0).all() and not clamp[0, 0, :, 0].any()          # sign +1 under A-3, UNCLAMPED
    assert int(res.exp_mode[0, 0, 0]) == 0                                          # log mode, no fallback
    ref, mode, flags = cc.exp_step_aggregate([(list(_F1_X), list(_F1_Y))] * 8, 0.0, min_distinct=3)
    assert mode == "log" and flags == []
    assert res.est[0, 0, 3, 0] == ref                                               # aggregate-level agreement with the pinned checker, exact
    assert abs(res.est[0, 0, 3, 0] - 0.9) < 1e-12                                   # the generating intercept


def test_normal_equation_log_mutant_fails_the_f1_aggregate_regression(tmp_path):
    mut = _load_estimators_with_source_mutant(tmp_path, "def fit_exp_log(", "def _ansatz_factory(", _NORMAL_EQUATION_LOG_MUTANT, "estimators_normal_equation_log_mutant")
    dm, V = _f1_arrays(mut)
    res_mut = mut.aggregate(dm, V, 4)
    d, V2 = _f1_arrays(E)
    ref = cc.exp_step_aggregate([(list(_F1_X), list(_F1_Y))] * 8, 0.0, min_distinct=3)[0]
    assert E.aggregate(d, V2, 4).est[0, 0, 3, 0] == ref
    assert int(res_mut.exp_mode[0, 0, 0]) == 0                                      # the mutant also runs log mode here
    assert res_mut.est[0, 0, 3, 0] != ref and abs(res_mut.est[0, 0, 3, 0] - ref) > 1e-13   # the normal-equation value differs (4.8e-12 relative)
    with pytest.raises(AssertionError):
        assert res_mut.est[0, 0, 3, 0] == ref                                       # the oracle assertion the mutant fails
    # on the nominal contract abscissas the two fits agree to rounding, so only the narrowed spread discriminates
    dd = E.design(np.tile(XS, (1, 8, 1))); VV = np.tile((0.9 * np.exp(-0.4 * XS))[None, None, None, :, None], (1, 1, 8, 1, 5))
    assert mut.aggregate(dd, VV, 4).est[0, 0, 3, 0] == pytest.approx(E.aggregate(dd, VV, 4).est[0, 0, 3, 0], rel=1e-10)


# ---- F-4 (round 05 follow-up): missing / non-finite observations null ONE EXP entry, never raise ----------------

def _f4_arrays():
    X = np.tile(XS, (1, 8, 1))
    d = E.design(X)
    V = np.tile((0.9 * np.exp(-0.4 * XS))[None, None, None, :, None], (1, 1, 8, 1, 5))
    return d, V.copy()


def test_missing_observation_nulls_only_the_affected_exp_entry_and_the_finite_control_is_pinned():
    d, V = _f4_arrays()
    a = E.asymptotes(4)
    # finite control: every EXP entry defined, log mode, and ZPI equals the pinned checker value exactly
    ctrl = E.aggregate(d, V, 4)
    ref, mode, flags = cc.exp_step_aggregate([(list(XS), list(V[0, 0, k, :, 0])) for k in range(8)], 0.0, min_distinct=3)
    assert mode == "log" and ctrl.est[0, 0, 3, 0] == ref and np.isfinite(ctrl.est[0, 0, 3, :]).all()
    assert (ctrl.exp_mode[0, 0] == 0).all()
    sig_ctrl = E.pinned_signs(d, V, a)
    # the Lead's reproduction: one NaN observation in seed 0, scale index 2, quantity ZPI
    for bad in (np.nan, np.inf, -np.inf):
        Vn = V.copy(); Vn[0, 0, 0, 2, 0] = bad
        sig = E.pinned_signs(d, Vn, a)
        assert np.isnan(sig[0, 0, 0, 0]) and (sig[0, 0, 1:, 0] == 1.0).all() and (sig[0, 0, :, 1:] == sig_ctrl[0, 0, :, 1:]).all()
        val, clamp, _ = E.fit_exp_log(d, Vn, sig, a)                      # must not raise (LinAlgError before F-4)
        assert np.isnan(val[0, 0, 0, 0]) and not clamp[0, 0, 0, 0]
        assert np.isfinite(val[0, 0, 1:, 0]).all() and np.isfinite(val[0, 0, :, 1:]).all()
        res = E.aggregate(d, Vn, 4)
        assert np.isnan(res.est[0, 0, 3, 0])                               # EXP ZPI undefined (no partial mean)
        assert np.array_equal(res.est[0, 0, 3, 1:], ctrl.est[0, 0, 3, 1:])  # the other EXP observables untouched
        assert (res.exp_mode[0, 0] == 0).all()                            # still log mode, no fallback triggered
        assert np.array_equal(res.est[0, 0, :3, 1:], ctrl.est[0, 0, :3, 1:])  # NONE/LIN/QUAD of other quantities untouched


def test_avoid_log_matches_checker_with_the_same_sign():
    for ys in (XS / 4, 0.05 * np.exp(XS), np.zeros(5)):
        s = cc.exp_sign(list(XS), list(ys), 0.0)
        got = E.exp_avoid_log_one(XS, ys, 0.0, s)
        ref = cc.exp_fit_avoid_log(list(XS), list(ys), 0.0, min_distinct=3)
        assert got == pytest.approx(ref, abs=1e-10)
    s0 = cc.exp_sign(list(XS), list(XS / 4), 0.0); assert s0 == 0.0                                       # A-3 fixture 1
    assert E.exp_avoid_log_one(XS, XS / 4, 0.0, s0) == cc.exp_fit_avoid_log(list(XS), list(XS / 4), 0.0, min_distinct=3)


def test_aggregate_matches_checker_step_aggregate_on_random_and_oracle_seeds():
    rng = np.random.default_rng(2)
    L = 4
    X = np.tile(XS, (2, 8, 1))
    d = E.design(X)
    V = rng.uniform(-0.5, 0.9, size=(6, 2, 8, 5, 5))
    V[0, 0, :, :, 0] = XS / 4                                            # A-3 fixture 1: 8 identical seeds -> sign 0 -> avoid_log
    V[1, 0, 3, :, 1] = 2.0 ** -L                                         # one seed exactly at the asymptote (raw = 0 -> clamp) among clean decays for PRET
    V[1, 0, [0, 1, 2, 4, 5, 6, 7], :, 1] = 2.0 ** -L + 0.9 * np.exp(-0.4 * XS)
    res = E.aggregate(d, V, L)
    a = E.asymptotes(L)
    for b in range(6):
        for n in range(2):
            for q in range(5):
                seed_data = [(list(X[n, k]), list(V[b, n, k, :, q])) for k in range(8)]
                ref, mode, flags = cc.exp_step_aggregate(seed_data, float(a[q]), min_distinct=3)
                got_mode = {0: "log", 1: "avoid_log", 2: "avoid_log_failed", 3: "fit_failure"}[int(res.exp_mode[b, n, q])]
                assert got_mode == mode, (b, n, q)
                got = res.seed_values  # empty unless requested; compare through est for ZPI/PRET
                if q == 0:
                    if ref is None:
                        assert np.isnan(res.est[b, n, 3, 0])
                    else:
                        assert res.est[b, n, 3, 0] == pytest.approx(ref, abs=1e-9)
                if q == 1:
                    if ref is None:
                        assert np.isnan(res.est[b, n, 3, 1])
                    else:
                        assert res.est[b, n, 3, 1] == pytest.approx(ref, abs=1e-9)
    ref0 = cc.exp_step_aggregate([(list(X[0, k]), list(V[0, 0, k, :, 0])) for k in range(8)], 0.0, min_distinct=3)
    assert ref0[1] == "avoid_log" and res.est[0, 0, 3, 0] == ref0[0]     # A-3 fixture 1 through the whole frozen order, equal to the checker
    assert int(res.exp_mode[0, 0, 0]) == 1 and int(res.exp_mode[1, 0, 1]) == 1   # the sign-0 seeds forced avoid_log for the whole step


def test_lin_quad_and_none_match_checker():
    rng = np.random.default_rng(3)
    X = np.tile(XS, (1, 8, 1)); X[0, 2] = [1.0, 1.0, 1.5, 2.0, 2.0]
    d = E.design(X)
    V = rng.normal(0, 0.4, size=(4, 1, 8, 5, 5))
    lin, quad = E.fit_lin_quad(d, V)
    for b in range(4):
        for k in range(8):
            for q in range(5):
                assert lin[b, 0, k, q] == pytest.approx(cc.poly_intercept(list(X[0, k]), list(V[b, 0, k, :, q]), 1), abs=1e-11)
                assert quad[b, 0, k, q] == pytest.approx(cc.poly_intercept(list(X[0, k]), list(V[b, 0, k, :, q]), 2), abs=1e-9)


def _dm_fixtures():
    pts = list(range(15, 24))
    def spike(peak, amp):
        c = np.zeros(48); c[peak - 1] = amp; return c
    def para(peak, shift):
        c = np.full(48, np.nan); c[14:23] = [1.0 - 0.1 * (n - peak - shift) ** 2 for n in pts]; return c
    fixtures = {
        "reviewer": np.stack([spike(19, 1.0)] * 4 + [spike(21, 1.0)] * 4),
        "tie": np.stack([np.where(np.isin(np.arange(1, 49), [18, 20]), 1.0, 0.0)] * 8),
        "para": np.stack([para(19, 0.2)] * 4 + [para(19, -0.3)] * 4),
        "edge": np.stack([spike(23, 1.0)] + [spike(19, 1.0)] * 7),
    }
    und = np.stack([spike(19, 1.0)] * 8); und[0, 18] = np.nan
    fixtures["undefined"] = und
    # non-finite seed values (amendment A-2 correction): +inf / -inf at the aggregate-matched step, elsewhere in the
    # window, mixed signs across seeds, in the timing path of a parabolic seed, and outside the window (ignored)
    for name, (k, n, v) in {"+inf_at_matched": (0, 19, np.inf), "-inf_at_matched": (0, 19, -np.inf),
                            "+inf_in_window": (3, 22, np.inf), "-inf_in_window": (5, 16, -np.inf)}.items():
        c = np.stack([spike(19, 1.0)] * 8); c[k, n - 1] = v; fixtures[name] = c
    mixed = np.stack([spike(19, 1.0)] * 8); mixed[0, 15] = np.inf; mixed[7, 21] = -np.inf; fixtures["mixed_inf"] = mixed
    tp = np.stack([para(19, 0.2)] * 4 + [para(19, -0.3)] * 4); tp[2, 17] = np.inf; fixtures["+inf_in_parabolic_timing"] = tp
    tm = np.stack([para(19, 0.2)] * 4 + [para(19, -0.3)] * 4); tm[6, 20] = -np.inf; fixtures["-inf_in_parabolic_timing"] = tm
    out = np.stack([spike(19, 1.0)] * 8); out[0, 30] = np.inf; out[1, 5] = -np.inf; fixtures["inf_outside_window"] = out
    return pts, fixtures


def _as_checker_curves(curves, pts):
    """The checker takes dicts step -> value; non-finite values are passed THROUGH as floats (inf, nan), never
    converted to None, so the checker's own non-finite rule is what is exercised."""
    return [{n: float(c[n - 1]) for n in pts} for c in curves]


def test_dm_seed_range_matches_checker_on_all_fixtures():
    pts, fixtures = _dm_fixtures()
    for name, curves in fixtures.items():
        got = E.dm_seed_range(curves, pts, +1.0)
        ref = cc.dm_seed_range(_as_checker_curves(curves, pts), pts, +1.0)
        assert got["matched_n"] == ref["matched_n"], name
        for key in ("amp_range", "timing_range"):
            if ref[key] is None:
                assert got[key] is None, (name, key)
            else:
                assert got[key] == pytest.approx(ref[key], abs=1e-12), (name, key)
        assert set(got["flags"]) == set(ref["flags"]), name
    assert E.dm_seed_range(fixtures["reviewer"], pts, +1.0)["amp_range"] == (0.0, 1.0)


def test_dm_seed_range_non_finite_seed_values_null_the_whole_range_in_both_implementations():
    pts, fixtures = _dm_fixtures()
    for name in ("+inf_at_matched", "-inf_at_matched", "+inf_in_window", "-inf_in_window", "mixed_inf",
                 "+inf_in_parabolic_timing", "-inf_in_parabolic_timing", "undefined"):
        for impl, curves in ((E.dm_seed_range, fixtures[name]), (cc.dm_seed_range, _as_checker_curves(fixtures[name], pts))):
            r = impl(curves, pts, +1.0)
            assert r["amp_range"] is None and r["timing_range"] is None, (name, impl.__module__)
            assert r["matched_n"] is None and r["flags"] == ["UNDEFINED"], (name, impl.__module__)
    # seven finite seeds never form a range on their own: the surviving seeds would give (1.0, 1.0) / (19.0, 19.0)
    for name in ("+inf_at_matched", "-inf_at_matched", "mixed_inf"):
        survivors = fixtures[name][np.isfinite(fixtures[name][:, 14:23]).all(axis=1)]
        assert len(survivors) in (6, 7) and E.dm_seed_range(survivors, pts, +1.0)["amp_range"] == (1.0, 1.0)
        assert E.dm_seed_range(fixtures[name], pts, +1.0)["amp_range"] is None
    # a non-finite value OUTSIDE the window is not a required seed value
    r = E.dm_seed_range(fixtures["inf_outside_window"], pts, +1.0)
    assert r["matched_n"] == 19 and r["amp_range"] == (1.0, 1.0) and r["timing_range"] == (19.0, 19.0)
    assert cc.dm_seed_range(_as_checker_curves(fixtures["inf_outside_window"], pts), pts, +1.0) == r


# ---- amendment A-3 (2026-09-09): portable zero branch of the EXP sign --------------------------------------------------

def test_a3_tolerance_matches_the_checker_and_fixture_1_is_sign_zero_through_the_frozen_order():
    for ys in (XS / 4, np.zeros(5), 10 * XS / 4, np.array([0.9, 0.6, 0.2, 0.1, 0.05])):
        assert E.exp_sign_tolerance(XS, ys) == pytest.approx(cc.exp_sign_tolerance(list(XS), list(ys)), rel=1e-15)
    assert E.exp_sign_tolerance(XS, XS / 4) == pytest.approx(7.965192e-14, rel=1e-6)
    d = E.design(XS[None, None, :])
    for ys, expected in ((XS / 4, 0.0), (np.zeros(5), 0.0), (XS / 4 + 1e-9, 1.0), (XS / 4 - 1e-9, -1.0), (XS / 4 + 1e-12, 1.0), (XS / 4 - 1e-12, -1.0)):
        V = ys[None, None, None, :, None].repeat(5, axis=4)
        assert (E.pinned_signs(d, V, np.zeros(5))[0, 0, 0] == expected).all(), ys


def test_a3_mutant_restoring_raw_np_sign_in_pinned_signs_fails_fixture_1(tmp_path):
    src = (ROOT / "phase2" / "estimators.py").read_text(encoding="utf-8")
    old = "                    sign[b, n, k, q] = 0.0 if abs(intercept - a[q]) <= tau else np.sign(-(a[q] - intercept))"
    assert src.count(old) == 1
    mut = _load_estimators_with_source_mutant(tmp_path, old, "    return sign", "                    sign[b, n, k, q] = np.sign(-(a[q] - intercept))   # MUTANT: raw np.sign, no A-3 tolerance\n", "estimators_raw_sign_mutant")
    d = mut.design(XS[None, None, :]); V = (XS / 4)[None, None, None, :, None].repeat(5, axis=4)
    got = mut.pinned_signs(d, V, np.zeros(5))[0, 0, 0]
    assert (got != 0.0).all() and set(got.tolist()) <= {-1.0, 1.0}          # raw sign: nonzero, platform-dependent
    assert (E.pinned_signs(E.design(XS[None, None, :]), V, np.zeros(5))[0, 0, 0] == 0.0).all()
    with pytest.raises(AssertionError):
        assert (got == 0.0).all()
