# Phase 2 Planning Notes: Charts and Analysis

> **Current status, 2026-09-08 (supersedes the two dated updates below).** The corrected A-2 candidate was accepted
> (independent review round 06; accepted `phase2` source identity `b7937c07302640fd9949c55f3cbddbc5415937caa76e78041021e65bed219f2b`,
> now historical: amendment A-3 of 2026-09-09 made the `EXP` sign's zero branch reachable, source identity `cb08ee1821d05646...`).
> The Phase 2 framework (preregistration, contract, checker, estimators, tests) is implemented. Phase 2 science has NOT been
> run: no contracted result exists, feasibility is unassessed, and a quarantined pilot acquisition (17 of 162 work units,
> stopped, values unused) did execute the Aer simulator and produce raw records. The dated updates below are kept as written.
>
> **Update, 2026-09-08 (A-1). HISTORICAL: written before A-2 and the pilot acquisition; "now" and "still" in this paragraph refer to that date and are superseded by the current status above; original wording kept.** Amendment A-1 (human-approved, pre-data) fixed the Phase 2B
> `EXP` rank minimum at three distinct realized abscissas (`docs/prereg-phase2.md` §4.3); Phase 2C
> keeps two. An offline Phase 2 environment and unexecuted scaffolding now exist; there is still
> no Phase 2 data, figure or result. The note below is historical as dated.
>
> **Update, 2026-09-08 (A-2). HISTORICAL: written before the A-2 correction was accepted; superseded by the current status above; original wording kept.** A second human-approved amendment fixed the `EXP` sign
> convention, the small-mask Phase 2A rule and the DM companion seed range (`docs/prereg-phase2.md`
> header; `tools/phase2_contract.json` `amendments`). Unaffected Aer probes and a quarantined pilot
> acquisition exist; still no contracted Phase 2 result.
>
> **Supersession, 2026-09-07.** Phase 2 is now preregistered in
> `docs/prereg-phase2.md`, with its recomputable analysis and output
> contract in `docs/phase2-analysis-contract.md` and its machine-readable
> companion `tools/phase2_contract.json`. Phase 2 remains **unexecuted**:
> no Phase 2 code, data, figure, simulator result or hardware result exists.
>
> What that preregistration supersedes in this document:
>
> - the Tier B planned commands R-B1 and R-B2 and the charts FC-5 and FC-6
>   that depend on them (§3, §5), and the quantities Q8 and the prospective
>   single-rate role of Q7 (§4);
> - the six open decisions of §6 (hypothesis intervals, residual tolerance,
>   the $10^{-9}$ rules' role, the additivity criterion, the mask threshold,
>   and the heuristic floor arithmetic as a Phase 2 objective).
>
> The current design differs from the framing here in two ways a reader must
> not miss. First, the primary Phase 2A analysis is the curve-level
> interaction $I(n) = A_{11} - A_{10} - A_{01} + A_{00}$ with declared
> material equivalence margins; the single-rate slopes $g_{ij}$ and
> $\Delta = g_{12} - (g_1 + g_2)$ are secondary, with their adequacy limits
> stated. Second, the new preregistration **reruns all four factorial cells
> prospectively** under one Phase 2 implementation and environment; the
> v0.1.0 combined arm is used **only as a historical cross-check**, never as
> a factorial cell, so the "two of the four cells already exist" framing of
> FC-6 no longer applies.
>
> What remains valid and unchanged: the Tier A recomputations of the
> recorded v0.1.0 data (FC-1 to FC-4, Q1 to Q7 as a post-hoc diagnostic, and
> commands R-1 to R-7), which read only `results/minimal/` and produce no new
> result. This document is otherwise a historical record. Apart from the
> duplicated clause in the FC-6 plot-type bullet, which was removed on
> 2026-09-07 so the sentence reads once, its body text is unchanged.

> As of 2026-09-06, work on Phase 2 has not started. This document lays out
> possible work; it is not a preregistration or an approved study. The
> $p_2 = 0$, $p_1 = 0$, and factorial experiments have not been written or
> run, so no data exist for them.
>
> The Tier A commands in §5 were tested against the v0.1.0 data. They only
> read existing files and did not produce new scientific results.
>
> Before running Phase 2, this document must be expanded into a
> preregistration like `docs/design.md` and reviewed. That preregistration
> must set the intervals, mask, and tolerances listed in §6.
>
> The v0.1.0 result remains unchanged. It comes from the metrics in
> design.md §13 and the recorded data, with the limitations reported in
> `docs/results-minimal.md`. Phase 2 requires explicit approval before any
> code is written or any experiment is run.

## 0. What this document covers

This document describes six possible charts. For each chart it names the
source files and columns, defines the calculations, lists the assumptions
that can be checked, and explains how to handle cases in which a calculation
is undefined. Section 5 provides commands for calculations that can be run
with the existing data. Section 7 maps each chart and quantity to its data,
formula, design reference, and command.

This work does not address hardware (design.md §14(d)), change any v0.1.0
definition or result, or settle the open questions in §6. It also does not
investigate the cross-platform reproduction failure recorded in
`docs/ci-reproduction-assessment.md` on 2026-09-06.

Any result quoted here already appears in `results/minimal/metrics.json`,
`docs/results-minimal.md`, or `docs/release-notes-v0.1.0.md`. Other
quantities are presented as formulas with commands that calculate them. The
row counts, column names, and seed counts were checked on 2026-09-06.

## 1. The two tiers

| Tier | Available data | How it may be used |
|---|---|---|
| **A: can be calculated now** | The required inputs are in the v0.1.0 data: `results/minimal/steps.csv`, `metrics.json`, `folded_circuits.csv`, `seed_arms.csv`, `shot_values.csv`, and `environment.json`. | These are post-hoc checks of recorded data, like the labeled oracle calculations in `docs/results-minimal.md` §9. They do not change the preregistered result. |
| **B: requires new experiments** | These calculations need the $p_2 = 0$ control arm $(p_1, p_2) = (10^{-3}, 0)$, the $p_1 = 0$ control arm $(0, 10^{-2})$, or both. | The commands are plans only. The required data do not exist, and this document does not predict the results. |

Each item below carries its tier in its heading.

## 2. Available data (checked 2026-09-06)

All under `results/minimal/`. Row counts exclude the header line. Column
names are exactly as they appear in the CSV headers.

| File | Rows | Exact header |
|---|---|---|
| `steps.csv` | 40 (one per Trotter step $n = 1..40$) | `n, ed_reference, e0_trotter, e_noisy_dm, zne_primary_mean, zne_primary_std, zne_nominal_mean, zne_nominal_std, zne_effective_mean, zne_effective_std, secondary_estimate, secondary_mode, secondary_std, eps_u, eps_m, eps_m_band, if_value, if_is_lower_bound, reportable, shot_baseline_mean, shot_baseline_std, shot_primary_mean, shot_primary_std, shot_primary_sem, shot_nominal_mean, shot_nominal_std, shot_effective_mean, shot_effective_std, shot_secondary_estimate, shot_secondary_mode, shot_secondary_std, shot_eps_u, shot_eps_m, shot_eps_m_band, shot_if_value, shot_if_is_lower_bound, shot_reportable` |
| `folded_circuits.csv` | 960 (40 steps × 8 fold seeds × 3 nominal scale factors) | `n, fold_seed, lambda_nominal, lambda_r, lambda_eff, expectation_dm, cx, sx, x, rz, sxdg` |
| `shot_values.csv` | 960 | `n, fold_seed, lambda_nominal, expectation_shot, seed_simulator` |
| `seed_arms.csv` | 320 (40 steps × 8 fold seeds) | `n, fold_seed, primary_intercept, nominal_intercept, effective_intercept, clamp_flag, secondary_log, secondary_avoid_log, secondary_avoid_log_failed, shot_clamp_flag, shot_secondary_log, shot_secondary_avoid_log, shot_secondary_avoid_log_failed` |
| `metrics.json` | - | top-level keys `gif_value, rms_u, rms_m, if_wins, reportable_steps_m, excluded_steps, majority_passes, verdict_passes, gif_is_lower_bound, m_zero_flagged, primary_pipeline`, and the same metric keys (plus `note`) under `shot_pipeline` |
| `environment.json` | - | keys `design_section, parameters, platform, source_identifier_note, source_tree_sha256, versions`; the rates used below are `parameters.noise.p1`, `parameters.noise.p2`, with gate classes `parameters.noise.one_qubit_gates`, `parameters.noise.two_qubit_gates`, `parameters.noise.clean_gates` |

Flag and mode columns are integer 0/1 (`reportable`, `if_is_lower_bound`,
`clamp_flag`, `secondary_avoid_log_failed`, and their `shot_` counterparts) or
strings (`secondary_mode`, `shot_secondary_mode` ∈ {`log`, `avoid_log`,
`avoid_log_failed`}). An `avoid_log_failed` step has an empty
`shot_secondary_estimate` cell by the recorded policy (design.md §20 M3-3;
`docs/results-minimal.md` §6 lists which steps).

## 3. Proposed charts

Conventions for every chart. The x-axis is the Trotter step $n$
(dimensionless; $Vt = n$ with $V = 1$, $\Delta t = 1$ per design.md §15).
Every observable-valued quantity is the staggered-magnetization density
$\langle Z_\pi\rangle/L$, dimensionless in $[-1, 1]$. Every chart shows all
40 steps, and masks are drawn as marker styles rather than by omission, so
that excluded steps stay visible (design.md §13).

Every band is the `ddof=1` sample standard deviation across the 8 fold seeds
(design.md §13 uncertainty bullet), and the legend must say which of two
different spreads it is:

- In the density-matrix pipeline the eight values differ only by the seeded
  folding configuration, because the pipeline is exact and sampling-free, so
  the band is folding-configuration spread and not statistical error
  (`docs/results-minimal.md` §6).
- In the shot pipeline the eight members differ in both the folding
  configuration and independent 8192-shot sampling, with a distinct
  `seed_simulator` per executed circuit (design.md §16). The eight recorded
  $n = 1$, `lambda_nominal == 1.0` shot expectations are all distinct
  although the unfolded circuit is identical. A shot SD therefore includes
  sampling variation, and the shot SEM $s_n/\sqrt{8}$ (§13) is the standard
  error of that eight-member mean.

Neither band is a confidence interval: no sampling distribution is modeled,
no coverage probability is claimed, and "no significance test is performed
or implied" (design.md §13, denominator bullet). Legends must say
"seed-spread SD" or "SEM", never "95%" or "uncertainty" without
qualification.

### FC-1 - Per-step improvement factor with the pre-registered mask (Tier A)

- **Plot type:** points joined by a thin line, one panel per pipeline
  (density-matrix primary; shot pipeline).
- **x:** `n` (steps, linear). **y:** $\mathrm{IF}(n)$ (dimensionless ratio,
  log scale). The recorded values span more than an order of magnitude (peak
  20.17 at $n = 4$, 1.107 at $n = 40$; `docs/release-notes-v0.1.0.md`,
  qualification 1), so a linear axis would hide the late-$n$ approach to 1.
  A horizontal reference line at $\mathrm{IF} = 1$.
- **Series / markers:** panel 1 uses `if_value`; panel 2 uses
  `shot_if_value`. Marker style encodes the mask: filled if `reportable == 1`
  (panel 2: `shot_reportable == 1`), hollow otherwise; a distinct marker if
  `if_is_lower_bound == 1` (panel 2: `shot_if_is_lower_bound == 1`), whose
  plotted value is then the flagged lower bound, not a point value.
- **Bands:** none. $\mathrm{IF}$ is a ratio of central values and design.md
  §13 defines no band for it; drawing one would invent a statistic.
- **Source / columns:** `results/minimal/steps.csv`: `n`, `if_value`,
  `if_is_lower_bound`, `reportable`, `shot_if_value`,
  `shot_if_is_lower_bound`, `shot_reportable`. Cross-check against
  `results/minimal/metrics.json`: `if_wins`, `reportable_steps_m`,
  `excluded_steps` (and the same under `shot_pipeline`).
- **Filter:** none. The chart marks the majority-test
  mask `reportable == 1`, which by design.md §13 is
  $\varepsilon_u(n) \ge \varepsilon_{\min} = 0.01$.
- **What it shows:** the recorded §13 quantities and the regime dependence
  described in qualification 1 of the release notes. **What it does not
  show:** a new verdict, any claim about late-$n$ behavior beyond
  "IF → 1" (design.md §13 saturation bullet: the metrics cannot there
  distinguish ZNE failure from absence of signal), or any hardware statement.
- **Quantities:** Q1 (both pipelines; R-1 recomputes the density-matrix
  columns with $\delta = 10^{-9}$ and the shot columns with
  $\delta = 10^{-3}$). **Command:** R-1.

### FC-2 - Recorded total attenuation ratio against the §11 heuristic (Tier A)

- **Plot type:** two stacked panels sharing x. Upper: $r(n)$ (linear y).
  Lower: $\ln r(n)$ (linear y). On the lower panel a single-exponential
  attenuation appears as a straight line, so departures show as curvature.
- **x:** `n` (steps, linear). **y (upper):** $r(n) = E_{\text{noisy}}(n)/E_0(n)$,
  dimensionless. **y (lower):** $\ln r(n)$, dimensionless.
- **Series:** (i) recorded $r(n)$ from the density-matrix pipeline; (ii) the
  §11 global-depolarizing heuristic $e^{-\Gamma(n)}$ computed from the recorded
  $\lambda = 1$ gate counts and the recorded rates (Q4). The heuristic is a
  reference curve, not a fit and not a prediction under test; design.md §11
  calls it "a heuristic, not a theorem".
- **Markers:** filled where the proposed mask $|E_0(n)| \ge 0.1$ holds,
  hollow where it does not. The threshold comes from
  `docs/prereg-p2zero-outline.md` §4, but it is not final. Here it only keeps
  ill-conditioned ratios near the oscillation nodes visually distinct.
- **Bands:** none. The density-matrix pipeline is exact under the noise
  model, with zero sampling variance (`docs/results-minimal.md` §6), and
  $E_{\text{noisy}}(n)$ at $\lambda = 1$ is seed-independent (design.md §13).
- **Source / columns:** `results/minimal/steps.csv`: `n`, `e0_trotter`,
  `e_noisy_dm`. For the heuristic curve: `results/minimal/folded_circuits.csv`
  rows with `lambda_nominal == 1.0`: `n`, `cx`, `sx`, `x`, `sxdg`;
  `results/minimal/environment.json`: `parameters.noise.p1`,
  `parameters.noise.p2`.
- **Filter:** display-only mask `abs(e0_trotter) >= 0.1` (source:
  outline §4, provisional). No row is dropped.
- **What it shows:** the discrepancy already recorded in
  `docs/results-minimal.md` §8 (observed decay roughly half the heuristic
  rate), on the recorded total attenuation. **What it does not show:** any
  apportionment between single- and two-qubit channels (outline §5; that
  requires the factorial, Tier B), any hypothesis verdict (the outline's
  H-G/H-L intervals are not final), or any statement about the true functional
  form of the response.
- **Quantities:** Q3, Q4. **Command:** R-3, R-4.

### FC-3 - Folding granularity: realized and effective scale vs nominal (Tier A)

- **Plot type:** strip/scatter, one point per `(n, fold_seed)`, three facets
  by `lambda_nominal` ∈ {1.0, 1.5, 2.0}.
- **x:** `n` (steps, linear). **y:** two overlaid series, dimensionless,
  linear scale: (i) $\lambda_r - \lambda_{\text{nominal}}$;
  (ii) $\lambda_{\text{eff}} - \lambda_r$. The differences are small, bounded,
  and signed, and a log axis cannot show zero or sign.
- **Reference curves:** the design's quantization envelope $\pm 1/(10n)$ for
  the $\lambda = 1.5$ facet (design.md §10, item 2: odd $n$ realizes
  $1.5 \pm$ at most $1/(10n)$), and the exact-zero line for the $\lambda = 1.0$
  and $2.0$ facets, which §10 states are exactly achievable at every $n$.
- **Bands:** none; every value is a deterministic count-derived number.
- **Source / columns:** `results/minimal/folded_circuits.csv`: `n`,
  `fold_seed`, `lambda_nominal`, `lambda_r`, `lambda_eff`, `cx`, `sx`, `x`,
  `sxdg`; `results/minimal/environment.json`: `parameters.noise.p1`,
  `parameters.noise.p2` (for recomputing `lambda_eff`).
- **Filter:** none.
- **What it shows:** whether the recorded abscissas obey the §10 statements
  (quantization grid; $\lambda_{\text{eff}} \le \lambda_r$ with equality at
  $\lambda_r = 1$). **What it does not show:** anything about ZNE performance or
  about which regression arm is better; those comparisons are already
  reported in `docs/results-minimal.md` §4 and are not revisited here.
- **Quantities:** Q5. **Command:** R-5.

### FC-4 - Per-seed primary intercept error and the seed-spread band (Tier A)

- **Plot type:** strip plot of per-seed values with the per-step central
  value and its band overlaid; two panels (density-matrix primary; shot
  primary).
- **x:** `n` (steps, linear). **y:** per-seed mitigated error
  $\varepsilon^{(s)}_m(n) = |E^{(s)}_{\text{ZNE}}(n) - E_0(n)|$ (dimensionless,
  log scale). The recorded seed spread ranges from $3\times10^{-5}$ to
  $3.9\times10^{-3}$ (`docs/results-minimal.md` §6) while the errors themselves
  reach $O(0.4)$ at late $n$ (§5 there), so a linear axis would collapse the
  spread to zero width.
- **Series / band:** eight points per $n$ (one per `fold_seed`) in each
  panel; the central $\varepsilon_m(n)$ (`eps_m`) and the band `eps_m_band`,
  which by design.md §13 is the `ddof=1` standard deviation of the eight
  per-seed errors. Panel 1's band is folding-configuration spread (exact
  pipeline). Panel 2 overlays `shot_eps_m`, `shot_eps_m_band` (a seed-spread
  SD that includes shot-sampling variation, see the conventions above), and
  separately `shot_primary_sem` (the standard error $s_n/\sqrt{8}$ of the
  shot primary, §13), each labeled as such. None is a confidence interval.
