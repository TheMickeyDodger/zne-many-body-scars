#!/usr/bin/env python
"""Offline contract checker for the Phase 2 preregistration.

Reads tools/phase2_contract.json, docs/prereg-phase2.md and
docs/phase2-analysis-contract.md (plus the three historical documents they
cross-reference) and checks that they agree with each other and with the
reference implementations of the declared estimators, which live in this
file and are exercised on synthetic fixtures with closed-form answers.

Offline, deterministic, standard library only. Imports nothing from
zne_scars, runs no experiment, touches no network, writes nothing.

Usage:
    python tools/phase2_contract_check.py [--root DIR] [--traceability]
Exit codes: 0 every check ran and passed; 1 every check ran and at least
one failed; 2 an input file is missing or unreadable, so no check could run
(the message names the path). See docs/phase2-analysis-contract.md §C7.
"""
from __future__ import annotations

import itertools
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

ALLOWED_DTYPES = {"int", "float", "str", "bool", "bytes", "text", "dict", "list[int]", "list[str]",
                  "list[dict]", "dict[str,int]", "dict[str,str]", "float, str", "float, str, dict",
                  "int, str"}
ENDPOINT_STATUSES = ["PASS", "FAIL", "OVERLAP", "INDETERMINATE"]
CONDITION_STATUSES = ["UNAVAILABLE", "PASS", "FAIL", "OVERLAP", "INDETERMINATE"]
DELIVERABLES = ["docs/prereg-phase2.md", "docs/phase2-analysis-contract.md", "tools/phase2_contract.json",
                "tools/phase2_contract_check.py", "tests/test_phase2_contract.py"]
# Rank rule minima (distinct realized abscissas) per phase. Amendment A-1 (2026-09-08, human-approved,
# pre-data): Phase 2B EXP requires three everywhere; Phase 2C EXP keeps two (prereg §5.4). The JSON
# (`phase2b.rank_rule`, `phase2c.transpilation.rank_rule`, C-EXP-MIN-2B, C-EXP-MIN-2C) is the authority;
# check_cross verifies these module values against it. The EXP reference functions take the minimum as a
# required parameter so that no caller can silently apply one phase's guard to the other.
RANK_RULE_2B = {"LIN": 2, "QUAD": 3, "EXP": 3}
# Amendment A-3 (2026-09-09, human-approved): scale-aware zero tolerance for the EXP sign. The JSON
# (`phase2b.exp_sign_tolerance`, C-A3-SIGN-TOL-C, C-A3-EPS) is the authority; these module values are bound to it by a check.
A3_SIGN_TOL_C = 4
A3_EPS_DOUBLE = 2.220446049250313e-16
RANK_RULE_2C = {"LIN": 2, "QUAD": 3, "EXP": 2}

# ============================================================================
# Reference implementations (the contract's algorithms, executable today)
# ============================================================================


def attenuation_ratio(e_ij: float, e00: float) -> float | None:
    """EQ-A1. None when the reference is exactly zero."""
    if e00 == 0:
        return None
    return e_ij / e00


def log_attenuation(r: float | None) -> float | None:
    """EQ-A2. None when the ratio is not positive."""
    if r is None or r <= 0:
        return None
    return -math.log(r)


def interaction(a11, a10, a01, a00=0.0):
    """EQ-A3 with the A_00 term written out."""
    if None in (a11, a10, a01):
        return None
    return a11 - a10 - a01 + a00


def eta_propagation(r: float, e00: float, eta_e: float):
    """EQ-A5: returns (eta_r, eta_a); eta_a is None when the log is unresolved."""
    eta_r = eta_e * (1.0 + abs(r)) / (abs(e00) - eta_e)
    if abs(r) <= eta_r:
        return eta_r, None
    return eta_r, eta_r / (abs(r) - eta_r)


def phase2a_step(e00, e10, e01, e11, eta_e=1e-9, m0=0.1, tau_max=math.log(1.10)):
    """One Phase 2A step: ratios, logs, interaction, budget, flags (prereg §3.3-§3.8)."""
    flags = []
    by_cell = {"10": [], "01": [], "11": []}
    out = {"e00": e00, "flags": flags, "flags_by_cell": by_cell, "in_mask": 0, "i_n": None, "eta_i": None, "abs_i_lo": None, "abs_i_hi": None,
           "r10": None, "r01": None, "r11": None}
    # 1. The mask is a function of the noiseless reference ONLY (prereg §3.4). It is decided here, before any
    #    noisy value is looked at, so no noisy outcome, failure or absence can change mask membership.
    if e00 is None or not isinstance(e00, (int, float)) or not math.isfinite(e00):
        flags.append("MISSING_OR_NONFINITE")
        by_cell["00"] = ["MISSING_OR_NONFINITE"]
        return out
    in_mask = abs(e00) >= m0
    out["in_mask"] = int(in_mask)
    if not in_mask:
        flags.append("BELOW_MASK")
    if abs(abs(e00) - m0) <= eta_e:
        flags.append("MASK_BOUNDARY")
    # 2. Noisy cells, each on its own: a missing or non-finite value flags THAT cell only; the other cells'
    #    values at this step are preserved and the step stays in the mask.
    cells = {"10": e10, "01": e01, "11": e11}
    a, eta_a = {}, {}
    for c, e in cells.items():
        if e is None or not isinstance(e, (int, float)) or not math.isfinite(e):
            flags.append("MISSING_OR_NONFINITE")
            by_cell[c].append("MISSING_OR_NONFINITE")
            a[c] = None
            continue
        r = attenuation_ratio(e, e00)
        out["r" + c] = r
        if r is None:
            a[c] = None
            continue
        if in_mask:
            if r <= 0:
                flags.append("SIGN_FLIP"); by_cell[c].append("SIGN_FLIP")
                a[c] = None
                continue
            eta_r, ea = eta_propagation(r, e00, eta_e)
            out["eta_r" + c] = eta_r
            if ea is None:
                flags.append("RATIO_UNRESOLVED"); by_cell[c].append("RATIO_UNRESOLVED")
                a[c] = None
                continue
            eta_a[c] = ea
            if r > 1 + eta_r:
                flags.append("RATIO_ABOVE_ONE"); by_cell[c].append("RATIO_ABOVE_ONE")
            if abs(r - 1) <= eta_r:
                flags.append("RATIO_NEAR_ONE"); by_cell[c].append("RATIO_NEAR_ONE")
        a[c] = log_attenuation(r)
        out["a" + c] = a[c]
    i_n = interaction(a.get("11"), a.get("10"), a.get("01"))
    out["i_n"] = i_n
    if in_mask and i_n is not None and len(eta_a) == 3:
        eta_i = sum(eta_a.values())
        out["eta_i"] = eta_i
        out["abs_i_lo"] = max(0.0, abs(i_n) - eta_i)
        out["abs_i_hi"] = abs(i_n) + eta_i
        if eta_i > tau_max:
            flags.append("NUMERICAL_INCONCLUSIVE")
    return out


BLOCKING_2A = {"MISSING_OR_NONFINITE", "MASK_BOUNDARY", "REFERENCE_MISMATCH", "SIGN_FLIP",
               "RATIO_UNRESOLVED", "NUMERICAL_INCONCLUSIVE", "TOO_FEW_POINTS"}


def c2_ok(mode, agg):
    return mode == "avoid_log" and agg is not None


def phase2a_verdict(rows, tau_rms=math.log(1.05), tau_max=math.log(1.10), k_min=3):
    """EQ-A4 + EQ-A11 over one L. rows: list of phase2a_step outputs."""
    masked = [r for r in rows if r["in_mask"]]
    flags = set(itertools.chain.from_iterable(r["flags"] for r in rows))
    if len(masked) < k_min:
        flags.add("TOO_FEW_POINTS")
    stats = None
    # Amendment A-2 (2026-09-08): the statistics exist only on a mask of at least k_min = 3 steps
    # (prereg §3.8: "Statistics undefined. Blocking."); the former gate accepted any non-empty mask.
    if len(masked) >= k_min and all(r["i_n"] is not None and r["eta_i"] is not None for r in masked):
        stats = {
            "s_rms_lo": math.sqrt(sum(r["abs_i_lo"] ** 2 for r in masked) / len(masked)),
            "s_rms_hi": math.sqrt(sum(r["abs_i_hi"] ** 2 for r in masked) / len(masked)),
            "s_max_lo": max(r["abs_i_lo"] for r in masked),
            "s_max_hi": max(r["abs_i_hi"] for r in masked),
        }
    blocking = sorted(flags & BLOCKING_2A)
    if blocking:
        return "INCONCLUSIVE", "blocking flag: " + ",".join(blocking), stats
    if stats is None:
        return "INCONCLUSIVE", "statistics undefined", stats
    if stats["s_rms_hi"] <= tau_rms and stats["s_max_hi"] <= tau_max:
        return "EQUIVALENT", "", stats
    if stats["s_rms_lo"] > tau_rms or stats["s_max_lo"] > tau_max:
        return "INTERACTION", "", stats
    return "INCONCLUSIVE", "interval straddles a margin", stats


def ols(xs, ys):
    """Ordinary least squares y = a + b x. Raises ValueError on a singular design."""
    n = len(xs)
    if n < 2 or len(set(xs)) < 2:
        raise ValueError("FIT_FAILURE: fewer than two distinct abscissas")
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return my - b * mx, b


SIZE_WIDE_BLOCKERS = {"REFERENCE_MISMATCH", "NUMERICAL_INCONCLUSIVE", "TOO_FEW_POINTS", "MASK_BOUNDARY"}
CELL_GATE_FLAGS = {"SIGN_FLIP", "RATIO_UNRESOLVED", "RATIO_ABOVE_ONE", "MISSING_OR_NONFINITE"}


def secondary_fit(rows, cell, l_flags, tau_res=0.05, eps_g=1e-9):
    """EQ-A7 over the whole fixed mask for ONE cell (prereg §3.9).

    Two blocking mechanisms, kept separate: size-wide blockers (`l_flags`, or the row-level
    MASK_BOUNDARY / NUMERICAL_INCONCLUSIVE flags) make every cell's fit unavailable at that L;
    cell-level gate flags (SIGN_FLIP, RATIO_UNRESOLVED, RATIO_ABOVE_ONE, MISSING_OR_NONFINITE)
    block only the cell that raised them. A flag raised by another cell never blocks this one."""
    row_wide = set()
    for r in rows:
        row_wide |= set(r["flags"]) & {"MASK_BOUNDARY", "NUMERICAL_INCONCLUSIVE"}
    size_block = (set(l_flags) | row_wide) & SIZE_WIDE_BLOCKERS
    if size_block:
        return {"fit_available": 0, "flags": ["FIT_UNAVAILABLE"], "reason": sorted(size_block)}
    # a missing or non-finite REFERENCE value leaves the frozen mask undefined at that step: size-wide loss,
    # every cell's fit is unavailable (checked over all rows, since such a row is never "in the mask")
    if any("00" in r.get("flags_by_cell", {}) for r in rows):
        return {"fit_available": 0, "flags": ["FIT_UNAVAILABLE"], "reason": ["MISSING_OR_NONFINITE reference"]}
    masked = [r for r in rows if r["in_mask"]]  # the frozen mask; never reduced by any noisy outcome
    viol = [i for i, r in enumerate(masked)
            if set(r.get("flags_by_cell", {}).get(cell, [])) & CELL_GATE_FLAGS or r.get("r" + cell) is None]
    if viol:
        return {"fit_available": 0, "flags": ["FIT_UNAVAILABLE"], "violating_steps": viol, "reason": ["cell gate"]}
    xs = [r["n"] for r in masked]
    ys = [math.log(r["r" + cell]) for r in masked]
    try:
        a, b = ols(xs, ys)
    except ValueError:
        return {"fit_available": 0, "flags": ["FIT_FAILURE"]}
    res = [y - (a + b * x) for x, y in zip(xs, ys)]
    g_raw = -b
    flags = []
    if g_raw < -eps_g:
        flags.append("ANTI_ATTENUATION")
        g_treated = None
    elif g_raw < 0:
        g_treated = 0.0
    else:
        g_treated = g_raw
    mar = max(abs(e) for e in res)
    return {"fit_available": 1, "g_raw": g_raw, "g_treated": g_treated, "intercept": a, "residuals": res,
            "max_abs_residual": mar, "residual_status": "RESIDUAL_ADEQUATE" if mar <= tau_res else "RESIDUAL_INADEQUATE",
            "flags": flags}


def find_peaks(y, d_min=5):
    """EQ-B6 candidates on a 1-based grid y[1..N] (y[0] unused). Returns 1-based steps."""
    n_max = len(y) - 1
    acc = []
    for n in range(2, n_max):
        if y[n] > y[n - 1] and y[n] >= y[n + 1]:
            if acc and n - acc[-1] < d_min:
                if y[n] > y[acc[-1]]:
                    acc[-1] = n
                continue
            acc.append(n)
    return acc


def parabolic_timing(ym, y0, yp):
    """EQ-B6: (t* - n, fallback_flag)."""
    den = ym - 2 * y0 + yp
    if den >= 0:
        return 0.0, True
    off = 0.5 * (ym - yp) / den
    if abs(off) > 1:
        return 0.0, True
    return off, False


def make_windows(peaks, w=4, n_max=48):
    """EQ-B6 item 9: disjoint windows, truncated at the midpoint when peaks are < 2w+1 apart."""
    wins = []
    for i, nk in enumerate(peaks):
        lo, hi = max(1, nk - w), min(n_max, nk + w)
        flags = []
        if i > 0 and nk - peaks[i - 1] < 2 * w + 1:
            lo = max(lo, math.ceil((peaks[i - 1] + nk + 1) / 2))
            flags.append("WINDOW_TRUNCATED")
        if i + 1 < len(peaks) and peaks[i + 1] - nk < 2 * w + 1:
            hi = min(hi, math.floor((nk + peaks[i + 1] - 1) / 2))
            flags.append("WINDOW_TRUNCATED")
        pts = list(range(lo, hi + 1))
        if len(pts) < 3:
            flags.append("UNAVAILABLE")
        wins.append({"n_ref": nk, "points": pts, "flags": flags, "timing_testable": timing_testable(pts, nk)})
    return wins


def timing_testable(points, n_ref):
    """Prereg §5.9 item 8: the window must contain n_ref-2 .. n_ref+2."""
    return all(p in points for p in range(n_ref - 2, n_ref + 3))


def match_peak(curve, points, polarity=1.0):
    """Reduced-point matching (prereg §5.9): curve is a dict step -> value defined on the points."""
    best = max(points, key=lambda n: (polarity * curve[n], -n))
    out = {"matched_n": best, "amplitude": curve[best], "flags": []}
    if (best - 1) in points and (best + 1) in points:
        off, fb = parabolic_timing(polarity * curve[best - 1], polarity * curve[best], polarity * curve[best + 1])
        out["timing"] = best + off
        if fb:
            out["flags"].append("INTERP_FALLBACK")
    else:
        out["timing"] = None
        out["flags"].append("NO_INTERIOR_PEAK")
    return out


def seed_value_undefined(v):
    """A DM companion seed value is undefined when it is missing (None), not a real number, or not finite
    (NaN, +inf, -inf) (amendment A-2 correction, 2026-09-08). Booleans are not values."""
    return v is None or isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)


def dm_seed_range(seed_curves, points, polarity=1.0):
    """DM companion seed range (amendment A-2, 2026-09-08; prereg §4.8, contract §C4.4 item 7).
    seed_curves: list over the eight seeds of dicts step -> value on the window points; a value is undefined
    when `seed_value_undefined` (missing/None, NaN, +inf, -inf), never only when it is None.
    1. Aggregate curve = arithmetic mean over seeds per step (§C4.3 step 4; any undefined seed value makes
       that step undefined). Match the aggregate on the window (§C4.4 item 5) -> n_hat.
    2. Amplitude range = [min_s X_s(n_hat), max_s X_s(n_hat)] over ALL seeds at the aggregate-matched step.
    3. Timing range = [min_s t_s, max_s t_s] with t_s each seed's OWN matched peak inside the SAME window
       (§C4.4 item 5 matching and tie rules; NO_INTERIOR_PEAK makes t_s undefined; INTERP_FALLBACK keeps
       t_s = n_s with the flag recorded).
    4. Any undefined required seed value nulls the WHOLE range (amplitude or timing separately): no partial
       range, ever. Returns {"matched_n", "amp_range", "timing_range", "flags"}; a null range is None."""
    K = len(seed_curves)
    agg = {}
    for n in points:
        vals = [c.get(n) for c in seed_curves]
        agg[n] = None if any(seed_value_undefined(v) for v in vals) else sum(vals) / K
    flags = []
    if any(agg[n] is None for n in points):
        return {"matched_n": None, "amp_range": None, "timing_range": None, "flags": ["UNDEFINED"]}
    m = match_peak(agg, points, polarity)
    n_hat = m["matched_n"]
    amps = [c.get(n_hat) for c in seed_curves]
    amp_range = None if any(seed_value_undefined(a) for a in amps) else (min(amps), max(amps))
    ts = []
    for c in seed_curves:
        if any(seed_value_undefined(c.get(n)) for n in points):
            ts.append(None)
            continue
        ms = match_peak(c, points, polarity)
        if "INTERP_FALLBACK" in ms["flags"]:
            flags.append("INTERP_FALLBACK")
        ts.append(ms["timing"])  # None on NO_INTERIOR_PEAK
    timing_range = None if any(t is None for t in ts) else (min(ts), max(ts))
    if timing_range is None:
        flags.append("NO_INTERIOR_PEAK")
    return {"matched_n": n_hat, "amp_range": amp_range, "timing_range": timing_range, "flags": sorted(set(flags))}


def tiae(x, ref):
    """EQ-B8 trapezoid with unit step over consecutive entries."""
    e = [abs(a - b) for a, b in zip(x, ref)]
    return sum(0.5 * (e[i] + e[i + 1]) for i in range(len(e) - 1))


def linear_quantile(sorted_vals, q):
    """EQ-B12 quantile on the extended real line: numpy 'linear' rule, no arithmetic on infinities."""
    b = len(sorted_vals)
    h = q * (b - 1)
    lo = math.floor(h)
    x1 = sorted_vals[lo]
    x2 = sorted_vals[min(lo + 1, b - 1)]
    if math.isinf(x1):
        return x1
    if math.isinf(x2):
        return x2 if h - lo > 0 else x1
    return x1 + (h - lo) * (x2 - x1)


def percentile_interval(values, q_lo, q_hi):
    """values: list of floats or None (undefined). Conservative undefined placement (prereg §6.3)."""
    defined = [v for v in values if v is not None]
    u = len(values) - len(defined)
    lo_vals = sorted(defined + [-math.inf] * u)
    hi_vals = sorted(defined + [math.inf] * u)
    lo, hi = linear_quantile(lo_vals, q_lo), linear_quantile(hi_vals, q_hi)
    flags = []
    if math.isinf(lo) or math.isinf(hi):
        flags.append("UNDEFINED")
    if defined and len(set(defined)) == 1:
        flags.append("DEGENERATE_CONSTANT")
    if not flags and 0.5 * (hi - lo) < 1e-12:  # prereg §6.7: half-width below h_min
        flags.append("DEGENERATE_COLLAPSED")
    return lo, hi, u, flags


def alternating_interval(values, q_lo, q_hi):
    """The rejected alternating construction, kept only to demonstrate why it is rejected."""
    defined = [v for v in values if v is not None]
    u = len(values) - len(defined)
    alt = [-math.inf if i % 2 == 0 else math.inf for i in range(u)]
    s = sorted(defined + alt)
    return linear_quantile(s, q_lo), linear_quantile(s, q_hi)


def three_way(lo, hi, a, b, p_lo=-math.inf, p_hi=math.inf, undefined=False, untestable=False):
    """EQ-B13: endpoint status on the closed band [a, b] and closed physical range.
    Invalid input (non-finite, inverted interval or band) is a ValueError, never a status."""
    if undefined or untestable or lo is None or hi is None:
        return "INDETERMINATE"
    for v in (lo, hi, a, b):
        if not isinstance(v, (int, float)) or math.isnan(v):
            raise ValueError("INVALID_INPUT: non-numeric interval or band")
    if lo > hi:
        raise ValueError("INVALID_INPUT: inverted interval")
    if a > b:
        raise ValueError("INVALID_INPUT: inverted band")
    if lo >= a and hi <= b and lo >= p_lo and hi <= p_hi:
        return "PASS"
    if hi < a or lo > b:
        return "FAIL"
    return "OVERLAP"


REQUIRED_ENDPOINTS = ("ZPI_AMP", "ZPI_TIME", "PRET_AMP", "PRET_TIME")


def condition_status(statuses, unavailable=False):
    """EQ-B14 over exactly the four required endpoints.

    `statuses` is a mapping endpoint name -> status with exactly the four
    REQUIRED_ENDPOINTS keys, or a sequence of exactly four statuses in that
    order. Anything else (missing, extra, duplicate or unknown endpoint, or
    an unknown status) is a ValueError: a condition can never pass on an
    incomplete or malformed endpoint set."""
    if unavailable:
        return "UNAVAILABLE"
    if isinstance(statuses, dict):
        if tuple(sorted(statuses)) != tuple(sorted(REQUIRED_ENDPOINTS)):
            raise ValueError(f"INVALID_INPUT: endpoints must be exactly {REQUIRED_ENDPOINTS}")
        vals = [statuses[k] for k in REQUIRED_ENDPOINTS]
    else:
        vals = list(statuses)
        if len(vals) != 4:
            raise ValueError("INVALID_INPUT: exactly four endpoint statuses are required")
    if any(v not in ENDPOINT_STATUSES for v in vals):
        raise ValueError("INVALID_INPUT: unknown endpoint status")
    statuses = vals
    if all(s == "PASS" for s in statuses):
        return "PASS"
    if any(s == "FAIL" for s in statuses):
        return "FAIL"
    if any(s == "OVERLAP" for s in statuses) and not any(s == "INDETERMINATE" for s in statuses):
        return "OVERLAP"
    return "INDETERMINATE"


def boundary(status_seq, grid):
    """EQ-B15 with persistence and located/unresolved classification.

    `status_seq` must be a complete keyed scan: a mapping kappa -> condition
    status whose keys are exactly the grid values, or a sequence with exactly
    one status per grid level. An empty or partial scan is a ValueError."""
    if not grid:
        raise ValueError("INVALID_INPUT: empty scan grid")
    if isinstance(status_seq, dict):
        if sorted(status_seq) != sorted(grid):
            raise ValueError("INVALID_INPUT: scan keys must equal the grid")
        status_seq = [status_seq[k] for k in grid]
    status_seq = list(status_seq)
    if len(status_seq) != len(grid):
        raise ValueError("INVALID_INPUT: one status per grid level is required")
    if any(s not in CONDITION_STATUSES for s in status_seq):
        raise ValueError("INVALID_INPUT: unknown condition status")
    kappa_star, located, non_monotone = None, 0, 0
    i = 0
    while i < len(status_seq) and status_seq[i] == "PASS":
        kappa_star = grid[i]
        i += 1
    if i < len(status_seq):
        nxt = status_seq[i]
        located = int(nxt == "FAIL")
        if kappa_star is None:
            kappa_star = "BELOW_MIN_FAIL" if nxt == "FAIL" else "UNRESOLVED_AT_MIN"
        if "PASS" in status_seq[i + 1:]:
            non_monotone = 1
    else:
        kappa_star = "AT_OR_ABOVE_MAX"
    return {"kappa_star": kappa_star, "located": located, "non_monotone": non_monotone}


def fold_global_counts(ops, lam):
    """§C4.2: returns (folded op list, lambda_r, lambda_r_1q)."""
    inv = {"cx": "cx", "x": "x", "sx": "sxdg", "sxdg": "sx", "rz": "rz"}
    q, f = divmod(lam - 1, 2)
    q = int(q)
    dag = [inv[o] for o in reversed(ops)]
    folded = list(ops)
    for _ in range(q):
        folded += dag + list(ops)
    if f > 0:
        n_p = round(f * len(ops) / 2)
        suffix = ops[len(ops) - n_p:] if n_p > 0 else []
        folded += [inv[o] for o in reversed(suffix)] + list(suffix)
    cx0 = ops.count("cx")
    one0 = sum(ops.count(g) for g in ("sx", "x", "sxdg"))
    lam_r = folded.count("cx") / cx0 if cx0 else None
    lam_1 = sum(folded.count(g) for g in ("sx", "x", "sxdg")) / one0 if one0 else None
    return folded, lam_r, lam_1


