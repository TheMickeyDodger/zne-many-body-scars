# Preregistration OUTLINE (draft): p₂ = 0 Single-Qubit Attenuation Control

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
> **Supersession, 2026-09-07.** The Phase 2 preregistration
> `docs/prereg-phase2.md` (with `docs/phase2-analysis-contract.md` and
> `tools/phase2_contract.json`) now governs the experiment this outline
> sketched. Phase 2 remains **unexecuted**: no code, data or result exists
> for the $p_2 = 0$ arm or for any other Phase 2 cell.
>
> Superseded by that preregistration:
>
> - the provisional hypothesis intervals H-G and H-L of §2 (no H-G / H-L
>   verdict is issued; the single-rate slope is a secondary quantity);
> - the residual tolerance that §4 left unfixed (now $\tau_{\mathrm{res}} = 0.05$
>   for the secondary fit only);
> - the pointwise adequacy gate $r > 1 + 10^{-9}$ of §4 (replaced by a
>   budget-based gate for the secondary fit; the $-10^{-9}$ anti-attenuation
>   and zero-treatment rules of §§2 and 4 are retained unchanged);
> - the undefined additivity criterion $\tau_{\mathrm{add}}$ of §5
>   (replaced by a curve-level equivalence assessment on the interaction
>   $I(n)$ with declared material margins, fixed before any data).
>
> The new design reruns all four factorial cells $(0,0)$, $(10^{-3},0)$,
> $(0,10^{-2})$, $(10^{-3},10^{-2})$ prospectively under one implementation
> and environment, at $L \in \{4, 6, 8\}$; the v0.1.0 combined arm is used
> only as a historical cross-check at $L = 6$, never as a factorial cell.
> The mask $\lvert E_0(n)\rvert \ge 0.1$ of §4 is adopted unchanged.
>
> Remaining historical record, not superseded: the framing of the question
> in §1, the licensing table and the freeze-ordering argument of §5, and the
> execution requirements of §6. The original outline and its 2026-09-06
> update follow unchanged.

> **Update, 2026-09-06.** The original banner says that this outline was not
> published. It is now included in the v0.1.0 GitHub release and Zenodo record
> 22005535. See `docs/release-notes-v0.1.0.md` for release details.
>
> Work on this experiment has not started. The repository contains no code
> or data for a p₂ = 0 arm, and this outline has not been approved as a
> preregistration. The hypothesis intervals in §2 and the residual tolerance
> in §4 have not been finalized. The 10⁻⁹ tolerances are policy choices, not
> calculated error bounds.
>
> `docs/followup-study-draft.md` uses this outline as a reference but does not
> finalize any of those choices. The original outline follows unchanged.