- **Source / columns:**
  - Panel 1: `results/minimal/seed_arms.csv`: `n`, `fold_seed`,
    `primary_intercept`; `results/minimal/steps.csv`: `n`, `e0_trotter`,
    `eps_m`, `eps_m_band`, `zne_primary_mean`, `zne_primary_std`.
  - Panel 2: the per-seed shot intercepts are not stored as a column, but
    they are fully reconstructible from the bundle. Join
    `results/minimal/shot_values.csv` (`n`, `fold_seed`, `lambda_nominal`,
    `expectation_shot`) with `results/minimal/folded_circuits.csv` (`n`,
    `fold_seed`, `lambda_nominal`, `lambda_r`) on `(n, fold_seed,
    lambda_nominal)` and apply the recorded primary estimator, the
    degree-one OLS zero-noise intercept on the realized abscissas
    $\lambda_r$ (design.md §10 pre-registered choice; §11 `LinearFactory`;
    implemented as `numpy.polyfit(..., 1)` in
    `src/zne_scars/zne_runner.py:linear_intercept`), per `(n, fold_seed)`.
    That gives all 320 shot intercepts.
  - Check: R-6 recomputes `shot_primary_mean`, `shot_primary_std`,
    `shot_primary_sem`, `shot_eps_m`, and `shot_eps_m_band` from the
    reconstructed intercepts, compares against `results/minimal/steps.csv`,
    and prints its own maximum deviation. On 2026-09-06, this calculation
    reproduced `shot_eps_m_band` for all 40 steps. Its largest absolute
    difference from the recorded column was 1.3270634591222574e-16.