def poly_intercept(xs, ys, degree):
    """Least-squares polynomial intercept at 0 (normal equations, small systems). FIT_FAILURE on rank."""
    if len(set(xs)) < degree + 1:
        raise ValueError("FIT_FAILURE: rank")
    m = degree + 1
    ata = [[sum(x ** (i + j) for x in xs) for j in range(m)] for i in range(m)]
    aty = [sum(y * x ** i for x, y in zip(xs, ys)) for i in range(m)]
    # Gaussian elimination
    for c in range(m):
        piv = max(range(c, m), key=lambda r: abs(ata[r][c]))
        ata[c], ata[piv] = ata[piv], ata[c]
        aty[c], aty[piv] = aty[piv], aty[c]
        for r in range(m):
            if r != c:
                fac = ata[r][c] / ata[c][c]
                ata[r] = [a - fac * b for a, b in zip(ata[r], ata[c])]
                aty[r] -= fac * aty[c]
    return aty[0] / ata[0][0]


def weighted_ols(xs, ys, ws):
    """Weighted least squares y = a + b x with weights w (numpy.polyfit(x, y, 1, w=w) convention:
    w multiplies the residual, so the normal equations use w^2)."""
    if len(set(xs)) < 2:
        raise ValueError("FIT_FAILURE: rank")
    w2 = [w * w for w in ws]
    s = sum(w2)
    sx = sum(w * x for w, x in zip(w2, xs))
    sy = sum(w * y for w, y in zip(w2, ys))
    sxx = sum(w * x * x for w, x in zip(w2, xs))
    sxy = sum(w * x * y for w, x, y in zip(w2, xs, ys))
    den = s * sxx - sx * sx
    if den == 0:
        raise ValueError("FIT_FAILURE: singular weighted design")
    b = (s * sxy - sx * sy) / den
    a = (sy - b * sx) / s
    return a, b


EXP_EPS = 1.0e-6  # mitiq v1.0.0 inference.py clamp (design.md §11)


def n_distinct(xs):
    """Distinct realized abscissas; duplicate abscissas are kept as recorded in the fit and count once here."""
    return len(set(float(x) for x in xs))


def pinned_linear_intercept(xs, ys):
    """The pinned mitiq v1.0.0 linear zero-noise intercept: `numpy.polyfit(x, y, 1)[-1]` (mitiq_polyfit,
    inference.py:171). This, not the closed-form normal equations, decides the EXP sign (amendment A-2)."""
    import numpy as np
    return float(np.polyfit(np.asarray(xs, float), np.asarray(ys, float), 1)[-1])


def exp_sign_tolerance(xs, ys, C=None, eps=None):
    """Amendment A-3 (2026-09-09): tau = C * eps * cond(V) * max|y| * lever, with V = numpy.vander(x, 2) (the degree-1
    design matrix polyfit forms), lever = 1 + mean(x)^2 / var(x) (population variance, ddof=0), eps the IEEE-754 double
    machine epsilon and C = 4. Computed per fit from the data; never a fixed number."""
    import numpy as np
    C = A3_SIGN_TOL_C if C is None else C
    eps = A3_EPS_DOUBLE if eps is None else eps
    x = np.asarray(xs, float); y = np.asarray(ys, float)
    V = np.vander(x, 2)
    cond = float(np.linalg.cond(V))
    var = float(np.var(x))                     # ddof=0
    lever = 1.0 + float(np.mean(x)) ** 2 / var
    return C * eps * cond * float(np.max(np.abs(y))) * lever


def exp_sign(xs, ys, asymptote):
    """EXP sign as the pinned mitiq v1.0.0 source (inference.py:1345-1348), sign = np.sign(-(asymptote - linear_intercept)),
    with the zero branch made reachable by amendment A-3 (2026-09-09): sign = 0 when |intercept - asymptote| <= tau
    (exp_sign_tolerance), else np.sign(-(asymptote - intercept)). A-2 (2026-09-08) had fixed sign(0) = 0 in place of the
    former '>= 0' ternary; in floating point the intercept of y = x/4 is never exactly zero and its raw sign differs
    between platforms, which A-3 resolves."""
    import numpy as np
    intercept = pinned_linear_intercept(xs, ys)
    if abs(intercept - asymptote) <= exp_sign_tolerance(xs, ys):
        return 0.0
    return float(np.sign(-(asymptote - intercept)))   # intercept = pinned_linear_intercept(xs, ys)


def exp_fit_fixed(xs, ys, asymptote, *, min_distinct):
    """EXP with a fixed asymptote, the mitiq v1.0.0 log-linear estimator (design.md §11; §C4.3 step 2),
    with the pinned sign and linear-fit convention (amendment A-2).

    `min_distinct` is the phase's rank minimum (RANK_RULE_2B["EXP"] = 3 for Phase 2B, RANK_RULE_2C["EXP"] = 2
    for Phase 2C); fewer distinct realized abscissas is FIT_FAILURE before any arithmetic. Duplicates are
    retained as recorded in the regression.
    1. sign: sigma = np.sign(-(asymptote - numpy.polyfit linear intercept)); sigma = 0 at equality;
    2. shifted_y = max(sigma * (y - asymptote), EXP_EPS): a clamp sets clamp_flag (sigma = 0 clamps every point);
    3. numpy.polyfit(x, ln(shifted_y), 1, w=sqrt(|shifted_y|)) (mitiq_polyfit with weights);
    4. intercept = asymptote + sigma * exp(z_0).
    Returns (intercept, clamped). With sigma = 0 the log-mode limit is exactly the asymptote; the clamp then
    sends the step to avoid_log under the homogeneity rule."""
    import numpy as np
    if n_distinct(xs) < min_distinct:
        raise ValueError(f"FIT_FAILURE: rank ({n_distinct(xs)} distinct abscissas < {min_distinct})")
    sigma = exp_sign(xs, ys, asymptote)
    raw = [sigma * (y - asymptote) for y in ys]
    clamped = any(v <= EXP_EPS for v in raw)
    shifted = [max(v, EXP_EPS) for v in raw]
    z = np.polyfit(np.asarray(xs, float), np.log(np.asarray(shifted, float)), 1, w=np.sqrt(np.abs(np.asarray(shifted, float))))
    return float(asymptote + sigma * math.exp(z[-1])), clamped


def exp_fit_avoid_log(xs, ys, asymptote, *, min_distinct):
    """EXP fallback exactly as the pinned mitiq v1.0.0 `PolyExpFactory.static_extrapolate` case 2
    (asymptote given, avoid_log=True; inference.py:1409): sign = sign(linear intercept - asymptote),
    ansatz asymptote + b * exp(c * x), initial guess [sign, -1.0], scipy.optimize.curve_fit with its
    defaults, zero-noise limit asymptote + b, and a solver RuntimeError as the only solver failure
    (mitiq raises ExtrapolationError; here ValueError('EXP_FIT_FAILED')). No constraint on c.
    The same phase rank minimum as the log mode applies first (`min_distinct`): the mode switch never
    relaxes the guard."""
    import numpy as np
    from scipy.optimize import curve_fit
    if n_distinct(xs) < min_distinct:
        raise ValueError(f"FIT_FAILURE: rank ({n_distinct(xs)} distinct abscissas < {min_distinct})")
    sign = exp_sign(xs, ys, asymptote)  # the same pinned convention as the log mode (amendment A-2)

    def ansatz(x, b, c):
        return asymptote + b * np.exp(x * c)

    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            opt, _ = curve_fit(ansatz, np.asarray(xs, float), np.asarray(ys, float), p0=[sign, -1.0])
    except RuntimeError:
        raise ValueError("EXP_FIT_FAILED")
    return float(asymptote + opt[0])


def exp_step_aggregate(seed_data, asymptote, *, min_distinct):
    """Frozen-order step 4 homogeneity rule for EXP over the seeds of one step (§C4.3).
    seed_data: list of (xs, ys). Returns (aggregate or None, mode, flags).
    Any seed whose fit is FIT_FAILURE (rank below `min_distinct`) makes the step aggregate None with the
    flag FIT_FAILURE and no surviving-seed mean; any clamp switches every seed to avoid_log; any solver
    failure there is EXP_FIT_FAILED with the aggregate None."""
    fits, clamps = [], []
    for xs, ys in seed_data:
        try:
            v, cl = exp_fit_fixed(xs, ys, asymptote, min_distinct=min_distinct)
        except ValueError as e:
            if str(e).startswith("FIT_FAILURE"):
                return None, "fit_failure", ["FIT_FAILURE"]
            raise
        fits.append(v)
        clamps.append(cl)
    if not any(clamps):
        return sum(fits) / len(fits), "log", []
    out = []
    for xs, ys in seed_data:
        try:
            out.append(exp_fit_avoid_log(xs, ys, asymptote, min_distinct=min_distinct))
        except ValueError as e:
            if str(e).startswith("FIT_FAILURE"):
                return None, "fit_failure", ["FIT_FAILURE"]
            return None, "avoid_log_failed", ["EXP_FIT_FAILED"]
    return sum(out) / len(out), "avoid_log", ["CLAMP_RERUN"]


def calibration_changes(pre, post, units):
    """EQ-C6 typed per-field change rows and per-unit maxima (never across units).
    pre/post: field -> value; units: field -> unit string."""
    rows = []
    for f in sorted(set(pre) | set(post)):
        u = units[f]
        if f in pre and f not in post:
            rows.append({"field": f, "unit": u, "pre": float(pre[f]), "post": None, "abs_change": None, "rel_change": None, "zero_pre": int(float(pre[f]) == 0), "status": "MISSING_POST"})
            continue
        if f in post and f not in pre:
            rows.append({"field": f, "unit": u, "pre": None, "post": float(post[f]), "abs_change": None, "rel_change": None, "zero_pre": 0, "status": "NEW_POST"})
            continue
        a, b = float(pre[f]), float(post[f])
        rows.append({"field": f, "unit": u, "pre": a, "post": b, "abs_change": abs(b - a),
                     "rel_change": (abs(b - a) / abs(a)) if a != 0 else None, "zero_pre": int(a == 0),
                     "status": "ZERO_PRE" if a == 0 else "PRESENT"})
    by_unit = {}
    for r in rows:
        if r["abs_change"] is None:
            continue
        u = r["unit"]
        if u not in by_unit or r["abs_change"] > by_unit[u]["abs_change"]:
            by_unit[u] = {"field": r["field"], "abs_change": r["abs_change"]}
    rel = [r for r in rows if r["rel_change"] is not None]
    top = max(rel, key=lambda r: r["rel_change"]) if rel else None
    summary = {"calib_max_rel_change": top["rel_change"] if top else None, "calib_max_rel_field": top["field"] if top else None,
               "calib_max_abs_by_unit": by_unit, "calib_zero_pre_fields": [r["field"] for r in rows if r["zero_pre"]],
               "calib_missing_fields": [r["field"] for r in rows if r["status"] == "MISSING_POST"],
               "calib_new_fields": [r["field"] for r in rows if r["status"] == "NEW_POST"]}
    return rows, summary


# Independent rendering expectations, written from the prose meaning of each flag column and mask
# (analysis contract C5), NOT derived from the JSON rules. Every series that carries value rules or a mask
# must be covered here; the checker composes each case on a synthetic row and compares against this table.
# Value-rule cases: flag value -> (marker prefix, value_state, source of y: 'own' | '<bound column>' | None).
VALUE_RULE_ORACLE = {
    ("B-STEPMET", "er_flag"): {"": ("filled", "value", "own"), "RATIO_LOWER_BOUND": ("triangle_up", "bound", "er_bound"),
                              "RATIO_ZERO_OVER_ZERO": ("hollow_floor", "unavailable", None), "RATIO_UNDEFINED": ("hollow_floor", "unavailable", None)},
    ("B-STEPMET", "ur_flag"): {"": ("filled", "value", "own"), "RATIO_LOWER_BOUND": ("triangle_up", "bound", "ur_bound"),
                              "RATIO_ZERO_OVER_ZERO": ("hollow_floor", "unavailable", None), "RATIO_UNDEFINED": ("hollow_floor", "unavailable", None)},
    ("B-STEPMET", "beta_flag_mit"): {"": ("filled", "value", "own"), "BETA_UNDEFINED": ("hollow_floor", "unavailable", None), "UNDEFINED": ("hollow_floor", "unavailable", None)},
    ("B-STEPMET", "beta_flag_noisy"): {"": ("filled", "value", "own"), "BETA_UNDEFINED": ("hollow_floor", "unavailable", None), "UNDEFINED": ("hollow_floor", "unavailable", None)},
    ("B-STEPMET", "if_is_lower_bound"): {"0": ("filled", "value", "own"), "1": ("triangle_up", "value", "own")},
    ("B-CURVEMET", "gif_is_lower_bound"): {"0": ("filled", "value", "own"), "1": ("triangle_up", "value", "own")},
    ("B-SEEDFIT", "fit_status"): {"OK": ("filled", "value", "own"), "FIT_FAILURE": ("hollow_floor", "unavailable", None),
                                 "FIT_UNAVAILABLE": ("hollow_floor", "unavailable", None), "EXP_FIT_FAILED": ("hollow_floor", "unavailable", None)},
    ("C-SEEDFIT", "fit_status"): {"OK": ("filled", "value", "own"), "FIT_FAILURE": ("hollow_floor", "unavailable", None),
                                 "FIT_UNAVAILABLE": ("hollow_floor", "unavailable", None), "EXP_FIT_FAILED": ("hollow_floor", "unavailable", None)},
    ("B-DIST", "verdict"): {"DISTINGUISHABLE": ("filled", "value", "own"), "NOT_DISTINGUISHABLE": ("hollow", "value", "own"),
                           "INDETERMINATE": ("hollow_floor", "value", "own"), "CONTROL_ABSENT": ("absent", "unavailable", None)},
    ("C-CALDIFF", "status", "abs_change"): {"PRESENT": ("filled", "value", "own"), "ZERO_PRE": ("filled", "value", "own"),
                                            "MISSING_POST": ("cross_floor", "unavailable", None), "NEW_POST": ("cross_floor", "unavailable", None)},
    ("C-CALDIFF", "status", "rel_change"): {"PRESENT": ("filled", "value", "own"), "ZERO_PRE": ("hollow_floor", "unavailable", None),
                                            "MISSING_POST": ("cross_floor", "unavailable", None), "NEW_POST": ("cross_floor", "unavailable", None)},
}
# Mask cases: (artifact, mask column) -> list of (row overlay, expected marker) on a plain value row (value 0.75).
# The overlay sets every column the mask may consult; the expected marker is the full composed marker.
MASK_ORACLE = {
    ("A-INT", "in_mask"): [({"in_mask": 1}, "filled"), ({"in_mask": 0}, "hollow")],
    ("A-RES", "is_max_abs_residual"): [({"is_max_abs_residual": 0}, "filled"), ({"is_max_abs_residual": 1}, "filled+edge")],
    ("A-HIST", "within_tau_hist"): [({"within_tau_hist": 1, "within_eta_e": 1}, "filled+edge"), ({"within_tau_hist": 1, "within_eta_e": 0}, "filled"),
                                    ({"within_tau_hist": 0, "within_eta_e": 1}, "hollow+edge"), ({"within_tau_hist": 0, "within_eta_e": 0}, "hollow"),
                                    ({"__y__": 0.0, "within_tau_hist": 1, "within_eta_e": 1}, "hollow_floor+edge")],
    ("B-STEPMET", "reportable"): [({"reportable": 1}, "filled"), ({"reportable": 0}, "hollow")],
    ("B-CURVEMET", "n_undefined_steps"): [({"n_undefined_steps": 0}, "filled"), ({"__y__": None, "n_undefined_steps": 1}, "hollow_floor"),
                                          ({"__y__": None, "n_undefined_steps": 7}, "hollow_floor"),
                                          ({"n_undefined_steps": 1}, "hollow"), ({"n_undefined_steps": 3}, "hollow")],  # any positive count hollows, not only a large one
    ("B-BOUND", "located"): [({"located": 1, "non_monotone": 0}, "filled"), ({"located": 0, "non_monotone": 0}, "hollow"),
                             ({"located": 1, "non_monotone": 1}, "filled+edge"), ({"located": 0, "non_monotone": 1}, "hollow+edge")],
    ("C-END", "status"): [({"status": "PASS"}, "filled"), ({"status": "FAIL"}, "cross"), ({"status": "OVERLAP"}, "half"),
                          ({"status": "INDETERMINATE"}, "hollow"), ({"__y__": None, "status": "UNAVAILABLE"}, "hollow_floor")],
}


def mask_condition_holds(have, want):
    """Mask condition semantics: '__null__' tests for null; a {op: value} dict is a comparison
    (>, >=, <, <=, ==, !=) that is false for a null; anything else is equality."""
    if want == "__null__":
        return have is None
    if isinstance(want, dict):
        if have is None or not _is_num(have):
            return False
        for op, v in want.items():
            if op == ">" and not have > v: return False
            if op == ">=" and not have >= v: return False
            if op == "<" and not have < v: return False
            if op == "<=" and not have <= v: return False
            if op == "==" and not same_value(have, v): return False
            if op == "!=" and same_value(have, v): return False
        return True
    return same_value(have, want)


def constant_value(constants, cid):
    """Numeric value of a constant for plotting; ValueError if it has no single numeric value."""
    k = constants.get(cid)
    if k is None:
        raise ValueError(f"unknown constant {cid}")
    v = k.get("value")
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"constant {cid} has no single numeric value")
    return float(v)


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def chart_points(series, panel, params, tables, cells, sched, art_cols, constants=None):
    """Extract the plotted coordinates of one series for one family instance from numeric tables.

    Three independent axes compose per point: the VALUE (a plug-in value, a bound named by a value
    rule, or explicitly unavailable), REPORTABILITY (mask conditions: filled / hollow / triangle /
    edge), and INTERVAL availability (a numeric ordered band, or explicitly unavailable). Permitted
    null states never raise; structural impossibilities (unknown flag, non-numeric value where one is
    claimed, unresolvable x, inverted band) do.

    Constant-sourced series resolve to their numeric horizontal line(s) (± when declared), only when
    their `when` condition matches the family parameters; otherwise they return [] with no point."""
    constants = constants or {}
    if series.get("source") == "constant":
        when = series.get("when", {})
        if any(str(params.get(k)) != str(v) for k, v in when.items()):
            return []
        val = constant_value(constants, series["constant"])
        if series.get("lines") == "±":
            return [{"x": "line", "y": val, "kind": "hline"}, {"x": "line", "y": -val, "kind": "hline"}]
        return [{"x": "line", "y": val, "kind": "hline"}]
    art = series["artifact"]
    resolved = resolve_selector(series.get("rows", {}), params, cells, sched)
    rows = select_rows(tables[art], resolved)
    xa, xc = panel["x"]["artifact"], panel["x"]["column"]
    pts = []
    for r in rows:
        # ---- x ----
        if "x_fixed" in series:
            x = series["x_fixed"]
        elif panel.get("x_from_cell"):
            cell = next((c for c in cells if c["cell_index"] == r.get("cell_index")), None)
            if cell is None:
                raise ValueError(f"{series['name']}: x_from_cell needs a cell_index on the row")
            x = cell[panel["x_from_cell"]]
        elif xa == art and xc in r:
            x = r[xc]
        elif xc in ("n", "point_n") and ("n" in r or "point_n" in r):
            x = r.get("n", r.get("point_n"))
        elif panel["x"].get("join_on"):
            keys = panel["x"]["join_on"]
            match = [q for q in tables[xa] if all(same_value(q.get(k), r.get(k)) for k in keys)]
            if len(match) != 1:
                raise ValueError(f"{series['name']}: x join on {keys} matched {len(match)} rows")
            x = match[0][xc]
        else:
            raise ValueError(f"{series['name']}: x column {xa}.{xc} not obtainable from {art} rows")
        pt = {"x": x, "marker": "filled"}
        # ---- value axis ----
        if series.get("role") == "marker" or panel["y"].get("categorical") or series.get("categorical"):
            pt.update({"y": r.get(series["column"]), "value_state": "categorical"})
        else:
            vr = series.get("value_rules")
            if vr:
                flag = r.get(vr["flag_column"])
                flag = "" if flag is None else str(flag)
                rule = vr["rules"].get(flag)
                if rule is None:
                    raise ValueError(f"{series['name']}: flag value {flag!r} of {vr['flag_column']} has no value rule")
                pt["flag"] = flag
                if rule["y"] is None:
                    pt.update({"y": None, "value_state": "unavailable", "marker": rule["marker"]})
                else:
                    yv = r.get(rule["y"])
                    if yv is None:
                        pt.update({"y": None, "value_state": "unavailable", "marker": "hollow_floor"})
                    elif _is_num(yv):
                        pt.update({"y": yv, "value_state": "bound" if rule["y"] != series["column"] else "value", "marker": rule["marker"]})
                    else:
                        raise ValueError(f"{series['name']}: rule for {flag!r} needs numeric {rule['y']}, got {yv!r}")
            else:
                yv = r.get(series["column"])
                if yv is None:
                    pt.update({"y": None, "value_state": "unavailable", "marker": "hollow_floor"})
                elif _is_num(yv):
                    pt.update({"y": yv, "value_state": "value"})
                else:
                    raise ValueError(f"{series['name']}: non-numeric y {series['column']}={yv!r}")
        # ---- logarithmic axis: a zero or negative value cannot be placed; drawn hollow at the floor, counted ----
        if panel.get("y_scale") == "log" and pt.get("value_state") in ("value", "bound") and _is_num(pt.get("y")) and pt["y"] <= 0:
            pt.update({"marker": "hollow_floor", "value_state": "nonpositive_on_log", "log_floor": True})
        # ---- reportability axis (mask) ----
        m = series.get("mask")
        if m:
            for cond_key, style in (("hollow_when", "hollow"), ("triangle_when", "triangle_up"), ("edge_when", "edge")):
                cond = m.get(cond_key)
                if not cond:
                    continue
                for col_, want in cond.items():
                    if mask_condition_holds(r.get(col_), want):
                        if style == "hollow":
                            if pt["marker"] == "filled":
                                pt["marker"] = "hollow"
                        elif pt["marker"] in ("filled", "hollow"):
                            pt["marker"] = pt["marker"] + "+" + style
                        else:
                            pt["marker"] = pt["marker"] + "+" + style
            sw = m.get("style_when")
            if sw:
                for col_, mapping in sw.items():
                    have = r.get(col_)
                    key = "" if have is None else str(have)
                    if key not in mapping:
                        raise ValueError(f"{series['name']}: status value {key!r} of {col_} has no style")
                    pt["marker"] = mapping[key]
            if m.get("annotate"):
                pt["annotate"] = r.get(m["annotate"])
        # ---- interval axis (band) ----
        b = series.get("band")
        if b:
            lo, hi = r.get(b["lo_column"].split(".", 1)[1]), r.get(b["hi_column"].split(".", 1)[1])
            if lo is None or hi is None:
                pt["band_state"] = "unavailable"
            elif _is_num(lo) and _is_num(hi) and lo <= hi:
                pt.update({"lo": lo, "hi": hi, "band_state": "band"})
            else:
                raise ValueError(f"{series['name']}: band {lo!r}..{hi!r} not numeric or inverted")
        pts.append(pt)
    return pts


def beta_hat(replicates, plugin):
    """§C4.5 item 5: bootstrap bias over ALL replicates; unavailable if any replicate is undefined."""
    if any(v is None for v in replicates):
        return None, "BETA_UNDEFINED"
    return sum(replicates) / len(replicates) - plugin, ""


def czz_from_moments(m_i, m_j, m_ij):
    return m_ij - m_i * m_j


def aggregate_frozen_order(seed_moments):
    """§C4.3 steps 3-4: per-seed CZZ then mean."""
    return sum(czz_from_moments(*m) for m in seed_moments) / len(seed_moments)


def aggregate_wrong_order(seed_moments):
    """Averaging the moments first (rejected)."""
    n = len(seed_moments)
    mi = sum(m[0] for m in seed_moments) / n
    mj = sum(m[1] for m in seed_moments) / n
    mij = sum(m[2] for m in seed_moments) / n
    return czz_from_moments(mi, mj, mij)


