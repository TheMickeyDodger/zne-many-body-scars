# Follow-up Study Draft — Proposed Charts, Definitions, and Traceability

> **Draft proposal, prepared 2026-09-06.** Not a preregistration, not
> reviewed for execution, and not approved for execution. No part of the
> proposed study has been run: there is no $p_2 = 0$ arm, no $p_1 = 0$ arm,
> no factorial arm, no data for any of them, and no code for any of them in
> this repository.
>
> The Tier A recomputation commands in §5 were run, read-only, against the
> frozen v0.1.0 bundle to confirm that they work as written; that produced no
> new evidence and wrote nothing to the repository.
>
> Before any run, this draft would have to become a full frozen
> preregistration in the style of `docs/design.md`, with its own adversarial
> review, and every provisional interval, mask, and tolerance listed in §6
> would have to be frozen there.
>
> Nothing here alters the v0.1.0 verdict, which is defined by the
> pre-registered metrics of design.md §13 on the recorded canonical data and
> reported with its qualifications in `docs/results-minimal.md`. Nothing here
> is published as a result, and nothing will be executed without explicit
> human authorization.

## 0. Purpose and scope

This draft proposes charts for a follow-up analysis. Each chart is pinned
to exact source files and column names of the frozen bundle, or to a named
future arm (§3). Every plotted or derived quantity is defined by its symbol,
formula, falsifiable assumptions, and degenerate cases with their
pre-declared handling. Frozen v0.1.0 definitions are reused by
citation wherever one exists (§4). Every quantity has a read-only
recomputation command (§5). A traceability matrix ties every chart and
quantity to its source, formula, governing definition, and command (§7).

Out of scope: hardware claims (design.md §14(d)); any change to the v0.1.0
definitions, numbers, tolerances, or pins; and resolution of the open items
in §6. Also out of scope is the cross-platform reproduction question
recorded in the dated annotation of `docs/ci-reproduction-assessment.md`
(2026-09-06). That is a reproduction-verification matter and gets no chart,
experiment, or diagnosis here.

**Numbers policy.** The only result numbers asserted here already appear in
`results/minimal/metrics.json`, `docs/results-minimal.md`, or
`docs/release-notes-v0.1.0.md`, and are cited where used. Every other
quantity is given as a formula plus a runnable command. Structural facts
(row counts, column names, seed counts) were checked against the files on
2026-09-06.

## 1. The two tiers

| Tier | Meaning | Evidentiary status |
|---|---|---|
| **A: recomputable today** | Inputs exist in the frozen v0.1.0 bundle: `results/minimal/steps.csv`, `metrics.json`, `folded_circuits.csv`, `seed_arms.csv`, `shot_values.csv`, `environment.json`. | Post-hoc diagnostics on recorded data, with the same standing as the labeled oracles of `docs/results-minimal.md` §9. Not preregistered, not new evidence, never a verdict. |
| **B: needs arms that do not exist** | Needs the $p_2 = 0$ control arm $(p_1, p_2) = (10^{-3}, 0)$, the $p_1 = 0$ control arm $(0, 10^{-2})$, or both (the full $2 \times 2$ factorial). | No input data. The command is specified but cannot be run today. No outcome is predicted. |

Each item below carries its tier in its heading.

## 2. Inputs that exist (frozen bundle inventory, checked 2026-09-06)

All under `results/minimal/`. Row counts exclude the header line. Column
names are exactly as they appear in the CSV headers.

| File | Rows | Exact header |
|---|---|---|
| `steps.csv` | 40 (one per Trotter step $n = 1..40$) | `n, ed_reference, e0_trotter, e_noisy_dm, zne_primary_mean, zne_primary_std, zne_nominal_mean, zne_nominal_std, zne_effective_mean, zne_effective_std, secondary_estimate, secondary_mode, secondary_std, eps_u, eps_m, eps_m_band, if_value, if_is_lower_bound, reportable, shot_baseline_mean, shot_baseline_std, shot_primary_mean, shot_primary_std, shot_primary_sem, shot_nominal_mean, shot_nominal_std, shot_effective_mean, shot_effective_std, shot_secondary_estimate, shot_secondary_mode, shot_secondary_std, shot_eps_u, shot_eps_m, shot_eps_m_band, shot_if_value, shot_if_is_lower_bound, shot_reportable` |
| `folded_circuits.csv` | 960 (40 steps × 8 fold seeds × 3 nominal scale factors) | `n, fold_seed, lambda_nominal, lambda_r, lambda_eff, expectation_dm, cx, sx, x, rz, sxdg` |
| `shot_values.csv` | 960 | `n, fold_seed, lambda_nominal, expectation_shot, seed_simulator` |
| `seed_arms.csv` | 320 (40 steps × 8 fold seeds) | `n, fold_seed, primary_intercept, nominal_intercept, effective_intercept, clamp_flag, secondary_log, secondary_avoid_log, secondary_avoid_log_failed, shot_clamp_flag, shot_secondary_log, shot_secondary_avoid_log, shot_secondary_avoid_log_failed` |
| `metrics.json` | — | top-level keys `gif_value, rms_u, rms_m, if_wins, reportable_steps_m, excluded_steps, majority_passes, verdict_passes, gif_is_lower_bound, m_zero_flagged, primary_pipeline`, and the same metric keys (plus `note`) under `shot_pipeline` |
| `environment.json` | — | keys `design_section, parameters, platform, source_identifier_note, source_tree_sha256, versions`; the rates used below are `parameters.noise.p1`, `parameters.noise.p2`, with gate classes `parameters.noise.one_qubit_gates`, `parameters.noise.two_qubit_gates`, `parameters.noise.clean_gates` |

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

