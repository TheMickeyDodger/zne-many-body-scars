# Phase 2 Preregistration: Channel Additivity, Physics-Aware Simulator Benchmark, and IBM Hardware Confirmation

**Status (as written 2026-09-07, historical):** preregistration draft for
review. Written 2026-09-07 against baseline
`657683c09459b9289a07dab0b27497882a5c819f` (branch
`phase2/revival-preservation`). Nothing in this document has been executed.
No Phase 2 code exists. No Phase 2 data exist. No IBM workload has been
submitted or prepared. The first gate is document review, not execution.

**Status update, 2026-09-08 (A-1). HISTORICAL: written before A-2 and the pilot acquisition; every "no Phase 2 data" statement in this paragraph was true on its date and is superseded by the current-status paragraph that follows. Original wording kept.** Amendment A-1 (below) is human-approved and pre-data. A fresh canonical read-only review of the amended artifacts is pending; implementation and the measured feasibility pilot resume only after that approval. What exists today: the offline Phase 2 environment `.venv-phase2` (pins in `requirements-phase2.txt`, identical to `requirements.txt`) and unexecuted scaffolding under `phase2/` (identity, contract access and observable-weight modules; no simulator, estimator or bootstrap code has run). No Phase 2 scientific execution of any kind has taken place: no `results/phase2*` bundle, no `figures-phase2*` root, no Aer execution, no fit, no bootstrap; `results/minimal/` is byte-identical to the baseline. No IBM workload has been submitted or prepared.

**Current status (2026-09-08, after A-2 and its correction; supersedes the paragraph above).** No CONTRACTED Phase 2 scientific result exists: no contracted `results/phase2*` bundle, no `figures-phase2*` root, no bootstrap, and `results/minimal/` is byte-identical to the baseline. Real Phase 2 execution HAS occurred outside any contracted result: Aer timing, method-selection and seed-determinism probes (evidence `1b-01`), and a separately labelled pilot acquisition `results/phase2-pilot` that executed Aer and produced folded circuits, raw density-matrix values and raw shot records for 17 completed of 162 work units under the pre-A-2 `phase2` source before it was stopped; it is quarantined, identity-mismatched with the current source, and its values are never used. `phase2/` holds estimator, simulation and pilot code that has run in tests and in that pilot. No IBM workload has been submitted or prepared. The corrected A-2 candidate was ACCEPTED on 2026-09-08 (independent review round 06 approved it; accepted `phase2` source identity `b7937c07302640fd9949c55f3cbddbc5415937caa76e78041021e65bed219f2b`). Feasibility of the full matrix is unassessed, and the during-run monitoring method carries a documented production NO-GO.

**Machine-readable companion:** `tools/phase2_contract.json` holds every
constant, threshold, matrix cell, schema and chart named here. Where a number
appears in this document and in the analysis contract
(`docs/phase2-analysis-contract.md`), the JSON value is authoritative and
`tools/phase2_contract_check.py` checks that the three agree.

**Amendment A-1 (2026-09-08, pre-data, human-approved).** Before any Phase 2
data existed (no `results/phase2*` bundle, no `figures-phase2*` root, no Aer
execution, no fit, no bootstrap; `results/minimal/` byte-identical to the
baseline), the independent read-only review of task 20260908-105435-177fe7
returned a canonical `REJECT`: this document's §4.3 required three distinct
realized abscissas for a Phase 2B `EXP` fit, while the analysis contract
§C4.2 and the checker's reference implementations required two, and the
JSON stated no Phase 2B value, so the frozen artifacts could not settle the
rule. The human decision, recorded as amendment A-1 in
`tools/phase2_contract.json` (`amendments`), fixes the Phase 2B `EXP`
minimum at **three** distinct realized abscissas everywhere in Phase 2B
(§4.3, `phase2b.rank_rule`, constant C-EXP-MIN-2B) and leaves the Phase 2C
minimum at **two** (§5.4, `phase2c.transpilation.rank_rule`, C-EXP-MIN-2C).
Nothing else changed. The pre-amendment identities are historical and are
retained in the JSON record: this document
`913831adf38828f9802fd55fb94f560cc4f7e16e48c3a62afe6336f3cffc19d4`, the
analysis contract
`97e67e68e0368c621393af118b7c0dc1f8f2018c04c9cfd0eef01c01ab14cdeb`, the JSON
`f77e15326baf9012c2799d0b7417556ff156ffb4e5d275cedd7be02a49e5b266`, the
checker `8d20d8c7d776e4c9b2f4ff8a69f671419c72a549bc73afe990a9cd6bc426a503`
and its tests
`6d5dc35a397db5708eabb4b34a92f75476f8405622dfaf5d975f5f8301a2f19b`. The
original `REJECT` stands as the record that triggered the amendment.

**Amendment A-2 (2026-09-08, human-approved; approval precedes the affected
analyses).** Three rules that the independent read-only review (round 04,
canonical `REJECT`) found under-specified or wrongly implemented were fixed by
human decision, recorded as `amendments[A-2]` in the JSON: (1) the `EXP`
sign is the pinned mitiq v1.0.0 / NumPy convention, `np.sign` of the
`numpy.polyfit` linear intercept minus the asymptote, including
`sign(0) = 0`, in both modes (§4.4, contract §C4.3); (2) fewer than
$k_{\min} = 3$ masked steps makes every affected Phase 2A statistic
undefined, with `TOO_FEW_POINTS` and `INCONCLUSIVE` (§3.6, §3.8); (3) the
density-matrix companion's seed range takes the amplitude of all eight seeds
at the aggregate-matched peak step and the timing of each seed's own matched
peak inside the same scheduled window, and any undefined required seed nulls
the whole range (§4.8). The exact primary tail probability is $1/9600$;
the rendering $1.0417 \times 10^{-4}$ is never used in computation (§6.3).
Scope qualifier, stated truthfully: no disputed `EXP` fit, no small-mask
Phase 2A statistic and no density-matrix seed-range analysis had run when
A-2 was approved; real Aer timing, method-selection and seed-determinism
probes and a separately labelled pilot acquisition
(`results/phase2-pilot`, quarantined, never a contracted result) had
already produced circuits, raw simulator measurements and pilot data. The
pre-A-2 identities are retained in the JSON record.

**Correction to A-2 (2026-09-08, after an independent review rejected
the first A-2 candidate; `amendments[A-2].correction_20260908` in the
JSON).** The rules above are unchanged. Their implementation was corrected:
the `EXP` sign is decided by the scalar `numpy.polyfit` call for every fit
(a closed-form fast path with a guard band was removed; the two intercepts
disagree in sign on clustered realized abscissas, so no equivalence is
claimed); after review round 05 the `EXP` log-mode fit is likewise the
pinned scalar `numpy.polyfit` weighted call for every fit, replacing
closed-form normal equations (the `LIN`/`QUAD` intercepts remain ordinary
least squares as specified); and every non-finite required density-matrix seed value (`NaN`,
$\pm\infty$) is undefined exactly like a missing one (§4.8).

**Sections.** §1 scope and boundaries. §2 shared definitions and the three
references. §3 Phase 2A, channel additivity. §4 Phase 2B, physics-aware
simulator benchmark. §5 Phase 2C, IBM hardware confirmation. §6 statistics.
§7 outputs. §8 stopping rules and deviations. §9 sources.

---

## 1. Scope and boundaries

### 1.1 What Phase 2 is

Phase 2 has three parts.

- **Phase 2A** measures whether the single-qubit and two-qubit depolarizing
  channels of the v0.1.0 noise model attenuate the staggered magnetization
  additively, using a complete $2\times 2$ factorial and a curve-level
  interaction statistic.
- **Phase 2B** measures, in a classical simulator, where circuit depth or
  noise strength causes zero-noise extrapolation (ZNE) to stop preserving
  both the amplitude and the timing of the scar revival, for
  $L \in \{4, 6, 8\}$ and several noise channels.
- **Phase 2C** is a confirmatory run of the $L = 6$ revival-preservation
  endpoints on one IBM Quantum backend, designed to fit strictly below 480
  estimated QPU seconds and gated behind a second human decision.

### 1.2 What this document supersedes

`docs/prereg-p2zero-outline.md` (the $p_2 = 0$ outline) and
`docs/followup-study-draft.md` (the Phase 2 planning notes) are historical
records. This document supersedes their analysis plans as follows.

| Historical item | Status under this preregistration |
|---|---|
| Outline §2 hypothesis intervals H-G / H-L for $g_1$ | Superseded. The single-rate slope is secondary here (§3.9); no H-G / H-L verdict is issued. |
| Outline §4 mask $\lvert E_0(n)\rvert \ge 0.1$ | Adopted unchanged as the Phase 2A mask (§3.4). |
| Outline §4 pointwise adequacy gate $r > 1 + 10^{-9}$ | Superseded by the budget-based gate $r_{ij}(n) > 1 + \eta_r^{ij}(n)$ of §3.8, which applies to the secondary fit only. |
| Outline §2/§4 rate rules: fitted $g \in [-10^{-9}, 0)$ treated as $0$; $g < -10^{-9}$ is anti-attenuation | Retained unchanged for the secondary fit (§3.9). |
| Outline §4 residual tolerance (never set) | Set here as $\tau_{\mathrm{res}} = 0.05$ for the secondary fit (§3.9). |
| Outline §5 additivity criterion $\lvert\Delta\rvert \le \tau_{\text{add}}$ | Superseded by the curve-level equivalence assessment on $I(n)$ (§3.5 to §3.7). $\Delta$ is reported as a secondary quantity without a pass/fail threshold. |
| Planning notes Q7 as a recomputation of the recorded combined arm (Tier A, command R-7) | Unchanged. It remains a valid post-hoc diagnostic of the v0.1.0 data and is cited in §3.9. |
| Planning notes Q7/Q8 as the prospective single-rate primary analysis for the factorial (FC-5, FC-6, R-B1, R-B2) | Superseded by §3: the curve-level interaction is primary and the single-rate slope is secondary. |
| Planning notes FC-1 to FC-4, Q1 to Q6, R-1 to R-6 | Unchanged. They concern the recorded v0.1.0 data only. |

The v0.1.0 result, its metrics, its verdict and its qualifications
(`docs/results-minimal.md`, `README.md` §2) are unchanged by anything here.

### 1.3 Boundaries of this task

This task produces documents and an offline contract checker. It does not:

- run any simulator or exact-diagonalization computation for Phase 2;
- create any Phase 2 result data, figure or `results/` subdirectory;
- touch IBM Quantum in any way;
- change sealed source (`src/**/*.py`, `scripts/*.py`, `requirements.txt`,
  `pyproject.toml`) or the canonical evidence (`results/minimal/`,
  `figures/`).

Every Phase 2 computation named below is a future action. Future entrypoints
are specified as contracts in `docs/phase2-analysis-contract.md` and are
labelled there as not yet implemented.

### 1.4 Writing conventions

Inference is marked **(inference)** where a statement goes beyond a cited
source or a recorded artifact. Quantities read from the recorded canonical
bundle are marked **(recorded, v0.1.0)**. Design choices that could have been
made otherwise are marked **(design choice)** and justified in place.

---

## 2. Shared definitions

### 2.1 Carried forward unchanged from design.md

The following are identical to `docs/design.md` and are not restated in
full here.

- Hamiltonian: the mixed-field Ising model of design.md §3 on an open chain
  of $L$ sites with the boundary longitudinal field halved, $V = 1$,
  $\Omega = 0.24$.
- Time evolution: first-order Trotter, $\Delta t = 1$, so step $n$ equals
  $Vt = n$ (design.md §6). Gate angles exactly as design.md §7.
- Initial state: the Néel state $\lvert Z_2\rangle$ with site 1 in
  $\lvert 0\rangle$; site $i$ maps to Qiskit qubit $q_{i-1}$; site 1 is the
  rightmost bit of a count string (design.md §4).
- Compilation: basis $\{rz, sx, x, cx\}$, `optimization_level=0`,
  `seed_transpiler=7` (design.md §7, §15).
- Fold-seed set $\{1000, \dots, 1007\}$ and the two-qubit-only folding policy
  `fidelities={"single": 1.0, "double": 0.99}` for local folding
  (design.md §10, §16).
- The v0.1.0 noise rates $p_1 = 10^{-3}$ on $\{sx, sxdg, x\}$ and
  $p_2 = 10^{-2}$ on $cx$, with $rz$ clean (design.md §8), as the baseline
  noise level.

### 2.2 Where Phase 2 extends the conventions

| Extension | Where | Note |
|---|---|---|
| Chain lengths $L \in \{4, 6, 8\}$ | §3, §4 | $L = 6$ is the v0.1.0 size and the hardware size. |
| Noise channels: dephasing (primary), amplitude damping, readout error, calibration-derived model (secondary) | §4.2 | New Aer channels; constructions cited in §9. |
| Noise levels $\kappa \in \{0.25, 0.5, 1, 2, 4\}$ multiplying $(p_1, p_2)$ | §4.2 | $\kappa = 1$ is the v0.1.0 level. |
| Scale factors $\{1, 1.25, 1.5, 1.75, 2\}$ (simulator) and $\{1, 1.5, 2\}$ (hardware) | §4.3, §5 | v0.1.0 used $\{1, 1.5, 2\}$. |
| Global folding alongside local folding | §4.3 | Local folding is the v0.1.0 method. |
| Quadratic and exponential extrapolators alongside linear | §4.4 | Linear stays primary. |
| Observables: return probability, local magnetization, nearest-neighbour $ZZ$ correlator alongside $\langle Z_\pi\rangle/L$ | §4.5 | All from one computational-basis measurement. |
| Step window $n = 1, \dots, 48$ for Phase 2B and 2C | §4.1, §5 | Phase 2A keeps $n = 1, \dots, 40$. |
| Shot count 4096 on hardware | §5 | Simulator shot pipeline keeps 8192. |

Nothing else changes. In particular the Hamiltonian parameters, the Trotter
scheme, the basis, the optimization level, the transpiler seed, the initial
state and the fold-seed set are not extended.

### 2.3 The three references, kept distinct

Three quantities are used throughout and are never interchanged. Each has
its own symbol, its own column in every table, and its own line in every
chart where it applies.

- $E^{\mathrm{ED}}(t)$: the **continuous-time exact-diagonalization** value
  of the observable at time $t = n\Delta t$, computed from the $2^L$-dimensional
  $H$ of design.md §3 by dense eigendecomposition (`numpy.linalg.eigh`), with
  the eigendecomposition residual $\max_j \lVert H v_j - \epsilon_j v_j\rVert_2$
  recorded and required to be at most $\epsilon_{\mathrm{ED}} = 10^{-10}$.
- $E_0(n)$: the **noiseless statevector** value of the **same Trotterized
  circuit** at step $n$.
- Noisy and mitigated values: density-matrix (exact under the noise model)
  or shot-based values at scale factor $\lambda \ge 1$, and their
  extrapolations to $\lambda = 0$.

$E_0$ is the mitigation-evaluation target. $E^{\mathrm{ED}} - E_0$ is the
Trotter error. Trotter error is never mixed into any ZNE metric.

### 2.4 The exact-diagonalization discrepancy stays visible

Scoring mitigation against $E_0$ measures recovery of the same Trotterized
circuit. It does not measure recovery of the exact continuous-time dynamics.
At $\Delta t = 1$ the Trotter error is deliberately not small (design.md §6).
At $L = 6$ and the first revival step $n = 19$ the recorded exact value is
`ed_reference` $= -0.8309868670981677$ and the recorded noiseless Trotter
value is `e0_trotter` $= -0.7379900962336665$, an absolute difference of
$0.0930$ in $\langle Z_\pi\rangle/L$ **(recorded, v0.1.0,**
`results/minimal/steps.csv`, read 2026-09-07**)**. Other steps differ by
other amounts; the full per-step Trotter-error curve is a required chart
series (§2.4 item 1).

This is enforced structurally, not by a disclaimer:

1. **Every chart of a mitigated observable carries the $E^{\mathrm{ED}}$
   curve.** Where one panel would be unreadable, a companion panel with the
   same axes carries it. The chart inventory in
   `docs/phase2-analysis-contract.md` lists the $E^{\mathrm{ED}}$ series for
   each such chart, and the checker fails if it is missing.
2. **Every physics-aware metric is reported twice** where the reference
   matters: once against $E_0$ (mitigation performance) and once against
   $E^{\mathrm{ED}}$ (agreement with exact dynamics), as separately named
   quantities with the reference in the name (for example
   $\Delta A^{(E_0)}_k$ and $\Delta A^{(\mathrm{ED})}_k$, §4.6). Revival
   amplitude and timing are always reported against both, because the
   Trotterized circuit's own revival amplitude and timing differ from the
   exact ones.
3. **Every success criterion names its reference in the criterion.** The
   Phase 2B and 2C success rules are stated against $E_0$ and say so. A
   statement that "scar dynamics were preserved" without a named reference
   is a defect in this document and in any report derived from it.

### 2.5 Symbols used across phases

| Symbol | Meaning | Units |
|---|---|---|
| $n$ | Trotter step; $Vt = n$ | steps |
| $L$ | chain length | sites |
| $E_{ij}(n)$ | Phase 2A density-matrix value of $\langle Z_\pi\rangle/L$ in cell $(i, j)$ | dimensionless |
| $r_{ij}(n)$, $A_{ij}(n)$, $I(n)$ | attenuation ratio, log-attenuation, interaction (§3.3) | dimensionless |
| $\tau_{\mathrm{RMS}}$, $\tau_{\max}$ | scientific equivalence margins on $I$ (§3.5) | dimensionless |
| $\eta_E$, $\eta_r$, $\eta_A$, $\eta_I$ | numerical reproducibility floors (§3.6) | as the quantity they bound |
| $\lambda$, $\lambda_r$ | nominal and realized scale factor (design.md §10) | dimensionless |
| $\kappa$ | noise-level multiplier on $(p_1, p_2)$ (§4.2) | dimensionless |

---

## 3. Phase 2A: channel additivity

### 3.1 Question and hypotheses

**Question.** Under the v0.1.0 gate-attached depolarizing model, does the
combined attenuation of $\langle Z_\pi\rangle/L$ by the single-qubit channel
($p_1$ on $sx$, $sxdg$, $x$) and the two-qubit channel ($p_2$ on $cx$) equal
the product of the two single-channel attenuations, step by step?

**Why it matters.** `docs/results-minimal.md` §8 records that the observed
total attenuation is about half the design.md §11 global-depolarizing
heuristic. Apportioning that gap between the two channels by subtraction is
valid only if the channels act additively on the log-attenuation scale
(outline §5). Phase 2A tests that premise directly instead of assuming it.

**Hypotheses, stated so they can fail.**

- $H_{\mathrm{add}}$ (additivity): the interaction $I(n)$ of §3.3 lies inside
  the equivalence margins of §3.5 on the mask, allowing for the numerical
  budget of §3.6.
- $H_{\mathrm{int}}$ (interaction): $I(n)$ lies outside a margin on the mask
  by more than the numerical budget allows.
- The third outcome, **inconclusive**, is neither. It is not evidence for
  either hypothesis (§3.7).

Design.md §11 already states that interleaved local channels need not
contract a many-body observable by a single scalar factor. No direction is
predicted here. **(design choice)** The study reports whichever of the three
outcomes the data produce, per $L$.

### 3.2 Design: the complete factorial

Four cells over $(p_1, p_2)$, each executed at every
$L \in \{4, 6, 8\}$, steps $n = 1, \dots, 40$, with the exact
density-matrix pipeline of design.md §8 at scale factor $\lambda = 1$ and no
folding:

| Cell | $(p_1, p_2)$ | Role |
|---|---|---|
| $(0,0)$ | $(0, 0)$ | noiseless reference $E_{00}(n)$ |
| $(1,0)$ | $(10^{-3}, 0)$ | single-qubit channel only |
| $(0,1)$ | $(0, 10^{-2})$ | two-qubit channel only |
| $(1,1)$ | $(10^{-3}, 10^{-2})$ | both channels |

**All four cells are rerun prospectively, under one Phase 2 implementation
and one Phase 2 environment**, in one invocation of the future entrypoint
(`docs/phase2-analysis-contract.md`, EP-2A). The $(0,0)$ cell is executed
through the same density-matrix executor with no noise model attached. Its
value is also compared with the separately computed statevector $E_0(n)$ of
§2.3 as part of the numerical validation gate of §3.6.

**The v0.1.0 combined arm is a historical cross-check only.** The recorded
`results/minimal/steps.csv` columns `e0_trotter` and `e_noisy_dm` are never
used as a Phase 2 factorial cell. They are compared with the Phase 2
$(0,0)$ and $(1,1)$ cells at $L = 6$ under this rule:

- **Comparison rule.** For every $n = 1, \dots, 40$, compute
  $d_{00}(n) = \lvert E_{00}^{\mathrm{P2}}(n) - \texttt{e0\_trotter}(n)\rvert$
  and
  $d_{11}(n) = \lvert E_{11}^{\mathrm{P2}}(n) - \texttt{e\_noisy\_dm}(n)\rvert$.
- **Tolerance.** $\tau_{\mathrm{hist}} = 10^{-12}$ absolute: the frozen
  design.md §16 cross-platform reproduction standard, unchanged. It is not
  loosened here. The one recorded test of that standard failed
  (`docs/ci-reproduction-assessment.md`); the failure stands as recorded, its
  cause is unresolved, and this cross-check neither resolves nor replaces
  that standard.
- **Verdict.** `HISTORICAL_CONSISTENT` if every $d_{00}(n)$ and
  $d_{11}(n)$ is at most $\tau_{\mathrm{hist}}$; otherwise
  `HISTORICAL_INCONSISTENT`, with the full list of offending steps and the
  maximum deviation reported.
