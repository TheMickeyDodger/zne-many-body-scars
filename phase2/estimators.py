"""Frozen estimator order (prereg §6.2, contract §C4.3), vectorised over a replicate axis.

Layout for one cell: abscissas X[n, k, j] (48 steps, 8 seeds, 5 scales), values
V[b, n, k, j, q] for the five raw quantities q = (ZPI, PRET, M_I, M_J, M_IJ).
Every closed-form step is evaluated identically for each replicate b. Two steps are
per-element loops by design: the EXP sign and the EXP log-mode weighted fit, which are
the SCALAR pinned `numpy.polyfit` calls for every (b, n, k, q) (amendment A-2
corrections, 2026-09-08: no closed-form fast path, no guard band, no normal-equation
substitute), and the scipy `curve_fit` of the avoid_log mode, which has no closed form. Nothing here is intended to change an estimator, an ordering, a seed,
a tie-break or a null/flag outcome relative to the checker's reference implementation
(tools/phase2_contract_check.py); tests/test_phase2_estimators.py compares the two on
synthetic fixtures. The EXP sign AND the EXP log-mode fit are the scalar pinned
`numpy.polyfit` calls for every element (A-2 correction rounds 04/05); the LIN/QUAD
intercepts remain ordinary least squares by normal equations, as the contract specifies
them and as the checker's `poly_intercept` also computes them.

Rank rule (amendment A-1): LIN >= 2, QUAD >= 3, EXP >= 3 distinct realized abscissas.
EXP sign (amendment A-2): np.sign(-(a - numpy.polyfit(x, y, 1)[-1])), zero at equality, in both
modes, decided by the scalar pinned call for every element; the pinned mitiq v1.0.0 convention,
never a '>= 0' ternary and never a closed-form intercept. Amendment A-3 (2026-09-09) makes the
zero branch reachable: sign = 0 when |intercept - a| <= tau = C*eps*cond(V)*max|y|*lever (C = 4),
computed per fit, for ANY intercept at or below tau including genuinely nonzero ones; the sign feeds
the clamp in fit_exp_log and the avoid_log initial guess.
DM companion seed range (amendment A-2): `dm_seed_range` below; every non-finite required seed
value (NaN, +inf, -inf, missing) is undefined and nulls the whole affected range.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
from scipy.optimize import curve_fit

from .observables import mloc_sign

EXP_EPS = 1.0e-6
RANK_RULE_2B = {"LIN": 2, "QUAD": 3, "EXP": 3}
EXTRAPOLATORS = ("NONE", "LIN", "QUAD", "EXP")
RAW = ("ZPI", "PRET", "M_I", "M_J", "M_IJ")
CURVE_QUANTITIES = ("ZPI", "PRET", "MLOC", "CZZ")
PEAK_OBS = ("ZPI", "PRET", "MLOC")
POLARITY = {"ZPI": -1.0, "PRET": 1.0, "MLOC": -1.0}


def asymptotes(L: int) -> np.ndarray:
    return np.array([0.0, 2.0 ** (-L), 0.0, 0.0, 0.0])


def n_distinct(xs) -> int:
    return len(set(float(x) for x in xs))


# ----------------------------------------------------------------- polynomial weights

def intercept_weights(x: np.ndarray, degree: int) -> np.ndarray:
    """w such that the least-squares polynomial intercept at 0 equals w @ y.
    Normal equations (A^T A) c = A^T y, c_0 = e_0^T (A^T A)^{-1} A^T y."""
    A = np.vander(np.asarray(x, float), degree + 1, increasing=True)
    ata = A.T @ A
    return np.linalg.solve(ata, A.T)[0]


@dataclass
class CellDesign:
    """Everything about a cell's abscissas that does not depend on data."""
    X: np.ndarray            # [n, k, j]
    w_lin: np.ndarray        # [n, k, j]
    w_quad: np.ndarray       # [n, k, j] (nan rows where QUAD rank fails)
    ok_lin: np.ndarray       # [n, k] bool
    ok_quad: np.ndarray      # [n, k] bool
    ok_exp: np.ndarray       # [n, k] bool
    n_distinct: np.ndarray   # [n, k] int