### FC-1 — Per-step improvement factor with the pre-registered mask (Tier A)

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
- **Filter predicate:** none applied. The chart marks the majority-test
  mask `reportable == 1`, which by design.md §13 is
  $\varepsilon_u(n) \ge \varepsilon_{\min} = 0.01$.
- **Licenses:** a visual restatement of the recorded §13 quantities and of
  qualification 1 of the release notes (regime dependence). **Does not
  license:** any new verdict, any claim about late-$n$ behavior beyond
  "IF → 1" (design.md §13 saturation bullet: the metrics cannot there
  distinguish ZNE failure from absence of signal), or any hardware statement.
- **Quantities:** Q1 (both pipelines; R-1 recomputes the density-matrix
  columns with $\delta = 10^{-9}$ and the shot columns with
  $\delta = 10^{-3}$). **Command:** R-1.

### FC-2 — Recorded total attenuation ratio against the §11 heuristic (Tier A)

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
- **Markers:** filled where the provisional mask $|E_0(n)| \ge 0.1$ holds,
  hollow where it does not. The mask is the one proposed provisionally in
  `docs/prereg-p2zero-outline.md` §4. It is unfrozen and is used here only to
  keep ill-conditioned near-node ratios visually distinct.
- **Bands:** none. The density-matrix pipeline is exact under the noise
  model, with zero sampling variance (`docs/results-minimal.md` §6), and
  $E_{\text{noisy}}(n)$ at $\lambda = 1$ is seed-independent (design.md §13).
- **Source / columns:** `results/minimal/steps.csv`: `n`, `e0_trotter`,
  `e_noisy_dm`. For the heuristic curve: `results/minimal/folded_circuits.csv`
  rows with `lambda_nominal == 1.0`: `n`, `cx`, `sx`, `x`, `sxdg`;
  `results/minimal/environment.json`: `parameters.noise.p1`,
  `parameters.noise.p2`.
- **Filter predicate:** display-only mask `abs(e0_trotter) >= 0.1` (source:
  outline §4, provisional). No row is dropped.
- **Licenses:** an exploratory picture of the discrepancy already recorded in
  `docs/results-minimal.md` §8 (observed decay roughly half the heuristic
  rate), on the recorded total attenuation. **Does not license:** any
  apportionment between single- and two-qubit channels (outline §5; that
  requires the factorial, Tier B), any hypothesis verdict (the outline's
  H-G/H-L intervals are unfrozen), or any statement about the true functional
  form of the response.
- **Quantities:** Q3, Q4. **Command:** R-3, R-4.

### FC-3 — Folding granularity: realized and effective scale vs nominal (Tier A)

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
- **Filter predicate:** none.
- **Licenses:** a check that the recorded abscissas obey the §10 statements
  (quantization grid; $\lambda_{\text{eff}} \le \lambda_r$ with equality at
  $\lambda_r = 1$). **Does not license:** anything about ZNE performance or
  about which regression arm is better; those comparisons are already
  reported in `docs/results-minimal.md` §4 and are not revisited here.
- **Quantities:** Q5. **Command:** R-5.

### FC-4 — Per-seed primary intercept error and the seed-spread band (Tier A)

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
    and prints its own maximum deviation. On 2026-09-06 an independent
    reviewer reconstruction recovered `shot_eps_m_band` on all 40 steps with
    a maximum absolute deviation of 1.3270634591222574e-16 from the recorded
    column.
- **Filter predicate:** none. Rows with `clamp_flag == 1` or
  `secondary_avoid_log_failed == 1` concern the secondary, not this chart.
  A future variant that plots the secondary must show a flagged row as a
  marker with no value, never a substituted one (design.md §11 clamped-fit
  policy; §20 M3-3).
- **Licenses:** a visual account of how small the density-matrix
  folding-configuration spread is relative to the error it decorates
  (already stated in `docs/results-minimal.md` §6), and of the size of the
  shot ensemble's seed-plus-sampling spread and SEM relative to the shot
  error. **Does not license:** any uncertainty statement about the true
  noiseless value, any significance claim, or any interpretation of the band
  as a probability interval.
- **Quantities:** Q1, Q6 (R-6 recomputes the density-matrix seed statistics
  from `seed_arms.csv` and the shot seed statistics, mean, SD, SEM, and error
  band, from the reconstructed shot intercepts). **Command:** R-1, R-6.

### FC-5 — Isolated single-qubit attenuation, $p_2 = 0$ control (Tier B)

- **Status: no input data exist.** This chart needs the arm
  $(p_1, p_2) = (10^{-3}, 0)$ described in `docs/prereg-p2zero-outline.md`,
  which has not been executed, has no frozen preregistration, and has no code
  in this repository. R-B1 specifies the command; it cannot run today.
- **Plot type (as it would be):** two stacked panels. Upper: $\ln r_1(n)$
  vs `n` with the masked points filled and the OLS line drawn only if the
  outline's adequacy gate passes and only after the residual tolerance has
  been frozen. Lower: the per-step fit residuals $e(n)$ vs `n`, which R-B1
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
- **Filter predicate (provisional, unfrozen):** `abs(e0_trotter) >= 0.1`,
  computed from pre-result quantities only (outline §4). A sign flip
  (`r <= 0`) or `r > 1 + 1e-9` on any masked step means "model inadequate"
  and no fit, per the outline's pre-declared gate. The $10^{-9}$ is a frozen
  policy tolerance, not a derived bound (outline §4).
- **Licenses / does not license:** exactly the table in outline §5: isolated
  single-channel statements only; no apportionment of the combined gap; no
  effect on the v0.1.0 verdict. No outcome is predicted here.
- **Quantities:** Q3 (applied to the future arm), Q8. **Command:** R-B1.

