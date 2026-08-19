# v0.1.0 Release Notes — DRAFT

> **DRAFT ONLY. No tag, release, or archive exists. This document is a proposal
> for the release owner; publishing it, and the release itself, require
> explicit human authorization.**

## What this is

The first sealed version of **zne-many-body-scars**: a local, simulation-only,
fully pre-registered measurement of whether zero-noise extrapolation (ZNE)
reduces the error of a quantum many-body-scar observable, in the mixed-field
Ising model (MFIM) at L = 6, under a fully specified depolarizing noise model
in a classical simulator. One canonical execution per the pre-registered
design. **Every scientific result number below is traceable to the frozen
recorded bundle** (`results/minimal/metrics.json`, `steps.csv`, or the
recomputation conventions stated in docs/results-minimal.md, with the source
quoted at each use). Operational numbers — the test count and the run time —
are dated observations of the development environment, deliberately NOT part
of the frozen bundle (design.md §16 excludes timing from the recorded outputs
precisely so byte-reproducibility never depends on wall clock); their evidence
basis is design.md §20 Phase A and docs/ci-reproduction-assessment.md, and
they are labeled where they appear.

**Contents of the artifact:**

- `docs/design.md` — the pre-registered design (20 sections) with its complete
  review history, including every rejected intermediate state.
- `results/minimal/` — the canonical recorded experiment: six deterministic
  files (`environment.json`, `metrics.json`, `steps.csv`, `seed_arms.csv`,
  `folded_circuits.csv`, `shot_values.csv`).
- `docs/results-minimal.md` — the findings, traceable to those files.
- `src/zne_scars/`, `scripts/` — all physics/statistics modules and the two
  orchestration scripts, content-hashed into
  `environment.json[source_tree_sha256]` and sealed in
  `tools/release_identity.json`.
- `tools/verify_reproduction.py` — the tested verifier a reproducer runs.
- `figures/` — one two-panel figure in two file formats (PNG and PDF),
  generated exclusively from the recorded CSV.
- `tests/` — the test suite (116 tests at sealing — an operational count, see
  above), including the pre-registered T1–T6 properties and the
  canonical-directory guards.
- `docs/reproduction-protocol.md` — cold-start reproduction instructions.

## Primary result — with its qualifications, which are part of the result

**The pre-registered verdict passes** (source: `results/minimal/metrics.json`):
RMS error over all 40 Trotter steps falls from 0.32079729685433694 (unmitigated)
to 0.25106736243976785 (ZNE primary), a global improvement factor
GIF = 1.2777339664421639, with per-step improvement IF > 1 on 39 of 39
reportable steps. The independently seeded 8192-shot pipeline gives
GIF = 1.2774206732205877 with the same 39/39 pattern (`metrics.json`,
`shot_pipeline`).

That sentence is incomplete without the following four qualifications:

1. **The improvement is strongly regime-dependent.** Per-step IF peaks at
   20.17 at n = 4 and decays to 1.107 by n = 40
   (`results/minimal/steps.csv`, `if_value` column). At late steps both errors
   saturate toward |E₀(n)| and the pre-registered metrics cannot distinguish
   ZNE failure from the absence of remaining signal — no claim is made there in
   either direction (design.md §13).
2. **Much of the metric's reward is amplitude restoration, not extrapolation.**
   A post-hoc *oracle* constant rescale — fitted against the exact answer,
   which no real experiment has — captures ≈ 68% of the primary's RMS
   reduction (oracle GIF 1.1739 vs primary 1.2777), and a two-parameter
   exponential oracle outperforms even the pre-registered secondary
   (docs/results-minimal.md §9, recomputable from `steps.csv` with the
   conventions stated there). ZNE still beats the constant-rescale oracle
   using only noisy data — but the per-step win count overstates what genuine
   extrapolation contributes.
3. **ZNE increased the error at exactly one step, and that step is excluded.**
   At n = 34 the unmitigated error was already negligible
   (ε_u = 0.0024 < ε_min = 0.01) and the primary landed at ε_m = 0.0166
   (IF = 0.145, `steps.csv` row n = 34). The step is excluded from the majority
   test by the **pre-registered** ε_min relevance filter — the filter was not
   adjusted after seeing results, and the step appears in every table and
   figure.
4. **The pre-registered ExpFactory(asymptote = 0) secondary outperforms the
   linear primary by ≈ 3.4× in RMS** (0.07349 vs 0.25107, computed from
   `steps.csv`; ratio 3.416). This is a statement about estimator fit on
   **this simulated noise model and these data only** — three scale factors
   cannot establish the true functional form or asymptote, the linear primary
   remains the pre-registered verdict, and nothing here predicts hardware
   behavior.

Two discrepancies from the design's own heuristics were **preserved, not tuned
away** (docs/results-minimal.md §8): the observed noise decay is ≈ 2× slower
than the §11 global-depolarizing heuristic (consistent with channel locality;
the single-qubit contribution is explicitly unresolved — a p₂ = 0 control is
outlined, unexecuted, in `docs/prereg-p2zero-outline.md`), and the
secondary-vs-primary ordering above.

## Scope — simulation only

Everything binds to: L = 6, the observable ⟨Z_π⟩/L, gate-attached two-tier
depolarizing noise (p₁ = 10⁻³, p₂ = 10⁻²), two-qubit-restricted seeded random
folding, scale factors {1.0, 1.5, 2.0}, fold seeds 1000–1007, and this pinned
software environment. **No statement transfers to hardware** — no device,
pulse, coherent-error, crosstalk, readout, or decoherence effects are modeled
(design.md §14(d), §18). This artifact makes no novelty claim; it is a
controlled, exactly-referenced measurement with its analysis pre-registered.

## Reproducing

See README §4 for the commands and `docs/reproduction-protocol.md` for the
full cold-start protocol, including exactly what to expect per platform and
how to distinguish a genuine discrepancy from an expected environment
difference. Verification is one command:
`python tools/verify_reproduction.py`. A full run takes ≈ 250 s wall clock on
the reference machine (Apple-silicon laptop; an operational number — measured
2026-08-18, recorded in design.md §20 A2-4, not part of the frozen bundle).

## Provenance

The sealed source identity of this release is
`environment.json[source_tree_sha256]`-compatible hash
`ab751d691a4cc3fc623b6044ef70dead0b54df46c0f33f880e574f7a828d6ca2`
(`tools/release_identity.json`) — a content hash over the **experiment
source** (`src/**/*.py`, `scripts/*.py`, `pyproject.toml`,
`requirements.txt`); the rest of the repository (verifier, tests, docs,
workflows) is covered by the release tag's commit identity, not by this hash. The canonical bundle records the hash of the
exact source that produced it (`7161d655…`). The difference between the two
consists, completely, of: (i) canonical-overwrite guards added to the run
scripts, including the new shared module `scripts/_canonical_guard.py`;
(ii) the corrected `source_identifier_note` wording those scripts emit; and
(iii) `license` metadata added to `pyproject.toml` — the full change-by-change
history, including every review-rejected intermediate state, is design.md §20
Phase A rows A2-1 through A2-6 (the hashed source last changed at A2-4;
A2-5/A2-6 record verifier corrections in unhashed `tools/`). No physical, statistical, or numerical
definition changed, verified by the byte identity of all five data files
across re-executions.

## References

Primary: I-C. Chen, B. Burdick, Y. Yao, P. P. Orth, T. Iadecola,
*Error-Mitigated Simulation of Quantum Many-Body Scars on Quantum Computers
with Pulse-Level Control*, Phys. Rev. Research **4**, 043027 (2022),
arXiv:2203.08291. Full verified reference list: design.md §19.
