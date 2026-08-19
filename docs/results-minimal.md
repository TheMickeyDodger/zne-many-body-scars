# Results: Minimal Experiment (design.md §15)

**Status:** M3 deliverable. All numbers below come from `results/minimal/` (bit-reproducible: three independent executions — two by the implementer, one by the project lead from a clean state — produced sha256-identical output files; recorded in `docs/review-package.md` §2). Figure: `figures/minimal_experiment.{png,pdf}`, regenerated from `results/minimal/steps.csv` only.

## 1. What was run

Exactly the configuration recorded in `results/minimal/environment.json` — design §15 with no deviations: $L=6$ MFIM ($V=1$, $\Omega=0.24$), first-order Trotter at $\Delta t = 1$ for $n = 1,\dots,40$, basis $\{rz, sx, x, cx\}$ at `optimization_level=0` with `seed_transpiler=7`, two-tier depolarizing noise ($p_1 = 10^{-3}$ on $sx/sxdg/x$, $p_2 = 10^{-2}$ on $cx$, $rz$ clean), fold seeds 1000–1007 with `fidelities={"single": 1.0, "double": 0.99}`, $\lambda \in \{1.0, 1.5, 2.0\}$, LinearFactory primary on realized $\lambda_r$ with the nominal-$\lambda$ and $\lambda_{\text{eff}}$ arms alongside, ExpFactory(asymptote=0.0) secondary, plus the seeded 8192-shot secondary pipeline (`seed_simulator = 9000 + 100n + 10k + j`). `environment.json` records the complete frozen environment (full pip-freeze package list, Python version, platform/BLAS) and a **source-tree identifier**: a sha256 content hash over the sorted files of `src/`, `scripts/`, `pyproject.toml`, and `requirements.txt` — a content hash, not a VCS revision, because no commit existed when the experiment was recorded and creating one was outside the experiment's scope; the hash identifies the exact source that ran, regardless of any later VCS history. per-step values in `steps.csv`; per-seed intercepts and clamp flags in `seed_arms.csv`; per-(n, seed, λ) realized $\lambda_r$ and folded instruction counts in `folded_circuits.csv`; raw shot values in `shot_values.csv`.

## 2. Pre-registered verdict (§13, density-matrix primary)

From `metrics.json`:

| Quantity | Value |
|---|---|
| $\mathrm{RMS}_u$ (all 40 steps) | 0.32080 |
| $\mathrm{RMS}_m$ (primary arm, all 40 steps) | 0.25107 |
| $\mathrm{GIF}$ | **1.2777** (point value, not a lower bound) |
| Reportable steps $m$ (baseline-relevance filter $\varepsilon_u \ge 0.01$) | 39 |
| Steps excluded by the filter | $n = 34$ only |
| Steps with $\mathrm{IF}(n) > 1$ among the 39 | **39** |
| Majority clause (wins $> m/2$) | pass |
| **Verdict** | **PASS** — GIF $> 1$ and IF $> 1$ on 39/39 reportable steps |

The full per-step table (all 40 steps, no subset) is `results/minimal/steps.csv`. Per-step IF ranges from 0.145 (at the excluded step $n=34$) to 20.17 (at $n=4$) among all steps.

**The one step where ZNE increased the error, reported plainly:** at $n = 34$ the unmitigated error was already negligible ($\varepsilon_u = 0.0024$, below $\varepsilon_{\min} = 0.01$) because the noisy and noiseless curves nearly coincide near a zero crossing of the oscillation ($E_0 = +0.016$, noisy $= +0.019$); the primary estimate landed at $\varepsilon_m = 0.0166$ (IF $= 0.145$). This step is excluded from the majority test by the *pre-registered* filter — the filter was not adjusted after seeing results, and the step is shown in every table and figure.

## 3. Where ZNE helped, hurt, or did neither

