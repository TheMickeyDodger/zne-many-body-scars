# Phase 2 Analysis and Output Contract

**Status (as written 2026-09-07, historical):** contract for the Phase 2
preregistration (`docs/prereg-phase2.md`), written 2026-09-07 against
baseline `657683c09459b9289a07dab0b27497882a5c819f`. Nothing described here
has been executed. No Phase 2 code exists. Every artifact path below is a
path a future implementation must produce; none exists today. The only
things that run today are the offline checker and its tests (§C8,
"runnable today").

**Status update, 2026-09-08 (A-1). HISTORICAL: written before A-2 and the pilot acquisition; every "no Phase 2 data" statement in this paragraph was true on its date and is superseded by the current-status paragraph that follows. Original wording kept.** Amendment A-1 (below; recorded in the JSON `amendments`) is human-approved and pre-data. A fresh canonical read-only review of the amended artifacts is pending; implementation and the measured feasibility pilot resume only after that approval. What exists today: the offline Phase 2 environment `.venv-phase2` (pins in `requirements-phase2.txt`, identical to `requirements.txt`) and unexecuted scaffolding under `phase2/` (identity, contract access and observable-weight modules; no simulator, estimator or bootstrap code has run). No Phase 2 scientific execution of any kind has taken place: no `results/phase2*` bundle, no `figures-phase2*` root, no Aer execution, no fit, no bootstrap; `results/minimal/` is byte-identical to the baseline. No IBM workload has been submitted or prepared. Every
artifact path in §C2 still names a file that does not exist.

**Current status (2026-09-08, after A-2 and its correction; supersedes the paragraph above).** No CONTRACTED Phase 2 scientific result exists: no contracted `results/phase2*` bundle, no `figures-phase2*` root, no bootstrap, and `results/minimal/` is byte-identical to the baseline. Real Phase 2 execution HAS occurred outside any contracted result: Aer timing, method-selection and seed-determinism probes (evidence `1b-01`), and a separately labelled pilot acquisition `results/phase2-pilot` that executed Aer and produced folded circuits, raw density-matrix values and raw shot records for 17 completed of 162 work units under the pre-A-2 `phase2` source before it was stopped; it is quarantined, identity-mismatched with the current source, and its values are never used. `phase2/` holds estimator, simulation and pilot code that has run in tests and in that pilot. No IBM workload has been submitted or prepared. The corrected A-2 candidate was ACCEPTED on 2026-09-08 (independent review round 06 approved it; accepted `phase2` source identity `b7937c07302640fd9949c55f3cbddbc5415937caa76e78041021e65bed219f2b`). Feasibility of the full matrix is unassessed, and the during-run monitoring method carries a documented production NO-GO.

**Authority.** `tools/phase2_contract.json` is the single source of truth
for every constant, matrix cell, schema, chart, equation and entrypoint.
This document renders and explains that content; `tools/phase2_contract_check.py`
checks that the JSON, this document and the preregistration agree.