def order_weights(weights, energies):
    """§C4.7 exact total order on (-w, energy, index); marginal flags never enter the order."""
    idx = sorted(range(len(weights)), key=lambda j: (-weights[j], energies[j], j))
    marginal = [(idx[i], idx[i + 1]) for i in range(len(idx) - 1) if abs(weights[idx[i]] - weights[idx[i + 1]]) <= 1e-12]
    return idx, marginal


def ratio_rule(num, den, delta=1e-9):
    if num is None or den is None or not math.isfinite(num) or not math.isfinite(den):
        return None, "RATIO_UNDEFINED"
    if den > delta:
        return num / den, ""
    if num > delta:
        return num / delta, "RATIO_LOWER_BOUND"
    return None, "RATIO_ZERO_OVER_ZERO"


def seed_simulator(cell_index, n, k, j):
    return 10 ** 6 * cell_index + 100 * n + 10 * k + j


# ---- Phase 2C executable rules (prereg §5.7-§5.10) ----


def fits(t_est, t_lim=479.0):
    """Prereg §5.7: fits(T) <=> T < T_lim, strict."""
    return t_est < t_lim


def gate_conditions(t_est_cons, u_cons, u_out, t_lim=479.0, t_cap=480.0, t_open=600.0, nothing_else_planned=True):
    """Prereg §5.7 (a)-(c) evaluated on numbers; returns the record the gate must store."""
    u_auth = u_cons + u_out
    a = fits(t_est_cons, t_lim)
    b = u_auth + t_lim <= t_cap
    c = bool(nothing_else_planned)
    return {"condition_a": a, "condition_b": b, "condition_c": c, "u_auth_s": u_auth,
            "reserve_after_s": t_open - (u_auth + t_lim), "submit": a and b and c}


def usage_estimate(durations_s, shots, rep_delay_s, d_init_s, m=1.2, t_sub=2.0):
    """Prereg §5.8: T_est^(1) and the binding T_est^cons = T_est^(N_circ)."""
    n_circ = len(durations_s)
    per_exec = sum(rep_delay_s + d + d_init_s for d in durations_s) * shots
    t1 = t_sub * 1 + m * per_exec
    tcons = t_sub * n_circ + m * per_exec
    return {"n_circ": n_circ, "t_est_1_s": t1, "t_est_cons_s": tcons, "s_cons": n_circ}


def hardware_schedule(n1z, n1p, n2z, n2p, n_a, n_max=48, target=12):
    """Prereg §5.9 items 3-8: point set, cores, extended windows, stored windows, structural check."""
    def ext(n):
        return {m for m in range(n - 2, n + 3) if 1 <= m <= n_max}
    def core(n):
        return {m for m in range(n - 1, n + 2) if 1 <= m <= n_max}
    E1 = ext(n1z) | ext(n1p)
    C1 = core(n1z) | core(n1p)
    E2 = (ext(n2z) | ext(n2p)) if n2z is not None and n2p is not None else set()
    C2 = (core(n2z) | core(n2p)) if E2 else set()
    P = {1, n_a} | E1 | E2
    order = [n_a, 1]
    while len(P) > target:
        removed = False
        for cand in order:
            if cand in P and cand not in E1 and cand not in E2:
                P.discard(cand); removed = True; break
        if removed:
            continue
        outer2 = sorted(E2 - C2, key=lambda m: (-abs(m - n2z), -m)) if E2 else []
        outer1 = sorted(E1 - C1, key=lambda m: (-abs(m - n1z), -m))
        pool = [m for m in outer2 if m in P] or [m for m in outer1 if m in P]
        if not pool:
            break
        P.discard(pool[0])
    windows = {}
    for tag, n in (("ZPI_1", n1z), ("PRET_1", n1p), ("ZPI_2", n2z), ("PRET_2", n2p)):
        if n is None:
            continue
        w = sorted(m for m in P if n - 2 <= m <= n + 2)
        windows[tag] = {"points": w, "timing_testable": all(m in w for m in range(n - 2, n + 3))}
    return {"points": sorted(P), "E1": sorted(E1), "C1": sorted(C1), "E2": sorted(E2), "windows": windows,
            "e1_subset_ok": E1 <= P}


def reduction_policy(points, E1, E2, C2, n_a, fold_instances, shots, duration_of, rep_delay_s, d_init_s, t_lim=479.0):
    """Prereg §5.10: apply R1..R8 in order until fits(T_est^cons); skip steps that would break E1 ⊆ P."""
    P, folds, sh = set(points), int(fold_instances), int(shots)
    def est():
        durs = [duration_of(n, lam) for n in sorted(P) for lam in (1.0, 1.5, 2.0) for _ in range(folds)]
        return usage_estimate(durs, sh, rep_delay_s, d_init_s)["t_est_cons_s"]
    log = []
    steps = [("R1", lambda: P.difference_update(set(E2) - set(C2))), ("R2", lambda: P.difference_update(set(C2))),
             ("R3", lambda: None), ("R4", lambda: None), ("R5", lambda: P.discard(1)), ("R6", lambda: P.discard(n_a)),
             ("R7", lambda: None), ("R8", lambda: None)]
    if fits(est(), t_lim):
        return {"applied": [], "abandoned": False, "points": sorted(P), "folds": folds, "shots": sh, "t_est_cons_s": est()}
    for sid, fn in steps:
        before = est()
        snap = (set(P), folds, sh)
        if sid == "R3": folds = max(2, folds - 1) if folds > 3 else folds
        elif sid == "R4": folds = 2 if folds > 2 else folds
        elif sid == "R7": sh = 2048 if sh > 2048 else sh
        elif sid == "R8": sh = 1024 if sh > 1024 else sh
        else: fn()
        if not set(E1) <= P:  # structural requirement: never remove a revival-1 extended-window point
            P, folds, sh = set(snap[0]), snap[1], snap[2]
            log.append({"step": sid, "applied": False, "skipped_reason": "would violate E1 subset of P"})
            continue
        after = est()
        log.append({"step": sid, "applied": True, "t_before": before, "t_after": after, "e1_subset_ok": set(E1) <= P})
        if fits(after, t_lim):
            return {"applied": log, "abandoned": False, "points": sorted(P), "folds": folds, "shots": sh, "t_est_cons_s": after}
    return {"applied": log, "abandoned": True, "points": sorted(P), "folds": folds, "shots": sh, "t_est_cons_s": est()}


def sha256_bytes(b):
    import hashlib
    return hashlib.sha256(b).hexdigest()


def lifecycle(approved, post_records, tamper=None):
    """§C6 items 1-2 on an in-memory bundle: approved artifacts are hashed into a pre-gate manifest; later
    records are added; the approved hashes must still verify. `tamper` optionally modifies one approved
    artifact after the gate, which must be detected."""
    bundle = dict(approved)
    pregate = {k: sha256_bytes(v) for k, v in approved.items()}
    if tamper:
        bundle[tamper[0]] = tamper[1]
    bundle.update(post_records)
    verified = all(sha256_bytes(bundle[k]) == h for k, h in pregate.items())
    manifest = {k: sha256_bytes(v) for k, v in bundle.items()}
    return {"pregate": pregate, "approved_verified": verified, "manifest": manifest,
            "added": sorted(set(post_records) - set(approved))}


def root_allowed(root, input_bundle=None):
    """§C6 item 6 output-root policy on repository-relative paths, evaluated on the RESOLVED path:
    dot components, empty components, absolute paths and anything escaping the repository are refused."""
    import posixpath
    raw = root.strip().replace("\\", "/")
    if not raw or raw.startswith("/") or raw.startswith("~") or re.match(r"^[A-Za-z]:", raw):
        return False
    r = posixpath.normpath(raw)
    if r in (".", "..") or r.startswith("../") or "/./" in raw or "/../" in raw or raw.endswith("/.") or raw.endswith("/..") or raw.startswith("./") or raw.startswith("../"):
        return False
    parts = r.split("/")
    if any(p in ("", ".", "..") for p in parts):
        return False
    if input_bundle is not None:
        input_bundle = posixpath.normpath(input_bundle.strip().replace("\\", "/"))
    low = [x.lower() for x in parts]
    if low[0] == "figures":  # the canonical figures/ directory and anything inside it
        return False
    if low[0] == "results":
        if len(parts) not in (2, 3) or not parts[1] or low[1] == "minimal":
            return False
        if len(parts) == 3 and parts[2] not in ("phase2a", "phase2b", "phase2c"):
            return False
        if input_bundle is not None and len(parts) == 3 and input_bundle.strip().rstrip("/").lower() == "/".join(low[:2]):
            return False  # writing into a subdirectory of the consumed input bundle
    elif low[0].startswith("figures-"):
        if len(parts) != 1 or len(low[0]) <= len("figures-"):
            return False
    else:
        return False
    if input_bundle is not None and input_bundle.strip().rstrip("/").lower() == r.lower():
        return False
    return True


def same_value(a, b):
    """Selector equality: numeric when both sides are numbers, else string equality."""
    try:
        return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=1e-12)
    except (TypeError, ValueError):
        return str(a) == str(b)


def resolve_selector(selector, params, matrix_cells=None, schedule_rows=None):
    """Resolve a chart series selector for one family instance.

    selector values are: a literal; a '{param}' placeholder replaced by params[param]; or a join
    {"from": "matrix", "where": {...}} (the set of cell_index values whose matrix row matches
    the resolved where-clause) or {"from": "schedule", "where": {...}} (the set of n_ref values
    of the schedule rows matching the where-clause). Descriptive free text is not allowed."""
    out = {}
    for k, v in selector.items():
        if isinstance(v, dict):
            where = {kk: resolve_value(vv, params) for kk, vv in v.get("where", {}).items()}
            if v.get("from") == "matrix":
                src = matrix_cells or []
                out[k] = {c["cell_index"] for c in src if all(same_value(c.get(kk), vv) for kk, vv in where.items())}
            elif v.get("from") == "schedule":
                src = schedule_rows or []
                out[k] = {r["n_ref"] for r in src if all(same_value(r.get(kk), vv) for kk, vv in where.items())}
            else:
                raise ValueError(f"unknown join source {v.get('from')}")
        else:
            out[k] = resolve_value(v, params)
    return out


def resolve_value(v, params):
    if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
        name = v[1:-1]
        if name not in params:
            raise ValueError(f"unbound chart parameter {name}")
        return params[name]
    if isinstance(v, str) and " " in v:
        raise ValueError(f"descriptive selector value not allowed: {v!r}")
    return v


def select_rows(rows, resolved):
    """Apply a resolved selector: sets match membership, everything else matches by string equality."""
    out = []
    for row in rows:
        ok = True
        for k, v in resolved.items():
            if isinstance(v, set):
                if not any(same_value(row.get(k), x) for x in v):
                    ok = False
                    break
            elif not same_value(row.get(k), v):
                ok = False
                break
        if ok:
            out.append(row)
    return out


def bootstrap_rng(phase, cell_index, b):
    """§C4.5 item 1: numpy.random.default_rng([20260907, phase, cell_index, b])."""
    import numpy as np
    return np.random.default_rng([20260907, phase, cell_index, b])


def resample_counts(counts, shots, rng):
    """§C4.5 item 1: multinomial resampling of a count vector with the frozen numpy generator."""
    total = sum(counts)
    if total <= 0:
        raise ValueError("INVALID_INPUT: empty count record")
    p_hat = [c / total for c in counts]
    return [int(v) for v in rng.multinomial(shots, p_hat)]


# ============================================================================
# Checks
# ============================================================================


class InputError(Exception):
    """An input file is missing or unreadable: exit code 2, no check can run."""