### FC-6 — $2 \times 2$ factorial additivity check (Tier B)

- **Status: no input data exist** for two of the four cells. The $(0, 0)$
  cell is the recorded `e0_trotter` reference and the $(10^{-3}, 10^{-2})$
  cell is the recorded canonical noisy run, so the combined-arm rate $g_{12}$
  is a Tier A diagnostic (Q7). The control arms $(10^{-3}, 0)$ and
  $(0, 10^{-2})$, which give $g_1$ and $g_2$, do not exist. R-B2 specifies
  the command; it cannot run today.
- **Plot type (as it would be):** a point chart of the three fitted rates
  $g_1, g_2, g_{12}$ (dimensionless per step, linear y) and, in a second
  panel, the additivity residual $\Delta = g_{12} - (g_1 + g_2)$ with the
  frozen additivity criterion drawn as a band. That band cannot be drawn
  today because the criterion is not frozen (outline §5), and this draft does
  not freeze it.
- **x:** categorical (the three arms; then the single residual). **y:** rate
  per step, dimensionless, linear.
- **Bands:** none of statistical origin (exact pipeline); the only band is
  the frozen criterion, once it exists.
- **Source / columns (future):** `steps.csv` of each new arm (`n`,
  `e0_trotter`, `e_noisy_dm`) plus the recorded `results/minimal/steps.csv`
  for the combined arm.
- **Filter predicate:** the same provisional mask as FC-5, applied
  identically to all arms.
- **Licenses / does not license:** per outline §5, the combined gap may be
  decomposed only if the criterion was frozen before either new arm ran. A
  failed additivity test is a reportable interaction finding, not a license
  to apportion by subtraction. If either control is executed before the
  criterion is frozen, this chart is post hoc by the outline's own rule and
  must be labeled so.
- **Quantities:** Q7, Q8. **Command:** R-7 (for $g_{12}$ only, Tier A), R-B2.

## 4. Definitions and formulas

Notation follows design.md §13 and `docs/results-minimal.md`: $E_0(n)$ is the
noiseless Trotter reference (`e0_trotter`), $E_{\text{noisy}}(n)$ the
unmitigated $\lambda = 1$ value (`e_noisy_dm`), $E_{\text{ZNE}}(n)$ the
seed-averaged primary ZNE estimate (`zne_primary_mean`), $E^{(s)}_{\text{ZNE}}(n)$
the per-seed primary intercept (`primary_intercept`), $s = 1..8$.

### Q1 — Per-step errors, improvement factor, relevance mask (frozen; design.md §13)

**Definitions, reused verbatim from design.md §13:**
$\varepsilon_u(n) = |E_{\text{noisy}}(n) - E_0(n)|$;
$\varepsilon_m(n) = |E_{\text{ZNE}}(n) - E_0(n)|$;
$\mathrm{IF}(n) = \varepsilon_u(n)/\varepsilon_m(n)$;
reportable iff $\varepsilon_u(n) \ge \varepsilon_{\min} = 0.01$ (a
baseline-relevance filter on the numerator, "not a denominator guard").

**Denominator handling (frozen, §13):** with $\delta = 10^{-9}$ (density
matrix) or $10^{-3}$ (shot), if $\varepsilon_m(n) \le \delta$ then
$\mathrm{IF}(n)$ is reported as the flagged lower bound
$\varepsilon_u(n)/\delta$ (`if_is_lower_bound == 1`), never as a point value;
no non-finite value enters any table.

**Assumptions (falsifiable):**

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

Nothing in this draft redefines any of these.

### Q2 — Aggregates (frozen; design.md §13)

$\mathrm{RMS}_u = \sqrt{\tfrac{1}{40}\sum_{n=1}^{40}\varepsilon_u(n)^2}$,
$\mathrm{RMS}_m$ analogously, $\mathrm{GIF} = \mathrm{RMS}_u/\mathrm{RMS}_m$;
"the RMS sums and GIF always run over all 40 steps; the baseline-relevance
filter does not touch them" (§13). **Assumption:** exactly 40 rows, none
missing (structural; R-2 asserts the row count). **Edge case:** none arises
on the recorded data; a hypothetical $\mathrm{RMS}_m = 0$ would be governed by
§13's `gif_is_lower_bound` flag, recorded in `metrics.json`. Recorded values
(`metrics.json`): $\mathrm{RMS}_u = 0.32079729685433694$,
$\mathrm{RMS}_m = 0.25106736243976785$, $\mathrm{GIF} = 1.2777339664421639$.

### Q3 — Attenuation ratio and its log (exploratory; mask from the unfrozen outline §4)

$$ r(n) = \frac{E_{\text{noisy}}(n)}{E_0(n)}, \qquad \ell(n) = \ln r(n), \qquad
\mathcal{M} = \{\, n : |E_0(n)| \ge 0.1 \,\}. $$
**Assumptions (falsifiable):**