- **Separate report, not a replacement.** The same deviations are also
  compared with the Phase 2 numerical budget $\eta_E$ of §3.6 and reported
  as a second, separately named quantity ("within the Phase 2 numerical
  budget: yes/no"). That report does not alter the `HISTORICAL_*` verdict.
- **Consequence.** An inconsistent cross-check does not change the Phase 2A
  verdict, which rests on the Phase 2 cells alone. It blocks any statement
  that Phase 2 reproduces v0.1.0, and it is recorded as a finding whose
  cause is outside Phase 2A's scope.

**Executions, all counted.** Per $L$: 4 cells × 40 steps = 160 Aer
density-matrix executions; 40 Aer statevector executions for $E_0$
(gate G1); and 4 cells × 40 steps = 160 independent dense-superoperator
executions (gate G2, §3.6). Total over three $L$: 480 Aer density-matrix,
120 Aer statevector and 480 dense-superoperator executions, 1080 in all.
The dense executions are executions like any other: they are rows of the
Phase 2A matrix in `tools/phase2_contract.json` (`phase2a.executions`),
they consume compute budget, and their outputs are saved with their own
schema (`results/phase2/phase2a/validation_dense.csv`, contract §C2). The
continuous-time $E^{\mathrm{ED}}$ is computed once per $L$ and plotted with
every Phase 2A observable chart, per §2.4, although it enters no Phase 2A
statistic.

### 3.3 Primary analysis: the curve-level interaction

For each cell $(i,j) \ne (0,0)$ and each step $n$ define

$$
r_{ij}(n) = \frac{E_{ij}(n)}{E_{00}(n)}, \qquad
A_{ij}(n) = -\ln r_{ij}(n), \qquad
A_{00}(n) = -\ln \frac{E_{00}(n)}{E_{00}(n)} \equiv 0 .
$$

The interaction is the factorial interaction contrast on the
log-attenuation scale:

$$
I(n) = A_{11}(n) - A_{10}(n) - A_{01}(n) + A_{00}(n) .
$$

The $A_{00}$ term is written so that $I(n)$ is the standard $2\times 2$
interaction contrast, $(A_{11} - A_{10}) - (A_{01} - A_{00})$: the change in
log-attenuation produced by adding the two-qubit channel when the
single-qubit channel is present, minus the same change when it is absent.
$A_{00}(n)$ vanishes identically by construction, so

$$
I(n) = -\ln r_{11}(n) + \ln r_{10}(n) + \ln r_{01}(n)
     = \ln \frac{r_{10}(n)\, r_{01}(n)}{r_{11}(n)} ,
$$

which is algebraically identical to the form in the task statement.
Exact additivity means $r_{11} = r_{10}\, r_{01}$ at every step, that is
$I(n) \equiv 0$.

**Units.** $I(n)$ is a dimensionless log-attenuation of the whole circuit
at step $n$. It is not a per-step rate and not a per-gate quantity. A value
$I(n) = 0.1$ means the combined attenuation ratio at step $n$ differs from
the product of the single-channel ratios by the factor $e^{-0.1} = 0.905$.

**Reported statistics**, over the masked step set $\mathcal{M}$ of §3.4,
defined only when $\mathcal{M}$ is non-empty and every masked $I(n)$ is
defined:

$$
S_{\mathrm{RMS}} = \sqrt{\frac{1}{\lvert\mathcal{M}\rvert}\sum_{n\in\mathcal{M}} I(n)^2},
\qquad
S_{\max} = \max_{n\in\mathcal{M}} \lvert I(n)\rvert .
$$

Both are dimensionless log-attenuations. If $\mathcal{M}$ is empty or any
masked $I(n)$ is undefined, both statistics are reported as **undefined**
(§3.8), never as a root-mean-square over zero points or over a subset. The
full per-step table of $r_{ij}(n)$, $A_{ij}(n)$, $I(n)$ and every flag of
§3.8 is saved for all 40 steps, masked or not.

### 3.4 Mask

Step $n$ is in the mask $\mathcal{M}$ if and only if
$\lvert E_{00}(n)\rvert \ge m_0 = 0.1$, evaluated on the computed
$E_{00}(n)$ with the inequality as written (equality is in the mask).
$E_{00}$ is noiseless, so the mask is fixed before any noisy cell runs. No
outcome-dependent quantity may enter the mask under any circumstances. The
masked and unmasked step lists are reported in full for every $L$.

**Mask-boundary ambiguity.** If
$\bigl\lvert\, \lvert E_{00}(n)\rvert - m_0 \,\bigr\rvert \le \eta_E$ for
one or more steps $n$, the mask at that $L$ is not numerically robust. The
fixed rule is the simplest one: every such step is flagged
`MASK_BOUNDARY`, the ambiguous steps are reported in full (step, computed
$E_{00}(n)$, distance from $m_0$), and the primary verdict for that $L$ is
`INCONCLUSIVE` (§3.8). No membership is tuned, toggled or chosen in any
way, however many steps are ambiguous.

At $L = 6$ the mask is already known from the recorded noiseless reference
**(recorded, v0.1.0,** `e0_trotter`, read 2026-09-07**)**:

- in the mask: 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19,
  20, 21, 22, 23, 24, 26, 27, 28, 29, 30, 31, 32, 33, 35, 36, 37, 38, 39, 40
  (36 steps);
- outside the mask: 5, 15, 25, 34 (4 steps, the oscillation nodes).

No recorded $\lvert E_{00}(n)\rvert$ at $L = 6$ lies within $\eta_E$ of
$m_0$ **(recorded, v0.1.0:** the nearest values are $0.0896$ at $n = 25$ and
$0.1324$ at $n = 24$**)**. The Phase 2 $(0,0)$ cell at $L = 6$ must reproduce
this list; a different list is a `HISTORICAL_INCONSISTENT` finding under
§3.2. The $L = 4$ and $L = 8$ lists are produced by the future noiseless
computation and are written to `results/phase2/phase2a/interaction.csv`
before any noisy cell runs, per the ordering rule in
`docs/phase2-analysis-contract.md` (EP-2A).

### 3.5 Scientific equivalence margins

The margins are **material** margins: the smallest interaction this study
treats as scientifically meaningful. They are declared, not derived from
any error bound or physical model.

**Route.** Declare the smallest materially meaningful multiplicative
discrepancy between the observed combined attenuation ratio $r_{11}(n)$ and
the product of the single-channel ratios $r_{10}(n)\, r_{01}(n)$, then map it
through the logarithm.

**Declared factors (design choice).**

- $f_{\max} = 1.10$: at every masked step, the combined attenuation ratio
  must lie within a factor $1.10$ of the product of the single-channel
  ratios, in either direction. This is the single-step guarantee.
- $f_{\mathrm{RMS}} = 1.05$: the root-mean-square of the per-step log
  discrepancy over the mask must not exceed $\ln 1.05$. This is a bound on
  the **typical log discrepancy on the factor scale**. It is not a bound on
  the root-mean-square of the relative ratio discrepancy itself, and it is
  not a statement that "the typical discrepancy is 5%"; the two coincide
  only to first order in small discrepancies.

**Arithmetic.** With $e^{-I(n)} = r_{11}(n) / (r_{10}(n)\, r_{01}(n))$,
a discrepancy factor between $1/f$ and $f$ is exactly
$\lvert I(n)\rvert \le \ln f$, symmetric in both directions. Hence

$$
\tau_{\max} = \ln f_{\max} = \ln 1.10 = 0.09531,
\qquad
\tau_{\mathrm{RMS}} = \ln f_{\mathrm{RMS}} = \ln 1.05 = 0.04879 ,
$$

both dimensionless log-attenuations per whole circuit, the same units as
$I(n)$. Rounded to five decimals here; the JSON holds the full-precision
values $\ln 1.10$ and $\ln 1.05$.

**Rationale and limits (design choice).** The factors are the resolution at
which this study is willing to call the combination of the two channels
multiplicative. They are set a priori so that the test can fail in either
direction: they are far above the numerical budget of §3.6, and far below
the whole-circuit attenuation factors observed at late steps (at $L = 6$
the recorded combined ratio falls to about $0.1$ by $n = 40$
**(recorded, v0.1.0)**), so a discrepancy at the margin is a small fraction
of the total attenuation. The factors are not derived from the per-step
rate discrepancy reported in `docs/results-minimal.md` §8, which is a
different quantity (a rate per step, not a whole-circuit factor), and this
document makes no claim that an interaction inside the margins leaves any
downstream apportionment conclusion unchanged. A different choice of
factors would move the verdict for data near the margin. Any such choice
must be declared before data exist, and this one is.

**What is not the margin.** A perturbative or accumulated-channel upper
bound on how large $\lvert I(n)\rvert$ *could* be is an upper bound on the
effect, not a scientific margin. For example, the design.md §11 exposures
$\Gamma_1(n) + \Gamma_2(n)$ at $L = 8$, $n = 40$ are of order
$2(L-1)\,n\,\gamma_2 \approx 560 \times 0.01005 \approx 5.6$ **(inference:**
gate count from design.md §7, rate from §8**)**. Adopting a bound of that
size as the margin would declare equivalence for interactions fifty times
larger than $\tau_{\max}$ and would make the test automatically permissive at
late $n$. Such bounds are cited here only as context and are not used
anywhere in the decision rule.

**Depth dependence.** The margins are constants. They do not depend on $n$
or $L$. **(design choice)** A depth-dependent margin would have to be
justified as a depth-dependent notion of materiality; no such notion is
claimed here.

**Fixed before data.** These margins are fixed by this document and by
`tools/phase2_contract.json` (`C-F-MAT-RMS`, `C-F-MAT-MAX`, `C-TAU-RMS`,
`C-TAU-MAX`). No Phase 2 outcome may change them. A change is a
preregistration deviation under §8.

### 3.6 Numerical accuracy budget and its validation gate (separate from the margin)

This subsection concerns numerical accuracy only. Its symbols are
$\eta_E$, $\eta_r$, $\eta_A$, $\eta_I$. They are never reused as scientific
thresholds, and they never widen $\tau_{\mathrm{RMS}}$ or $\tau_{\max}$.

**What $\eta_E$ is.** $\eta_E = 10^{-9}$ is an **assumed per-value
numerical accuracy budget**: the analysis assumes that every Phase 2A
density-matrix expectation value $E$ differs from the exact value
$\tilde E$ under the noise model by at most $\eta_E$ in absolute terms. It
is a declared policy value **(design choice)**, equal to the v0.1.0
density-matrix denominator threshold $\delta = 10^{-9}$ (design.md §13) and
to the outline's $10^{-9}$ policy tolerance. It is not a proven solver
error bound. Two facts support the choice without proving it: (a) in the
one recorded cross-platform reproduction, the raw density-matrix
expectation values agreed to $10^{-12}$ while some derived quantities did
not (`docs/ci-reproduction-assessment.md`; the six failing `steps.csv`
values are ratio and shot-secondary columns, not `e_noisy_dm` or
`e0_trotter`) **(recorded)**; (b) the budget is three orders of magnitude
above that observed reproducibility level. Neither fact bounds the error
against the exact value. The gate below is what tests the premise.

**Validation gate (executed by EP-2A, before any verdict).**

- **G1, two Aer paths.** For every $L$ and $n$,
  $\lvert E_{00}^{\mathrm{DM}}(n) - E_0^{\mathrm{SV}}(n)\rvert \le \eta_E$,
  where the first value comes from the density-matrix executor with no
  noise and the second from the statevector simulation of the same circuit.
- **G2, independent implementation.** For every cell, $L$ and $n$ (480
  executions), the expectation value is recomputed by a dense-superoperator
  implementation written independently of Aer. The recorded transpiled
  circuit is read from `results/phase2/phase2a/circuits.json`, which
  stores every instruction with its qubits **and its rotation
  parameters**. The replay starts from the all-zero computational state
  $\lvert 0\cdots 0\rangle$ (one preparation boundary for every pipeline):
  the recorded circuit begins with the $\lfloor L/2\rfloor$ preparation
  $X$ gates that build $\lvert Z_2\rangle$ (the sealed builder includes
  them, and design.md §8 and §11 count them in the noisy single-qubit
  exposure), so they are replayed with their $p_1$ channel like every other
  instruction. Each instruction is applied to the $2^L \times 2^L$ density
  matrix in `numpy` as its unitary conjugation with the recorded parameter,
  followed by the Kraus map of the channel attached to that instruction name
  (depolarizing Kraus operators written out from the design.md §11 channel
  definition, identity for `rz`), in circuit order; the observable is
  $\mathrm{Tr}[\rho Z_\pi]/L$ with $Z_\pi$ built from the same site map. Output: one row per
  $(L, \text{cell}, n)$ with the dense value, the Aer value and their
  difference. Let $d_{\mathrm{val}}$ be the maximum absolute difference
  over all rows. The gate requires $d_{\mathrm{val}} \le \eta_E / 10$, a
  tenfold margin inside the budget.
- **Status.** `NUMERICS_VALIDATED` if G1 and G2 both pass;
  `NUMERICS_UNVALIDATED` otherwise. $d_{\mathrm{val}}$ and the largest G1
  deviation are recorded in `results/phase2/phase2a/verdict_2a.json`.

**Conditionality rule (the one place this is stated).** Every Phase 2A
verdict is conditional on the budget premise, always. Passing G1 and G2
supports the assumed budget; it does not prove a worst-case error bound,
because two agreeing implementations can share an error and because the
gate samples the same circuits the analysis uses. No unconditional
scientific equivalence claim is ever made. The label attached to every
verdict is one of:

- `NUMERICS_VALIDATED`: "conditional on the numerical budget
  $\eta_E = 10^{-9}$; budget supported by validation gates G1 and G2";
- `NUMERICS_UNVALIDATED`: "conditional on the numerical budget
  $\eta_E = 10^{-9}$; budget not supported: gate G1/G2 failed" (naming the
  gate and the observed deviation).

The gate is a falsification test of the premise: a failure discredits the
budget, a pass leaves it assumed. Every later reference to a verdict's
status refers to this paragraph.

**Propagation, written out.** These are conditional formulas: they hold if
the budget premise holds, and they cannot establish it. For a masked step,
where $\lvert E_{00}(n)\rvert \ge m_0 > \eta_E$:

1. Ratio. From $\tilde r = \tilde E_{ij} / \tilde E_{00}$,
   $$
   \lvert \tilde r_{ij}(n) - r_{ij}(n)\rvert \;\le\;
   \eta_r^{ij}(n) := \frac{\eta_E\,\bigl(1 + \lvert r_{ij}(n)\rvert\bigr)}{\lvert E_{00}(n)\rvert - \eta_E} .
   $$
   (Worst case over the signs of the two perturbations; obtained by
   bounding $\lvert(E_{ij} + a)/(E_{00} + b) - E_{ij}/E_{00}\rvert$ with
   $\lvert a\rvert, \lvert b\rvert \le \eta_E$.)
2. Log-attenuation. If $\lvert r_{ij}(n)\rvert > \eta_r^{ij}(n)$,
   $$
   \lvert \tilde A_{ij}(n) - A_{ij}(n)\rvert \;\le\;
   \eta_A^{ij}(n) := \frac{\eta_r^{ij}(n)}{\lvert r_{ij}(n)\rvert - \eta_r^{ij}(n)} ,
   $$
   using $\lvert\ln(1 + x)\rvert \le \lvert x\rvert/(1 - \lvert x\rvert)$ for
   $\lvert x\rvert < 1$. If $\lvert r_{ij}(n)\rvert \le \eta_r^{ij}(n)$ the
   logarithm is not numerically resolvable; the step receives the
   `RATIO_UNRESOLVED` flag of §3.8.
3. Interaction. By the triangle inequality,
   $$
   \lvert \tilde I(n) - I(n)\rvert \;\le\;
   \eta_I(n) := \eta_A^{11}(n) + \eta_A^{10}(n) + \eta_A^{01}(n) .
   $$
4. Statistics. Per step, $\lvert \tilde I(n)\rvert$ lies in
   $[\,\max(0, \lvert I(n)\rvert - \eta_I(n)),\; \lvert I(n)\rvert + \eta_I(n)\,]$.
   Because the root-mean-square and the maximum are monotone in each
   $\lvert I(n)\rvert$, the bound intervals are
   $$
   S_{\mathrm{RMS}}^{\mathrm{lo}} = \sqrt{\tfrac{1}{\lvert\mathcal{M}\rvert}\textstyle\sum_{n\in\mathcal{M}} \max(0, \lvert I(n)\rvert - \eta_I(n))^2},
   \quad
   S_{\mathrm{RMS}}^{\mathrm{hi}} = \sqrt{\tfrac{1}{\lvert\mathcal{M}\rvert}\textstyle\sum_{n\in\mathcal{M}} (\lvert I(n)\rvert + \eta_I(n))^2},
   $$
   $$
   S_{\max}^{\mathrm{lo}} = \max_{n\in\mathcal{M}} \max(0, \lvert I(n)\rvert - \eta_I(n)),
   \qquad
   S_{\max}^{\mathrm{hi}} = \max_{n\in\mathcal{M}} \bigl(\lvert I(n)\rvert + \eta_I(n)\bigr).
   $$
   All four exist only when every masked $I(n)$ and $\eta_I(n)$ is defined
   **and** $\lvert\mathcal{M}\rvert \ge k_{\min} = 3$; otherwise every one of
   them is undefined (null), `TOO_FEW_POINTS` is set and the verdict is
   `INCONCLUSIVE` (§3.8; amendment A-2). The per-step records and the
   frozen mask are kept in full.

**Where the budget binds.** $\eta_A$ grows as $\lvert r\rvert$ shrinks, so
the late-step, strongly attenuated cells carry the largest floors. The
$\eta$ terms for the $(1,0)$ and $(0,1)$ cells cannot be inferred from the
recorded combined arm, because those cells have never been run; every
$\eta$ value is computed from the Phase 2 outputs by EP-2A and saved
per step in `results/phase2/phase2a/interaction.csv`.

**Rule.** If $\eta_I(n) > \tau_{\max}$ at some masked $n$, that step is
flagged `NUMERICAL_INCONCLUSIVE`. It stays in the mask and in every table.
The verdict for that $L$ is `INCONCLUSIVE` (§3.7). The margin is never
relaxed to accommodate the budget.

### 3.7 Decision rule: interval-inclusion equivalence assessment with bound intervals

**What this is, and what it is not.** Phase 2A has no sampling
distribution, so the intervals of §3.6 are worst-case bound intervals
conditional on the numerical budget, not confidence intervals. They carry no
coverage probability. The decision rule below is therefore a deterministic
**interval-inclusion equivalence assessment**: equivalence is declared only
if the whole bound interval lies inside the equivalence region, and
interaction only if it lies wholly outside. It is not a statistical
two-one-sided-tests procedure, not a hypothesis test at any level, and its
"inconclusive" outcome is not a statistical failure to reject. The term
"95%" does not appear anywhere in Phase 2A reporting.

For each $L$ separately, with the blocking flags defined in §3.8:

- **`EQUIVALENT`.** No blocking flag is present for that $L$, and
  $S_{\mathrm{RMS}}^{\mathrm{hi}} \le \tau_{\mathrm{RMS}}$ and
  $S_{\max}^{\mathrm{hi}} \le \tau_{\max}$.
- **`INTERACTION`.** No blocking flag is present for that $L$, and
  $S_{\mathrm{RMS}}^{\mathrm{lo}} > \tau_{\mathrm{RMS}}$ or
  $S_{\max}^{\mathrm{lo}} > \tau_{\max}$.
- **`INCONCLUSIVE`.** Every other case: a blocking flag is present, or a
  statistic is undefined, or an interval straddles a margin. This outcome
  is not evidence of additivity and not evidence of interaction. It is
  reported with the same prominence as the other two, with its reason
  (which flag, or which interval straddles which margin).

The three outcomes are exhaustive by construction: the third is the
complement of the first two. They are mutually exclusive because a blocking
flag or an undefined statistic excludes the first two at once, and
otherwise $S^{\mathrm{lo}} \le S^{\mathrm{hi}}$ for both statistics makes
$S^{\mathrm{hi}} \le \tau$ and $S^{\mathrm{lo}} > \tau$ incompatible.

Every verdict carries the numerical status of §3.6 (`NUMERICS_VALIDATED` or
`NUMERICS_UNVALIDATED`) and the conditional label required there. In both
cases the verdict is conditional on the assumed budget; the status says
only whether the budget is supported by the gate or not. The verdict is reported per $L$. No pooling across
$L$ is performed. A single sentence per $L$ states the verdict, the
numerical status, the two bound intervals, and the margins, in that order.

### 3.8 Edge cases, pre-declared

Every case below produces a deterministic, reportable outcome. No step is
ever removed from a table. Flags are stored per $(L, \text{cell}, n)$ in
`results/phase2/phase2a/interaction.csv`. "Blocking" means the primary
verdict for that $L$ is `INCONCLUSIVE`; that is the one primary decision
for every blocking case.

| Case | Detection | Flag | Primary analysis | Secondary fit (§3.9) |
|---|---|---|---|---|
| Missing or non-finite value in any cell at any $n$ | value absent, NaN or infinite | `MISSING_OR_NONFINITE` | Blocking. | Fit unavailable for that cell. |
| $E_{00}(n) = 0$ or $\lvert E_{00}(n)\rvert < m_0$ | noiseless value | `BELOW_MASK` | Outside $\mathcal{M}$; $r$, $A$, $I$ tabulated where defined, excluded from $S_{\mathrm{RMS}}$, $S_{\max}$. Not blocking. | Outside the fit domain. |
| Mask-boundary ambiguity, $\bigl\lvert\lvert E_{00}(n)\rvert - m_0\bigr\rvert \le \eta_E$ at one or more steps | §3.4 | `MASK_BOUNDARY` | Blocking. All ambiguous steps reported in full. No membership tuning. | Fit unavailable for all cells at that $L$. |
| $(0,0)$ cell disagrees with the statevector $E_0$ beyond $\eta_E$ (gate G1) | §3.6 | `REFERENCE_MISMATCH` | Blocking. Both values reported. | Fit unavailable for all cells at that $L$. |
| Gate G2 fails | §3.6 | `NUMERICS_UNVALIDATED` | Not blocking by itself; the verdict is computed and carries the "budget not supported" label of §3.6. | Same label. |
| Sign disagreement, $r_{ij}(n) \le 0$ at a masked step | $E_{ij}(n)\, E_{00}(n) \le 0$ | `SIGN_FLIP` | $A_{ij}(n)$, $I(n)$ undefined at that step. Blocking. Step and values reported in full. | Fit unavailable for that cell. |
| Positive but numerically unresolved ratio, $0 < \lvert r_{ij}(n)\rvert \le \eta_r^{ij}(n)$ at a masked step | §3.6 step 2 | `RATIO_UNRESOLVED` | $A_{ij}(n)$, $I(n)$ undefined at that step. Blocking. | Fit unavailable for that cell. |
| Ratio above one beyond the budget, $r_{ij}(n) > 1 + \eta_r^{ij}(n)$ at a masked step | Phase 2 adequacy gate | `RATIO_ABOVE_ONE` | $A_{ij}(n) < 0$; $I(n)$ defined and used. Not blocking. | Fit unavailable for that cell (adequacy gate). |
| Ratio equal to one within the budget, $\lvert r_{ij}(n) - 1\rvert \le \eta_r^{ij}(n)$ | equality case | `RATIO_NEAR_ONE` | $A_{ij}(n)$ computed as is (may be $0$ or slightly negative). Not blocking. Not an adequacy violation. | Included as is. |
| Budget exceeds the margin, $\eta_I(n) > \tau_{\max}$ at a masked step | §3.6 rule | `NUMERICAL_INCONCLUSIVE` | Blocking. | Fit unavailable for all cells at that $L$. |
| Fewer than $k_{\min} = 3$ masked steps, or $\mathcal{M}$ empty | count | `TOO_FEW_POINTS` | Statistics undefined. Blocking. | Fit unavailable for all cells at that $L$. |
| Secondary fit fails numerically (singular design, non-finite input) | numerical | `FIT_FAILURE` | Not blocking. | Slope undefined for that cell; no substitution. |

Nothing is silently excluded. Every flag count appears in
`results/phase2/phase2a/verdict_2a.json`. A blocking flag anywhere in the
mask at a given $L$ yields exactly one primary decision, `INCONCLUSIVE`,
with the flag named as the reason.

**Gate rules retained from and superseded in the outline, stated once.**
The outline §4 pointwise adequacy gate $r > 1 + 10^{-9}$ is **superseded**
by the budget-based Phase 2 gate $r_{ij}(n) > 1 + \eta_r^{ij}(n)$ above
(`RATIO_ABOVE_ONE`). The outline §2/§4 rate rules ($g \in [-10^{-9}, 0)$
treated as $0$; $g < -10^{-9}$ is anti-attenuation) are **retained**
unchanged in §3.9. §1.2 records the same split.

### 3.9 Secondary analysis: single-rate slopes

For each noisy cell $(i,j)$ and each $L$, the fit domain is the **entire
fixed mask** $\mathcal{M}$ of §3.4. The fit is performed only if every
masked step of that cell is free of the fit-gate flags `SIGN_FLIP`,
`RATIO_UNRESOLVED`, `RATIO_ABOVE_ONE` and `MISSING_OR_NONFINITE`, and the
$L$ is free of `REFERENCE_MISMATCH`, `NUMERICAL_INCONCLUSIVE`,
`TOO_FEW_POINTS` and `MASK_BOUNDARY`. If any masked step of the cell violates a fit gate, the
whole fit for that cell is `FIT_UNAVAILABLE`: no slope is reported, no
subset is fitted, and the violating steps are listed. Fitting a surviving
subset would be outcome-dependent exclusion and is prohibited.

When the fit is performed, fit $\ln r_{ij}(n) \approx a_{ij} + b_{ij}\, n$
by ordinary least squares over all of $\mathcal{M}$ and report
$g_{ij} = -b_{ij}$ (dimensionless per step), the intercept $a_{ij}$, and
every residual $e_{ij}(n) = \ln r_{ij}(n) - (a_{ij} + b_{ij} n)$. The
outline's rate rules are retained: a fitted $g_{ij} \in [-10^{-9}, 0)$ is
treated as $0$; a fitted $g_{ij} < -10^{-9}$ is reported as
`ANTI_ATTENUATION` and that cell's rate is not used further. Then, only
when all three cell fits are available and none is `ANTI_ATTENUATION`,

$$
\Delta = g_{11} - g_{10} - g_{01} \quad \text{(dimensionless per step)};
$$

otherwise $\Delta$ is reported as unavailable with the reason. $\Delta$
carries no pass/fail threshold. The outline's $\tau_{\text{add}}$ is not
defined and is superseded (§1.2).

**Adequacy limitations, stated explicitly.**

1. The single-exponential-in-$n$ form is the design.md §11
   global-depolarizing heuristic. Design.md §11 itself flags that heuristic
   as not generally valid for interleaved local channels.
2. The recorded v0.1.0 combined arm shows strong residual structure under
   this fit: over the 36 masked steps the largest absolute residual of
   $\ln r_{11}(n)$ about its least-squares line is $0.99$ and the
   root-mean-square residual is $0.21$ **(recorded, v0.1.0, recomputed
   2026-09-07 from** `results/minimal/steps.csv` **with the outline §4
   estimator, no tolerance applied; the saved-input command is R-7 in**
   `docs/followup-study-draft.md`**)**. A fitted single rate compresses that
   structure into one number and can report additivity or interaction for
   reasons unrelated to the channels.
3. Therefore $\Delta$ is descriptive. It is never the basis of the Phase 2A
   verdict.