- **Early steps ($n \lesssim 5$):** largest relative gains — IF between 1.9 and 20.2 (peak at $n=4$: $\varepsilon_u = 0.0249 \to \varepsilon_m = 0.0012$).
- **Moderate depth ($n = 6$–$30$):** improvement at every step, IF between 1.09 (at the oscillation node $n=25$) and 2.56 (at $n=7$); e.g. $n=10$: $\varepsilon_u = 0.315 \to \varepsilon_m = 0.142$ (IF 2.22).
- **Late steps ($n \gtrsim 35$):** IF declines toward 1 (1.04 at $n=35$, 1.11 at $n=40$) — the saturation regime, §5 below.
- **Hurt:** only the filtered step $n = 34$ (above).

## 4. The three linear arms and the secondary

RMS absolute errors over all 40 steps, computed from `steps.csv` columns:

| Estimator | RMS error vs $E_0$ |
|---|---|
| Unmitigated | 0.32080 |
| Primary (linear on realized $\lambda_r$) | 0.25107 |
| Nominal-$\lambda$ comparison arm | 0.25103 |
| $\lambda_{\text{eff}}$ diagnostic arm | 0.24303 |
| **Secondary, ExpFactory(asymptote = 0)** | **0.07349** |

Three observations, all consistent with the design's own analysis:

1. **The pre-registered secondary strongly outperforms the linear primary** (RMS 0.073 vs 0.251): the exponential estimator, under its *imposed* zero asymptote, fit these data much better than the linear one — the misspecification direction §11's heuristic anticipated (a linear extrapolant under-recovering, with bias toward zero growing with depth). This is a statement about estimator fit on these data, not about the true response shape or asymptote, which three scale factors cannot establish (§11). The verdict above nonetheless remains the pre-registered primary's — the linear factory was chosen for source fidelity and that choice is not revised after the fact; the secondary's performance is reported as a finding, and it was pre-registered too, so this is not a post-hoc selection. No secondary fit was clamp-flagged at any step ( `seed_arms.csv`: all flags 0); every step used log mode.
2. **The $\lambda_{\text{eff}}$ arm is modestly better than the $\lambda_r$ arm** (0.243 vs 0.251), the direction §10 predicts (its heuristic intercept is $E_0$ rather than $E_0 e^{-\Gamma_1}$); the effect is small because the unscaled single-qubit exposure is a small fraction of the total under these rates.
3. **Primary vs nominal arms differ only in the third-or-later decimal** (they use identical data; their abscissas differ only at odd $n$, where $\lambda = 1.5$ is off-grid and the realized abscissa is $\lambda_r = 1.5 \pm 1/(10n)$ — recorded per (n, seed, λ) in `folded_circuits.csv`).

## 5. The late-$n$ regime vs the §11/§13 predictions

Observed, from `steps.csv`: the noisy and mitigated values are attenuated toward zero while $E_0$ keeps oscillating at $O(1)$; both errors saturate toward $|E_0(n)|$ (at $n = 40$: $E_0 = -0.541$, noisy $= -0.058$, primary $= -0.105$, $\varepsilon_u = 0.483$, $\varepsilon_m = 0.436$) and IF $\to$ 1.04–1.11 — matching §13's saturation bullet and §18(2). Per §13, in this regime the metrics cannot distinguish a ZNE failure from the absence of remaining signal, so no claim is made either way beyond the recorded numbers. The secondary's much larger late-$n$ recovery (e.g. $-0.451$ of $E_0 = -0.541$ at $n=40$) is visible in the figure but is equally subject to that caveat.

## 6. Uncertainty labels

The density-matrix pipeline is **exact under the noise model**: expectation values carry zero sampling variance. The $\pm 1$ sd band on the ZNE curves is **folding-configuration spread across the 8 seeds** (ddof=1), not statistical error; it is small throughout (primary-arm sd between $3\times10^{-5}$ at $n=1$ and $3.9\times10^{-3}$ at $n=10$).