> **STATUS: DRAFT OUTLINE FOR FUTURE WORK - NOT AN APPROVED PREREGISTRATION,
> NOT EXECUTED, AND NOT PART OF THE v0.1.0 EVIDENCE BASE.** As a draft
> artifact, this outline WAS adversarially reviewed (Phase A M2, review rounds
> 05-08: three rejections and an approval, which materially changed its mask,
> adequacy gate, tolerance framing, hypothesis intervals, and additivity
> clause - transcripts in the project's review records). That is document
> review, not approval to execute: no code for this experiment exists in this
> repository, and before execution this outline would need to be expanded into
> a full preregistration (in the style of docs/design.md) and frozen, with its
> own review history. It is included in the repository only so the open
> question it addresses is stated precisely - nothing about it is published,
> and nothing will be without explicit human authorization.

## 1. The question it isolates (why this experiment)

The v0.1.0 run preserved a discrepancy (docs/results-minimal.md §8;
design.md §11, §20): the observed total attenuation of ⟨Z_π⟩/L is ≈ 2× slower
than the global-depolarizing heuristic
E(λ) ≈ E₀·e^-(Γ₂λ + Γ₁), Γ_k = N_k·γ_k, γ_k = -ln(1-p_k) (design.md §11) -
per step, exponent ≈ 10γ₂ + ~12γ₁ ≈ 0.113 predicted vs ≈ 0.050-0.056 observed.
The recorded data measure only the *total*; the single-qubit contribution
(the Γ₁ "floor" of §11's λ_eff algebra, design.md §10) is explicitly
unresolved. Setting **p₂ = 0** removes the two-qubit channel entirely, so the
measured attenuation is the single-qubit exposure's contraction of Z_π alone.

## 2. Hypotheses - stated so they can fail

Let g₁ be the fitted per-step attenuation rate (defined in §4) under
p₁ = 10⁻³, p₂ = 0, and let g₁^heur = ~12γ₁ ≈ 0.012 per step be the §11
global-exposure prediction (the exact N₁(n)/n gate count to be taken from the
transpiled circuits, as recorded in `folded_circuits.csv` conventions).

- **H-G (global-exposure):** 0.75·g₁^heur ≤ g₁ ≤ 1.25·g₁^heur (both endpoints
  included) - the single-qubit channels contract Z_π at approximately the
  global-exposure rate.
- **H-L (locality suppression):** 0 ≤ g₁ < 0.50·g₁^heur - local single-qubit
  channels contract this sum of single-site observables materially slower than
  global exposure (down to and including no measurable contraction), mirroring
  the direction observed for the total in §8. **H-L is bounded below by
  zero**: a fitted g₁ in [-10⁻⁹, 0) is treated as 0 (the same frozen policy
  tolerance as the adequacy gate, same caveats), and a fitted
  **g₁ < -10⁻⁹ is NOT H-L** - attenuation *increasing* signal with depth is a
  qualitatively different phenomenon, handled by the fit-level verdict in §4.
- **Neither:** 0.50·g₁^heur ≤ g₁ < 0.75·g₁^heur, or g₁ > 1.25·g₁^heur - the
  heuristic's single-qubit arithmetic is wrong in a way this design alone does
  not explain; report as such.

The interval boundaries above are provisional for this outline and must be
frozen (with justification) in the full preregistration before any data are
seen.

## 3. Fixed parameters (identical to design.md §15 except the one control)

L = 6, V = 1, Ω = 0.24, Δt = 1, n = 1…40; |Z₂⟩ initial state; observable
⟨Z_π⟩/L; basis {rz, sx, x, cx}, `optimization_level=0`, `seed_transpiler=7`;
noise **p₁ = 10⁻³ on sx/sxdg/x (unchanged), p₂ = 0 on cx (the control),
rz clean**; exact density-matrix pipeline only (zero sampling variance). No
shot pipeline and no ZNE arms are required for the primary metric; if ZNE arms
are run as secondary diagnostics, the Γ₂ = 0 λ_eff convention of design.md §20
M2-6 applies and must be cited. No other parameter may move; any deviation
disqualifies the run from answering §1.

## 4. Primary metric and analysis plan (to be frozen before execution)

- Compute r(n) = E_noisy(n)/E₀(n) per step from the recorded outputs (same
  bundle format as §16).
- **Pre-specified mask, computed from pre-result quantities ONLY:** include
  step n iff |E₀(n)| ≥ 0.1 - excluding oscillation nodes where the ratio is
  ill-conditioned. E₀ is the noiseless Trotter reference: it is
  noise-independent and computable before any noisy execution, so the mask is
  fixed before the outcome exists. **No outcome-dependent quantity - r(n)
  included - may enter the mask under any circumstances**; the full masked and
  unmasked step lists are reported.
- **Pre-declared model-adequacy gate (evaluated on masked steps, before any
  fit), symmetric on both sides of the model's prediction:** the attenuation
  model under test predicts 0 < r(n) ≤ 1 on every masked step, and a violation
  on either side triggers the same deterministic verdict. If ANY masked step
  has **r(n) ≤ 0** (a sign flip) **or r(n) > 1 + 10⁻⁹**, the pre-declared
  verdict is **"model inadequate"**: every violating step is reported in full,
  no fit is performed, and no H-G/H-L verdict is issued. The 10⁻⁹ upper
  tolerance is a **frozen policy choice, not a derived error bound**: it is
  fixed here, in advance, solely so the gate is deterministic. No claim is
  made that 10⁻⁹ cannot mask a real excursion - only that, by this
  pre-declared policy, an excursion smaller than it will be treated as
  numerical rather than physical. Deriving a validated numerical-error bound
  for r(n) (solver error propagated through the ratio under the |E₀| ≥ 0.1
  mask) is exactly the kind of work this outline defers: the full
  preregistration may replace the policy value with a derived bound, but only
  before any execution. Violating steps are never excluded, in the mask or
  anywhere else, and no branch of this gate is left to a criterion chosen
  after data exist.
- **Primary metric** (computed only if the adequacy gate passes): g₁ = -slope
  of the OLS fit of ln r(n) against n over the masked steps, reported with its
  residuals. Non-linearity of ln r(n) beyond a residual tolerance likewise
  yields "model inadequate" rather than a forced verdict - but that tolerance
  is NOT fixed by this outline: **on this branch the outline is explicitly not
  yet a freezable analysis plan.** The full preregistration must freeze the
  residual tolerance before any execution (§6); until it does, no run under
  this outline can produce a valid H-G/H-L verdict at all.
- **Fit-level anti-attenuation verdict (deterministic, mirroring the
  pointwise gate):** a fitted g₁ < -10⁻⁹ - a clean linear *increase* of
  ln r(n) with depth, which the pointwise gate cannot catch since every r(n)
  can remain inside (0, 1] - yields the pre-declared verdict **"model
  inadequate - anti-attenuation"**, a distinct reportable outcome: the fitted
  rate and per-step r(n) are reported in full, and no H-G/H-L verdict is
  issued. The -10⁻⁹ threshold is the same frozen policy tolerance as the
  adequacy gate, with the same caveats.
- Verdict (only if neither inadequacy verdict fired): evaluate H-G / H-L /
  neither per §2's frozen intervals.

## 5. What each outcome would and would not license

A single-arm p₂ = 0 run measures the **isolated** single-qubit response and
nothing else. Design §11 itself notes that interleaved local channels do not
generally factor into independent scalar contractions, so no outcome of this
control alone can apportion the *combined*-noise (p₁ + p₂) attenuation gap of
§8 between the two channel tiers. Claims are licensed accordingly:

| Outcome | Licenses (isolated-channel statements only) | Does NOT license |
|---|---|---|
| H-G holds | "In isolation, the single-qubit exposure contracts Z_π at ≈ the global-exposure rate"; using the measured g₁ as the single-qubit input to §11's λ_eff algebra *for the isolated channel*. | Attributing any share of the §8 combined-noise gap to either channel (requires the additivity test below); any change to the v0.1.0 verdict, metrics, or qualifications; any claim about the true λ-response form or asymptote. |
| H-L holds | "In isolation, local single-qubit channels contract this observable materially slower than global exposure" - resolving §11's Γ₁ arithmetic for the isolated channel. | Same exclusions - including NOT the claim that locality explains the combined gap, and NOT a strengthening of the v0.1.0 ZNE result, whose verdict never depended on the heuristic's rate. |
| Neither / model inadequate | Reporting the §11 heuristic as quantitatively unreliable for this system beyond its already-documented qualitative role. | Same exclusions. |

**Pre-declared factorial extension required for any apportionment claim.**
Decomposing the combined gap needs the full 2×2 comparison over (p₁, p₂) arms:
(0, 0) - the noiseless reference, already recorded in the canonical bundle as
the per-step E₀ (`steps.csv`, `e0_trotter`), which every r(n) is defined
against; (10⁻³, 0) - this control; (0, 10⁻²) - a second, separate control;
and (10⁻³, 10⁻²) - the recorded v0.1.0 canonical noisy run. The additivity
test is whether the combined fitted rate satisfies g₁₂ ≈ g₁ + g₂ within a
numerical criterion that must be frozen **before either new arm runs - that
is, before this p₂ = 0 control itself executes**, since a criterion chosen
after observing g₁ could be selected to make the additivity verdict come out
either way. If this control is executed before such a criterion is frozen,
its result is thereby disqualified from any later *preregistered* factorial
inference - a factorial analysis using it would be explicitly post hoc and
must be labeled as such. Only if additivity holds under the frozen criterion
may the combined gap be decomposed into per-channel shares; a failed
additivity test is itself a reportable interaction finding, not a license to
apportion by subtraction. Neither the second control nor the additivity
criterion is part of this outline's scope - they are named here so the
limitation and the freeze-ordering are pre-declared rather than discovered.

**No outcome retroactively strengthens or weakens the v0.1.0 result.** The
v0.1.0 verdict is defined by its pre-registered §13 metrics on recorded data;
this control resolves only the §11 diagnostic arithmetic that v0.1.0 already
flags as unresolved - and, per the table, only for the isolated channel. That
is stated here, in advance, precisely so it cannot be reframed later.

## 6. Execution requirements (when and if this proceeds)

Expand to a full preregistration reusing design.md's conventions (§13 metric
definitions, §16 determinism plan, seed schedule, bundle format) with explicit
citations; freeze it with a review history before the first run; write outputs
to a fresh `results/` subdirectory - never `results/minimal/` - and record the
then-current source identity. Runtime should be comparable to the v0.1.0
minimal experiment (≈ 250 s reference wall clock) or less without the shot
pipeline and folding arms.