**Amendment A-1 (2026-09-08, pre-data, human-approved).** Before any Phase 2
data existed, the independent read-only review of task
20260908-105435-177fe7 returned a canonical `REJECT` because §C4.2 of this
document (and the checker's reference implementations) required two
distinct abscissas for a Phase 2B `EXP` fit while prereg §4.3 required
three, and the JSON stated no Phase 2B value. The human decision, recorded
as `amendments[A-1]` in the JSON, fixes the Phase 2B `EXP` minimum at
**three** distinct realized abscissas everywhere in Phase 2B (§C4.2,
`phase2b.rank_rule`, constant C-EXP-MIN-2B) and keeps the Phase 2C minimum
at **two** (prereg §5.4, `phase2c.transpilation.rank_rule`, C-EXP-MIN-2C);
the checker's `EXP` reference functions now take the phase minimum as a
required parameter and are exercised at both values (§C7). Nothing else
changed. The pre-amendment identities are historical and retained in the
JSON record (this document
`97e67e68e0368c621393af118b7c0dc1f8f2018c04c9cfd0eef01c01ab14cdeb`; the
preregistration, JSON, checker and tests as listed there). The original
`REJECT` stands as the record that triggered the amendment.

**Amendment A-2 (2026-09-08, human-approved; approval precedes the affected
analyses).** Recorded as `amendments[A-2]` in the JSON: (1) `EXP` sign =
`np.sign(-(a - numpy.polyfit intercept))`, zero at equality, in both modes
(§C4.3 step 2; the checker's former `>= 0` ternary at that site and its
closed-form intercept are replaced by the pinned convention, and the two
modes now agree); (2) fewer than $k_{\min} = 3$ masked steps → every Phase 2A
statistic null, `TOO_FEW_POINTS`, `INCONCLUSIVE` (§C4.1 step 4); (3) DM
companion seed range defined in §C4.4 item 7 (amplitude at the
aggregate-matched step over all seeds, timing from each seed's own matched
peak in the same window, any undefined required seed nulls the whole range).
The exact primary tail probability $1/9600$ replaces the rounded
$1.0417\times10^{-4}$ wherever a number is computed (§C4.5). Scope
qualifier: no disputed `EXP` fit, small-mask statistic or DM seed-range
analysis had run at approval, but real Aer probes and a separately
labelled, quarantined pilot acquisition (`results/phase2-pilot`) had
already produced circuits, raw measurements and pilot data. Pre-A-2
identities are retained in the JSON record.

**Correction to A-2 (2026-09-08, after an independent review rejected
the first A-2 candidate; recorded as `amendments[A-2].correction_20260908`).**
The implementation's `EXP` sign is the scalar `numpy.polyfit` call for every
element: a closed-form fast path with a guard band was removed, because the
closed-form and the `numpy.polyfit` intercepts disagree in sign on clustered
realized abscissas within the admitted domain, and no equivalence is
claimed. After review round 05 the `EXP` log-mode fit is likewise the
pinned scalar `numpy.polyfit(x, ln(shifted), 1, w=sqrt(shifted))` call for
every element (§C4.3 step 2), replacing closed-form normal equations that
gave a different unclamped value on clustered abscissas; the `LIN`/`QUAD`
intercepts remain ordinary least squares as specified. Every non-finite required DM companion seed value (`NaN`,
$\pm\infty$) is undefined exactly like a missing one (§C4.4 item 7), in the
reference checker and the implementation alike. The rules of A-2 are
unchanged; only their implementation and its tests were corrected.

**Sections.** C1 scope and conventions. C2 artifact schemas. C3 equation
registry. C4 estimator algorithms. C5 chart inventory. C6 manifest and
provenance. C7 offline checker and its fixtures. C8 entrypoints and the
one-command reproduction contract. C9 traceability matrix. C10 edge-case
policy index.

---

## C1. Scope and conventions

### C1.1 Directory layout of a Phase 2 bundle

```
results/phase2/                  the bundle root (any results/<name>, name not "minimal")
├── environment_phase2.json      one environment record (B-ENV)
├── manifest.json                sha256 of every file, raw inputs listed separately (T-MAN)
├── provenance.json              identities and run log (T-PROV)
├── deviations.md                explicit deviation record, never empty (T-DEV)
├── phase2a/                     Phase 2A artifacts (A-*)
├── phase2b/                     Phase 2B artifacts (B-*)
└── phase2c/                     Phase 2C artifacts (C-*)
figures-phase2/                  every chart, png and pdf (§C5); a sibling of figures/, never inside it
```

`results/minimal/` and the canonical `figures/` directory are v0.1.0
evidence. They are never written by any future entrypoint, and adding a
file or a subdirectory inside `figures/` counts as writing, exactly as the
v0.1.0 canonical guard treats it (design.md §20 A2-3). Phase 2 figures
therefore live beside `figures/`, in `figures-phase2/` (and
`figures-phase2-repro/` for a reproduction), under the bundle and
output-root policy of §C6 item 6.

### C1.2 Column conventions

- **dtype**: `int`, `float`, `str`, `bool`, or a JSON container type.
- **units**: physical or logical units; "observable units" means the
  observable's own dimensionless scale (prereg §4.5); "steps" means
  Trotter steps, equal to $Vt$.
- **null policy**: `never null`, or the exact condition under which the
  cell is empty. An empty CSV cell is the only null representation; no
  sentinel numbers are ever written. Every null is accompanied by a flag
  in the row's `flags` column or by a status column that explains it.
- **flags**: a semicolon-separated list of flag names from the
  preregistration's vocabularies (prereg §3.8, §4.6, §4.8, §6.7); the
  empty string means no flag.
- **bit ordering**: every `outcome` string is Qiskit-ordered; site $i$ is
  bit $b_{i-1}$ counted from the right (design.md §4).
- **identifiers**: `cell_index` is the row index of
  `phase2b.matrix_cells` / `control_cells` in the JSON; `obs` is one of
  `ZPI`, `PRET`, `MLOC`, `CZZ`, `M_I`, `M_J`, `M_IJ` (the last three are the
  raw moments $\langle Z_{i^*}\rangle$, $\langle Z_{i^*+1}\rangle$,
  $\langle Z_{i^*}Z_{i^*+1}\rangle$); `extrapolator` is `LIN`, `QUAD`,
  `EXP`, or `NONE` for the unmitigated curve; `pipeline` is `DM` or `SHOT`.

### C1.3 Kinds of artifact required by the task

| Kind | Artifacts |
|---|---|
| raw observations | A-CELLS, A-REF, B-REF, B-RAWDM, B-RAWSHOT, C-RAW |
| chart-input tables | B-MIT, C-MIT (plus every metrics table below) |
| processed metrics | A-INT, A-SEC, A-VERD, B-STEPMET, B-PEAKMET, B-CURVEMET, B-END, B-COND, B-BOUND, B-DIST, C-END, C-VERD |
| bootstrap samples / deterministic uncertainty | B-BOOTPEAK, C-BOOTPEAK (every peak-level replicate); per-step quantiles in B-MIT, C-MIT; A-INT bound columns; replay from seeds (§C4.7) |
| fit diagnostics | A-RES, A-DENSE, B-SEEDFIT, C-SEEDFIT, C-IDEAL |
| circuit and transpilation records | A-CIRC, B-FOLD, C-QPY, C-DUR |
| calibration snapshot | C-CALPRE, C-CALPOST, C-BSEL |
| usage estimate and actual usage | C-EST, C-LEDGER, C-LEDGER-RECON, C-RECHECK, C-REDLOG, C-USAGE, C-JOB |
| schedules and selection | B-SCHED, B-CTRL, C-SCHED, B-CELLLOG |
| manifests and provenance | T-MAN, T-MANGATE, T-PROV, B-ENV, T-DEV |

---

## C2. Artifact schemas (column level)

Abbreviations in the null column: **NN** = never null.

### C2.1 Phase 2A (`results/phase2/phase2a/`), produced by EP-2A

**A-CIRC `circuits.json`** - the complete transpiled circuit per $(L, n)$, starting from $\lvert 0\cdots 0\rangle$ and including the preparation $X$ gates and every rotation parameter, replayed by the dense recomputation.

| key | dtype | units | null |
|---|---|---|---|
| `L` | int | sites | NN |
| `n` | int | steps | NN |
| `initial_state` | str | always the all-zero computational state; preparation gates are instructions | NN |
| `instructions` | list[dict] | circuit order; each `{name, qubits (Qiskit indices), params (radians; empty for parameter-free gates)}`; the $\lfloor L/2\rfloor$ preparation `x` gates come first | NN |
| `counts_by_name` | dict[str,int] | count, preparation gates included | NN |

**A-CELLS `cells.csv`** - exact density-matrix $\langle Z_\pi\rangle/L$ for every cell and step.

| column | dtype | units | null |
|---|---|---|---|
| `L` | int | sites | NN |
| `cell` | str | one of `00`, `10`, `01`, `11` | NN |
| `p1` | float | probability | NN |
| `p2` | float | probability | NN |
| `n` | int | steps | NN |
| `e_dm` | float | observable units | null only on execution failure, then flag `MISSING_OR_NONFINITE` in A-INT |

**A-REF `reference.csv`** - statevector and exact references.

| column | dtype | units | null |
|---|---|---|---|
| `L` | int | sites | NN |
| `n` | int | steps | NN |
| `e0_sv` | float | observable units | NN (gate G1 input) |
| `e_ed` | float | observable units | NN |

**A-DENSE `validation_dense.csv`** - gate G2 rows, one per $(L, \text{cell}, n)$.

| column | dtype | units | null |
|---|---|---|---|
| `L` | int | sites | NN |
| `cell` | str | cell label | NN |
| `n` | int | steps | NN |
| `e_dense` | float | observable units | NN |
| `e_aer` | float | observable units | NN |
| `abs_diff` | float | observable units | NN |

**A-INT `interaction.csv`** - per-step interaction table, all 40 steps.

| column | dtype | units | null |
|---|---|---|---|
| `L` | int | sites | NN |
| `n` | int | steps | NN |
| `in_mask` | int | 0/1 | NN |
| `e00` | float | observable units | NN |
| `r10`, `r01`, `r11` | float | dimensionless | null iff `e00 == 0` |
| `a10`, `a01`, `a11` | float | dimensionless log-attenuation | null iff the ratio is $\le 0$ or `RATIO_UNRESOLVED` |
| `i_n` | float | dimensionless log-attenuation per whole circuit | null iff any `a_ij` null |
| `eta_r10`, `eta_r01`, `eta_r11` | float | dimensionless | null outside the mask |
| `eta_a10`, `eta_a01`, `eta_a11` | float | dimensionless | null if undefined (§C4.1) |
| `a10_plus_a01` | float | dimensionless log-attenuation (stored additive prediction $A_{10} + A_{01}$, plotted by CH-A2) | null iff `a10` or `a01` null |
| `eta_i` | float | dimensionless | null if any `eta_a` null |
| `i_lo`, `i_hi` | float | dimensionless log-attenuation (signed band $I \mp \eta_I$, plotted by CH-A3) | null iff `i_n` or `eta_i` null |
| `abs_i_lo`, `abs_i_hi` | float | dimensionless (magnitude bounds, used by EQ-A4 only) | null iff `i_n` or `eta_i` null |
| `flags` | str | prereg §3.8 vocabulary | NN |

**A-SEC `secondary_slopes.csv`** - secondary fits per cell, whole fixed mask only.

| column | dtype | units | null |
|---|---|---|---|
| `L` | int | sites | NN |
| `cell` | str | cell label | NN |
| `fit_available` | int | 0/1 | NN |
| `g_raw` | float | per step | null iff `fit_available == 0` |
| `g_treated` | float | per step | null iff `fit_available == 0` or `ANTI_ATTENUATION` |
| `intercept` | float | dimensionless | null iff `fit_available == 0` |
| `max_abs_residual`, `rms_residual` | float | dimensionless | null iff `fit_available == 0` |
| `n_points` | int | count | NN |
| `residual_status` | str | `RESIDUAL_ADEQUATE` / `RESIDUAL_INADEQUATE` / empty | NN |
| `flags` | str | `FIT_UNAVAILABLE`, `ANTI_ATTENUATION`, `FIT_FAILURE`, violating steps | NN |

**A-RES `secondary_residuals.csv`** - `L` int, `cell` str, `n` int (steps), `ln_r` float, `fitted` float, `residual` float (all dimensionless, NN; rows exist only for available fits), `is_max_abs_residual` int (0/1, the masked step attaining the fit's maximum absolute residual; drawn with an edge marker on CH-A5).

**A-HIST `historical_crosscheck.csv`** - $L = 6$ cross-check.

| column | dtype | units | null |
|---|---|---|---|
| `n` | int | steps | NN |
| `e00_p2`, `e0_trotter_recorded`, `d00` | float | observable units | NN |
| `e11_p2`, `e_noisy_dm_recorded`, `d11` | float | observable units | NN |
| `within_tau_hist` | int | 0/1 ($10^{-12}$, frozen standard) | NN |
| `within_eta_e` | int | 0/1 ($10^{-9}$, separate report) | NN |

**A-VERD `verdict_2a.json`** - keys under `per_L[L]`: `verdict` (str: `EQUIVALENT` / `INTERACTION` / `INCONCLUSIVE`), `numerics_status` (str), `conditional_label` (str, prereg §3.6 wording), `d_val` (float, observable units), `g1_max_dev` (float), `s_rms_lo`, `s_rms_hi`, `s_max_lo`, `s_max_hi` (float, dimensionless, null if undefined), `tau_rms`, `tau_max` (float), `flag_counts` (dict[str,int]), `mask_in`, `mask_out` (list[int]), `reason` (str), `delta` (float per step, null if unavailable), `delta_reason` (str); top-level `historical` (dict: verdict, offending steps, max deviation).

### C2.2 Phase 2B (`results/phase2/phase2b/`)

**B-ENV `results/phase2/environment_phase2.json`** (EP-2A) - `python` str, `packages` dict[str,str] (pip freeze), `platform` dict (as design.md §16), `phase2_source_sha256` str (hex over sorted `phase2/**/*.py` and `requirements-phase2.txt`), `v010_sealed_identity` str; all NN.

**B-REF `reference_curves.csv`** (EP-2B) - `L` int, `state` str (`Z2` / `CTRL`), `n` int, `obs` str, `e_ed` float, `e0_sv` float (observable units); all NN. Control rows exist only when a control qualifies.

**B-SCHED `peak_schedule.csv`** (EP-2B) - noiseless schedule, fixed before any noisy value.

| column | dtype | units | null |
|---|---|---|---|
| `L` | int | sites | NN |
| `state` | str | `Z2` / `CTRL` | NN |
| `obs` | str | `ZPI` / `PRET` / `MLOC` | NN |
| `k` | int | revival | NN |
| `n_ref` | int | steps | null iff `NO_SCHEDULED_PEAK` |
| `t_ref` | float | steps | null iff `NO_SCHEDULED_PEAK` |
| `amp_ref` | float | observable units | null iff `NO_SCHEDULED_PEAK` |
| `w_lo`, `w_hi` | int | steps | null iff `UNAVAILABLE` |
| `n_ed` | int | steps | null iff `ED_PEAK_UNAVAILABLE` |
| `t_ed` | float | steps | null iff `ED_PEAK_UNAVAILABLE` |
| `amp_ed` | float | observable units | null iff `ED_PEAK_UNAVAILABLE` |
| `timing_testable` | int | 0/1 (window contains $n_{\mathrm{ref}} \pm 2$) | NN |
| `flags` | str | `INTERP_FALLBACK`, `NO_SCHEDULED_PEAK`, `WINDOW_TRUNCATED`, `ED_PEAK_UNAVAILABLE`, `TIMING_UNTESTABLE` | NN |

**B-FOLD `folded_circuits.csv`** (EP-2B) - `cell_index` int, `n` int, `fold_seed` int, `lambda_nominal` float, `lambda_r` float, `lambda_r_1q` float, `cx` int, `sx` int, `sxdg` int, `x` int, `rz` int, `n_ops` int; all NN.

**B-RAWDM `raw_dm.csv`** (EP-2B) - `cell_index` int, `n` int, `fold_seed` int (-1 for the unfolded unmitigated execution), `lambda_nominal` float, `obs` str (`ZPI`, `PRET`, `M_I`, `M_J`, `M_IJ`), `value` float (observable units; null only on `CELL_FAILED`).

**B-RAWSHOT `raw_shots.csv`** (EP-2B) - the shot record, one row per (circuit, outcome) with nonzero count.

| column | dtype | units | null |
|---|---|---|---|
| `cell_index` | int | matrix index | NN |
| `n` | int | steps | NN |
| `fold_seed` | int | seed | NN |
| `lambda_nominal` | float | dimensionless | NN |
| `seed_simulator` | int | $10^6\,\text{cell\_index} + 100n + 10k + j$ | NN |
| `shots_requested`, `shots_actual` | int | shots | NN |
| `outcome` | str | Qiskit-ordered bitstring | NN |
| `count` | int | shots | NN |

**B-RAWSHOTOBS `raw_shot_observables.csv`** (EP-ANALYZE; frozen order step 1 on the shot record) - `cell_index` int, `n` int, `fold_seed` int, `lambda_nominal` float, `obs` str (`ZPI`, `PRET`, `M_I`, `M_J`, `M_IJ`), `value` float (observable units; null only when the circuit record is absent), `shots_actual` int. Every shot-pipeline fit consumes these rows, and CH-B9 plots them.

**B-SEEDFIT `seed_fits.csv`** (EP-ANALYZE) - per-seed extrapolations (frozen order step 2).

| column | dtype | units | null |
|---|---|---|---|
| `cell_index` | int | matrix index | NN |
| `pipeline` | str | `DM` / `SHOT` | NN |
| `n` | int | steps | NN |
| `fold_seed` | int | seed | NN |
| `extrapolator` | str | `LIN` / `QUAD` / `EXP` | NN |
| `obs` | str | §C1.2 | NN |
| `intercept` | float | observable units | null iff `fit_status != OK` |
| `fit_status` | str | `OK` / `FIT_FAILURE` / `FIT_UNAVAILABLE` / `EXP_FIT_FAILED` | NN |
| `clamp_flag` | int | 0/1 | NN |
| `exp_mode` | str | `log` / `avoid_log` / empty | NN |
| `n_distinct_abscissas` | int | count | NN |
| `residual_rms` | float | observable units | null iff not `OK` or exactly determined |

**B-MIT `mitigated.csv`** (EP-ANALYZE) - aggregated curves with seed range, reported and decision intervals.

| column | dtype | units | null |
|---|---|---|---|
| `cell_index` | int | matrix index | NN |
| `pipeline` | str | `DM` / `SHOT` | NN |
| `n` | int | steps | NN |
| `extrapolator` | str | `LIN` / `QUAD` / `EXP` / `NONE` | NN |
| `obs` | str | §C1.2 | NN |
| `estimate` | float | observable units | null iff the aggregate is undefined |
| `seed_min`, `seed_max` | float | observable units | null iff undefined |
| `seed_sd` | float | observable units (`ddof=1`) | null iff fewer than 2 seeds |
| `ci95_lo`, `ci95_hi` | float | observable units | null iff `UNDEFINED` (SHOT only; empty for DM) |
| `dec_lo`, `dec_hi` | float | observable units | null iff `UNDEFINED` (SHOT only) |
| `dec_level` | float | coverage of the decision interval | NN |
| `n_undefined_replicates` | int | count | NN |
| `n_unphysical_replicates` | int | count | NN |
| `beta_hat` | float | observable units | null iff any replicate is undefined or the interval is `UNDEFINED` (never a survivor mean; flag `BETA_UNDEFINED`) |
| `flags` | str | `UNPHYSICAL_ESTIMATE`, `UNPHYSICAL_INTERVAL`, `DEGENERATE_*`, `UNDEFINED`, `PARTIAL_SHOTS` | NN |

**B-BOOTPEAK `bootstrap_peak_replicates.csv`** (EP-ANALYZE) - every peak-level replicate: `cell_index` int, `extrapolator` str, `obs` str (`ZPI`/`PRET`/`MLOC`), `k` int, `b` int, `amplitude` float (null iff undefined), `timing` float steps (null iff undefined), `defined` int 0/1.

**B-STEPMET `step_metrics.csv`** (EP-ANALYZE)

| column | dtype | units | null |
|---|---|---|---|
| `cell_index`, `n` | int | index, steps | NN |
| `extrapolator` | str | `LIN` / `QUAD` / `EXP` | NN |
| `obs` | str | §C1.2 | NN |
| `eps_dm_mit` | float | observable units | null iff DM aggregate undefined |
| `eps_dm_noisy` | float | observable units | NN |
| `er` | float | dimensionless | null iff `er_flag` non-empty |
| `er_flag` | str | empty / `RATIO_LOWER_BOUND` / `RATIO_ZERO_OVER_ZERO` / `RATIO_UNDEFINED` | NN |
| `er_bound` | float | dimensionless: the flagged lower bound $\lvert\epsilon_{\mathrm{mit}}\rvert/\delta_R$ | null unless `er_flag == RATIO_LOWER_BOUND` |
| `u_mit`, `u_noisy` | float | observable units | null iff `UNDEFINED` |
| `ur` | float | dimensionless | null iff `ur_flag` non-empty |
| `ur_flag` | str | as `er_flag` | NN |
| `ur_bound` | float | dimensionless: $u_{\mathrm{mit}}/\delta_R$ | null unless `ur_flag == RATIO_LOWER_BOUND` |
| `beta_hat_mit`, `beta_hat_noisy` | float | observable units | null iff any replicate is undefined (`BETA_UNDEFINED`, possible even with finite conservative quantiles) or the interval is `UNDEFINED` |
| `if_value` | float | dimensionless | null iff `eps_dm_mit` null |
| `if_is_lower_bound`, `reportable` | int | 0/1 | NN |

**B-PEAKMET `peak_metrics.csv`** (EP-ANALYZE) - amplitude and timing errors, both references, separately named by `ref`.

| column | dtype | units | null |
|---|---|---|---|
| `cell_index` | int | matrix index | NN |
| `pipeline` | str | `DM` / `SHOT` | NN |
| `extrapolator` | str | `LIN` / `QUAD` / `EXP` / `NONE` | NN |
| `obs` | str | `ZPI` / `PRET` / `MLOC` | NN |
| `k` | int | revival | NN |
| `ref` | str | `E0` / `ED` | NN |
| `amp_ref` | float | observable units | null iff reference peak unavailable |
| `amp_est` | float | observable units | null iff undefined |
| `d_amp` | float | observable units | null iff either null |
| `t_ref` | float | steps | null iff reference peak unavailable |
| `t_est` | float | steps | null iff `NO_INTERIOR_PEAK` |
| `d_t` | float | steps | null iff either null |
| `matched_n` | int | steps | null iff undefined |
| `flags` | str | §C10 | NN |

**B-CURVEMET `curve_metrics.csv`** (EP-ANALYZE) - `cell_index` int, `pipeline` str, `extrapolator` str, `obs` str, `ref` str (`E0`/`ED`), `tiae` float (observable units × steps; null iff any step undefined), `n_undefined_steps` int, `gif` float (dimensionless; null iff undefined), `gif_is_lower_bound` int.

**B-END `endpoints.csv`** (EP-ANALYZE) - every endpoint with both intervals and its status.

| column | dtype | units | null |
|---|---|---|---|
| `cell_index` | int | matrix index | NN |
| `pipeline` | str | `DM` / `SHOT` | NN |
| `extrapolator` | str | `LIN` / `QUAD` / `EXP` | NN |
| `k` | int | revival | NN |
| `obs` | str | `ZPI` / `PRET` | NN |
| `endpoint` | str | `AMP` / `TIME` | NN |
| `family` | str | `PRIMARY` / `EXPLORATORY` | NN |
| `ref_value` | float | observable units or steps | null iff `UNAVAILABLE` |
| `tol` | float | as `ref_value` | NN |
| `plugin` | float | as `ref_value`: the plug-in amplitude or timing whose interval follows | null iff undefined (`NO_INTERIOR_PEAK`, failed fit) |
| `plugin_error` | float | as `ref_value`: `plugin - ref_value` | null iff either null |
| `band_lo`, `band_hi` | float | as `ref_value` (closed band) | null iff `UNAVAILABLE` |
| `dec_lo`, `dec_hi` | float | as `ref_value` | null iff `UNDEFINED` |
| `dec_level` | float | coverage | NN |
| `ci95_lo`, `ci95_hi` | float | as `ref_value` | null iff `UNDEFINED` |
| `status` | str | `PASS` / `FAIL` / `OVERLAP` / `INDETERMINATE` / `UNAVAILABLE` | NN |
| `flags` | str | §C10 | NN |

**B-COND `conditions.csv`** (EP-ANALYZE) - `cell_index` int, `pipeline` str, `extrapolator` str, `k` int, `family` str, `status_condition` str (`UNAVAILABLE` / `PASS` / `FAIL` / `OVERLAP` / `INDETERMINATE`), `status_zpi_amp`, `status_zpi_time`, `status_pret_amp`, `status_pret_time` str; all NN.

**B-BOUND `boundary_2b.csv`** (EP-ANALYZE)

| column | dtype | units | null |
|---|---|---|---|
| `L` | int | sites | NN |
| `noise_model` | str | `DEP` / `DEPH` / `AMP` / `RO` / `CAL` | NN |
| `folding` | str | `LOCAL` / `GLOBAL` | NN |
| `extrapolator` | str | `LIN` / `QUAD` / `EXP` | NN |
| `pipeline` | str | `DM` / `SHOT` | NN |
| `k` | int | revival | NN |
| `family` | str | `PRIMARY` / `EXPLORATORY` | NN |
| `kappa_star` | str | a $\kappa$ value, `BELOW_MIN_FAIL`, `UNRESOLVED_AT_MIN`, `AT_OR_ABOVE_MAX` | NN |
| `located` | int | 0/1 | NN |
| `status_sequence` | str | statuses at $\kappa = 0.25;0.5;1;2;4$ | NN |
| `non_monotone` | int | 0/1 | NN |
| `k_star_by_kappa` | str | $k^*$ per $\kappa$, semicolon-separated | NN |
| `hypothesis_component` | str | H-2B(a)/(b)/(c): `met` / `falsified` / `not evaluable`; empty for exploratory | NN |

**B-CTRL `control_selection.json`** (EP-2B) - `per_L[L]`: `qualifies` bool, `selected_bitstring` str (site-ordered; null iff none), `selected_count_string` str (null iff none), `e_z2` float, `e_selected` float (null iff none), `w_s_selected` float (null iff none), `scar_manifold_groups` list[dict] (group mean energy, weight, `WEIGHT_MARGINAL`), `closest_candidates` list[dict] (three closest: bitstring, `e`, `w_s`, failed criterion), `flags` list[str], `reason` str.

**B-DIST `distinguishability.csv`** (EP-ANALYZE) - `L` int, `noise_model` str, `folding` str, `extrapolator` str, `obs` str (`ZPI`/`PRET`/`MLOC`), `k` int, `d` float (observable units; null iff undefined), `ci95_lo`, `ci95_hi` float (null iff `UNDEFINED`), `verdict` str (`DISTINGUISHABLE` / `NOT_DISTINGUISHABLE` / `INDETERMINATE` / `CONTROL_ABSENT`).

**B-CELLLOG `cell_log.csv`** (EP-2B) - `cell_index` int, `status` str (`run` / `not_run` / `blocked` / `conditional_run` / `conditional_omitted` / `CELL_FAILED`), `executions_dm` int, `executions_shot` int, `wall_seconds` float (null if not run; informational, enters no result).

### C2.3 Phase 2C (`results/phase2/phase2c/`)

**C-BSEL `backend_selection.json`** (EP-2C-PREFLIGHT) - `gate_time_utc` str, `candidates` list[dict] (name, eligibility per criterion, best-path score, pending jobs), `selected_backend` str (null iff none eligible), `selected_version` str, `chains` dict keyed by `L` in 4, 6, 8 (physical tuple, score), `score_equation` str (prereg §5.2), `flags` list[str] (`SCORE_MARGINAL`).

**C-CALPRE `calibration_snapshot_pre.json`, C-CALPOST `calibration_snapshot_post.json`** - `captured_utc` str, `backend` dict (name, version), `properties` dict (`backend.properties().to_dict()`, whole device), `configuration` dict (`backend.configuration().to_dict()`), `target_rows` list[dict] (instruction, qubits, `duration_s`, `error`, whole device, including `measure` and `reset`); all NN.

**C-SCHED `schedule.json`** (EP-2C-PREFLIGHT) - `points` list[int], `n_1_z`, `n_1_p` int, `n_2_z`, `n_2_p` int (null iff revival 2 dropped), `n_a` int, `windows` dict keyed by endpoint `(obs, k)` → measured points within ±2, `timing_testable` dict keyed by endpoint → 0/1, `e1_subset_ok` bool, `fold_seeds` list[int], `shots` int, `n_circ` int, `blocked_reason` str (empty unless blocked).

**C-QPY `transpiled_circuits.qpy`** - binary QPY container of every transpiled, folded, measured circuit in schedule order; no columns.

**C-DUR `circuit_durations.csv`** (EP-2C-PREFLIGHT)

| column | dtype | units | null |
|---|---|---|---|
| `point_n` | int | steps | NN |
| `lambda_nominal` | float | dimensionless | NN |
| `fold_seed` | int | seed | NN |
| `native_2q_gate` | str | `cx` / `ecr` / `cz` | NN |
| `native_2q_count` | int | count | NN |
| `lambda_r` | float | dimensionless | NN |
| `depth` | int | layers | NN |
| `d_c_s` | float | seconds, includes measurement | NN |
| `d_init_s` | float | seconds, from the target `reset` | NN |
| `dt_s` | float | seconds | NN |
| `counts_json` | str | JSON of instruction counts by name | NN |
| `phys_to_clbit` | str | JSON list: classical bit $i-1 \leftarrow$ physical `chain[i-1]` | NN |
| `layout_ok`, `native_ok` | int | 0/1 | NN |

**C-IDEAL `ideal_equivalence.csv`** - `point_n` int, `lambda_nominal` float, `fold_seed` int, `obs` str, `e0_declared` float, `e_ideal` float, `abs_diff` float, `ok` int; all NN.

**C-EST `usage_estimate.json`** (EP-2C-PREFLIGHT; immutable after the gate)

| key | dtype | units | null |
|---|---|---|---|
| `gate_time_utc` | str | ISO 8601 | NN |
| `t_lim_s`, `t_cap_s`, `t_open_s` | int | QPU seconds (479, 480, 600) | NN |
| `rep_delay_s`, `t_sub_s` | float | seconds | NN |
| `m_multiplier` | float | dimensionless (1.2) | NN |
| `n_circ`, `n_shots` | int | circuits, shots | NN |
| `t_est_1_s` | float | QPU seconds (information) | NN |
| `s_cons` | int | assumed sub-jobs $= n_{\mathrm{circ}}$ | NN |
| `t_est_cons_s` | float | QPU seconds (binding) | NN |
| `fits` | bool | $t_{\mathrm{est\_cons}} < 479$ | NN |
| `u_cons_s`, `u_cons_read_utc` | float, str | QPU seconds; ISO 8601 | NN |
| `u_out_s`, `u_out_read_utc`, `u_out_components` | float, str, dict | other workloads only; service jobs and ledger entries counted | NN |
| `u_auth_s` | float | QPU seconds | NN |
| `condition_a`, `condition_b`, `condition_c` | bool | prereg §5.7 | NN |
| `reserve_after_s` | float | $600 - (u_{\mathrm{auth}} + 479)$ | NN |
| `split_assumption` | str | prereg §5.8 wording | NN |

**C-LEDGER `authorization_ledger_approved.json`** (EP-2C-PREFLIGHT; immutable approved snapshot at gate time) - `entries` list[dict]: `gate_time_utc`, `backend`, `max_execution_time_s`, `job_id` (null until submitted), `closed` bool, `closed_reason`.

**C-LEDGER-RECON `authorization_ledger_reconciliation.json`** (EP-2C-SUBMIT; written after submission, never modifies the approved snapshot) - `entries` list[dict] (every approved entry plus `job_id` once submitted, `closed`, `closed_reason`, `service_usage_s` when available), `reconciled_utc` str, `approved_snapshot_sha256` str (sha256 of the approved snapshot it reconciles); all NN.

**C-RECHECK `pre_submit_recheck.json`** (EP-2C-SUBMIT; separate artifact, fresh timestamp) - `recheck_time_utc` str, `u_cons_s`, `u_out_s`, `u_auth_s` float, `condition_b` bool, `backend` dict (name, version, operational), `chain` list[int], `approved_hashes` dict[str,str] (path → recomputed sha256), `hashes_match` bool, `schedule_match` bool, `proceed` bool.

**C-REDLOG `reduction_log.json`** - `steps` list[dict] (step id, `applied` bool, `skipped_reason`, `t_est_cons_before_s`, `t_est_cons_after_s`, `e1_subset_ok`, `points_after`, `n_circ_after`, `shots_after`), `abandoned` bool, `final_points` list[int].

**C-JOB `job_record.json`** - `submitted_utc` str, `job_id` str, `backend` dict, `options` dict (every option of prereg §5.5), `pubs` list[dict] (circuit index, shots), `terminal_status` str, `terminal_utc` str.

**C-USAGE `usage_actual.json`** - `quantum_seconds` float (`job.usage()`), `metrics_quantum_seconds` float (`job.metrics()`), `ratio_to_t_est_cons`, `ratio_to_t_est_1` float, `calib_max_rel_change` float (dimensionless, over fields with pre ≠ 0; null iff none) with `calib_max_rel_field` str, `calib_max_abs_by_unit` dict (unit → {field, abs_change}: one maximum per unit, never across units), `calib_zero_pre_fields`, `calib_missing_fields`, `calib_new_fields` list[str].

**C-CALDIFF `calibration_change.csv`** (EP-2C-SUBMIT) - one typed row per numeric calibration leaf of either snapshot: `field` str (identified, e.g. `qubit[3].T1`), `unit` str from the unit inventory s, dimensionless, Hz, `status` str (`PRESENT` / `ZERO_PRE` / `MISSING_POST` / `NEW_POST`), `pre` float (null iff `NEW_POST`), `post` float (null iff `MISSING_POST`), `abs_change` float in the field's unit (null iff missing or new), `rel_change` float dimensionless (null unless `PRESENT`), `zero_pre` int. Missing and new fields are rows, never omissions. Maxima are taken only within one unit; quantities with different units are never compared.

**C-RAW `raw_shots_hw.csv`** (EP-2C-SUBMIT) - `point_n` int, `fold_seed` int, `lambda_nominal` float, `pub_index` int, `shots_requested`, `shots_actual` int, `outcome` str, `count` int; all NN.

**C-SEEDFIT `seed_fits_hw.csv`**, **C-MIT `mitigated_hw.csv`**, **C-BOOTPEAK `bootstrap_peak_replicates_hw.csv`** (EP-ANALYZE) - as their Phase 2B counterparts with `point_n` in place of `cell_index` (and no `cell_index`); C-SEEDFIT adds `exact_fit` int (0/1, `QUAD` through three points).

**C-END `endpoints_hw.csv`** (EP-ANALYZE) - as B-END (including `plugin` and `plugin_error`) without `cell_index`/`pipeline`, with `family` str (`CF-2C` / `EXPLORATORY`) and `ref` str (`E0` / `ED`); `ED` rows are reported only and carry an empty `status`.

**C-PEAKMET `peak_metrics_hw.csv`** (EP-ANALYZE) - as B-PEAKMET without `cell_index`/`pipeline`: per `extrapolator` (`LIN`, `QUAD`, `EXP`, `NONE`), `obs`, `k` and `ref`, the reference and plug-in amplitude, `d_amp`, reference and plug-in timing, `d_t`, `matched_n`, `flags`.

**C-STEPMET `step_metrics_hw.csv`** (EP-ANALYZE; descriptive, no decision) - `point_n` int, `extrapolator` str, `obs` str; `eps_raw`, `eps_mit` float (observable units; $\lvert\hat X - E_0\rvert$ on the shot plug-in estimates); `if_value` float (null iff a plug-in is undefined or the lower-bound flag is set), `if_bound` float (null unless `if_is_lower_bound == 1`; then $\varepsilon_{\mathrm{raw}}/\delta_{\mathrm{shot}}$), `if_is_lower_bound` int, `reportable` int ($\varepsilon_{\mathrm{raw}} \ge \varepsilon_{\min} = 0.01$); `u_raw`, `u_mit` float (decision-interval half-widths; null iff `UNDEFINED`), `ur` float, `ur_flag` str, `ur_bound` float (as B-STEPMET). Equation EQ-C7.

**C-VERD `verdict_2c.json`** - `cf_2c_status` str, `endpoint_statuses` dict[str,str], `alpha_e` float (0.0125), `dec_level` float (0.9875), `assumption_statement` str (prereg §6.2 exchangeability condition), `revival_2` dict (exploratory statuses or `DROPPED`).

### C2.4 Top level

**T-MAN `manifest.json`** - `files` dict[str,str] (relative path → sha256 of every file under the bundle root except the manifest), `raw_inputs` dict[str,str] (relative path → sha256 of every raw-input artifact, immutable once listed), `generated_utc` str, `deviations_record` str (`NONE` / `ENUMERATED`, copied from the first line of `deviations.md`).

**T-MANGATE `results/phase2/phase2c/manifest_pregate.json`** (EP-2C-PREFLIGHT; immutable) - `files` dict[str,str] (relative path → sha256 of every gate-approved artifact: C-BSEL, C-CALPRE, C-SCHED, C-QPY, C-DUR, C-IDEAL, C-EST, C-LEDGER, C-REDLOG), `generated_utc` str, `gate_record_sha256` str. EP-2C-SUBMIT and EP-ANALYZE verify every approved hash against this file and never rewrite it.

**T-PROV `provenance.json`** - `phase2_source_sha256` str, `v010_sealed_identity` str, `contract_sha256` str (sha256 of `tools/phase2_contract.json` used), `git_head` str (informational; null if not a repository), `entrypoint_runs` list[dict] (id, start/end UTC, exit code), `timestamps_note` str. The timestamp fields legitimately differ between reproductions and are excluded from byte comparison.

**T-DEV `deviations.md`** - must exist and be non-empty; its first non-blank line is exactly `DEVIATIONS: NONE` or `DEVIATIONS: ENUMERATED`, followed in the second case by one entry per deviation as prereg §6.11. An absent or empty file is missing evidence, not a declaration, and is a contract violation (exit 2).

---

## C3. Equation registry

Each equation lists the columns it consumes and produces (`ARTIFACT.column`). The checker verifies that every referenced column is declared in §C2 and that every declared column is referenced by an equation or a chart or carries a usage note.

| id | statement | inputs | outputs | prereg |
|---|---|---|---|---|
| EQ-A1 | $r_{ij}(n) = E_{ij}(n)/E_{00}(n)$ | A-CELLS.e_dm | A-INT.e00, r10, r01, r11 | §3.3 |
| EQ-A2 | $A_{ij} = -\ln r_{ij}$, $A_{00} \equiv 0$ | A-INT.r10, r01, r11 | A-INT.a10, a01, a11 | §3.3 |
| EQ-A3 | $I(n) = A_{11} - A_{10} - A_{01} + A_{00}$ | A-INT.a10, a01, a11 | A-INT.i_n | §3.3 |
| EQ-A4 | $S_{\mathrm{RMS}}$, $S_{\max}$ over the mask, with bound intervals | A-INT.i_n, in_mask, abs_i_lo, abs_i_hi | A-VERD.s_rms_lo/hi, s_max_lo/hi | §3.3, §3.6 |
| EQ-A5 | $\eta_r$, $\eta_A$, $\eta_I$ propagation; signed band $[I - \eta_I, I + \eta_I]$; magnitude bounds | A-INT.r*, e00 | A-INT.eta_r*, eta_a*, eta_i, i_lo, i_hi, abs_i_lo, abs_i_hi | §3.6 |
| EQ-A6 | mask $\lvert E_{00}(n)\rvert \ge m_0$; `MASK_BOUNDARY` | A-INT.e00 | A-INT.in_mask, A-VERD.mask_in, mask_out | §3.4 |
| EQ-A7 | OLS $\ln r_{ij} \approx a + bn$ over the whole mask; $g = -b$; residuals; gates | A-INT.r*, in_mask, flags | A-SEC.*, A-RES.* | §3.9 |
| EQ-A8 | $\Delta = g_{11} - g_{10} - g_{01}$ | A-SEC.g_treated | A-VERD.delta, delta_reason | §3.9 |
| EQ-A9 | $d_{00}$, $d_{11}$ against the recorded bundle | A-CELLS.e_dm, recorded `steps.csv` | A-HIST.*, A-VERD.historical | §3.2 |
| EQ-A10 | gate G1 and G2, $d_{\mathrm{val}}$ | A-CELLS.e_dm, A-REF.e0_sv, A-DENSE.e_dense, e_aer, A-CIRC.* | A-DENSE.abs_diff, A-VERD.d_val, g1_max_dev, numerics_status, conditional_label | §3.6 |
| EQ-A11 | Phase 2A verdict by interval inclusion with blocking flags | A-VERD.s_*, A-INT.flags | A-VERD.verdict, reason, flag_counts, tau_rms, tau_max | §3.7 |
| EQ-B1 | raw observables and moments from counts or $\rho$ | B-RAWSHOT.outcome, count, shots_actual; B-RAWDM.value | B-RAWDM.obs, value; B-RAWSHOTOBS.value, shots_actual (frozen order step 1) | §4.5 |
| EQ-B2 | $\lambda_r$, $\lambda_r^{(1)}$ | B-FOLD.cx, sx, sxdg, x | B-FOLD.lambda_r, lambda_r_1q | §4.3 |
| EQ-B3 | per-seed LIN, QUAD, EXP intercepts with rank and clamp rules | B-FOLD.lambda_r, B-RAWDM.value, B-RAWSHOT.count | B-SEEDFIT.*, C-SEEDFIT.* | §4.4 |
| EQ-B4 | $\mathrm{CZZ}_s$ from the seed's extrapolated moments | B-SEEDFIT.intercept (M_I, M_J, M_IJ) | B-SEEDFIT rows with obs = CZZ | §4.4 |
| EQ-B5 | aggregation across seeds under the homogeneity rule; unmitigated = mean of $\lambda = 1$ | B-SEEDFIT.intercept, fit_status | B-MIT.estimate, seed_min, seed_max, seed_sd, flags; C-MIT likewise | §6.2 |
| EQ-B6 | schedule peaks, parabolic timing, windows, identity, testability | B-REF.e0_sv, e_ed | B-SCHED.*, C-SCHED.* | §4.6, §5.9 |
| EQ-B7 | matched peak; $\Delta A_k^{(\mathrm{ref})}$, $\Delta t_k^{(\mathrm{ref})}$ | B-MIT.estimate, B-SCHED.* | B-PEAKMET.* | §4.7 |
| EQ-B8 | trapezoid TIAE per reference | B-MIT.estimate, B-REF.e0_sv, e_ed | B-CURVEMET.tiae, n_undefined_steps, ref | §4.7 |
| EQ-B9 | $\epsilon^{\mathrm{DM}}$, ER with the ratio rule | B-MIT.estimate (DM), B-REF.e0_sv | B-STEPMET.eps_dm_*, er, er_flag | §4.7 |
| EQ-B10 | $u$ = half-width of the **decision** interval at the family's level (never the reported 95% columns), UR, $\hat\beta$ | B-MIT.dec_lo, dec_hi, dec_level, beta_hat | B-STEPMET.u_*, ur, ur_flag, beta_hat_* | §4.7 |
| EQ-B11 | IF$(n)$ with $\varepsilon_{\min}$ and $\delta$; GIF | B-STEPMET.eps_dm_* | B-STEPMET.if_*, reportable; B-CURVEMET.gif, gif_is_lower_bound | §4.7 |
| EQ-B12 | percentile quantile with undefined replicates at $\mp\infty$; reported and decision levels; $\hat\beta$ | B-BOOTPEAK.*, B-RAWSHOT.count, seed_simulator | B-MIT/C-MIT interval columns, B-END/C-END interval columns, B-DIST.ci95_* | §6.3, §6.4 |
| EQ-B13 | three-way endpoint status with the physical-range condition | B-END/C-END.dec_*, band_*, ref_value, tol | B-END/C-END.status, flags | §6.5 |
| EQ-B14 | condition status; family; CF-2C verdict | B-END.status, B-SCHED.flags | B-COND.*, C-VERD.* | §4.8, §5.11 |
| EQ-B15 | boundary with persistence and located/unresolved | B-COND.status_condition | B-BOUND.* | §4.8 |
| EQ-B16 | $D_k^O$ and its interval | B-MIT.estimate (scar, control), B-SCHED.n_ref | B-DIST.d, verdict | §4.7 |
| EQ-B17 | control energy density, scar manifold, overlap, total orders | B-REF (noiseless), $H$ | B-CTRL.* | §4.9 |
| EQ-B18 | `seed_simulator` formula | matrix index | B-RAWSHOT.seed_simulator | §4.11 |
| EQ-C1 | $T_{\mathrm{est}}^{(S)}$; binding $T_{\mathrm{est}}^{\mathrm{cons}}$ | C-DUR.d_c_s, d_init_s; C-SCHED.n_circ, shots | C-EST.t_est_1_s, t_est_cons_s, s_cons, fits, rep_delay_s, m_multiplier, t_sub_s | §5.8 |
| EQ-C2 | $\mathrm{fits}(T) \Leftrightarrow T < 479$; $U_{\mathrm{auth}} + 479 \le 480$; reserve $= 121 - U_{\mathrm{auth}}$ | C-EST.t_est_cons_s, u_cons_s, u_out_s; C-LEDGER.entries | C-EST.u_auth_s, condition_*, reserve_after_s; C-RECHECK.* | §5.7 |
| EQ-C3 | layout score $\sum_{\text{bonds}} e_2 + \sum_{\text{qubits}} \tfrac12(P(1\vert 0) + P(0\vert 1))$ | C-CALPRE.* | C-BSEL.* | §5.2 |
| EQ-C4 | scheduled duration incl. measurement; native $\lambda_r$; ideal equivalence within $\eta_E$ | C-QPY, C-CALPRE.target_rows | C-DUR.*, C-IDEAL.* | §5.4 |
| EQ-C5 | reduction R1 to R8 until fits; skip any step violating $E_1 \subseteq \mathcal{P}$ | C-EST.t_est_cons_s, C-SCHED.points | C-REDLOG.* | §5.10 |
| EQ-C6 | actual-usage ratios; calibration change with zero-pre handling | C-EST.*, C-CALPRE, C-CALPOST | C-USAGE.* | §5.3, §5.6 |
| EQ-C7 | hardware descriptive metrics on shot plug-in estimates: $\varepsilon_{\mathrm{raw}}$, $\varepsilon_{\mathrm{mit}}$, IF with $\varepsilon_{\min} = 0.01$ and $\delta_{\mathrm{shot}} = 10^{-3}$ (design.md §13 shot rule), UR of decision half-widths | C-MIT.estimate, dec_lo, dec_hi; B-REF.e0_sv | C-STEPMET.* | §5.11 |

---

## C4. Estimator algorithms (reference definitions)

The checker (§C7) contains reference implementations of every algorithm in this section and exercises them on synthetic fixtures. A future implementation must reproduce the checker's reference values on those fixtures exactly.

### C4.1 Phase 2A

1. **Ratios and logs (EQ-A1, EQ-A2).** For each masked step and cell: `r = e_dm / e00`; if `r <= 0` set `SIGN_FLIP`, `a` null; else `a = -ln(r)`.
2. **Budget propagation (EQ-A5)**, computed values only: `eta_r = eta_E*(1+|r|)/(|e00|-eta_E)`; if `|r| <= eta_r` set `RATIO_UNRESOLVED`, `eta_a` null; else `eta_a = eta_r/(|r|-eta_r)`; `eta_i = eta_a10+eta_a01+eta_a11`; `abs_i_lo = max(0, |i| - eta_i)`, `abs_i_hi = |i| + eta_i`; if `eta_i > tau_max` set `NUMERICAL_INCONCLUSIVE`; if `r > 1 + eta_r` set `RATIO_ABOVE_ONE`; if `|r - 1| <= eta_r` set `RATIO_NEAR_ONE`.
3. **Mask (EQ-A6).** `in_mask = |e00| >= 0.1`; if `| |e00| - 0.1 | <= eta_E` set `MASK_BOUNDARY` (blocking; no membership change).
4. **Statistics (EQ-A4).** Over masked steps only, and only if every masked `i_n` is defined and the mask holds at least $k_{\min} = 3$ steps (amendment A-2; a smaller mask sets `TOO_FEW_POINTS`, leaves all four null and gives `INCONCLUSIVE`, while the per-step rows and the mask itself are kept): `s_rms_lo = sqrt(mean(abs_i_lo^2))`, `s_rms_hi = sqrt(mean(abs_i_hi^2))`, `s_max_lo = max(abs_i_lo)`, `s_max_hi = max(abs_i_hi)`; otherwise all four null.
5. **Verdict (EQ-A11).** If any blocking flag (`MISSING_OR_NONFINITE`, `MASK_BOUNDARY`, `REFERENCE_MISMATCH`, `SIGN_FLIP`, `RATIO_UNRESOLVED`, `NUMERICAL_INCONCLUSIVE`, `TOO_FEW_POINTS`) is present at that $L$, or any statistic is null: `INCONCLUSIVE` with the reason. Else `EQUIVALENT` if `s_rms_hi <= tau_rms and s_max_hi <= tau_max`; else `INTERACTION` if `s_rms_lo > tau_rms or s_max_lo > tau_max`; else `INCONCLUSIVE` ("interval straddles a margin").
6. **Secondary fit (EQ-A7).** The domain is every masked step. The fit is unavailable (`FIT_UNAVAILABLE`, violating steps listed) if any masked step of the cell carries `SIGN_FLIP`, `RATIO_UNRESOLVED`, `RATIO_ABOVE_ONE` or `MISSING_OR_NONFINITE`, or the $L$ carries `REFERENCE_MISMATCH`, `NUMERICAL_INCONCLUSIVE`, `TOO_FEW_POINTS` or `MASK_BOUNDARY`. Otherwise ordinary least squares of `ln_r` on `n` over all masked steps: with $\bar n$, $\bar\ell$ the means, $b = \sum (n-\bar n)(\ell-\bar\ell)/\sum (n-\bar n)^2$, $a = \bar\ell - b\bar n$; `g_raw = -b`; `g_treated = 0` if `-1e-9 <= g_raw < 0`, `ANTI_ATTENUATION` if `g_raw < -1e-9`, else `g_raw`; residuals `ln_r - (a + b n)`; `RESIDUAL_ADEQUATE` iff `max|residual| <= 0.05`. A singular denominator (all masked `n` equal, impossible with ≥ 3 distinct steps) is `FIT_FAILURE`.
7. **Historical cross-check (EQ-A9).** `d00`, `d11` per step at $L = 6$; `HISTORICAL_CONSISTENT` iff all `<= 1e-12`; `within_eta_e` reported separately.
8. **Dense recomputation (gate G2), one preparation boundary.** For each `(L, cell, n)`: start from $\rho = \lvert 0\cdots 0\rangle\langle 0\cdots 0\rvert$ (the all-zero state; the recorded circuit itself contains the $\lfloor L/2\rfloor$ preparation `x` gates on the even sites, exactly as the sealed builder emits them, and design.md §8 and §11 count those gates in the noisy single-qubit exposure, so preparation noise is included by replaying them); for each instruction of A-CIRC in order, apply the unitary conjugation $U\rho U^\dagger$ of the instruction (`rz(θ)`, `sx`, `sxdg`, `x`, `cx` with their standard matrices and the recorded parameter), then the Kraus map of the channel attached to that instruction name: depolarizing with parameter $p$ on $k$ qubits as $(1-p)\rho + p\,\mathrm{Tr}_{k}(\rho)\otimes I/2^k$ on the instruction's qubits (design.md §11), nothing for `rz`; finally `e_dense = Tr[rho Z_pi]/L` with $Z_\pi$ from the same site map. Never start from $\lvert Z_2\rangle$: replaying the recorded preparation gates from $\lvert Z_2\rangle$ would return the all-zero state before the evolution. `d_val = max abs_diff`; `NUMERICS_VALIDATED` iff `d_val <= 1e-10` and every G1 deviation `<= 1e-9`.

### C4.2 Global folding arithmetic (`GLOBAL`)

Input: the transpiled operation list $U = (u_1, \dots, u_m)$ without final measurements, and the nominal $\lambda \ge 1$. With `q, f = divmod(lambda - 1, 2)` (`q` integer, `f` in $[0, 2)$): the folded list is $U$ followed by $q$ copies of $(U^\dagger, U)$, followed, if $f > 0$, by $(S^\dagger, S)$ where $S$ is the suffix of the last `n_p = round(f * m / 2)` operations (Python `round`, half to even); $U^\dagger$ is the reversed list of inverses. Inverses: `cx`→`cx`, `x`→`x`, `sx`→`sxdg`, `sxdg`→`sx`, `rz(θ)`→`rz(-θ)`. Measurements are appended after folding; no barriers exist. Counts: `lambda_r = cx_folded / cx_base`; `lambda_r_1q = (sx+sxdg+x)_folded / (sx+x)_base`. Synthetic fixture (§C7): a 10-operation list with 4 `cx` at $\lambda = 1.5$ gives `q = 0`, `f = 0.5`, `n_p = round(2.5) = 2`, so the suffix of the last two operations is folded; `lambda_r` is then determined by how many of those two are `cx`.

Rank rule for every Phase 2B fit, both folding variants (`LOCAL` and `GLOBAL`), both pipelines, recorded counts and every bootstrap replicate (prereg §4.3; amendment A-1, 2026-09-08): `LIN` needs at least 2 distinct realized abscissas, `QUAD` at least 3, `EXP` (two parameters with the asymptote fixed) at least 3 in log mode and in `avoid_log` mode alike (two distinct abscissas are the algebraic full-rank necessity of the two-parameter fit; three is the human-selected admission minimum above it, amendment A-1); otherwise `FIT_FAILURE` with `n_distinct_abscissas` recorded, and under §C4.3 step 4 one failed seed makes the step aggregate null with no surviving-seed mean. Duplicate abscissas are kept as recorded in the regression and count once toward the rank. Abscissas are fixed under resampling, so a rank failure is structural and every replicate inherits it. The machine-readable rule is `phase2b.rank_rule` (JSON), bound to the constant C-EXP-MIN-2B = 3; before A-1 this paragraph said 2 for `EXP`. Phase 2C keeps `EXP` at 2 (C-EXP-MIN-2C = 2, `phase2c.transpilation.rank_rule`, prereg §5.4): the hardware arm is separate and its minimum is never exported to Phase 2B. The checker's reference implementations take the minimum as a required parameter and are exercised at both values (§C7).

### C4.3 Frozen estimator order (prereg §6.2), for recorded counts and every replicate

1. Per circuit $(n, s, j)$: from counts and `shots_actual`, compute `ZPI`, `PRET`, `M_I`, `M_J`, `M_IJ` (one pass over the same counts; `PRET` is the fraction of counts equal to the state's own count string; `ZPI` is $\tfrac{1}{L}\sum_i (-1)^i \langle Z_i\rangle$ with $Z_i = +1$ for bit value 0).
2. Per fold seed $s$: for each raw quantity separately, fit over that seed's $(\lambda_r, \text{value})$ points: `LIN` (degree-1 least squares, intercept at 0), `QUAD` (degree-2, intercept at 0), `EXP` exactly as the pinned mitiq v1.0.0 `ExpFactory` with a fixed asymptote $a$ (0 for `ZPI`, `MLOC`, `M_I`, `M_J`, `M_IJ`; $2^{-L}$ for `PRET`): the sign $\sigma$ is `np.sign` of the linear intercept minus $a$, the linear intercept being `numpy.polyfit(lambda_r, y, 1)[-1]` exactly as the pinned source (`mitiq_polyfit`), so $\sigma = 0$ when the intercept equals $a$ and the log-mode limit is then exactly $a$ (amendment A-2; the same $\sigma$ seeds the `avoid_log` initial guess, so the two modes never disagree); shifted values $\max(\sigma(y - a), 10^{-6})$ with any clamp setting `clamp_flag`; log mode is a weighted linear fit of $\ln(\text{shifted})$ on $\lambda_r$ with weights $\sqrt{\text{shifted}}$ (numpy `polyfit` convention), intercept $a + \sigma e^{\text{fit}(0)}$; the `avoid_log` mode required by the homogeneity rule is `scipy.optimize.curve_fit` of $a + b\,e^{c x}$ with initial guess $[\sigma, -1]$ and default settings, limit $a + b$, with a solver `RuntimeError` as the only solver failure (`EXP_FIT_FAILED`) and no constraint on $c$; with the rank rule of the phase, applied before either mode: §C4.2 for Phase 2B (`LIN` 2, `QUAD` 3, `EXP` 3 distinct realized abscissas); prereg §5.4 and `phase2c.transpilation.rank_rule` for Phase 2C (`LIN` 2, `QUAD` 3, `EXP` 2). A missing circuit (no record or zero shots) makes every fit of that seed at that step `FIT_UNAVAILABLE`.
3. Per fold seed: `CZZ_s = M_IJ_s - M_I_s · M_J_s` from the seed's extrapolated moments; `MLOC_s = (-1)^{i*} M_I_s`.
4. Aggregate across seeds: arithmetic mean per quantity and extrapolator. Homogeneity rule for `EXP`: if any seed at a step has `clamp_flag = 1`, refit all seeds in `avoid_log`; if any seed's fit is `EXP_FIT_FAILED`, `FIT_FAILURE` or `FIT_UNAVAILABLE`, the step's aggregate is null with the flag; never a partial mean. The unmitigated value is the mean over seeds of the $\lambda = 1$ circuits. `seed_min`, `seed_max`, `seed_sd` (`ddof=1`) from the per-seed values.
5. Peak matching (§C4.4) on the aggregated curve; then every metric of EQ-B7 to EQ-B11.

Aggregation-order fixture (§C7): two seeds with moment triples $(M_I, M_J, M_{IJ}) = (0.5, 0.5, 0.25)$ and $(-0.5, -0.5, 0.25)$ give per-seed connected correlations $0$ and $0$, mean $0$; the connected correlation of the averaged moments is $0.25 - 0 \cdot 0 = 0.25$. The frozen order returns $0$.

### C4.4 Peaks, windows, matching, timing

1. On the noiseless grid $y(n) = \sigma_O O_0(n)$, $n = 1..N$: candidates are $2 \le n \le N-1$ with $y(n) > y(n-1)$ and $y(n) \ge y(n+1)$; processed ascending, a candidate within $d_{\min} = 5$ of an accepted peak replaces it only if strictly higher (earlier kept on a tie); accepted peaks are numbered $k = 1, 2, \dots$.
2. Parabolic timing at grid step $n$: $t^* = n + \tfrac12 (y_- - y_+)/(y_- - 2y_0 + y_+)$; if the denominator is $\ge 0$ or $\lvert t^* - n\rvert > 1$, $t^* = n$ and `INTERP_FALLBACK`.
3. Revival identity: $k$ from the `ZPI` schedule; the `PRET` (and `MLOC`, ED) peak for revival $k$ is the accepted peak inside the window $W_k$; none or more than one → `NO_SCHEDULED_PEAK` (condition `UNAVAILABLE`) or `ED_PEAK_UNAVAILABLE`.
4. Windows: $W_k = [n_k - 4, n_k + 4]$ clipped to $[1, N]$; if $n_{k+1} - n_k < 9$, truncate at the midpoint (`WINDOW_TRUNCATED`); width $< 3$ → `UNAVAILABLE`; window lacking $n_k^{O} \pm 2$ → `TIMING_UNTESTABLE`.
5. Matching a curve $X$: $\hat n = \arg\max_{n \in W} \sigma_O X(n)$ (earliest on a tie); interior iff $\hat n \pm 1$ are both measured points in $W$; interior → parabolic timing; else `NO_INTERIOR_PEAK` (timing `INDETERMINATE`). Amplitude is $X(\hat n)$ always.
6. Three-point bound (independent-review finding 1): with $a = y_0 - y_- > 0$ and $b = y_0 - y_+ \ge 0$, $t^* - n = (a - b)/(2(a + b)) \in [-0.5, 0.5]$; hence on a three-point window centred on the reference no finite timing can exceed $\tau_t = 1$, and the endpoint is `TIMING_UNTESTABLE`. The checker demonstrates the bound over a synthetic grid of $(a, b)$ and shows a five-point window producing a `FAIL`.
7. **DM companion seed range (amendment A-2).** For each endpoint of the density-matrix companion (prereg §4.8): the aggregated curve (mean over the eight seeds per step, undefined where any seed is undefined) is matched on the window by item 5, giving $\hat n$; the **amplitude** range is $[\min_s X^{(s)}(\hat n), \max_s X^{(s)}(\hat n)]$ over all eight seeds at that step; the **timing** range is $[\min_s t^*_s, \max_s t^*_s]$ with $t^*_s$ each seed's own matched peak inside the same window by items 2 and 5 (`NO_INTERIOR_PEAK` makes $t^*_s$ undefined). Any undefined required seed value nulls the whole amplitude or timing range; no partial range is ever formed. A seed value is undefined when it is missing or non-finite (`NaN`, $+\infty$ or $-\infty$); the reference `dm_seed_range` and the implementation apply the same rule (correction to A-2, 2026-09-08, replacing a missing-value-only sentinel). The Reviewer counterexample (four seeds peaking at 19 and four at 21, amplitude 1; aggregate matched at 19 with amplitude 0.5) therefore gives the amplitude range $[0, 1]$ (`OVERLAP` against the `PRET` band $[0.95, 1.05]$), not the own-peak range $[1, 1]$ (`PASS`).

### C4.5 Bootstrap and intervals

1. Generator: `numpy.random.default_rng([20260907, phase, cell_index, b])`, `phase` 2 or 3, `cell_index` 0 for hardware. Circuits in ascending $(n, \text{seed index}, \text{scale index})$; `rng.multinomial(shots_actual, p_hat)` with `p_hat` over the $2^L$ outcomes in ascending integer order of the Qiskit-ordered string.
2. Replicate statistics via §C4.3; undefined replicates stored as undefined, never dropped.
3. Quantile: sort the $B$ values; $h = q(B-1)$; $x_{(\lfloor h\rfloor+1)} + (h - \lfloor h\rfloor)(x_{(\lfloor h\rfloor+2)} - x_{(\lfloor h\rfloor+1)})$ with 1-based order statistics; for the lower quantile every undefined replicate is placed at $-\infty$, for the upper at $+\infty$; if either order statistic entering the formula is infinite the quantile is that infinity (no arithmetic on infinities) and the interval is `UNDEFINED`. Exact counts tolerated: $u \le \lfloor h\rfloor$; that is 4 at $B_{\mathrm{P}} = 48000$, $q = 1/9600$ exactly (rendered $1.0417\times10^{-4}$; the rounded value is never used, it would tolerate 5); 12 at $B = 2000$, $q = 0.00625$; 49 at $B = 2000$, $q = 0.025$.
4. Levels: reported `ci95` at $(0.025, 0.975)$ always; decision at $(\alpha_e/2, 1-\alpha_e/2)$ with $\alpha_e = 0.05/240$ (Phase 2B primary, $B = 48000$), $0.0125$ (CF-2C, $B = 2000$), $0.05$ (exploratory, $B = 2000$).
5. $\hat\beta$ = mean of **all** $B$ replicates minus the plug-in estimate. If any replicate is undefined, $\hat\beta$ is unavailable (null, flag `BETA_UNDEFINED`) even when the conservative quantiles are finite; it is never computed over the defined replicates alone. The checker asserts that a finite interval does not imply a defined $\hat\beta$.
6. Physical bounds: nothing clipped; `UNPHYSICAL_ESTIMATE` / `UNPHYSICAL_INTERVAL` flags; a pass requires the decision interval inside the closed band and inside the closed physical range.

### C4.6 Statuses, conditions, boundary

- Endpoint (EQ-B13): with decision interval $[\ell, h]$, closed band $[a, b]$ and physical range $[p_{\mathrm{lo}}, p_{\mathrm{hi}}]$: `INDETERMINATE` if the interval is undefined or degenerate (§C10) or the endpoint is `TIMING_UNTESTABLE` or `NO_INTERIOR_PEAK`; else `PASS` if $\ell \ge a$, $h \le b$, $\ell \ge p_{\mathrm{lo}}$, $h \le p_{\mathrm{hi}}$; else `FAIL` if $h < a$ or $\ell > b$; else `OVERLAP`.
- Condition (EQ-B14): `UNAVAILABLE` if any endpoint's reference is unavailable; else `PASS` if all four `PASS`; else `FAIL` if any `FAIL`; else `OVERLAP` if any `OVERLAP` and none `INDETERMINATE`; else `INDETERMINATE`. The combination (`FAIL`, `INDETERMINATE`, `PASS`, `PASS`) is `FAIL`.
- Boundary (EQ-B15): scan $\kappa$ ascending; $\kappa^*$ = largest $\kappa_i$ with `PASS` at every level up to $i$; next level `FAIL` → `located = 1`; next level `OVERLAP`/`INDETERMINATE`/`UNAVAILABLE` → unresolved (`located = 0`); first level `FAIL` → `BELOW_MIN_FAIL`; first level otherwise not `PASS` → `UNRESOLVED_AT_MIN`; all `PASS` → `AT_OR_ABOVE_MAX`; any `PASS` after a non-`PASS` → `non_monotone = 1`, boundary unchanged. $k^*(\kappa)$ = largest $k$ with `PASS` at revivals $1..k$.
- H-2B components per $(L, \text{model})$: (a) `met` iff $\kappa^*(1) \in \{0.5, 1, 2\}$ and located, `falsified` iff located outside that set, `BELOW_MIN_FAIL` or `AT_OR_ABOVE_MAX`, else `not evaluable`; (b) and (c) likewise on located values.

### C4.7 Control selection total orders, ratio rule, replay

- Eigenvalue groups by adjacent-gap chaining at $10^{-9}$; group key $(-w_j, \bar\epsilon_j, j)$ compared exactly; candidate key $(\lvert e - e_{Z_2}\rvert, w_S, \text{index})$ compared exactly; marginality flags at $10^{-12}$ never enter the ordering. Fixture (§C7): three weights $(0.5, 0.5 + 0.75\times10^{-12}, 0.5 + 1.5\times10^{-12})$ have a unique descending order $(3, 2, 1)$ by exact comparison, with `WEIGHT_MARGINAL` set for both adjacent pairs.
- Ratio rule (EQ-B9, EQ-B10) with $\delta_R = 10^{-9}$: value if the denominator exceeds $\delta_R$ and both are finite; `RATIO_LOWER_BOUND` if the denominator is at most $\delta_R$ and the numerator exceeds it; `RATIO_ZERO_OVER_ZERO` if both are at most $\delta_R$; `RATIO_UNDEFINED` if either is non-finite or degenerate.
- Replay: EP-ANALYZE `--replay` regenerates every replicate from the saved counts and seeds and must reproduce the stored quantiles and B-BOOTPEAK/C-BOOTPEAK byte-for-byte in the same environment; a difference is exit code 4.

### C4.8 `CAL` reconstruction (future implementation contract, choices fixed)

Input: C-CALPRE. For the chain of size $L$ from C-BSEL: for each simulator instruction on logical qubits, the channel is built from the physical qubit(s) `chain[i-1]`: single-qubit `sx`, `x`, `sxdg` → thermal relaxation with the physical qubit's $T_1$, $T_2$ and the instruction's reported duration, composed with a depolarizing channel whose parameter makes the total average gate error equal the reported gate error (the Aer device-model construction); `cx` on logical $(q_{i-1}, q_i)$ → the same construction for the native two-qubit gate on the physical bond in the reported direction with the larger error; `rz` clean; readout: per-qubit matrix $[[1-P(1\vert 0), P(1\vert 0)], [P(0\vert 1), 1-P(0\vert 1)]]$ applied classically to the probability vector in the `DM` pipeline and as `ReadoutError` in the `SHOT` pipeline. Every executed instruction of every folded `CAL` circuit must have a channel (T6-style check) or the cell is `CAL_MISSING_CHANNEL` and not run. The model is a stand-in on the simulator basis, stated with every `CAL` result.

---

## C5. Chart inventory

Every chart is written in **both** `png` and `pdf` to `figures-phase2/<id>[_<param>...].<fmt>` (a sibling of the canonical `figures/` directory, never inside it). Every series names its artifact, column and equation (§C9 is generated from this inventory). Masks are drawn as marker styles, never by omission. Every mask states its conditions in machine form (`hollow_when`, `edge_when`, `triangle_when`, `style_when`, comparison operators such as `{">": 0}`) beside its prose meaning, and a condition on a never-null column can never test for null. On a logarithmic axis a zero or negative value is drawn hollow at the axis floor with an annotated count. A bound column declares `bound_for`, the quantity it bounds (`er_bound` for `er`, `ur_bound` for `ur`), and a value rule may draw a bound only for that quantity. A plotted column whose null is explained by a flag column carries **value rules** binding each flag value to the column actually drawn and its marker: a `RATIO_LOWER_BOUND` row is drawn as an upward triangle at its bound column (`er_bound`, `ur_bound`), a lower-bound `IF` or `GIF` as a triangle at the flagged value, `RATIO_ZERO_OVER_ZERO`, `RATIO_UNDEFINED`, `BETA_UNDEFINED` and failed fits hollow at the axis floor, and calibration statuses as stated for CH-C5; a flag value without a rule is a contract violation. Band legends state exactly what the band is; the words "95%" appear only on a band that is a 95% percentile bootstrap interval, and the word "uncertainty" never appears alone. Every chart that shows a mitigated observable carries the $E^{\mathrm{ED}}$ series (prereg §2.4).

| id | title | family (one file per combination) | panels: x, y (units, scale) | series (artifact.column, equation) | band / mask | legend wording |
|---|---|---|---|---|---|---|
| CH-A1 | Attenuation ratios per cell | L ∈ {4,6,8} | `ratios`: n (steps, linear); r (dimensionless, linear) | A-INT.r10, r01, r11 (EQ-A1) | mask A-INT.in_mask: filled in mask, hollow outside | "r_10 single-qubit only", "r_01 two-qubit only", "r_11 both" |
| CH-A2 | Log-attenuation and the additive prediction | L | `logatt`: n; A (log-attenuation, linear) | A-INT.a10, a01, a11 (EQ-A2); A-INT.a10_plus_a01, a stored column (EQ-A3) | mask as CH-A1 | "A_10", "A_01", "A_11 observed combined", "A_10 + A_01 additive prediction (stored column)" |
| CH-A3 | Interaction with bound intervals and margins | L | `interaction`: n; I (log-attenuation per whole circuit, linear) | A-INT.i_n (EQ-A3); horizontal ±tau_max and ±tau_RMS drawn from the constants C-TAU-MAX and C-TAU-RMS (EQ-A11), not from any column | band A-INT.i_lo/i_hi (signed; the magnitude bounds abs_i_lo/abs_i_hi are never drawn around the signed value); mask as CH-A1 | "numerical bound interval on signed I(n), budget eta_E = 10^-9, status <validated/unvalidated>; not a confidence interval"; "±tau_max = ±ln 1.10"; "±tau_RMS = ±ln 1.05" |
| CH-A4 | Phase 2A observable per cell with both references | L | `obs`: n; Z_pi/L (linear) | A-REF.e_ed, e0_sv (EQ-A10); A-CELLS.e_dm for cells 10, 01, 11 (EQ-A1) | none | "E^ED continuous-time exact", "E_0 noiseless Trotter", "cell (1,0)", "cell (0,1)", "cell (1,1)" |
| CH-A5 | Secondary fits and residuals | L × cell ∈ {10, 01, 11} (file `CH-A5_{L}_{cell}`) | `lnr`: n; ln r (linear). `residuals`: n; residual (linear) | A-RES.ln_r, fitted, residual for the file's L and cell (EQ-A7); horizontal ±tau_res from the constant C-TAU-RES | mask A-RES.is_max_abs_residual: the step attaining the maximum absolute residual drawn with an edge marker | "ln r_ij masked steps", "OLS line (only if fit available)", "residual", "±tau_res = ±0.05" |
| CH-A6 | Historical cross-check at L = 6 | none | `dev`: n; deviation (observable units, log; an exact-zero deviation is drawn hollow at the axis floor with an annotated count, never log(0)) | A-HIST.d00, d11 (EQ-A9); horizontal lines from the constants C-TAU-HIST (10^-12) and C-ETA-E (10^-9), not from any column | mask A-HIST.within_tau_hist (filled) and within_eta_e (marker edge) | "|E_00^P2 - e0_trotter|", "|E_11^P2 - e_noisy_dm|", "tau_hist = 10^-12 frozen standard", "eta_E = 10^-9 separate report" |
| CH-B1 | Observable time series with both references (κ = 1) | L × model ∈ {DEP,DEPH,AMP,RO,CAL} × folding | one panel per obs ∈ {ZPI, PRET, MLOC, CZZ}: n (= Vt, steps, linear); observable units (linear) | B-REF.e_ed, e0_sv (EQ-B8); B-MIT.estimate for NONE, LIN, QUAD, EXP on SHOT and LIN on DM (EQ-B3, EQ-B5) | SHOT series: band B-MIT.ci95_lo/ci95_hi; DM series: band B-MIT.seed_min/seed_max | "E^ED", "E_0", "unmitigated shot", "LIN primary shot", "QUAD shot", "EXP fixed-asymptote ansatz shot", "LIN exact pipeline"; bands: "95% percentile bootstrap interval of the shot record (reported; not the decision interval)", "seed range across fold seeds, exact pipeline; zero by construction under GLOBAL; not a confidence interval" |
| CH-B2 | Revival amplitude error vs noise level, both references | L × model ∈ {DEP,DEPH} × folding × k | `vs_E0`, `vs_ED`: κ (log); ΔA (observable units, linear) | B-PEAKMET.d_amp for LIN, QUAD, EXP with ref = E0 / ED, rows selected by the file's L, model, folding, k and obs with κ taken from each cell (EQ-B7); horizontal ±tau_A from the constants C-TAU-A-ZPI or C-TAU-A-PRET according to the file's obs (EQ-B13) on `vs_E0` | none | "ΔA^(E0) LIN/QUAD/EXP", "ΔA^(ED) LIN/QUAD/EXP", "±tau_A" |
| CH-B3 | Revival timing error vs noise level, both references | as CH-B2 | `vs_E0`, `vs_ED`: κ (log); Δt (steps, linear) | B-PEAKMET.d_t, rows selected as CH-B2 (EQ-B7); horizontal ±tau_t from the constant C-TAU-T | none | "Δt^(E0) …", "Δt^(ED) …", "±tau_t = ±1 step" |
| CH-B4 | Condition status map with boundary | L × model (all five) × folding × extrapolator | `map`: κ columns × k rows; categorical status | B-COND.status_condition (EQ-B14); B-BOUND.kappa_star, family (EQ-B15) | none | five status colours named in the legend; "boundary κ*(k): located solid / unresolved dashed"; "PRIMARY family bold frame / EXPLORATORY" |
| CH-B5 | Deterministic error, uncertainty and bootstrap bias vs depth | L × model ∈ {DEP,DEPH} × folding × κ | `er`: n; ER (log). `ur`: n; UR (log). `beta`: n; β̂ (observable units, linear) | B-STEPMET.er, ur per extrapolator with er_flag / ur_flag as marker styles (EQ-B9, EQ-B10); beta_hat_mit per extrapolator and beta_hat_noisy once (stored on the LIN rows) with beta_flag_* as marker styles (EQ-B10); rows selected by the file's L, model, folding, κ and obs | none (flags as marker styles: value filled, RATIO_LOWER_BOUND triangle at the bound column, undefined hollow at the axis floor) | "ER(n) LIN/QUAD/EXP", "UR(n) …", "bootstrap bias estimate, mitigated LIN/QUAD/EXP (finite-sample, relative to the plug-in)", "bootstrap bias estimate, unmitigated" |
| CH-B6 | Mitigation gain vs depth and time | as CH-B5 | `if`: n (= Vt; time and depth share the axis); IF (log) | B-STEPMET.if_value per extrapolator (EQ-B11), rows selected by the file's L, model, folding, κ and obs; the IF = 1 line from the constant C-IF-ONE | mask B-STEPMET.reportable and if_is_lower_bound: filled if reportable; upward triangle at the bound when the value is a flagged lower bound; nothing omitted | "IF(n) LIN/QUAD/EXP", "IF = 1 reference line" |
| CH-B7 | Global improvement factor vs noise level | L × model ∈ {DEP,DEPH} × folding | `gif`: κ (log); GIF (log) | B-CURVEMET.gif per extrapolator with gif_is_lower_bound as a marker style (EQ-B11), rows selected by the file's L, model, folding and obs with κ from each cell | none | "GIF LIN/QUAD/EXP" (triangle at the bound when flagged) |
| CH-B8 | Time-integrated absolute error vs noise level, both references | as CH-B7 | `tiae_E0`, `tiae_ED`: κ (log); TIAE (observable units × steps, linear) | B-CURVEMET.tiae per extrapolator and unmitigated with n_undefined_steps as a marker annotation (EQ-B8), rows selected by the file's L, model, folding and obs with κ from each cell | none | "TIAE^(E0) …", "TIAE^(ED) …" (annotated count when steps are undefined) |
| CH-B9 | Extrapolation fits at the scheduled revival steps | L × model ∈ {DEP,DEPH} × folding × κ | `fits_dm`: λ_r; observable units - B-RAWDM.value with B-SEEDFIT intercepts, rows pipeline = DM only. `fits_shot`: λ_r; observable units - B-RAWSHOTOBS.value with B-SEEDFIT intercepts, rows pipeline = SHOT only. Rows: the cell from the file's (L, model, folding, κ), obs = ZPI, n joined from the schedule (the two scheduled ZPI revival steps, drawn as separate facets); one plotted value per (n, fold_seed, λ_nominal) | B-RAWDM.value, B-RAWSHOTOBS.value (EQ-B1); B-SEEDFIT.intercept, fit_status (EQ-B3); B-FOLD.lambda_r_1q on a secondary axis (EQ-B2) | none | "per-seed exact density-matrix values", "per-circuit shot-pipeline values", "LIN/QUAD/EXP intercept per seed (pipeline named)", "fit status markers", "single-qubit realized scale (GLOBAL only)"; the two pipelines are never mixed in one panel |
| CH-B10 | Control distinguishability | L × model ∈ {DEP,DEPH} × folding (conditional) | `d`: k; D (observable units, linear), one facet per observable (ZPI, PRET, MLOC); one value per (k, obs) | B-DIST.d with value rules on verdict (DISTINGUISHABLE filled, NOT_DISTINGUISHABLE hollow, INDETERMINATE hollow at the floor, CONTROL_ABSENT absent) (EQ-B16), rows extrapolator = LIN for the file's L, model and folding | band B-DIST.ci95_lo/ci95_hi | "D_k^O per observable"; band "95% percentile bootstrap interval of the difference (exploratory)"; "CONTROL_ABSENT: empty panel with the recorded reason" |
| CH-B11 | Primary-family boundary summary | none | `bound`: L grouped by model and k; κ* (log) | B-BOUND.kappa_star (EQ-B15); row selector family = PRIMARY, pipeline = SHOT, folding = LOCAL, extrapolator = LIN, every model and k | mask B-BOUND.located: filled when located = 1, hollow when 0 (unresolved); edge when non_monotone = 1; hypothesis_component annotated | "κ*(k) PRIMARY family (LOCAL+LIN, shot): located filled / unresolved hollow", "H-2B component outcome", "NON_MONOTONE marker" |
| CH-C1 | Hardware observables at the measured points with both references | none | one panel per obs: point_n (steps, linear); observable units (linear) | B-REF.e_ed, e0_sv at L = 6 (EQ-B8); C-MIT.estimate for NONE, LIN, QUAD, EXP (EQ-B3, EQ-B5); C-MIT.seed_sd | band C-MIT.ci95_lo/ci95_hi | "E^ED (L = 6)", "E_0 (L = 6 noiseless Trotter)", "unmitigated hardware", "LIN primary", "QUAD exactly determined", "EXP fixed-asymptote ansatz", "fold-instance spread (ddof=1 SD), not a confidence interval"; band "95% percentile bootstrap interval of the hardware shot record, conditional on shot exchangeability (reported; not the decision interval)" |
| CH-C2 | Hardware endpoint intervals against tolerance bands (CF-2C and exploratory revival 2 separately) | none | `forest_cf2c`: endpoint (categorical); value - rows family = CF-2C, extrapolator = LIN, revival 1, ref = E0 for every interval, band and status series, ref = ED for the ED-reference series only. `forest_exploratory`: every other (k, extrapolator) row with family = EXPLORATORY, faceted by extrapolator and k; one plotted value per (endpoint, k, obs, extrapolator) | C-END.dec_lo/dec_hi, ci95_lo/ci95_hi, band_lo/band_hi, plugin (EQ-B13, EQ-B12, EQ-B7) with marker style by status (PASS filled, FAIL cross, OVERLAP half-filled, INDETERMINATE hollow, UNAVAILABLE hollow at the axis floor with no interval); C-END.ref_value for ED rows (EQ-B7) | band 1: decision interval at the coverage stored in `dec_level` (0.9875 for CF-2C, 0.95 for exploratory); band 2: reported 95% interval | "decision interval, coverage = dec_level column, drives the status", "95% percentile bootstrap interval (reported)", "closed tolerance band around the E_0 reference", "status marker", "ED reference value (reported only; no interval, no decision)"; the two families are never drawn in one panel |
| CH-C3 | Hardware extrapolation fits per measured point | none | `fits`: λ_r (linear); observable units (linear); one facet per measured point, one plotted value per (point_n, fold_seed) | C-SEEDFIT.intercept, fit_status (EQ-B3); C-DUR.lambda_r (EQ-C4) | none | "LIN/QUAD (EXACT_FIT)/EXP intercept per fold instance", "fit status markers" |
| CH-C4 | QPU usage: binding estimate, baseline and actual | none | `usage`: category; QPU seconds (linear) | C-EST.t_est_cons_s, t_est_1_s, t_lim_s, t_cap_s, u_auth_s (EQ-C1, EQ-C2); C-USAGE.quantum_seconds (EQ-C6) | none | "binding conservative estimate", "single-job baseline (information)", "enforced limit 479 s", "cap 480 s", "actual usage (job.usage())", "U_auth at gate" |
| CH-C5 | Calibration change between snapshots, per identified field and unit | unit ∈ {s, dimensionless, Hz} (the unit inventory; one file per unit) | `abs`: field (categorical); absolute change in the panel's unit. `rel`: field (categorical); relative change (dimensionless) | C-CALDIFF.abs_change, rel_change, rows unit = the file's unit (EQ-C6), with value rules on `status`: PRESENT filled; ZERO_PRE filled on `abs`, hollow at the floor on `rel`; MISSING_POST and NEW_POST as crosses at the floor on both | none (statuses as marker styles) | "absolute change per field, in <unit>", "relative change per field (information only; no drift claim)", "missing post-run", "new post-run" |

File counts per format, stored per chart in the JSON (`n_files_per_format`) and summed by the checker: CH-A1 to CH-A4 three each, CH-A5 nine (L × cell), CH-A6 one; CH-B1 30; CH-B2 and CH-B3 48 each (L × model × folding × k × obs); CH-B4 90; CH-B5 and CH-B6 240 each (L × model × folding × κ × obs); CH-B7 and CH-B8 24 each; CH-B9 60; CH-B10 up to 12; CH-B11 one; CH-C1 to CH-C4 one each; CH-C5 three (one per unit of the inventory): **846 files per format**, 1,692 files in all. Every family parameter appears in the filename, and the checker expands every family in both formats and requires all 1,692 paths to be distinct. Each file exists in both formats. A chart whose family cell was not run, blocked, or has no qualifying control is still written, as an empty panel carrying the recorded reason; no chart is ever omitted.

---

## C6. Manifest and provenance contract

1. **Manifest.** `<bundle>/manifest.json` lists the sha256 of every file under the bundle root except itself, plus every file under the matching figure root (`figures-phase2/*`), with the raw-input subset listed again under `raw_inputs`. It is rewritten by EP-ANALYZE and EP-FIGURES at the end of each run; any entrypoint verifies the manifest of the inputs it consumes before starting and exits 2 on mismatch, and a changed `raw_inputs` hash is always exit 2.
2. **Immutability after a gate.** Every Phase 2C preflight artifact (C-BSEL, C-CALPRE, C-SCHED, C-QPY, C-DUR, C-IDEAL, C-EST, the approved ledger snapshot C-LEDGER, C-REDLOG) is immutable after the second human gate, and its hash is fixed in the immutable pre-gate manifest T-MANGATE, which no later entrypoint rewrites. Accounting that changes after submission (job id, closure, service usage) is written to the separate reconciliation record C-LEDGER-RECON, which names the approved snapshot it reconciles. C-RECHECK, C-JOB, C-RAW, C-USAGE, C-CALPOST and C-LEDGER-RECON are created afterwards and hashed into the mutable bundle manifest T-MAN. A lifecycle fixture in the checker proves that every gate-approved hash stays verifiable after the submission and reanalysis records are added.
3. **Provenance.** `provenance.json` records the Phase 2 source identity (sha256 over sorted `phase2/**/*.py` and `requirements-phase2.txt`), the v0.1.0 sealed identity `ab751d691a4cc3fc623b6044ef70dead0b54df46c0f33f880e574f7a828d6ca2` (unchanged; the sealed source is imported read-only), the sha256 of the `tools/phase2_contract.json` used, the git revision if any (informational), and every entrypoint run with its exit code. Timestamps are the only fields allowed to differ between reproductions.
4. **Environment.** `environment_phase2.json` is written once by EP-2A and verified equal (excluding nothing) by every later entrypoint; a difference is a contract violation (exit 2), because "one Phase 2 implementation and one environment" is a rule of the preregistration (§3.2).
5. **Deviations.** `deviations.md` follows prereg §6.11: present, non-empty, with an explicit `DEVIATIONS: NONE` or `DEVIATIONS: ENUMERATED` first line; the manifest copies that declaration. Absence or emptiness fails the manifest check.
6. **Bundle roots, protected paths, and adding derived artifacts.** *Protected, never written:* `results/minimal/**`, and the canonical `figures/` directory including anything inside it (creating a file or subdirectory there counts as writing), in any letter case. *Bundle roots:* a bundle is `results/<name>` with `<name>` non-empty and not `minimal` in any letter case; the default bundle is `results/phase2` and the reproduction bundle is `results/phase2-repro`; the phase entrypoints write into the bundle's own subdirectories `results/<name>/phase2a`, `phase2b`, `phase2c`, which are the only accepted bundle-internal targets; figure roots are `figures-<name>` beside the canonical directory (`figures-phase2`, `figures-phase2-repro`), never inside `figures/`. *Raw inputs are immutable, derived artifacts are added:* the outputs of EP-2A, EP-2B and EP-2C-SUBMIT are the bundle's raw inputs, hash-listed in the manifest's `raw_inputs` set as soon as they are written; EP-ANALYZE and EP-FIGURES write their derived artifacts into the **same** bundle root and never overwrite a raw input (the raw hashes are verified before and after the run; any change is exit 2). *Reproduction:* EP-REPRO writes to a bundle root different from its `--bundle` input and never writes into that input; it refuses an `--out` that resolves to the input or to a protected path. Refused roots exit 3 before any write. The checker evaluates this policy on the documented commands and on the accepted and refused examples stored in the JSON; the v0.1.0 canonical guard is never relaxed.

---

## C7. The offline checker and its synthetic fixtures (runnable today)

`tools/phase2_contract_check.py` reads `tools/phase2_contract.json`, `docs/prereg-phase2.md`, this document, and the three historical documents it cross-references (`docs/design.md`, `docs/prereg-p2zero-outline.md`, `docs/followup-study-draft.md`), every path resolved relative to the repository root or to the directory given by `--root`. It imports only the standard library, NumPy (the pinned `numpy==2.2.6`, so the resampling reference is the frozen `default_rng` plus `multinomial` construction of §C4.5) and SciPy (the pinned `scipy==1.17.1`, so the exponential `avoid_log` reference is the same `scipy.optimize.curve_fit` invocation as the pinned Mitiq fallback, §C4.3), touches no network, imports nothing from `zne_scars`, `qiskit` or `mitiq`, runs no experiment, writes nothing, and finishes in a second or two. It prints one line per check and a summary line.

**Exit-code semantics (EP-CHECK), in the style of §C8:**

| exit code | meaning |
|---|---|
| 0 | every check ran and passed |
| 1 | every check ran and at least one failed; each failure is printed with its detail |
| 2 | an input file is missing or unreadable (absent path, undecodable text, or unparseable JSON), so no check could be run; the message names the offending path and nothing else is printed |

A failed check and an absent input are different events: a missing contract file is not a wrong contract, and a caller must be able to tell them apart. Any other uncaught error is a defect in the checker itself and is not mapped to a code.

**Algebra fixtures (closed-form answers).** Exactly additive synthetic cells ($E_{11} = E_{10}E_{01}/E_{00}$) give $I(n) \equiv 0$ to floating-point; an interacting fixture with $r_{11} = r_{10} r_{01} e^{-0.2}$ gives $I(n) = 0.2$; the budget propagation reproduces the closed-form $\eta_r$, $\eta_A$, $\eta_I$; the OLS slope on $\ln r = 0.3 - 0.05 n$ returns $g = 0.05$ with zero residuals; the peak extractor on a synthetic cosine grid finds the known peaks and the parabolic timing of a known parabola exactly; the trapezoid quadrature on a piecewise-linear error returns the analytic integral; the percentile interval on a fixed synthetic replicate set with a fixed seed returns the known quantiles; the global-folding arithmetic on a 10-operation list gives the stated counts; the exponential fit recovers the parameters of an exact synthetic exponential. **Amendment A-2 fixtures:** five zero observations give a log-mode limit of exactly 0 (sign 0, clamped), not $\approx 10^{-6}$; $x = (1, 1.25, 1.5, 1.75, 2)$, $y = x/4$ over eight identical seeds gives the pinned `polyfit` intercept $-4.97\times10^{-17}$, sign $-1$, a clamp and the `avoid_log` aggregate $0.1353653348$, not the former log-mode $0.1325890835$; intercepts $\pm 10^{-9}$ from the asymptote give signs $\pm 1$; a nonzero asymptote follows the same rule; one sign-0 seed switches the whole step to `avoid_log`; masks of 0, 1 and 2 steps leave all four Phase 2A statistics null with `TOO_FEW_POINTS` and `INCONCLUSIVE` while a 3-step mask yields values; the DM seed range reproduces the Reviewer counterexample ($[0, 1]$, `OVERLAP`), per-seed parabolic timings, earliest-tie matching, and nulls the whole range on any undefined seed or an edge peak. **Rank boundary fixtures (amendment A-1):** the `EXP` reference implementations, driven by the JSON minima, are exercised at one, two and three distinct realized abscissas in both modes: one is `FIT_FAILURE` under both phases; two (with or without duplicate points) is `FIT_FAILURE` under the Phase 2B minimum of 3 and a fit under the Phase 2C minimum of 2; three is a fit under both; a repeated abscissa is shown to change the regression (kept as recorded) while counting once for the rank; one rank-deficient seed among eight nulls the Phase 2B step aggregate with no surviving-seed mean, in log mode and under a clamp-forced `avoid_log` rerun; and a bootstrap over a record with two distinct realized abscissas yields an undefined interval under Phase 2B for every replicate (abscissas are fixed under resampling) and a defined interval under the Phase 2C minimum.

**Edge-case fixtures (declared verdict produced).** Sign flip → `SIGN_FLIP` and `INCONCLUSIVE`; ratio above one beyond the budget → `RATIO_ABOVE_ONE` in the primary and `FIT_UNAVAILABLE` in the secondary; below-mask step → excluded from the statistics but present in the table; fewer than three masked steps → `TOO_FEW_POINTS` and `INCONCLUSIVE`; singular fit → `FIT_FAILURE`; constant replicates → `DEGENERATE_CONSTANT` and `INDETERMINATE`; saturated counts → `DEGENERATE_SATURATED`; mask-boundary reference ($\lvert E_{00}\rvert = 0.1 + 10^{-10}$) → `MASK_BOUNDARY`, `INCONCLUSIVE`, and the secondary fit unavailable; a schedule with fewer than two peaks → `UNAVAILABLE`; the three-point timing window → `TIMING_UNTESTABLE`, with the bound $\lvert t^* - n\rvert \le 0.5$ demonstrated over a grid of drops, and a five-point window producing a timing `FAIL`.

**Statistics fixtures.** Undefined replicates: the exact tolerated counts (4 / 12 / 49) pass and one more fails at each of the three levels, and an alternating placement is shown to be rejected by the rule; the aggregation-order fixture of §C4.3 returns 0 and not 0.25; the unphysical intercept $(0.9, 0.6, 0.3) \mapsto 1.5$ is flagged `UNPHYSICAL_ESTIMATE` and cannot pass; the near-tied projector weights order deterministically; the status combination (`FAIL`, `INDETERMINATE`, `PASS`, `PASS`) is `FAIL`; an interval crossing a band edge is `OVERLAP`; an interval disjoint from the band is `FAIL`; a located boundary requires a `FAIL` at the next level.

**Schema and cross-consistency.** Every `ARTIFACT.column` referenced by any chart series, band, mask or equation is declared; every declared column is referenced or carries a usage note; dtypes are from the allowed set and units are non-empty; every chart lists both `png` and `pdf`; every chart that plots a mitigated observable includes an `e_ed` series; every constant's render string appears in each document it is required in and matches its value; every `§` cross-reference in the two Phase 2 documents resolves to a heading (bare `§n.m` to the preregistration, `§Cn` to this document, `design.md §n` and `outline §n` to those documents); the JSON three-way rule, the joint-pass rule and the tie orders agree with the prose vocabularies; the matrix totals (150 cells: 72 run, 72 not run, 6 blocked; 12 conditional; 280,080 unconditional executions; 350,208 if everything runs) and the uniqueness of every `seed_simulator` value across all enumerated cells are recomputed from the machine-readable matrix; the rank rule is checked across every surface (`phase2b.rank_rule` = {2, 3, 3} and `phase2c.transpilation.rank_rule` = {2, 3, 2} numerically, the constants C-EXP-MIN-2B / C-EXP-MIN-2C, the JSON prose, prereg §4.3, §5.4 and §6.2, this document's §C4.2 and §C4.3, and the checker's own minima), and the dated amendment record with its historical identities must be present, so that a mismatch between any two of these surfaces fails the checker.

**Chart rendering against an independent oracle.** The checker carries two tables written from the prose meanings in §C5, not derived from the JSON: a value-rule oracle (for every flag column, each flag value → marker, value state and the source of the drawn value: the series' own column, its declared `bound_for` column, or nothing) and a mask oracle (for every mask column, rows covering each meaning: in and out of mask; located and unresolved; monotone and non-monotone; positive, and exactly zero on a logarithmic axis; a zero and a positive undefined-step count with and without a value; each endpoint status). Every series that carries value rules or a mask must have an oracle entry, or the check fails. Each case is composed by the same three-axis point routine used for real artifacts on a synthetic row in which the own column, every bound column and every other bound column carry distinct values, and the marker, the value state and the drawn value must equal the oracle's, so substituting one declared column for another (for example `er_bound` for `ur_bound`), inverting a mask's polarity, changing a threshold, or swapping two status styles fails even though every column is declared. Separately, a value rule may draw a non-null column other than the series' own only if that column declares `bound_for` equal to the series' column; a mask condition on a never-null column may not test for null; a `style_when` map must cover exactly the column's vocabulary; and a row carrying distinct ER and UR lower bounds must render the ER bound on every ER series and the UR bound on every UR series.

**Whitespace.** Because the deliverables are untracked, the verification set includes `git diff --check --no-index /dev/null <file>` for each deliverable, which inspects whitespace without touching the index.

---

## C8. Entrypoints and the one-command reproduction contract

### C8.1 Runnable today

| id | command | inputs | outputs | exit codes |
|---|---|---|---|---|
| EP-CHECK | `.venv/bin/python tools/phase2_contract_check.py` | the JSON, the two Phase 2 documents, the three historical documents | stdout report; writes nothing | 0 all checks pass; 1 at least one failed (each printed); 2 input missing or unparseable |
| EP-TESTS | `.venv/bin/python -m pytest -q tests/test_phase2_contract.py` | the checker; synthetic fixtures under `tmp_path` | pytest report | 0 pass; nonzero failure |

Both are deterministic, offline, and use no experiment code.

### C8.2 Future entrypoints (contracts; none exists today)

> **These commands cannot be run today.** They name a package `phase2/`
> and an environment `.venv-phase2` that do not exist. Each is a contract
> a later implementation must satisfy. The `phase2/` package lives outside
> the sealed paths and has its own identity hash (§C6.3); it may import
> the sealed v0.1.0 modules read-only.

**EP-2A - Phase 2A factorial**
`.venv-phase2/bin/python -m phase2.run_phase2a --contract tools/phase2_contract.json --out results/phase2/phase2a`
Inputs: `phase2a` section of the JSON; sealed modules read-only; `results/minimal/steps.csv` read-only for the cross-check. Outputs: A-CIRC, A-REF, A-CELLS, A-DENSE, A-INT, A-SEC, A-RES, A-HIST, A-VERD, B-ENV. Order: A-CIRC and A-REF for every $L$; the $(0,0)$ cells and the mask columns of A-INT written before any noisy cell executes; the noisy cells; A-DENSE; verdicts. Exit codes: 0 completed (any verdict); 1 unexpected error with `CELL_FAILED` rows left in place; 2 contract violation (schema, hash, ordering); 3 canonical-guard refusal. Determinism: density-matrix values reproducible to $\eta_E$ on any platform, byte-identical on the same hardware and environment. Failure behaviour: no value is ever substituted; every failure is a flag or a `CELL_FAILED` row.

**EP-2B - Phase 2B matrix**
`.venv-phase2/bin/python -m phase2.run_phase2b --contract tools/phase2_contract.json --cells all --out results/phase2/phase2b`
Inputs: `phase2b.matrix_cells` and `control_cells`; C-CALPRE only for `CAL` cells (absent → those cells stay blocked). Outputs: B-REF, B-SCHED, B-CTRL, B-FOLD, B-RAWDM, B-RAWSHOT, B-CELLLOG. Order: B-REF and B-SCHED for every $L$ (noiseless), B-CTRL (noiseless selection), control references, run cells in `cell_index` order, conditional cells. Exit codes: 0 every run cell completed; 1 unexpected error with `CELL_FAILED` rows; 2 contract violation; 3 canonical-guard refusal. Determinism: shot records byte-identical on the same Aer build given `seed_simulator`; DM values to $\eta_E$. Failure behaviour: a failed cell is rerun once with identical seeds after a logged deviation; a second failure stays `CELL_FAILED`.

**EP-ANALYZE - analysis of saved observations**
`.venv-phase2/bin/python -m phase2.analyze --contract tools/phase2_contract.json --results results/phase2 [--replay]`
Inputs: every raw artifact of EP-2A, EP-2B and EP-2C-SUBMIT that exists. Outputs: B-RAWSHOTOBS, B-SEEDFIT, B-MIT, B-BOOTPEAK, B-STEPMET, B-PEAKMET, B-CURVEMET, B-END, B-COND, B-BOUND, B-DIST, C-SEEDFIT, C-MIT, C-BOOTPEAK, C-PEAKMET, C-STEPMET, C-END, C-VERD, T-MAN, T-PROV. Exit codes: 0 complete; 1 unexpected error; 2 contract violation or manifest mismatch; 4 with `--replay`, regenerated quantiles or peak replicates differ from the stored ones. Determinism: byte-identical outputs in the same environment for the same inputs. Failure behaviour: no survivor averaging; every undefined quantity is null with a flag.

**EP-FIGURES - charts**
`.venv-phase2/bin/python -m phase2.make_figures --contract tools/phase2_contract.json --results results/phase2 --out figures-phase2`
Inputs: the chart-input artifacts of §C5. Outputs: every chart of §C5 in both formats under `figures-phase2/`. Exit codes: 0 every chart written; 2 a chart-input column is missing; 3 output-root refusal (`figures/` and `results/minimal` refused; `figures-phase2` and `figures-phase2-repro` permitted, §C6 item 6). Determinism: png byte-identical in the same environment; pdf differs only in its creation-date field (design.md §20 A2-2). Failure behaviour: an unrun family cell yields an empty panel with the recorded reason, never an omitted file.

**EP-2C-PREFLIGHT - hardware preflight (first human gate: read-only service access)**
`.venv-phase2/bin/python -m phase2.preflight_phase2c --contract tools/phase2_contract.json --results results/phase2`
Inputs: B-REF for $L = 6$, state `Z2`; live read-only backend list and calibration at gate time. Outputs: C-BSEL, C-CALPRE, C-SCHED, C-QPY, C-DUR, C-IDEAL, C-EST, C-LEDGER, C-REDLOG, T-MANGATE. Exit codes: 0 preflight passed (fits, $E_1 \subseteq \mathcal{P}$, all checks); 3 blocked or abandoned (reason in C-SCHED.blocked_reason or C-REDLOG.abandoned); 2 contract violation; 1 unexpected error. Determinism: deterministic given the snapshot. Failure behaviour: fail closed; any unverifiable condition is exit 3 and no submission artifact is produced.

**EP-2C-SUBMIT - the one submission (second human gate)**
`.venv-phase2/bin/python -m phase2.submit_phase2c --contract tools/phase2_contract.json --results results/phase2 --gate-record <path>`
Inputs: every EP-2C-PREFLIGHT output unchanged (hashes verified); the gate record. Outputs: C-RECHECK, C-JOB, C-RAW, C-USAGE, C-CALPOST, C-CALDIFF, C-LEDGER-RECON. Exit codes: 0 job completed and recorded; 3 recheck failed, aborted before submission; 5 job cancelled by the service at `max_execution_time`, usage recorded; 1 unexpected error. Determinism: none for the acquisition (prereg §6.9 scope 3); the records are complete. Failure behaviour: one submission only; any abort requires a new gate.

**EP-REPRO - one-command reproduction of a bundle**
`.venv-phase2/bin/python -m phase2.reproduce --contract tools/phase2_contract.json --bundle results/phase2 --out results/phase2-repro`
Inputs: a complete bundle with T-MAN. Behaviour: runs EP-2A, EP-2B, EP-ANALYZE and EP-FIGURES into `results/phase2-repro/` and `figures-phase2-repro/`, then compares against the bundle under the prereg §6.9 scopes (simulator re-acquisition and reanalysis; hardware acquisition is never rerun, only reanalysed from the bundle's saved counts). Outputs: the reproduced artifacts and a comparison report listing every differing quantity with its scope and tolerance. Exit codes: 0 reproduced within scope; 1 unexpected error; 2 manifest or contract mismatch; 4 reproduction discrepancy. Determinism: as its component entrypoints. Failure behaviour: never writes into the bundle it compares against.

### C8.3 What "reproduction" means, by scope

| Scope | What is rerun | Guarantee | Entrypoint |
|---|---|---|---|
| Contract validation | nothing scientific | checker passes | EP-CHECK (today) |
| Reanalysis | analysis only, from saved counts and seeds | byte-identical outputs in the same environment; `--replay` reproduces stored quantiles and peak replicates | EP-ANALYZE |
| Simulator re-acquisition | EP-2A and EP-2B | DM values to $\eta_E$; shot records byte-identical on the same Aer build | EP-REPRO |
| Hardware re-acquisition | never | none; a new job is a new experiment with its own gates | - |

---

## C9. Traceability matrix

The matrix has one row per (chart, panel, series). The columns are: chart id → panel id → series name → artifact path → column → equation id → producing command (the entrypoint that writes the column, per §C2, and EP-FIGURES which draws it). It is generated by EP-CHECK from the chart inventory and printed when the checker is run with `--traceability`; every row must resolve, and the check fails otherwise. The first rows, rendered here so the format is fixed:

| chart | panel | series | file | column | equation | command |
|---|---|---|---|---|---|---|
| CH-A1 | ratios | r10 | `results/phase2/phase2a/interaction.csv` | `r10` | EQ-A1 | EP-2A (write), EP-FIGURES (draw) |
| CH-A1 | ratios | r01 | `results/phase2/phase2a/interaction.csv` | `r01` | EQ-A1 | EP-2A, EP-FIGURES |
| CH-A1 | ratios | r11 | `results/phase2/phase2a/interaction.csv` | `r11` | EQ-A1 | EP-2A, EP-FIGURES |
| CH-A3 | interaction | i_n | `results/phase2/phase2a/interaction.csv` | `i_n` (band `i_lo`, `i_hi`) | EQ-A3, EQ-A5 | EP-2A, EP-FIGURES |
| CH-B1 | ZPI | lin_shot | `results/phase2/phase2b/mitigated.csv` | `estimate` (band `ci95_lo`, `ci95_hi`), rows extrapolator = LIN, pipeline = SHOT | EQ-B3, EQ-B5, EQ-B12 | EP-ANALYZE, EP-FIGURES |
| CH-B4 | map | status | `results/phase2/phase2b/conditions.csv` | `status_condition` | EQ-B14 | EP-ANALYZE, EP-FIGURES |
| CH-B11 | bound | kstar | `results/phase2/phase2b/boundary_2b.csv` | `kappa_star`, `located` | EQ-B15 | EP-ANALYZE, EP-FIGURES |
| CH-C2 | forest | dec | `results/phase2/phase2c/endpoints_hw.csv` | `dec_lo`, `dec_hi`, `status` | EQ-B12, EQ-B13 | EP-ANALYZE, EP-FIGURES |
| CH-C4 | usage | cons | `results/phase2/phase2c/usage_estimate.json` | `t_est_cons_s` | EQ-C1 | EP-2C-PREFLIGHT, EP-FIGURES |

Every other row follows the same pattern and is listed in full by the checker. The producing command for each artifact is the `produced_by` field of §C2; every plotted value therefore traces to a saved column and an equation, and no chart draws a value that is not saved.

---

## C10. Edge-case policy index

| Flag | Where declared | Effect |
|---|---|---|
| `MISSING_OR_NONFINITE`, `BELOW_MASK`, `MASK_BOUNDARY`, `REFERENCE_MISMATCH`, `NUMERICS_UNVALIDATED`, `SIGN_FLIP`, `RATIO_UNRESOLVED`, `RATIO_ABOVE_ONE`, `RATIO_NEAR_ONE`, `NUMERICAL_INCONCLUSIVE`, `TOO_FEW_POINTS`, `FIT_FAILURE` | prereg §3.8 | Phase 2A primary and secondary effects as tabulated there; blocking flags give `INCONCLUSIVE` |
| `FIT_UNAVAILABLE`, `ANTI_ATTENUATION`, `RESIDUAL_ADEQUATE`, `RESIDUAL_INADEQUATE` | prereg §3.9 | secondary fit availability and adequacy |
| `HISTORICAL_CONSISTENT`, `HISTORICAL_INCONSISTENT` | prereg §3.2 | cross-check verdict, never a factorial input |
| `INTERP_FALLBACK`, `NO_INTERIOR_PEAK`, `NO_SCHEDULED_PEAK`, `WINDOW_TRUNCATED`, `ED_PEAK_UNAVAILABLE`, `TIMING_UNTESTABLE` | prereg §4.6, §5.9 | schedule and matching; `TIMING_UNTESTABLE` and `NO_INTERIOR_PEAK` never pass |
| `EXP_FIT_FAILED`, `EXACT_FIT`, `CELL_FAILED`, `PARTIAL_SHOTS`, `CAL_MISSING_CHANNEL` | prereg §4.4, §6.2, §6.10, §4.2 | fit and execution records |
| `RATIO_LOWER_BOUND`, `RATIO_ZERO_OVER_ZERO`, `RATIO_UNDEFINED` | prereg §4.7 | ratio rule for ER and UR |
| `DEGENERATE_CONSTANT`, `DEGENERATE_SATURATED`, `DEGENERATE_COLLAPSED`, `UNDEFINED`, `UNPHYSICAL_ESTIMATE`, `UNPHYSICAL_INTERVAL` | prereg §6.3, §6.7 | endpoint `INDETERMINATE` or never `PASS` |
| `NON_MONOTONE`, `BELOW_MIN_FAIL`, `UNRESOLVED_AT_MIN`, `AT_OR_ABOVE_MAX` | prereg §4.8 | boundary classification |
| `THRESHOLD_MARGINAL`, `TIE_MARGINAL`, `WEIGHT_MARGINAL`, `SCORE_MARGINAL` | prereg §4.9, §5.2 | marginality records; never change an ordering |
| `REPRO_AMBIGUOUS` | prereg §6.9 | discrete reproduction disagreement, both results kept |
| `DISTINGUISHABLE`, `NOT_DISTINGUISHABLE`, `INDETERMINATE`, `CONTROL_ABSENT` | prereg §4.7 | control comparison verdicts |