**Shot pipeline (8192 shots, seeded per §16) — the full §13 secondary, reported alongside the primary, not replacing it.** Per step, `steps.csv` records the $\lambda=1$ baseline (mean of the eight seeded executions with ddof=1 sd, e.g. $n=20$: sd $= 0.0072$), all three linear arms ($\lambda_r$ primary, nominal, $\lambda_{\text{eff}}$) with ddof=1 sd and standard error (sem $0.0014$ at $n=1$ to $0.0062$ at $n=37$), the ExpFactory secondary with its per-step mode, the per-seed error band, and per-step IF with lower-bound flag and reportability (the per-seed shot clamp flags and both per-seed fit modes are in `seed_arms.csv`). Shot aggregates and verdict, from `metrics.json`: $\mathrm{RMS}_u = 0.32063$, $\mathrm{RMS}_m = 0.25100$, GIF $= 1.2774$ (point value), $m = 39$ (only $n=34$ excluded), IF $> 1$ on 39/39 reportable steps — **shot verdict: PASS**, consistent with the density-matrix primary's.

**Shot-secondary fit failures, disclosed:** on the near-zero shot data at $n = 34$–$37$ the exponential secondary was clamp-flagged (9 seed-level flags), switching those steps to `avoid_log` mode per §11; at $n = 36$–$37$ the nonlinear fits converged, but at $n = 34$–$35$ four seed-level `avoid_log` fits raised mitiq's `ExtrapolationError` (non-convergence). Per the recorded policy (design §20 M3-3), those steps' shot-secondary estimates are marked `avoid_log_failed` and left empty — never substituted or partially averaged. The density-matrix secondary is unaffected (zero clamp flags, zero failures, all 40 steps in log mode).

## 7. What this does NOT show (per design §14(d))

Nothing about real hardware: no IBM-device, pulse-level, coherent-error, crosstalk, readout, $T_1/T_2$, or drift claims — none of these are modeled. No claim that ZNE "works for QMBS on hardware". No claims beyond $L = 6$, this observable ($\langle Z_\pi\rangle/L$), this noise channel (two-tier gate-attached depolarizing), these rates, this folding policy, this scale-factor set, or this seed ensemble. No analytic claim about the true functional form of $E(\lambda)$ — the arm and secondary comparisons are fitted estimates under the two pre-registered models. The secondary's advantage here is a statement about *this simulated noise model* and these data only: the pre-registered exponential estimator fit these data better than the linear one. No claim is made about the true functional form of $E(\lambda)$ or about the asymptote — three points with an *imposed* asymptote cannot verify it — and none of this transfers to hardware noise.

## 8. Discrepancy from expectation, preserved and explained

**The observed decay is roughly half the §11 heuristic's rate.** The global-depolarizing heuristic predicts per-step attenuation $e^{-(10\gamma_2 + \sim 12\gamma_1)} \approx e^{-0.113}$ per step; the recorded data give noisy/$E_0$ ratios of 0.608 at $n=10$, 0.337 at $n=20$, 0.184 at $n=30$ — i.e. $\approx e^{-0.050}$ to $e^{-0.056}$ per step. This is **consistent with** the locality misspecification §11 itself flags — interleaved *local* depolarizing channels need not contract a sum of single-site observables at the global-exposure rate (a two-qubit channel only touches its own support) — but these data do not isolate the mechanism: the observed quantity is *total* attenuation, and neither implementation effects nor the split between one- and two-qubit contributions is excluded by this run alone. The factor of $\approx 2$ therefore applies to **observed total attenuation only**; the §11 single-qubit floor arithmetic (the $\Gamma_1$-based magnitude estimate) is left explicitly unresolved — a control run with $p_2 = 0$, which isolates the single-qubit exposure's contraction of $Z_\pi$, would settle it. The heuristic's qualitative expectations (a decaying response in $\lambda$, the linear-fit bias toward zero, late-$n$ saturation) are consistent with the recorded data; its imposed zero asymptote is a modeling choice these data cannot verify. No parameters were changed in response to this observation.

## 9. Post-hoc diagnostics: oracle counterfactuals (review-requested; NOT pre-registered)