- **Filter:** none. Rows with `clamp_flag == 1` or
  `secondary_avoid_log_failed == 1` concern the secondary, not this chart.
  A future variant that plots the secondary must show a flagged row as a
  marker with no value, never a substituted one (design.md §11 clamped-fit
  policy; §20 M3-3).
- **What it shows:** how small the density-matrix
  folding-configuration spread is relative to the error it decorates
  (already stated in `docs/results-minimal.md` §6), and of the size of the
  shot ensemble's seed-plus-sampling spread and SEM relative to the shot
  error. **What it does not show:** uncertainty in the true
  noiseless value, any significance claim, or any interpretation of the band
  as a probability interval.
- **Quantities:** Q1, Q6 (R-6 recomputes the density-matrix seed statistics
  from `seed_arms.csv` and the shot seed statistics, mean, SD, SEM, and error
  band, from the reconstructed shot intercepts). **Command:** R-1, R-6.

### FC-5 - Isolated single-qubit attenuation, $p_2 = 0$ control (Tier B)

- **Data required:** the $(p_1, p_2) = (10^{-3}, 0)$ arm described in
  `docs/prereg-p2zero-outline.md`. No code or data exist for this arm, and
  its preregistration has not been completed. R-B1 shows the planned command.
- **Plot type:** two stacked panels. Upper: $\ln r_1(n)$
  vs `n` with the masked points filled and the OLS line drawn only if the
  outline's adequacy gate passes and only after the preregistration sets the
  residual tolerance. Lower: the per-step fit residuals $e(n)$ vs `n`, which R-B1
  prints explicitly, one line per masked step.
- **x:** `n` (steps, linear). **y (upper):** $\ln r_1(n)$, dimensionless,
  linear. **y (lower):** residual $\ln r_1(n) - (a + b\,n)$, dimensionless,
  linear.
- **Bands:** none (exact density-matrix pipeline, per outline §3).
- **Source / columns (future):** a fresh bundle in a new
  `results/<p2zero-arm>/` directory (never `results/minimal/`, outline §6)
  in the §16 bundle format: `steps.csv` columns `n`, `e0_trotter`,
  `e_noisy_dm`. $E_0(n)$ is the same noiseless Trotter reference already
  recorded in `results/minimal/steps.csv` `e0_trotter`, and the future bundle
  must reproduce it, since it is noise-independent.
- **Proposed filter:** `abs(e0_trotter) >= 0.1`,
  computed from pre-result quantities only (outline §4). A sign flip
  (`r <= 0`) or `r > 1 + 1e-9` on any masked step means "model inadequate"
  and no fit, under the rule in the outline. The $10^{-9}$ is a fixed
  policy tolerance, not a derived bound (outline §4).
- **What it could show:** only the behavior of the isolated single-qubit
  channel described in outline §5. It could not divide the combined gap
  between channels or change the v0.1.0 result.
- **Quantities:** Q3 (applied to the future arm), Q8. **Command:** R-B1.

### FC-6 - $2 \times 2$ factorial additivity check (Tier B)

- **Available data:** two of the four cells. The $(0, 0)$
  cell is the recorded `e0_trotter` reference and the $(10^{-3}, 10^{-2})$
  cell is the recorded canonical noisy run, so the combined-arm rate $g_{12}$
  is a Tier A diagnostic (Q7). The control arms $(10^{-3}, 0)$ and
  $(0, 10^{-2})$, which give $g_1$ and $g_2$, do not exist. R-B2 specifies
  the planned command, but it needs those two control arms.
- **Plot type:** a point chart of the three fitted rates
  $g_1, g_2, g_{12}$ (dimensionless per step, linear y) and, in a second
  panel, the additivity residual $\Delta = g_{12} - (g_1 + g_2)$ with the
  permitted range drawn as a band. That range has not been chosen (outline §5), so it
  cannot yet be drawn.
- **x:** categorical (the three arms; then the single residual). **y:** rate
  per step, dimensionless, linear.
- **Bands:** none of statistical origin (exact pipeline). The only band will
  show the permitted additivity range after that range has been set.
- **Source / columns (future):** `steps.csv` of each new arm (`n`,
  `e0_trotter`, `e_noisy_dm`) plus the recorded `results/minimal/steps.csv`
  for the combined arm.
- **Proposed filter:** the same mask as FC-5, applied
  identically to all arms.
- **What it could show:** under outline §5, the combined gap may be divided
  between the two channels only if the additivity rule is set before either
  new arm runs. If the data fail that test, the channels interact and simple
  subtraction is not justified. If either control runs before the rule is
  set, the comparison must be described as post-hoc.
- **Quantities:** Q7, Q8. **Command:** R-7 (for $g_{12}$ only, Tier A), R-B2.

## 4. Definitions and formulas

