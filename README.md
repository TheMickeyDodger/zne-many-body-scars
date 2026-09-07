# zne-many-body-scars

This repository studies zero-noise extrapolation (ZNE) in a classical
simulation of quantum many-body scar dynamics in the mixed-field Ising model
(MFIM). The study design is in [`docs/design.md`](docs/design.md), the results
are in [`docs/results-minimal.md`](docs/results-minimal.md), and the recorded
data are in `results/minimal/`. The experiment was run once under the design
and reproduced twice on the same machine with byte-identical output.

![Canonical minimal experiment showing MFIM scar dynamics and absolute error under zero-noise extrapolation](figures/minimal_experiment.png)

## Project status

Status as of 2026-09-06. Release details are in the "Release status" paragraph of §4.

| Phase | Status |
|---|---|
| **Phase 1**, documentation update after the v0.1.0 release (change record: design.md §20 rows P1-1..P1-3) | Finished. [PR 1](https://github.com/TheMickeyDodger/zne-many-body-scars/pull/1) was merged as commit `1da75c8db312888c50d86da71283f3b7fd095fd4`. |
| **Phase 2**, follow-up study | Work has not started. [`docs/followup-study-draft.md`](docs/followup-study-draft.md) is a planning document, not a preregistration. No experiments have been run and no data have been collected. |
| **Phase 3** | Phase 3 is deferred. Work has not started. |

### Reproduction evidence

- **Repeated runs on the same machine produced identical files.** All six output files were byte-for-byte identical across three runs with the same pinned environment and hardware (design.md §16; "Determinism claim" in §4).
- **The tests pass.** GitHub Actions run [34073032105](https://github.com/TheMickeyDodger/zne-many-body-scars/actions/runs/34073032105) completed successfully on the merge commit. PR 1 records 116 passing tests under Python 3.12.14 with pinned dependencies. To run them locally, use `.venv/bin/python -m pytest -q` (§4).
- **The cross-platform comparison failed, and we do not yet know why.** Run [34063462240](https://github.com/TheMickeyDodger/zne-many-body-scars/actions/runs/34063462240) found 609 values outside the §16 tolerance of 1e-12: 6 in `steps.csv` and 603 in `seed_arms.csv`. `shot_values.csv` was byte-identical, while `folded_circuits.csv` and `metrics.json` agreed to 1e-12. The experiment still produced its rounded §13 result of `PASS`, but that result is separate from the failed reproduction check. The tolerance and scientific claims remain unchanged. See [`docs/ci-reproduction-assessment.md`](docs/ci-reproduction-assessment.md) for the full comparison.

## 1. The question

Does ZNE reduce the error in $\langle Z_\pi\rangle/L$ for a first-order
Trotter simulation of the one-dimensional MFIM with local depolarizing noise?
The comparison uses the noiseless value of the same circuit. Design.md §1
defines the question and states that a negative result would also be reported.

## 2. Result

The summary values below come from `results/minimal/metrics.json`; the
per-step values come from `results/minimal/steps.csv`. The oracle comparison
is defined in `docs/results-minimal.md` §9 and can be recalculated from
`steps.csv`.

**The result passes the criterion set in advance.** GIF is 1.2777: RMS error
falls from 0.32080 without mitigation to 0.25107 with mitigation. IF is above
1 on all 39 reportable steps. Step $n=34$ is excluded by the
$\varepsilon_{\min}$ filter; it is also the only step where ZNE increases the
error (IF = 0.145), when the unmitigated error is already very small.

Four qualifications matter:

- **The improvement is strongly regime-dependent.** IF peaks at 20.17 at n = 4 and decays to ≈ 1.107 by n = 40.
- **Much of the improvement comes from restoring amplitude, not from extrapolation.** A post-hoc *oracle* constant rescale, fitted with access to the exact answer, captures about 68% of the primary method's reduction in RMS error. The per-step win count therefore overstates the contribution from extrapolation itself. ZNE still beats the oracle (GIF 1.278 versus 1.174) while using only noisy data at three scale factors.
- **At late steps no claim is made in either direction.** Both errors saturate toward $|E_0(n)|$ and IF → 1; the pre-registered metrics cannot distinguish ZNE failure from the absence of any remaining signal there (design.md §13).
- **Two discrepancies remain open** (results note §§4 and 8). The observed decay is about twice as slow as the design's global-depolarizing estimate. Channel locality may explain this, but the single-qubit contribution is unresolved; a $p_2=0$ control would test it. The ExpFactory secondary method also has about 3.4 times lower RMS error than the linear primary (0.07349 versus 0.25107). Among the linear methods, the $\lambda_{\text{eff}}$ diagnostic is slightly better than the primary (0.24303 versus 0.25107), as the algebra in design.md §10 suggests. The linear primary still determines the reported result because the design selected it before the run. The secondary result applies only to this simulated noise model.

The shot-based secondary pipeline (8192 shots, seeded) independently gives GIF = 1.2774 and the same 39/39 pattern.

## 3. Provenance in brief

The original paper by Chen, Burdick, Yao, Orth, and Iadecola reports
error-mitigated scar dynamics on IBM hardware with systems up to 19 qubits.
The Mitiq documentation provides a simpler simulator example. This repository
uses those sources but runs a separate $L=6$ simulation with its own design.
It neither reproduces the paper's hardware experiment nor makes claims about
hardware performance. Design.md §14 gives the full source comparison and
limitations.

## 4. Reproduction

Requirements: Python 3.12.x (mitiq 1.0.0 requires ≥3.11, <3.13), network access for the initial install only.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt   # fully pinned lockfile
.venv/bin/python -m pip install -e .

.venv/bin/python -m pytest -q

# Reproduce the experiment in a new directory. The scripts refuse to write to
# results/minimal/ or figures/ unless explicitly overridden.
.venv/bin/python scripts/run_minimal.py --out results/repro

# Compare the new bundle with the recorded data. See design.md §16 and
# docs/reproduction-protocol.md for the same-hardware and cross-platform rules.
.venv/bin/python tools/verify_reproduction.py --canonical results/minimal --repro results/repro

# Regenerate figures (reads recorded CSV only), likewise into a fresh directory
# (figures-repro is the default; canonical figures/ is likewise refused without
# the explicit override flag):
.venv/bin/python scripts/make_figures.py --results results/repro --out figures-repro
```

The tests take seconds and the experiment takes a few minutes on a laptop.
Runtime is printed to the terminal but not stored in `results/`, so wall-clock
time cannot affect file comparison. Durations in `docs/mutation-evidence.md`
come from the test harness, not the experiment.

**Determinism.** Three runs on the same machine and pinned environment produced
the same six files byte for byte. The source recorded by the original bundle
has hash `7161d655…`. Later changes to write guards, provenance wording, and
package metadata changed the source hash but not the five data files; the
expected `environment.json` differences are checked against
`tools/release_identity.json`. Exact byte comparison requires Python 3.12.14
and the same hardware and BLAS build. On a different machine, pass
`--different-hardware` to request the numerical comparison. The cross-platform
tolerance is 1e-12, although the first Linux run failed that comparison. The
figures are regenerated from the CSV data, but their image files are not
expected to be byte-identical. See design.md §16 and §20 for the full rules.

**Release status (2026-09-06)**

- GitHub release `v0.1.0` points to revision `51f55c1` and was published at 2026-08-19T03:40:16Z.
- Zenodo record 22005535 has version DOI `10.5281/zenodo.22005535`. `CITATION.cff` cites the concept DOI `10.5281/zenodo.22005534`.
- On 2026-09-06, an independent comparison confirmed that all 22 protected files in the Zenodo archive match this repository.
- The published GitHub release text still contains the old DRAFT disclaimer. `docs/release-notes-v0.1.0.md` explains this discrepancy and the release-date and DOI details.
- The first full-reproduction workflow run failed the §16 cross-platform comparison at 1e-12. The cause remains unknown. `docs/ci-reproduction-assessment.md` records the result. Neither the tolerance nor the scientific claims have changed.

## 5. Limitations

The experiment uses $L=6$, the staggered-magnetization density
$\langle Z_\pi\rangle/L$, depolarizing rates $p_1=10^{-3}$ and $p_2=10^{-2}$,
seeded random folding restricted to two-qubit gates, scale factors
{1.0, 1.5, 2.0}, and fold seeds 1000–1007. The results do not automatically
extend to other system sizes, observables, noise models, rates, or hardware
(design.md §14(d) and §18). In particular, the secondary method's 3.4-fold
advantage applies only to these data and does not establish the functional
form of the noise response.

## 6. References

Design.md §19 lists the sources used by this project: the paper by Chen et
al., *Phys. Rev. Research* **4**, 043027 (2022), arXiv:2203.08291, DOI
10.1103/PhysRevResearch.4.043027; the Mitiq example “Use ZNE to simulate
quantum many body scars with Qiskit on IBMQ backends”; and the relevant Mitiq
1.0.0 and Qiskit Aer 0.17.2 API documentation.

## 7. Repository layout

```
docs/design.md            pre-registered design + full revision history (§20)
docs/results-minimal.md   findings of the minimal experiment, traceable to results/
docs/review-package.md    historical review package for the first-commit decision (dated annotation at top)
docs/mutation-evidence.md mechanically generated mutation-sensitivity evidence (13 defects)
docs/release-notes-v0.1.0.md        release notes for the published v0.1.0 (dated annotation at top; historical DRAFT text kept below it)
docs/reproduction-protocol.md       cold-start reproduction protocol for external researchers
docs/ci-reproduction-assessment.md  results of the 2026-09-06 full-reproduction run and the remaining open question
docs/prereg-p2zero-outline.md       working outline for a future control experiment
docs/phase-a-review-package.md      Phase A review package for the v0.1.0 seal decision
docs/followup-study-draft.md        planning document for the Phase 2 charts and analysis
src/zne_scars/            all physics/statistics modules (importable, side-effect-free)
tests/                    test suite incl. the pre-registered T1–T6 properties (run pytest for the live count)
scripts/run_minimal.py    executes design §15 exactly; orchestration only
scripts/make_figures.py   regenerates figures from recorded results only
scripts/_canonical_guard.py  prevents accidental writes to the recorded data and figures
tools/verify_reproduction.py tested reproduction verifier (unhashed; the single comparison entry point)
tools/release_identity.json  sealed v0.1.0 source identity (hash of src/, scripts/, pyproject, requirements)
results/minimal/          the recorded experiment (deterministic, 6 files)
figures/                  generated exclusively from results/minimal/
.github/workflows/        unit tests plus the manual full-reproduction workflow; its first run failed the numerical comparison
requirements.txt          pinned environment (pip freeze --exclude-editable)
pyproject.toml            packaging + pytest configuration
LICENSE                   Apache-2.0
CITATION.cff              citation metadata (Zenodo concept DOI 10.5281/zenodo.22005534; date-released 2026-08-18)
.gitignore                excludes venv/caches and the default reproduction-output directories
```