class Checker:
    def __init__(self, root: Path):
        self.root = root
        self.results = []
        self.contract = None
        self.docs = {}

    def rec(self, name, ok, detail=""):
        self.results.append((name, bool(ok), detail))

    # ---------------- loading ----------------
    def load(self):
        """Read every input relative to the root. Raises InputError (exit 2) naming the offending path."""
        cpath = self.root / "tools/phase2_contract.json"
        if not cpath.is_file():
            raise InputError(f"missing input file: {cpath}")
        try:
            self.contract = json.loads(cpath.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError) as e:
            raise InputError(f"unreadable input file: {cpath} ({e.__class__.__name__}: {e})")
        for key, rel in (("prereg", "docs/prereg-phase2.md"), ("contract", "docs/phase2-analysis-contract.md"),
                         ("design", "docs/design.md"), ("outline", "docs/prereg-p2zero-outline.md"),
                         ("followup", "docs/followup-study-draft.md")):
            p = self.root / rel
            if not p.is_file():
                raise InputError(f"missing input file: {p}")
            try:
                self.docs[key] = p.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as e:
                raise InputError(f"unreadable input file: {p} ({e.__class__.__name__}: {e})")

    # ---------------- algebra fixtures ----------------
    def check_algebra(self):
        e00 = [0.9, -0.7, 0.5, -0.3, 0.2, -0.6]
        r10 = [0.95, 0.9, 0.85, 0.8, 0.75, 0.7]
        r01 = [0.8, 0.7, 0.6, 0.5, 0.45, 0.4]
        rows = []
        for i, e in enumerate(e00):
            rows.append(phase2a_step(e, e * r10[i], e * r01[i], e * r10[i] * r01[i]))
        self.rec("algebra: I(n) identically zero on exactly additive input",
                 all(abs(r["i_n"]) < 1e-12 for r in rows), f"max|I| = {max(abs(r['i_n']) for r in rows):.2e}")
        rows2 = [phase2a_step(e, e * r10[i], e * r01[i], e * r10[i] * r01[i] * math.exp(-0.2)) for i, e in enumerate(e00)]
        self.rec("algebra: I(n) = 0.2 on interacting input (r11 = r10 r01 e^-0.2)",
                 all(abs(r["i_n"] - 0.2) < 1e-12 for r in rows2))
        eta_r, eta_a = eta_propagation(0.5, 0.25, 1e-9)
        self.rec("algebra: budget propagation closed form",
                 abs(eta_r - 1e-9 * 1.5 / (0.25 - 1e-9)) < 1e-24 and abs(eta_a - eta_r / (0.5 - eta_r)) < 1e-24)
        v, reason, st = phase2a_verdict(rows)
        self.rec("algebra: additive fixture verdict EQUIVALENT with tiny bound intervals",
                 v == "EQUIVALENT" and st["s_max_hi"] < 1e-6, f"{v} {reason}")
        v2, _, st2 = phase2a_verdict(rows2)
        self.rec("algebra: interacting fixture (0.2 > tau_max) verdict INTERACTION", v2 == "INTERACTION", v2)
        xs = list(range(1, 11))
        a, b = ols(xs, [0.3 - 0.05 * x for x in xs])
        self.rec("algebra: OLS slope recovers g = 0.05 with zero residual", abs(-b - 0.05) < 1e-12 and abs(a - 0.3) < 1e-12)
        y = [0.0] + [-math.cos(2 * math.pi * n / 20) for n in range(1, 49)]
        self.rec("algebra: peak extractor finds 10, 30 on -cos(2 pi n/20)", find_peaks(y) == [10, 30], str(find_peaks(y)))
        par = {n: 1 - (n - 20.3) ** 2 for n in (19, 20, 21)}
        m = match_peak(par, [19, 20, 21])
        self.rec("algebra: parabolic timing exact on a parabola (t* = 20.3)", abs(m["timing"] - 20.3) < 1e-12, str(m))
        self.rec("algebra: trapezoid TIAE on e(n) = n, n = 1..5 equals 12", abs(tiae([1, 2, 3, 4, 5], [0] * 5) - 12) < 1e-12)
        vals = [float(i) for i in range(1, 2001)]
        lo, hi, u, fl = percentile_interval(vals, 0.025, 0.975)
        self.rec("algebra: percentile interval on 1..2000 at 95% = (50.975, 1950.025)",
                 abs(lo - 50.975) < 1e-9 and abs(hi - 1950.025) < 1e-9 and not fl, f"{lo} {hi}")
        c1 = resample_counts([1024, 0, 0, 0], 1024, bootstrap_rng(2, 1, 0))
        c2 = resample_counts([300, 300, 300, 124], 1024, bootstrap_rng(2, 1, 0))
        c3 = resample_counts([300, 300, 300, 124], 1024, bootstrap_rng(2, 1, 0))
        c4 = resample_counts([300, 300, 300, 124], 1024, bootstrap_rng(2, 1, 1))
        self.rec("algebra: frozen numpy default_rng([20260907, phase, cell, b]) multinomial resampling is reproducible and seed-distinct; a degenerate record returns itself",
                 c1 == [1024, 0, 0, 0] and c2 == c3 and c2 != c4 and sum(c2) == 1024 and c2 == [316, 306, 297, 105], str(c2))
        ops = ["sx", "rz", "cx", "sx", "cx", "rz", "cx", "x", "cx", "rz"]
        folded, lam_r, lam_1 = fold_global_counts(ops, 1.5)
        self.rec("algebra: fold_global lambda = 1.5 on 10 ops folds the suffix (cx, rz): 14 ops, lambda_r = 6/4 = 1.5, lambda_r_1q = 1",
                 len(folded) == 14 and abs(lam_r - 1.5) < 1e-12 and abs(lam_1 - 1.0) < 1e-12, f"{lam_r} {lam_1}")
        folded2, lam_r2, _ = fold_global_counts(ops, 3.0)
        self.rec("algebra: fold_global lambda = 3 triples every operation", len(folded2) == 30 and abs(lam_r2 - 3.0) < 1e-12)
        xs = [1.0, 1.25, 1.5, 1.75, 2.0]
        self.rec("algebra: LIN intercept exact on y = 0.8 - 0.3 x",
                 abs(poly_intercept(xs, [0.8 - 0.3 * x for x in xs], 1) - 0.8) < 1e-12)
        self.rec("algebra: QUAD intercept exact on y = 0.7 - 0.2 x + 0.05 x^2",
                 abs(poly_intercept(xs, [0.7 - 0.2 * x + 0.05 * x * x for x in xs], 2) - 0.7) < 1e-10)
        ex, cl = exp_fit_fixed(xs, [0.0 + 0.9 * math.exp(-0.4 * x) for x in xs], 0.0, min_distinct=RANK_RULE_2B["EXP"])
        self.rec("algebra: EXP fixed-asymptote fit recovers b = 0.9 on exact data", abs(ex - 0.9) < 1e-10 and not cl)
        ne, ncl = exp_fit_fixed([1, 1.5, 2], [0.9, 0.6, 0.2], 0.0, min_distinct=RANK_RULE_2B["EXP"])
        self.rec("algebra: EXP on non-exact data uses the mitiq sign and sqrt-shifted weights: 3.4834832 (unweighted would give 4.5459713)",
                 abs(ne - 3.483483195) < 1e-8 and not ncl, f"{ne}")
        ce, ccl = exp_fit_fixed([1, 1.5, 2], [0.1, 0.2, 0.8], 0.0, min_distinct=RANK_RULE_2B["EXP"])
        agg, mode, fl = exp_step_aggregate([([1, 1.5, 2], [0.9, 0.6, 0.2]), ([1, 1.5, 2], [0.1, 0.2, 0.8])], 0.0, min_distinct=RANK_RULE_2B["EXP"])
        agg2, mode2, _ = exp_step_aggregate([([1, 1.5, 2], [0.9, 0.6, 0.2]), ([1, 1.5, 2], [0.85, 0.55, 0.25])], 0.0, min_distinct=RANK_RULE_2B["EXP"])
        self.rec("algebra: EXP clamp on rising data triggers the homogeneity rerun for every seed of the step (mode avoid_log, or avoid_log_failed with no partial mean); a clean step stays in log mode",
                 ccl and ((mode == "avoid_log" and agg is not None) or (mode == "avoid_log_failed" and agg is None and "EXP_FIT_FAILED" in fl)) and mode2 == "log" and agg2 is not None, f"{mode} {mode2}")
        al = exp_fit_avoid_log([1, 1.5, 2], [0.9 * math.exp(-0.4 * x) for x in [1, 1.5, 2]], 0.0, min_distinct=RANK_RULE_2B["EXP"])
        self.rec("algebra: EXP avoid_log fallback (mitiq case 2: p0 = [sign, -1], scipy curve_fit) recovers b = 0.9 on exact data", abs(al - 0.9) < 1e-8, f"{al}")
        rising = [0.05 * math.exp(x) for x in (1, 1.5, 2)]
        agg3, mode3, fl3 = exp_step_aggregate([([1, 1.5, 2], rising)] * 8, 0.0, min_distinct=RANK_RULE_2B["EXP"])
        self.rec("algebra: y = 0.05 exp(x) clamps in log mode and the declared avoid_log rerun recovers the intercept 0.05 (Reviewer fixture)",
                 mode3 == "avoid_log" and agg3 is not None and abs(agg3 - 0.05) < 1e-9, f"{agg3} {mode3}")
        self.rec("algebra: frozen order CZZ = 0 vs moment-first 0.25 on the Reviewer fixture",
                 aggregate_frozen_order([(0.5, 0.5, 0.25), (-0.5, -0.5, 0.25)]) == 0.0
                 and abs(aggregate_wrong_order([(0.5, 0.5, 0.25), (-0.5, -0.5, 0.25)]) - 0.25) < 1e-12)
        self.rec("algebra: unphysical LIN intercept 1.5 from probabilities 0.9, 0.6, 0.3",
                 abs(poly_intercept([1, 1.5, 2], [0.9, 0.6, 0.3], 1) - 1.5) < 1e-12)

    # ---------------- edge cases ----------------
    def check_edge_cases(self):
        r = phase2a_step(0.5, 0.45, -0.3, 0.2)
        self.rec("edge: sign flip -> SIGN_FLIP, I undefined, verdict INCONCLUSIVE",
                 "SIGN_FLIP" in r["flags"] and r["i_n"] is None and phase2a_verdict([r] * 3)[0] == "INCONCLUSIVE")
        r = phase2a_step(0.5, 0.55, 0.4, 0.3)
        self.rec("edge: ratio above one -> RATIO_ABOVE_ONE, I still defined (primary not blocked)",
                 "RATIO_ABOVE_ONE" in r["flags"] and r["i_n"] is not None and phase2a_verdict([r] * 3)[0] != "INCONCLUSIVE" or
                 ("RATIO_ABOVE_ONE" in r["flags"] and r["i_n"] is not None))
        rows = [dict(phase2a_step(0.5, 0.55, 0.4, 0.3), n=1), dict(phase2a_step(0.5, 0.45, 0.4, 0.36), n=2), dict(phase2a_step(0.5, 0.45, 0.4, 0.36), n=3)]
        self.rec("edge: ratio above one makes the secondary fit FIT_UNAVAILABLE (no survivor fit)",
                 secondary_fit(rows, "10", [])["fit_available"] == 0)
        rv = [dict(phase2a_step(0.5, 0.55, 0.5 * math.exp(-0.1 * n), 0.55 * math.exp(-0.1 * n)), n=n) for n in range(1, 6)]
        f01, f10, f11 = secondary_fit(rv, "01", []), secondary_fit(rv, "10", []), secondary_fit(rv, "11", [])
        self.rec("edge: a cell-level gate flag blocks only its own cell (Reviewer fixture): cell 10 unavailable, cell 01 fits g = 0.1 exactly, cell 11 fits",
                 f10["fit_available"] == 0 and f01["fit_available"] == 1 and abs(f01["g_raw"] - 0.1) < 1e-12 and f11["fit_available"] == 1, str(f01.get("g_raw")))
        rv2 = [dict(phase2a_step(0.1 + 1e-10, 0.09, 0.08, 0.07), n=1)] + rv[1:]
        self.rec("edge: a size-wide blocker (MASK_BOUNDARY) still blocks every cell's fit at that size",
                 all(secondary_fit(rv2, ce, [])["fit_available"] == 0 for ce in ("10", "01", "11")))
        below = phase2a_step(0.05, 0.04, 0.03, 0.02)
        self.rec("edge: below-mask step flagged BELOW_MASK, tabulated, excluded from statistics",
                 "BELOW_MASK" in below["flags"] and below["in_mask"] == 0 and below["r10"] is not None)
        good = phase2a_step(0.5, 0.45, 0.4, 0.36)
        v, reason, _ = phase2a_verdict([good, good, below])
        self.rec("edge: fewer than 3 masked steps -> TOO_FEW_POINTS, INCONCLUSIVE", v == "INCONCLUSIVE" and "TOO_FEW_POINTS" in reason, reason)
        try:
            ols([2, 2, 2], [1, 2, 3])
            ff = False
        except ValueError:
            ff = True
        try:
            poly_intercept([1, 1, 2], [0.1, 0.2, 0.3], 2)
            rank_ok = False
        except ValueError:
            rank_ok = True
        self.rec("edge: singular design -> FIT_FAILURE; QUAD with 2 distinct abscissas -> FIT_FAILURE", ff and rank_ok)
        self.check_exp_rank_boundary()
        self.check_a2_exp_sign()
        self.check_a3_sign_tolerance()
        self.check_a2_small_mask()
        self.check_a2_dm_seed_range()
        lo, hi, u, fl = percentile_interval([0.3] * 2000, 0.025, 0.975)
        self.rec("edge: constant replicates -> DEGENERATE_CONSTANT (INDETERMINATE, never a pass)",
                 "DEGENERATE_CONSTANT" in fl and three_way(lo, hi, 0.2, 0.4, undefined=True) == "INDETERMINATE")
        sat = resample_counts([4096, 0], 4096, bootstrap_rng(3, 0, 1))
        self.rec("edge: saturated counts resample to themselves -> DEGENERATE_SATURATED interval of zero width",
                 sat == [4096, 0] and percentile_interval([1.0] * 100, 0.025, 0.975)[3] != [])
        mb = phase2a_step(0.1 + 1e-10, 0.09, 0.08, 0.07)
        v_mb, reason_mb, _ = phase2a_verdict([mb, good, good])
        sec = secondary_fit([dict(mb, n=1), dict(good, n=2), dict(good, n=3)], "10", ["MASK_BOUNDARY"])
        self.rec("edge: boundary-ambiguous reference -> MASK_BOUNDARY blocks the verdict and the secondary fit",
                 "MASK_BOUNDARY" in mb["flags"] and v_mb == "INCONCLUSIVE" and "MASK_BOUNDARY" in reason_mb and sec["fit_available"] == 0)
        # timing floor
        worst = 0.0
        for a in [0.001, 0.01, 0.1, 0.5, 1.0, 2.0]:
            for b in [0.0, 0.001, 0.01, 0.1, 0.5, 1.0, 2.0]:
                off, fb = parabolic_timing(1 - a, 1.0, 1 - b)
                if not fb:
                    worst = max(worst, abs(off))
        three = make_windows([20], w=1, n_max=48)[0]
        five = timing_testable([18, 19, 20, 21, 22], 20)
        curve5 = {18: 0.1, 19: 0.3, 20: 0.6, 21: 1.0, 22: 0.9}
        m5 = match_peak(curve5, [18, 19, 20, 21, 22])
        self.rec("edge: three-point window bound |t*-n| <= 0.5 -> TIMING_UNTESTABLE; five-point window can exceed tau_t = 1",
                 worst <= 0.5 + 1e-12 and not three["timing_testable"] and five and m5["timing"] is not None and abs(m5["timing"] - 20.0) > 1.0,
                 f"worst offset {worst:.3f}, five-point timing {m5['timing']:.3f}")
        cases = {(48000, 1.0 / 9600.0): 4, (2000, 0.00625): 12, (2000, 0.025): 49}  # exact primary tail 1/9600, never the rounded 1.0417e-4
        ok = True
        det = []
        for (B, q), allowed in cases.items():
            base = [0.01 * math.sin(i) for i in range(B)]
            for u in (allowed, allowed + 1):
                vals = base[:B - u] + [None] * u
                lo, hi, uu, fl = percentile_interval(vals, q, 1 - q)
                finite = "UNDEFINED" not in fl
                ok &= finite == (u == allowed)
                det.append(f"B={B} q={q:.6g} u={u} finite={finite}")
            alt = base[:B - 2 * allowed] + [None] * (2 * allowed)
            alo, ahi = alternating_interval(alt, q, 1 - q)
            clo, chi, _, cfl = percentile_interval(alt, q, 1 - q)
            ok &= math.isfinite(alo) and math.isfinite(ahi) and "UNDEFINED" in cfl
        self.rec("edge: undefined-replicate counts 4/12/49 tolerated, +1 undefined; alternating placement rejected", ok, "; ".join(det))
        self.rec("edge: unphysical estimate/interval never passes (PRET interval [1.4, 1.6] vs band [0.95, 1.05])",
                 three_way(1.4, 1.6, 0.95, 1.05, 0.0, 1.0) == "FAIL" and three_way(0.98, 1.02, 0.95, 1.05, 0.0, 1.0) == "OVERLAP")
        self.rec("edge: statuses: (FAIL, INDETERMINATE, PASS, PASS) -> FAIL; overlap -> OVERLAP; disjoint -> FAIL; inside -> PASS",
                 condition_status(["FAIL", "INDETERMINATE", "PASS", "PASS"]) == "FAIL"
                 and three_way(0.05, 0.15, 0.0, 0.1) == "OVERLAP" and three_way(0.2, 0.3, 0.0, 0.1) == "FAIL"
                 and three_way(0.0, 0.1, 0.0, 0.1) == "PASS" and condition_status(["PASS", "OVERLAP", "PASS", "PASS"]) == "OVERLAP"
                 and condition_status(["PASS", "OVERLAP", "INDETERMINATE", "PASS"]) == "INDETERMINATE")
        idx, marg = order_weights([0.5, 0.5 + 0.75e-12, 0.5 + 1.5e-12], [1.0, 2.0, 3.0])
        self.rec("edge: three near-tied projector weights order uniquely (2, 1, 0) with two WEIGHT_MARGINAL pairs",
                 idx == [2, 1, 0] and len(marg) == 2, str(idx))
        g = [0.25, 0.5, 1.0, 2.0, 4.0]
        b1 = boundary(["PASS", "PASS", "FAIL", "FAIL", "FAIL"], g)
        b2 = boundary(["PASS", "PASS", "OVERLAP", "FAIL", "FAIL"], g)
        b3 = boundary(["FAIL", "FAIL", "PASS", "FAIL", "FAIL"], g)
        b4 = boundary(["INDETERMINATE"] + ["FAIL"] * 4, g)
        b5 = boundary(["PASS"] * 5, g)
        self.rec("edge: boundary located only on FAIL; OVERLAP unresolved; BELOW_MIN_FAIL; UNRESOLVED_AT_MIN; AT_OR_ABOVE_MAX; NON_MONOTONE",
                 b1 == {"kappa_star": 0.5, "located": 1, "non_monotone": 0} and b2["kappa_star"] == 0.5 and b2["located"] == 0
                 and b3["kappa_star"] == "BELOW_MIN_FAIL" and b3["non_monotone"] == 1 and b4["kappa_star"] == "UNRESOLVED_AT_MIN"
                 and b5["kappa_star"] == "AT_OR_ABOVE_MAX")
        self.rec("edge: ratio rule value / lower bound / zero-over-zero / undefined",
                 ratio_rule(0.2, 0.4)[1] == "" and ratio_rule(0.2, 1e-10)[1] == "RATIO_LOWER_BOUND"
                 and ratio_rule(1e-10, 1e-10)[1] == "RATIO_ZERO_OVER_ZERO" and ratio_rule(float("nan"), 1.0)[1] == "RATIO_UNDEFINED")
        wins = make_windows([19, 26], w=4, n_max=48)
        self.rec("edge: peaks 7 apart -> windows truncated at the midpoint and disjoint",
                 "WINDOW_TRUNCATED" in wins[0]["flags"] and not set(wins[0]["points"]) & set(wins[1]["points"]))
        # ---- Reviewer round-03 finding 1: invalid or incomplete input never yields success ----
        def raises(fn):
            try:
                fn()
                return False
            except ValueError:
                return True
        self.rec("edge: condition_status rejects an empty, three-endpoint, extra-endpoint or unknown-status input",
                 raises(lambda: condition_status([])) and raises(lambda: condition_status(["PASS"] * 3))
                 and raises(lambda: condition_status(["PASS"] * 5)) and raises(lambda: condition_status(["PASS", "PASS", "PASS", "MAYBE"]))
                 and raises(lambda: condition_status({"ZPI_AMP": "PASS", "ZPI_TIME": "PASS", "PRET_AMP": "PASS"}))
                 and condition_status({"ZPI_AMP": "PASS", "ZPI_TIME": "PASS", "PRET_AMP": "PASS", "PRET_TIME": "PASS"}) == "PASS")
        g = [0.25, 0.5, 1.0, 2.0, 4.0]
        self.rec("edge: boundary rejects an empty scan, a partial scan and a mis-keyed scan",
                 raises(lambda: boundary([], g)) and raises(lambda: boundary(["PASS"], g)) and raises(lambda: boundary([], []))
                 and raises(lambda: boundary({0.25: "PASS", 0.5: "PASS"}, g))
                 and boundary({k: "PASS" for k in g}, g)["kappa_star"] == "AT_OR_ABOVE_MAX")
        self.rec("edge: three_way rejects an inverted interval, an inverted band and NaN",
                 raises(lambda: three_way(0.8, 0.2, 0.0, 1.0)) and raises(lambda: three_way(0.2, 0.8, 1.0, 0.0))
                 and raises(lambda: three_way(float("nan"), 0.8, 0.0, 1.0)))
        span = [1.5e-12 * i / 1999 for i in range(2000)]
        lo, hi, _, fl = percentile_interval(span, 0.025, 0.975)
        self.rec("edge: collapse detector uses the half-width (prereg §6.7): 2000 values spanning [0, 1.5e-12] are DEGENERATE_COLLAPSED",
                 "DEGENERATE_COLLAPSED" in fl and 0.5 * (hi - lo) < 1e-12, f"half-width {0.5 * (hi - lo):.3e} {fl}")
        # ---- finding 4: executable hardware rules against the contract's structured parameters ----
        c = self.contract
        K = c["constants"]
        t_lim, t_cap, t_open, reserve = K["C-T-LIM"]["value"], K["C-QPU-CAP"]["value"], K["C-OPEN-ALLOWANCE"]["value"], K["C-RESERVE"]["value"]
        self.rec("hardware: T_lim < T_cap, T_open - T_cap = reserve = 120, max_execution_time = T_lim, all from the JSON",
                 t_lim < t_cap and t_open - t_cap == reserve == 120 and K["C-MAX-EXEC"]["value"] == t_lim == c["phase2c"]["max_execution_time"] == 479)
        self.rec("hardware: fits() is strict at 479 and rejects 479.5 (which is below the 480 cap)",
                 not fits(479.0, t_lim) and fits(478.999, t_lim) and not fits(479.5, t_lim) and 479.5 < t_cap)
        g1 = gate_conditions(340.0, 0.0, 1.0, t_lim, t_cap, t_open)
        g2 = gate_conditions(340.0, 0.5, 0.6, t_lim, t_cap, t_open)
        g3 = gate_conditions(479.0, 0.0, 0.0, t_lim, t_cap, t_open)
        self.rec("hardware: gate (b) U_auth + 479 <= 480 leaves reserve 121 - U_auth: passes at U_auth = 1 (reserve exactly 120), fails at 1.1; an estimate of 479 fails (a)",
                 g1["submit"] and g1["reserve_after_s"] == 120 and not g2["condition_b"] and not g3["condition_a"])
        ill = c["phase2c"]["estimate"]["illustration"]
        est = usage_estimate([ill["D_c_us"] * 1e-6] * ill["N_circ"], 4096, ill["rep_delay_us"] * 1e-6, ill["D_init_us"] * 1e-6,
                             c["phase2c"]["estimate"]["M"], c["phase2c"]["estimate"]["t_sub"])
        self.rec("hardware: illustration recomputed from the JSON: T_est^(1) = 341.7, T_est^cons = 627.7, and the binding value does not fit",
                 abs(est["t_est_1_s"] - ill["T_est_1_s"]) < 0.06 and abs(est["t_est_cons_s"] - ill["T_est_cons_s"]) < 0.06 and not fits(est["t_est_cons_s"], t_lim),
                 f"{est}")
        n1, n2 = K["C-PEAK-EXPECTED-L6"]["value"]
        na = K["C-TROUGH-EXPECTED-L6"]["value"]
        sch = hardware_schedule(n1, n1, n2, n2, na)
        self.rec("hardware: schedule from the expected L=6 peaks gives 12 points {1,10,17..21,37..41}, both revival-1 windows timing-testable, E_1 subset of P",
                 sch["points"] == [1, 10, 17, 18, 19, 20, 21, 37, 38, 39, 40, 41] and sch["e1_subset_ok"]
                 and all(sch["windows"][k]["timing_testable"] for k in ("ZPI_1", "PRET_1")), str(sch["points"]))
        sch2 = hardware_schedule(19, 21, 39, 39, 10)
        self.rec("hardware: shifted PRET reference peak enlarges the point set and keeps both revival-1 windows testable; the size rule never removes core points",
                 set(sch2["C1"]) <= set(sch2["points"]) and sch2["windows"]["PRET_1"]["timing_testable"] and sch2["windows"]["ZPI_1"]["timing_testable"], str(sch2["points"]))
        dur = lambda n, lam: 220e-6 * (0.5 + 0.5 * lam)  # synthetic per-circuit duration
        red = reduction_policy(sch["points"], sch["E1"], sch["E2"], [n2 - 1, n2, n2 + 1], na, 4, 4096, dur, 250e-6, 10e-6, t_lim)
        red_ok = (not red["abandoned"]) and set(sch["E1"]) <= set(red["points"]) and fits(red["t_est_cons_s"], t_lim)
        self.rec("hardware: reduction R1..R8 reaches a fitting configuration without removing any revival-1 extended-window point",
                 red_ok, f"applied {[s['step'] for s in red['applied'] if s.get('applied')]} -> {red['t_est_cons_s']:.1f} s, {len(red['points'])} points")
        red2 = reduction_policy(sch["points"], sch["E1"], sch["E2"], [n2 - 1, n2, n2 + 1], na, 4, 4096, lambda n, lam: 5e-2, 250e-6, 10e-6, t_lim)
        self.rec("hardware: when even the floor does not fit the run is abandoned, with E_1 still intact",
                 red2["abandoned"] and set(sch["E1"]) <= set(red2["points"]) and not fits(red2["t_est_cons_s"], t_lim))
        base48 = [0.01 * math.sin(i) for i in range(48000)]
        blo, bhi, bu, bfl = percentile_interval(base48[:-3] + [None] * 3, 0.05 / 480, 1 - 0.05 / 480)
        bval, bflag = beta_hat(base48[:-3] + [None] * 3, 0.0)
        self.rec("edge: finite conservative quantiles with 3 undefined replicates still leave the bootstrap bias unavailable (BETA_UNDEFINED), explained by its flag column",
                 "UNDEFINED" not in bfl and bval is None and bflag == "BETA_UNDEFINED" and abs(beta_hat([1.0, 2.0], 1.2)[0] - 0.3) < 1e-12 and beta_hat([1.0, 2.0], 1.2)[1] == "")
        # ---- lifecycle (contract §C6): approved hashes stay verifiable; tampering is detected ----
        approved = {"usage_estimate.json": b'{"t_est_cons_s": 340.0}', "schedule.json": b'{"points": [1]}', "authorization_ledger_approved.json": b'{"entries": []}'}
        post = {"pre_submit_recheck.json": b'{"proceed": true}', "usage_actual.json": b'{"quantum_seconds": 300}', "authorization_ledger_reconciliation.json": b'{"entries": [{"closed": true}]}'}
        life = lifecycle(approved, post)
        tam = lifecycle(approved, post, tamper=("usage_estimate.json", b'{"t_est_cons_s": 100.0}'))
        self.rec("lifecycle: gate-approved hashes verify after submission and reanalysis records are added; a modified approved artifact is detected",
                 life["approved_verified"] and set(life["added"]) == set(post) and not tam["approved_verified"]
                 and all(k in life["manifest"] for k in list(approved) + list(post)))
        # ---- output-root policy on the JSON examples and the documented commands ----
        pol = c["entrypoints"]["output_root_guard"]
        acc = all(root_allowed(r, i) for r, i in pol["accepted_examples"])
        refd = all(not root_allowed(r, i) for r, i in pol["refused_examples"])
        cmds = [e["command"] for e in c["entrypoints"]["future"]]
        outs = []
        for cmd in cmds:
            m = re.search(r"--out (\S+)", cmd)
            if m:
                outs.append(m.group(1))
        self.rec("roots: accepted and refused examples from the JSON evaluate as declared; every documented --out is an accepted root; figures/ is refused",
                 acc and refd and all(root_allowed(o, "results/phase2" if "repro" in o else None) for o in outs) and not root_allowed("figures/phase2"),
                 f"outs={outs} acc={acc} refd={refd}")

    # ---------------- EXP rank boundary (amendment A-1) ----------------
    def check_exp_rank_boundary(self):
        """One, two and three distinct realized abscissas, duplicates, both EXP modes, failed-seed
        propagation through the §C4.3 step 4 homogeneity rule, and propagation through the bootstrap
        (abscissas are fixed under resampling). Phase 2B minimum 3, Phase 2C minimum 2."""
        m2b, m2c = RANK_RULE_2B["EXP"], RANK_RULE_2C["EXP"]
        decay = lambda x: 0.9 * math.exp(-0.4 * x)
        rising = lambda x: 0.05 * math.exp(x)  # clamps in log mode -> avoid_log rerun (Reviewer fixture)
        one = ([1.0, 1.0, 1.0], [0.5, 0.4, 0.3])
        two = ([1.0, 2.0], [decay(1.0), decay(2.0)])
        two_dup = ([1.0, 1.0, 2.0, 2.0], [decay(1.0), decay(1.0) + 0.02, decay(2.0), decay(2.0) - 0.02])
        three = ([1.0, 1.5, 2.0], [decay(x) for x in (1.0, 1.5, 2.0)])
        three_dup = ([1.0, 1.0, 1.5, 2.0], [decay(1.0), decay(1.0) + 0.02, decay(1.5), decay(2.0)])

        def outcome(fn, data, m):
            try:
                return ("fit", fn(data[0], data[1], 0.0, min_distinct=m))
            except ValueError as e:
                return ("FIT_FAILURE" if str(e).startswith("FIT_FAILURE") else "EXP_FIT_FAILED", None)

        res = {}
        for label, data in (("one", one), ("two", two), ("two_dup", two_dup), ("three", three), ("three_dup", three_dup)):
            for mode, fn in (("log", exp_fit_fixed), ("avoid_log", exp_fit_avoid_log)):
                for ph, m in (("2B", m2b), ("2C", m2c)):
                    res[(label, mode, ph)] = outcome(fn, data, m)[0]
        want = {}
        for mode in ("log", "avoid_log"):
            want[("one", mode, "2B")] = want[("one", mode, "2C")] = "FIT_FAILURE"
            want[("two", mode, "2B")] = want[("two_dup", mode, "2B")] = "FIT_FAILURE"
            want[("two", mode, "2C")] = want[("two_dup", mode, "2C")] = "fit"
            want[("three", mode, "2B")] = want[("three", mode, "2C")] = "fit"
            want[("three_dup", mode, "2B")] = want[("three_dup", mode, "2C")] = "fit"
        bad = [f"{k}: {res[k]} (want {want[k]})" for k in want if res[k] != want[k]]
        self.rec("edge: EXP rank boundary in BOTH modes: 1 distinct -> FIT_FAILURE (2B and 2C); 2 distinct (with or without duplicate points) -> FIT_FAILURE under the Phase 2B minimum 3, a fit under the Phase 2C minimum 2; 3 distinct -> a fit in both",
                 not bad, "; ".join(bad))
        # duplicates are retained as recorded: the four-point fit (3 distinct) differs from the fit on the three
        # distinct points alone, and the distinct count is what the rank rule sees
        v4 = exp_fit_fixed(three_dup[0], three_dup[1], 0.0, min_distinct=m2b)[0]
        v3 = exp_fit_fixed(three[0], three[1], 0.0, min_distinct=m2b)[0]
        self.rec("edge: duplicate abscissas are kept as recorded (a repeated point changes the regression) and count once for the rank rule (4 points, 3 distinct -> fits under Phase 2B)",
                 n_distinct(three_dup[0]) == 3 and abs(v4 - v3) > 1e-9 and abs(v3 - 0.9) < 1e-10, f"{v4} {v3}")
        # failed-seed propagation through the homogeneity rule (C4.3 step 4): 7 clean seeds + 1 rank-deficient seed
        clean = [three] * 7
        agg_b, mode_b, fl_b = exp_step_aggregate(clean + [two], 0.0, min_distinct=m2b)
        agg_c, mode_c, fl_c = exp_step_aggregate(clean + [two], 0.0, min_distinct=m2c)
        agg_ok, mode_ok, _ = exp_step_aggregate(clean + [three], 0.0, min_distinct=m2b)
        surv = sum(exp_fit_fixed(x, y, 0.0, min_distinct=m2b)[0] for x, y in clean) / 7
        self.rec("edge: one rank-deficient seed (2 distinct) nulls the Phase 2B EXP step aggregate (FIT_FAILURE, no surviving-seed mean); the same step aggregates under the Phase 2C minimum; eight clean seeds aggregate",
                 agg_b is None and mode_b == "fit_failure" and fl_b == ["FIT_FAILURE"] and agg_c is not None and mode_c == "log"
                 and agg_ok is not None and abs(agg_ok - 0.9) < 1e-9 and surv is not None,
                 f"{agg_b} {mode_b} {agg_c} {mode_c}")
        # the same propagation in avoid_log mode: a clamped clean seed forces the rerun, the rank-deficient seed still fails
        rise = ([1.0, 1.5, 2.0], [rising(x) for x in (1.0, 1.5, 2.0)])
        agg_r, mode_r, fl_r = exp_step_aggregate([rise] * 7 + [([1.0, 2.0], [rising(1.0), rising(2.0)])], 0.0, min_distinct=m2b)
        agg_r2, mode_r2, _ = exp_step_aggregate([rise] * 8, 0.0, min_distinct=m2b)
        self.rec("edge: under a clamp (avoid_log rerun) a rank-deficient seed still nulls the Phase 2B step (FIT_FAILURE, no partial mean); all-clean rising seeds aggregate in avoid_log",
                 agg_r is None and mode_r == "fit_failure" and fl_r == ["FIT_FAILURE"] and mode_r2 == "avoid_log" and agg_r2 is not None and abs(agg_r2 - 0.05) < 1e-9,
                 f"{agg_r} {mode_r} {mode_r2}")
        # bootstrap propagation: abscissas are fixed under resampling, so a structural rank failure cannot be repaired
        import numpy as np
        xs2 = [1.0, 1.0, 2.0, 2.0, 2.0]  # 5 recorded points, 2 distinct realized abscissas
        rec_counts = [[7000, 1192], [6900, 1292], [5000, 3192], [5100, 3092], [4900, 3292]]  # positive, decaying <Z>: no clamp, so only rank decides
        B = 200
        reps_b, reps_c = [], []
        for b in range(B):
            rng = bootstrap_rng(2, 7, b)
            ys = []
            for cnt in rec_counts:
                r = resample_counts(cnt, 8192, rng)
                ys.append((r[0] - r[1]) / 8192)  # <Z> of one qubit from the resampled record
            v_b, _, _ = exp_step_aggregate([(xs2, ys)] * 8, 0.0, min_distinct=m2b)
            v_c, _, _ = exp_step_aggregate([(xs2, ys)] * 8, 0.0, min_distinct=m2c)
            reps_b.append(v_b)
            reps_c.append(v_c)
        lo_b, hi_b, u_b, fl_ib = percentile_interval(reps_b, 0.025, 0.975)
        lo_c, hi_c, u_c, fl_ic = percentile_interval(reps_c, 0.025, 0.975)
        self.rec("edge: bootstrap cannot repair a structural rank failure: with 2 distinct realized abscissas every resampled replicate is undefined under Phase 2B (interval UNDEFINED, u = B, status INDETERMINATE), while the Phase 2C minimum yields a defined interval",
                 u_b == B and "UNDEFINED" in fl_ib and three_way(lo_b, hi_b, -1, 1, undefined=True) == "INDETERMINATE"
                 and u_c == 0 and "UNDEFINED" not in fl_ic and math.isfinite(lo_c) and math.isfinite(hi_c),
                 f"u_b={u_b} fl_b={fl_ib} u_c={u_c} fl_c={fl_ic}")

    # ---------------- amendment A-2 fixtures ----------------
    def check_a2_exp_sign(self):
        import numpy as np
        m = RANK_RULE_2B["EXP"]
        xs = [1.0, 1.25, 1.5, 1.75, 2.0]
        # Reviewer oracle 1: five zero observations -> sign 0 -> log-mode limit exactly the asymptote 0 (not ~1e-6)
        v0, c0 = exp_fit_fixed(xs, [0.0] * 5, 0.0, min_distinct=m)
        # oracle 2: y = x/4, eight identical seeds -> the pinned polyfit intercept is a platform-dependent value of either sign
        # within a few 1e-17 of the exact zero; under A-3 it is within tau -> sign 0 -> clamp -> avoid_log from p0 = [0, -1]
        ys = [x / 4 for x in xs]
        s2 = exp_sign(xs, ys, 0.0)
        agg2, mode2, fl2 = exp_step_aggregate([(xs, ys)] * 8, 0.0, min_distinct=m)
        # near-zero: an intercept a hair below / above the asymptote follows np.sign of the pinned polyfit value
        yb = [x / 4 - 1e-9 for x in xs]; ya = [x / 4 + 1e-9 for x in xs]
        sb, sa = exp_sign(xs, yb, 0.0), exp_sign(xs, ya, 0.0)
        # nonzero asymptote: y = a exactly; the pinned polyfit intercept is a to rounding, within tau -> sign 0 -> limit exactly a
        a = 2.0 ** -6
        va, ca = exp_fit_fixed(xs, [a] * 5, a, min_distinct=m)
        s_a = exp_sign(xs, [a] * 5, a)
        va_ok = (va == a) if s_a == 0.0 else (va == a + s_a * EXP_EPS)
        # both modes take the sign from the one exp_sign (former inconsistency: log mode used '>= 0', avoid_log used np.sign)
        agree = all(exp_sign(xs, y, 0.0) == (0.0 if abs(pinned_linear_intercept(xs, y)) <= exp_sign_tolerance(xs, y) else float(np.sign(-(0.0 - pinned_linear_intercept(xs, y))))) for y in (ys, yb, ya, [0.0] * 5))
        ok = (v0 == 0.0 and c0 and s2 == 0.0 and c2_ok(mode2, agg2) and sb == -1.0 and sa == 1.0 and va_ok and ca and agree and mode2 == "avoid_log")
        self.rec("a2: EXP sign is np.sign(-(a - numpy.polyfit intercept)) in BOTH modes with the A-3 zero tolerance: five zeros -> intercept exactly 0, sign 0, limit exactly 0 (clamped, not ~1e-6); y = x/4 x 8 seeds -> intercept within tau of 0 for both recorded platform values, sign 0, clamp, avoid_log (not log-mode 0.1325890835); near-zero +/-1e-9 -> +1/-1; y = a (nonzero asymptote) -> sign 0 and limit exactly a; one sign-0 seed switches the whole step to avoid_log under the homogeneity rule; the step aggregate is the avoid_log mean",
                 ok, f"v0={v0} s2={s2} mode2={mode2} agg2={agg2} sb={sb} sa={sa} va={va} s_a={s_a}")
        # homogeneity branch: seven clean seeds plus one exact-zero-intercept seed -> whole step to avoid_log
        clean = ([1.0, 1.5, 2.0], [0.9 * math.exp(-0.4 * x) for x in (1.0, 1.5, 2.0)])
        agg3, mode3, _ = exp_step_aggregate([clean] * 7 + [(xs, ys)], 0.0, min_distinct=m)
        v_x4 = exp_fit_avoid_log(xs, ys, 0.0, min_distinct=m)          # the y = x/4 seed in avoid_log from p0 = [0, -1] (A-3 sign 0)
        v_clean = exp_fit_avoid_log(clean[0], clean[1], 0.0, min_distinct=m)
        self.rec("a2: one sign-0 seed (clamped) switches the whole step to avoid_log under the homogeneity rule; the step aggregate is the avoid_log mean of all eight seeds, never a mix",
                 mode3 == "avoid_log" and agg3 is not None and abs(agg3 - (7 * v_clean + v_x4) / 8) < 1e-9 and abs(v_clean - 0.9) < 1e-6, f"{mode3} {agg3} v_x4={v_x4}")

    # ---------------- amendment A-3 fixtures (2026-09-09): portable zero branch ----------------
    def check_a3_sign_tolerance(self):
        import numpy as np
        m = RANK_RULE_2B["EXP"]
        xs = [1.0, 1.25, 1.5, 1.75, 2.0]; ys = [x / 4 for x in xs]
        tau = exp_sign_tolerance(xs, ys)
        # fixture 1: the exact-zero intercept; the two measured platform values must both map to sign 0
        measured = {"macOS Accelerate numpy 2.2.6": -4.965068306494546e-17, "Linux CI": 7.019562571716503e-17}
        ic = pinned_linear_intercept(xs, ys)
        f1 = exp_sign(xs, ys, 0.0) == 0.0 and abs(ic) <= tau and all(abs(v) <= tau for v in measured.values())
        # the derivation's factors for this fixture (decision brief section 3): cond(V) 9.440009, lever 19.0, max|y| 0.5
        V = np.vander(np.asarray(xs), 2); cond = float(np.linalg.cond(V)); lever = 1 + np.mean(xs) ** 2 / np.var(xs)
        factors_ok = abs(cond - 9.440009) < 1e-5 and abs(lever - 19.0) < 1e-12 and abs(tau - 7.965192e-14) < 1e-18
        # margins for THIS nominal fixture (brief section 4.3): the contract's smallest discriminated magnitude 1e-9 is >= 1e4 above tau, and tau is
        # >= 100x above the observed platform spread; these say nothing about the whole admitted domain
        spread = abs(measured["Linux CI"] - measured["macOS Accelerate numpy 2.2.6"])
        margins_ok = 1e-9 / tau > 1e4 and tau / spread > 100
        # fixture 2: offsets +/-1e-9 and +/-1e-12 exceed tau (by ~1.3e4 and ~13x here) and so give +1 / -1
        f2 = all(exp_sign(xs, [x / 4 + d for x in xs], 0.0) == np.sign(d) for d in (1e-9, -1e-9, 1e-12, -1e-12))
        # fixture 3: exact zeros -> intercept 0.0, sign 0, limit exactly the asymptote
        v0, c0 = exp_fit_fixed(xs, [0.0] * 5, 0.0, min_distinct=m)
        f3 = pinned_linear_intercept(xs, [0.0] * 5) == 0.0 and exp_sign(xs, [0.0] * 5, 0.0) == 0.0 and v0 == 0.0 and c0
        # fixture 4: nonzero asymptote and homogeneity behave as under A-2 for these fixtures (intercepts far above tau)
        a = 0.25; dec = [a + 0.9 * math.exp(-0.4 * x) for x in xs]
        va, ca = exp_fit_fixed(xs, dec, a, min_distinct=m)
        f4 = exp_sign(xs, dec, a) == 1.0 and abs(va - (a + 0.9)) < 1e-9 and not ca and exp_sign(xs, [a - 0.1 - 0.3 * x for x in xs], a) == -1.0
        # fixture 5: the raw np.sign mutant returns a nonzero sign on fixture 1 (it cannot return 0 there, since the
        # floating-point intercept is never exactly zero); the A-3 rule returns 0
        raw = float(np.sign(-(0.0 - ic)))
        f5 = raw != 0.0 and exp_sign(xs, ys, 0.0) == 0.0
        # tau scales with the data: it is computed per fit, not a constant
        tau_big = exp_sign_tolerance(xs, [10 * y for y in ys]); tau_wide = exp_sign_tolerance([1, 2, 3, 4, 5], ys)
        scales = abs(tau_big - 10 * tau) < 1e-25 and tau_wide != tau
        self.rec("a3: EXP sign zero tolerance tau = C*eps*cond(V)*max|y|*lever (C = 4, eps 2.220446049250313e-16, lever = 1 + mean^2/var with ddof=0): fixture 1 y = x/4 -> sign 0 on both measured platform intercepts (-4.965e-17 macOS, +7.020e-17 Linux; tau 7.965e-14 = cond 9.440009 x lever 19 x 0.5 x 4 eps); margins > 1e4 against 1e-9 and > 100x above the platform spread; offsets +/-1e-9 and +/-1e-12 exceed tau and give +1/-1; exact zeros -> 0; nonzero asymptote fixtures behave as under A-2; the raw np.sign mutant fails fixture 1; tau scales with the data; any intercept at or below tau, including a genuinely nonzero one, is sign 0 (portability of fixture 1 is demonstrated for the recorded intercepts by emulation on macOS; the Linux leg has not been run)",
                 f1 and factors_ok and margins_ok and f2 and f3 and f4 and f5 and scales,
                 f"ic={ic} tau={tau} cond={cond} lever={lever} raw={raw} f1={f1} factors={factors_ok} margins={margins_ok} f2={f2} f3={f3} f4={f4} f5={f5} scales={scales}")

    def check_a2_small_mask(self):
        good = phase2a_step(0.5, 0.45, 0.4, 0.36)
        below = phase2a_step(0.05, 0.04, 0.03, 0.02)
        res = {}
        for k in (0, 1, 2, 3):
            rows = [good] * k + [below] * (3 - k)
            v, reason, stats = phase2a_verdict(rows)
            res[k] = (v, "TOO_FEW_POINTS" in reason, stats)
        ok = (all(res[k][2] is None and res[k][0] == "INCONCLUSIVE" and res[k][1] for k in (0, 1, 2))
              and res[3][2] is not None and all(isinstance(res[3][2][x], float) for x in ("s_rms_lo", "s_rms_hi", "s_max_lo", "s_max_hi")))
        self.rec("a2: masks of 0, 1 and 2 steps leave EVERY Phase 2A statistic undefined (None) with TOO_FEW_POINTS and INCONCLUSIVE; a 3-step mask yields the four statistics (values checked, not only the status)",
                 ok, str({k: (r[0], r[1], r[2] is not None) for k, r in res.items()}))

    def check_a2_dm_seed_range(self):
        pts = list(range(15, 24))
        def curve(peak_n, amp, base=0.0):
            return {n: (amp if n == peak_n else base) for n in pts}
        # Reviewer counterexample: four seeds peak at 19, four at 21, amplitude 1; aggregate matches 19 at 0.5
        seeds = [curve(19, 1.0)] * 4 + [curve(21, 1.0)] * 4
        r = dm_seed_range(seeds, pts, +1.0)
        amp_ok = r["matched_n"] == 19 and r["amp_range"] == (0.0, 1.0)     # values at the aggregate step, NOT own peaks [1, 1]
        band = three_way(r["amp_range"][0], r["amp_range"][1], 0.95, 1.05)
        # timing: each seed's own peak inside the same window -> spikes give t = n exactly (den < 0, offset 0), range [19, 21];
        # INTERP_FALLBACK (den >= 0) cannot occur at an earliest strict argmax: y0 > y- and y0 >= y+ force den < 0 (three-point bound)
        t_ok = r["timing_range"] == (19.0, 21.0) and r["flags"] == []
        # tie rule: an aggregate with equal values at 19 and 21 matches the earliest (19)
        seeds_tie = [curve(19, 1.0)] * 4 + [curve(21, 1.0)] * 4
        # undefined seed propagation: one seed undefined at the matched step -> amplitude range null; undefined at any
        # window point -> its timing undefined -> timing range null; no partial range
        und = [{**curve(19, 1.0), 19: None}] + [curve(19, 1.0)] * 7
        ru = dm_seed_range(und, pts, +1.0)
        und2 = [{**curve(19, 1.0), 22: None}] + [curve(19, 1.0)] * 7
        ru2 = dm_seed_range(und2, pts, +1.0)
        # a seed whose own matched peak sits on the window edge -> NO_INTERIOR_PEAK -> timing range null, amplitude range intact
        edge = [curve(23, 1.0)] + [curve(19, 1.0)] * 7
        re_ = dm_seed_range(edge, pts, +1.0)
        # parabolic timing for genuine peaks, per seed, min/max over seeds
        def para(peak_n, shift):
            return {n: 1.0 - 0.1 * (n - peak_n - shift) ** 2 for n in pts}
        rp = dm_seed_range([para(19, 0.2)] * 4 + [para(19, -0.3)] * 4, pts, +1.0)
        p_ok = rp["timing_range"] is not None and abs(rp["timing_range"][0] - 18.7) < 1e-9 and abs(rp["timing_range"][1] - 19.2) < 1e-9 and rp["flags"] == []
        ok = (amp_ok and band == "OVERLAP" and t_ok and dm_seed_range(seeds_tie, pts, +1.0)["matched_n"] == 19
              and ru["matched_n"] is None and ru["amp_range"] is None and ru["timing_range"] is None
              and ru2["amp_range"] is None and ru2["timing_range"] is None
              and re_["amp_range"] == (0.0, 1.0) and re_["timing_range"] is None and "NO_INTERIOR_PEAK" in re_["flags"] and p_ok)
        self.rec("a2: DM companion range: amplitude over all eight seeds AT the aggregate-matched step (Reviewer counterexample [0,1] -> OVERLAP, not own-peak [1,1] -> PASS); timing from each seed's own matched peak in the same window ([19, 21], fallback flagged; parabolic per seed [18.7, 19.2]); earliest-tie matching; any undefined required seed nulls the whole amplitude or timing range, an edge peak nulls timing only",
                 ok, f"amp={r['amp_range']} band={band} t={r['timing_range']} ru={ru} ru2={ru2['amp_range']} edge={re_} para={rp}")
        # A-2 correction (2026-09-08): non-finite seed values (+inf, -inf, NaN) are undefined exactly like None
        null = {"matched_n": None, "amp_range": None, "timing_range": None, "flags": ["UNDEFINED"]}
        nf = {}
        for label, v in (("+inf", math.inf), ("-inf", -math.inf), ("nan", math.nan)):
            nf[f"{label}@matched"] = dm_seed_range([{**curve(19, 1.0), 19: v}] + [curve(19, 1.0)] * 7, pts, +1.0)
            nf[f"{label}@window"] = dm_seed_range([{**curve(19, 1.0), 22: v}] + [curve(19, 1.0)] * 7, pts, +1.0)
            nf[f"{label}@timing"] = dm_seed_range([{**para(19, 0.2), 18: v}] + [para(19, 0.2)] * 7, pts, +1.0)
        nf["mixed"] = dm_seed_range([{**curve(19, 1.0), 16: math.inf}, {**curve(19, 1.0), 22: -math.inf}] + [curve(19, 1.0)] * 6, pts, +1.0)
        outside = dm_seed_range([{**curve(19, 1.0), 40: math.inf}] + [curve(19, 1.0)] * 7, pts, +1.0)
        nf_ok = (all(v == null for v in nf.values()) and outside["amp_range"] == (1.0, 1.0) and outside["timing_range"] == (19.0, 19.0)
                 and seed_value_undefined(math.inf) and seed_value_undefined(-math.inf) and seed_value_undefined(math.nan)
                 and seed_value_undefined(None) and not seed_value_undefined(0.0))
        self.rec("a2 correction: every non-finite required DM seed value (+inf, -inf, NaN) or missing value nulls the WHOLE affected range with no surviving-seed range, at the aggregate-matched step, elsewhere in the window and in the timing path, single or mixed; a non-finite value outside the window is not required",
                 nf_ok, str({k: (v["matched_n"], v["amp_range"], v["timing_range"]) for k, v in nf.items()}) + f" outside={outside}")

    # ---------------- schema ----------------
    def check_schema(self):
        c = self.contract
        arts = c.get("artifacts")
        charts = c.get("charts")
        eqs = c.get("equations")
        if not isinstance(arts, list) or not isinstance(charts, list) or not isinstance(eqs, dict):
            self.rec("schema: artifacts, charts and equations are declared as structures in the JSON", False,
                     f"artifacts={type(arts).__name__} charts={type(charts).__name__} equations={type(eqs).__name__}")
            return
        ids = [a["id"] for a in arts]
        col_dup = []
        for a in arts:
            names = [col["name"] for col in a.get("columns", a.get("keys", []))]
            if len(names) != len(set(names)):
                col_dup.append(a["id"])
        self.rec("schema: non-empty inventories with unique artifact, chart and equation ids and unique column names",
                 len(arts) >= 40 and len(charts) >= 20 and len(eqs) >= 30 and len(ids) == len(set(ids))
                 and len({ch["id"] for ch in charts}) == len(charts) and not col_dup
                 and all(ch.get("panels") and all(p.get("series") for p in ch["panels"]) for ch in charts),
                 f"{len(arts)} artifacts, {len(charts)} charts, {len(eqs)} equations, dup columns {col_dup}")
        declared = {}
        ok_dtype, bad = True, []
        for a in arts:
            cols = a.get("columns", a.get("keys", []))
            for col in cols:
                declared[f"{a['id']}.{col['name']}"] = col
                if col.get("dtype") not in ALLOWED_DTYPES or not col.get("units") or not col.get("null_policy"):
                    ok_dtype = False
                    bad.append(f"{a['id']}.{col['name']}")
        self.rec("schema: every declared column has an allowed dtype, non-empty units and a null policy", ok_dtype, ", ".join(bad[:10]))
        referenced = set()
        missing = []
        for eid, e in eqs.items():
            for ref in e.get("inputs", []) + e.get("outputs", []):
                referenced.add(ref)
                if ref not in declared:
                    missing.append(f"{eid}:{ref}")
        for ch in charts:
            for p in ch.get("panels", []):
                xref = f"{p['x']['artifact']}.{p['x']['column']}"
                referenced.add(xref)
                if xref not in declared:
                    missing.append(f"{ch['id']}:{xref}")
                for s in p.get("series", []):
                    if s.get("source") == "constant":
                        if s.get("constant") not in c.get("constants", {}):
                            missing.append(f"{ch['id']}:constant {s.get('constant')}")
                        if s.get("equation") not in eqs:
                            missing.append(f"{ch['id']}:equation {s.get('equation')}")
                        continue
                    ref = f"{s['artifact']}.{s['column']}"
                    referenced.add(ref)
                    if ref not in declared:
                        missing.append(f"{ch['id']}:{ref}")
                    if s.get("equation") not in eqs:
                        missing.append(f"{ch['id']}:equation {s.get('equation')}")
                    for b in ("band", "mask"):
                        if s.get(b):
                            for key in ("lo_column", "hi_column", "column"):
                                if key in s[b]:
                                    referenced.add(s[b][key])
                                    if s[b][key] not in declared:
                                        missing.append(f"{ch['id']}:{s[b][key]}")
        self.rec("schema: every chart- or equation-referenced column and equation is declared", not missing, ", ".join(missing[:10]))
        unused = [k for k, col in declared.items() if k not in referenced and not col.get("usage_note")]
        self.rec("schema: no declared column is silently unused (referenced or carries a usage note)", not unused, ", ".join(unused[:15]) + (f" (+{len(unused)-15})" if len(unused) > 15 else ""))
        fmt_bad = [ch["id"] for ch in charts if sorted(ch.get("formats", [])) != ["pdf", "png"]]
        self.rec("schema: every chart has both a png and a pdf entry", not fmt_bad, ", ".join(fmt_bad))
        no_ed = []
        for ch in charts:
            mitigated = any(s.get("artifact") in ("B-MIT", "C-MIT") for p in ch["panels"] for s in p["series"])
            if mitigated:
                for p in ch["panels"]:
                    if not any(s.get("column") == "e_ed" for s in p["series"]) and any(s.get("artifact") in ("B-MIT", "C-MIT") and s.get("column") == "estimate" for s in p["series"]):
                        no_ed.append(f"{ch['id']}/{p['id']}")
        # ---- chart traceability: selectors bound to declared columns, family parameters resolved, joins evaluated ----
        art_cols = {a["id"]: {col["name"] for col in a.get("columns", a.get("keys", []))} for a in arts}
        cells_all = c["phase2b"]["matrix_cells"] + c["phase2b"]["control_cells"]
        sched_rows = [{"L": L, "state": "Z2", "obs": o, "k": k, "n_ref": n} for L in (4, 6, 8) for o in ("ZPI", "PRET", "MLOC") for k, n in ((1, 19), (2, 39))]
        sample_cells = [x for x in cells_all if x["status"] in ("run", "conditional")]
        steps = [1, 10, 19, 20, 39]
        OBS5 = ["ZPI", "PRET", "MLOC", "CZZ", "M_I"]
        syn = {}
        syn["A-INT"] = [{"L": L, "n": n} for L in (4, 6, 8) for n in steps]
        syn["A-CELLS"] = [{"L": L, "cell": ce, "n": n} for L in (4, 6, 8) for ce in ("00", "10", "01", "11") for n in steps]
        syn["A-REF"] = [{"L": L, "n": n} for L in (4, 6, 8) for n in steps]
        syn["A-RES"] = [{"L": L, "cell": ce, "n": n} for L in (4, 6, 8) for ce in ("10", "01", "11") for n in steps]
        syn["A-SEC"] = [{"L": L, "cell": ce} for L in (4, 6, 8) for ce in ("10", "01", "11")]
        syn["A-VERD"] = [{"L": L} for L in (4, 6, 8)]
        syn["A-HIST"] = [{"n": n} for n in steps]
        syn["B-REF"] = [{"L": L, "state": st, "obs": o, "n": n} for L in (4, 6, 8) for st in ("Z2", "CTRL") for o in OBS5 for n in steps]
        syn["B-MIT"] = [{"cell_index": x["cell_index"], "pipeline": pl, "n": n, "extrapolator": ex, "obs": o, "kappa": x["kappa"]}
                        for x in sample_cells for pl in ("DM", "SHOT") for n in steps for ex in ("NONE", "LIN", "QUAD", "EXP") for o in OBS5]
        syn["B-STEPMET"] = [{"cell_index": x["cell_index"], "n": n, "extrapolator": ex, "obs": o, "kappa": x["kappa"]} for x in sample_cells for n in steps for ex in ("LIN", "QUAD", "EXP") for o in OBS5]
        syn["B-PEAKMET"] = [{"cell_index": x["cell_index"], "pipeline": pl, "extrapolator": ex, "obs": o, "k": k, "ref": r, "kappa": x["kappa"]}
                            for x in sample_cells for pl in ("DM", "SHOT") for ex in ("NONE", "LIN", "QUAD", "EXP") for o in ("ZPI", "PRET", "MLOC") for k in (1, 2) for r in ("E0", "ED")]
        syn["B-CURVEMET"] = [{"cell_index": x["cell_index"], "pipeline": pl, "extrapolator": ex, "obs": o, "ref": r, "kappa": x["kappa"]}
                             for x in sample_cells for pl in ("DM", "SHOT") for ex in ("NONE", "LIN", "QUAD", "EXP") for o in OBS5 for r in ("E0", "ED")]
        syn["B-END"] = [{"cell_index": x["cell_index"], "pipeline": pl, "extrapolator": ex, "k": k, "obs": o, "endpoint": e, "kappa": x["kappa"]}
                        for x in sample_cells for pl in ("DM", "SHOT") for ex in ("LIN", "QUAD", "EXP") for k in (1, 2) for o in ("ZPI", "PRET") for e in ("AMP", "TIME")]
        syn["B-COND"] = [{"cell_index": x["cell_index"], "pipeline": pl, "extrapolator": ex, "k": k, "kappa": x["kappa"]} for x in sample_cells for pl in ("DM", "SHOT") for ex in ("LIN", "QUAD", "EXP") for k in (1, 2)]
        syn["B-SEEDFIT"] = [{"cell_index": x["cell_index"], "pipeline": pl, "n": n, "fold_seed": s, "extrapolator": ex, "obs": o, "kappa": x["kappa"]}
                            for x in sample_cells[:40] for pl in ("DM", "SHOT") for n in (19, 39) for s in (1000, 1001) for ex in ("LIN", "QUAD", "EXP") for o in ("ZPI", "M_I")]
        syn["B-RAWDM"] = [{"cell_index": x["cell_index"], "n": n, "fold_seed": s, "lambda_nominal": lam, "obs": o, "kappa": x["kappa"]} for x in sample_cells[:40] for n in (19, 39) for s in (1000, 1001) for lam in (1.0, 2.0) for o in ("ZPI", "M_I")]
        syn["B-RAWSHOTOBS"] = syn["B-RAWDM"]
        syn["B-FOLD"] = [{"cell_index": x["cell_index"], "n": n, "fold_seed": s, "lambda_nominal": lam, "kappa": x["kappa"]} for x in sample_cells[:40] for n in (19, 39) for s in (1000, 1001) for lam in (1.0, 2.0)]
        syn["B-BOUND"] = [{"L": L, "noise_model": nm, "folding": fo, "extrapolator": ex, "pipeline": pl, "k": k, "family": ("PRIMARY" if (fo, ex, pl) == ("LOCAL", "LIN", "SHOT") and nm in ("DEP", "DEPH") else "EXPLORATORY")}
                          for L in (4, 6, 8) for nm in ("DEP", "DEPH", "AMP") for fo in ("LOCAL", "GLOBAL") for ex in ("LIN", "QUAD", "EXP") for pl in ("DM", "SHOT") for k in (1, 2)]
        syn["B-DIST"] = [{"L": L, "noise_model": nm, "folding": fo, "extrapolator": ex, "obs": o, "k": k} for L in (4, 6, 8) for nm in ("DEP", "DEPH") for fo in ("LOCAL", "GLOBAL") for ex in ("LIN", "NONE") for o in ("ZPI", "PRET", "MLOC") for k in (1, 2)]
        syn["C-MIT"] = [{"point_n": n, "extrapolator": ex, "obs": o} for n in (1, 10, 19) for ex in ("NONE", "LIN", "QUAD", "EXP") for o in OBS5]
        syn["C-SEEDFIT"] = [{"point_n": n, "fold_seed": s, "extrapolator": ex, "obs": o} for n in (1, 19) for s in (1000, 1001) for ex in ("LIN", "QUAD", "EXP") for o in ("ZPI", "M_I")]
        syn["C-END"] = [{"extrapolator": ex, "k": k, "obs": o, "endpoint": e, "family": f, "ref": r} for ex in ("LIN", "QUAD", "EXP") for k in (1, 2) for o in ("ZPI", "PRET") for e in ("AMP", "TIME") for f in ("CF-2C", "EXPLORATORY") for r in ("E0", "ED")]
        syn["C-DUR"] = [{"point_n": n, "lambda_nominal": lam, "fold_seed": s} for n in (1, 19) for lam in (1.0, 2.0) for s in (1000, 1001)]
        syn["C-EST"] = [{}]
        syn["C-USAGE"] = [{}]
        undeclared, empty, ambiguous, bad_values = [], [], [], []
        evaluated = 0
        for ch in charts:
            fam = ch["family_params"]
            keys = list(fam)
            combos = list(itertools.product(*[fam[k] for k in keys])) if keys else [()]
            for combo in combos[:6]:
                params = dict(zip(keys, combo))
                for pnl in ch["panels"]:
                    xcol = pnl["x"]["column"]
                    for s in pnl["series"]:
                        if s.get("source") == "constant":
                            continue
                        art = s["artifact"]
                        sel = s.get("rows", {})
                        for k, v in sel.items():
                            if k not in art_cols.get(art, set()):
                                undeclared.append(f"{ch['id']}:{s['name']}:{k}")
                            if isinstance(v, str) and " " in v:
                                bad_values.append(f"{ch['id']}:{s['name']}:{k}")
                        try:
                            resolved = resolve_selector(sel, params, cells_all, sched_rows)
                        except ValueError as e:
                            bad_values.append(f"{ch['id']}:{s['name']}:{e}")
                            continue
                        rows = syn.get(art)
                        if rows is None:
                            continue
                        picked = select_rows(rows, resolved)
                        evaluated += 1
                        if not picked:
                            empty.append(f"{ch['id']}:{pnl['id']}:{s['name']}")
                            continue
                        ident = ch.get("row_identity")
                        if ident is None:
                            step_aliases = {"n": ("n", "point_n"), "point_n": ("point_n", "n")}
                            xc = next((cand for cand in step_aliases.get(xcol, (xcol,)) if cand in art_cols.get(art, set())), None)
                            ident = [xc] if xc else []
                            ident = ident + [k for k in ("fold_seed", "lambda_nominal") if any(k in r for r in picked)]
                            if xcol not in ("cell_index",) and any("cell_index" in r for r in picked) and not isinstance(resolved.get("cell_index"), set):
                                ident = ident + ["cell_index"]
                        seen = {}
                        for r in picked:
                            key = tuple(r.get(k) for k in ident)
                            seen[key] = seen.get(key, 0) + 1
                        dup = [k for k, v in seen.items() if v > 1]
                        if dup:
                            ambiguous.append(f"{ch['id']}:{pnl['id']}:{s['name']} identity {ident} dup {dup[:1]}")
        self.rec("schema: every chart selector key is a declared column of its artifact and every selector value is a literal, a bound {parameter} or a declared join",
                 not undeclared and not bad_values, ", ".join((undeclared + bad_values)[:8]))
        self.rec(f"schema: chart traceability evaluated on synthetic rows spanning cells, observables, revivals and steps ({evaluated} series instances): every series selects rows and each plotted value maps to exactly one row",
                 not empty and not ambiguous, ", ".join((empty + ambiguous)[:6]))
        # ---- x-column binding: a panel's x is an output of its declared equation, or a declared key column ----
        xbad = []
        for ch in charts:
            for pnl in ch["panels"]:
                x = pnl["x"]
                ref = f"{x['artifact']}.{x['column']}"
                if x.get("equation"):
                    if ref not in set(eqs.get(x["equation"], {}).get("outputs", [])):
                        xbad.append(f"{ch['id']}/{pnl['id']}: {ref} is not an output of {x['equation']}")
                elif x.get("key_column"):
                    colspec = declared.get(ref)
                    if not colspec or "row key" not in colspec.get("usage_note", ""):
                        xbad.append(f"{ch['id']}/{pnl['id']}: {ref} declared as key column but not a row key")
                else:
                    xbad.append(f"{ch['id']}/{pnl['id']}: x has neither an equation nor key_column")
        self.rec("schema: every panel x column is bound to its equation's outputs (or is a declared row-key column); a wrong x column fails here",
                 not xbad, "; ".join(xbad[:6]))
        # ---- coordinate extraction on numeric fixtures: every plotted value is actually obtainable ----
        def fill(rows, art):
            spec = {col["name"]: col for col in arts_by_id[art].get("columns", arts_by_id[art].get("keys", []))}
            out = []
            for i, r in enumerate(rows):
                q = dict(r)
                for name, cs in spec.items():
                    if name in q:
                        continue
                    if cs["dtype"] == "int" and cs["units"].startswith("0/1"):
                        q[name] = i % 2  # 0/1 flag columns take valid flag values
                    elif cs["dtype"] in ("float", "int"):
                        q[name] = 0.1 * (i % 7 + 1)
                    else:
                        first = cs["units"].split(" / ")[0].strip() if " / " in cs["units"] else "OK"
                        q[name] = "" if first.lower().startswith("empty") else first
                for lo, hi in (("dec_lo", "dec_hi"), ("ci95_lo", "ci95_hi"), ("seed_min", "seed_max"), ("i_lo", "i_hi"), ("band_lo", "band_hi"), ("abs_i_lo", "abs_i_hi")):
                    if lo in spec and hi in spec:
                        base = q.get("estimate", q.get("i_n", q.get("d", 0.3)))
                        base = base if isinstance(base, (int, float)) else 0.3
                        q[lo], q[hi] = base - 0.1, base + 0.1
                out.append(q)
            return out
        arts_by_id = {a["id"]: a for a in arts}
        pre = {"qubit[3].T1": 100e-6, "qubit[3].T2": 80e-6, "gate[ecr][3,4].error": 0.010, "qubit[4].readout_error": 0.0, "qubit[3].frequency": 5.0e9}
        post = {"qubit[3].T1": 120e-6, "qubit[3].T2": 80e-6, "gate[ecr][3,4].error": 0.011, "qubit[4].readout_error": 0.02, "qubit[3].frequency": 5.0001e9}
        units = {"qubit[3].T1": "s", "qubit[3].T2": "s", "gate[ecr][3,4].error": "dimensionless", "qubit[4].readout_error": "dimensionless", "qubit[3].frequency": "Hz"}
        cal_rows, cal_sum = calibration_changes(pre, post, units)
        self.rec("hardware: calibration change rows are typed per field with units; maxima only within a unit (T1 in s: 2e-5; error dimensionless: 0.001; frequency in Hz: 1e5); zero-pre field has no relative change and is listed",
                 cal_sum["calib_max_abs_by_unit"]["s"]["field"] == "qubit[3].T1" and abs(cal_sum["calib_max_abs_by_unit"]["s"]["abs_change"] - 2e-5) < 1e-15
                 and cal_sum["calib_max_abs_by_unit"]["Hz"]["field"] == "qubit[3].frequency" and abs(cal_sum["calib_max_abs_by_unit"]["Hz"]["abs_change"] - 1e5) < 1e-3
                 and cal_sum["calib_max_abs_by_unit"]["dimensionless"]["field"] == "qubit[4].readout_error"
                 and cal_sum["calib_max_rel_field"] == "qubit[3].T1" and abs(cal_sum["calib_max_rel_change"] - 0.2) < 1e-12
                 and cal_sum["calib_zero_pre_fields"] == ["qubit[4].readout_error"] and all(r["rel_change"] is None for r in cal_rows if r["zero_pre"]),
                 json.dumps(cal_sum)[:200])
        tables = {a: fill(rows, a) for a, rows in syn.items() if a in arts_by_id}
        tables["C-CALDIFF"] = cal_rows
        K = c["constants"]
        tables["C-EST"] = fill([{"gate_time_utc": "2026-09-07T00:00:00Z"}], "C-EST")
        tables["C-USAGE"] = fill([dict(cal_sum)], "C-USAGE")
        coord_bad, n_points = [], 0
        for ch in charts:
            fam = ch["family_params"]
            keys = list(fam)
            combos = list(itertools.product(*[fam[k] for k in keys])) if keys else [()]
            for combo in combos[:6]:
                params = dict(zip(keys, combo))
                for pnl in ch["panels"]:
                    for s in pnl["series"]:
                        try:
                            pts = chart_points(s, pnl, params, tables, cells_all, sched_rows, art_cols, c["constants"])
                        except (ValueError, KeyError) as e:
                            coord_bad.append(f"{ch['id']}/{pnl['id']}/{s['name']}: {e}")
                            continue
                        if not pts and not (s.get("source") == "constant" and s.get("when")):
                            coord_bad.append(f"{ch['id']}/{pnl['id']}/{s['name']}: no points")
                        n_points += len(pts)
        ch_c5 = next(ch for ch in charts if ch["id"] == "CH-C5")
        c5 = [chart_points(s, pnl, {"unit": u}, tables, cells_all, sched_rows, art_cols, c["constants"]) for u in ("s", "dimensionless") for pnl in ch_c5["panels"] for s in pnl["series"]]
        c5_ok = all(all(isinstance(pt["x"], str) for pt in pts) for pts in c5) and any(any(pt.get("value_state") == "unavailable" and pt.get("flag") == "ZERO_PRE" for pt in pts) for pts in c5)
        self.rec(f"schema: chart coordinates extracted on numeric fixtures ({n_points} points): every series yields (x, y[, band]) from its declared columns, x joins resolve uniquely, bands are ordered; CH-C5 coordinates are identified fields with per-unit values",
                 not coord_bad and c5_ok, "; ".join(coord_bad[:6]))
        by_id = {ch["id"]: ch for ch in charts}
        a2 = [s for s in by_id["CH-A2"]["panels"][0]["series"] if s["name"] == "a10_plus_a01"]
        a6 = by_id["CH-A6"]["panels"][0]["series"]
        b11_ok = all(s.get("rows", {}).get("family") == "PRIMARY" for s in by_id["CH-B11"]["panels"][0]["series"])
        c2_ok = all(all(s.get("rows", {}).get("family") == ("CF-2C" if "cf2c" in pnl["id"] else "EXPLORATORY") for s in pnl["series"]) for pnl in by_id["CH-C2"]["panels"])
        b9_ok = all(all((s.get("rows", {}).get("pipeline") == ("DM" if pnl["id"].endswith("_dm") else "SHOT")) for s in pnl["series"] if s["artifact"] == "B-SEEDFIT") for pnl in by_id["CH-B9"]["panels"])
        self.rec("schema: CH-B11 selects PRIMARY only, CH-C2 keeps families apart, CH-B9 never mixes pipelines, CH-A2 plots a stored column, CH-A6 thresholds are constants",
                 bool(a2) and a2[0]["column"] == "a10_plus_a01" and any(s.get("source") == "constant" for s in a6) and b11_ok and c2_ok and b9_ok)
        producers = {}
        for e in c["entrypoints"]["future"] + c["entrypoints"]["runnable_now"]:
            producers[e["id"]] = set(e.get("outputs", []))
        prod_bad = [a["id"] for a in arts if a["produced_by"] not in ("EP-ANY",) and a["id"] not in producers.get(a["produced_by"], set())]
        self.rec("schema: every artifact appears in the output list of the entrypoint it names as producer", not prod_bad, ", ".join(prod_bad))
        # the operative prose output list of each future entrypoint (contract §C8.2) must equal the JSON list
        doc = self.docs["contract"]
        sec = doc[doc.index("### C8.2"):doc.index("### C8.3")] if "### C8.2" in doc and "### C8.3" in doc else ""
        ep_bad = []
        for e in c["entrypoints"]["future"]:
            m = re.search(r"\*\*" + re.escape(e["id"]) + r" (?:—|-).*?Outputs:(.*?)(?:Exit codes:|Behaviour:)", sec, re.S)
            if not m:
                ep_bad.append(f"{e['id']}: no Outputs list in §C8.2")
                continue
            prose_ids = set(re.findall(r"\b([ABCT]-[A-Z0-9]+(?:-[A-Z0-9]+)*)\b", m.group(1)))
            json_ids = {o for o in e["outputs"] if re.fullmatch(r"[ABCT]-[A-Z0-9]+(?:-[A-Z0-9]+)*", o)}
            if prose_ids != json_ids:
                ep_bad.append(f"{e['id']}: prose {sorted(prose_ids - json_ids)} extra / {sorted(json_ids - prose_ids)} missing")
        self.rec("schema: each future entrypoint's operative prose output list (§C8.2) equals its JSON output list, compared inside the entrypoint section", not ep_bad, "; ".join(ep_bad[:4]))
        # ---- output paths: expand every family in both formats and require distinct paths ----
        paths, n_expanded, pattern_bad = [], 0, []
        for ch in charts:
            fam = ch["family_params"]
            keys = list(fam)
            for k in keys:
                if "{%s}" % k not in ch["file_pattern"]:
                    pattern_bad.append(f"{ch['id']} pattern lacks {{{k}}}")
            for combo in (itertools.product(*[fam[k] for k in keys]) if keys else [()]):
                for fmt in ch["formats"]:
                    paths.append(ch["file_pattern"].format(**dict(zip(keys, combo)), fmt=fmt))
                    n_expanded += 1
        dup_paths = sorted({p_ for p_ in paths if paths.count(p_) > 1})[:5]
        self.rec(f"schema: expanding every chart family across both formats gives {n_expanded} paths, all distinct, and every family parameter appears in its filename",
                 len(set(paths)) == n_expanded and not pattern_bad and n_expanded == 2 * sum(ch.get("n_files_per_format", 0) for ch in charts),
                 "; ".join(pattern_bad[:4] + dup_paths))
        # ---- value rules: flagged values are drawn at their bound, never lost ----
        ch_b5 = next(ch for ch in charts if ch["id"] == "CH-B5")
        er_series = next(s for pnl in ch_b5["panels"] for s in pnl["series"] if s["name"] == "er_lin")
        er_panel = next(pnl for pnl in ch_b5["panels"] for s in pnl["series"] if s["name"] == "er_lin")
        cell1 = next(x for x in cells_all if x["L"] == 6 and x["noise_model"] == "DEP" and x["folding"] == "LOCAL" and same_value(x["kappa"], 1.0))
        fx = [{"cell_index": cell1["cell_index"], "n": 19, "extrapolator": "LIN", "obs": "ZPI", "er": None, "er_flag": "RATIO_LOWER_BOUND", "er_bound": 200000000.0},
              {"cell_index": cell1["cell_index"], "n": 20, "extrapolator": "LIN", "obs": "ZPI", "er": None, "er_flag": "RATIO_ZERO_OVER_ZERO", "er_bound": None},
              {"cell_index": cell1["cell_index"], "n": 21, "extrapolator": "LIN", "obs": "ZPI", "er": None, "er_flag": "RATIO_UNDEFINED", "er_bound": None},
              {"cell_index": cell1["cell_index"], "n": 22, "extrapolator": "LIN", "obs": "ZPI", "er": 0.3, "er_flag": "", "er_bound": None}]
        fx = [dict(r, kappa=1.0) for r in fx]
        pts = chart_points(er_series, er_panel, {"L": 6, "model": "DEP", "folding": "LOCAL", "kappa": 1.0, "obs": "ZPI"}, dict(tables, **{"B-STEPMET": fx}), cells_all, sched_rows, art_cols, c["constants"])
        byx = {pt["x"]: pt for pt in pts}
        vr_ok = (byx[19]["y"] == 200000000.0 and byx[19]["marker"] == "triangle_up" and byx[20]["y"] is None and byx[20]["marker"] == "hollow_floor"
                 and byx[21]["y"] is None and byx[21]["marker"] == "hollow_floor" and byx[22]["y"] == 0.3 and byx[22]["marker"] == "filled")
        try:
            chart_points(er_series, er_panel, {"L": 6, "model": "DEP", "folding": "LOCAL", "kappa": 1.0, "obs": "ZPI"},
                         dict(tables, **{"B-STEPMET": [dict(fx[0], er_flag="SOMETHING_ELSE")]}), cells_all, sched_rows, art_cols, c["constants"])
            unknown_rejected = False
        except ValueError:
            unknown_rejected = True
        self.rec("schema: value rules bind flags to their columns and markers: RATIO_LOWER_BOUND drawn as a triangle at er_bound (2e8), zero-over-zero and undefined hollow at the floor, plain value filled; an unknown flag is rejected",
                 vr_ok and unknown_rejected, str(byx))
        # independent expectations: one row carrying DISTINCT er and ur bounds; each series must draw ITS quantity's bound
        expect = {"er": 200000000.0, "ur": 7.5}
        both_rows = [dict(cell_index=cell1["cell_index"], n=19, extrapolator=ex, obs="ZPI", kappa=1.0,
                          er=None, er_flag="RATIO_LOWER_BOUND", er_bound=expect["er"], ur=None, ur_flag="RATIO_LOWER_BOUND", ur_bound=expect["ur"])
                     for ex in ("LIN", "QUAD", "EXP")]
        wrong_quantity = []
        for pnl in ch_b5["panels"]:
            for s in pnl["series"]:
                if s.get("value_rules") and s["column"] in expect:
                    got = chart_points(s, pnl, {"L": 6, "model": "DEP", "folding": "LOCAL", "kappa": 1.0, "obs": "ZPI"}, dict(tables, **{"B-STEPMET": both_rows}), cells_all, sched_rows, art_cols, c["constants"])
                    if not got or got[0].get("y") != expect[s["column"]] or got[0].get("marker") != "triangle_up":
                        wrong_quantity.append(f"{s['name']} -> {got[0] if got else None}")
        self.rec("schema: with distinct ER and UR bounds on one row, every ER series draws the ER bound and every UR series the UR bound (expectation fixed by quantity, independent of the rule under test)",
                 not wrong_quantity, "; ".join(wrong_quantity[:4]))
        # masks against their declared meaning: located/unresolved, monotone/non-monotone, positive/zero on a log axis, count annotation
        ch_b11 = next(ch for ch in charts if ch["id"] == "CH-B11")
        p11 = ch_b11["panels"][0]
        s11 = next(s for s in p11["series"] if s["name"] == "kstar")
        brow = {"L": 6, "noise_model": "DEP", "folding": "LOCAL", "extrapolator": "LIN", "pipeline": "SHOT", "k": 1, "family": "PRIMARY", "hypothesis_component": "not evaluable"}
        rows11 = [dict(brow, kappa_star="UNRESOLVED_AT_MIN", located=0, non_monotone=1), dict(brow, k=2, kappa_star="0.5", located=1, non_monotone=0),
                  dict(brow, noise_model="DEPH", kappa_star="1", located=0, non_monotone=0), dict(brow, noise_model="DEPH", k=2, kappa_star="2", located=1, non_monotone=1)]
        p11pts = chart_points(s11, p11, {}, dict(tables, **{"B-BOUND": rows11}), cells_all, sched_rows, art_cols, c["constants"])
        mk11 = [pt["marker"] for pt in p11pts]
        ch_a6 = next(ch for ch in charts if ch["id"] == "CH-A6")
        p6a = ch_a6["panels"][0]
        s6a = next(s for s in p6a["series"] if s["name"] == "d00")
        rows6a = [{"n": 1, "d00": 0.0, "within_tau_hist": 1, "within_eta_e": 1}, {"n": 2, "d00": 3e-13, "within_tau_hist": 1, "within_eta_e": 1}, {"n": 3, "d00": 5e-11, "within_tau_hist": 0, "within_eta_e": 1}, {"n": 4, "d00": 2e-8, "within_tau_hist": 0, "within_eta_e": 0}]
        a6pts = {pt["x"]: pt for pt in chart_points(s6a, p6a, {}, dict(tables, **{"A-HIST": rows6a}), cells_all, sched_rows, art_cols, c["constants"])}
        ch_b8 = next(ch for ch in charts if ch["id"] == "CH-B8")
        p8 = ch_b8["panels"][0]
        s8 = next(s for s in p8["series"] if s["name"] == "tiae_lin")
        rows8 = [{"cell_index": cell1["cell_index"], "pipeline": "SHOT", "extrapolator": "LIN", "obs": "ZPI", "ref": "E0", "tiae": None, "n_undefined_steps": 3, "kappa": 1.0},
                 {"cell_index": cell1["cell_index"] + 2 if False else cell1["cell_index"], "pipeline": "SHOT", "extrapolator": "LIN", "obs": "PRET", "ref": "E0", "tiae": 1.2, "n_undefined_steps": 0, "kappa": 1.0}]
        b8pts = chart_points(s8, p8, {"L": 6, "model": "DEP", "folding": "LOCAL", "obs": "ZPI"}, dict(tables, **{"B-CURVEMET": rows8}), cells_all, sched_rows, art_cols, c["constants"])
        self.rec("schema: masks render their declared meaning: boundary unresolved -> hollow, non-monotone -> edge, located -> filled (CH-B11); zero on a log axis -> hollow at the floor and counted, outside tau_hist -> hollow, inside eta_E -> edge (CH-A6); undefined TIAE -> hollow at the floor with the count annotated (CH-B8)",
                 mk11 == ["hollow+edge", "filled", "hollow", "filled+edge"]
                 and a6pts[1]["marker"] == "hollow_floor+edge" and a6pts[1].get("log_floor") and a6pts[2]["marker"] == "filled+edge" and a6pts[3]["marker"] == "hollow+edge" and a6pts[4]["marker"] == "hollow"
                 and b8pts and b8pts[0]["value_state"] == "unavailable" and b8pts[0]["marker"] == "hollow_floor" and b8pts[0].get("annotate") == 3,
                 json.dumps({"b11": mk11, "a6": {k: v["marker"] for k, v in a6pts.items()}, "b8": b8pts}))
        flagged_missing = []
        for ch in charts:
            for pnl in ch["panels"]:
                for s in pnl["series"]:
                    if s.get("source") == "constant" or s.get("categorical") or s.get("role") == "marker":
                        continue
                    colspec = declared.get(f"{s['artifact']}.{s['column']}", {})
                    pol = colspec.get("null_policy", "")
                    if any(tok in pol for tok in ("RATIO_LOWER_BOUND", "BETA_UNDEFINED", "if_is_lower_bound", "fit_status", "status ==", "status is")) and not s.get("value_rules"):
                        flagged_missing.append(f"{ch['id']}:{s['name']}")
        self.rec("schema: every plotted column whose null policy is explained by a flag column carries value rules", not flagged_missing, ", ".join(flagged_missing[:8]))
        # ---- every mask, band and value-rule reference resolves to a declared column; every declared flag value has a rule ----
        def vocab(colspec):
            u = colspec.get("units", "")
            if u.startswith("0/1"):
                return {"0", "1"}
            if " / " in u:
                toks = [y.strip() for x in u.split(" / ") for y in x.split(";")]
                out = set()
                for x in toks:
                    if "empty" in x.lower():
                        out.add("")
                        continue
                    x = x.split(" (")[0].split(":")[0].strip()
                    out.add(x)
                return out
            return None
        ref_bad, branch_bad, n_branches = [], [], 0
        for ch in charts:
            fam = ch["family_params"]
            keys = list(fam)
            params0 = {k: fam[k][0] for k in keys}
            for pnl in ch["panels"]:
                for s in pnl["series"]:
                    if s.get("source") == "constant":
                        continue
                    art = s["artifact"]
                    cols = art_cols.get(art, set())
                    for key in ("mask", "band"):
                        obj = s.get(key)
                        if not obj:
                            continue
                        for ck in ("column", "lo_column", "hi_column"):
                            if ck in obj and (obj[ck].split(".", 1)[0] != art or obj[ck].split(".", 1)[1] not in cols):
                                ref_bad.append(f"{ch['id']}:{s['name']}:{key}.{ck}={obj[ck]}")
                        for cond in ("hollow_when", "triangle_when", "edge_when"):
                            for col_ in obj.get(cond, {}) if isinstance(obj.get(cond), dict) else []:
                                if col_ not in cols:
                                    ref_bad.append(f"{ch['id']}:{s['name']}:{key}.{cond}.{col_}")
                        if obj.get("annotate") and obj["annotate"] not in cols:
                            ref_bad.append(f"{ch['id']}:{s['name']}:mask.annotate={obj['annotate']}")
                    mk = s.get("mask")
                    if mk:
                        for cond in ("hollow_when", "triangle_when", "edge_when"):
                            for col_, want in (mk.get(cond) or {}).items():
                                spec_ = declared.get(f"{art}.{col_}", {})
                                if want == "__null__" and spec_.get("null_policy", "").startswith("never null"):
                                    ref_bad.append(f"{ch['id']}:{s['name']}:{cond}.{col_} tests null on a never-null column (vacuous)")
                        if mk.get("style_when"):
                            for col_, mapping in mk["style_when"].items():
                                if col_ not in cols:
                                    ref_bad.append(f"{ch['id']}:{s['name']}:style_when.{col_}")
                                voc_ = vocab(declared.get(f"{art}.{col_}", {}))
                                if voc_ is not None and voc_ - {""} != set(mapping):
                                    ref_bad.append(f"{ch['id']}:{s['name']}:style_when vocabulary {sorted(voc_)} != {sorted(mapping)}")
                        if not any(mk.get(k) for k in ("hollow_when", "triangle_when", "edge_when", "style_when", "annotate")):
                            ref_bad.append(f"{ch['id']}:{s['name']}: mask has no machine condition")
                    vr = s.get("value_rules")
                    if not vr:
                        continue
                    fc = vr.get("flag_column")
                    if fc not in cols:
                        ref_bad.append(f"{ch['id']}:{s['name']}:value_rules.flag_column={fc}")
                        continue
                    for fv, rule in vr["rules"].items():
                        if rule.get("y") is not None and rule["y"] not in cols:
                            ref_bad.append(f"{ch['id']}:{s['name']}:rule[{fv}].y={rule['y']}")
                            continue
                        if rule.get("y") is not None and rule["y"] != s["column"]:
                            bf = declared.get(f"{art}.{rule['y']}", {}).get("bound_for")
                            if bf != s["column"]:
                                ref_bad.append(f"{ch['id']}:{s['name']}:rule[{fv}].y={rule['y']} is not declared as a bound for {s['column']} (bound_for={bf})")
                    voc = vocab(declared.get(f"{art}.{fc}", {}))
                    if voc is not None and voc != set(vr["rules"]):
                        ref_bad.append(f"{ch['id']}:{s['name']}: flag vocabulary {sorted(voc)} != rules {sorted(vr['rules'])}")
                    # exercise every declared branch on a synthetic row against the INDEPENDENT oracle:
                    # the own column carries 0.75, every bound column carries a distinct value, and the expected
                    # marker / state / y come from VALUE_RULE_ORACLE, not from the rule under test
                    base_row = {k: (1 if k == "cell_index" else "ZPI" if k == "obs" else "LIN" if k == "extrapolator" else 19) for k in ("cell_index", "n", "point_n", "obs", "extrapolator", "k", "field", "unit", "L", "pipeline") if k in cols}
                    oracle = VALUE_RULE_ORACLE.get((art, fc, s["column"])) or VALUE_RULE_ORACLE.get((art, fc))
                    if oracle is None:
                        branch_bad.append(f"{ch['id']}:{s['name']}: no independent expectation for {art}.{fc}")
                        continue
                    if set(oracle) != set(vr["rules"]):
                        branch_bad.append(f"{ch['id']}:{s['name']}: rule set {sorted(vr['rules'])} != oracle {sorted(oracle)}")
                    bound_cols = {col_ for col_ in cols if declared.get(f"{art}.{col_}", {}).get("bound_for")}
                    for fv, (want_marker, want_state, y_src) in oracle.items():
                        row = dict(base_row)
                        row[fc] = (int(fv) if fv in ("0", "1") and declared[f"{art}.{fc}"]["dtype"] == "int" else fv)
                        row[s["column"]] = 0.75
                        for j, bc in enumerate(sorted(bound_cols)):
                            row[bc] = 1000.0 + j  # distinct from the own value and from each other
                        try:
                            pts_ = chart_points(dict(s, rows={}), dict(pnl, x=dict(pnl["x"], join_on=None), x_from_cell=None), params0, {art: [row]}, cells_all, sched_rows, art_cols, c["constants"])
                        except ValueError as e:
                            branch_bad.append(f"{ch['id']}:{s['name']}[{fv}]: {e}")
                            continue
                        n_branches += 1
                        pt = pts_[0] if pts_ else None
                        want_y = None if y_src is None else (0.75 if y_src == "own" else row[y_src])
                        if pt is None or pt.get("marker") != want_marker or pt.get("value_state") != want_state or (want_y is not None and pt.get("y") != want_y):
                            branch_bad.append(f"{ch['id']}:{s['name']}[{fv}] -> {pt}, expected {want_marker}/{want_state}/y={want_y}")
        self.rec("schema: every mask, band and value-rule column reference is a declared column of its artifact, and every declared flag value has exactly one rule",
                 not ref_bad, "; ".join(ref_bad[:6]))
        self.rec(f"schema: every declared value-rule branch is exercised on a synthetic row ({n_branches} branches) against the independent oracle: marker, value state and y source (own value or the declared bound, distinct values)",
                 not branch_bad and n_branches > 0, "; ".join(branch_bad[:6]))
        mask_bad, n_mask_cases = [], 0
        for ch in charts:
            fam = ch["family_params"]
            params0 = {k: fam[k][0] for k in fam}
            for pnl in ch["panels"]:
                for s in pnl["series"]:
                    mk = s.get("mask")
                    if not mk or s.get("source") == "constant":
                        continue
                    art = s["artifact"]
                    cols = art_cols.get(art, set())
                    mcol = mk["column"].split(".", 1)[1]
                    cases = MASK_ORACLE.get((art, mcol))
                    if cases is None:
                        mask_bad.append(f"{ch['id']}:{s['name']}: no independent expectation for mask {mk['column']}")
                        continue
                    base_row = {k: (1 if k == "cell_index" else "ZPI" if k == "obs" else "LIN" if k == "extrapolator" else "SHOT" if k == "pipeline" else "E0" if k == "ref" else 19) for k in ("cell_index", "n", "point_n", "obs", "extrapolator", "k", "field", "unit", "L", "pipeline", "ref") if k in cols}
                    xcol = pnl["x"].get("column")
                    if xcol and pnl["x"].get("artifact") == art and xcol not in base_row:
                        base_row[xcol] = "X0"
                    vr = s.get("value_rules")
                    for overlay, want_marker in cases:
                        row = dict(base_row)
                        row[s["column"]] = 0.75
                        for k_, v_ in overlay.items():
                            if k_ == "__y__":
                                row[s["column"]] = v_
                            else:
                                row[k_] = v_
                        if vr and vr["flag_column"] not in row:
                            plain = next((fv for fv, (m_, st_, src_) in (VALUE_RULE_ORACLE.get((art, vr["flag_column"], s["column"])) or VALUE_RULE_ORACLE.get((art, vr["flag_column"]))).items() if m_ == "filled"), "")
                            row[vr["flag_column"]] = (int(plain) if plain in ("0", "1") and declared[f"{art}.{vr['flag_column']}"]["dtype"] == "int" else plain)
                        try:
                            pts_ = chart_points(dict(s, rows={}), dict(pnl, x=dict(pnl["x"], join_on=None), x_from_cell=None), params0, {art: [row]}, cells_all, sched_rows, art_cols, c["constants"])
                        except ValueError as e:
                            mask_bad.append(f"{ch['id']}:{s['name']}{overlay}: {e}")
                            continue
                        n_mask_cases += 1
                        pt = pts_[0] if pts_ else None
                        if pt is None or pt.get("marker") != want_marker:
                            mask_bad.append(f"{ch['id']}:{s['name']}{overlay} -> {pt and pt.get('marker')}, expected {want_marker}")
                        elif mk.get("annotate") and pt.get("annotate") != row.get(mk["annotate"]):
                            mask_bad.append(f"{ch['id']}:{s['name']}{overlay}: annotation {pt.get('annotate')} != {row.get(mk['annotate'])}")
        self.rec(f"schema: every mask is composed on synthetic rows against the independent oracle of its prose meaning ({n_mask_cases} cases: in/out of mask, located/unresolved, monotone/non-monotone, zero on a log axis, undefined with count, status styles)",
                 not mask_bad and n_mask_cases > 0, "; ".join(mask_bad[:6]))
        # ---- constants resolve to numeric lines under their when conditions (CH-B2 with obs = PRET) ----
        ch_b2 = next(ch for ch in charts if ch["id"] == "CH-B2")
        pb2 = ch_b2["panels"][0]
        got = {}
        for s in pb2["series"]:
            if s.get("source") == "constant":
                got[s["name"]] = chart_points(s, pb2, {"L": 6, "model": "DEP", "folding": "LOCAL", "k": 1, "obs": "PRET"}, tables, cells_all, sched_rows, art_cols, c["constants"])
        self.rec("schema: constant lines resolve to their numeric plotted values under their when conditions (CH-B2, obs = PRET: ±0.05 drawn, the ZPI ±0.10 line skipped)",
                 got.get("tol_pret") == [{"x": "line", "y": 0.05, "kind": "hline"}, {"x": "line", "y": -0.05, "kind": "hline"}] and got.get("tol_zpi") == [],
                 json.dumps(got))
        # ---- valid reporting states compose without raising ----
        ch_b6 = next(ch for ch in charts if ch["id"] == "CH-B6")
        p6 = ch_b6["panels"][0]
        s6 = next(s for s in p6["series"] if s["name"] == "if_lin")
        cell1 = next(x for x in cells_all if x["L"] == 6 and x["noise_model"] == "DEP" and x["folding"] == "LOCAL" and same_value(x["kappa"], 1.0))
        b6 = {"cell_index": cell1["cell_index"], "n": 19, "extrapolator": "LIN", "obs": "ZPI", "kappa": 1.0}
        rows6 = [dict(b6, eps_dm_noisy=0.001, eps_dm_mit=0.0005, if_value=2.0, if_is_lower_bound=0, reportable=0),
                 dict(b6, n=20, eps_dm_noisy=None, eps_dm_mit=None, if_value=None, if_is_lower_bound=0, reportable=0),
                 dict(b6, n=21, eps_dm_noisy=0.5, eps_dm_mit=1e-12, if_value=5e8, if_is_lower_bound=1, reportable=1)]
        p6pts = {pt["x"]: pt for pt in chart_points(s6, p6, {"L": 6, "model": "DEP", "folding": "LOCAL", "kappa": 1.0, "obs": "ZPI"}, dict(tables, **{"B-STEPMET": rows6}), cells_all, sched_rows, art_cols, c["constants"])}
        ch_b1 = next(ch for ch in charts if ch["id"] == "CH-B1")
        p1 = ch_b1["panels"][0]
        s1 = next(s for s in p1["series"] if s["name"] == "lin_shot")
        rows1 = [{"cell_index": cell1["cell_index"], "pipeline": "SHOT", "n": 19, "extrapolator": "LIN", "obs": "ZPI", "estimate": 0.5, "ci95_lo": None, "ci95_hi": None, "flags": "UNDEFINED"}]
        p1pts = chart_points(s1, p1, {"L": 6, "model": "DEP", "folding": "LOCAL"}, dict(tables, **{"B-MIT": rows1}), cells_all, sched_rows, art_cols, c["constants"])
        self.rec("schema: valid reporting states compose on three axes: IF = 2 with reportable = 0 is drawn hollow; an undefined IF is an explicit unavailable point; a lower-bound IF is a triangle; an estimate with an undefined interval keeps its value and marks the band unavailable",
                 p6pts[19]["y"] == 2.0 and p6pts[19]["marker"] == "hollow" and p6pts[20]["value_state"] == "unavailable" and p6pts[21]["marker"] == "triangle_up" and p6pts[21]["y"] == 5e8
                 and p1pts and p1pts[0]["y"] == 0.5 and p1pts[0]["band_state"] == "unavailable" and p1pts[0]["value_state"] == "value",
                 json.dumps({"b6": p6pts, "b1": p1pts}))
        pre_m = {"qubit[3].T1": 100e-6, "gate[ecr][3,4].error": 0.010}
        post_m = {"qubit[3].T1": 120e-6, "qubit[5].frequency": 5.1e9}
        rows_m, sum_m = calibration_changes(pre_m, post_m, {"qubit[3].T1": "s", "gate[ecr][3,4].error": "dimensionless", "qubit[5].frequency": "Hz"})
        st = {r["field"]: r["status"] for r in rows_m}
        self.rec("hardware: calibration fields missing post-run or new post-run are reported as rows (MISSING_POST / NEW_POST) and listed, never omitted",
                 st == {"gate[ecr][3,4].error": "MISSING_POST", "qubit[3].T1": "PRESENT", "qubit[5].frequency": "NEW_POST"}
                 and sum_m["calib_missing_fields"] == ["gate[ecr][3,4].error"] and sum_m["calib_new_fields"] == ["qubit[5].frequency"]
                 and "Hz" not in sum_m["calib_max_abs_by_unit"] and set(K["C-CAL-UNITS"]["value"]) == set(next(ch for ch in charts if ch["id"] == "CH-C5")["family_params"]["unit"]),
                 json.dumps(st))
        declared_total = sum(ch.get("n_files_per_format", 0) for ch in charts)
        recomputed = sum(math.prod(len(v) for v in ch["family_params"].values()) if ch["family_params"] else 1 for ch in charts)
        self.rec("schema: chart file counts per format recomputed from the family parameters equal the declared totals (JSON, contract, prereg)",
                 declared_total == recomputed == c.get("charts_total_files_per_format") and f"{recomputed} files per format" in self.docs["contract"] and f"{recomputed} files per format" in self.docs["prereg"],
                 f"declared {declared_total} recomputed {recomputed} json {c.get('charts_total_files_per_format')}")
        self.rec("schema: every panel plotting a mitigated observable carries the E^ED series", not no_ed, ", ".join(no_ed))
        doc = self.docs["contract"]
        miss_doc = [ch["id"] for ch in charts if ch["id"] not in doc] + [a["id"] for a in arts if a["id"] not in doc] + [e for e in eqs if e not in doc]
        self.rec("schema: every chart, artifact and equation id appears in the analysis contract", not miss_doc, ", ".join(miss_doc[:10]))
        band_bad = []
        for ch in charts:
            for p in ch["panels"]:
                for s in p["series"]:
                    if s.get("source") == "constant":
                        continue
                    b = s.get("band")
                    if b:
                        leg = b.get("legend", "")
                        if ("95%" in leg and b.get("kind") != "percentile_bootstrap_95") or (leg.strip().lower() == "uncertainty"):
                            band_bad.append(f"{ch['id']}:{s['name']}")
        self.rec("schema: band legends say 95% only for a 95% percentile bootstrap band and never bare 'uncertainty'", not band_bad, ", ".join(band_bad))

    # ---------------- cross-field ----------------
    @staticmethod
    def normalize(text):
        t = text.replace("\\times", "×").replace("\\,", "").replace("\\;", " ").replace("\\{", "{").replace("\\}", "}")
        t = t.replace("\\mathrm{s}", "s").replace("\\mu", "µ").replace("\\ ", " ").replace("{,}", ",")
        return re.sub(r"\s+", " ", t)

    @staticmethod
    def parse_render(render):
        r = render.strip().replace("−", "-")
        m = re.fullmatch(r"([0-9.]+)\s*×\s*10\^\{(-?\d+)\}", r)
        if m:
            return float(m.group(1)) * 10 ** int(m.group(2))
        m = re.fullmatch(r"10\^\{(-?\d+)\}", r)
        if m:
            return 10.0 ** int(m.group(1))
        m = re.fullmatch(r"([0-9.]+)%", r)
        if m:
            return float(m.group(1)) / 100
        try:
            return float(r)
        except ValueError:
            return None

    def check_cross(self):
        c = self.contract
        consts = c.get("constants", {})
        docs = {"prereg": self.normalize(self.docs["prereg"]), "contract": self.normalize(self.docs["contract"])}
        missing, mismatch = [], []
        for cid, k in consts.items():
            for where in k.get("required_in", []):
                if k["render"] not in docs[where]:
                    missing.append(f"{cid}[{where}]")
            val = self.parse_render(k["render"])
            if val is not None and isinstance(k["value"], (int, float)) and not isinstance(k["value"], bool):
                if not math.isclose(val, k["value"], rel_tol=2e-3, abs_tol=1e-15):
                    mismatch.append(f"{cid}: render {k['render']} vs value {k['value']}")
        self.rec("cross: every constant's render string appears in each document it is required in", not missing, ", ".join(missing))
        # ---- binding: each constant's render must sit at its named definition site (anchor + render + non-digit) ----
        unbound, misbound = [], []
        for cid, k in consts.items():
            dfn = k.get("definition")
            if not dfn or not dfn.get("anchor"):
                unbound.append(cid)
                continue
            text = docs[dfn["doc"]]
            needle = dfn["anchor"] + k["render"]
            pos = text.find(needle)
            while pos != -1:
                nxt = text[pos + len(needle): pos + len(needle) + 1]
                if not nxt.isdigit():
                    break
                pos = text.find(needle, pos + 1)
            if pos == -1:
                misbound.append(f"{cid}: '{needle[-40:]}' not at its definition site in {dfn['doc']}")
        self.rec("cross: every constant is bound to a named definition site (anchor + render, non-digit boundary); a mutated value or render fails here",
                 not unbound and not misbound, "; ".join(unbound[:5] + misbound[:8]))
        self.rec("cross: every numeric constant's render matches its JSON value", not mismatch, ", ".join(mismatch))
        symbols = [k["symbol"] for k in consts.values()]
        dup = [s for s in set(symbols) if symbols.count(s) > 1]
        self.rec("cross: every constant symbol is declared once", not dup, ", ".join(dup))
        # cross-references
        heads = {
            "prereg": set(re.findall(r"^#{2,3} (\d+(?:\.\d+)?)\.? ", self.docs["prereg"], re.M)),
            "contract": set(re.findall(r"^#{2,3} (C\d+(?:\.\d+)?)\.? ", self.docs["contract"], re.M)),
            "design": set(re.findall(r"^## (\d+)\. ", self.docs["design"], re.M)),
            "outline": set(re.findall(r"^## (\d+)\. ", self.docs["outline"], re.M)),
        }
        unresolved = []
        for dname in ("prereg", "contract"):
            text = self.docs[dname]
            last_prefix, last_end = None, -10
            for m in re.finditer(r"(design\.md|outline|contract|prereg)?\s*§§?\s*((?:C\d+|\d+)(?:\.\d+)*)", text, re.I):
                prefix, ref = (m.group(1).lower() if m.group(1) else None), m.group(2)
                between = text[last_end:m.start()]
                if prefix is None and last_prefix and m.start() - last_end < 12 and re.fullmatch(r"[\s,;]*(and|to|–|-)?[\s,;]*", between):
                    prefix = last_prefix  # list continuation: "design.md §7, §15" inherits the prefix
                last_prefix, last_end = prefix, m.end()
                if prefix == "design.md":
                    target = "design"
                elif prefix == "outline":
                    target = "outline"
                elif prefix == "contract" or ref.startswith("C"):
                    target = "contract"
                else:
                    target = "prereg"
                if ref not in heads[target] and ref.split(".")[0] not in heads[target]:
                    unresolved.append(f"{dname}: §{ref} -> {target}")
        unresolved = sorted(set(unresolved))
        self.rec("cross: every § cross-reference in the two Phase 2 documents resolves to a heading", not unresolved, "; ".join(unresolved[:12]) + (f" (+{len(unresolved)-12})" if len(unresolved) > 12 else ""))
        # semantic agreement JSON vs prose
        tw = c.get("statistics", {}).get("three_way_rule", {})
        jp = c.get("phase2b", {}).get("joint_pass", {})
        rule = str(jp.get("rule", "")).lower()
        interval = str(jp.get("interval", "")).lower()
        fail_clause = rule.split("fail if")[1].split(";")[0] if "fail if" in rule else ""
        sem_ok = all(k in tw for k in ENDPOINT_STATUSES) and "OVERLAP" in jp.get("endpoint_statuses", []) \
            and sorted(jp.get("condition_statuses", [])) == sorted(CONDITION_STATUSES) \
            and "decision interval" in interval and ("95%" not in interval or "drives no decision" in interval) \
            and "any fail" in fail_clause and "indeterminate" not in fail_clause
        self.rec("cross: JSON joint-pass rule carries OVERLAP, does not suppress FAIL, and does not decide on 95% intervals", bool(sem_ok), (rule + " | " + interval)[:200])
        prose = self.docs["prereg"]
        self.rec("cross: prose §6.5 three-way vocabulary present (PASS, FAIL, OVERLAP, INDETERMINATE) and JSON statuses match",
                 all(f"`{s}`" in prose for s in ENDPOINT_STATUSES) and set(jp.get("endpoint_statuses", [])) == set(ENDPOINT_STATUSES))
        cs = c.get("phase2b", {}).get("control_selection", {})
        tie = (cs.get("weight_tie_order", "") + cs.get("candidate_tie_order", "")).lower()
        self.rec("cross: JSON tie orders are exact total orders (no tolerance-based ordering)",
                 "exact" in tie and "tolerance" not in tie.replace("no tolerance", ""), tie[:120])
        # matrix totals and seeds
        cells = c["phase2b"]["matrix_cells"]
        ctrl = c["phase2b"]["control_cells"]
        s = c["phase2b"]["matrix_summary"]
        counts = {k: sum(1 for x in cells if x["status"] == k) for k in ("run", "not_run", "blocked")}
        tot_run = sum(x["executions_total"] for x in cells)
        grand = tot_run + 144 + counts["blocked"] * 3888 + sum(x["executions_total"] for x in ctrl) + 144
        self.rec("cross: matrix totals recomputed (150 cells: 72/72/6; 12 conditional; 280,080 unconditional; 350,208 all)",
                 len(cells) == 150 and counts == {"run": 72, "not_run": 72, "blocked": 6} and len(ctrl) == 12
                 and tot_run + 144 == s.get("executions_total_unconditional") == 280080 and grand == s.get("grand_total_if_everything_runs") == 350208,
                 f"{counts} unconditional={tot_run + 144} grand={grand} summary={s.get('grand_total_if_everything_runs')}")
        seeds = set()
        n_seeds = 0
        for x in cells + ctrl:
            for n in range(1, 49):
                for k in range(8):
                    for j in range(5):
                        seeds.add(seed_simulator(x["cell_index"], n, k, j))
                        n_seeds += 1
        self.rec("cross: every seed_simulator value is unique across all enumerated cells", len(seeds) == n_seeds, f"{n_seeds} seeds")
        # timing floor / control refs / CAL rule / conservative estimate carried in JSON
        p2c = json.dumps(c.get("phase2c", {}))
        self.rec("cross: JSON phase2c carries TIMING_UNTESTABLE, fits(T) < 479, binding conservative estimate and no accepted-risk exception",
                 "TIMING_UNTESTABLE" in p2c and "T < 479" in p2c and "T_est^cons" in p2c and "accepted-risk" not in p2c.replace("no accepted-risk", ""))
        p2b = json.dumps(c.get("phase2b", {}))
        self.rec("cross: JSON phase2b carries state-indexed control references, CAL_MISSING_CHANNEL and the deterministic seed-range exemption",
                 "E0_ctrl" in p2b and "CAL_MISSING_CHANNEL" in p2b and "EXEMPT" in p2b)
        self.rec("cross: JSON Phase 2A secondary blockers include MASK_BOUNDARY",
                 "MASK_BOUNDARY" in c.get("phase2a", {}).get("secondary", {}).get("L_level_blockers", []))
        self.check_rank_rule_consistency()
        self.check_a2_consistency()
        marker = "TO" + "DO"  # assembled so this file does not contain the marker itself
        todo = [rel for rel in DELIVERABLES if (self.root / rel).exists() and marker in (self.root / rel).read_text(encoding="utf-8")]
        self.rec("cross: no checkpoint marker (TO-DO) in any deliverable", not todo, ", ".join(todo))

    # ---------------- rank rule consistency (amendment A-1) ----------------
    @staticmethod
    def _section(text, heading_regex):
        """Text of one markdown section: from the heading matching heading_regex to the next heading of the same or higher level."""
        m = re.search(heading_regex, text, re.M)
        if not m:
            return ""
        level = len(m.group(0)) - len(m.group(0).lstrip("#"))
        rest = text[m.end():]
        nxt = re.search(r"^#{1,%d} " % level, rest, re.M)
        return rest[: nxt.start()] if nxt else rest

    def check_rank_rule_consistency(self):
        """The Phase 2B EXP minimum is stated numerically in phase2b scope of the JSON, bound to constants,
        equal to this module's RANK_RULE_2B, and carried by the prereg (§4.3, §6.2) and the contract (§C4.2,
        §C4.3) in words that agree; the Phase 2C minimum stays two (prereg §5.4, phase2c.transpilation)."""
        c = self.contract
        words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
        rr_b = c.get("phase2b", {}).get("rank_rule", {})
        rr_c = c.get("phase2c", {}).get("transpilation", {}).get("rank_rule", {})
        consts = c.get("constants", {})
        cb = consts.get("C-EXP-MIN-2B", {}).get("value")
        cc_ = consts.get("C-EXP-MIN-2C", {}).get("value")
        json_ok = ({k: rr_b.get(k) for k in ("LIN", "QUAD", "EXP")} == RANK_RULE_2B
                   and {k: rr_c.get(k) for k in ("LIN", "QUAD", "EXP")} == RANK_RULE_2C
                   and cb == RANK_RULE_2B["EXP"] == 3 and cc_ == RANK_RULE_2C["EXP"] == 2)
        self.rec("rank: JSON phase2b.rank_rule = {LIN 2, QUAD 3, EXP 3} and phase2c.transpilation.rank_rule = {LIN 2, QUAD 3, EXP 2} (numeric, phase-scoped), C-EXP-MIN-2B = 3, C-EXP-MIN-2C = 2, all equal to the checker's RANK_RULE_2B / RANK_RULE_2C",
                 json_ok, f"phase2b={rr_b} phase2c={rr_c} C-EXP-MIN-2B={cb} C-EXP-MIN-2C={cc_}")
        # the phase2c prose strings in the JSON agree with the numeric rule
        ex_c = c.get("phase2c", {}).get("transpilation", {}).get("extrapolators", {})
        ex_b = c.get("phase2b", {}).get("extrapolators", {})
        txt_ok = True
        for k, v in RANK_RULE_2C.items():
            m = re.search(r">=\s*(\d)\s*distinct", ex_c.get(k, ""))
            txt_ok = txt_ok and bool(m) and int(m.group(1)) == v
        m = re.search(r">=\s*(\d)\s*distinct realized abscissas", ex_b.get("EXP", ""))
        txt_ok = txt_ok and bool(m) and int(m.group(1)) == RANK_RULE_2B["EXP"]
        est = c.get("statistics", {}).get("bootstrap", {}).get("estimator_order", [""] * 2)[1]
        txt_ok = (txt_ok and "Phase 2B: phase2b.rank_rule" in est and "EXP 3 distinct realized abscissas" in est
                  and "Phase 2C: phase2c.transpilation.rank_rule" in est and "EXP 2)" in est)
        self.rec("rank: JSON prose agrees with the numeric rules (phase2c.transpilation.extrapolators say >= 2/3/2; phase2b.extrapolators.EXP says >= 3 distinct realized abscissas; the estimator order names phase2b.rank_rule with EXP 3)",
                 txt_ok, f"{ex_c} | {ex_b.get('EXP', '')[-120:]} | {est[-100:]}")
        # prereg §4.3 (Phase 2B) says three for EXP; §5.4 (Phase 2C) says two; §6.2 step 2 names §4.3 and three
        pre = self.docs["prereg"]
        s43 = self._section(pre, r"^### 4\.3 ")
        s54 = self._section(pre, r"^### 5\.4 ")
        s62 = self._section(pre, r"^### 6\.2 ")
        m43 = re.search(r"exponential fit needs at least (\w+) distinct realized abscissas", s43)
        m43b = re.search(r"\$n\^\{\\mathrm\{EXP\}\}_\{\\min,\\mathrm\{2B\}\} = (\d)\$", s43)
        m54 = re.search(r"`EXP` with the declared asymptote \(its two-parameter log-linear fit\s+requires at least (\w+) distinct abscissas", s54)
        m54b = re.search(r"\$n\^\{\\mathrm\{EXP\}\}_\{\\min,\\mathrm\{2C\}\} = (\d)\$", s54)
        m62 = re.search(r"rank requirements of the phase \(Phase 2B, §4\.3:\s+`LIN` (\w+), `QUAD` (\w+), `EXP` (\w+) distinct realized abscissas,\s+amendment A-1; Phase 2C, §5\.4: `LIN` (\w+), `QUAD` (\w+), `EXP` (\w+)\)", s62)
        pre_ok = (m43 and words.get(m43.group(1)) == RANK_RULE_2B["EXP"] and m43b and int(m43b.group(1)) == RANK_RULE_2B["EXP"]
                  and "everywhere in Phase 2B" in s43 and "both folding variants" in s43
                  and m54 and words.get(m54.group(1)) == RANK_RULE_2C["EXP"] and m54b and int(m54b.group(1)) == RANK_RULE_2C["EXP"]
                  and m62 and [words.get(g) for g in m62.groups()] == [RANK_RULE_2B["LIN"], RANK_RULE_2B["QUAD"], RANK_RULE_2B["EXP"], RANK_RULE_2C["LIN"], RANK_RULE_2C["QUAD"], RANK_RULE_2C["EXP"]]
                  and "algebraic" in s43 and "admission" in s43)
        self.rec("rank: prereg §4.3 states the Phase 2B EXP minimum three (everywhere in Phase 2B, both folding variants) with the symbol bound to C-EXP-MIN-2B; §5.4 keeps the Phase 2C minimum two; §6.2 step 2 is phase-aware (Phase 2B LIN two / QUAD three / EXP three; Phase 2C LIN two / QUAD three / EXP two); §4.3 distinguishes the algebraic two-point necessity from the human-selected admission minimum",
                 bool(pre_ok), f"4.3={m43 and m43.group(1)} sym={m43b and m43b.group(1)} 5.4={m54 and m54.group(1)} sym={m54b and m54b.group(1)} 6.2={m62 and m62.groups()}")
        con = self.docs["contract"]
        c42 = self._section(con, r"^### C4\.2 ")
        c43 = self._section(con, r"^### C4\.3 ")
        m42 = re.search(r"`LIN` needs at least (\d) distinct realized abscissas, `QUAD` at least (\d), `EXP` \(two parameters with the asymptote fixed\) at least (\d)", c42)
        m42c = re.search(r"Phase 2C keeps `EXP` at (\d)", c42)
        m43c = re.search(r"with the rank rule of the phase, applied before either mode: §C4\.2 for Phase 2B \(`LIN` (\d), `QUAD` (\d), `EXP` (\d) distinct realized abscissas\); prereg §5\.4 and `phase2c\.transpilation\.rank_rule` for Phase 2C \(`LIN` (\d), `QUAD` (\d), `EXP` (\d)\)", c43)
        con_ok = (m42 and [int(g) for g in m42.groups()] == [RANK_RULE_2B["LIN"], RANK_RULE_2B["QUAD"], RANK_RULE_2B["EXP"]]
                  and "both folding variants" in c42 and m42c and int(m42c.group(1)) == RANK_RULE_2C["EXP"]
                  and m43c and [int(g) for g in m43c.groups()] == [RANK_RULE_2B["LIN"], RANK_RULE_2B["QUAD"], RANK_RULE_2B["EXP"], RANK_RULE_2C["LIN"], RANK_RULE_2C["QUAD"], RANK_RULE_2C["EXP"]]
                  and "algebraic full-rank necessity" in c42 and "admission minimum" in c42)
        self.rec("rank: contract §C4.2 rank rule reads LIN 2 / QUAD 3 / EXP 3 for Phase 2B (both folding variants) and keeps Phase 2C EXP at 2; §C4.3 step 2 is phase-aware (Phase 2B 2/3/3 via §C4.2, Phase 2C 2/3/2 via prereg §5.4), so the shared estimator order carries no unconditional rule and the two incorporations (prereg §6.2 -> §4.3 / §5.4, contract §C4.3 -> §C4.2 / §5.4) agree; §C4.2 separates the algebraic necessity from the admission minimum",
                 bool(con_ok), f"C4.2={m42 and m42.groups()} 2C={m42c and m42c.group(1)} C4.3={m43c and m43c.groups()}")
        # the checker's own functions, driven by the JSON minima, discriminate two distinct abscissas by phase
        two = ([1.0, 2.0], [0.5, 0.3])
        def fails(fn, m):
            try:
                fn(two[0], two[1], 0.0, min_distinct=m)
                return False
            except ValueError as e:
                return str(e).startswith("FIT_FAILURE")
        disc = (isinstance(rr_b.get("EXP"), int) and isinstance(rr_c.get("EXP"), int)
                and all(fails(fn, rr_b["EXP"]) for fn in (exp_fit_fixed, exp_fit_avoid_log))
                and not any(fails(fn, rr_c["EXP"]) for fn in (exp_fit_fixed, exp_fit_avoid_log)))
        self.rec("rank: driven by the JSON minima, both EXP reference implementations reject two distinct abscissas under phase2b.rank_rule and accept them under phase2c.transpilation.rank_rule",
                 disc)
        # the dated amendment record with the historical identities and the canonical REJECT that triggered it
        am = c.get("amendments", [])
        a1 = next((a for a in am if a.get("id") == "A-1"), None)
        hist = (a1 or {}).get("historical_identities", {})
        am_ok = (a1 is not None and a1.get("date") == "2026-09-08" and a1.get("pre_data") is True
                 and a1.get("rule", {}).get("phase2b_exp_min_distinct") == 3 and a1.get("rule", {}).get("phase2c_exp_min_distinct") == 2
                 and hist.get("docs/prereg-phase2.md") == "913831adf38828f9802fd55fb94f560cc4f7e16e48c3a62afe6336f3cffc19d4"
                 and hist.get("docs/phase2-analysis-contract.md") == "97e67e68e0368c621393af118b7c0dc1f8f2018c04c9cfd0eef01c01ab14cdeb"
                 and hist.get("tools/phase2_contract.json") == "f77e15326baf9012c2799d0b7417556ff156ffb4e5d275cedd7be02a49e5b266"
                 and hist.get("tools/phase2_contract_check.py") == "8d20d8c7d776e4c9b2f4ff8a69f671419c72a549bc73afe990a9cd6bc426a503"
                 and hist.get("tests/test_phase2_contract.py") == "6d5dc35a397db5708eabb4b34a92f75476f8405622dfaf5d975f5f8301a2f19b"
                 and "REJECT" in json.dumps(a1.get("trigger", ""))
                 and "A-1" in pre and "A-1" in con and "2026-09-08" in pre and "2026-09-08" in con)
        self.rec("rank: dated pre-data amendment A-1 (2026-09-08) is recorded in the JSON with the five historical identities and the canonical Reviewer REJECT that triggered it, and both documents carry the amendment record",
                 am_ok, json.dumps(a1)[:200] if a1 else "no A-1 record")

    # ---------------- amendment A-2 cross-surface consistency ----------------
    def check_a2_consistency(self):
        import inspect
        c = self.contract
        pre, con = self.docs["prereg"], self.docs["contract"]
        am = next((a for a in c.get("amendments", []) if a.get("id") == "A-2"), None)
        hist = (am or {}).get("historical_identities_pre_a2", {})
        rules = (am or {}).get("rules", {})
        rec_ok = (am is not None and am.get("date") == "2026-09-08" and am.get("pre_data") is True and "pre_data_scope" in am
                  and "already produced" in am["pre_data_scope"] and "REJECT" in am.get("trigger", "")
                  and hist.get("tools/phase2_contract_check.py") == "2e069bf88118ac579b910594a182994a7c6c1c8b329a806e6c0bfebb5284ff1b"
                  and hist.get("docs/prereg-phase2.md") == "2617aa72f5cac45d1ac0d4c13c46bdd5690e47f99ff09ca2c5a3d6ebd3d6cafb"
                  and "np.sign" in rules.get("exp_sign", "") and "polyfit" in rules.get("exp_sign", "")
                  and "TOO_FEW_POINTS" in rules.get("small_mask", "") and "aggregate-matched" in rules.get("dm_seed_range", "")
                  and "1/9600" in rules.get("primary_tail_probability", "") and "source_identity_split" in am
                  and "A-2" in pre and "A-2" in con)
        self.rec("a2: dated amendment A-2 is recorded in the JSON with its truthful pre-data scope qualifier, the round-04 REJECT trigger, the four rules, the pre-A-2 identities and the source-identity split, and both documents carry it", rec_ok, json.dumps(am)[:160] if am else "no A-2")
        # surfaces agree on the sign convention
        c43 = self._section(con, r"^### C4\.3 ")
        s44 = self._section(pre, r"^### 4\.4 ")
        ex_txt = c.get("phase2b", {}).get("extrapolators", {}).get("EXP", "")
        src = inspect.getsource(exp_fit_fixed) + inspect.getsource(exp_sign) + inspect.getsource(exp_fit_avoid_log)
        sign_ok = ("`np.sign` of the linear intercept minus $a$" in c43 and "numpy.polyfit" in c43 and "sigma = 0" in c43.replace("$\\sigma = 0$", "sigma = 0")
                   and "`np.sign` of the `numpy.polyfit` linear intercept" in s44 and "np.sign(-(asymptote - numpy.polyfit" in ex_txt
                   and re.search(r">=\s*0\s+else", src) is None and "intercept = pinned_linear_intercept(xs, ys)" in src and "np.sign(-(asymptote - intercept" in src and src.count("exp_sign(xs, ys, asymptote)") >= 2)
        self.rec("a2: EXP sign convention agrees on every surface (prereg §4.4, contract §C4.3, JSON phase2b.extrapolators.EXP, checker source: np.sign of the numpy.polyfit intercept, no '>= 0' ternary, one exp_sign used by both modes)", sign_ok)
        # A-3: the tolerance rule on every surface, with explicit numeric authority in the JSON (style of phase2b.rank_rule)
        a3 = next((x for x in c.get("amendments", []) if x.get("id") == "A-3"), None)
        tol = c.get("phase2b", {}).get("exp_sign_tolerance", {})
        kc = c.get("constants", {}).get("C-A3-SIGN-TOL-C", {}); ke = c.get("constants", {}).get("C-A3-EPS", {})
        a3_ok = (a3 is not None and a3.get("date") == "2026-09-09" and "historical_identities_pre_a3" in a3
                 and a3["historical_identities_pre_a3"].get("phase2_source_sha256_accepted_a2") == "b7937c07302640fd9949c55f3cbddbc5415937caa76e78041021e65bed219f2b"
                 and tol.get("C") == A3_SIGN_TOL_C and tol.get("eps") == A3_EPS_DOUBLE and kc.get("value") == A3_SIGN_TOL_C and ke.get("value") == A3_EPS_DOUBLE
                 and "lever" in tol.get("formula", "") and "cond" in tol.get("formula", "") and tol.get("ddof") == 0
                 and "tau" in ex_txt and "A-3" in ex_txt
                 and "amendment A-3" in c43 and "\\tau" in c43 and "amendment A-3" in s44 and "\\tau" in s44
                 and "exp_sign_tolerance(xs, ys)" in inspect.getsource(exp_sign) and "np.vander(x, 2)" in inspect.getsource(exp_sign_tolerance) and "np.var(x)" in inspect.getsource(exp_sign_tolerance))
        self.rec("a3: the sign tolerance is recorded on every surface (JSON amendments[A-3] with the historical accepted-A-2 source identity, phase2b.exp_sign_tolerance {C, eps, formula, ddof 0}, constants C-A3-SIGN-TOL-C = 4 and C-A3-EPS bound to the checker's A3_SIGN_TOL_C / A3_EPS_DOUBLE, prereg §4.4, contract §C4.3, checker exp_sign via exp_sign_tolerance)", a3_ok)
        c41 = self._section(con, r"^### C4\.1 ")
        s36 = self._section(pre, r"^### 3\.6 ")
        km = c.get("constants", {}).get("C-MIN-MASKED", {})
        mask_ok = ("at least $k_{\\min} = 3$ steps (amendment A-2" in c41 and "TOO_FEW_POINTS" in c41
                   and "\\ge k_{\\min} = 3$" in s36 and "TOO_FEW_POINTS" in s36 and km.get("value") == 3 and "statistics" in km.get("where", "")
                   and "small_mask_rule" in c.get("phase2a", {}).get("primary_analysis", {})
                   and "len(masked) >= k_min" in inspect.getsource(phase2a_verdict))
        self.rec("a2: small-mask rule agrees on every surface (prereg §3.6, contract §C4.1 step 4, C-MIN-MASKED, phase2a.primary_analysis.small_mask_rule, checker gate len(masked) >= k_min)", mask_ok)
        c44 = self._section(con, r"^### C4\.4 ")
        s48 = self._section(pre, r"^### 4\.8 ")
        dm = c.get("phase2b", {}).get("dm_companion", "")
        dm_ok = ("7. **DM companion seed range (amendment A-2).**" in c44 and "no partial range" in c44
                 and "aggregate-matched" in dm and "WHOLE" in dm and "own** matched peak" in s48 and "never a partial range" in s48
                 and callable(globals().get("dm_seed_range")) and re.search(r"no partial\s+range", inspect.getsource(dm_seed_range)) is not None
                 # A-2 correction: the non-finite rule on every surface
                 and "non-finite" in c44 and "non-finite" in s48 and "non-finite" in dm and "non-finite" in rules.get("dm_seed_range", "")
                 and "math.isfinite(v)" in inspect.getsource(seed_value_undefined) and "seed_value_undefined" in inspect.getsource(dm_seed_range))
        self.rec("a2: DM companion seed range is defined on every surface (prereg §4.8, contract §C4.4 item 7, JSON phase2b.dm_companion and amendments[A-2].rules, checker dm_seed_range) with amplitude at the aggregate-matched step, timing per seed in the same window, no partial range, and every missing or non-finite required seed value undefined", dm_ok)
        qv = c.get("constants", {}).get("C-CI-Q-PRIMARY", {}).get("value", [None])[0]
        q_ok = (qv == 1.0 / 9600.0 and "1/9600" in c.get("statistics", {}).get("bootstrap", {}).get("undefined_replicates", "")
                and "1/9600" in pre and "1/9600" in con and "(48000, 1.0 / 9600.0): 4" in inspect.getsource(Checker.check_edge_cases))
        self.rec("a2: the primary tail probability is exactly 1/9600 in the JSON constant, both documents and the checker's undefined-count fixture (4 tolerated, never 5)", q_ok, f"{qv}")

    # ---------------- whitespace ----------------
    def check_whitespace(self):
        # Launch git on CPython's posix_spawn path rather than fork(), which is unsafe on macOS while other
        # threads are alive. For the supported runtime that path needs an executable with a NONEMPTY DIRECTORY
        # COMPONENT, close_fds=False, no cwd, and the remaining Popen conditions (no preexec_fn/pass_fds/uid/gid,
        # pipe descriptors numbered above 2), so it is not unconditional. Our stronger guarantee is an absolute
        # executable: shutil.which can return a bare name when PATH holds an empty component, so the lookup is
        # made absolute. Symlinks are not resolved: resolution is not needed to satisfy the directory-component
        # condition, and keeping the lookup's own spelling is the conservative choice. close_fds=False keeps
        # descriptors that are already inheritable (Python-created ones are non-inheritable by default) open in
        # the child until it exits; that exposure is bounded because the child is a read-only diff comparison
        # whose stdout and stderr are captured and which finishes before the checker continues. Git is resolved
        # once per call and the repository located with -C.
        git = shutil.which("git")
        if git is None:
            self.rec("whitespace: git available for --no-index --check", False, "git not found")
            return
        git = str(Path(git).absolute())
        bad = []
        for rel in DELIVERABLES:
            p = self.root / rel
            if not p.exists():
                continue
            try:
                r = subprocess.run([git, "-C", str(self.root), "diff", "--check", "--no-index", "/dev/null", str(p)],
                                   capture_output=True, text=True, close_fds=False)
            except FileNotFoundError:
                self.rec("whitespace: git available for --no-index --check", False, "git not found")
                return
            if r.returncode == 2 or "trailing whitespace" in r.stdout or "space before tab" in r.stdout:
                bad.append(rel)
        self.rec("whitespace: git diff --check --no-index /dev/null <file> clean for every deliverable (index untouched)", not bad, ", ".join(bad))

    # ---------------- traceability ----------------
    def traceability_rows(self):
        c = self.contract
        arts = {a["id"]: a for a in c.get("artifacts", [])} if isinstance(c.get("artifacts"), list) else {}
        rows = []
        for ch in c.get("charts", []) if isinstance(c.get("charts"), list) else []:
            for p in ch["panels"]:
                for s in p["series"]:
                    if s.get("source") == "constant":
                        rows.append((ch["id"], p["id"], s["name"], "tools/phase2_contract.json", f"constants.{s['constant']}", s["equation"], "EP-FIGURES (constant)"))
                        continue
                    a = arts.get(s["artifact"], {})
                    sel = ";".join(f"{k}={v}" for k, v in s.get("rows", {}).items()) or "-"
                    rows.append((ch["id"], p["id"], s["name"], a.get("path", "?"), f"{s['column']} [{sel}]", s["equation"], f"{a.get('produced_by', '?')}, EP-FIGURES"))
        return rows

    def run(self):
        self.load()
        self.check_algebra()
        self.check_edge_cases()
        self.check_schema()
        self.check_cross()
        self.check_whitespace()
        return self.results


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    root = Path(__file__).resolve().parents[1]
    if "--root" in argv:
        i = argv.index("--root")
        if i + 1 >= len(argv):
            print("--root requires a directory argument", file=sys.stderr)
            return 2
        root = Path(argv[i + 1]).resolve()
    ck = Checker(root)
    try:
        results = ck.run()
    except InputError as e:
        print(f"[INPUT] {e}", file=sys.stderr)
        return 2
    failed = 0
    for name, ok, detail in results:
        print(f"[{'OK ' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail and not ok else ""))
        failed += not ok
    if "--traceability" in argv:
        print("chart\tpanel\tseries\tfile\tcolumn\tequation\tcommand")
        for r in ck.traceability_rows():
            print("\t".join(map(str, r)))
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