These diagnostics were computed after the review, from `steps.csv` only, and are labeled post hoc; they qualify — in both directions — how much of the §2 verdict reflects genuine extrapolation. All are recomputable from the recorded columns with the stated definitions.

**Constant-rescale oracle.** Fit a single constant $c$ by least squares against $E_0$ itself (i.e. the oracle *cheats*: $c = \sum_n E_{\text{noisy}} E_0 / \sum_n E_{\text{noisy}}^2 = 1.6024$) and score $c \cdot E_{\text{noisy}}$ with the §13 metrics: RMS $= 0.27327$, GIF $= 1.1739$, IF $> 1$ on 34/39 reportable steps. Two readings, both true:

- (a) The metric substantially rewards amplitude restoration: about **68% of the primary's RMS reduction** is available to this trivial oracle (oracle 14.8% RMS reduction vs ZNE 21.7%), so "IF $> 1$ on 39/39 steps" overstates how much genuine extrapolation contributes per step.
- (b) The primary nonetheless **beats the oracle** (GIF 1.278 vs 1.174; 39/39 vs 34/39 wins) while using only noisy data at three scale factors and never seeing $E_0$ — the improvement is not purely an amplitude-restoration artifact.

**Exponential-undo oracles (calibrate the secondary).** Convention for every fitted number below, stated so a reader can recompute from `steps.csv`: direct RMS minimization of the oracle prediction against $E_0$ over the named steps, no mask; for each candidate rate $g$ (grid over $[0, 0.15]$, locally refined) the amplitude $c$ (where present) is the closed-form OLS solution; scored with the §13 RMS/GIF definitions.

- *One parameter* ($E_{\text{noisy}} e^{gn}$, all 40 steps): $g = 0.0563$/step, RMS $= 0.05367$, GIF $= 5.98$.
- *Two parameters* ($c\,e^{gn} E_{\text{noisy}}$, all 40 steps): $c = 0.9219$, $g = 0.0595$/step, RMS $= 0.04845$, GIF $= 6.62$ — **better than the pre-registered secondary** (GIF 4.37).
- *Held-out variant* (the more meaningful one, since the null never sees the steps it is scored on): fit $(c, g)$ on $n \le 20$ ($c = 0.9507$, $g = 0.0565$), score on $n = 21$–$40$: oracle GIF $= 5.22$ vs the secondary's GIF $= 3.96$ on the same test window.

The conclusion that survives regardless of fitting convention: **a two-parameter trivial oracle, fitted against the answer, outperforms the pre-registered secondary** — so no lower-bound claim, and no claim about where a non-cheating estimator "must sit", can be made from these oracles (an earlier draft made that claim; it was wrong and is withdrawn). The honest reading stands: all of these oracles use $E_0$, which a real experiment never has; what they bound is how much of the apparent improvement is explainable by simple amplitude/decay restoration — and that share is large, for the secondary as well as for the primary.

## Reproduction

```
# into a FRESH directory (the default; both scripts refuse both frozen canonical
# directories, results/minimal/ and figures/, as output targets — by filesystem
# identity, adding files included — without --allow-canonical-overwrite):
.venv/bin/python scripts/run_minimal.py --out results/repro
# executable comparison against the canonical bundle: exits non-zero on genuine
# mismatch; detects and reports same-platform (byte identity of the five data
# files; environment.json differs only in documented provenance/tooling fields)
# vs off-platform (1e-12 numeric agreement) — expectations itemized in README §4:
.venv/bin/python tools/verify_reproduction.py --canonical results/minimal --repro results/repro
.venv/bin/python scripts/make_figures.py --results results/repro --out figures-repro
```
The run completes in a few minutes on a laptop (timing is stdout-only and deliberately not part of the recorded outputs). A second, independent run was executed into a separate directory at the time of the original work and verified byte-identical (sha256) against `results/minimal/`; the identity is recorded in `docs/review-package.md` (§1 inventory row and §2 determinism row), and the byte-identical copy itself was deliberately not committed — an identical duplicate adds no information.