**Residual-structure diagnostic.** An available fit for cell $(i,j)$ is
`RESIDUAL_ADEQUATE` if $\max_{n\in\mathcal{M}} \lvert e_{ij}(n)\rvert \le \tau_{\mathrm{res}} = 0.05$
and `RESIDUAL_INADEQUATE` otherwise. $\tau_{\mathrm{res}}$ is a
dimensionless tolerance on $\ln r$ **(design choice)**: a single-exponential
summary that misses any masked step by more than a factor $e^{0.05} = 1.051$
in ratio is declared inadequate. Based on item 2, the combined cell at
$L = 6$ is expected to be `RESIDUAL_INADEQUATE`; that expectation is
recorded here so it cannot be presented later as a surprise.

**What a residual failure licenses.** It licenses only the statement that
the single-rate summary is inadequate for that cell and that $\Delta$ is not
interpretable for that $L$. It does not license any statement about
additivity or interaction; those come from §3.7 only. It does not license
any change to the mask, the margins or the primary statistic.

### 3.10 Uncertainty treatment: bound intervals, no bootstrap

In the exact density-matrix pipeline at $\lambda = 1$ there is **no sampling
variation**. Each $E_{ij}(n)$ is a deterministic function of the circuit,
the noise model and the numerical environment. No folding is applied, so
there is no seed ensemble either. A bootstrap needs an exchangeable
resampling unit; here none exists. Resampling steps, cells or seeds would
manufacture a spread with no scientific meaning, and the interval it produced
would say nothing about additivity.

**Choice.** Phase 2A's only uncertainty statement is the worst-case bound
interval of §3.6, propagated through $r$, $\ln r$ and $I$ under the mask
and conditional on the numerical budget $\eta_E$, whose validation status is
always reported alongside. These intervals are labelled "numerical bound
interval, budget $\eta_E = 10^{-9}$, status validated/unvalidated" in every
table and legend. They are never called confidence intervals, never given a
coverage level, and never called uncertainty without the word "numerical".

**Why not a shot-based companion arm.** A companion arm with 8192-shot
sampling would have a genuine resampling unit (the shot record) and a
meaningful bootstrap. It would answer a different question: how well shot
data can resolve $I(n)$. Phase 2A's question is about the channels
themselves, for which the exact pipeline is the right instrument; the
shot-level resolution question is covered in Phase 2B, whose shot pipeline
carries the bootstrap of §6. **(design choice)** Adding the arm to Phase 2A
would add 480 executions and a second decision rule without changing the
answer to the Phase 2A question.

### 3.11 What each outcome does and does not license

| Outcome (per $L$) | Licenses | Does not license |
|---|---|---|
| `EQUIVALENT`, numerics validated | Treating $A_{11} \approx A_{10} + A_{01}$ within the declared margins on the mask at that $L$, conditional on the assumed budget $\eta_E$, which the gate supports. | Any unconditional statement; any statement about other $L$, other rates, other channels, the true functional form of the noise response, the v0.1.0 verdict, or any downstream apportionment conclusion beyond the stated margins. |
| `EQUIVALENT`, numerics unvalidated | The same conditional statement, with the label that the budget is not supported. | Any unconditional statement; the same exclusions. |
| `INTERACTION` | Reporting that the channels do not combine multiplicatively at that $L$ beyond the margin; the sign and depth profile of $I(n)$ as a finding (conditional label if unvalidated). | Attributing the interaction to a mechanism; any apportionment by subtraction. |
| `INCONCLUSIVE` | Reporting the intervals, flags and reason. | Any additivity or interaction claim. |

No outcome retroactively strengthens or weakens the v0.1.0 result, whose
verdict is defined by its own pre-registered metrics on recorded data.

---

## 4. Phase 2B: physics-aware simulator benchmark

### 4.1 Question, hypotheses and window

**Question.** In a classical simulator with a fully specified noise model,
at what circuit depth (revival index) and at what noise level does
zero-noise extrapolation stop preserving **both** the amplitude **and** the
timing of the scar revival, for **both** the staggered magnetization and the
return probability, relative to the noiseless value of the same Trotterized
circuit?

**Primary confirmatory result: the boundary itself.** The primary Phase
2B result is the depth-or-noise boundary for simultaneous amplitude-and-
timing preservation on the **primary family** declared in §4.10: local
folding with the linear extrapolator, on the shot pipeline, at every
$L \in \{4, 6, 8\}$, both primary noise models (`DEP`, `DEPH`), every
scanned level $\kappa \in \{0.25, 0.5, 1, 2, 4\}$, and both revivals
$k \in \{1, 2\}$, with the deterministic estimator of §4.8 and the
family-wise multiplicity treatment of §4.10. Every other combination
(global folding, the quadratic and exponential extrapolators, the
secondary noise models, the control) is exploratory.

**Primary hypothesis H-2B, stated so it can fail.** For each of the six
$(L, \text{model})$ pairs in the primary family:

- H-2B(a), boundary inside the grid: $\kappa^*(1) \in \{0.5, 1, 2\}$ and is
  **located** (§4.8: the next scanned level is an observed `FAIL`, not an
  indeterminate condition);
- H-2B(b), depth monotonicity: $\kappa^*(2) \le \kappa^*(1)$ in the grid
  order;

and across sizes, for each model and each $k$:

- H-2B(c), size monotonicity:
  $\kappa^*(k; L = 8) \le \kappa^*(k; L = 6) \le \kappa^*(k; L = 4)$.

**What falsifies it.** H-2B is falsified by any single observed
violation: a located $\kappa^*(1)$ of $0.25$ or $4$, a `BELOW_MIN_FAIL`,
or a full-grid pass (`AT_OR_ABOVE_MAX`); an observed
$\kappa^*(2) > \kappa^*(1)$ with both boundaries located; an observed
increase of $\kappa^*(k)$ with $L$ between located boundaries. "Located"
means the next level is `FAIL` under the three-way rule of §6.5, so every
falsification rests on a supported negative claim, not on a missed
interval. A `NON_MONOTONE` sequence (§4.8) is contrary evidence that is reported
with the boundary; it never explains away an increase and never exempts
any part of H-2B from falsification. A component whose boundary is
**unresolved** (an indeterminate condition breaks the scan before a `FAIL`
is observed, §4.8) is reported as "H-2B not evaluable" for that component:
neither confirmation nor falsification. Whether or not H-2B survives, every
boundary and every pass/fail/indeterminate map is reported.

**(inference from the recorded v0.1.0 data)** The recorded linear-primary
error at the first revival step $n = 19$ is $0.326$ and the recorded
exponential-secondary error is $0.088$ in $\langle Z_\pi\rangle/L$
(`results/minimal/steps.csv`, `eps_m` and `secondary_estimate`, read
2026-09-07); the design therefore expects the primary combination at
$L = 6$, `DEP` to fail the amplitude tolerance $\tau_A^{Z_\pi} = 0.10$ at
$\kappa = 1$, which under H-2B(a) would place $\kappa^*(1)$ at $0.5$. That
is an expectation, not a rule.

**Exploratory expectations (design choice, inference).** For the
exploratory maps: E-2B-1, the boundary $\kappa^*(k)$ is non-increasing in
$k$ and in $L$ for every combination; E-2B-2, at $L = 6$ under `DEP` some
(folding, extrapolator) combination passes revival 1 at some
$\kappa \le 1$. These are reported as met, not met, or not evaluable; they
carry no confirmatory weight, and a `NON_MONOTONE` flag does not exempt
E-2B-1 either.

**Window.** Steps $n = 1, \dots, 48$ for every cell. At $L = 6$ the recorded
noiseless grid revivals are at $n = 19$ and $n = 39$ **(recorded, v0.1.0)**;
a 40-step window would clip the matching window of the second revival
(§4.6), so the window is extended to 48. **(design choice)** No third
revival is expected inside the window; if one is found by the §4.6 rule it
is reported but is not an endpoint.

### 4.2 Noise models and noise levels

Real hardware noise is **observed, never selectable**: it belongs to Phase
2C only, where the device determines it. Every noise model in this section
is a simulator construction chosen by this document. A reader who meets the
calibration-derived model below must not confuse it with hardware data: it
is a simulator noise model built from a calibration snapshot, and its cells
are marked blocked until that snapshot exists.

The noise-level multiplier $\kappa \in \{0.25, 0.5, 1, 2, 4\}$ scales the
baseline rates $(p_1, p_2) = (10^{-3}, 10^{-2})$ of design.md §8, so that
$\kappa = 1$ is the v0.1.0 level.

| Id | Tier | Construction (Qiskit Aer 0.17.1 API, §9) |
|---|---|---|
| `DEP` | primary | `depolarizing_error(kappa*p1, 1)` on `sx`, `sxdg`, `x`; `depolarizing_error(kappa*p2, 2)` on `cx`; `rz` clean (design.md §8). |
| `DEPH` | primary | `phase_damping_error(kappa*p1)` on `sx`, `sxdg`, `x`; `phase_damping_error(kappa*p2).tensor(phase_damping_error(kappa*p2))` on `cx`; `rz` clean. |
| `AMP` | secondary | `amplitude_damping_error(p1)` on `sx`, `sxdg`, `x`; `amplitude_damping_error(p2).tensor(amplitude_damping_error(p2))` on `cx`; `rz` clean; $\kappa = 1$ only. |
| `RO` | secondary | `DEP` at $\kappa = 1$ plus a symmetric readout error $p_{\mathrm{ro}} = 0.02$ on every qubit. Shot pipeline: `ReadoutError([[1-p_ro, p_ro],[p_ro, 1-p_ro]])` via `add_all_qubit_readout_error`. Density-matrix pipeline: readout noise attached to the measurement instruction cannot alter pre-measurement density-matrix expectation values, so the computational-basis probability vector is extracted from the density matrix, the classical transition matrix (tensor product of the per-qubit $2\times 2$ readout matrix) is applied to it, and every observable is evaluated from the transformed probabilities. $\kappa = 1$ only. |
| `CAL` | secondary | Reconstructed **offline** from the saved Phase 2C pre-run calibration snapshot (§5.3), never from a live backend. Scientific content, fixed here: for every physical qubit of the chain layout (rule below), a thermal-relaxation channel with the snapshot's $T_1$, $T_2$ and the instruction duration, composed with a depolarizing channel whose parameter is set so that the total average gate error equals the snapshot's reported gate error for that instruction on those qubits (the Aer device-model construction; §9); readout as the per-qubit asymmetric matrix $[[1-P(1\vert 0), P(1\vert 0)],[P(0\vert 1), 1-P(0\vert 1)]]$ from the snapshot's assignment errors. Shot pipeline: gate channels attached by instruction and qubits, readout by `ReadoutError` per qubit. Density-matrix pipeline: gate channels as above; readout applied classically to the probability vector as for `RO`, with the per-qubit asymmetric matrices. **Native-gate translation, frozen:** the simulator executes the design.md basis $\{rz, sx, x, cx\}$ on logical qubits; the snapshot names the device's native two-qubit gate (`cx`, `ecr` or `cz`) on physical bonds. The reconstructed two-qubit channel of the native gate on physical bond $(\text{chain}[i-1], \text{chain}[i])$, taken in the reported direction with the larger error, is attached to the simulator's `cx` on logical bond $(q_{i-1}, q_i)$; the single-qubit channels of physical qubit $\text{chain}[i-1]$ for `sx` and `x` (and `sxdg`, using the `sx` calibration) are attached to the same instruction names on logical $q_{i-1}$; `rz` stays clean; readout uses physical $\text{chain}[i-1]$'s matrix on logical $q_{i-1}$. The model is a calibration-derived stand-in on the simulator basis, not a model of the device's own decomposition; that limitation is stated with every `CAL` result. **Missing-channel rule:** if any instruction executed by any `CAL` circuit (checked as in v0.1.0 test T6 over every folded circuit) has no reconstructed channel, the cell is `CAL_MISSING_CHANNEL` and is not run; no channel is ever silently omitted. The snapshot's concrete representation and the reconstruction algorithm are a future implementation contract in `docs/phase2-analysis-contract.md` (§C4, `CAL`), labelled as such; the choices above are not deferred. $\kappa = 1$ only. **Blocked** until the snapshot exists; the snapshot requires the Phase 2C first gate. |

**Chain layout rule for `CAL`.** The single layout rule and score
equation of §5.2 (sum over bonds of the native two-qubit gate error plus
the sum over qubits of the per-qubit mean assignment error, with its
directed-edge, missing-calibration, tie and orientation rules) is applied
to the whole-device snapshot of §5.3 for each $L \in \{4, 6, 8\}$
separately. The chosen tuple for each $L$ is recorded in
`results/phase2/phase2c/backend_selection.json` and reused unchanged by
every `CAL` cell.

**Parameter convention (design choice, stated as a limitation).** The
dephasing and amplitude-damping channel parameters are set numerically equal
to the depolarizing probabilities. This is a parameter convention, not a
calibration of channel strength; no claim is made that two models at the
same $\kappa$ are "equally noisy". Boundaries are reported per model and are
not compared across models as if on a common noise scale.

### 4.3 Scale factors, folding variants and realized scales

Nominal scale factors $\lambda \in \{1, 1.25, 1.5, 1.75, 2\}$ for every
simulator cell. Two folding variants are applied to the transpiled circuit
(`optimization_level=0`, design.md §7), and the realized scale is measured
from the folded circuit, never inferred:

- `LOCAL`: `fold_gates_at_random` with the bound seed and
  `fidelities={"single": 1.0, "double": 0.99}` (design.md §10, carried
  forward). Only `cx` gates are folded. Realized scale
  $\lambda_r = N_{cx}^{\mathrm{folded}} / N_{cx}^{\mathrm{base}}$.
- `GLOBAL`: `fold_global` (mitiq v1.0.0 `folding.py`, §9), applied to the
  operation list of the transpiled circuit **without** its final
  measurements (measurements are appended after folding; no barriers are
  present). With $q, f = \mathrm{divmod}(\lambda - 1, 2)$: the whole
  operation list $U$ is folded $q$ times as $U\,(U^\dagger U)^{q}$, then a
  **suffix** of $n_{\mathrm{p}} = \mathrm{round}(f \cdot \lvert U\rvert / 2)$
  operations (Python `round`, half to even) is folded once as
  $U\,(S^\dagger S)$ where $S$ is that suffix. So integer folds fold every
  operation; a partial fold folds only the suffix. Inverse operations
  realized by folding: `cx`$^\dagger$ = `cx`, `x`$^\dagger$ = `x`,
  `sx`$^\dagger$ = `sxdg` (noisy, design.md §8), `rz`$(\theta)^\dagger$ =
  `rz`$(-\theta)$ (clean); every instruction name in every folded circuit
  is either `rz` or carries a channel, checked as in v0.1.0 test T6. Two
  realized scales are recorded: $\lambda_r = N_{cx}^{\mathrm{folded}}/N_{cx}^{\mathrm{base}}$,
  the regression abscissa, and $\lambda_r^{(1)} = N_{1}^{\mathrm{folded}}/N_{1}^{\mathrm{base}}$
  over the noisy single-qubit gates (`sx`, `sxdg`, `x`), reported alongside
  and never merged with $\lambda_r$. If two nominal $\lambda$ produce the
  same $\lambda_r$ at some step, both points enter the regression as
  recorded (duplicate abscissas are allowed by least squares). The rank
  rule stated after this list applies to both folding variants. A base circuit
  with $N_{cx}^{\mathrm{base}} = 0$ cannot occur ($N_{cx} = 2(L-1)n \ge 6$).
  `fold_global` is deterministic, so the eight fold seeds produce identical
  circuits under `GLOBAL`; the seed loop is still executed so the shot
  pipeline receives eight independent `seed_simulator` values, and the
  density-matrix values are identical across seeds by construction (their
  seed spread is exactly zero and is reported as such, not as evidence of
  precision). The complete operation-level arithmetic is restated in
  `docs/phase2-analysis-contract.md` §C4 and exercised by the checker on a
  synthetic operation list.

**Rank rule for every Phase 2B fit (both folding variants, both pipelines,
recorded counts and every bootstrap replicate; amendment A-1).** Each fit
requires full design-matrix rank for its declared form, counted on the
distinct realized abscissas $\lambda_r$ of that seed's fit group: at least
two distinct realized abscissas for `LIN` and at least three for `QUAD`; the
exponential fit needs at least three distinct realized abscissas as well,
$n^{\mathrm{EXP}}_{\min,\mathrm{2B}} = 3$, everywhere in Phase 2B, in log
mode and in `avoid_log` mode alike. Two distinct abscissas are the algebraic
full-rank necessity of the two-parameter exponential fit; the Phase 2B
minimum of three is a human-selected admission guard above that necessity,
so that no Phase 2B exponential is admitted on the minimal two-point design.
Duplicate abscissas are kept as recorded
in the regression and count once toward the rank. Fewer distinct realized
abscissas than required makes that extrapolator `FIT_FAILURE` at that step
and seed, with the distinct-abscissa count recorded, and under the
homogeneity rule of §6.2 step 4 one failed seed makes the step's aggregate
undefined with no surviving-seed mean. Abscissas are fixed under bootstrap
resampling (§6.2), so a rank failure is structural: every replicate inherits
it and no interval can repair it. The machine-readable rule is
`phase2b.rank_rule` in `tools/phase2_contract.json`; the hardware arm keeps
its own, separate minimum of two for `EXP` (§5.4), which is never exported
to Phase 2B.

Every extrapolation regresses on the realized $\lambda_r$ (design.md §10
pre-registered choice). The nominal-$\lambda$ comparison arm of design.md
§10 is not repeated in Phase 2B **(design choice:** it differed from the
primary only in the third decimal in v0.1.0, `docs/results-minimal.md` §4**)**.

### 4.4 Extrapolators, with the primary declared in advance

All three extrapolators are computed from the same data at every step, seed
and cell. No extra executions are needed.

| Id | Estimator | Role |
|---|---|---|
| `LIN` | degree-1 ordinary least squares on $(\lambda_r, E)$, intercept at $\lambda_r = 0$ (the `LinearFactory` estimator, design.md §11) | **primary for every arm** |
| `QUAD` | degree-2 ordinary least squares on $(\lambda_r, E)$, intercept at $0$ (the `PolyFactory(order=2)` estimator, §9) | reported alongside |
| `EXP` | $E(\lambda) = a + b\,e^{-c\lambda}$ with the asymptote $a$ fixed in advance (the `ExpFactory(asymptote=a)` estimator), log-linear mode with the design.md §11 clamp policy, the sign being `np.sign` of the `numpy.polyfit` linear intercept minus $a$ (zero at equality, amendment A-2; the same sign seeds the `avoid_log` initial guess): any clamped seed at a step switches all eight seeds at that step to `avoid_log`, a failed nonlinear fit is recorded as `EXP_FIT_FAILED` with no estimate and no substitution (design.md §20 M3-3); at least three distinct realized abscissas in either mode (§4.3 rank rule, amendment A-1) | reported alongside |