The notation follows design.md §13 and `docs/results-minimal.md`. $E_0(n)$ is
the noiseless Trotter reference (`e0_trotter`), and
$E_{\text{noisy}}(n)$ is the unmitigated $\lambda=1$ value (`e_noisy_dm`).
$E_{\text{ZNE}}(n)$ is the mean primary ZNE estimate
(`zne_primary_mean`), while $E^{(s)}_{\text{ZNE}}(n)$ is the primary intercept
for seed $s$ (`primary_intercept`), with $s=1,\ldots,8$.

### Q1 - Per-step errors and improvement factor

As defined in design.md §13,
$\varepsilon_u(n) = |E_{\text{noisy}}(n) - E_0(n)|$;
$\varepsilon_m(n) = |E_{\text{ZNE}}(n) - E_0(n)|$;
$\mathrm{IF}(n) = \varepsilon_u(n)/\varepsilon_m(n)$. A step is reportable
when $\varepsilon_u(n) \ge \varepsilon_{\min} = 0.01$. This filters out steps
where the original error is too small to make the comparison useful; it does
not protect the denominator.

Design.md §13 also sets the denominator rule. With $\delta = 10^{-9}$ (density
matrix) or $10^{-3}$ (shot), if $\varepsilon_m(n) \le \delta$ then
$\mathrm{IF}(n)$ is reported as the flagged lower bound
$\varepsilon_u(n)/\delta$ (`if_is_lower_bound == 1`), never as a point value;
no non-finite value enters any table.

**Checks:**

- The recorded columns equal these formulas applied to the recorded inputs,
  in both pipelines: density matrix from `e_noisy_dm`/`zne_primary_mean`,
  shot from `shot_baseline_mean`/`shot_primary_mean` (the §13 shot baseline
  is the mean of the eight seeded $\lambda = 1$ executions). R-1 checks this
  to floating-point precision.
- $\varepsilon_{\min}$ and $\delta$ are the recorded `environment.json`
  `parameters.eps_min`, `parameters.delta_density_matrix`,
  `parameters.delta_shot`.

**Edge cases:**

- $\varepsilon_m(n) \le \delta$ gives the lower-bound flag as above.
- $\varepsilon_u(n) < \varepsilon_{\min}$ is tabulated but excluded from the
  majority test only (the recorded case is $n = 34$: `metrics.json`
  `excluded_steps`).

These definitions are unchanged.

### Q2 - Aggregate error and improvement

$\mathrm{RMS}_u = \sqrt{\tfrac{1}{40}\sum_{n=1}^{40}\varepsilon_u(n)^2}$,
$\mathrm{RMS}_m$ is defined in the same way, and
$\mathrm{GIF} = \mathrm{RMS}_u/\mathrm{RMS}_m$. These calculations use all
40 steps; the reportability filter does not apply (§13). R-2 checks that all
40 rows are present. If $\mathrm{RMS}_m$ were zero, §13 would report GIF as a
lower bound using the `gif_is_lower_bound` flag in `metrics.json`. That case
does not occur in the recorded data. The recorded values
(`metrics.json`): $\mathrm{RMS}_u = 0.32079729685433694$,
$\mathrm{RMS}_m = 0.25106736243976785$, $\mathrm{GIF} = 1.2777339664421639$.

### Q3 - Attenuation ratio and its logarithm

$$ r(n) = \frac{E_{\text{noisy}}(n)}{E_0(n)}, \qquad \ell(n) = \ln r(n), \qquad
\mathcal{M} = \{\, n : |E_0(n)| \ge 0.1 \,\}. $$
**Checks:**

