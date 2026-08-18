"""Pre-registered comparison metrics (design.md §13).

eps_u(n) = |E_noisy(n) - E_0(n)|, eps_m(n) = |E_ZNE(n) - E_0(n)|,
IF(n) = eps_u/eps_m with the baseline-relevance filter (eps_u >= EPS_MIN, a
numerator-only relevance criterion) and the delta denominator rule; RMS and
GIF always over all steps; ddof=1 bands; the m=0 majority edge case is vacuous
and flagged, never an exception. Per §13, no function here may raise on, or
return, a non-finite value for in-range inputs.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

EPS_MIN = 0.01  # baseline-relevance filter threshold (design §13)
DELTA_DENSITY_MATRIX = 1e-9  # denominator rule, deterministic pipeline (design §13)
DELTA_SHOT = 1e-3  # denominator rule, shot pipeline (design §13)


def abs_error(estimate: float, reference: float) -> float:
    return abs(estimate - reference)


def is_reportable(eps_u: float) -> bool:
    """Baseline-relevance filter: step enters the IF majority test iff eps_u >= EPS_MIN.
    This constrains the NUMERATOR only (relevance), not the denominator (§13)."""
    return eps_u >= EPS_MIN


@dataclass(frozen=True)
class ImprovementFactor:
    value: float
    is_lower_bound: bool  # True when the denominator hit delta: value is a flagged lower bound

    @property
    def exceeds_one(self) -> bool:
        return self.value > 1.0


def improvement_factor(eps_u: float, eps_m: float, delta: float) -> ImprovementFactor:
    """IF(n) with the pre-registered denominator rule (§13): if eps_m <= delta
    (including exactly zero), report the flagged lower bound eps_u/delta instead
    of a point value. Never raises, never returns a non-finite number."""
    if delta <= 0:
        raise ValueError("delta must be positive")
    if eps_m <= delta:
        return ImprovementFactor(value=eps_u / delta, is_lower_bound=True)
    return ImprovementFactor(value=eps_u / eps_m, is_lower_bound=False)


def rms(errors: Sequence[float]) -> float:
    """Root-mean-square over ALL provided steps (the filter never touches this)."""
    arr = np.asarray(errors, dtype=float)
    return float(np.sqrt(np.mean(arr**2)))


def global_improvement_factor(
    rms_u: float, rms_m: float, delta: float
) -> ImprovementFactor:
    """GIF = RMS_u / RMS_m with the same delta denominator rule as IF (§13:
    'no non-finite value ever enters any table or aggregate')."""
    return improvement_factor(rms_u, rms_m, delta)


@dataclass(frozen=True)
class MajorityOutcome:
    reportable_steps: int  # m
    wins: int  # steps with IF > 1
    passes: bool | None  # None when m == 0: clause is vacuous (§13 edge case)

    @property
    def is_vacuous(self) -> bool:
        return self.reportable_steps == 0


def majority_outcome(
    improvement_factors: Sequence[ImprovementFactor],
) -> MajorityOutcome:
    """Strict-majority test over the reportable steps: passes iff wins > m/2
    (odd m has no tie; an exact tie at even m fails). m == 0 yields the vacuous
    outcome (passes=None) — never an exception (§13)."""
    m = len(improvement_factors)
    wins = sum(1 for f in improvement_factors if f.exceeds_one)
    if m == 0:
        return MajorityOutcome(reportable_steps=0, wins=0, passes=None)
    return MajorityOutcome(reportable_steps=m, wins=wins, passes=wins > m / 2)


@dataclass(frozen=True)
class Verdict:
    passes: bool
    gif: ImprovementFactor
    majority: MajorityOutcome
    m_zero_flagged: bool  # True when the majority clause was vacuous (§13: flag prominently)


def experiment_verdict(
    gif: ImprovementFactor, majority: MajorityOutcome
) -> Verdict:
    """§13 pass/fail: GIF > 1 AND strict majority of reportable steps with IF > 1.
    When m == 0 the majority clause is vacuous: the verdict rests on GIF alone,
    flagged."""
    if majority.is_vacuous:
        return Verdict(
            passes=gif.exceeds_one, gif=gif, majority=majority, m_zero_flagged=True
        )
    return Verdict(
        passes=gif.exceeds_one and bool(majority.passes),
        gif=gif,
        majority=majority,
        m_zero_flagged=False,
    )


def seed_band(values: Sequence[float]) -> tuple[float, float, float]:
    """(mean, ddof=1 standard deviation, standard error) over the seed ensemble
    (design §13). Requires at least two values."""
    arr = np.asarray(values, dtype=float)
    if arr.size < 2:
        raise ValueError("need >= 2 seed values for a ddof=1 band")
    std = float(np.std(arr, ddof=1))
    return float(np.mean(arr)), std, std / float(np.sqrt(arr.size))


def shot_baseline(lambda_one_values: Sequence[float]) -> tuple[float, float]:
    """Shot-pipeline unmitigated baseline (§13): the mean of the independently
    seeded lambda=1 executions, with its ddof=1 standard deviation."""
    mean, std, _ = seed_band(lambda_one_values)
    return mean, std