**Why quadratic rather than Richardson.** Richardson extrapolation through
five scale factors is the degree-4 interpolating polynomial (mitiq
`RichardsonFactory` is "a particular case of a polynomial fit with order
equal to the number of data points minus 1", §9). A degree-4 extrapolant
through five noisy points amplifies scatter and is rejected; the degree-2
least-squares fit is the declared middle option.

**Declared asymptotes for `EXP` (design choice, with its limitation).**
$a = 0$ for $\langle Z_\pi\rangle/L$, for $(-1)^{i^*}\langle Z_{i^*}\rangle$,
and for each raw moment $\langle Z_{i^*}\rangle$, $\langle Z_{i^*+1}\rangle$,
$\langle Z_{i^*} Z_{i^*+1}\rangle$; $a = 2^{-L}$ for the return probability.
These are the values of the observables in the maximally mixed state,
which is a fact. That the noisy expectation converges to them as
$\lambda \to \infty$ is an **ansatz**, and it is a different ansatz under
each model: the maximally mixed state is the fixed point of the
depolarizing channels of `DEP`, but pure dephasing (`DEPH`) preserves
computational-basis populations and amplitude damping (`AMP`) is
non-unital with fixed point $\lvert 0\rangle^{\otimes L}$, so under those
models the fixed-asymptote exponential is a shape assumption with no
endpoint guarantee, and its estimates are labelled "fixed-asymptote
ansatz" in every table. `EXP` is reported alongside under every model, and
these labels are part of the report. Nothing here is a claim about the
shape of the noise response (design.md §11).

**Moment-wise rule for the connected correlator.** `CZZ` (§4.5) is nonlinear
in the moments and is not traceless. It is never extrapolated directly.
Under every extrapolator the three raw moments are extrapolated separately
and `CZZ` is formed from the extrapolated moments. This applies to `LIN`
and `QUAD` as well as `EXP`, so `CZZ` is defined the same way under all
three.

**Primary per arm.** `LIN` on `LOCAL` folding is the primary for every cell.
It is the v0.1.0 protocol (design.md §11, §15). `QUAD`, `EXP` and `GLOBAL`
are reported alongside in every table and chart that shows the primary.

**What counts as an outcome-driven selection violation.** Any of the
following, after any Phase 2B value has been seen, is a preregistration
deviation under §8 and voids the confirmatory claim of §4.10:

1. changing the primary extrapolator or folding variant, for any cell;
2. reporting the boundary of a non-primary combination as "the" result
   without the primary's boundary beside it;
3. omitting any computed extrapolator, folding variant, observable, cell or
   scan point from the saved tables or the chart inventory;
4. changing a tolerance, a mask, the peak schedule, a scan order, the
   persistence rule, the control-selection rule or the step window;
5. adding a cell or a scale factor not in the matrix of §4.11.

### 4.5 References and observables

**References for every $L$.** $E^{\mathrm{ED}}$ is computed for every
$L \in \{4, 6, 8\}$ by dense eigendecomposition of the $2^L$-dimensional
$H$ (`numpy.linalg.eigh`), with the residual
$\max_j \lVert H v_j - \epsilon_j v_j\rVert_2 \le \epsilon_{\mathrm{ED}} = 10^{-10}$
and the orthonormality defect $\lVert V^\dagger V - \mathbb{1}\rVert_{\max} \le 10^{-10}$
recorded; a violation halts EP-2B before any noisy cell. $E_0$ is the
noiseless statevector of the same transpiled circuit at every $n$. Both are
saved per $(L, n, \text{observable})$ in
`results/phase2/phase2b/reference_curves.csv` and are never interchanged
(§2.3).

**One measurement, four observables.** Every circuit is measured once in
the computational basis on all $L$ qubits. All four observables are
functions of the same count record (shot pipeline) or of the same
computational-basis probability vector (density-matrix pipeline). Their
estimates are therefore **correlated**. The bootstrap of §6 resamples the
count record once per replicate and recomputes all four observables from
that single resample, so the covariance is carried through every interval
and every difference; it is never assumed zero.

**Bit ordering.** In a count string $b_{L-1} \cdots b_1 b_0$, site $i$ is
bit $b_{i-1}$; site 1 is the rightmost bit (design.md §4). The Néel state
$\lvert Z_2\rangle = \lvert 0101\cdots\rangle_{\text{site}}$ has the count
string obtained by reversing the site string: `1010` for $L = 4$, `101010`
for $L = 6$, `10101010` for $L = 8$. $Z_i = +1$ for bit value $0$.

| Id | Definition | Units, range | Initial value on $\lvert Z_2\rangle$ | Revival polarity $\sigma$ | Circuit cost |
|---|---|---|---|---|---|
| `ZPI` | $\langle Z_\pi\rangle/L$, $Z_\pi = \sum_{i=1}^{L}(-1)^i Z_i$ (design.md §5) | dimensionless, $[-1, 1]$ | $-1$ | $-1$ (revival is a local minimum) | 0 extra circuits |
| `PRET` | $P_{\mathrm{ret}} = \lvert\langle Z_2\vert\psi(n)\rangle\rvert^2$: shot pipeline, the fraction of counts equal to the $\lvert Z_2\rangle$ count string; density-matrix pipeline, $\mathrm{Tr}[\rho\,\lvert Z_2\rangle\langle Z_2\rvert]$ | probability, $[0, 1]$ | $1$ | $+1$ (revival is a local maximum) | 0 extra circuits |
| `MLOC` | $(-1)^{i^*}\langle Z_{i^*}\rangle$ with $i^* = L/2$: site 2, 3, 4 for $L = 4, 6, 8$ | dimensionless, $[-1, 1]$ | $-1$ | $-1$ | 0 extra circuits |
| `CZZ` | $\langle Z_{i^*} Z_{i^*+1}\rangle - \langle Z_{i^*}\rangle\langle Z_{i^*+1}\rangle$ on the central bond $(i^*, i^*+1)$ | dimensionless, $[-1, 1]$ (connected correlator of two $\pm 1$ variables); nonlinear in the moments; not traceless | $0$ | none (not an endpoint) | 0 extra circuits |

**Why site $i^* = L/2$.** It is a bulk site (full longitudinal field
$-2V$, design.md §3), and one of the two sites nearest the chain centre;
the lower index is the tie-break. **(inference)** A central site is
expected to be the single-site observable least affected by the open
boundary; that is the motivation, not a guaranteed property. The factor
$(-1)^{i^*}$ makes the initial value $-1$ for every $L$, so amplitude
tolerances mean the same thing at every size.

**Why the central bond.** `CZZ` is the connected nearest-neighbour
correlator of the interaction term $H_{ZZ}$ on the central bond, at zero
additional circuit cost; **(inference)** the central bond is expected, not
guaranteed, to be the bond least affected by the boundary. It is declared
as a reported observable, not an endpoint.

**Dropped correlator.** The Paper's unequal-time correlator
$\mathcal{C}_Y$ requires $4 \times 2 \times \lfloor L/2\rfloor$ auxiliary
circuits per time point (design.md §5). Its cost is not justified by any
Phase 2B question; it is not in the matrix.

### 4.6 Peak and revival definition (deterministic, from noiseless information only)

The schedule is computed from $E_0$ alone, before any noisy or mitigated
value exists, and saved in `results/phase2/phase2b/peak_schedule.csv`.

1. **Search grid.** Integer steps $n = 1, \dots, N$ with $N = 48$. The
   quantity searched is $y(n) = \sigma_O\, O_0(n)$, the polarity-signed
   noiseless value of observable $O \in \{\texttt{ZPI}, \texttt{PRET}, \texttt{MLOC}\}$
   (polarity from the §4.5 table; `CZZ` has no schedule).
2. **Local-maximum rule.** $n$ is a candidate peak if and only if
   $2 \le n \le N-1$, $y(n) > y(n-1)$ and $y(n) \ge y(n+1)$. The strict left
   and non-strict right inequalities make the earliest step of an exact
   plateau the candidate. Steps $n = 1$ and $n = N$ are never peaks. Step
   $n = 0$ (the initial state, the global maximum of $y$) is not on the grid.
3. **Minimum separation.** Candidates are processed in ascending $n$. A
   candidate closer than $d_{\min} = 5$ steps to an already accepted peak is
   compared with it: the one with the larger $y$ is kept; on an exact tie the
   earlier one is kept.
4. **Indexing.** Accepted peaks are numbered $k = 1, 2, \dots$ in ascending
   $n$; $n_k^{O}$ denotes the grid step of peak $k$ of observable $O$.
5. **Sub-step timing by parabolic interpolation.** For a peak at grid step
   $n$ with $y_- = y(n-1)$, $y_0 = y(n)$, $y_+ = y(n+1)$:
   $$
   t^* = n + \frac{1}{2}\,\frac{y_- - y_+}{y_- - 2y_0 + y_+} .
   $$
   Window: the three points $n-1, n, n+1$ only. Failure policy: if the
   denominator is $\ge 0$ (not concave) or $\lvert t^* - n\rvert > 1$, then
   $t^* = n$ and the flag `INTERP_FALLBACK` is set. Timing is in Trotter
   steps, equal to $Vt$ with $V = 1$, $\Delta t = 1$.
6. **Amplitude.** The revival amplitude is the grid value $O(n_k)$ at the
   peak step, not an interpolated value.
7. **Revival identity and schedule.** The revival index $k \in \{1, 2\}$
   is defined on the `ZPI` noiseless schedule: $n_k := n_k^{\texttt{ZPI}}$.
   At $L = 6$ the recorded `ZPI` grid peaks are $n = 19$ and $n = 39$
   **(recorded, v0.1.0)**; all other peaks are unknown until EP-2B computes
   them. For `PRET` (and `MLOC`, reported only), peak $k$ is the accepted
   `PRET` peak whose grid step lies inside the window $W_k$ of item 9; if
   there is none, or more than one, the `PRET` reference for revival $k$ is
   `NO_SCHEDULED_PEAK`. **All four endpoints stay required at each declared
   revival.** A missing reference peak for any endpoint makes the whole
   condition $(\cdot, k)$ `UNAVAILABLE` for every combination: not a pass,
   not a fail, and never a pass on the remaining endpoints. If `ZPI` itself
   has fewer than two accepted peaks at some $L$, revival 2 is
   `UNAVAILABLE` at that $L$. All of this is decided from $E_0$ alone and
   recorded in the schedule file before any noisy value exists.
8. **The same rule on $E^{\mathrm{ED}}$, without reassigning identity.**
   Steps 1 to 6 are applied separately to the grid values
   $E^{\mathrm{ED}}(n)$, $n = 1, \dots, N$, per observable. The ED peak used
   for revival $k$ is the accepted ED peak whose grid step lies inside the
   same window $W_k$; if there is none, or more than one, the ED-referenced
   metrics for that revival and observable are `ED_PEAK_UNAVAILABLE` and
   are reported as unavailable. No ED peak is ever relabelled to a
   different $k$, and the $E_0$-referenced endpoints are unaffected.
9. **Unique, non-overlapping windows.** The window of revival $k$ is
   $W_k = [n_k - w, n_k + w]$ with $w = 4$, clipped to $[1, N]$. If two
   consecutive scheduled `ZPI` peaks satisfy $n_{k+1} - n_k < 2w + 1 = 9$,
   the windows would overlap; they are then truncated at the midpoint,
   $W_k \leftarrow [\,n_k - w,\; \lfloor (n_k + n_{k+1} - 1)/2 \rfloor\,]$ and
   $W_{k+1} \leftarrow [\,\lceil (n_k + n_{k+1} + 1)/2 \rceil,\; n_{k+1} + w\,]$,
   flagged `WINDOW_TRUNCATED`, so that no grid step belongs to two windows
   and one observed peak can never satisfy two revivals. A truncated window
   narrower than three steps makes that revival `UNAVAILABLE`. At $L = 6$
   the recorded peaks are 20 steps apart and no truncation occurs.

**Matching a noisy or mitigated curve to a scheduled peak.** For observable
$O$, revival $k$, and any curve $X(n)$ (unmitigated, mitigated by any
extrapolator, or a bootstrap replicate), using the same window $W_k$ for
every observable:

- matched step $\hat n_k = \arg\max_{n \in W_k} \sigma_O X(n)$, earliest on
  a tie;
- if $\hat n_k$ is an endpoint of $W_k$, the flag `NO_INTERIOR_PEAK` is set:
  the amplitude $X(\hat n_k)$ is still reported, the timing is undefined,
  and the timing endpoint is `INDETERMINATE` (§4.8);
- otherwise $t^*_k$ by the parabolic formula on
  $(\hat n_k - 1, \hat n_k, \hat n_k + 1)$ with the same failure policy.

Because the windows are disjoint (item 9), the matched step for revival
$k$ can never be the matched step for revival $k + 1$. $w = 4$ is less
than half the recorded revival period of about 20 steps
**(recorded, v0.1.0:** peaks at 19 and 39**)**. A timing endpoint is a
test only if a timing error beyond $\tau_t$ is observable: a window
truncated (item 9) to fewer than the five points $n_k^{O} \pm 2$ makes
the timing endpoint `TIMING_UNTESTABLE` (it can never be `PASS`; §5.9
item 8 gives the algebra), and the condition cannot be `PASS`.

### 4.7 Physics-aware metrics

Every metric below is defined for a mitigated curve $X$ (any extrapolator,
any folding, either pipeline) and for the unmitigated curve. Where a
reference enters, the metric is computed and named twice: superscript
$(E_0)$ against the noiseless Trotter reference, superscript
$(\mathrm{ED})$ against the exact continuous-time reference. Both are saved
in `results/phase2/phase2b/metrics_2b.csv`.

| Metric | Formula | Units | Edge cases |
|---|---|---|---|
| Revival amplitude error | $\Delta A_k^{(E_0)} = X(\hat n_k) - O_0(n_k^{O})$; $\Delta A_k^{(\mathrm{ED})} = X(\hat n_k) - E^{\mathrm{ED}}(n_k^{\mathrm{ED}})$ | observable units | `NO_SCHEDULED_PEAK`: condition `UNAVAILABLE`. `ED_PEAK_UNAVAILABLE`: the ED-referenced value unavailable, the $E_0$ one unaffected. |
| Revival timing error | $\Delta t_k^{(E_0)} = t^*_k[X] - t^*_k[O_0]$; $\Delta t_k^{(\mathrm{ED})} = t^*_k[X] - t^{*,\mathrm{ED}}_k$ | Trotter steps | `NO_INTERIOR_PEAK`: undefined, endpoint `INDETERMINATE`. `INTERP_FALLBACK` on either side: reported with the flag. |
| Time-integrated absolute error | $\mathrm{TIAE}^{(\mathrm{ref})} = \sum_{n=1}^{N-1} \tfrac{1}{2}\bigl(\lvert e(n)\rvert + \lvert e(n+1)\rvert\bigr)$ with $e(n) = X(n) - \mathrm{ref}(n)$, trapezoid rule, unit step, window $[1, 48]$ | observable units × steps | any undefined $X(n)$: `TIAE` undefined, count of undefined steps reported. |
| Deterministic plug-in error | $\epsilon^{\mathrm{DM}}_X(n) = X^{\mathrm{DM}}(n) - E_0(n)$: the error of the estimator applied to the exact computational-basis probabilities of the density-matrix pipeline. It is **not** a statistical bias: for the nonlinear estimators (`EXP`, the connected `CZZ`, the peak amplitude and timing) it differs in general from $\mathbb{E}[X^{\mathrm{SHOT}}] - E_0$. Error-reduction ratio $\mathrm{ER}(n) = \lvert\epsilon^{\mathrm{DM}}_{\mathrm{mit}}(n)\rvert / \lvert\epsilon^{\mathrm{DM}}_{\mathrm{noisy}}(n)\rvert$ | observable units; ratio dimensionless | ratio rule below. |
| Statistical bias (bootstrap estimate) | $\hat\beta_X(n) = \bar X^{\mathrm{boot}}(n) - \hat X^{\mathrm{SHOT}}(n)$: the bootstrap estimate of the **finite-sample bias of the estimator relative to its plug-in functional** (mean of the replicates minus the plug-in estimate, Efron 1979, §9). It is distinct from the total estimator error relative to a reference, $\hat X^{\mathrm{SHOT}}(n) - E_0(n)$ and $\hat X^{\mathrm{SHOT}}(n) - E^{\mathrm{ED}}(n)$, which are reported beside it with their intervals. No exact bias is claimed. | observable units | degenerate replicates (§6.7): reported as degenerate. |
| Uncertainty (statistical) | $u_X(n)$ = half-width of the percentile bootstrap interval of $X^{\mathrm{SHOT}}(n)$ at the level of the family the cell belongs to (§4.10, §6); uncertainty ratio $\mathrm{UR}(n) = u_{\mathrm{mit}}(n)/u_{\mathrm{noisy}}(n)$ | observable units; ratio dimensionless | ratio rule below; degenerate interval (§6): $u$ reported as degenerate, ratio undefined. |
| Mitigation gain versus depth and time | $\mathrm{IF}(n) = \varepsilon_u(n)/\varepsilon_m(n)$ with $\varepsilon_u, \varepsilon_m$ against $E_0$, the baseline-relevance filter $\varepsilon_{\min} = 0.01$ and the $\delta$ rule of design.md §13, on the density-matrix pipeline; plotted against $n$, which is also $Vt$, with the reference line $\mathrm{IF} = 1$ (design.md §13: above it ZNE helped); the global $\mathrm{GIF}$ over all 48 steps per cell, tabulated against $\kappa$ | dimensionless | as design.md §13. |
| Distinguishability from the control | For each named observable $O \in \{\texttt{ZPI}, \texttt{PRET}, \texttt{MLOC}\}$ separately, $D_k^{O} = O_{\mathrm{scar}}(n_k) - O_{\mathrm{ctrl}}(n_k)$ at the scheduled `ZPI` peak steps $n_k$, with the 95% percentile bootstrap interval of the difference (scar and control circuits are independent; each replicate resamples both). For `PRET` the two terms are return probabilities to **different** initial states (§4.9). Comparison family: exploratory, unadjusted, per observable and per $k$. | observable units | control absent: metric omitted with the recorded reason; `DISTINGUISHABLE` iff the interval excludes $0$, else `NOT_DISTINGUISHABLE`; degenerate interval: `INDETERMINATE`. A nonzero difference at the scar peak is not by itself evidence of scar-manifold separation or of better preservation; it says only that the two curves differ there. |

**Ratio rule for $\mathrm{ER}$ and $\mathrm{UR}$ (explicit, this
document).** With resolution $\delta_R = 10^{-9}$ in observable units:
if numerator and denominator are both finite and the denominator exceeds
$\delta_R$, the ratio is reported as a value; if the denominator is at most
$\delta_R$ and the numerator exceeds $\delta_R$, the ratio is reported as
the flagged lower bound "$\ge$ numerator$/\delta_R$" (`RATIO_LOWER_BOUND`);
if both are at most $\delta_R$, the ratio is undefined with the flag
`RATIO_ZERO_OVER_ZERO` ("both below resolution"); if either is non-finite
or degenerate, the ratio is undefined with the flag `RATIO_UNDEFINED`. No
non-finite value enters any table.

$\mathrm{ER}$, $\hat\beta$ and $\mathrm{UR}$ are **three quantities**. They
are never multiplied, averaged or otherwise combined into one score.
Deterministic error comes from the exact pipeline, statistical bias and
uncertainty from the shot pipeline, so each is measured where it is
cleanly defined. "Uncertainty reduction versus bias reduction" is reported
as the pair $(\mathrm{ER}(n), \mathrm{UR}(n))$ with $\hat\beta$ beside it.

**How the metric set prevents concealment.**

- Pointwise improvement cannot hide degraded revival structure, because
  the pass criterion of §4.8 is evaluated only at the scheduled revival
  peaks on amplitude and timing; a curve that is closer to $E_0$ on average
  but has a shifted or flattened revival fails there regardless of its
  root-mean-square error.
- Improvement in the point estimate cannot hide inflated variance, because
  the pass requires the entire bootstrap interval inside the tolerance band;
  an interval widened by extrapolation fails even when its centre is inside.
  $\mathrm{UR}(n)$ makes the inflation visible as its own number.
- A good $E_0$ score cannot be presented as agreement with exact dynamics,
  because every amplitude and timing error is reported against
  $E^{\mathrm{ED}}$ as well, under its own name (§2.4).
- $\mathrm{TIAE}$ is reported beside the peak metrics so a curve that
  matches the peaks but is wrong elsewhere is also visible.

### 4.8 Joint pass criterion and the primary boundary

**Endpoints.** Four endpoints per revival $k$: amplitude and timing, for
`ZPI` and `PRET`. Reference for every endpoint: $E_0$. (The same endpoints
against $E^{\mathrm{ED}}$ are computed and reported under their own names
and enter no pass decision; §2.4.)

**Tolerances (design choice).** $\tau_A^{Z_\pi} = 0.10$ (5% of the
observable's range of 2), $\tau_A^{P} = 0.05$ (5% of the range of 1),
$\tau_t = 1.0$ step (about 5% of the recorded revival period of about
20 steps). They are fixed by this document and the JSON.

**Per-endpoint status, with uncertainty.** For the shot pipeline, let
$[\ell, h]$ be the **decision interval** (§6.4: the equal-tailed percentile
bootstrap interval at the family's per-endpoint level; the 95% interval is
reported beside it and drives no decision) of the mitigated amplitude
$X(\hat n_k)$ or of the mitigated timing $t^*_k[X]$, and let the closed
tolerance band be

- amplitude: $[\,O_0(n_k^{O}) - \tau_A^{O},\; O_0(n_k^{O}) + \tau_A^{O}\,]$;
- timing: $[\,t^*_k[O_0] - \tau_t,\; t^*_k[O_0] + \tau_t\,]$.

Each endpoint has exactly one status by the three-way rule of §6.5:
`PASS` (interval inside the closed band, edges included), `FAIL` (interval
disjoint from the closed band: non-preservation supported), `OVERLAP`
(interval crosses a band edge: unresolved, neither), or `INDETERMINATE`
(interval undefined or degenerate per §6.7, including `NO_INTERIOR_PEAK`
and the undefined-replicate rule of §6.3). Non-inclusion alone is never
failure. Point estimates alone never pass.

**Joint status of a condition.** A condition is a tuple
$(L, \text{model}, \kappa, \text{folding}, \text{extrapolator}, k)$. Its
status is `UNAVAILABLE` if the schedule marked revival $k$ unavailable for
any endpoint (§4.6 item 7); otherwise `PASS` if all four endpoints are
`PASS`; otherwise `FAIL` if at least one endpoint is `FAIL`; otherwise
`OVERLAP` if at least one endpoint is `OVERLAP` and none is
`INDETERMINATE`; otherwise `INDETERMINATE`. **All four endpoints are
required at every declared revival**; no condition ever passes on a
subset of them. The conjunction inside a condition is an intersection-union
test (§6); it covers nothing beyond that condition.

**Density-matrix companion (deterministic ranges, exempt from the
statistical-degeneracy rules).** The same three-way inclusion rule is
evaluated on the density-matrix pipeline with the interval replaced by the
range across the eight fold seeds, $[\min_s X^{(s)}, \max_s X^{(s)}]$,
labelled "seed range, exact pipeline" and never called a confidence
interval. Because this range is deterministic, the bootstrap degeneracy
rules of §6.7 do **not** apply to it: a zero-width range is a valid
deterministic interval (a point), and under `GLOBAL` folding it is zero by
construction (§4.3) and is labelled "zero seed spread by construction",
which claims no statistical precision and invalidates nothing. The
range is defined per endpoint (amendment A-2): the **amplitude** range is
$[\min_s X^{(s)}(\hat n), \max_s X^{(s)}(\hat n)]$ over all eight seeds
at the step $\hat n$ matched on the **aggregated** curve (§4.6 matching and
tie rules); the **timing** range is $[\min_s t^*_s, \max_s t^*_s]$ over
each seed's **own** matched peak inside the **same** scheduled window
$W_k$, with the same matching, tie and interpolation rules. If any required
seed value is undefined (a missing or non-finite value, `NaN`, $+\infty$ or
$-\infty$, at any window point; an undefined $X^{(s)}(\hat n)$; an undefined
aggregate; or a seed with `NO_INTERIOR_PEAK` in the window), the whole
amplitude or timing range is undefined; there is never a partial range. A
companion endpoint is `INDETERMINATE` only when its plug-in value or its
range is undefined (`NO_INTERIOR_PEAK`, failed fit, non-finite, or
`TIMING_UNTESTABLE`). The companion yields a secondary, exploratory
boundary, reported beside the primary, that isolates the deterministic
plug-in error of the extrapolator (§4.7) from shot noise.

**Boundary estimator (deterministic).** For each combination
$(L, \text{model}, \text{folding}, \text{extrapolator})$ and each revival
$k$, on the shot pipeline:

1. Scan $\kappa$ in ascending order $0.25, 0.5, 1, 2, 4$ (only $\kappa = 1$
   exists for secondary models; their "scan" is the single point).
2. Persistence rule: the noise boundary $\kappa^*(k)$ is the largest scanned
   $\kappa_i$ such that the condition is `PASS` at every one of
   $\kappa_1, \dots, \kappa_i$. The status of the next level
   $\kappa_{i+1}$ classifies the boundary: `FAIL` there (non-preservation
   supported by a disjoint decision interval, §6.5) means the boundary is
   **located**; `OVERLAP`, `INDETERMINATE` or `UNAVAILABLE` there means the
   boundary is **unresolved** at $\kappa_{i+1}$, which is reported as such
   and is never described as an observed failure. A `PASS` that follows
   any non-`PASS` level does not move the boundary; it sets the flag
   `NON_MONOTONE`, and the full status sequence is reported.
3. First scanned level not `PASS`: $\kappa^*(k)$ = `BELOW_MIN_FAIL` if
   that level is `FAIL` (non-preservation supported even at 0.25), or
   `UNRESOLVED_AT_MIN` if it is `OVERLAP`, `INDETERMINATE` or `UNAVAILABLE`
   (no failure is demonstrated).
4. Every level `PASS`: $\kappa^*(k)$ = `AT_OR_ABOVE_MAX` (the scan does not
   locate a boundary at or below 4).
5. Depth boundary at each $\kappa$: $k^*(\kappa)$ is the largest $k$ such
   that revivals $1, \dots, k$ are all `PASS` at that $\kappa$; $k^* = 0$
   if revival 1 is not `PASS`, with the same located/unresolved
   classification from the status of revival $k^* + 1$.
6. Endpoint disagreement: the joint boundary is by construction at most
   the minimum over the four endpoints' individual boundaries, and each
   endpoint's own boundary and status sequence is reported in the same row
   so the reader sees which endpoint limits the result and whether it did
   so by `FAIL` or by `INDETERMINATE`. Every combination is reported as a
   full $k \times \kappa$ status map with the three statuses distinguished
   (chart CH-B4 in the contract), not only as the derived boundary.

**The primary result** is, for each $(L, \text{model})$ in the primary
family of §4.10, the pair $(\kappa^*(1), \kappa^*(2))$ with its
located/unresolved classification and the map $k^*(\kappa)$, computed with
the family-level intervals declared there. The same estimator with
unadjusted intervals gives the exploratory maps for every other
combination, reported beside it.

### 4.9 Non-scar control: selection rule to be executed later

The control is included only if a noiseless exact-diagonalization rule,
fixed here and executed by EP-2B before any noisy result exists, identifies
a computational-basis product state with comparable energy density and
substantially lower scar-manifold overlap. **This selection is not run in
this task.** Every comparison below is on computed double-precision values
with the inequality exactly as written; a candidate whose deciding quantity
lies within $10^{-12}$ of a threshold is treated as the inequality says and
is flagged `THRESHOLD_MARGINAL` in the record. Ordering never uses a
tolerance (items 5 and 8), because a within-tolerance tie relation is not
transitive; the checker exercises a three-value near-tie fixture.

1. **Candidate set and order.** All $2^L$ computational-basis product
   states, enumerated by the ascending integer value of the site-ordered
   bitstring (site 1 most significant), excluding $\lvert Z_2\rangle$ and
   $\lvert Z_2'\rangle$ (its translate).
2. **Energy density.** $e(\psi) = \langle\psi\vert H\vert\psi\rangle / L$ in
   units of $V$. For a product state in the $Z$ basis the $X$ term
   contributes zero, so $e$ is the diagonal energy per site.
3. **Comparable energy density.** $\lvert e(\psi) - e(Z_2)\rvert \le \delta_e = 0.1$.
4. **Eigenspace grouping (adjacent-gap chaining).** Sort the eigenvalues
   of $H$ ascending. Consecutive eigenvalues whose gap is at most
   $\epsilon_{\mathrm{deg}} = 10^{-9}$ belong to the same group; a group
   ends at the first gap larger than $\epsilon_{\mathrm{deg}}$ (chaining on
   adjacent gaps, not on total spread). Each group $j$ has the projector
   $P_j$ onto the span of its eigenvectors and the representative energy
   $\bar\epsilon_j$ (the group mean). The measure below is
   basis-independent inside each group.
5. **Scar manifold.** Rank the groups by the exact key
   $(-w_j, \bar\epsilon_j, j)$ ascending, with
   $w_j = \langle Z_2\vert P_j\vert Z_2\rangle$ compared as computed
   doubles (a total order; no tolerance enters the ordering). Consecutive
   groups in that order whose $w$ differ by at most $10^{-12}$ are flagged
   `WEIGHT_MARGINAL` in the record. The scar manifold $S$ is the smallest
   leading set in that order with $\sum_{j \in S} w_j \ge W_S = 0.9$.
6. **Overlap measure.** $w_S(\psi) = \sum_{j \in S} \langle\psi\vert P_j\vert\psi\rangle$.
7. **Substantially lower overlap.** $w_S(\psi) \le w_{\max} = 0.25$.
8. **Tie-break among qualifying candidates.** Order by the exact key
   $(\lvert e(\psi) - e(Z_2)\rvert,\; w_S(\psi),\; \text{index})$
   ascending, compared as computed doubles: a total order, so the selected
   candidate is unique and no tolerance enters the ordering. If the
   selected candidate and the next one differ by at most $10^{-12}$ in the
   deciding key component, the selection is flagged `TIE_MARGINAL` and both
   are recorded; the selection stands.
9. **If none qualifies**, the control is omitted at that $L$ and the reason
   is recorded in `results/phase2/phase2b/control_selection.json`: the
   three closest candidates ordered by the same key (smallest
   $\lvert e - e(Z_2)\rvert$, then smallest $w_S$, then index), each with
   its bitstring, $e$, $w_S$, and which criterion it failed. The
   distinguishability metric is then omitted with that reason, and the
   reason is preserved in every report that would have carried the metric.

**Control observables.** `ZPI`, `MLOC` and `CZZ` use the same definitions
as for the scar state. The control's return probability projects onto
**its own** initial product state, $P_{\mathrm{ret}}^{\mathrm{ctrl}}(n) = \lvert\langle \psi_{\mathrm{ctrl}}\vert\psi(n)\rangle\rvert^2$
(the conventional return definition); the Néel projector is never applied
to the control. The control's own count string is recorded with the
selection.

**Control reference curves (state-indexed).** The scar references
$E_0$ and $E^{\mathrm{ED}}$ are defined for $\lvert Z_2\rangle$ and cannot
serve the control. For a qualifying control at size $L$, EP-2B computes
its own references before any noisy control cell runs and saves them in
`reference_curves.csv` under the state label `CTRL`: $E_0^{\mathrm{ctrl}}(n)$
by 48 noiseless statevector executions of the same transpiled circuit
with the control product state prepared by $X$ gates on its `1` sites
(one execution per step, exactly as for the scar state), and
$E^{\mathrm{ED},\mathrm{ctrl}}(t)$ from the **same** eigendecomposition of
$H$ already computed for the scar state (the eigenvectors are reused;
only the initial-state amplitudes change), for all four observables with
the control's own return projector. Each qualifying control therefore
adds 48 statevector executions; three qualifying controls add 144, and
the all-run total of §4.11 counts them. The control's deterministic
plug-in error and every reference-dependent metric of §4.7 are computed
against $E_0^{\mathrm{ctrl}}$ and $E^{\mathrm{ED},\mathrm{ctrl}}$, never
against the scar references.

A qualifying control is run in the twelve conditional cells of §4.11
(`DEP` and `DEPH` at $\kappa = 1$, both foldings, each $L$), with the same
observables, seeds and pipelines as the scar cells. The scar state's `ZPI`
schedule fixes the comparison steps $n_k$ for the distinguishability
metric of §4.7; the control's own curve is not searched for peaks, and the
control has no revival endpoints of its own.

**(inference)** At $L = 6$ the polarized state $\lvert 000000\rangle$ has
the same diagonal energy as $\lvert Z_2\rangle$ ($E = -5$), so at least one
candidate meets the energy window; whether any candidate meets the overlap
criterion is unknown until the rule runs.

### 4.10 The primary family, its multiplicity treatment, and the exploratory family

**Primary family (fixed in advance).**

| Element | Declaration |
|---|---|
| Folding and extrapolator | `LOCAL` and `LIN` (the v0.1.0 protocol), shot pipeline, reference $E_0$, observables `ZPI` and `PRET` |
| Sizes | $L \in \{4, 6, 8\}$ |
| Noise models | `DEP`, `DEPH` (the primary models) |
| Scan variable and ordered grid | $\kappa$ on $0.25, 0.5, 1, 2, 4$, scanned ascending within each $(L, \text{model})$ |
| Depth dimension | revivals $k = 1$ and $k = 2$ |
| Primary family $\mathcal{F}_{\mathrm{P}}$ | the $m = 3 \times 2 \times 5 \times 2 = 60$ conditions $(L, \text{model}, \kappa, k)$, four endpoints each, 240 endpoint intervals |
| Estimator | §4.8, applied to each $(L, \text{model})$ scan |
| Result | six pairs $(\kappa^*(1), \kappa^*(2))$ with their located/unresolved classification, six maps $k^*(\kappa)$, and the full $60$-condition status map with every endpoint interval |
| Hypothesis | H-2B of §4.1 |

**Multiplicity and uncertainty over the whole family.** A boundary claim is
a claim about every condition in its scan at once, and it makes both
positive claims (`PASS`) and negative claims (`FAIL`, §6.5). Both error
types are controlled at the family level by the rule of §6.4 and §6.6:

- within a condition, the four endpoints must all be `PASS`; the
  conjunction is an intersection-union test whose size is at most the size
  of one endpoint test (§6.6, Berger and Hsu 1996), so no adjustment is
  needed inside a condition;
- across the $m = 60$ conditions, every endpoint decision uses the
  decision interval at per-endpoint level
  $\alpha_e = \alpha_{\mathrm{F}} / (4m) = 0.05 / 240 = 2.083 \times 10^{-4}$
  (coverage $0.99979$), from $B_{\mathrm{P}} = 48000$ replicates, with the
  quantile algorithm of §6.3 (the lower quantile interpolates between the
  5th and 6th order statistics; it is not an exact rank);
- the resulting family-wise bounds, by Boole's inequality: probability of
  any false pass at most $m\,\alpha_e = 0.0125$; probability of any false
  negative at most $4m\,\alpha_e = 0.05$; simultaneous coverage of the 240
  decision intervals at least $1 - 240\,\alpha_e = 0.95$.

The reported 95% intervals are saved beside every decision interval and
drive no decision (§6.4). All of this is conditional on the bootstrap
intervals having their nominal coverage, which is the standard caveat of
any bootstrap claim (§6.3).

**A `FAIL` is a supported negative claim; unresolved is not failure.** A
`FAIL` requires the decision interval to be disjoint from the closed band
(§6.5), so a false `FAIL` is bounded at the family level as above. A
`FAIL` lowers a reported boundary and the persistence rule of §4.8 makes a
later `PASS` unable to restore it; `NON_MONOTONE` records the contrary
evidence and exempts nothing (§4.1). An `OVERLAP`, `INDETERMINATE` or
`UNAVAILABLE` condition leaves the boundary unresolved, which is reported
as unresolved and is never counted as a demonstrated failure or as a pass.

**Exploratory family.** Every other cell, combination, revival and scan
point (global folding, the quadratic and exponential extrapolators, the
secondary noise models, the control comparisons, the density-matrix
companion boundaries) is exploratory. It is reported with unadjusted 95%
percentile intervals ($B = 2000$, §6), labelled exploratory in every table
and chart, and never presented as a confirmed preservation claim.
Exploratory expectations E-2B-1 and E-2B-2 (§4.1) are reported as met, not
met, or not evaluable.

**No substitution.** The primary family may not be reduced to a subset,
replaced by a different combination, or swapped with an exploratory map
after any value has been seen. Doing so is a selection violation under
§4.4.

### 4.11 The fixed complete matrix

Every cell has, identically: steps $n = 1, \dots, 48$; nominal scale factors
$\{1, 1.25, 1.5, 1.75, 2\}$; fold seeds $\{1000, \dots, 1007\}$; the three
extrapolators `LIN` (primary), `QUAD`, `EXP`; the four observables `ZPI`,
`PRET`, `MLOC`, `CZZ`; both pipelines, density-matrix (`DM`, exact) and
shot (`SHOT`, 8192 shots, `seed_simulator` $= 10^6 \cdot \text{cell\_index} + 100\,n + 10\,k + j$
for seed index $k = 0..7$ and scale index $j = 0..4$, unique across the
whole matrix). Per step and run cell: `DM` executes 1 unmitigated unfolded
circuit plus $8 \times 5 = 40$ folded circuits (41); `SHOT` executes
$8 \times 5 = 40$ folded circuits (the $\lambda = 1$ folds return the base
circuit and are executed once per seed; the shot baseline is the mean of
those eight, design.md §13). A run cell is therefore $81 \times 48 = 3888$
circuit executions. The scar $E_0$ is 48 statevector executions per $L$
(144 total), shared by every scar cell at that $L$; a qualifying control
adds its own 48 state-indexed statevector executions per $L$ (§4.9).
$E^{\mathrm{ED}}$ is one dense eigendecomposition per $L$, reused for the
control's exact curve; neither is a circuit execution.

Status codes in the table: **run**; **not run** (secondary model, $\kappa$
other than 1: deliberately not executed); **blocked** (`CAL`, waiting for
the Phase 2C snapshot); **conditional** (control, §4.9).

| # | $L$ | model | tier | $\kappa$ | folding | state | status | executions |
|---|---|---|---|---|---|---|---|---|
| 1 | 4 | `DEP` | primary | 0.25 | `LOCAL` | `Z2` | run | 3,888 |
| 2 | 4 | `DEP` | primary | 0.25 | `GLOBAL` | `Z2` | run | 3,888 |
| 3 | 4 | `DEP` | primary | 0.5 | `LOCAL` | `Z2` | run | 3,888 |
| 4 | 4 | `DEP` | primary | 0.5 | `GLOBAL` | `Z2` | run | 3,888 |
| 5 | 4 | `DEP` | primary | 1 | `LOCAL` | `Z2` | run | 3,888 |
| 6 | 4 | `DEP` | primary | 1 | `GLOBAL` | `Z2` | run | 3,888 |
| 7 | 4 | `DEP` | primary | 2 | `LOCAL` | `Z2` | run | 3,888 |
| 8 | 4 | `DEP` | primary | 2 | `GLOBAL` | `Z2` | run | 3,888 |
| 9 | 4 | `DEP` | primary | 4 | `LOCAL` | `Z2` | run | 3,888 |
| 10 | 4 | `DEP` | primary | 4 | `GLOBAL` | `Z2` | run | 3,888 |
| 11 | 4 | `DEPH` | primary | 0.25 | `LOCAL` | `Z2` | run | 3,888 |
| 12 | 4 | `DEPH` | primary | 0.25 | `GLOBAL` | `Z2` | run | 3,888 |
| 13 | 4 | `DEPH` | primary | 0.5 | `LOCAL` | `Z2` | run | 3,888 |
| 14 | 4 | `DEPH` | primary | 0.5 | `GLOBAL` | `Z2` | run | 3,888 |
| 15 | 4 | `DEPH` | primary | 1 | `LOCAL` | `Z2` | run | 3,888 |
| 16 | 4 | `DEPH` | primary | 1 | `GLOBAL` | `Z2` | run | 3,888 |
| 17 | 4 | `DEPH` | primary | 2 | `LOCAL` | `Z2` | run | 3,888 |
| 18 | 4 | `DEPH` | primary | 2 | `GLOBAL` | `Z2` | run | 3,888 |
| 19 | 4 | `DEPH` | primary | 4 | `LOCAL` | `Z2` | run | 3,888 |
| 20 | 4 | `DEPH` | primary | 4 | `GLOBAL` | `Z2` | run | 3,888 |
| 21 | 4 | `AMP` | secondary | 0.25 | `LOCAL` | `Z2` | not run | 0 |
| 22 | 4 | `AMP` | secondary | 0.25 | `GLOBAL` | `Z2` | not run | 0 |
| 23 | 4 | `AMP` | secondary | 0.5 | `LOCAL` | `Z2` | not run | 0 |
| 24 | 4 | `AMP` | secondary | 0.5 | `GLOBAL` | `Z2` | not run | 0 |
| 25 | 4 | `AMP` | secondary | 1 | `LOCAL` | `Z2` | run | 3,888 |
| 26 | 4 | `AMP` | secondary | 1 | `GLOBAL` | `Z2` | run | 3,888 |
| 27 | 4 | `AMP` | secondary | 2 | `LOCAL` | `Z2` | not run | 0 |
| 28 | 4 | `AMP` | secondary | 2 | `GLOBAL` | `Z2` | not run | 0 |
| 29 | 4 | `AMP` | secondary | 4 | `LOCAL` | `Z2` | not run | 0 |
| 30 | 4 | `AMP` | secondary | 4 | `GLOBAL` | `Z2` | not run | 0 |
| 31 | 4 | `RO` | secondary | 0.25 | `LOCAL` | `Z2` | not run | 0 |
| 32 | 4 | `RO` | secondary | 0.25 | `GLOBAL` | `Z2` | not run | 0 |
| 33 | 4 | `RO` | secondary | 0.5 | `LOCAL` | `Z2` | not run | 0 |
| 34 | 4 | `RO` | secondary | 0.5 | `GLOBAL` | `Z2` | not run | 0 |
| 35 | 4 | `RO` | secondary | 1 | `LOCAL` | `Z2` | run | 3,888 |
| 36 | 4 | `RO` | secondary | 1 | `GLOBAL` | `Z2` | run | 3,888 |
| 37 | 4 | `RO` | secondary | 2 | `LOCAL` | `Z2` | not run | 0 |
| 38 | 4 | `RO` | secondary | 2 | `GLOBAL` | `Z2` | not run | 0 |
| 39 | 4 | `RO` | secondary | 4 | `LOCAL` | `Z2` | not run | 0 |
| 40 | 4 | `RO` | secondary | 4 | `GLOBAL` | `Z2` | not run | 0 |
| 41 | 4 | `CAL` | secondary | 0.25 | `LOCAL` | `Z2` | not run | 0 |
| 42 | 4 | `CAL` | secondary | 0.25 | `GLOBAL` | `Z2` | not run | 0 |
| 43 | 4 | `CAL` | secondary | 0.5 | `LOCAL` | `Z2` | not run | 0 |
| 44 | 4 | `CAL` | secondary | 0.5 | `GLOBAL` | `Z2` | not run | 0 |
| 45 | 4 | `CAL` | secondary | 1 | `LOCAL` | `Z2` | blocked | 0 |
| 46 | 4 | `CAL` | secondary | 1 | `GLOBAL` | `Z2` | blocked | 0 |
| 47 | 4 | `CAL` | secondary | 2 | `LOCAL` | `Z2` | not run | 0 |
| 48 | 4 | `CAL` | secondary | 2 | `GLOBAL` | `Z2` | not run | 0 |
| 49 | 4 | `CAL` | secondary | 4 | `LOCAL` | `Z2` | not run | 0 |
| 50 | 4 | `CAL` | secondary | 4 | `GLOBAL` | `Z2` | not run | 0 |
| 51 | 6 | `DEP` | primary | 0.25 | `LOCAL` | `Z2` | run | 3,888 |
| 52 | 6 | `DEP` | primary | 0.25 | `GLOBAL` | `Z2` | run | 3,888 |
| 53 | 6 | `DEP` | primary | 0.5 | `LOCAL` | `Z2` | run | 3,888 |
| 54 | 6 | `DEP` | primary | 0.5 | `GLOBAL` | `Z2` | run | 3,888 |
| 55 | 6 | `DEP` | primary | 1 | `LOCAL` | `Z2` | run | 3,888 |
| 56 | 6 | `DEP` | primary | 1 | `GLOBAL` | `Z2` | run | 3,888 |
| 57 | 6 | `DEP` | primary | 2 | `LOCAL` | `Z2` | run | 3,888 |
| 58 | 6 | `DEP` | primary | 2 | `GLOBAL` | `Z2` | run | 3,888 |
| 59 | 6 | `DEP` | primary | 4 | `LOCAL` | `Z2` | run | 3,888 |
| 60 | 6 | `DEP` | primary | 4 | `GLOBAL` | `Z2` | run | 3,888 |
| 61 | 6 | `DEPH` | primary | 0.25 | `LOCAL` | `Z2` | run | 3,888 |
| 62 | 6 | `DEPH` | primary | 0.25 | `GLOBAL` | `Z2` | run | 3,888 |
| 63 | 6 | `DEPH` | primary | 0.5 | `LOCAL` | `Z2` | run | 3,888 |
| 64 | 6 | `DEPH` | primary | 0.5 | `GLOBAL` | `Z2` | run | 3,888 |
| 65 | 6 | `DEPH` | primary | 1 | `LOCAL` | `Z2` | run | 3,888 |
| 66 | 6 | `DEPH` | primary | 1 | `GLOBAL` | `Z2` | run | 3,888 |
| 67 | 6 | `DEPH` | primary | 2 | `LOCAL` | `Z2` | run | 3,888 |
| 68 | 6 | `DEPH` | primary | 2 | `GLOBAL` | `Z2` | run | 3,888 |
| 69 | 6 | `DEPH` | primary | 4 | `LOCAL` | `Z2` | run | 3,888 |
| 70 | 6 | `DEPH` | primary | 4 | `GLOBAL` | `Z2` | run | 3,888 |
| 71 | 6 | `AMP` | secondary | 0.25 | `LOCAL` | `Z2` | not run | 0 |
| 72 | 6 | `AMP` | secondary | 0.25 | `GLOBAL` | `Z2` | not run | 0 |
| 73 | 6 | `AMP` | secondary | 0.5 | `LOCAL` | `Z2` | not run | 0 |
| 74 | 6 | `AMP` | secondary | 0.5 | `GLOBAL` | `Z2` | not run | 0 |
| 75 | 6 | `AMP` | secondary | 1 | `LOCAL` | `Z2` | run | 3,888 |
| 76 | 6 | `AMP` | secondary | 1 | `GLOBAL` | `Z2` | run | 3,888 |
| 77 | 6 | `AMP` | secondary | 2 | `LOCAL` | `Z2` | not run | 0 |
| 78 | 6 | `AMP` | secondary | 2 | `GLOBAL` | `Z2` | not run | 0 |
| 79 | 6 | `AMP` | secondary | 4 | `LOCAL` | `Z2` | not run | 0 |
| 80 | 6 | `AMP` | secondary | 4 | `GLOBAL` | `Z2` | not run | 0 |
| 81 | 6 | `RO` | secondary | 0.25 | `LOCAL` | `Z2` | not run | 0 |
| 82 | 6 | `RO` | secondary | 0.25 | `GLOBAL` | `Z2` | not run | 0 |
| 83 | 6 | `RO` | secondary | 0.5 | `LOCAL` | `Z2` | not run | 0 |
| 84 | 6 | `RO` | secondary | 0.5 | `GLOBAL` | `Z2` | not run | 0 |
| 85 | 6 | `RO` | secondary | 1 | `LOCAL` | `Z2` | run | 3,888 |
| 86 | 6 | `RO` | secondary | 1 | `GLOBAL` | `Z2` | run | 3,888 |
| 87 | 6 | `RO` | secondary | 2 | `LOCAL` | `Z2` | not run | 0 |
| 88 | 6 | `RO` | secondary | 2 | `GLOBAL` | `Z2` | not run | 0 |
| 89 | 6 | `RO` | secondary | 4 | `LOCAL` | `Z2` | not run | 0 |
| 90 | 6 | `RO` | secondary | 4 | `GLOBAL` | `Z2` | not run | 0 |
| 91 | 6 | `CAL` | secondary | 0.25 | `LOCAL` | `Z2` | not run | 0 |
| 92 | 6 | `CAL` | secondary | 0.25 | `GLOBAL` | `Z2` | not run | 0 |
| 93 | 6 | `CAL` | secondary | 0.5 | `LOCAL` | `Z2` | not run | 0 |
| 94 | 6 | `CAL` | secondary | 0.5 | `GLOBAL` | `Z2` | not run | 0 |
| 95 | 6 | `CAL` | secondary | 1 | `LOCAL` | `Z2` | blocked | 0 |
| 96 | 6 | `CAL` | secondary | 1 | `GLOBAL` | `Z2` | blocked | 0 |
| 97 | 6 | `CAL` | secondary | 2 | `LOCAL` | `Z2` | not run | 0 |
| 98 | 6 | `CAL` | secondary | 2 | `GLOBAL` | `Z2` | not run | 0 |
| 99 | 6 | `CAL` | secondary | 4 | `LOCAL` | `Z2` | not run | 0 |
| 100 | 6 | `CAL` | secondary | 4 | `GLOBAL` | `Z2` | not run | 0 |
| 101 | 8 | `DEP` | primary | 0.25 | `LOCAL` | `Z2` | run | 3,888 |
| 102 | 8 | `DEP` | primary | 0.25 | `GLOBAL` | `Z2` | run | 3,888 |
| 103 | 8 | `DEP` | primary | 0.5 | `LOCAL` | `Z2` | run | 3,888 |
| 104 | 8 | `DEP` | primary | 0.5 | `GLOBAL` | `Z2` | run | 3,888 |
| 105 | 8 | `DEP` | primary | 1 | `LOCAL` | `Z2` | run | 3,888 |
| 106 | 8 | `DEP` | primary | 1 | `GLOBAL` | `Z2` | run | 3,888 |
| 107 | 8 | `DEP` | primary | 2 | `LOCAL` | `Z2` | run | 3,888 |
| 108 | 8 | `DEP` | primary | 2 | `GLOBAL` | `Z2` | run | 3,888 |
| 109 | 8 | `DEP` | primary | 4 | `LOCAL` | `Z2` | run | 3,888 |
| 110 | 8 | `DEP` | primary | 4 | `GLOBAL` | `Z2` | run | 3,888 |
| 111 | 8 | `DEPH` | primary | 0.25 | `LOCAL` | `Z2` | run | 3,888 |
| 112 | 8 | `DEPH` | primary | 0.25 | `GLOBAL` | `Z2` | run | 3,888 |
| 113 | 8 | `DEPH` | primary | 0.5 | `LOCAL` | `Z2` | run | 3,888 |
| 114 | 8 | `DEPH` | primary | 0.5 | `GLOBAL` | `Z2` | run | 3,888 |
| 115 | 8 | `DEPH` | primary | 1 | `LOCAL` | `Z2` | run | 3,888 |
| 116 | 8 | `DEPH` | primary | 1 | `GLOBAL` | `Z2` | run | 3,888 |
| 117 | 8 | `DEPH` | primary | 2 | `LOCAL` | `Z2` | run | 3,888 |
| 118 | 8 | `DEPH` | primary | 2 | `GLOBAL` | `Z2` | run | 3,888 |
| 119 | 8 | `DEPH` | primary | 4 | `LOCAL` | `Z2` | run | 3,888 |
| 120 | 8 | `DEPH` | primary | 4 | `GLOBAL` | `Z2` | run | 3,888 |
| 121 | 8 | `AMP` | secondary | 0.25 | `LOCAL` | `Z2` | not run | 0 |
| 122 | 8 | `AMP` | secondary | 0.25 | `GLOBAL` | `Z2` | not run | 0 |
| 123 | 8 | `AMP` | secondary | 0.5 | `LOCAL` | `Z2` | not run | 0 |
| 124 | 8 | `AMP` | secondary | 0.5 | `GLOBAL` | `Z2` | not run | 0 |
| 125 | 8 | `AMP` | secondary | 1 | `LOCAL` | `Z2` | run | 3,888 |
| 126 | 8 | `AMP` | secondary | 1 | `GLOBAL` | `Z2` | run | 3,888 |
| 127 | 8 | `AMP` | secondary | 2 | `LOCAL` | `Z2` | not run | 0 |
| 128 | 8 | `AMP` | secondary | 2 | `GLOBAL` | `Z2` | not run | 0 |
| 129 | 8 | `AMP` | secondary | 4 | `LOCAL` | `Z2` | not run | 0 |
| 130 | 8 | `AMP` | secondary | 4 | `GLOBAL` | `Z2` | not run | 0 |
| 131 | 8 | `RO` | secondary | 0.25 | `LOCAL` | `Z2` | not run | 0 |
| 132 | 8 | `RO` | secondary | 0.25 | `GLOBAL` | `Z2` | not run | 0 |
| 133 | 8 | `RO` | secondary | 0.5 | `LOCAL` | `Z2` | not run | 0 |
| 134 | 8 | `RO` | secondary | 0.5 | `GLOBAL` | `Z2` | not run | 0 |
| 135 | 8 | `RO` | secondary | 1 | `LOCAL` | `Z2` | run | 3,888 |
| 136 | 8 | `RO` | secondary | 1 | `GLOBAL` | `Z2` | run | 3,888 |
| 137 | 8 | `RO` | secondary | 2 | `LOCAL` | `Z2` | not run | 0 |
| 138 | 8 | `RO` | secondary | 2 | `GLOBAL` | `Z2` | not run | 0 |
| 139 | 8 | `RO` | secondary | 4 | `LOCAL` | `Z2` | not run | 0 |
| 140 | 8 | `RO` | secondary | 4 | `GLOBAL` | `Z2` | not run | 0 |
| 141 | 8 | `CAL` | secondary | 0.25 | `LOCAL` | `Z2` | not run | 0 |
| 142 | 8 | `CAL` | secondary | 0.25 | `GLOBAL` | `Z2` | not run | 0 |
| 143 | 8 | `CAL` | secondary | 0.5 | `LOCAL` | `Z2` | not run | 0 |
| 144 | 8 | `CAL` | secondary | 0.5 | `GLOBAL` | `Z2` | not run | 0 |
| 145 | 8 | `CAL` | secondary | 1 | `LOCAL` | `Z2` | blocked | 0 |
| 146 | 8 | `CAL` | secondary | 1 | `GLOBAL` | `Z2` | blocked | 0 |
| 147 | 8 | `CAL` | secondary | 2 | `LOCAL` | `Z2` | not run | 0 |
| 148 | 8 | `CAL` | secondary | 2 | `GLOBAL` | `Z2` | not run | 0 |
| 149 | 8 | `CAL` | secondary | 4 | `LOCAL` | `Z2` | not run | 0 |
| 150 | 8 | `CAL` | secondary | 4 | `GLOBAL` | `Z2` | not run | 0 |
| 151 | 4 | `DEP` | control | 1 | `LOCAL` | `CTRL` | conditional | 3,888 |
| 152 | 4 | `DEP` | control | 1 | `GLOBAL` | `CTRL` | conditional | 3,888 |
| 153 | 4 | `DEPH` | control | 1 | `LOCAL` | `CTRL` | conditional | 3,888 |
| 154 | 4 | `DEPH` | control | 1 | `GLOBAL` | `CTRL` | conditional | 3,888 |
| 155 | 6 | `DEP` | control | 1 | `LOCAL` | `CTRL` | conditional | 3,888 |
| 156 | 6 | `DEP` | control | 1 | `GLOBAL` | `CTRL` | conditional | 3,888 |
| 157 | 6 | `DEPH` | control | 1 | `LOCAL` | `CTRL` | conditional | 3,888 |
| 158 | 6 | `DEPH` | control | 1 | `GLOBAL` | `CTRL` | conditional | 3,888 |
| 159 | 8 | `DEP` | control | 1 | `LOCAL` | `CTRL` | conditional | 3,888 |
| 160 | 8 | `DEP` | control | 1 | `GLOBAL` | `CTRL` | conditional | 3,888 |
| 161 | 8 | `DEPH` | control | 1 | `LOCAL` | `CTRL` | conditional | 3,888 |
| 162 | 8 | `DEPH` | control | 1 | `GLOBAL` | `CTRL` | conditional | 3,888 |

**Totals (recomputed by the offline checker from the machine-readable
matrix, including not-run, blocked and conditional cells; the checker also
verifies that every `seed_simulator` value is unique across the whole
matrix).** 150 enumerated scar cells: 72 run, 72 not run, 6 blocked; 12
conditional control cells. Circuit executions: $72 \times 3888 = 279{,}936$
plus 144 scar statevector executions $= 280{,}080$ unconditional;
$+ 23{,}328$ if the six `CAL` cells are unblocked; $+ 46{,}656 + 144$
(twelve control cells plus three state-indexed control reference runs of
48) if a control qualifies at every $L$; grand total if everything runs
$350{,}208$.

**Wall clock (inference).** The recorded v0.1.0 run executed 2000 circuits
at $L = 6$ in 250.3 s of wall clock (design.md §20 A2-4), about 0.13 s per
execution including overhead. Scaling by execution count alone gives about
$3.5 \times 10^4$ s for the unconditional matrix; $L = 8$ density matrices
are 16 times larger than $L = 6$ ones and $L = 4$ ones 16 times smaller, so
the honest order-of-magnitude statement is $10^4$ to $10^5$ s, hours to a
few days on one workstation, to be measured and recorded by EP-2B. No
timing enters any result file.

---

## 5. Phase 2C: IBM hardware confirmation at $L = 6$

### 5.1 Scope and status

Phase 2C is a design. Nothing in it is submitted, prepared for submission,
or evaluated against a live service in this task. Submission requires the
**second human gate** of §5.12, which can only be reached after exact
transpilation and a backend-specific preflight that do not exist yet. The
hardware noise is whatever the chosen device has at run time; it is
observed, never selected (§4.2). Every IBM rule below is cited to the
documentation read on 2026-09-07 (§9, entries S-IBM-1 to S-IBM-8).

Fixed parameters: $L = 6$, the design.md §15 circuit, nominal scale factors
$\lambda \in \{1, 1.5, 2\}$, `LOCAL` folding only with four fold instances
(seeds $1000$ to $1003$), 4096 shots per circuit preferred, roughly 8 to
12 time points chosen by §5.9 from both primary observables.

### 5.2 Backend selection: deterministic, evaluated at gate time, recorded

The rule is evaluated once, at gate time, from one snapshot of the
service's backend list, and its full evaluation table is saved to
`results/phase2/phase2c/backend_selection.json`. No post-hoc swapping: if
the chosen backend is not operational at submission time, the run is
deferred and a new gate is required with a new snapshot; the design never
substitutes another backend silently.

**Eligibility** (all required): a real device (`simulator=False`);
`operational=True`; `min_num_qubits=6` (filters of
`QiskitRuntimeService.backends()`, S-IBM-6); accessible under the account's
Open Plan instance; a native gate set containing `rz`, `sx`, `x` and one
two-qubit gate among `cx`, `ecr`, `cz`; a reported `default_rep_delay` and
`rep_delay_range`; a reported `reset` instruction duration in the target
(§5.4 item 5); and at least one **eligible six-path** under the layout rule
below.

**Layout rule and score (one equation, used by §4.2 and §5.2 alike).** For
a candidate simple path $(q_1, \dots, q_L)$ of physical qubits:

$$
\mathrm{score} = \sum_{i=1}^{L-1} e_2(q_i, q_{i+1}) \;+\; \sum_{i=1}^{L} \tfrac{1}{2}\bigl(P(1\vert 0)_{q_i} + P(0\vert 1)_{q_i}\bigr),
$$

the **sum** over bonds of the two-qubit gate error plus the **sum** over
qubits of the per-qubit mean assignment error (not a mean over qubits).
$e_2(q_i, q_{i+1})$ is the error of the backend's native two-qubit gate on
that bond: if the target reports the gate in both directions, the larger
of the two errors (conservative, since direction is fixed only at
transpilation); if in one direction, that one. A path is **ineligible** if
any needed calibration value (a bond's two-qubit error in every reported
direction, a qubit's assignment errors, $T_1$, $T_2$, or any single-qubit
gate error or duration on a path qubit) is missing, `None` or non-finite.
Among eligible paths, the minimum score wins; an exact tie (equal computed
doubles) goes to the lexicographically smallest tuple of physical indices;
the path is oriented so that site 1 is the endpoint with the smaller
physical index. The layout is computed for $L = 4, 6, 8$ from the same
snapshot; the $L = 6$ layout is the hardware chain, and all three are
recorded for the `CAL` model of §4.2.

**Ordering.** Eligible backends are ordered by their best six-path score,
ascending.

**Tie-break.** Equal scores (exact equality of the computed doubles) are
broken by the smaller number of pending jobs at gate time, then by the
lexicographically smaller backend name. Scores within $10^{-12}$ of each
other are flagged `SCORE_MARGINAL` in the record but are still ordered by
exact value (a total order; no tolerance enters the ordering).

### 5.3 Calibration capture

**Pre-run snapshot**, taken at gate time before layout selection and
transpilation, saved to `results/phase2/phase2c/calibration_snapshot_pre.json`:
`backend.properties().to_dict()` in full, for **every** qubit and gate of
the device (including its last-update timestamp); `backend.configuration().to_dict()`
(basis gates, coupling map with edge directions, `dt`, `rep_delay_range`,
`default_rep_delay`, `dynamic_reprate_enabled`); the complete
`backend.target` serialized as one row per (instruction name, qubit tuple)
with duration and error (S-IBM-6), including `measure` and `reset`, for the
whole device; the UTC capture time; the backend name and version. The whole
device is captured so that the `CAL` reconstruction of §4.2 is possible for
every $L \in \{4, 6, 8\}$ layout, not only for the six-site chain.

**Post-run snapshot**, the same capture immediately after the job reaches a
terminal state, saved to `calibration_snapshot_post.json`. The two are
compared field by field into `calibration_change.csv`, one typed row per
numeric leaf of **either** snapshot: the identified field, its unit from
the unit inventory s, dimensionless, Hz, the pre and post values, and a
status: `PRESENT` (both values, $\mathrm{pre} \ne 0$), `ZERO_PRE` (both
values, $\mathrm{pre} = 0$), `MISSING_POST` (a pre-run field absent
post-run) or `NEW_POST` (a post-run field absent pre-run); a missing or new
field is always a row, never omitted. For `PRESENT` and `ZERO_PRE` rows the
absolute change $\lvert \mathrm{post} - \mathrm{pre}\rvert$ is recorded in
the field's own unit, and for `PRESENT` rows the dimensionless relative
change $\lvert \mathrm{post} - \mathrm{pre}\rvert / \lvert \mathrm{pre}\rvert$.
`usage_actual.json` records the largest absolute change **within each
unit** with its field, the largest relative change with its field, and the
lists of zero-pre, missing and new fields. No maximum is ever taken across
fields of different units: a change in $T_1$ (seconds) and a change in a
gate error (dimensionless) are never compared. All of it is information
only. No drift claim is made from it: PUB execution order is not
guaranteed (S-IBM-5), so the snapshots bound nothing about the state of
the device during any particular circuit.

### 5.4 Exact transpilation, layout preservation and duration accounting

1. **Layout and routing.** The logical circuit (design.md §15, site $i$ on
   logical qubit $q_{i-1}$) is compiled with
   `generate_preset_pass_manager(optimization_level=0, backend=...,
   initial_layout=chain, seed_transpiler=7)`, where `chain` maps logical
   $q_{i-1}$ to the $i$-th physical qubit of the recorded six-path. Every
   two-qubit gate of the circuit acts on a nearest-neighbour pair of the
   path, so no routing is needed; the preflight **asserts** that the
   transpiled circuit contains no `swap` and no two-qubit gate on any pair
   other than the five path bonds, and that no instruction of any kind acts
   on a physical qubit outside the path. Any violation fails the preflight.
   Idle device qubits carry no instruction and are not measured.
2. **Fold** the transpiled circuit, before measurement, with the `LOCAL`
   policy of §4.3 restricted to the backend's native two-qubit gate
   (`cx`, `ecr` and `cz` are each self-inverse, so the inserted inverse is
   the same native gate). **Hardware folding scope: `LOCAL` only.** Global
   folding is a simulator-only comparison (§4.3) and is not run on
   hardware. The implementation verifies that every instruction of every
   folded circuit is in the backend's native set (the v0.1.0 T6-style
   check, design.md §17); if the inverse of any gate is not native, that
   gate's inverse is re-transpiled at `optimization_level=0` and the extra
   instructions are counted in the realized scale. $\lambda_r$ is the native
   two-qubit gate count ratio, measured from the folded circuit.
3. **Measure** the six path qubits, appended after folding, with physical
   qubit `chain[i-1]` written to classical bit $i - 1$, so the count string
   keeps the design.md §4 convention (site 1 is the rightmost bit) and the
   observables of §4.5 apply unchanged. The physical-to-classical mapping
   is recorded per circuit.
4. **Ideal-equivalence check (offline, at gate time, before submission).**
   For every scheduled point, the noiseless statevector expectation values
   of the transpiled unfolded circuit **and of every folded circuit**
   (folding is the identity in the ideal case) must equal the declared
   $E_0$ for all four observables within $\eta_E = 10^{-9}$. This is a
   simulator computation in the Phase 2 environment, not a hardware
   action; a violation fails the preflight. Its results are saved to
   `results/phase2/phase2c/ideal_equivalence.csv`.
5. **Schedule** each folded, measured circuit with the snapshot's
   instruction durations (ASAP scheduling over the `target` durations, in
   units of `dt`) and record the scheduled circuit duration $D_c$ in
   seconds, **including the measurement instruction**.
6. **Reset.** `init_qubits=True` is kept (S-IBM-5, S-IBM-7). The reset
   duration $D_{\mathrm{init}}$ is the snapshot's `reset` instruction
   duration on the path qubits (the maximum over the six). If the target
   does not expose a `reset` duration, the preflight **fails closed**: no
   fallback value is used, because no value is established as conservative
   for an arbitrary backend. (A backend without a reported reset duration
   is ineligible under §5.2.)
7. **Records.** Every transpiled and folded circuit is saved in QPY to
   `results/phase2/phase2c/transpiled_circuits.qpy`, with one row per
   circuit in `circuit_durations.csv`: point $n$, nominal $\lambda$, fold
   seed, instruction counts by name, native two-qubit count, $\lambda_r$,
   depth, $D_c$, $D_{\mathrm{init}}$, `dt`, physical-to-classical mapping.

**Extrapolators on hardware.** With $\lambda_r$ values from the three
nominal scale factors, the following are computed from the same data:
`LIN` (**primary**, at least two distinct abscissas required), `QUAD`
(three distinct abscissas required; with exactly three points it is the
exactly determined degree-2 interpolant, equal to Richardson extrapolation
through three points, and is flagged `EXACT_FIT` with no residual), and
`EXP` with the declared asymptote (its two-parameter log-linear fit
requires at least two distinct abscissas, with the design.md §11 clamp
policy). Fewer distinct abscissas than required gives `FIT_FAILURE` for
that extrapolator at that point. The hardware minimum for `EXP` is
$n^{\mathrm{EXP}}_{\min,\mathrm{2C}} = 2$ (`phase2c.transpilation.rank_rule`,
constant C-EXP-MIN-2C); it is a separate arm with three nominal scale
factors, it was left unchanged by amendment A-1, and it is never exported
to the Phase 2B rule of §4.3, whose `EXP` minimum is three. No extrapolator is selected after the
data are seen (§4.4).

### 5.5 Execution mode and options

**Job mode, one job.** Open Plan users cannot submit session jobs;
workloads must run in job mode or batch mode (S-IBM-3). Batch mode is
**not** used: the batch `max_time` is a time-to-live, not an aggregate QPU
usage cap, and running jobs finish beyond it (S-IBM-4). If a batch were
ever used instead, the rule that would bound aggregate usage is the sum of
the member jobs' `max_execution_time` values, which would have to satisfy
§5.7(b) in place of the single value; this document does not authorize
that alternative.

**Options** (SamplerV2, S-IBM-7, S-IBM-8), all recorded in
`job_record.json`: `max_execution_time = 479`; `execution.init_qubits =
True`; `execution.rep_delay` = the backend's `default_rep_delay`, read from
the snapshot and recorded (S-IBM-5); `execution.meas_type = "classified"`;
`dynamical_decoupling.enable = False`; `twirling.enable_gates = False` and
`twirling.enable_measure = False`; shots given explicitly per PUB. Dynamical
decoupling and twirling are disabled so that the only mitigation under
test is ZNE **(design choice)**.

### 5.6 `max_execution_time`

$\texttt{max\_execution\_time} = T_{\mathrm{lim}} = 479$ seconds. This value
is **QPU usage seconds, not wall-clock time** (S-IBM-1). The effective
limit is the smaller of this value and the service maximum of three hours
(S-IBM-1), so the effective limit is 479 s. If the job reaches it, the
service cancels it and raises `RuntimeJobMaxTimeoutError` (S-IBM-1); the
usage consumed up to cancellation is read back as below. The enforced
limit is a protection separate from the estimate: it bounds what the job
can consume whatever the estimate turns out to be worth.

**Actual usage** is read after the terminal state from `job.usage()` and
`job.metrics()["usage"]["quantum_seconds"]` (S-IBM-1, S-IBM-2) and saved to
`results/phase2/phase2c/usage_actual.json` beside the estimate.

### 5.7 The 480-second rule (fail-closed preflight)

Open Plan allowance: $T_{\mathrm{open}} = 600$ s of QPU usage per
**28-day rolling window** (S-IBM-1). Design cap: $T_{\mathrm{cap}} = 480$ s.
Reserve: $T_{\mathrm{open}} - T_{\mathrm{cap}} = 120$ s. Enforced job limit:
$T_{\mathrm{lim}} = 479$ s.

**One fit predicate, used everywhere.** $\mathrm{fits}(T) :\Leftrightarrow T < T_{\mathrm{lim}} = 479$
(strict). Because $479 < 480$, $\mathrm{fits}(T)$ implies $T < 480$: an
estimate that fits cannot be at or above the cap, and an estimate of
$479.5$, which is below the cap but predicts a job the limit would cancel,
does not fit. Every reduction step of §5.10 and every gate check uses this
predicate and no other.

Submission is permitted only if all of the following are verified at gate
time, recorded in `usage_estimate.json`, and re-verified by §5.7(d); if any
cannot be verified, no submission:

- (a) **Estimate fits:** $\mathrm{fits}(T_{\mathrm{est}}^{\mathrm{cons}})$
  for the binding conservative estimate of §5.8; the single-job baseline
  is recorded with it for information only.
- (b) **Worst-case accumulated usage within the cap:**
  $U_{\mathrm{auth}} + T_{\mathrm{lim}} \le T_{\mathrm{cap}}$, that is
  $U_{\mathrm{auth}} + 479 \le 480$, where
  $U_{\mathrm{auth}} = U_{\mathrm{cons}} + U_{\mathrm{out}}$ counts **other**
  workloads only, so this candidate job's limit of 479 s is added exactly
  once: $U_{\mathrm{cons}}$ is the QPU usage consumed on the instance in
  the trailing 28 days, read from the account; $U_{\mathrm{out}}$ is the
  sum of (i) the `max_execution_time` of every queued or running job on
  the instance other than this candidate, read from the service, and (ii)
  the limits of every open entry, other than this candidate, in the
  **approved ledger snapshot** `results/phase2/phase2c/authorization_ledger_approved.json`,
  written at gate time and never modified afterwards. The snapshot lists
  every gate-authorized job with its limit, its gate time and, once
  submitted, its job id. Which record each stage reads: at gate time, (b)
  reads the service and the snapshot; at the pre-submit recheck (d), the
  service again and the **same** snapshot, and any authorization not in
  the snapshot means a new gate; after submission, the separate
  reconciliation record `authorization_ledger_reconciliation.json` closes
  an entry when its job id appears in the service's usage or job list and
  records the service usage, so no job is ever counted both from the
  snapshot and from the service. Each quantity is saved with its timestamp
  and their sum in `usage_estimate.json`. The reserve then holds by the enforced limit,
  whatever the estimate was worth:
  $T_{\mathrm{open}} - (U_{\mathrm{auth}} + T_{\mathrm{lim}}) = 121 - U_{\mathrm{auth}} \ge 120$
  exactly when $U_{\mathrm{auth}} \le 1$ s. In practice (b) requires a
  window with no other QPU use.
- (c) **Nothing else planned:** no other QPU workload is planned on the
  instance inside the same window; the gate record says so.
- (d) **Last pre-submit recheck, in its own artifact.** The approved
  `usage_estimate.json` and the manifest that hashes it are immutable
  after the gate. Immediately before the submission call, a separate
  `pre_submit_recheck.json` is written with a fresh timestamp (new by
  construction) containing: re-read $U_{\mathrm{cons}}$ and
  $U_{\mathrm{out}}$ and their sum; the backend name, version and
  operational state; the selected chain; the recomputed SHA-256 of every
  approved artifact. **Semantic values that must match the gate record:**
  backend name and version, chain tuple, every approved artifact hash,
  and the schedule; **values that must still satisfy the rule with their
  fresh readings:** condition (b) with the re-read usage. Any mismatch or
  any failed condition aborts the submission and requires a new gate. The
  recheck artifact is itself hashed into the post-gate manifest after the
  run.

Arithmetic, for the record: $600 - 480 = 120$; $\mathrm{fits}(T) \Leftrightarrow T < 479$;
$U_{\mathrm{auth}} + 479 \le 480 \Leftrightarrow U_{\mathrm{auth}} \le 1$;
$600 - (U_{\mathrm{auth}} + 479) = 121 - U_{\mathrm{auth}}$, which is at
least $120$ under (b) and equals exactly $120$ at $U_{\mathrm{auth}} = 1$.

### 5.8 The estimate: approximate, conditional on the split count

The documented baseline (S-IBM-2) is
$\langle\text{per sub-job overhead}\rangle + (\texttt{rep\_delay} + \langle\text{circuit duration}\rangle) \times \langle\text{num executions}\rangle$,
with about 2 s per sub-job, `rep_delay` defaulting to 250 µs on most
backends, and executions equal to circuits times shots after PUB broadcast.
The documentation states this is an approximation and that the service may
split a job into several sub-jobs; the split rule is not documented
(S-IBM-2). This design therefore treats the estimate as **approximate and
conditional on the sub-job count $S$**, and states its uncertainty
instead of asserting exactness:

$$
T_{\mathrm{est}}^{(S)} = t_{\mathrm{sub}} \cdot S \;+\; M \sum_{c=1}^{N_{\mathrm{circ}}} \bigl(\texttt{rep\_delay} + D_c + D_{\mathrm{init}}\bigr)\, N_{\mathrm{shots}},
$$

with $t_{\mathrm{sub}} = 2$ s (S-IBM-2); $M = 1.2$, a declared multiplier
for unknown per-execution overhead **(design choice; it is a declared
allowance, not a derived bound)**; $D_c$ and $D_{\mathrm{init}}$ from §5.4,
measured from the snapshot's reported durations; `rep_delay` from the
snapshot. The sub-job count is unknown, so the **binding** estimate is the
conservative one, $T_{\mathrm{est}}^{\mathrm{cons}} := T_{\mathrm{est}}^{(S_{\mathrm{cons}})}$
with $S_{\mathrm{cons}} = N_{\mathrm{circ}}$, one sub-job per circuit.
This rests on a stated **assumption**: that the service does not split
the shots of a single circuit across sub-jobs, so that one sub-job per
circuit is the finest split. No primary source read for this document
establishes that; if the assumption is false the estimate is not
conservative, and the enforced limit of §5.6 is the protection that
remains. The gate (§5.7(a)) and every reduction step (§5.10) use
$\mathrm{fits}(T_{\mathrm{est}}^{\mathrm{cons}})$ and nothing else; there
is no accepted-risk exception for any declared estimate at or above
$T_{\mathrm{lim}}$. The single-job baseline $T_{\mathrm{est}}^{(1)}$ is
recorded beside it for information. Nothing in this estimate is exact:
durations are the snapshot's reported values, overhead is allowed for by
$M$, and the split is assumed. After the run, actual usage is compared
with both values and the ratios are recorded; a ratio above 1 against
$T_{\mathrm{est}}^{\mathrm{cons}}$ falsifies the assumption for that
backend and any later design must use that finding.

**Illustrative arithmetic (inference; not the preflight, and not a
feasibility proof).** With the full §5.9 schedule of 12 points, 3 scale
factors and 4 fold instances, $N_{\mathrm{circ}} = 144$ and
$N_{\mathrm{exec}} = 144 \times 4096 = 589{,}824$. Taking, for illustration
only, $D_c = 220\ \mu\mathrm{s}$ for every circuit, `rep_delay`
$= 250\ \mu\mathrm{s}$ and $D_{\mathrm{init}} = 10\ \mu\mathrm{s}$: per
execution $480\ \mu\mathrm{s}$; $589{,}824 \times 480\ \mu\mathrm{s} = 283.1$ s;
$\times 1.2 = 339.7$ s; $T_{\mathrm{est}}^{(1)} = 341.7$ s;
$T_{\mathrm{est}}^{\mathrm{cons}} = 339.7 + 2 \times 144 = 627.7$ s, which
does **not** fit: under these assumed durations the full 144-circuit
schedule would be reduced by §5.10 before any gate. These numbers use
assumed durations and show only that the policy binds in this range; the
binding numbers are the snapshot's durations at gate time.

### 5.9 Time-point schedule from noiseless information only, for both required observables

The schedule is a deterministic function of $E_0$ at $L = 6$ (the
noiseless Trotter curve, $n = 1, \dots, 48$), computed by EP-2C-preflight
and saved to `results/phase2/phase2c/schedule.json` before any hardware
outcome exists. Points are never chosen or changed after seeing hardware
data. The point set is built from **both** primary observables so that
every required endpoint is structurally evaluable before any QPU second is
spent.

1. **Reference peaks.** Compute the `ZPI` grid peaks $n_1^Z, n_2^Z$ and
   the `PRET` grid peaks by §4.6, with the revival identity rule of §4.6
   item 7: $n_k^P$ is the `PRET` peak inside the `ZPI` window $W_k$. At
   $L = 6$ the recorded `ZPI` peaks are 19 and 39 **(recorded, v0.1.0)**;
   the `PRET` peaks are unknown until EP-2C-preflight computes them.
2. **Blocking on missing references.** If $n_1^Z$ or $n_1^P$ does not
   exist, revival 1 is `UNAVAILABLE` and the **preflight is blocked**: no
   schedule, no gate, no submission, reason recorded. If $n_2^Z$ or
   $n_2^P$ does not exist, revival 2 is dropped from the schedule and the
   reason recorded; the run proceeds with revival 1 only.
3. **Anti-revival point.** $n_a = \arg\max_{1 \le n < n_1^Z} \langle Z_\pi\rangle/L$
   on the grid (expected 10, **recorded, v0.1.0**), earliest on a tie.
4. **Cores and extended windows.** For each available revival $k$ and each
   endpoint observable $O \in \{Z, P\}$: the **core**
   $C_k^{O} = \{n_k^{O} - 1, n_k^{O}, n_k^{O} + 1\}$ (the three points the
   timing estimator needs when the matched peak sits on the reference
   step) and the **extended window**
   $E_k^{O} = \{n_k^{O} - 2, \dots, n_k^{O} + 2\}$, both intersected with
   $[1, 48]$. $C_k = C_k^{Z} \cup C_k^{P}$ and $E_k = E_k^{Z} \cup E_k^{P}$.
5. **Full schedule.** $\mathcal{P} = \{1, n_a\} \cup E_1 \cup E_2$ (with
   $E_2$ absent if revival 2 was dropped). When $n_k^P = n_k^Z$ this is 12
   points (expected $\{1, 10, 17, \dots, 21, 37, \dots, 41\}$); when the
   two peaks differ by one or two steps it is up to 16.
6. **Size priority rule (target 8 to 12 points).** While
   $\lvert\mathcal{P}\rvert > 12$, remove in this fixed order: $n_a$; then
   $1$; then the point of $E_2 \setminus C_2$ farthest from $n_2^Z$ (larger
   $n$ first on a tie); then the point of $E_1 \setminus C_1$ farthest from
   $n_1^Z$ (larger $n$ first on a tie). Core points are never removed by
   this rule.
7. **Stored windows.** For every endpoint $(O, k)$ the **stored matching
   window** is $W_k^{O} = \mathcal{P} \cap [n_k^{O} - 2, n_k^{O} + 2]$, the
   measured points within two steps of the reference peak. The windows
   are written to `schedule.json` and are what §5.11 uses; no fixed
   "five-point window" is assumed after any removal.
8. **Structural evaluability requirement, including timing
   testability.** A timing endpoint is a test only if a timing error
   larger than $\tau_t = 1$ step can be observed. On a three-point window
   centred on the reference step that is impossible: for an interior
   maximum with drops $a = y_0 - y_- > 0$ and $b = y_0 - y_+ \ge 0$ the
   parabolic offset is $t^* - n = (a - b)/(2(a + b)) \in [-0.5, 0.5]$, the
   reference timing lies in the same interval, and an edge maximum is
   undefined rather than failing; every finite timing value would then
   sit inside the tolerance automatically and the criterion could not
   fail. The preflight therefore requires, for **both** revival-1
   endpoints, the full extended window
   $E_1^{O} = \{n_1^{O} - 2, \dots, n_1^{O} + 2\} \subseteq \mathcal{P}$
   (so a match at $n_1^{O} \pm 1$ is interior and can give
   $\lvert t^* - t^*_{\mathrm{ref}}\rvert > 1$). This is checked after the
   full schedule, after every reduction step of §5.10, and at the gate;
   if it fails at any point the run is **abandoned before submission**
   with the reason recorded. In every phase, a timing endpoint whose
   stored window does not contain $n^{O}_k \pm 2$ is `TIMING_UNTESTABLE`:
   it is reported with its interval but can never be `PASS`, and a
   condition containing it can never be `PASS`. The checker demonstrates
   the three-point bound and the five-point testability on synthetic
   curves (contract §C7).
9. **Circuits.** Per point: 3 scale factors × 4 fold instances
   (seeds 1000 to 1003) = 12 circuits; 12 points give $N_{\mathrm{circ}} = 144$
   at 4096 shots.

**Reduced-point matching algorithm (used by §5.11 on hardware data).** For
endpoint $(O, k)$ with stored window $W_k^{O}$ and a hardware curve $X(n)$
defined on $\mathcal{P}$: the matched step is
$\hat n = \arg\max_{n \in W_k^{O}} \sigma_O X(n)$, earliest on a tie; the
match is **interior** if and only if $\hat n - 1$ and $\hat n + 1$ are both
measured points in $W_k^{O}$; if interior, the timing is the parabolic
formula of §4.6 on $(\hat n - 1, \hat n, \hat n + 1)$ with its failure
policy; otherwise `NO_INTERIOR_PEAK` and the timing endpoint is
`INDETERMINATE`. The amplitude endpoint uses $X(\hat n)$ in every case. The
same algorithm is applied to each bootstrap replicate. A timing endpoint
whose stored window lacks $n_k^{O} \pm 2$ is `TIMING_UNTESTABLE` (item 8)
whatever the data show.

### 5.10 Deterministic under-cap reduction policy

If §5.7(a) fails with the full schedule, apply the following steps in
order, recomputing the binding estimate $T_{\mathrm{est}}^{\mathrm{cons}}$
of §5.8 after each with the same $\mathrm{fits}$ predicate, and stop at
the first step at which $\mathrm{fits}(T_{\mathrm{est}}^{\mathrm{cons}})$
holds. After every step the structural requirement
$E_1 \subseteq \mathcal{P}$ of §5.9 item 8 is rechecked; a step that would
violate it is not applied and the policy proceeds to the next step. The sequence uses only the snapshot and the
transpiled durations, never a hardware outcome, and it terminates because
it is finite.

| Step | Reduction | Effect on the design |
|---|---|---|
| R1 | remove $E_2 \setminus C_2$ | revival-2 windows shrink to their cores |
| R2 | remove $C_2$ | revival-2 endpoints abandoned, recorded |
| R3 | fold instances $4 \to 3$ (drop seed 1003) | seed spread coarser |
| R4 | fold instances $3 \to 2$ (drop seed 1002) | seed spread minimal |
| R5 | remove $n = 1$ | no early-time point |
| R6 | remove $n_a$ | no anti-revival point |
| R7 | shots $4096 \to 2048$ | wider intervals |
| R8 | shots $2048 \to 1024$ | wider intervals |
| Floor | $\neg\,\mathrm{fits}(T_{\mathrm{est}}^{\mathrm{cons}})$ after R8 | **abandon**: no submission; recorded in `reduction_log.json` |

The floor configuration is $E_1 = E_1^{Z} \cup E_1^{P}$ (five to nine
points), three scale factors, two fold instances, 1024 shots: 30 to 54
circuits. The extended windows of both revival-1 endpoints are never
reduced, because a narrower window would make the timing criterion
untestable (§5.9 item 8); the run is abandoned rather than reduced
further. Every applied and skipped step is
written to `reduction_log.json` with the estimate bracket before and after
and the structural check result.

### 5.11 Success and failure rules (shot data)

The endpoints, tolerances, statuses and the required-endpoint rule are
those of §4.6 and §4.8; matching uses the **stored windows** and the
reduced-point algorithm of §5.9 on whatever point set was actually
submitted: amplitude and timing for `ZPI` and `PRET` against $E_0$ (the
$L = 6$ noiseless Trotter curve). Because §5.9 item 8 guarantees both
revival-1 cores are measured, every required endpoint is structurally
evaluable; an `INDETERMINATE` can still arise from the data (an edge
match or a degenerate interval), never from the design. The reference
$E^{\mathrm{ED}}$ enters no pass decision and is reported beside every
metric (§2.4).

- **Confirmatory condition CF-2C:** revival $k = 1$, four endpoints. The
  family has one condition, so the per-endpoint decision level is
  $\alpha_e = 0.05 / 4 = 0.0125$ (§6.4): each endpoint's decision interval
  is the equal-tailed percentile bootstrap interval at coverage $0.9875$
  from $B = 2000$ replicates of the 4096-shot records; the 95% interval is
  reported beside it. Statuses follow the three-way rule of §6.5: `PASS`
  (decision interval inside the closed band), `FAIL` (decision interval
  disjoint from the closed band: non-preservation supported), `OVERLAP`
  (unresolved), `INDETERMINATE`. The condition is `PASS` only if all four
  endpoints are `PASS`; it never passes on a subset.
- **Revival 2**, if retained by §5.9 and §5.10, is exploratory with 95%
  intervals.
- **Extrapolators.** `LIN` is primary; `QUAD` (exactly determined through
  three points) and fixed-asymptote `EXP` are reported beside it (§5.4).
  Folding on hardware is `LOCAL` only (§5.4 item 2).
- **Descriptive quantities**, no decision, saved in
  `results/phase2/phase2c/step_metrics_hw.csv` and
  `peak_metrics_hw.csv` (contract §C2.3): the raw $\lambda = 1$ values;
  $\mathrm{IF}(n)$ at each measured point, defined on the shot plug-in
  point estimates as $\varepsilon_{\mathrm{raw}}/\varepsilon_{\mathrm{mit}}$
  against $E_0$ with the design.md §13 shot-pipeline rule
  ($\varepsilon_{\min} = 0.01$ baseline-relevance filter,
  $\delta_{\mathrm{shot}} = 10^{-3}$ flagged lower bound); the uncertainty
  ratio of the decision-interval half-widths; the plug-in amplitude, timing
  and matched step of every endpoint with their errors against both
  references; the seed spread across fold instances; `MLOC` and `CZZ` at
  every point.

**Interpretation.** `PASS` at CF-2C licenses the statement "on this
device, on this date, with this chain, ZNE preserved the revival-1
amplitude and timing of $\langle Z_\pi\rangle/L$ and $P_{\mathrm{ret}}$
relative to the noiseless Trotter circuit within the declared tolerances,
at the declared level, under the assumption that each circuit's shots are
exchangeable draws from one distribution (§6.2); the intervals do not
contain device drift or correlated-error variability". `FAIL` licenses "non-preservation of at least one
named endpoint is supported at the declared level". `OVERLAP` and
`INDETERMINATE` license only the reported intervals. Nothing about other
devices, dates, chains, sizes or continuous-time dynamics is licensed by
any outcome.

### 5.12 The second human gate

**Presented:** the backend selection table (§5.2) and the pre-run snapshot
(§5.3); the schedule and any reduction log (§5.9, §5.10); the exact PUB
list (every circuit, its shots, its fold seed and $\lambda_r$); the
transpiled-circuit records and `circuit_durations.csv` (§5.4);
`usage_estimate.json` with the binding conservative estimate
$T_{\mathrm{est}}^{\mathrm{cons}}$ of §5.8 and the value of
$\mathrm{fits}(T_{\mathrm{est}}^{\mathrm{cons}})$, the single-job baseline
for information only, and the conditions of §5.7 with their values,
including $U_{\mathrm{cons}}$, $U_{\mathrm{out}}$, their sum and
timestamps, together with the approved ledger snapshot; the
options dump of §5.5; the offline checker's pass on the preflight
artifacts (EP-2C-preflight, contract §C7); a statement that no other QPU
use is planned in the window.

**Must be true:** §5.7(a), (b), (c) verified at the gate and (d) at
submission; both revival-1 cores are in the schedule (§5.9 item 8); every
circuit passed the layout, native-instruction and ideal-equivalence checks
of §5.4; the schedule is at or above the floor; the reset duration was
read from the target (no fallback); the snapshot is less than 24 hours old
**(design choice)**; the preflight artifacts are unchanged since the
checker ran (exact SHA-256 hashes in the manifest match).

**Authorizes:** exactly one submission of exactly that job, on that
backend, within 24 hours of the gate. Any change to any presented item,
any expiry, any failure of the job before completion, or any wish to
resubmit requires a new gate with a new snapshot and a new preflight, and
must again satisfy §5.7(b) with the updated $U_{\mathrm{auth}}$, which after
any real usage in the window will ordinarily make a second run impossible
until the window rolls. That consequence is accepted.

### 5.13 What Phase 2C does and does not license

Phase 2C confirms or fails to confirm the $L = 6$, revival-1 preservation
endpoints on one device at one time. It does not calibrate the simulator
noise models, does not establish the Phase 2B boundary on hardware, and
does not test any claim about continuous-time dynamics; the
$E^{\mathrm{ED}}$ comparison is reported so the reader can see the Trotter
gap, not to claim it was closed.

---

## 6. Statistics

### 6.1 Where uncertainty comes from, per arm

| Arm | Source of variation | Uncertainty statement | Interval type |
|---|---|---|---|
| Phase 2A (exact density matrix, $\lambda = 1$, no folding) | none: deterministic | numerical bound interval conditional on $\eta_E$ (§3.6, §3.10) | bound interval, no coverage level |
| Phase 2B density-matrix pipeline | folding configuration across the eight seeds (`LOCAL`); none under `GLOBAL` | seed range $[\min_s, \max_s]$ and `ddof=1` seed spread, labelled as such | seed range, no coverage level |
| Phase 2B shot pipeline | multinomial sampling of 8192 shots per circuit, on top of the fixed folding configurations | percentile bootstrap of the shot record (§6.2, §6.3) | decision interval and reported 95% interval |
| Phase 2C | multinomial sampling of 4096 shots per circuit on hardware, plus whatever the device does | percentile bootstrap of the shot record (§6.2, §6.3) | decision interval and reported 95% interval |

No bootstrap is applied where there is no sampling (§3.10). Fold seeds
are a fixed design factor everywhere and are never resampled; their spread
is reported as a seed range or seed spread, never as a confidence interval.

### 6.2 Bootstrap: resampling unit, seeds, replicates

**Resampling unit: the per-circuit shot record.** For each executed
circuit $c$ (one $(n, \text{fold seed}, \lambda)$ triple in a cell) the
record is the vector of counts over the $2^L$ computational-basis
outcomes, together with the **actual** number of shots returned. In the
simulator, given the circuit, its noise model and its `seed_simulator`,
the shots are independent draws from one fixed outcome distribution, so
they are exchangeable within the record; that is why the shot record is
the correct unit there (Efron 1979, §9). **On hardware this is an
assumption, not a property**: the device's noise is observed, no seed
fixes it, and the bootstrap of the hardware shot record is valid only
under the assumption that the 4096 shots of a circuit are exchangeable
draws from one distribution. Variability that assumption omits, and that
the intervals therefore do not contain: drift of the device between and
within circuits, non-stationary or correlated errors across shots, and
calibration changes during the job. The calibration snapshots of §5.3 do
**not** establish the assumption; they only record the device state at
two instants. Every hardware coverage statement in this document is
conditional on this assumption and says so where it is made (§5.11).
Fold seeds, steps, cells and scale factors are design factors, not draws
from a population, and are not resampled.

**Procedure for replicate $b = 1, \dots, B$ of a cell:**

1. Create `rng = numpy.random.default_rng([20260907, phase, cell_index, b])`
   with `phase` $= 2$ for Phase 2B and $3$ for Phase 2C, `cell_index` the
   matrix index (Phase 2C uses `cell_index` $= 0$).
2. For every circuit $c$ of the cell in ascending $(n, \text{seed index}, \text{scale index})$
   order, draw `rng.multinomial(N_shots, p_hat_c)` where `p_hat_c` is the
   empirical outcome distribution of the recorded counts, over the $2^L$
   outcomes in ascending integer order of the Qiskit-ordered count string.
3. From the resampled counts, run the **frozen estimator order** below,
   identical to the order used on the recorded counts, so that every
   replicate repeats the same nonlinear pipeline.
4. Store the replicate statistics; a statistic that cannot be computed
   (failed exponential fit, `NO_INTERIOR_PEAK`, `INTERP_FALLBACK`, or a
   non-finite value) is stored as **undefined** for that replicate, never
   dropped and never substituted.

**Frozen estimator order (recorded counts and every replicate alike).**

1. **Per circuit** $(n, s, j)$: from the counts and actual shots, the raw
   quantities $\langle Z_\pi\rangle/L$, $P_{\mathrm{ret}}$,
   $\langle Z_{i^*}\rangle$, $\langle Z_{i^*+1}\rangle$ and
   $\langle Z_{i^*} Z_{i^*+1}\rangle$, all from the same counts (this is
   where the shared-measurement covariance enters, and it is carried by
   resampling the counts once per replicate).
2. **Per fold seed** $s$: for each raw quantity separately, the `LIN`,
   `QUAD` and `EXP` fits over that seed's $(\lambda_r, \text{value})$
   points, with the rank requirements of the phase (Phase 2B, §4.3:
   `LIN` two, `QUAD` three, `EXP` three distinct realized abscissas,
   amendment A-1; Phase 2C, §5.4: `LIN` two, `QUAD` three, `EXP` two) and
   the design.md §11 clamp rule for `EXP` evaluated per seed. This is the v0.1.0 order: fit each
   fold instance, then aggregate (design.md §8, §11).
3. **Per fold seed**: the connected correlator from that seed's
   extrapolated moments,
   $\mathrm{CZZ}_s = \langle Z_{i^*} Z_{i^*+1}\rangle_s - \langle Z_{i^*}\rangle_s \langle Z_{i^*+1}\rangle_s$
   (§4.4, moment-wise rule).
4. **Aggregation across seeds**, declared: the arithmetic mean over the
   eight (hardware: four or fewer) fold seeds, per extrapolator and per
   quantity, under the design.md §11 homogeneity rule: for `EXP`, if any
   seed at a step is clamp-flagged, all seeds at that step are refitted in
   `avoid_log` mode; if any seed's fit fails or is `FIT_UNAVAILABLE`, the
   step's aggregate for that extrapolator is **undefined** (no partial or
   mixed averages). The unmitigated value is the mean of the $\lambda = 1$
   circuits over seeds (design.md §13).