- $E_0(n) \ne 0$ (domain).
- $|E_0(n)| \ge 0.1$ on the mask, so that the ratio is not ill-conditioned
  near oscillation nodes (outline §4's stated purpose).
- $r(n) > 0$, so that $\ell(n)$ exists.
- $E_0$ is noise-independent, so $\mathcal{M}$ depends on pre-result
  quantities only (outline §4). No outcome-dependent quantity, $r(n)$
  included, may enter the mask.
- No independence assumption is needed: $E_{\text{noisy}}(n)$ at
  $\lambda = 1$ is a single deterministic value per step (design.md §13).

**When the calculation is undefined:** if $E_0(n) = 0$, $r$ is undefined
and the row is reported as unmasked with no value. If $r(n) \le 0$ inside
$\mathcal{M}$, that is a sign flip: $\ell$ is undefined, the step is
reported, and no fit is performed. This is the adequacy check described in
outline §4. If $r(n) > 1 + 10^{-9}$ inside
$\mathcal{M}$, the step is reported; the $10^{-9}$ is the outline's policy
tolerance, a policy choice and not a derived bound. R-3 prints both the
masked and the unmasked step lists.
The threshold 0.1 is still a proposal. Using it for this calculation does not
make it part of the final analysis plan.

### Q4 - Estimated total exposure at $\lambda = 1$

Following §11, $\gamma_k \equiv -\ln(1 - p_k)$,
$\Gamma_2 = N_2\gamma_2$, $\Gamma_1 = N_1\gamma_1$, with $N_2$ the total number
of noisy two-qubit gate applications in the whole circuit at $\lambda = 1$ and
$N_1$ the total number of noisy single-qubit gate applications including the
state-preparation $X$ gates. Define $\Gamma(n) = \Gamma_2(n) + \Gamma_1(n)$ and
the heuristic reference curve $r_{\text{heur}}(n) = e^{-\Gamma(n)}$ (the §11
curve $E(\lambda) \approx E_0 e^{-(\Gamma_2\lambda + \Gamma_1)}$ at
$\lambda = 1$).
For the existing data, $N_2(n)$ = `cx` and
$N_1(n)$ = `sx + x + sxdg` from `folded_circuits.csv` rows with
`lambda_nominal == 1.0`; the noisy gate classes are exactly
`environment.json` `parameters.noise.two_qubit_gates` and
`parameters.noise.one_qubit_gates`; `rz` is in `clean_gates` and is excluded.
**Checks:**

- The $\lambda = 1$ counts are identical across the 8 fold seeds at every
  $n$, because folding at $\lambda = 1$ returns the circuit unchanged
  (design.md §13). R-4 asserts this and stops if it is violated.
- The `sxdg` column is included in $N_1$ whatever its value, since the noise
  model attaches $p_1$ to it (design.md §8).

**Edge cases:** $p_k = 0$ gives $\gamma_k = 0$ exactly; $p_k \to 1$ gives
$\gamma_k \to \infty$ (not in range). Section 11 calls the curve a heuristic,
not a theorem, and
`docs/results-minimal.md` §8 already records that the observed total decay is
roughly half its rate. The curve is used only as a reference.

### Q5 - Realized and effective scale factors

Following §10, $\lambda_r = N_{cx}^{\text{folded}}/N_{cx}^{\text{base}}$
(measured from the folded circuit), and
$$ \lambda_{\text{eff}} = \frac{\Gamma_2\,\lambda_r + \Gamma_1}{\Gamma_2 + \Gamma_1}
\;\le\; \lambda_r, \quad \text{equality at } \lambda_r = 1, $$
with $\Gamma_k$ as in Q4 at the given $n$. For the recorded data,
$N_{cx}^{\text{folded}}$ = `cx` of the row; $N_{cx}^{\text{base}}$ = `cx` of
the same-$n$ row with `lambda_nominal == 1.0`; rates from `environment.json`.
**Checks:**

- $N_{cx}^{\text{base}} > 0$ (it is $10n$, §10).
- $\Gamma_1 + \Gamma_2 > 0$.
- The recorded `lambda_r` and `lambda_eff` columns equal these formulas
  (R-5 checks to floating point).

**Edge cases:**

- $\lambda_r = 1$ gives $\lambda_{\text{eff}} = 1$ exactly.
- $\Gamma_2 = 0$ (the $p_2 = 0$ arm) gives $\lambda_{\text{eff}} = 1$ for
  every $\lambda_r$, so the $\lambda_{\text{eff}}$ regression is degenerate
  there. Outline §3 requires citing the design.md §20 M2-6 convention for
  that arm.
- For $\Gamma_1 = \Gamma_2 = 0$ the $0/0$ case is defined as
  $\lambda_{\text{eff}} = \lambda_r$ by design.md §20 M2-6.

Section 10 also gives the quantization rule $\lambda_r \in \{1 + m/(5n)\}$;
$\lambda = 1.5$ is exactly achievable only at even $n$.

### Q6 - Variation across seeds

$\bar E_{\text{ZNE}}(n) = \tfrac18\sum_s E^{(s)}_{\text{ZNE}}(n)$. Let $s_n$
be the sample standard deviation across seeds, calculated with `ddof=1`; the
standard error is $s_n/\sqrt{8}$. For the per-seed errors
$\varepsilon^{(s)}_m(n) = |E^{(s)}_{\text{ZNE}}(n) - E_0(n)|$, the error band
is their `ddof=1` standard deviation. It is calculated from the absolute
errors themselves, not by linearizing the absolute-value function (§13).
The same formulas
define the shot pipeline's `shot_primary_mean`, `shot_primary_std`,
`shot_primary_sem`, `shot_eps_m`, `shot_eps_m_band` over the eight per-seed
shot intercepts $E^{(s)}_{\text{ZNE,shot}}(n)$, each the degree-one OLS
intercept of the three recorded `expectation_shot` values against their
realized $\lambda_r$ (design.md §10, §11; `linear_intercept` in
`src/zne_scars/zne_runner.py`).

**Checks:**

- Exactly 8 seeds per step and exactly 3 scale factors per seed (R-6 prints
  the counts).
- The recorded density-matrix columns `zne_primary_mean`, `zne_primary_std`,
  and `eps_m_band` equal these formulas over `primary_intercept`.
- The recorded shot columns equal these formulas over the reconstructed shot
  intercepts. R-6 checks all of them and prints the maximum deviation.

**What the bands are:**
as set out in the §3 chart conventions, $s_n$ is folding-configuration
spread in the density-matrix pipeline and includes sampling variation in the
shot pipeline. In the shot pipeline $s_n/\sqrt{8}$ is the standard error of
the eight-member mean. Neither $\pm s_n$ nor $\pm s_n/\sqrt{8}$ is a
confidence interval.

**Edge cases:**

- Fewer than 2 valid seeds leaves the standard deviation undefined and no
  band is drawn.
- For the secondary, a step with any `clamp_flag == 1` seed is entirely
  rerun in `avoid_log` mode, and a step with any
  `secondary_avoid_log_failed == 1` (or `shot_` counterpart) has no
  estimate: "no partial or mixed averages" (design.md §11; §20 M3-3).
- The recorded density-matrix secondary has zero flags and the shot
  secondary has flagged steps at $n = 34$ - $37$ (`docs/results-minimal.md`
  §6); R-6 prints the recorded flag counts.

### Q7 - Attenuation rate in the existing combined-noise data

Over the masked steps $\mathcal{M}$ of Q3 with $\ell(n) = \ln r(n)$, the
ordinary least-squares line $\ell(n) \approx a + b\,n$:
$$ b = \frac{\sum_{n\in\mathcal{M}} (n - \bar n)(\ell(n) - \bar\ell)}{\sum_{n\in\mathcal{M}} (n - \bar n)^2}, \qquad
g_{12} = -b, \qquad e(n) = \ell(n) - (a + b\,n). $$

This applies the estimator in outline §4 to the recorded combined arm
$(10^{-3}, 10^{-2})$. Because that analysis was not specified before the
data were collected, it is post-hoc.

The analysis reports two values: the raw fitted rate $\hat g = -b$, and the
rate $g$ after applying the rule in outline §2:
$g = 0$ if $\hat g \in [-10^{-9}, 0)$, otherwise $g = \hat g$. A raw
$\hat g < -10^{-9}$ is not treated; it triggers the "model inadequate -
anti-attenuation" verdict (outline §4) and no rate is used further. R-7
prints both $\hat g_{12}$ and $g_{12}$.

**Checks:**

- The single-exponential-in-$n$ form is the §11 heuristic, which §11 flags
  as not generally valid for interleaved local channels. Residual structure
  is therefore expected to be informative, not noise.
- No homoscedasticity or independence of residuals is assumed or needed to
  compute the slope.
- At least three masked points are required.

**The command handles failures in this order:**

- With fewer than 3 masked points, R-7 stops with a message and reports no
  rate, before computing any mean or slope. A two-point line is exactly
  determined and has no residual, and fewer points have no slope at all.
- With any sign flip inside $\mathcal{M}$, R-7 exits with a message naming
  the step and performs no fit.

The outline does not yet specify a residual tolerance (outline §4), so this
calculation cannot pass or fail the model. R-7 prints the residuals without
classifying them.

R-7 calculates $g_{12}$. It is different from the oracle rates in
`docs/results-minimal.md` §9: the fits use different objectives and domains,
and Q7 applies a mask while §9 does not. The values should not be compared as
though they measure the same thing.

### Q8 - Control-arm rates and additivity

$g_1$ is the Q7 estimator applied to the future $(10^{-3}, 0)$ arm's
$r_1(n)$, and $g_2$ is the same on the future $(0, 10^{-2})$ arm.
$\Delta = g_{12} - (g_1 + g_2)$, where every $g$ entering $\Delta$ is the
rate after applying Q7's rule: a raw $\hat g \in [-10^{-9}, 0)$ becomes 0.
R-B1 and R-B2 print both values and use the adjusted value in $\Delta$.

**Assumptions:**

- Each arm passes the outline's adequacy gate (0 < r ≤ 1 + 10⁻⁹ on all
  masked steps).
- The fitted rate must not trigger the anti-attenuation rule. Under outline
  §§2 and 4, $g_1 < -10^{-9}$ is classified as “model inadequate -
  anti-attenuation,” while $g_1 \in [-10^{-9},0)$ is treated as zero.
- The same mask on all arms.
- A residual tolerance specified before any run.
- An additivity criterion $|\Delta| \le \tau_{\text{add}}$ specified before
  either new arm runs (outline §5).

**Edge cases:** if any arm is "model inadequate", whether by
the pointwise gate, by the fit-level anti-attenuation rule, or by the
residual test after its tolerance is set, there is no $\Delta$.
$g_1^{\text{heur}}$ (outline §2) requires the exact $N_1(n)$, which Q4 can
calculate from the existing gate counts, but the hypothesis intervals remain
provisional. This document does not define $\tau_{\text{add}}$, and there are
no data from which to calculate $g_1$ or $g_2$.

## 5. Commands

Run each Tier A command below from the repository root. Each reads files under
`results/minimal/` and writes nothing. All seven were tested on 2026-09-06
against baseline
`1822597ed5e222ac770e0f619d0bfa62e8276c20` with Python 3.12.14 in the pinned
`.venv`; each exited 0.

When a command checks a recorded column, it prints the largest absolute
difference. A result near floating-point rounding error (about $10^{-16}$),
or exactly zero, confirms that the column contains the stated calculation.

### R-1 - Per-step errors, improvement factors, and masks

```bash
.venv/bin/python -c "import csv,json; R=list(csv.DictReader(open('results/minimal/steps.csv'))); P=json.load(open('results/minimal/environment.json'))['parameters']; emin=P['eps_min']
for tag,base,mit,delta in [('dm','e_noisy_dm','zne_primary_mean',P['delta_density_matrix']),('shot','shot_baseline_mean','shot_primary_mean',P['delta_shot'])]:
    pre='' if tag=='dm' else 'shot_'; d=0.0; wins=0; rep=0; lb=0
    for r in R:
        e0=float(r['e0_trotter']); eu=abs(float(r[base])-e0); em=abs(float(r[mit])-e0)
        d=max(d,abs(eu-float(r[pre+'eps_u'])),abs(em-float(r[pre+'eps_m'])))
        if em>delta: d=max(d,abs(eu/em-float(r[pre+'if_value'])))
        else: lb+=1
        d=max(d,abs(int(em<=delta)-int(r[pre+'if_is_lower_bound'])))
        rp=int(eu>=emin); d=max(d,abs(rp-int(r[pre+'reportable']))); rep+=rp; wins+=int(rp and (eu/em>1 if em>delta else eu/delta>1))
    print(tag,'rows',len(R),'delta',delta,'eps_min',emin,'max_abs_dev_vs_recorded',d,'reportable_m',rep,'if_wins',wins,'lower_bound_rows',lb)"
```

### R-2 - Aggregate metrics