def design(X: np.ndarray) -> CellDesign:
    N, K, J = X.shape
    nd = np.zeros((N, K), int)
    w_lin = np.full((N, K, J), np.nan)
    w_quad = np.full((N, K, J), np.nan)
    for n in range(N):
        for k in range(K):
            nd[n, k] = n_distinct(X[n, k])
            if nd[n, k] >= RANK_RULE_2B["LIN"]:
                w_lin[n, k] = intercept_weights(X[n, k], 1)
            if nd[n, k] >= RANK_RULE_2B["QUAD"]:
                w_quad[n, k] = intercept_weights(X[n, k], 2)
    return CellDesign(X=X, w_lin=w_lin, w_quad=w_quad,
                      ok_lin=nd >= RANK_RULE_2B["LIN"], ok_quad=nd >= RANK_RULE_2B["QUAD"],
                      ok_exp=nd >= RANK_RULE_2B["EXP"], n_distinct=nd)


# ----------------------------------------------------------------- per-seed fits (step 2)

def fit_lin_quad(d: CellDesign, V: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """V[b, n, k, j, q] -> LIN[b, n, k, q], QUAD[b, n, k, q] (nan where the rank rule fails)."""
    lin = np.einsum("nkj,bnkjq->bnkq", np.nan_to_num(d.w_lin), V)
    quad = np.einsum("nkj,bnkjq->bnkq", np.nan_to_num(d.w_quad), V)
    lin[:, ~d.ok_lin] = np.nan
    quad[:, ~d.ok_quad] = np.nan
    return lin, quad


A3_SIGN_TOL_C = 4                        # amendment A-3 (2026-09-09): safety factor of the sign zero tolerance
A3_EPS_DOUBLE = 2.220446049250313e-16   # IEEE-754 double machine epsilon


def sign_tolerance_factors(x: np.ndarray) -> float:
    """cond(numpy.vander(x, 2)) * lever, lever = 1 + mean(x)^2 / var(x) with population variance (ddof=0); the data-independent
    part of the A-3 tolerance for one abscissa set."""
    x = np.asarray(x, float)
    cond = float(np.linalg.cond(np.vander(x, 2)))
    lever = 1.0 + float(np.mean(x)) ** 2 / float(np.var(x))
    return cond * lever


def exp_sign_tolerance(x: np.ndarray, y: np.ndarray) -> float:
    """Amendment A-3: tau = C * eps * cond(V) * max|y| * lever, computed per fit (never a constant)."""
    return A3_SIGN_TOL_C * A3_EPS_DOUBLE * sign_tolerance_factors(x) * float(np.max(np.abs(np.asarray(y, float))))


def pinned_signs(d: CellDesign, V: np.ndarray, a: np.ndarray) -> np.ndarray:
    """EXP sign for every (b, n, k, q) from the SCALAR pinned numpy.polyfit(x, y, 1)[-1] call (amendment A-2, corrected
    2026-09-08: no closed-form fast path, no guard band), with the zero branch made reachable by amendment A-3 (2026-09-09):
    sign = 0 when |intercept - a| <= tau = C * eps * cond(V) * max|y| * lever, else np.sign(-(a - intercept)). tau is computed
    per element from the data (the cond(V) * lever factor once per abscissa set); it is never a fixed number. Matches
    tools/phase2_contract_check.py::exp_sign. A missing/non-finite observation leaves that seed's sign undefined (nan);
    rank-failed (n, k) get sign 0 and are nulled downstream."""
    B, N, K, J, Q = V.shape
    sign = np.zeros((B, N, K, Q))
    finite = np.isfinite(V).all(axis=3)                            # [b,n,k,q]
    for n in range(N):
        for k in range(K):
            if not d.ok_exp[n, k]:
                continue
            x = d.X[n, k]
            factors = sign_tolerance_factors(x)
            for b in range(B):
                for q in range(Q):
                    if not finite[b, n, k, q]:
                        sign[b, n, k, q] = np.nan
                        continue
                    y = V[b, n, k, :, q]
                    intercept = float(np.polyfit(x, y, 1)[-1])
                    tau = A3_SIGN_TOL_C * A3_EPS_DOUBLE * factors * float(np.max(np.abs(y)))
                    sign[b, n, k, q] = 0.0 if abs(intercept - a[q]) <= tau else np.sign(-(a[q] - intercept))
    return sign


def fit_exp_log(d: CellDesign, V: np.ndarray, sigma: np.ndarray, a: np.ndarray):
    """mitiq v1.0.0 ExpFactory log mode with the PINNED weighted fit, per (b, n, k, q):
    shifted = max(sigma * (y - a), EXP_EPS); z = numpy.polyfit(x, ln(shifted), 1, w=sqrt(shifted)) (the scalar
    mitiq_polyfit call, exactly as tools/phase2_contract_check.py::exp_fit_fixed); intercept = a + sigma * exp(z[-1]).
    The closed-form weighted normal equations were removed (A-2 correction, round 05, 2026-09-08): they are not the
    pinned estimator and on clustered abscissas they give a different unclamped log-mode value
    (tests/test_phase2_estimators.py::test_log_mode_regression_unclamped_clustered_abscissas).
    `sigma` from pinned_signs (0 at equality within the A-3 tolerance: every point clamps, the value is exactly a, and
    the homogeneity rule sends the step to avoid_log with initial guess [0, -1]).
    Returns (intercept[b,n,k,q], clamp[b,n,k,q] bool, sigma[b,n,k,q]); nan where EXP rank fails."""
    B, N, K, J, Q = V.shape
    raw = sigma[..., None, :] * (V - a)                            # [b,n,k,j,q]
    clamp = np.any(raw <= EXP_EPS, axis=3)                         # [b,n,k,q]
    sh = np.maximum(raw, EXP_EPS)
    ly = np.log(sh)
    w = np.sqrt(sh)
    # Missing-input preservation (F-4, 2026-09-08): a seed with any non-finite observation or an undefined sign has
    # an undefined (nan) EXP intercept, exactly as before the pinned fit; nothing non-finite reaches numpy.polyfit
    # (weighted lstsq raises LinAlgError on non-finite weights). Other (b, n, k, q) entries are unaffected.
    finite = np.isfinite(V).all(axis=3) & np.isfinite(sigma)      # [b,n,k,q]
    afit = np.full((B, N, K, Q), np.nan)
    for n in range(N):
        for k in range(K):
            if not d.ok_exp[n, k]:
                continue
            x = d.X[n, k]
            for b in range(B):
                for q in range(Q):
                    if not finite[b, n, k, q]:
                        continue
                    afit[b, n, k, q] = np.polyfit(x, ly[b, n, k, :, q], 1, w=w[b, n, k, :, q])[-1]
    val = a + sigma * np.exp(afit)                                 # sigma = 0 -> exactly the asymptote (clamped)
    val[:, ~d.ok_exp] = np.nan
    clamp[:, ~d.ok_exp] = False
    return val, clamp, sigma


def _ansatz_factory(a):
    def ansatz(x, b, c):
        return a + b * np.exp(x * c)
    return ansatz


def exp_avoid_log_one(x: np.ndarray, y: np.ndarray, a: float, sign: float) -> float | None:
    """mitiq case 2 (asymptote given, avoid_log): p0 = [sign, -1] with the same pinned sign as the log mode,
    scipy defaults; None on the solver RuntimeError (EXP_FIT_FAILED)."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            opt, _ = curve_fit(_ansatz_factory(a), np.asarray(x, float), np.asarray(y, float), p0=[sign, -1.0])
    except RuntimeError:
        return None
    return float(a + opt[0])


# ----------------------------------------------------------------- aggregation (steps 3-4)

@dataclass
class StepResult:
    est: np.ndarray            # [b, n, 4 ext, 4 curve quantities] (nan = undefined)
    exp_mode: np.ndarray       # [b, n, 5 raw q] int: 0 log, 1 avoid_log, 2 avoid_log_failed, 3 fit_failure
    n_avoid_log_fits: int      # scipy curve_fit calls performed
    seed_values: dict          # per-seed intercepts for B-SEEDFIT when b == 1 (else empty)


def aggregate(d: CellDesign, V: np.ndarray, L: int, keep_seed_values: bool = False) -> StepResult:
    """Frozen order steps 2-4 for every replicate in V."""
    B, N, K, J, Q = V.shape
    a = asymptotes(L)
    lin, quad = fit_lin_quad(d, V)
    sigma = pinned_signs(d, V, a)
    exl, clamp, sigma = fit_exp_log(d, V, sigma, a)
    # homogeneity rule, per (b, n, q): any clamped seed -> every seed refit in avoid_log
    exp = exl.copy()
    mode = np.zeros((B, N, Q), dtype=np.int8)
    rank_fail = ~d.ok_exp                                          # [n, k]
    mode[:, rank_fail.any(axis=1), :] = 3
    trig = clamp.any(axis=2) & (mode == 0)                         # [b, n, q]
    n_calls = 0
    for b, n, q in zip(*np.nonzero(trig)):
        vals = []
        failed = False
        for k in range(K):
            v = exp_avoid_log_one(d.X[n, k], V[b, n, k, :, q], a[q], float(sigma[b, n, k, q]))
            n_calls += 1
            if v is None:
                failed = True
                break
            vals.append(v)
        if failed:
            exp[b, n, :, q] = np.nan
            mode[b, n, q] = 2
        else:
            exp[b, n, :, q] = vals
            mode[b, n, q] = 1
    exp[:, rank_fail, :] = np.nan
    # step 3 per seed: CZZ_s, MLOC_s; step 4 mean over seeds (nan propagates: no partial mean)
    none_seed = V[:, :, :, 0, :]                                   # lambda = 1 circuits per seed [b,n,k,q]
    ms = mloc_sign(L)
    est = np.full((B, N, 4, 4), np.nan)
    for e, arr in enumerate((none_seed, lin, quad, exp)):
        zpi, pret, mi, mj, mij = (arr[..., i] for i in range(5))
        czz = mij - mi * mj
        mloc = ms * mi
        est[:, :, e, 0] = zpi.mean(axis=2)
        est[:, :, e, 1] = pret.mean(axis=2)
        est[:, :, e, 2] = mloc.mean(axis=2)
        est[:, :, e, 3] = czz.mean(axis=2)
    seed_values = {}
    if keep_seed_values:
        seed_values = {"LIN": lin, "QUAD": quad, "EXP": exp, "EXP_LOG": exl, "clamp": clamp, "NONE": none_seed}
    return StepResult(est=est, exp_mode=mode, n_avoid_log_fits=n_calls, seed_values=seed_values)


# ----------------------------------------------------------------- schedule and matching (§C4.4)

def find_peaks(y: np.ndarray, d_min: int = 5) -> list[int]:
    """y indexed 1..N (y[0] unused). Returns accepted 1-based peak steps."""
    N = len(y) - 1
    acc = []
    for n in range(2, N):
        if y[n] > y[n - 1] and y[n] >= y[n + 1]:
            if acc and n - acc[-1] < d_min:
                if y[n] > y[acc[-1]]:
                    acc[-1] = n
                continue
            acc.append(n)
    return acc


def windows(peaks: list[int], w: int = 4, n_max: int = 48) -> list[dict]:
    import math
    out = []
    for i, nk in enumerate(peaks):
        lo, hi = max(1, nk - w), min(n_max, nk + w)
        flags = []
        if i > 0 and nk - peaks[i - 1] < 2 * w + 1:
            lo = max(lo, math.ceil((peaks[i - 1] + nk + 1) / 2)); flags.append("WINDOW_TRUNCATED")
        if i + 1 < len(peaks) and peaks[i + 1] - nk < 2 * w + 1:
            hi = min(hi, math.floor((nk + peaks[i + 1] - 1) / 2)); flags.append("WINDOW_TRUNCATED")
        pts = list(range(lo, hi + 1))
        if len(pts) < 3:
            flags.append("UNAVAILABLE")
        out.append({"n_ref": nk, "points": pts, "flags": flags,
                    "timing_testable": all(p in pts for p in range(nk - 2, nk + 3))})
    return out


def parabolic_offset(ym, y0, yp):
    """Vectorised EQ-B6 timing offset with the fallback rule: (offset, fallback)."""
    den = ym - 2 * y0 + yp
    with np.errstate(divide="ignore", invalid="ignore"):
        off = 0.5 * (ym - yp) / den
    fb = (den >= 0) | (np.abs(off) > 1) | ~np.isfinite(off)
    return np.where(fb, 0.0, off), fb


def match_peaks(curves: np.ndarray, points: list[int], polarity: float):
    """curves[b, n(1..48 at index n-1)] -> (amplitude[b], timing[b], defined_amp[b], defined_t[b]).
    argmax over the window (earliest tie), interior test, parabolic timing; a replicate with any
    undefined window value has undefined amplitude and timing; NO_INTERIOR_PEAK or INTERP_FALLBACK
    makes the replicate timing undefined (prereg §6.2 step 4)."""
    pts = np.asarray(points) - 1
    W = curves[:, pts] * polarity                                  # [b, w]
    any_nan = np.isnan(W).any(axis=1)
    Wf = np.where(np.isnan(W), -np.inf, W)
    idx = np.argmax(Wf, axis=1)                                    # first max = earliest tie
    best = pts[idx]                                                # 0-based step index
    amp = curves[np.arange(len(curves)), best]
    interior = (idx > 0) & (idx < len(pts) - 1)
    ym = np.where(interior, W[np.arange(len(curves)), np.clip(idx - 1, 0, len(pts) - 1)], np.nan)
    y0 = W[np.arange(len(curves)), idx]
    yp = np.where(interior, W[np.arange(len(curves)), np.clip(idx + 1, 0, len(pts) - 1)], np.nan)
    off, fb = parabolic_offset(ym, y0, yp)
    timing = (best + 1) + off
    def_amp = ~any_nan
    def_t = def_amp & interior & ~fb
    amp = np.where(def_amp, amp, np.nan)
    timing = np.where(def_t, timing, np.nan)
    return amp, timing, def_amp, def_t


def peak_replicates(est: np.ndarray, schedule: list[dict]) -> dict:
    """est[b, n, ext, q] -> per (ext, obs, k) arrays of amplitude/timing/defined over b."""
    out = {}
    for e, ename in enumerate(EXTRAPOLATORS):
        for qi, obs in enumerate(PEAK_OBS):
            for k, win in enumerate(schedule, start=1):
                if "UNAVAILABLE" in win["flags"]:
                    continue
                amp, t, da, dt = match_peaks(est[:, :, e, qi], win["points"], POLARITY[obs])
                out[(ename, obs, k)] = {"amplitude": amp, "timing": t, "defined_amp": da, "defined_timing": dt}
    return out


# ----------------------------------------------------------------- DM companion seed range (amendment A-2)

def dm_seed_range(seed_curves: np.ndarray, points: list[int], polarity: float):
    """seed_curves[k, 48] per-seed DM plug-in curve -> dict with the aggregate-matched step, the amplitude
    range over ALL seeds at that step, the timing range of each seed's OWN matched peak inside the same
    window, and flags. A seed value is undefined when it is not finite (NaN, +inf, -inf; a missing value
    is NaN in this array layout). Any undefined required seed nulls the whole amplitude or timing range
    (no partial range). Mirrors tools/phase2_contract_check.py::dm_seed_range."""
    seed_curves = np.asarray(seed_curves, float)
    seed_curves = np.where(np.isfinite(seed_curves), seed_curves, np.nan)   # every non-finite value is undefined
    pts = np.asarray(points) - 1
    agg = seed_curves.mean(axis=0)[None, :]                        # nan propagates: undefined step
    if not np.isfinite(agg[0, pts]).all():
        return {"matched_n": None, "amp_range": None, "timing_range": None, "flags": ["UNDEFINED"]}
    amp, t, da, dt = match_peaks(agg, points, polarity)
    W = agg[0, pts] * polarity
    n_hat = int(pts[np.argmax(W)]) + 1
    amps = seed_curves[:, n_hat - 1]
    amp_range = (float(amps.min()), float(amps.max())) if np.isfinite(amps).all() else None
    ts_amp, ts, das, dts = match_peaks(seed_curves, points, polarity)
    flags = []
    if (~dts).any():
        timing_range = None
        flags.append("NO_INTERIOR_PEAK" if (das & ~dts).any() else "UNDEFINED")
    else:
        timing_range = (float(ts.min()), float(ts.max()))
    return {"matched_n": n_hat, "amp_range": amp_range, "timing_range": timing_range, "flags": flags}