5. **Peak matching** (§4.6, or §5.9 on hardware) on the aggregated curve,
   then every metric of §4.7.

Because `EXP` and `CZZ` are nonlinear, averaging before fitting would give
different numbers; the checker carries a synthetic fixture on which the
two orders differ and asserts the frozen order (contract §C7).

**Absent or partial records, without survivor averaging.** Every
circuit's record stores its actual shot count; observables use the actual
count. A circuit with no record (absent) or with zero shots makes that
seed's fits at that step `FIT_UNAVAILABLE` for every extrapolator (a
missing scale point changes the design and is not fitted around), and by
step 4 the step's aggregate is undefined and reported as such; the seed
average is never taken over the remaining seeds. A partial record (fewer
shots than requested) is used as recorded, with its actual count, and is
flagged `PARTIAL_SHOTS`.

**Replicate counts.** $B = 2000$ for every exploratory interval and for
Phase 2C; $B_{\mathrm{P}} = 48000$ for the primary Phase 2B family (§6.4).
Peak-level replicates are saved (`bootstrap_peak_replicates.csv`); per-step
replicate quantiles are saved rather than all per-step replicates.

### 6.3 Interval construction: equal-tailed percentile

The interval at coverage $1 - \alpha$ is the pair of empirical quantiles
$(q_{\alpha/2}, q_{1 - \alpha/2})$ of the replicate statistics, computed by
the linear-interpolation quantile: with the $B$ replicate values sorted
ascending as $x_{(1)} \le \dots \le x_{(B)}$ and $h = q\,(B - 1)$ (zero-based
position), the quantile is
$x_{(\lfloor h\rfloor + 1)} + (h - \lfloor h\rfloor)\,\bigl(x_{(\lfloor h\rfloor + 2)} - x_{(\lfloor h\rfloor + 1)}\bigr)$
(NumPy `quantile` with `method="linear"`). Ranks are therefore interpolated,
not exact order statistics: for $B = 2000$ and $q = 0.025$, $h = 49.975$,
between the 50th and 51st order statistics; for $B_{\mathrm{P}} = 48000$ and
$q = \alpha_e/2 = 1.0417 \times 10^{-4}$ (exactly $1/9600$; the rounded
rendering is never used in computation, since it would tolerate five
undefined replicates instead of four), $h = 4.99990$, between the 5th and
6th. $B_{\mathrm{P}}$ was chosen so the primary decision quantile is
interpolated among the lowest order statistics rather than extrapolated
below the first.