- $E_0(n) \ne 0$ (domain).
- $|E_0(n)| \ge 0.1$ on the mask, so that the ratio is not ill-conditioned
  near oscillation nodes (outline §4's stated purpose).
- $r(n) > 0$, so that $\ell(n)$ exists.
- $E_0$ is noise-independent, so $\mathcal{M}$ depends on pre-result
  quantities only (outline §4). No outcome-dependent quantity, $r(n)$
  included, may enter the mask.
- No independence assumption is needed: $E_{\text{noisy}}(n)$ at
  $\lambda = 1$ is a single deterministic value per step (design.md §13).

**Edge cases, pre-declared handling:** if $E_0(n) = 0$, $r$ is undefined
and the row is reported as unmasked with no value. If $r(n) \le 0$ inside
$\mathcal{M}$, that is a sign flip: $\ell$ is undefined, the step is
reported, and no fit is performed. This mirrors the outline §4 adequacy gate
as a diagnostic report, not a verdict. If $r(n) > 1 + 10^{-9}$ inside
$\mathcal{M}$, the step is reported; the $10^{-9}$ is the outline's policy
tolerance, a policy choice and not a derived bound. R-3 prints both the
masked and the unmasked step lists.
**Status:** the mask threshold 0.1 is provisional and unfrozen; using it here
does not freeze it.

### Q4 — Heuristic total exposure at $\lambda = 1$ (frozen form; design.md §11)

Reused verbatim from §11: $\gamma_k \equiv -\ln(1 - p_k)$,
$\Gamma_2 = N_2\gamma_2$, $\Gamma_1 = N_1\gamma_1$, with $N_2$ the total number
of noisy two-qubit gate applications in the whole circuit at $\lambda = 1$ and
$N_1$ the total number of noisy single-qubit gate applications including the
state-preparation $X$ gates. Define $\Gamma(n) = \Gamma_2(n) + \Gamma_1(n)$ and
the heuristic reference curve $r_{\text{heur}}(n) = e^{-\Gamma(n)}$ (the §11
curve $E(\lambda) \approx E_0 e^{-(\Gamma_2\lambda + \Gamma_1)}$ at
$\lambda = 1$).
**Operationalization on the bundle:** $N_2(n)$ = `cx` and
$N_1(n)$ = `sx + x + sxdg` from `folded_circuits.csv` rows with
`lambda_nominal == 1.0`; the noisy gate classes are exactly
`environment.json` `parameters.noise.two_qubit_gates` and
`parameters.noise.one_qubit_gates`; `rz` is in `clean_gates` and is excluded.
**Assumptions (falsifiable):**

- The $\lambda = 1$ counts are identical across the 8 fold seeds at every
  $n$, because folding at $\lambda = 1$ returns the circuit unchanged
  (design.md §13). R-4 asserts this and stops if it is violated.
- The `sxdg` column is included in $N_1$ whatever its value, since the noise
  model attaches $p_1$ to it (design.md §8).

**Edge cases:** $p_k = 0$ gives $\gamma_k = 0$ exactly; $p_k \to 1$ gives
$\gamma_k \to \infty$ (not in range). **Status:**
§11 calls the curve "a heuristic diagnostic", not a theorem, and
`docs/results-minimal.md` §8 already records that the observed total decay is
roughly half its rate. This quantity is a reference curve only.

### Q5 — Realized and effective scale factors (frozen; design.md §10)

Reused verbatim from §10: $\lambda_r = N_{cx}^{\text{folded}}/N_{cx}^{\text{base}}$
(measured from the folded circuit), and
$$ \lambda_{\text{eff}} = \frac{\Gamma_2\,\lambda_r + \Gamma_1}{\Gamma_2 + \Gamma_1}
\;\le\; \lambda_r, \quad \text{equality at } \lambda_r = 1, $$
with $\Gamma_k$ as in Q4 at the given $n$. **Operationalization:**
$N_{cx}^{\text{folded}}$ = `cx` of the row; $N_{cx}^{\text{base}}$ = `cx` of
the same-$n$ row with `lambda_nominal == 1.0`; rates from `environment.json`.
**Assumptions (falsifiable):**

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

**Quantization (frozen, §10 item 2):** $\lambda_r \in \{1 + m/(5n)\}$;
$\lambda = 1.5$ is exactly achievable only at even $n$.

### Q6 — Seed-ensemble statistics (frozen; design.md §13 uncertainty bullet)

$\bar E_{\text{ZNE}}(n) = \tfrac18\sum_s E^{(s)}_{\text{ZNE}}(n)$;
band $s_n$ = sample standard deviation with `ddof=1`; standard error
$s_n/\sqrt{8}$; per-seed errors $\varepsilon^{(s)}_m(n) = |E^{(s)}_{\text{ZNE}}(n) - E_0(n)|$
and their `ddof=1` standard deviation is the error band, "not obtained by
linearized propagation through the absolute value" (§13). The same formulas
define the shot pipeline's `shot_primary_mean`, `shot_primary_std`,
`shot_primary_sem`, `shot_eps_m`, `shot_eps_m_band` over the eight per-seed
shot intercepts $E^{(s)}_{\text{ZNE,shot}}(n)$, each the degree-one OLS
intercept of the three recorded `expectation_shot` values against their
realized $\lambda_r$ (design.md §10, §11; `linear_intercept` in
`src/zne_scars/zne_runner.py`).

**Assumptions (falsifiable):**

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
  secondary has flagged steps at $n = 34$–$37$ (`docs/results-minimal.md`
  §6); R-6 prints the recorded flag counts.

### Q7 — Post-hoc combined-arm attenuation rate (exploratory, Tier A; not a verdict)

Over the masked steps $\mathcal{M}$ of Q3 with $\ell(n) = \ln r(n)$, the
ordinary least-squares line $\ell(n) \approx a + b\,n$:
$$ b = \frac{\sum_{n\in\mathcal{M}} (n - \bar n)(\ell(n) - \bar\ell)}{\sum_{n\in\mathcal{M}} (n - \bar n)^2}, \qquad
g_{12} = -b, \qquad e(n) = \ell(n) - (a + b\,n). $$

This is the outline §4 primary-metric form applied, post hoc, to the recorded
combined arm $(10^{-3}, 10^{-2})$.

Two values are distinguished everywhere:
the raw fitted rate $\hat g = -b$ exactly as the OLS returns it, and the
policy-treated rate $g$, obtained by the outline's frozen rule (outline §2):
$g = 0$ if $\hat g \in [-10^{-9}, 0)$, otherwise $g = \hat g$. A raw
$\hat g < -10^{-9}$ is not treated; it triggers the "model inadequate —
anti-attenuation" verdict (outline §4) and no rate is used further. R-7
prints both $\hat g_{12}$ and $g_{12}$.

**Assumptions (falsifiable):**

- The single-exponential-in-$n$ form is the §11 heuristic, which §11 flags
  as not generally valid for interleaved local channels. Residual structure
  is therefore expected to be informative, not noise.
- No homoscedasticity or independence of residuals is assumed or needed to
  compute the slope.
- At least 3 masked points.

**Edge cases, pre-declared and implemented in the command in this order:**

- With fewer than 3 masked points, R-7 stops with a message and reports no
  rate, before computing any mean or slope. A two-point line is exactly
  determined and has no residual, and fewer points have no slope at all.
- With any sign flip inside $\mathcal{M}$, R-7 exits with a message naming
  the step and performs no fit.

**Verdict status:** the outline's residual tolerance is not frozen
(outline §4), so no model adequacy verdict can be issued on this or any arm;
R-7 prints the residual summary and says so.

The value of $g_{12}$ is left to R-7 rather than asserted here. It is a
different fitted quantity from the RMS-fitted oracle rates of
`docs/results-minimal.md` §9 (different objective, different domain, masked
versus unmasked) and must not be compared to them as if it were the same
number.

### Q8 — Control-arm rates and the additivity residual (Tier B; no data)

$g_1$ is the Q7 estimator applied to the future $(10^{-3}, 0)$ arm's
$r_1(n)$, and $g_2$ is the same on the future $(0, 10^{-2})$ arm.
$\Delta = g_{12} - (g_1 + g_2)$, where every $g$ entering $\Delta$ is the
policy-treated rate of Q7: a raw $\hat g \in [-10^{-9}, 0)$ becomes 0.
R-B1 and R-B2 print the raw and the treated value side by side and use only
the treated one.

**Assumptions:**

- Each arm passes the outline's adequacy gate (0 < r ≤ 1 + 10⁻⁹ on all
  masked steps).