```bash
.venv/bin/python -c "import csv,json,math; R=list(csv.DictReader(open('results/minimal/steps.csv'))); m=json.load(open('results/minimal/metrics.json'))
ru=math.sqrt(sum(float(r['eps_u'])**2 for r in R)/len(R)); rm=math.sqrt(sum(float(r['eps_m'])**2 for r in R)/len(R))
print('n_steps',len(R),'rms_u',ru,'rms_m',rm,'gif',ru/rm); print('dev_vs_metrics',ru-m['rms_u'],rm-m['rms_m'],ru/rm-m['gif_value'])"
```

### R-3 - Attenuation ratio and logarithm for all 40 steps

```bash
.venv/bin/python -c "import csv,math; R=list(csv.DictReader(open('results/minimal/steps.csv'))); out=[]
for r in R:
    n=int(r['n']); e0=float(r['e0_trotter']); en=float(r['e_noisy_dm']); masked=abs(e0)>=0.1
    ratio=en/e0 if e0!=0 else float('nan'); out.append((n,masked,ratio))
inc=[o for o in out if o[1]]; exc=[o[0] for o in out if not o[1]]
print('steps',len(out),'masked_in',len(inc),'masked_out',exc); print('sign_flips_in_mask',sum(1 for o in inc if o[2]<=0),'ratio_gt_1_in_mask',sum(1 for o in inc if o[2]>1+1e-9))
for n,masked,ratio in out: print('n',n,'mask','IN ' if masked else 'OUT','r',ratio,'ln_r',(math.log(ratio) if ratio>0 else 'undefined (r<=0)') if ratio==ratio else 'undefined (E0=0)')"
```

### R-4 - Estimated exposure from recorded gate counts and error rates

```bash
.venv/bin/python -c "import csv,json,math; env=json.load(open('results/minimal/environment.json'))['parameters']['noise']; g1=-math.log(1-env['p1']); g2=-math.log(1-env['p2'])
F=[r for r in csv.DictReader(open('results/minimal/folded_circuits.csv')) if float(r['lambda_nominal'])==1.0]; base={}
for r in F: base.setdefault(int(r['n']),set()).add((int(r['cx']),int(r['sx'])+int(r['x'])+int(r['sxdg'])))
assert all(len(v)==1 for v in base.values()), 'lambda=1 counts must be seed-independent'
print('gamma1',g1,'gamma2',g2,'clean_gates',env['clean_gates'],'one_qubit_gates',env['one_qubit_gates'],'two_qubit_gates',env['two_qubit_gates'])
print('steps',len(base))
for n in sorted(base):
    N2,N1=next(iter(base[n])); G=N2*g2+N1*g1
    print('n',n,'N2',N2,'N1',N1,'Gamma',G,'Gamma_per_step',G/n,'exp(-Gamma)',math.exp(-G))"
```

### R-5 - Realized and effective scale factors

```bash
.venv/bin/python -c "import csv,json,math; env=json.load(open('results/minimal/environment.json'))['parameters']['noise']; g1=-math.log(1-env['p1']); g2=-math.log(1-env['p2'])
F=list(csv.DictReader(open('results/minimal/folded_circuits.csv'))); base={}
for r in F:
    if float(r['lambda_nominal'])==1.0: base[int(r['n'])]=(int(r['cx']),int(r['sx'])+int(r['x'])+int(r['sxdg']))
dr=de=0.0; offgrid=0
for r in F:
    n=int(r['n']); cx0,n1=base[n]; lr=int(r['cx'])/cx0; G2=cx0*g2; G1=n1*g1; le=(G2*lr+G1)/(G2+G1)
    dr=max(dr,abs(lr-float(r['lambda_r']))); de=max(de,abs(le-float(r['lambda_eff']))); offgrid+=int(abs(lr-float(r['lambda_nominal']))>1e-12)
print('rows',len(F),'max_dev_lambda_r',dr,'max_dev_lambda_eff',de,'rows_with_lambda_r_ne_nominal',offgrid,'lambda_eff_le_lambda_r_everywhere',all(float(r['lambda_eff'])<=float(r['lambda_r'])+1e-12 for r in F))"
```

### R-6 - Variation across seeds and fit-status counts

```bash
.venv/bin/python -c "import csv,math,statistics as S,numpy as np; st={int(r['n']):r for r in csv.DictReader(open('results/minimal/steps.csv'))}; A=list(csv.DictReader(open('results/minimal/seed_arms.csv'))); by={}
for r in A: by.setdefault(int(r['n']),[]).append(r)
d=0.0
for n,rows in by.items():
    e0=float(st[n]['e0_trotter']); p=[float(r['primary_intercept']) for r in rows]
    d=max(d,abs(S.mean(p)-float(st[n]['zne_primary_mean'])),abs(S.stdev(p)-float(st[n]['zne_primary_std'])),abs(S.stdev([abs(x-e0) for x in p])-float(st[n]['eps_m_band'])))
print('rows',len(A),'seeds_per_step',sorted(set(len(v) for v in by.values())),'max_dev_vs_steps_csv',d)
lr={(int(r['n']),int(r['fold_seed']),float(r['lambda_nominal'])):float(r['lambda_r']) for r in csv.DictReader(open('results/minimal/folded_circuits.csv'))}; pts={}
for r in csv.DictReader(open('results/minimal/shot_values.csv')): pts.setdefault((int(r['n']),int(r['fold_seed'])),[]).append((lr[(int(r['n']),int(r['fold_seed']),float(r['lambda_nominal']))],float(r['expectation_shot'])))
sh={}
for (n,s),xy in sorted(pts.items()): sh.setdefault(n,[]).append(float(np.polyfit([x for x,_ in xy],[y for _,y in xy],1)[1]))
ds=0.0
for n,I in sh.items():
    e0=float(st[n]['e0_trotter']); m=S.mean(I); sd=S.stdev(I)
    ds=max(ds,abs(m-float(st[n]['shot_primary_mean'])),abs(sd-float(st[n]['shot_primary_std'])),abs(sd/math.sqrt(len(I))-float(st[n]['shot_primary_sem'])),abs(abs(m-e0)-float(st[n]['shot_eps_m'])),abs(S.stdev([abs(i-e0) for i in I])-float(st[n]['shot_eps_m_band'])))
print('shot_intercepts_reconstructed',sum(len(v) for v in sh.values()),'scale_factors_per_seed',sorted(set(len(v) for v in pts.values())),'shot_seeds_per_step',sorted(set(len(v) for v in sh.values())),'max_dev_shot_mean_std_sem_eps_m_band_vs_steps_csv',ds)
print('clamp_flag',sum(int(r['clamp_flag']) for r in A),'secondary_avoid_log_failed',sum(int(r['secondary_avoid_log_failed']) for r in A),'shot_clamp_flag',sum(int(r['shot_clamp_flag']) for r in A),'shot_secondary_avoid_log_failed',sum(int(r['shot_secondary_avoid_log_failed']) for r in A))
print('shot_secondary_mode_by_step',{n:st[n]['shot_secondary_mode'] for n in st if st[n]['shot_secondary_mode']!='log'},'empty_shot_secondary_estimate',[n for n in st if st[n]['shot_secondary_estimate']==''])"
```

### R-7 - OLS attenuation rate for the existing combined-noise data

```bash
.venv/bin/python -c "import csv,math; R=list(csv.DictReader(open('results/minimal/steps.csv'))); masked=[]
for r in R:
    e0=float(r['e0_trotter']); en=float(r['e_noisy_dm'])
    if abs(e0)>=0.1: masked.append((int(r['n']),en/e0))
k=len(masked)
if k<3: raise SystemExit('fewer than 3 masked points (%d): rate not reported'%k)
flips=[n for n,q in masked if q<=0]
if flips: raise SystemExit('sign flip inside mask at n=%r: fit not performed'%flips)
pts=[(n,math.log(q)) for n,q in masked]
mx=sum(p[0] for p in pts)/k; my=sum(p[1] for p in pts)/k
b=sum((x-mx)*(y-my) for x,y in pts)/sum((x-mx)**2 for x,_ in pts); a=my-b*mx; g12_raw=-b
g12=0.0 if -1e-9<=g12_raw<0 else g12_raw   # rule from outline s2: rates in [-1e-9, 0) become 0; rates below -1e-9 are anti-attenuation
res=[(x,y-(a+b*x)) for x,y in pts]
for x,e in res: print('residual n=%d e=%r'%(x,e))
print('masked_points',k,'g12_raw',g12_raw,'g12_treated',g12,'anti_attenuation_flag',g12_raw<-1e-9,'intercept',a,'max_abs_residual',max(abs(e) for _,e in res),'rms_residual',math.sqrt(sum(e*e for _,e in res)/k),'NOTE: no residual tolerance has been set; this command does not classify the fit')"
```