**Why percentile (design choice).** It is recomputable exactly from the
saved replicates by the formula above; it needs no variance estimate, no
normal approximation and no jackknife; it stays inside the range of the
replicate values; and it is well defined, as a degenerate interval, when
the replicates are constant. Two properties sometimes claimed for it are
**not** claimed here: the linear-interpolation quantile does not commute
exactly with a nonlinear monotone transform (on $[0, 1]$ the $0.25$
quantile is $0.25$, whose square is $0.0625$, while the same quantile of the
squared values is $0.25$), and staying inside the replicate range is not
staying inside the observable's physical range, because extrapolated
values can be unphysical (see below). The bias-corrected and accelerated
interval (DiCiccio and Efron 1996, §9) was considered and not chosen: its
acceleration requires a jackknife over thousands of shots per circuit
across every circuit of a cell, and its bias correction is undefined when
the replicates are constant, which is exactly the degenerate case §6.7
must handle.

**Physical bounds, without clipping or exclusion.** Raw (unmitigated)
values computed from counts lie within the observable's range by
construction. Extrapolated values need not: a linear zero-scale intercept
of the probabilities $0.9, 0.6, 0.3$ at scales $1, 1.5, 2$ is $1.5$. No
value is ever clipped, replaced or excluded. A plug-in estimate outside
the closed physical range of §4.5 is flagged `UNPHYSICAL_ESTIMATE`; a
replicate outside it is counted, and the count is reported; a decision
or reported interval that extends outside the range is flagged
`UNPHYSICAL_INTERVAL`. **Effect on the primary pass:** `PASS` requires the
decision interval to lie inside the closed tolerance band **and** inside
the closed physical range; an interval flagged `UNPHYSICAL_INTERVAL`
therefore never passes. It is `FAIL` only if disjoint from the band (§6.5)
and otherwise `OVERLAP`. `TIAE`, `ER` and every other metric use the
unclipped values.