- The outline's fit-level anti-attenuation verdict does not fire. Quoted
  from outline §§2, 4 exactly: a fitted $g_1 < -10^{-9}$ yields "model
  inadequate — anti-attenuation"; a fitted $g_1 \in [-10^{-9}, 0)$ is
  treated as 0 (the same frozen policy tolerance as the adequacy gate, same
  caveats).
- The same mask on all arms.
- A residual tolerance frozen before any run.
- An additivity criterion $|\Delta| \le \tau_{\text{add}}$ frozen before
  either new arm runs (outline §5).

**Edge cases:** if any arm is "model inadequate", whether by
the pointwise gate, by the fit-level anti-attenuation verdict, or by the
residual-tolerance branch once a tolerance is frozen, there is no $\Delta$.
$g_1^{\text{heur}}$ (outline §2) requires the exact $N_1(n)$, which is
readable today from Q4's operationalization, but its hypothesis intervals
remain provisional. **Status:** $\tau_{\text{add}}$ is not defined by this
draft, and neither $g_1$ nor $g_2$ has any input data. No value or outcome is
predicted.

## 5. Recomputation and verification method

Every Tier A command below is a self-contained `.venv/bin/python -c "..."`
invocation, run from the repository root. Each reads only files under
`results/minimal/` and writes nothing, so the sealed source identity is
untouched. All seven were run on 2026-09-06 against baseline
`1822597ed5e222ac770e0f619d0bfa62e8276c20` with Python 3.12.14 in the pinned
`.venv`, and each exited 0. Any reader of the released repository can re-run
them. The stdout of the 2026-09-06 run is kept as internal provenance at
`.herd/state/task-evidence-20260906/executor/recompute-tierA.log`, which is
not shipped with the release and not needed to verify anything.

Where a command compares a recomputation with a recorded column, it prints
the maximum absolute deviation. A value at floating-point round-off, of
order $10^{-16}$ or exactly 0, confirms that the recorded column is the
stated formula applied to the recorded inputs.

### R-1 — Q1 (FC-1, FC-4): per-step errors, IF, mask

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

### R-2 — Q2: aggregates vs `metrics.json`

```bash
.venv/bin/python -c "import csv,json,math; R=list(csv.DictReader(open('results/minimal/steps.csv'))); m=json.load(open('results/minimal/metrics.json'))
ru=math.sqrt(sum(float(r['eps_u'])**2 for r in R)/len(R)); rm=math.sqrt(sum(float(r['eps_m'])**2 for r in R)/len(R))
print('n_steps',len(R),'rms_u',ru,'rms_m',rm,'gif',ru/rm); print('dev_vs_metrics',ru-m['rms_u'],rm-m['rms_m'],ru/rm-m['gif_value'])"
```

### R-3 — Q3 (FC-2): attenuation ratio and log at all 40 steps with mask marker; degenerate-case report

```bash
.venv/bin/python -c "import csv,math; R=list(csv.DictReader(open('results/minimal/steps.csv'))); out=[]
for r in R:
    n=int(r['n']); e0=float(r['e0_trotter']); en=float(r['e_noisy_dm']); masked=abs(e0)>=0.1
    ratio=en/e0 if e0!=0 else float('nan'); out.append((n,masked,ratio))
inc=[o for o in out if o[1]]; exc=[o[0] for o in out if not o[1]]
print('steps',len(out),'masked_in',len(inc),'masked_out',exc); print('sign_flips_in_mask',sum(1 for o in inc if o[2]<=0),'ratio_gt_1_in_mask',sum(1 for o in inc if o[2]>1+1e-9))
for n,masked,ratio in out: print('n',n,'mask','IN ' if masked else 'OUT','r',ratio,'ln_r',(math.log(ratio) if ratio>0 else 'undefined (r<=0)') if ratio==ratio else 'undefined (E0=0)')"
```