### R-B1 - Planned Q3/Q8 command for the $p_2 = 0$ arm (FC-5)

The required data do not exist. Run this command only after the study has an
approved preregistration and has created a new data bundle. Replace the
placeholder with that bundle's path.

```bash
# This requires results/<p2zero-arm>/steps.csv, which does not exist yet.
.venv/bin/python -c "import csv,math; R=list(csv.DictReader(open('results/<p2zero-arm>/steps.csv'))); pts=[]; viol=[]
for r in R:
    e0=float(r['e0_trotter']); en=float(r['e_noisy_dm'])
    if abs(e0)>=0.1:
        q=en/e0
        if q<=0 or q>1+1e-9: viol.append((int(r['n']),q))
        else: pts.append((int(r['n']),math.log(q)))
if viol: raise SystemExit('model inadequate (outline s4 gate): violating steps %r; no fit performed'%viol)
k=len(pts)
if k<3: raise SystemExit('fewer than 3 masked points (%d): rate not reported'%k)
mx=sum(p[0] for p in pts)/k; my=sum(p[1] for p in pts)/k
b=sum((x-mx)*(y-my) for x,y in pts)/sum((x-mx)**2 for x,_ in pts); a=my-b*mx; g1_raw=-b
if g1_raw<-1e-9: raise SystemExit('model inadequate - anti-attenuation (outline s4): raw g1=%r'%g1_raw)
g1=0.0 if -1e-9<=g1_raw<0 else g1_raw   # rule from outline s2: raw rate in [-1e-9, 0) is treated as 0
res=[(x,y-(a+b*x)) for x,y in pts]
for x,e in res: print('residual n=%d e=%r'%(x,e))
TAU_RES=None  # set this in the approved preregistration before running the experiment
if TAU_RES is not None and max(abs(e) for _,e in res)>TAU_RES: raise SystemExit('model inadequate - residual tolerance exceeded (outline s4)')
print('masked_points',k,'g1_raw',g1_raw,'g1_treated',g1,'max_abs_residual',max(abs(e) for _,e in res),'NOTE: the residual tolerance and H-G/H-L intervals are not final; this command does not issue a result')"
```

### R-B2 - Planned Q8 additivity command for FC-6

Two of the three rates cannot yet be calculated because the control-arm data
do not exist. Outline §5 requires the additivity threshold
$\tau_{\text{add}}$ to be set before either control arm runs, so it remains
undefined here.

```bash
# This requires both control-arm data sets, which do not exist yet.
.venv/bin/python -c "import csv,math
def rate(path):
    pts=[]
    for r in csv.DictReader(open(path)):
        e0=float(r['e0_trotter']); en=float(r['e_noisy_dm'])
        if abs(e0)>=0.1:
            q=en/e0
            if q<=0 or q>1+1e-9: raise SystemExit('model inadequate in %s at n=%s'%(path,r['n']))
            pts.append((int(r['n']),math.log(q)))
    k=len(pts)
    if k<3: raise SystemExit('fewer than 3 masked points (%d) in %s: rate not reported'%(k,path))
    mx=sum(p[0] for p in pts)/k; my=sum(p[1] for p in pts)/k
    b=sum((x-mx)*(y-my) for x,y in pts)/sum((x-mx)**2 for x,_ in pts); a=my-b*mx; g_raw=-b
    if g_raw<-1e-9: raise SystemExit('model inadequate - anti-attenuation (outline s4) in %s: raw g=%r'%(path,g_raw))
    g=0.0 if -1e-9<=g_raw<0 else g_raw   # rule from outline s2: raw rate in [-1e-9, 0) is treated as 0
    res=[(x,y-(a+b*x)) for x,y in pts]
    for x,e in res: print('%s residual n=%d e=%r'%(path,x,e))
    if TAU_RES is not None and max(abs(e) for _,e in res)>TAU_RES: raise SystemExit('model inadequate - residual tolerance exceeded (outline s4) in %s'%path)
    print(path,'g_raw',g_raw,'g_treated',g)
    return g
TAU_RES=None  # set in the approved preregistration before any experiment
TAU_ADD=None  # set in the approved preregistration before either control arm runs
g12=rate('results/minimal/steps.csv'); g1=rate('results/<p2zero-arm>/steps.csv'); g2=rate('results/<p1zero-arm>/steps.csv')
D=g12-(g1+g2)
print('g12',g12,'g1',g1,'g2',g2,'Delta',D,'NOTE: TAU_RES and TAU_ADD have not been set; this command does not classify the result')"
```

## 6. Decisions required before Phase 2

Before running Phase 2, the preregistration must settle the hypothesis
intervals, residual tolerance, additivity rule, and mask threshold described
below. The $10^{-9}$ rules already come from the outline. The final two items
are existing questions that Phase 2 will not answer.

1. **Hypothesis intervals.** Outline §2 proposes H-G as $[0.75, 1.25]$ of
   $g_1^{\text{heur}}$ and H-L as $[0, 0.50)$, with other values classified as
   “neither.” These intervals need a justification and final approval before
   any control-arm data are collected.
2. **Residual tolerance.** Outline §4 does not yet give a numerical tolerance
   for the residuals of the $\ln r(n)$ fit. Without one, the residuals can be
   reported but cannot be used to accept or reject the model.
3. **The $10^{-9}$ rules.** Outline §4 treats these as fixed policy choices,
   not calculated error bounds. A masked step fails the adequacy check if
   $r(n) \le 0$ or $r(n) > 1 + 10^{-9}$. A fitted $g_1 < -10^{-9}$ is
   classified as anti-attenuation, while $g_1 \in [-10^{-9}, 0)$ is treated as
   zero. This document uses those endpoints without changing them.
4. **Additivity.** The preregistration must define
   $\tau_{\text{add}}$ before either control arm runs (outline §5). This
   document defines $\Delta$ but does not choose the allowed range.
5. **The mask threshold** $|E_0| \ge 0.1$ is the outline's provisional
   choice; it is used here for display and diagnostics only.
6. **The heuristic's $\Gamma_1$ floor arithmetic** remains unresolved on the
   recorded data (`docs/results-minimal.md` §8), and FC-2 does not resolve it.
7. **Cross-platform reproduction.** The failed Linux comparison recorded in
   `docs/ci-reproduction-assessment.md` is a separate problem and is not part
   of this study.

The two Tier B calculations cannot be completed until the control experiments
have been designed, approved, and run.

## 7. Sources and calculations