**Coverage is approximate and conditional.** Bootstrap intervals have
their nominal coverage only asymptotically and conditionally on the
resampling model; for a discrete statistic such as the matched-peak step
chosen by `argmax`, and for a timing derived from three grid points, the
finite-sample coverage is unknown. Every statement of the form "at the
declared level" in this document is conditional on the nominal coverage
holding, and says so where it is made.

**Undefined replicates, fixed conservative treatment.** Undefined
replicates are not removed and no interval is ever computed from the
surviving replicates alone. Nothing is assumed about where the undefined
values would have fallen, so each interval endpoint is computed under the
assumption least favourable to it: for the **lower** quantile, every
undefined replicate is placed at $-\infty$; for the **upper** quantile,
every undefined replicate is placed at $+\infty$. Interpolation is on the
extended real line without arithmetic on infinities: if either of the two
order statistics entering the linear-interpolation formula is infinite,
the quantile is that infinity. An infinite endpoint makes the interval
`UNDEFINED` and the endpoint status `INDETERMINATE` (§6.7); a finite
interval stands, with the number of undefined replicates reported beside
it. Exact counts: with $u$ undefined replicates the lower quantile is
finite if and only if $u \le \lfloor h\rfloor$ with $h = q\,(B - 1)$, and
symmetrically for the upper; so at most $4$ undefined replicates are
tolerated for the primary decision interval ($B_{\mathrm{P}} = 48000$,
$h = 4.9999$), at most $12$ for the CF-2C decision interval ($B = 2000$,
$q = 0.00625$, $h = 12.49$), and at most $49$ for a reported 95% interval
at $B = 2000$ ($h = 49.975$). The checker exercises these exact allowed
and blocked counts at both the reported and the adjusted levels on
synthetic replicate sets (contract §C7).

### 6.4 Decision intervals and reported intervals

Two intervals are always computed and saved in separate columns:

- the **reported 95% interval** (`ci95_lo`, `ci95_hi`), the same for every
  endpoint everywhere, requested by the task and shown in every chart;
- the **decision interval** (`dec_lo`, `dec_hi`) at coverage
  $1 - \alpha_e$, which alone drives the endpoint status.

The per-endpoint decision level is $\alpha_e = \alpha_{\mathrm{F}} / (4m)$
with $\alpha_{\mathrm{F}} = 0.05$ and $m$ the number of conditions in the
confirmatory family (four endpoints per condition):

| Family | $m$ | $\alpha_e$ | decision coverage | $B$ |
|---|---|---|---|---|
| Phase 2B primary (§4.10) | 60 | $0.05/240 = 2.083 \times 10^{-4}$ | $0.99979$ | 48000 |
| Phase 2C CF-2C (§5.11) | 1 | $0.05/4 = 0.0125$ | $0.9875$ | 2000 |
| every exploratory endpoint | - | $0.05$ (unadjusted) | $0.95$ | 2000 |

For exploratory endpoints the decision interval and the reported interval
coincide; the columns are still both written. A reader who sees a decision
interval sees its level in the column metadata and never a bare "95%".

### 6.5 Endpoint statuses: the three-way rule and what a negative means

Let $[\ell, h]$ be the decision interval and $[a, b]$ the **closed**
tolerance band $[\mathrm{ref} - \tau, \mathrm{ref} + \tau]$.