### R-4 — Q4 (FC-2): heuristic exposure at all 40 steps from recorded counts and rates

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

### R-5 — Q5 (FC-3): realized and effective scale vs recorded columns

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

### R-6 — Q6 (FC-4): seed-ensemble statistics, both pipelines (shot intercepts reconstructed), and flag counts

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

### R-7 — Q7 (FC-6, combined arm only): post-hoc OLS rate, raw and policy-treated — exploratory, no verdict

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
g12=0.0 if -1e-9<=g12_raw<0 else g12_raw   # outline s2 frozen policy: raw rate in [-1e-9, 0) treated as 0; raw < -1e-9 would be 'anti-attenuation' (outline s4)
res=[(x,y-(a+b*x)) for x,y in pts]
for x,e in res: print('residual n=%d e=%r'%(x,e))
print('masked_points',k,'g12_raw',g12_raw,'g12_treated',g12,'anti_attenuation_flag',g12_raw<-1e-9,'intercept',a,'max_abs_residual',max(abs(e) for _,e in res),'rms_residual',math.sqrt(sum(e*e for _,e in res)/k),'NOTE: residual tolerance UNFROZEN (prereg outline s4); no verdict')"
```

### R-B1 — Q3/Q8 on the $p_2 = 0$ arm (FC-5) — **CANNOT BE RUN TODAY**

No input exists. The path below does not exist, and only the execution of a
frozen, reviewed preregistration may create it. The command is written out
now so that the method is fixed in advance; substitute the future bundle
path where marked.

```bash
# NOT RUNNABLE TODAY: results/<p2zero-arm>/steps.csv does not exist (no p2 = 0 arm has been executed).
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
g1=0.0 if -1e-9<=g1_raw<0 else g1_raw   # outline s2 frozen policy: raw rate in [-1e-9, 0) is treated as 0
res=[(x,y-(a+b*x)) for x,y in pts]
for x,e in res: print('residual n=%d e=%r'%(x,e))
TAU_RES=None  # residual tolerance: NOT FROZEN (outline s4); must be frozen in the full preregistration before any run
if TAU_RES is not None and max(abs(e) for _,e in res)>TAU_RES: raise SystemExit('model inadequate - residual tolerance exceeded (outline s4)')
print('masked_points',k,'g1_raw',g1_raw,'g1_treated',g1,'max_abs_residual',max(abs(e) for _,e in res),'NOTE: residual tolerance (TAU_RES) and H-G/H-L intervals UNFROZEN; no verdict may be issued')"
```

### R-B2 — Q8 additivity residual (FC-6) — **CANNOT BE RUN TODAY**

No input exists for two of the three rates. The criterion
$\tau_{\text{add}}$ is deliberately left undefined here: outline §5 requires
it to be frozen before either control arm runs, and this draft does not
freeze it.

```bash
# NOT RUNNABLE TODAY: neither results/<p2zero-arm>/ nor results/<p1zero-arm>/ exists; tau_add is not frozen.
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
    g=0.0 if -1e-9<=g_raw<0 else g_raw   # outline s2 frozen policy: raw rate in [-1e-9, 0) is treated as 0
    res=[(x,y-(a+b*x)) for x,y in pts]
    for x,e in res: print('%s residual n=%d e=%r'%(path,x,e))
    if TAU_RES is not None and max(abs(e) for _,e in res)>TAU_RES: raise SystemExit('model inadequate - residual tolerance exceeded (outline s4) in %s'%path)
    print(path,'g_raw',g_raw,'g_treated',g)
    return g
