# Review Package — for the human owner

> **[2026-08-18, Phase A annotation — read first.]** This is the historical
> decision artifact for the FIRST commit of this repository. It is retained
> unedited (below this note) as part of the review history, and it records the
> work-tree state as of that decision. The state has since moved: the commit it
> requested was authorized and made (`0c6e986`), the `results/minimal-repro/`
> directory it inventories no longer exists in the tree (leaving it uncommitted
> and disposable was this document's own §5 recommendation), and Phase A
> subsequently hardened the run scripts' IO paths
> and added the release documentation — complete change history in
> `docs/design.md` §20 (Phase A rows). Present-tense statements below are
> present-tense relative to that first-commit decision, not to the current tree.

**Purpose:** everything needed to decide whether to authorise a **first commit** of this repository. At the time this package was prepared, no commit had been made (granting the approval this document requests is exactly what changes that); the document requests that decision and nothing more (§7). Every claim here traces to an artifact already in the work tree as of this package.

## 1. Work-tree inventory

*(Snapshot as of the M4 review package; the work tree itself is the live source for anything added later.)*

| Path | Purpose |
|---|---|
| `.gitignore` | excludes `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `*.egg-info/` |
| `pyproject.toml` | packaging (src layout, editable install) + pytest configuration |
| `requirements.txt` | fully pinned lockfile (`pip freeze --exclude-editable`) from the environment that ran everything |
| `README.md` | question, answer-with-qualifications, provenance, reproduction, limitations |
| `docs/design.md` | the pre-registered design (M1), 20 sections; §20 is the complete revision log across all milestones |
| `docs/results-minimal.md` | findings of the minimal experiment, every number traceable to `results/minimal/` |
| `docs/review-package.md` | this document |
| `docs/mutation-evidence.md` | mechanically generated mutation-sensitivity evidence for 13 defects (edit → failing output → revert proof) |
| `src/zne_scars/__init__.py` | package marker (side-effect-free) |
| `src/zne_scars/hamiltonian.py` | MFIM Hamiltonian (design §3), exact continuous-time reference (§12.2) |
| `src/zne_scars/trotter.py` | first-order Trotter circuits, Paper Fig. 1 angles, basis/transpilation (§6–7) |
| `src/zne_scars/observables.py` | $Z_\pi$ operator and the single audited count-string decoder (§4–5) |
| `src/zne_scars/noise.py` | `NoiseConfig` (single source of truth for rates) + two-tier depolarizing model (§8) |
| `src/zne_scars/executors.py` | density-matrix / statevector / seeded-shot executors; noise-declaration tagging (§8, §12, §16) |
| `src/zne_scars/zne_runner.py` | seeded fidelity-restricted folding, three regression arms, §11 secondary policy (§9–11) |
| `src/zne_scars/metrics.py` | §13 metrics: filters, δ rules, RMS/GIF, majority, verdict, ddof=1 bands |
| `tests/test_hamiltonian.py` | T1: hermiticity + exact boundary/bulk/ZZ/X coefficients by Pauli-trace |
| `tests/test_trotter.py` | T2: exact factorization, dt² convergence, ordering probes |
| `tests/test_observables.py` | T3: Néel extremal values, estimator agreement |
| `tests/test_zne.py` | T4–T6 + arms, granularity grid, seed threading, declaration rules, secondary policy |
| `tests/test_metrics.py` | §13 guarantees incl. denominator rules and edge cases |
| `scripts/run_minimal.py` | executes design §15 exactly; orchestration only |
| `scripts/make_figures.py` | regenerates figures from a recorded results directory (`--results`, default `results/minimal/`); no simulation |
| `results/minimal/` | the recorded experiment: `environment.json`, `metrics.json`, `steps.csv`, `seed_arms.csv`, `folded_circuits.csv`, `shot_values.csv` |
| `results/minimal-repro/` | independent second run; byte-identical to `results/minimal/` (determinism evidence) |
| `figures/minimal_experiment.{png,pdf}` | the §15 two-panel figure, generated from recorded data |
| `src/zne_scars.egg-info/` | build artifact of the editable install; gitignored |
| `.venv/` | project virtualenv (Python 3.12.14); gitignored |

## 2. Evidence summary

- **Tests:** 52 passing as of the M4 package (`.venv/bin/python -m pytest -q` is the live source), including the six pre-registered T1–T6 properties. **Mutation evidence exists for 13 specific defects, not for all 52 tests — and it is checkable in this repository:** [`docs/mutation-evidence.md`](mutation-evidence.md) was generated mechanically (apply mutation → run named test → capture real failing output verbatim → revert), lists each of the 13 mutations with its exact edit, target test, and captured assertion output, states its count from its own entries, and ends with the revert proof (marker grep + full green suite). Tests outside those 13 (e.g. the declaration-rule and length-guard tests, which assert exceptions directly) have not been mutation-verified.
- **Determinism:** proven, not asserted. The experiment was run twice by the implementer into separate directories, and once more by the Lead independently from a clean state; **all six recorded files are sha256-identical across all three runs**. Recorded outputs contain no timestamps or absolute paths.
- **Figures:** proven to derive from recorded data — `figures/` was deleted and regenerated by `make_figures.py` alone, with no simulation executed.
- **Provenance:** `results/minimal/environment.json` records the complete pip freeze, Python/platform/BLAS, all parameters and seeds, and a source-tree sha256 (a content hash over `src/`, `scripts/`, `pyproject.toml`, `requirements.txt` — not a VCS revision, because at the time of the recorded run no commit existed; the hash remains valid regardless of later VCS history).

## 3. Review history — the real record

**Through round 20 — the end of M3, the cutoff for every count in this section: 15 REJECT, 5 APPROVE** (full transcripts under `.herd/state/reviews/`). M4 rounds are deliberately **not** included: reviewing this document itself adds rounds, so any unqualified count would be stale the moment it was reviewed — a reader who counts the directory today will get a larger number, and that is expected, not an error; the directory is the live source. (An earlier draft stated 16/4 for the same cutoff — that miscount is itself item 4 of the accountability list below.) Summary of MAJOR-and-above findings and their resolutions:

- **M1 (design):** three BLOCKERs — a "noise scaling holds by construction" overclaim (fixed by the fidelity-restricted folding policy with realized-scale recording), an out-of-context quotation of the Paper's QPT gate benchmark as support for the many-body linear fit (re-attributed with both assumptions), and a provenance-table overclaim ("exact quantification" → empirical measurement). Majors included the sx→sxdg inverse-instruction leakage (noise model extended + test T6), the wrong-estimator bias derivation (replaced by the three-point OLS with the 25/24 coefficient), site-ordering ambiguity (dual ket notation), and metric edge-case rules. Later M1 rounds corrected the heuristic to carry λ only on the folded term, discovered the λ_eff identity that makes the floor abscissa-dependent, and scoped every "unremovable floor" claim.
- **M2 (implementation):** the three pre-registered arms and the §11 secondary policy were initially missing as module logic (implemented with tests); a metrics function violated §13's own no-non-finite guarantee (fixed, tested); T6's tolerance would have accepted broken folding (replaced by exact grid-derived counts); seed threading was untested (structural tests added); two successive holes in the λ_eff/noise-declaration rule were closed (undeclared executors now raise; contradictory declarations now raise) and one degenerate crash (p₁=p₂=0) was defined away deliberately.
- **M3 (experiment):** the shot pipeline was initially a fragment (extended to the full §13 metric set with its own alongside-verdict); a genuine defect surfaced during regeneration — mitiq's avoid_log fit can fail to converge on near-zero shot data — and was handled by a flag-and-never-substitute policy (design §20 M3-3); provenance was completed (full freeze + source hash); oracle counterfactuals were added as labeled post-hoc diagnostics; several overclaims in the results note were narrowed to what the data support.
- **Stated without softening: five corrections originated from the Lead's own erroneous statements** (transcripts under `.herd/state/reviews/`, incl. `*round-12.md` for item 2, `*round-20.md` for item 3, `*round-23.md` for item 5; the list was compiled by mechanically searching every review transcript for Lead admissions, after recollection twice produced an undercount):
  1. M1 §18(2): "every estimator's variance and conditioning degrade without bound" — false for the fixed-abscissa OLS and the zero-variance density-matrix pipeline.
  2. M1 §18(2): the noiseless reference $E_0$ "collapses toward zero" and "absolute errors stay bounded and small" — both false; $E_0$ is noise-independent and the errors *saturate* toward $|E_0|$.
  3. M3 §9: the one-parameter oracle marks "where a non-cheating estimator must sit" — a bound that does not exist; a two-parameter oracle beats the secondary, and the claim was withdrawn in the results note.
  4. M4: this document's review count first stated as 16 REJECT / 4 APPROVE; the recorded count through round 20 (the same end-of-M3 cutoff as above) is 15 / 5. The Lead's subsequent correction quoted a "current" total that was itself already stale when written — any unqualified round count inside a document under review invalidates itself; the cutoff is the fix.
  5. M4: offered "label the timings as unrecorded observations" as an acceptable option, when the brief required every README number to trace to a results artifact; the labeling was insufficient and the figures were ultimately removed.

  Each correction is recorded in the affected document. A review record that under-reports who was wrong looks like accountability while providing less of it — and this list itself was undercounted twice (four stated where five were recorded), which is why it is now compiled mechanically from the transcripts rather than from memory.

## 4. Claims made / claims NOT made

**Made (each traceable):** the pre-registered verdict passes (GIF 1.2777, RMS 0.32080 → 0.25107, 39/39 reportable steps, m=39; `metrics.json`); improvement is regime-dependent (IF 20.17 at n=4 → 1.107 at n=40; `steps.csv`); ≈68% of the primary's RMS reduction is available to an answer-fitted constant oracle, which ZNE nonetheless beats (results note §9); the pre-registered secondary outperforms the primary 3.4× in RMS on these data (0.07349 vs 0.25107; `steps.csv`); observed decay is ≈2× slower than the design heuristic, consistent with channel locality but mechanism not isolated (results note §8); determinism as in §2 above.

**NOT made (design §14(d) governs):** nothing about real hardware, pulse control, coherent/readout/crosstalk/T₁T₂ noise, or drift; nothing beyond L=6, this observable, this channel, these rates, this folding policy, these scale factors, this seed ensemble; no claim about the true functional form of the noise response or its asymptote; no transferability of the secondary's advantage; at late steps, no claim that ZNE works or fails (metrics cannot distinguish there, design §13).

## 5. Proposed first commit

**Stage exactly:**

```
.gitignore  pyproject.toml  requirements.txt  README.md
docs/design.md  docs/results-minimal.md  docs/review-package.md  docs/mutation-evidence.md
src/zne_scars/  (8 files)     tests/  (5 files)     scripts/  (2 files)
results/minimal/  (6 files)   figures/minimal_experiment.png  figures/minimal_experiment.pdf
```

**Recommendation: include `results/minimal/` and `figures/` — exclude `results/minimal-repro/`.**

- *For inclusion of results and figures:* this is an inspectable research artifact; a reader should be able to check the experimental numbers in the README and results note against the recorded data without executing anything (citation-class facts check against design §19 instead). The full results directory is ~small (six text files), the figures ~340 KB. Determinism cuts both ways, but reproducibility-in-principle is not the same as inspectability-in-hand.
- *Against (considered honestly):* generated data in VCS is often noise. Here it is the evidence base for the experiment's published findings, which outweighs the convention; anyone can regenerate and diff.
- *`results/minimal-repro/` specifically:* **exclude.** It was **verified byte-identical** to `results/minimal/` (empirically — the identity is evidence, not a guarantee) and exists only as determinism evidence; committing an identical copy adds no information (the identity is recorded here and in the review transcripts). Recommend leaving it untracked in the work tree until the owner has verified the hashes, then deleting it at their discretion.
- `.gitignore` already excludes `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `*.egg-info/` — keeping the virtualenv and the known build/cache artifacts out of any staging operation.

## 6. Residual risks carried forward

1. The λ_eff/declaration check is only as strong as the declaration: a custom executor tagged with rates it does not actually simulate defeats it (a closure's true noise is not introspectable). Module-built executors have no such gap.
2. The Γ₁ single-qubit floor magnitude is unresolved; a p₂ = 0 control run would settle it (results note §8). Not run — out of the pre-registered scope.
3. The late-n regime is uninformative by design (§13 saturation); conclusions there are deliberately withheld.
4. The oracle decomposition shows the §13 metrics substantially reward amplitude restoration; any future comparison of mitigation methods on this benchmark should report the oracle baseline alongside.
5. Aer API docs verified at 0.17.1 vs installed 0.17.2 (design §16/§19, flagged UNVERIFIED at patch level); the mitiq 1.0.0 changelog's "ZNE bug fix" is unexamined in detail (design §18.8).
6. The macOS Accelerate BLAS emits spurious complex-matmul warnings; filtered only in two test modules with per-module rationale, and one unasserted path (the ED reference in the run script) relies on corroboration against the Trotter curve rather than a direct assertion.

## 7. Approval requested

**Authorisation to make a first commit of the file list in §5 — yes or no.** Nothing else is requested: **no push, no remote, no publication** — those are separate decisions that have not been asked for, and nothing in this repository should be read as implying them.