- `PASS`: $\ell \ge a$ and $h \le b$ (preservation established at the
  declared level; equality at either edge counts as inside).
- `FAIL`: $h < a$ or $\ell > b$ (the interval is disjoint from the closed
  band; non-preservation supported at the declared level).
- `OVERLAP`: otherwise, when the interval is estimable (it contains both
  values inside and outside the band; **unresolved**, neither preservation
  nor non-preservation).
- `INDETERMINATE`: the interval is undefined or degenerate (§6.7).

Non-inclusion is never evidence of non-preservation: only disjointness is.
Condition statuses (§4.8) follow: `PASS` if all four endpoints `PASS`;
`FAIL` if at least one endpoint `FAIL`; `OVERLAP` if none `FAIL`, none
`INDETERMINATE`, at least one `OVERLAP`; `INDETERMINATE` if none `FAIL` and
at least one `INDETERMINATE`; `UNAVAILABLE` from the schedule. A boundary
is **located** only when the next scanned level is `FAIL`; `OVERLAP`,
`INDETERMINATE` and `UNAVAILABLE` leave it unresolved (§4.8).

### 6.6 Multiplicity and the simultaneous statement

**Within a condition.** The four endpoints must all `PASS`. The conjunction
is an intersection-union test: it rejects "not all preserved" only if every
component test rejects, so its size is at most the largest component size
(Berger and Hsu 1996, §9). No adjustment is needed inside a condition, and
the intersection-union test covers **only** that one preselected condition.

**Across the family.** Selection across folding variants, extrapolators,
noise models, levels, sizes, revivals and along the scanned boundary is a
separate family and gets the Bonferroni treatment of §6.4:

- **false pass** (an endpoint declared `PASS` when the true value is
  outside the band): per endpoint at most $\alpha_e$, so per condition at
  most $\alpha_e$ (the conjunction needs every endpoint), and over $m$
  conditions at most $m\,\alpha_e = \alpha_{\mathrm{F}}/4$;
- **false negative** (an endpoint declared `FAIL` when the true value is
  inside the band; this requires the decision interval to miss the true
  value): per endpoint at most $\alpha_e$, over $4m$ endpoints at most
  $4m\,\alpha_e = \alpha_{\mathrm{F}} = 0.05$;
- **simultaneous coverage** of the $4m$ decision intervals, by Boole's
  inequality: at least $1 - 4m\,\alpha_e = 0.95$.

For the Phase 2B primary family ($m = 60$): false-pass bound $0.0125$,
false-negative bound $0.05$, simultaneous coverage of the 240 decision
intervals at least $0.95$. For CF-2C ($m = 1$): false-pass bound $0.0125$,
false-negative bound $0.05$, simultaneous coverage of the four decision
intervals at least $0.95$. All conditional on nominal bootstrap coverage
(§6.3). Exploratory endpoints carry no family-wise statement and say so.

### 6.7 Degeneracy never creates automatic success

Each case gets a flag, the endpoint status `INDETERMINATE`, and a full
report of the raw quantities; none is ever treated as a narrow pass.

| Case | Detection | Flag |
|---|---|---|
| Constant replicates | all $B$ replicate values equal | `DEGENERATE_CONSTANT` |
| Saturated counts | for some circuit of the endpoint's window, all counts in one outcome; or an observable at a bound of its range in every replicate | `DEGENERATE_SATURATED` |
| Collapsed interval | decision-interval half-width below $h_{\min} = 10^{-12}$ | `DEGENERATE_COLLAPSED` |
| Undefined interval | an infinite endpoint under the §6.3 undefined-replicate rule | `UNDEFINED` |
| Undefined statistic | the plug-in statistic itself undefined (`NO_INTERIOR_PEAK`, failed fit, non-finite) | `UNDEFINED` |
| Unphysical interval | decision or reported interval extends outside the closed physical range (§6.3) | `UNPHYSICAL_INTERVAL` (never `PASS`; `FAIL` or `OVERLAP` by §6.5) |

Saturation can be physically genuine (a return probability near 1 at early
steps); it is still reported as degenerate, because an interval of zero
width carries no evidence about its own coverage.

### 6.8 Success passes with uncertainty

Every success criterion in this document references an interval and never
a point estimate alone: Phase 2A, the bound interval of §3.6 inside the
margins; Phase 2B and 2C, the decision interval inside the closed band for
all four endpoints. A point estimate inside a band with an interval that is
not is `OVERLAP` or `FAIL`, never a pass.

### 6.9 Numerical reproducibility tolerances (separate from every scientific threshold)

| Quantity | Value | Role | Not to be confused with |
|---|---|---|---|
| $\eta_E$ | $10^{-9}$ | assumed accuracy budget for density-matrix expectation values, Phase 2A (gate-supported or not, §3.6; always assumed, never proven) and Phase 2B `DM` values | $\tau_{\mathrm{RMS}}$, $\tau_{\max}$, $\tau_A$, $\tau_t$ |
| $\tau_{\mathrm{hist}}$ | $10^{-12}$ | frozen design.md §16 cross-platform standard, used unchanged for the Phase 2A historical cross-check | any Phase 2 budget |
| $\delta$, $\delta_R$ | $10^{-9}$ | denominator resolution for ratios (`IF`, `ER`, `UR`) | any tolerance |
| $h_{\min}$ | $10^{-12}$ | collapsed-interval detection | any tolerance |
| $\epsilon_{\mathrm{ED}}$ | $10^{-10}$ | eigendecomposition residual gate | any tolerance |
| $\epsilon_{\mathrm{deg}}$ | $10^{-9}$ | eigenvalue grouping | any tolerance |
| threshold margin | $10^{-12}$ | marginality flags in selection rules | any tolerance |

**Reproduction contract for Phase 2 outputs, scoped by what is
reproduced.**

1. **Reanalysis of saved observations** (EP-ANALYZE on the saved raw
   counts, density-matrix values, seeds and schedule): deterministic. In
   the same pinned Phase 2 environment every analysis output (metrics,
   statuses, boundaries, bootstrap quantiles and peak replicates) must be
   byte-identical, because the bootstrap seeds are fixed and the estimator
   order is frozen. Across platforms, floating-point reductions may
   differ; the per-quantity rules below apply.
2. **Simulator re-acquisition** (EP-2A, EP-2B rerun): density-matrix
   expectation values to $\eta_E = 10^{-9}$ absolute on any platform; shot
   records byte-identical given `seed_simulator` on the same Aer build
   (design.md §16) and only statistically reproducible across builds.
3. **Hardware re-acquisition**: not reproducible in any sense. A new job
   has new calibration, usage, timestamps and provenance, and no seed
   governs the device. Only the reanalysis of its saved counts (scope 1)
   is reproducible.

**Per-quantity reproducibility rules.** $\eta_E$ is an accuracy budget for
input expectation values, not automatically a tolerance for derived
quantities. Where a propagation formula exists it is used: $r$, $A$ and
$I$ with the bounds of §3.6. Every other derived quantity (fits, peak
steps, timings, ratios, statuses, boundaries) is a deterministic function
of its saved inputs, so reproduction is tested on the inputs (density-
matrix values to $\eta_E$; counts, seeds and schedule byte-identical) and
the derived quantities are recomputed by the same frozen order. A
recomputation from inputs that agree within $\eta_E$ but produces a
different **discrete** result (a different matched step, status, boundary
level or flag) is recorded as `REPRO_AMBIGUOUS` for that quantity, with
both results; it is never resolved by choosing one. Continuous derived
quantities are reported with their difference; no tolerance is claimed
for them beyond the inputs.

**Replaying uncertainty from saved counts and seeds.** Only per-step
bootstrap quantiles are stored, not per-step replicates. Because the
counts, the `seed_simulator` values, the bootstrap seed formula of §6.2
and the estimator order are all saved, every replicate is recomputable:
EP-ANALYZE with `--replay` regenerates all replicates from the saved
counts and seeds and must reproduce the stored quantiles and the stored
peak-level replicates byte-for-byte in the same environment. The
peak-level replicates are stored in full.

The design.md §16 expectation of cross-platform agreement to $10^{-12}$
was tested once and failed (`docs/ci-reproduction-assessment.md`, run
34063462240, 2026-09-06); the tolerance, the recorded failure and the
v0.1.0 claims are unchanged by this document, and no cause is proposed
here. Phase 2 does not rely on $10^{-12}$ for any decision.

### 6.10 Stopping rules

- **Phase 2A** stops when all twelve cells, the 120 statevector runs and the
  480 dense validation runs have completed and the verdicts are written.
  There is no interim analysis.
- **Phase 2B** stops when every `run` cell of §4.11 and every conditional
  control cell that qualified have completed. No cell is added, removed or
  reordered after any result is seen. A cell that raises an error is
  recorded as `CELL_FAILED` with the traceback, the cause is fixed, the
  fix is logged as a deviation (§6.11), and the cell is rerun once with
  identical seeds; a second failure leaves the cell `CELL_FAILED` in every
  table and map.
- **Phase 2C** stops after one job. A job that fails before completion is
  recorded with its actual usage; a second submission requires a new gate
  and must satisfy §5.7(b) with the updated usage (§5.12), which will
  ordinarily prevent it within the window.
- No result may cause any threshold, mask, schedule, scan, matrix cell or
  reference to change. Any such change is a deviation.

### 6.11 Preregistration deviation procedure

1. **Record before continuing.** Every departure from this document,
   however small, is written as an entry in `results/phase2/deviations.md`
   before the analysis proceeds past the point of departure: date
   (UTC), the section and rule departed from, what was done instead, why,
   who decided, and the effect on claims.
2. **Effect on claims, fixed in advance.** A deviation touching a
   confirmatory rule (any threshold, mask, schedule, scan, family
   definition, tolerance, extrapolator or folding choice, or the §5.7
   conditions) changes the status of every claim that depends on it from
   confirmatory to exploratory; the confirmatory claim is reported as
   "not made, deviation D-n". A deviation touching only reporting or
   packaging leaves claim status unchanged and is still recorded.
3. **Late discovery.** A deviation found after analysis is recorded the
   same way, with the discovery date, and the affected claims are
   downgraded retroactively in every report that carries them.
4. **No silent deviation, and no silence mistaken for a record.**
   `results/phase2/deviations.md` must exist and be non-empty in every
   bundle. Its first non-blank line is exactly `DEVIATIONS: NONE` or
   `DEVIATIONS: ENUMERATED`, followed in the second case by the entries of
   item 1. An absent or empty file is missing evidence, not a declaration,
   and is a contract violation (contract §C6). The manifest records which
   declaration the file carries.

---

## 7. Outputs

Every output of Phase 2 is specified in `docs/phase2-analysis-contract.md`
and in `tools/phase2_contract.json`; this section states what must exist
and where the specification lives.

- **Artifacts.** Fifty-one artifacts under `results/phase2/` with
  column-level schemas (contract §C2): raw observations (A-CELLS, A-REF,
  B-REF, B-RAWDM, B-RAWSHOT, C-RAW), chart-input tables (B-MIT, C-MIT),
  processed metrics (A-INT, A-SEC, A-VERD, B-STEPMET, B-PEAKMET,
  B-CURVEMET, B-END, B-COND, B-BOUND, B-DIST, C-END, C-VERD), bootstrap
  samples and deterministic uncertainty artifacts (B-BOOTPEAK, C-BOOTPEAK,
  the interval columns of B-MIT and C-MIT, the bound columns of A-INT), fit
  diagnostics (A-RES, A-DENSE, B-SEEDFIT, C-SEEDFIT, C-IDEAL), circuit and
  transpilation records (A-CIRC, B-FOLD, C-QPY, C-DUR), calibration
  snapshots (C-CALPRE, C-CALPOST, C-BSEL), usage estimate and actual usage
  (C-EST, C-LEDGER, C-LEDGER-RECON, C-RECHECK, C-REDLOG, C-USAGE, C-JOB),
  schedules and selection (B-SCHED, B-CTRL, C-SCHED, B-CELLLOG), and
  manifests and provenance (T-MAN, T-MANGATE, T-PROV, B-ENV, T-DEV).
- **Charts.** Twenty-two chart families (contract §C5), every file in both
  PNG and PDF, 846 files per format when every family cell exists (the
  count is stored per chart in the JSON and summed by the checker); every
  chart of a mitigated observable carries the $E^{\mathrm{ED}}$ series;
  every band legend says exactly what the band is; masks are marker styles,
  never omissions; an unrun family cell is an empty panel with its reason.
- **Traceability.** Every plotted value traces chart → panel → series (with
  its row selector) → file → column → equation → producing command
  (contract §C9); the checker generates the full matrix from the inventory
  and fails if any row does not resolve.
- **Provenance and manifests.** The bundle manifest, the immutable pre-gate
  manifest, the provenance record with the Phase 2 source identity and the
  unchanged v0.1.0 sealed identity, the one environment record, and the
  explicit deviation record (contract §C6).
- **Reproduction.** The one-command reproduction is EP-REPRO (contract
  §C8.2), a future entrypoint specified as a contract; what runs today is
  the offline checker EP-CHECK and its tests EP-TESTS (contract §C8.1).
  Nothing else exists yet, and no document may present a future entrypoint
  as runnable.

---

## 8. Stopping rules and preregistration deviations

The stopping rules are §6.10 and the deviation procedure is §6.11; both
apply to every phase. The rules that a reader is most likely to need are
restated here in one place:

1. No result changes any threshold, mask, schedule, scan, family, matrix
   cell, reference or extrapolator choice. Any such change is a deviation.
2. A deviation to a confirmatory rule turns every dependent claim from
   confirmatory to exploratory, and the confirmatory claim is reported as
   not made.
3. Phase 2C has one submission per gate, and a second gate must again
   satisfy §5.7(b) with the updated usage.
4. Every bundle carries a non-empty `deviations.md` whose first line
   declares `DEVIATIONS: NONE` or `DEVIATIONS: ENUMERATED`.

---

## 9. Sources

All URLs were read read-only on **2026-09-07** unless another date is
given. Statements in this document that go beyond these sources are marked
**(inference)** or **(design choice)** where they occur (§1.4); §9.6 lists
the inferences that carry weight.

### 9.1 Physics

1. I-C. Chen, B. Burdick, Y. Yao, P. P. Orth, T. Iadecola, *Error-Mitigated
   Simulation of Quantum Many-Body Scars on Quantum Computers with
   Pulse-Level Control*, Phys. Rev. Research **4**, 043027 (2022);
   arXiv:2203.08291; DOI 10.1103/PhysRevResearch.4.043027.
   https://arxiv.org/abs/2203.08291 . Used for: the model, the Trotter
   scheme, the observables and the statement that coherent dynamics persist
   "over up to 40 Trotter steps" (abstract), all through design.md §§3-7.
2. design.md §19 items 1-15 (read 2026-08-18 by that document): the
   Mitiq example, Mitiq 1.0.0 sources, Qiskit Aer 0.17.1 API pages for
   `depolarizing_error`, `AerSimulator` and the noise-model API, and the
   `SXGate` inverse. Carried forward unchanged for everything §2.1 reuses.

### 9.2 Qiskit Aer 0.17.1 API (channels introduced in §4.2)

3. `phase_damping_error(param_phase, canonical_kraus=True)`:
   https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.phase_damping_error.html
4. `amplitude_damping_error(param_amp, excited_state_population=0, canonical_kraus=True)`:
   https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.amplitude_damping_error.html
5. `QuantumError.tensor`, `expand`, `compose`:
   https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.QuantumError.html
6. `ReadoutError(probabilities, atol=1e-08)` with
   `probabilities[m] = [P(0|m), P(1|m), ...]`:
   https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.ReadoutError.html
7. `NoiseModel.from_backend(...)`, `add_all_qubit_quantum_error`,
   `add_all_qubit_readout_error`:
   https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.NoiseModel.html
8. `pauli_error(noise_ops)`:
   https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.pauli_error.html
   (read; not used for a primary construction).
9. Aer 0.17.2 device-model construction (`_device_depolarizing_error`,
   `_device_thermal_relaxation_error`, `_combine_depol_and_relax_error`),
   the source of the `CAL` depolarizing-parameter equation and its caps:
   https://github.com/Qiskit/qiskit-aer/blob/0.17.2/qiskit_aer/noise/device/models.py
   (verified read-only by an independent reviewer on 2026-09-07 against the
   installed package; no channel executed).

### 9.3 Mitiq v1.0.0 sources (folding and extrapolation, §4.3, §4.4)

10. `mitiq/zne/scaling/folding.py`: `fold_global(circuit, scale_factor, **kwargs)`
    with `divmod(scale_factor - 1, 2)` and the partial suffix fold of
    `int(round(fraction_scale * len(operations) / 2))` operations;
    `fold_gates_at_random(circuit, scale_factor, seed=None, **kwargs)`;
    "The scale factor must be a real number >= 1":
    https://raw.githubusercontent.com/unitaryfoundation/mitiq/v1.0.0/mitiq/zne/scaling/folding.py
11. `mitiq/zne/inference.py`: `LinearFactory`, `PolyFactory(scale_factors, order, ...)`
    with `order` at most `len(scale_factors) - 1`, `RichardsonFactory` as
    "a particular case of a polynomial fit with order equal to the number
    of data points minus 1", `ExpFactory(scale_factors, asymptote=None, avoid_log=False, ...)`
    with ansatz $y = a + b e^{-cx}$:
    https://raw.githubusercontent.com/unitaryfoundation/mitiq/v1.0.0/mitiq/zne/inference.py

### 9.4 IBM Quantum documentation (every hardware rule of §5)

12. S-IBM-1, `max_execution_time`: "based on *QPU usage* (quantum usage
    only), not wall clock time"; the limit is the smaller of the user value
    and the service maximum of three hours; "On the Open Plan, you can use
    up to 10 minutes on a QPU per 28-day rolling window"; exceeding the
    limit cancels the job with `RuntimeJobMaxTimeoutError`; usage from
    `job.metrics()['usage']['quantum_seconds']`:
    https://quantum.cloud.ibm.com/docs/en/guides/max-execution-time
13. S-IBM-2, estimating run time: the baseline
    `<per sub-job overhead> + (rep_delay + <circuit length>) * <num executions>`,
    "approximately 2s per sub-job", `rep_delay` "Defaults to 250
    microseconds on most IBM backends", executions "total number of
    circuits times the number of shots, where the circuits are those
    generated after PUB elements are broadcasted", the estimate is "an
    approximation", a job "may be divided into multiple sub-jobs if it is
    too large", `init_qubits` adds reset time, actual usage via
    `job.usage()` and REST:
    https://quantum.cloud.ibm.com/docs/en/guides/estimate-job-run-time
14. S-IBM-3, execution modes: "Open Plan users cannot submit session jobs.
    Workloads must be run in job mode or batch mode.":
    https://quantum.cloud.ibm.com/docs/en/guides/run-jobs-session
15. S-IBM-4, batch mode: `max_time` is a time-to-live; "Any jobs that are
    running will finish, but jobs still queued are failed"; Open Plan
    default TTL 10 minutes; no aggregate usage cap stated:
    https://quantum.cloud.ibm.com/docs/guides/run-jobs-batch
16. S-IBM-5, repetition rate and `init_qubits`: the implicit reset
    controlled by `init_qubits`; lowering `rep_delay` "decreases [total QPU
    execution time], at the expense of increasing the state preparation
    error rate"; `backend.rep_delay_range`; "there is no guarantee on the
    order the circuits from PUBs are executed":
    https://quantum.cloud.ibm.com/docs/en/guides/repetition-rate-execution
17. S-IBM-6, backend information: `QiskitRuntimeService.backends()` with
    `simulator=False`, `operational=True`, `min_num_qubits`; `least_busy()`;
    `backend.properties().qubit_property()`; `backend.target` with
    `InstructionProperties` duration and error;
    `backend.properties(datetime=...)`:
    https://quantum.cloud.ibm.com/docs/en/guides/get-qpu-information
18. S-IBM-7, `SamplerExecutionOptionsV2` (qiskit-ibm-runtime 0.49):
    `init_qubits` default True; `rep_delay` default
    `backend.default_rep_delay`, within `backend.rep_delay_range`;
    `meas_type` default "classified":
    https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/options-sampler-execution-options-v2
19. S-IBM-8, `SamplerOptions`: `max_execution_time`, `default_shots`
    (4096 when unset), `dynamical_decoupling`, `twirling`, `execution`,
    `environment`:
    https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/options-sampler-options

### 9.5 Methodology

20. K. Temme, S. Bravyi, J. M. Gambetta, *Error mitigation for short-depth
    quantum circuits*, Phys. Rev. Lett. **119**, 180509 (2017);
    arXiv:1612.02058. Zero-noise extrapolation by "Richardson's deferred
    approach to the limit". https://arxiv.org/abs/1612.02058
21. T. Giurgica-Tiron, Y. Hindy, R. LaRose, A. Mari, W. J. Zeng, *Digital
    zero noise extrapolation for quantum error mitigation*, 2020 IEEE
    International Conference on Quantum Computing and Engineering;
    arXiv:2005.10921. Unitary folding (local and global) and the
    extrapolation methods compared. https://arxiv.org/abs/2005.10921
22. R. L. Berger, J. C. Hsu, *Bioequivalence trials, intersection-union
    tests and equivalence confidence sets*, Statistical Science
    **11**(4), 283-319 (1996). The intersection-union test and the caution
    that size-$\alpha$ tests do not generally correspond to
    $100(1-2\alpha)\%$ confidence sets.
    https://projecteuclid.org/journals/statistical-science/volume-11/issue-4/Bioequivalence-trials-intersection-union-tests-and-equivalence-confidence-sets/10.1214/ss/1032280304.full
23. K. Li, S. Sinks, P. Sun, L. Yang, *On the Confidence Intervals in
    Bioequivalence Studies*, arXiv:2306.06698 (abstract read): a
    size-$\alpha$ two-one-sided-tests procedure corresponds to a
    $100(1-2\alpha)\%$ interval "only when the two one-sided tests in TOST
    are 'equal-tailed'". https://arxiv.org/abs/2306.06698
24. D. J. Schuirmann, *A comparison of the Two One-Sided Tests Procedure and
    the Power Approach for assessing the equivalence of average
    bioavailability*, J. Pharmacokinet. Biopharm. **15**(6), 657-680
    (1987). Bibliographic record only (the publisher page redirected to an
    authorization endpoint and the PubMed page served only a cookie notice
    on 2026-09-07); cited as the origin of TOST, with every substantive
    statement resting on items 22 and 23.
25. B. Efron, *Bootstrap Methods: Another Look at the Jackknife*, Ann.
    Statist. **7**(1), 1-26 (1979): resampling "with replacement from the
    empirical distribution"; the bootstrap bias estimate.
    https://projecteuclid.org/journals/annals-of-statistics/volume-7/issue-1/Bootstrap-Methods-Another-Look-at-the-Jackknife/10.1214/aos/1176344552.full
26. T. J. DiCiccio, B. Efron, *Bootstrap confidence intervals*, Statistical
    Science **11**(3), 189-228 (1996): the survey of BCa, bootstrap-t, ABC
    and calibration against which the percentile construction of §6.3 was
    chosen.
    https://projecteuclid.org/journals/statistical-science/volume-11/issue-3/Bootstrap-confidence-intervals/10.1214/ss/1032280214.full

### 9.6 Inferences that carry weight (none is a citation)

- The material discrepancy factors $f_{\max} = 1.10$ and
  $f_{\mathrm{RMS}} = 1.05$ (§3.5); the numerical budget $\eta_E = 10^{-9}$
  (§3.6); the tolerances $\tau_A$, $\tau_t$, the window $w = 4$, the
  separation $d_{\min} = 5$ and the 48-step window (§4.1, §4.6, §4.8); the
  control-selection constants (§4.9); the family and level choices of
  §4.10 and §6.4 - all design choices.
- The one-sub-job-per-circuit split assumption behind
  $T_{\mathrm{est}}^{\mathrm{cons}}$ and the multiplier $M = 1.2$ (§5.8);
  the illustrative gate durations of §5.8; the 24-hour snapshot age
  (§5.12).
- The parameter convention equating dephasing and amplitude-damping
  parameters to depolarizing probabilities (§4.2); the expectation that a
  central site or bond is least affected by the open boundary (§4.5); the
  wall-clock order of magnitude (§4.11); the polarized state's energy
  coincidence at $L = 6$ (§4.9); the expectation that the linear primary
  fails the amplitude tolerance at $\kappa = 1$ (§4.1).
- Everything read from the recorded v0.1.0 bundle is marked
  **(recorded, v0.1.0)** and is a fact about that bundle, not an inference.