TAU_RES=None  # residual tolerance: NOT FROZEN (outline s4)
TAU_ADD=None  # additivity criterion: NOT FROZEN (outline s5); must be frozen before either control arm runs
g12=rate('results/minimal/steps.csv'); g1=rate('results/<p2zero-arm>/steps.csv'); g2=rate('results/<p1zero-arm>/steps.csv')
D=g12-(g1+g2)
print('g12',g12,'g1',g1,'g2',g2,'Delta',D,'NOTE: TAU_RES and TAU_ADD NOT FROZEN; no adequacy or additivity verdict may be issued')"
```

## 6. Unresolved items

Nothing in this draft resolves, freezes, narrows, or reinterprets any of
the following. They are listed so that a future preregistration knows what
remains open. Items 1, 2, 4, and 5 are provisional analysis choices that
such a preregistration would have to freeze before any run. Item 3 is a set
of policy tolerances that are already frozen and are only reused here. Item
6 is an unresolved finding on the recorded data, and item 7 is a
reproduction question that §0 places out of scope.

1. **The $p_2 = 0$ outline's §2 hypothesis intervals** (H-G: $[0.75, 1.25]$
   of $g_1^{\text{heur}}$; H-L: $[0, 0.50)$; "neither" otherwise) are
   provisional and unfrozen; they "must be frozen (with justification) in the
   full preregistration before any data are seen" (outline §2).
2. **The outline's §4 residual tolerance** for the $\ln r(n)$ fit is
   "explicitly not yet a freezable analysis plan". Until it is frozen, no run
   under the outline can produce a valid H-G/H-L verdict, and Q7's residual
   summary on the recorded arm is likewise verdict-free.
3. **The $10^{-9}$ policy tolerances** are frozen policy choices made for
   determinism, not derived error bounds (outline §4). In the outline's own
   words: the adequacy gate fires on $r(n) \le 0$ or $r(n) > 1 + 10^{-9}$ on
   any masked step. The fit-level verdict fires on a fitted $g_1 < -10^{-9}$
   ("model inadequate — anti-attenuation"), while $g_1 \in [-10^{-9}, 0)$ is
   treated as 0. This draft reuses these for reporting only, derives nothing
   from them, and does not redefine, tighten, or move any endpoint.
4. **The additivity criterion** $\tau_{\text{add}}$ for any factorial
   apportionment claim must be frozen before either new arm runs
   (outline §5). This draft names the quantity $\Delta$ and does not freeze
   the criterion.
5. **The mask threshold** $|E_0| \ge 0.1$ is the outline's provisional
   choice; it is used here for display and diagnostics only.
6. **The heuristic's $\Gamma_1$ floor arithmetic** remains unresolved on the
   recorded data (`docs/results-minimal.md` §8), and FC-2 does not resolve it.
7. **The open cross-platform reproduction question** recorded on 2026-09-06 in
   the dated annotation of `docs/ci-reproduction-assessment.md` is out of
   scope here and receives no chart, experiment, or diagnosis in this draft.

No future verdict is stated, implied, expected, or predicted for any Tier B
item. About future arms this draft says only what data they would need and
how the pre-declared gates would be applied.

## 7. Traceability matrix

| ID | Tier | Quantity | Source file(s) | Exact column(s)/key(s) | Formula ref (section in this doc) | Governing frozen definition (design.md / results-minimal.md section) | Recomputation command ref | Runnable today? (Y/N + why not) |
|---|---|---|---|---|---|---|---|---|
| FC-1 | A | Per-step $\mathrm{IF}(n)$ with reportability and lower-bound flags, both pipelines | `results/minimal/steps.csv`; `results/minimal/metrics.json` | `n`, `if_value`, `if_is_lower_bound`, `reportable`, `shot_if_value`, `shot_if_is_lower_bound`, `shot_reportable`; `if_wins`, `reportable_steps_m`, `excluded_steps` (+ `shot_pipeline.*`) | §4 Q1 | design.md §13 (IF, ε_min filter, δ handling, saturation bullet) | R-1 (both pipelines) | Y |
| FC-2 | A | $r(n)$, $\ln r(n)$ vs heuristic $e^{-\Gamma(n)}$, provisional mask | `results/minimal/steps.csv`; `results/minimal/folded_circuits.csv`; `results/minimal/environment.json` | `n`, `e0_trotter`, `e_noisy_dm`; `n`, `lambda_nominal`, `cx`, `sx`, `x`, `sxdg`; `parameters.noise.p1`, `parameters.noise.p2` | §4 Q3, Q4 | design.md §11 (heuristic, γ_k, Γ_k); results-minimal.md §8 (discrepancy); mask: prereg outline §4 (unfrozen) | R-3 (all 40 steps: $r$, $\ln r$ where defined, mask marker), R-4 (all 40 steps: $N_1$, $N_2$, $\Gamma$, $e^{-\Gamma}$) | Y |
| FC-3 | A | $\lambda_r - \lambda_{\text{nominal}}$ and $\lambda_{\text{eff}} - \lambda_r$ per (n, seed, λ) | `results/minimal/folded_circuits.csv`; `results/minimal/environment.json` | `n`, `fold_seed`, `lambda_nominal`, `lambda_r`, `lambda_eff`, `cx`, `sx`, `x`, `sxdg`; `parameters.noise.p1`, `parameters.noise.p2` | §4 Q5 | design.md §10 (λ_r, λ_eff, quantization grid); §20 M2-6 (degenerate case) | R-5 | Y |
| FC-4 | A | Per-seed $\varepsilon^{(s)}_m(n)$, central $\varepsilon_m(n)$, seed-spread band, shot SD/SEM/band (shot intercepts reconstructed) | `results/minimal/seed_arms.csv`; `results/minimal/steps.csv`; `results/minimal/shot_values.csv`; `results/minimal/folded_circuits.csv` | `n`, `fold_seed`, `primary_intercept`; `n`, `e0_trotter`, `eps_m`, `eps_m_band`, `zne_primary_mean`, `zne_primary_std`, `shot_primary_mean`, `shot_primary_std`, `shot_primary_sem`, `shot_eps_m`, `shot_eps_m_band`; `shot_values.csv`: `n`, `fold_seed`, `lambda_nominal`, `expectation_shot`; `folded_circuits.csv`: `n`, `fold_seed`, `lambda_nominal`, `lambda_r` | §4 Q1, Q6 | design.md §13 (uncertainty bullet); results-minimal.md §6 (density-matrix spread is not statistical error; shot spread includes sampling variation; neither a confidence interval) | R-1, R-6 | Y |
| FC-5 | B | $\ln r_1(n)$ and residuals on the $p_2 = 0$ arm | future `results/<p2zero-arm>/steps.csv` (does not exist); `results/minimal/steps.csv` for the reference $E_0$ | future `n`, `e0_trotter`, `e_noisy_dm`; recorded `e0_trotter` | §4 Q3, Q8 | prereg outline §§3–5 (mask threshold, hypothesis intervals, residual tolerance unfrozen; the $10^{-9}$ gate and anti-attenuation tolerances frozen as policy choices, not derived bounds); design.md §16 bundle format | R-B1 (prints per-step residuals; anti-attenuation branch included; residual-tolerance branch present but inert until a tolerance is frozen) | N: the $(10^{-3}, 0)$ arm has never been executed; no data, no code, no frozen preregistration |
| FC-6 | B | $g_1, g_2, g_{12}$ and $\Delta = g_{12} - (g_1 + g_2)$ | future `results/<p2zero-arm>/steps.csv` and `results/<p1zero-arm>/steps.csv` (neither exists); `results/minimal/steps.csv` | `n`, `e0_trotter`, `e_noisy_dm` in each | §4 Q7, Q8 | prereg outline §5 (factorial, additivity criterion unfrozen); design.md §11 | R-7 ($g_{12}$ only), R-B2 (per-arm gate, anti-attenuation, and residual branches specified; residual and additivity criteria inert until frozen) | N: two of four factorial cells have no data; $\tau_{\text{add}}$ not frozen |
| Q1 | A | $\varepsilon_u$, $\varepsilon_m$, $\mathrm{IF}$, reportable mask (both pipelines) | `results/minimal/steps.csv`; `results/minimal/environment.json` | `e0_trotter`, `e_noisy_dm`, `zne_primary_mean`, `eps_u`, `eps_m`, `if_value`, `if_is_lower_bound`, `reportable`, `shot_baseline_mean`, `shot_primary_mean`, `shot_eps_u`, `shot_eps_m`, `shot_if_value`, `shot_if_is_lower_bound`, `shot_reportable`; `parameters.eps_min`, `parameters.delta_density_matrix`, `parameters.delta_shot` | §4 Q1 | design.md §13 | R-1 | Y |
| Q2 | A | $\mathrm{RMS}_u$, $\mathrm{RMS}_m$, $\mathrm{GIF}$ | `results/minimal/steps.csv`; `results/minimal/metrics.json` | `eps_u`, `eps_m`; `rms_u`, `rms_m`, `gif_value`, `gif_is_lower_bound` | §4 Q2 | design.md §13 (all-40-step aggregates) | R-2 | Y |
| Q3 | A | $r(n)$, $\ell(n) = \ln r(n)$, mask $\mathcal{M}$ | `results/minimal/steps.csv` | `n`, `e0_trotter`, `e_noisy_dm` | §4 Q3 | prereg outline §4 (mask threshold 0.1 provisional and unfrozen; the gate's $10^{-9}$ a frozen policy tolerance, not a derived bound); design.md §13 (E_noisy seed-independent) | R-3 (all 40 steps with mask marker) | Y |
| Q4 | A | $\gamma_k$, $\Gamma_1(n)$, $\Gamma_2(n)$, $\Gamma(n)$, $e^{-\Gamma(n)}$ | `results/minimal/folded_circuits.csv`; `results/minimal/environment.json` | `n`, `lambda_nominal`, `cx`, `sx`, `x`, `sxdg`; `parameters.noise.p1`, `parameters.noise.p2`, `parameters.noise.one_qubit_gates`, `parameters.noise.two_qubit_gates`, `parameters.noise.clean_gates` | §4 Q4 | design.md §11 (definitions), §8 (noisy gate classes) | R-4 | Y |
| Q5 | A | $\lambda_r$, $\lambda_{\text{eff}}$ | `results/minimal/folded_circuits.csv`; `results/minimal/environment.json` | `n`, `fold_seed`, `lambda_nominal`, `lambda_r`, `lambda_eff`, `cx`, `sx`, `x`, `sxdg`; `parameters.noise.p1`, `parameters.noise.p2` | §4 Q5 | design.md §10; §20 M2-6 | R-5 | Y |
| Q6 | A | Seed mean, `ddof=1` SD, SEM, per-seed error band (both pipelines; shot intercepts reconstructed), flag/mode counts | `results/minimal/seed_arms.csv`; `results/minimal/steps.csv`; `results/minimal/shot_values.csv`; `results/minimal/folded_circuits.csv` | `n`, `fold_seed`, `primary_intercept`, `clamp_flag`, `secondary_avoid_log_failed`, `shot_clamp_flag`, `shot_secondary_avoid_log_failed`; `zne_primary_mean`, `zne_primary_std`, `eps_m_band`, `shot_primary_mean`, `shot_primary_std`, `shot_primary_sem`, `shot_eps_m`, `shot_eps_m_band`, `shot_secondary_mode`, `shot_secondary_estimate`; `shot_values.csv`: `n`, `fold_seed`, `lambda_nominal`, `expectation_shot`; `folded_circuits.csv`: `n`, `fold_seed`, `lambda_nominal`, `lambda_r` | §4 Q6 | design.md §13 (uncertainty bullet), §11 (clamp policy), §20 M3-3 (failed-fit policy); results-minimal.md §6 | R-6 | Y |
| Q7 | A | $g_{12}$ (post-hoc OLS rate on the combined arm), residuals | `results/minimal/steps.csv` | `n`, `e0_trotter`, `e_noisy_dm` | §4 Q7 | prereg outline §4 (estimator form; residual tolerance unfrozen, so no verdict) and §2 (frozen $[-10^{-9}, 0) \to 0$ treatment, applied to the reported rate); design.md §11 (heuristic status) | R-7 (guards: <3 masked points, not reported; sign flip, no fit; prints raw and policy-treated rate, per-step residuals) | Y (as an exploratory diagnostic only; no verdict possible) |
| Q8 | B | $g_1$, $g_2$, $\Delta$, $\tau_{\text{add}}$ | future `results/<p2zero-arm>/steps.csv`, `results/<p1zero-arm>/steps.csv` (neither exists); `results/minimal/steps.csv` | `n`, `e0_trotter`, `e_noisy_dm` in each | §4 Q8 | prereg outline §§2, 4, 5. Unfrozen: the H-G/H-L/neither hypothesis intervals, the residual tolerance, the additivity criterion $\tau_{\text{add}}$. Frozen as policy choices, not derived bounds: the $10^{-9}$ adequacy-gate tolerance and the $-10^{-9}$ anti-attenuation boundary with its $[-10^{-9}, 0) \to 0$ treatment | R-B1, R-B2 (both print raw and policy-treated rates) | N: no control-arm data exist; criterion not frozen |