| ID | Tier | Quantity | Source file(s) | Exact column(s)/key(s) | Formula in this document | Existing definition | Command | Can run now? |
|---|---|---|---|---|---|---|---|---|
| FC-1 | A | Per-step $\mathrm{IF}(n)$ with reportability and lower-bound flags, both pipelines | `results/minimal/steps.csv`; `results/minimal/metrics.json` | `n`, `if_value`, `if_is_lower_bound`, `reportable`, `shot_if_value`, `shot_if_is_lower_bound`, `shot_reportable`; `if_wins`, `reportable_steps_m`, `excluded_steps` (+ `shot_pipeline.*`) | §4 Q1 | design.md §13 (IF, ε_min filter, δ handling, saturation bullet) | R-1 (both pipelines) | Y |
| FC-2 | A | $r(n)$, $\ln r(n)$ vs heuristic $e^{-\Gamma(n)}$, proposed mask | `results/minimal/steps.csv`; `results/minimal/folded_circuits.csv`; `results/minimal/environment.json` | `n`, `e0_trotter`, `e_noisy_dm`; `n`, `lambda_nominal`, `cx`, `sx`, `x`, `sxdg`; `parameters.noise.p1`, `parameters.noise.p2` | §4 Q3, Q4 | design.md §11 (heuristic, γ_k, Γ_k); results-minimal.md §8 (discrepancy); mask: prereg outline §4 (not final) | R-3 (all 40 steps: $r$, $\ln r$ where defined, mask marker), R-4 (all 40 steps: $N_1$, $N_2$, $\Gamma$, $e^{-\Gamma}$) | Y |
| FC-3 | A | $\lambda_r - \lambda_{\text{nominal}}$ and $\lambda_{\text{eff}} - \lambda_r$ per (n, seed, λ) | `results/minimal/folded_circuits.csv`; `results/minimal/environment.json` | `n`, `fold_seed`, `lambda_nominal`, `lambda_r`, `lambda_eff`, `cx`, `sx`, `x`, `sxdg`; `parameters.noise.p1`, `parameters.noise.p2` | §4 Q5 | design.md §10 (λ_r, λ_eff, quantization grid); §20 M2-6 (degenerate case) | R-5 | Y |
| FC-4 | A | Per-seed $\varepsilon^{(s)}_m(n)$, central $\varepsilon_m(n)$, seed-spread band, shot SD/SEM/band (shot intercepts reconstructed) | `results/minimal/seed_arms.csv`; `results/minimal/steps.csv`; `results/minimal/shot_values.csv`; `results/minimal/folded_circuits.csv` | `n`, `fold_seed`, `primary_intercept`; `n`, `e0_trotter`, `eps_m`, `eps_m_band`, `zne_primary_mean`, `zne_primary_std`, `shot_primary_mean`, `shot_primary_std`, `shot_primary_sem`, `shot_eps_m`, `shot_eps_m_band`; `shot_values.csv`: `n`, `fold_seed`, `lambda_nominal`, `expectation_shot`; `folded_circuits.csv`: `n`, `fold_seed`, `lambda_nominal`, `lambda_r` | §4 Q1, Q6 | design.md §13 (uncertainty bullet); results-minimal.md §6 (density-matrix spread is not statistical error; shot spread includes sampling variation; neither a confidence interval) | R-1, R-6 | Y |
| FC-5 | B | $\ln r_1(n)$ and residuals on the $p_2 = 0$ arm | future `results/<p2zero-arm>/steps.csv` (does not exist); `results/minimal/steps.csv` for the reference $E_0$ | future `n`, `e0_trotter`, `e_noisy_dm`; recorded `e0_trotter` | §4 Q3, Q8 | prereg outline §§3-5 (proposed mask, hypothesis intervals, and residual tolerance; fixed $10^{-9}$ policy rules); design.md §16 bundle format | R-B1 (prints each residual and applies the anti-attenuation rule; the residual test remains disabled until its tolerance is set) | N: the $(10^{-3}, 0)$ arm has not been run and the preregistration is incomplete |
| FC-6 | B | $g_1, g_2, g_{12}$ and $\Delta = g_{12} - (g_1 + g_2)$ | future `results/<p2zero-arm>/steps.csv` and `results/<p1zero-arm>/steps.csv` (neither exists); `results/minimal/steps.csv` | `n`, `e0_trotter`, `e_noisy_dm` in each | §4 Q7, Q8 | prereg outline §5 (factorial design and proposed additivity rule); design.md §11 | R-7 ($g_{12}$ only), R-B2 (checks each arm; the residual and additivity tests remain disabled until their limits are set) | N: the two control arms have no data and $\tau_{\text{add}}$ has not been chosen |
| Q1 | A | $\varepsilon_u$, $\varepsilon_m$, $\mathrm{IF}$, reportable mask (both pipelines) | `results/minimal/steps.csv`; `results/minimal/environment.json` | `e0_trotter`, `e_noisy_dm`, `zne_primary_mean`, `eps_u`, `eps_m`, `if_value`, `if_is_lower_bound`, `reportable`, `shot_baseline_mean`, `shot_primary_mean`, `shot_eps_u`, `shot_eps_m`, `shot_if_value`, `shot_if_is_lower_bound`, `shot_reportable`; `parameters.eps_min`, `parameters.delta_density_matrix`, `parameters.delta_shot` | §4 Q1 | design.md §13 | R-1 | Y |
| Q2 | A | $\mathrm{RMS}_u$, $\mathrm{RMS}_m$, $\mathrm{GIF}$ | `results/minimal/steps.csv`; `results/minimal/metrics.json` | `eps_u`, `eps_m`; `rms_u`, `rms_m`, `gif_value`, `gif_is_lower_bound` | §4 Q2 | design.md §13 (all-40-step aggregates) | R-2 | Y |
| Q3 | A | $r(n)$, $\ell(n) = \ln r(n)$, mask $\mathcal{M}$ | `results/minimal/steps.csv` | `n`, `e0_trotter`, `e_noisy_dm` | §4 Q3 | prereg outline §4 (proposed mask threshold 0.1 and fixed $10^{-9}$ policy tolerance); design.md §13 ($E_{\text{noisy}}$ is seed-independent) | R-3 (all 40 steps with mask marker) | Y |
| Q4 | A | $\gamma_k$, $\Gamma_1(n)$, $\Gamma_2(n)$, $\Gamma(n)$, $e^{-\Gamma(n)}$ | `results/minimal/folded_circuits.csv`; `results/minimal/environment.json` | `n`, `lambda_nominal`, `cx`, `sx`, `x`, `sxdg`; `parameters.noise.p1`, `parameters.noise.p2`, `parameters.noise.one_qubit_gates`, `parameters.noise.two_qubit_gates`, `parameters.noise.clean_gates` | §4 Q4 | design.md §11 (definitions), §8 (noisy gate classes) | R-4 | Y |
| Q5 | A | $\lambda_r$, $\lambda_{\text{eff}}$ | `results/minimal/folded_circuits.csv`; `results/minimal/environment.json` | `n`, `fold_seed`, `lambda_nominal`, `lambda_r`, `lambda_eff`, `cx`, `sx`, `x`, `sxdg`; `parameters.noise.p1`, `parameters.noise.p2` | §4 Q5 | design.md §10; §20 M2-6 | R-5 | Y |
| Q6 | A | Seed mean, `ddof=1` SD, SEM, per-seed error band (both pipelines; shot intercepts reconstructed), flag/mode counts | `results/minimal/seed_arms.csv`; `results/minimal/steps.csv`; `results/minimal/shot_values.csv`; `results/minimal/folded_circuits.csv` | `n`, `fold_seed`, `primary_intercept`, `clamp_flag`, `secondary_avoid_log_failed`, `shot_clamp_flag`, `shot_secondary_avoid_log_failed`; `zne_primary_mean`, `zne_primary_std`, `eps_m_band`, `shot_primary_mean`, `shot_primary_std`, `shot_primary_sem`, `shot_eps_m`, `shot_eps_m_band`, `shot_secondary_mode`, `shot_secondary_estimate`; `shot_values.csv`: `n`, `fold_seed`, `lambda_nominal`, `expectation_shot`; `folded_circuits.csv`: `n`, `fold_seed`, `lambda_nominal`, `lambda_r` | §4 Q6 | design.md §13 (uncertainty bullet), §11 (clamp policy), §20 M3-3 (failed-fit policy); results-minimal.md §6 | R-6 | Y |
| Q7 | A | $g_{12}$ (post-hoc OLS rate on the combined arm), residuals | `results/minimal/steps.csv` | `n`, `e0_trotter`, `e_noisy_dm` | §4 Q7 | prereg outline §4 (estimator and proposed residual tolerance) and §2 (rates in $[-10^{-9}, 0)$ become zero); design.md §11 | R-7 (requires at least three masked points and no sign flip; prints the raw and adjusted rates and every residual) | Y, for exploration only; no residual limit has been set |
| Q8 | B | $g_1$, $g_2$, $\Delta$, $\tau_{\text{add}}$ | future `results/<p2zero-arm>/steps.csv`, `results/<p1zero-arm>/steps.csv` (neither exists); `results/minimal/steps.csv` | `n`, `e0_trotter`, `e_noisy_dm` in each | §4 Q8 | prereg outline §§2, 4, 5. The intervals, residual tolerance, and $\tau_{\text{add}}$ are not final. The $10^{-9}$ adequacy and anti-attenuation rules are fixed policy choices rather than error bounds. | R-B1, R-B2 (both print raw and adjusted rates) | N: no control-arm data exist and the additivity rule is not final |
