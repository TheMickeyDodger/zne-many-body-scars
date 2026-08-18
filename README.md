# zne-many-body-scars

A local, simulation-only study of zero-noise extrapolation (ZNE) applied to quantum many-body scar dynamics in the mixed-field Ising model (MFIM). Fully specified by [`docs/design.md`](docs/design.md) (the pre-registered design, 20 sections with a complete review history), with **one canonical execution** per that design plus two reproductions that verified byte-identity; findings in [`docs/results-minimal.md`](docs/results-minimal.md), raw recorded data in `results/minimal/`.

## 1. The question

Does ZNE, applied to a first-order Trotter simulation of quantum many-body scar dynamics in the one-dimensional MFIM, reduce the error of the staggered-magnetization observable $\langle Z_\pi\rangle/L$ relative to the noiseless value of the *same* circuit, under a fully specified local depolarizing noise model in a classical simulator? (design.md §1 — a measurement, pre-registered, with a negative result declared reportable in advance.)

## 2. The answer as found — qualifications inline

*(Verdict-class numbers below are from `results/minimal/metrics.json`; per-step numbers from `results/minimal/steps.csv`; oracle decompositions from `docs/results-minimal.md` §9, recomputable from `steps.csv` with the conventions stated there.)*

**The pre-registered verdict passes** — GIF = 1.2777 (RMS error 0.32080 unmitigated → 0.25107 mitigated), with IF > 1 on 39 of 39 reportable steps (m = 39; step n = 34 excluded by the pre-registered ε_min filter, and it is also the one step where ZNE increased the error, IF = 0.145, where there was almost nothing to mitigate) — **but that sentence is incomplete without the following four qualifications, which are part of the result:**

- **The improvement is strongly regime-dependent.** IF peaks at 20.17 at n = 4 and decays to ≈ 1.107 by n = 40.
- **Much of the metric's reward is amplitude restoration, not extrapolation.** A post-hoc *oracle* constant rescale — fitted against the exact answer, which no real experiment has — captures ≈ 68% of the primary's RMS reduction, so the per-step win count overstates what genuine extrapolation contributes. ZNE nonetheless beats that oracle (GIF 1.278 vs 1.174) using only noisy data at three scale factors.
- **At late steps no claim is made in either direction.** Both errors saturate toward $|E_0(n)|$ and IF → 1; the pre-registered metrics cannot distinguish ZNE failure from the absence of any remaining signal there (design.md §13).
- **Two discrepancies were preserved, not tuned away** (results note §§4, 8): the observed decay is ≈ 2× slower than the design's global-depolarizing heuristic (consistent with channel locality; the single-qubit floor correction is explicitly unresolved — a p₂ = 0 control would settle it), and the pre-registered ExpFactory(asymptote = 0) *secondary* outperforms the linear primary by ≈ 3.4× in RMS (0.07349 vs 0.25107). Among the linear arms themselves, the λ_eff diagnostic edges the primary (RMS 0.24303 vs 0.25107), the ordering the design's §10 algebra anticipated. The linear primary remains the verdict — it was pre-registered as such for source fidelity and was not swapped after seeing results — and the secondary's advantage is a statement about this simulated noise model only.

The shot-based secondary pipeline (8192 shots, seeded) independently gives GIF = 1.2774 and the same 39/39 pattern.

## 3. Provenance in brief

Per the provenance table in **design.md §14**, which governs: (a) the original paper (Chen, Burdick, Yao, Orth, Iadecola, PRR **4**, 043027 (2022); arXiv:2203.08291) demonstrates error-mitigated scar dynamics on IBM hardware up to 19 qubits; (b) the Mitiq documentation example reproduces a simplified simulator version; (c) **this repository** performs a controlled, exactly-referenced, simulation-only measurement of ZNE's effect at L = 6 (it does not replicate the Paper's hardware results or the example's exact configuration); (d) nothing here supports hardware claims of any kind — see §14(d) for the full restriction list, which this README does not weaken.

## 4. Reproduction

Requirements: Python 3.12.x (mitiq 1.0.0 requires ≥3.11, <3.13), network access for the initial install only.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt   # fully pinned lockfile
.venv/bin/python -m pip install -e .

.venv/bin/python -m pytest -q

# Reproduce the experiment into a FRESH directory — never overwrite the canonical
# results/minimal/, the evidence base the experiment's documented numbers check against:
.venv/bin/python scripts/run_minimal.py --out results/repro

# The determinism claim's evidence IS this comparison — run it, do not skip it:
shasum -a 256 results/minimal/* results/repro/*
# every file must hash identically to its counterpart; equivalently:
diff -r results/minimal results/repro && echo "byte-identical"

# Regenerate figures (reads recorded CSV only), likewise into a fresh directory:
.venv/bin/python scripts/make_figures.py --results results/repro --out figures-repro
```

Cost, qualitatively: the test suite runs in seconds; the experiment in a few minutes on a laptop. No experiment-runtime timing is recorded in `results/` — a deliberate design choice (timing goes to stdout only and is excluded from the deterministic outputs, precisely so that byte-reproducibility does not depend on wall clock). Incidental pytest durations appearing in `docs/mutation-evidence.md` are test-harness output, not experiment data.

**Determinism claim** (design.md §16; proven, not asserted): on the same pinned environment, the experiment's six recorded output files are byte-identical across runs — verified across three independent executions (two by the implementer, one by the project lead from a clean state), all sha256-identical. **Exact byte-comparison requires Python 3.12.14** (the version recorded in `environment.json`); any other 3.12.x gives numerical reproduction only. Cross-platform, design.md §16 claims only 1e-12 agreement (BLAS reductions differ). Nothing time- or path-dependent enters the recorded outputs. The figure regeneration claim is that figures derive from recorded CSV only; no byte-identity claim is made for image files.

## 5. Limitations

Everything measured here binds to: L = 6, the staggered-magnetization density $\langle Z_\pi\rangle/L$, gate-attached two-tier depolarizing noise at p₁ = 10⁻³ / p₂ = 10⁻², two-qubit-restricted seeded random folding, scale factors {1.0, 1.5, 2.0}, and fold seeds 1000–1007. No statement transfers to other sizes, observables, channels, rates, or to hardware (design.md §14(d), §18). In particular, the ExpFactory secondary's 3.4× advantage is a statement about **this simulated noise model** and these data; it is not evidence the exponential ansatz wins elsewhere, and no claim is made about the true functional form of the noise response.

## 6. References

The verified citations of **design.md §19** (all fetched and checked during M1; no new sources here). Primary: I-C. Chen, B. Burdick, Y. Yao, P. P. Orth, T. Iadecola, *Error-Mitigated Simulation of Quantum Many-Body Scars on Quantum Computers with Pulse-Level Control*, Phys. Rev. Research **4**, 043027 (2022), arXiv:2203.08291, DOI 10.1103/PhysRevResearch.4.043027; the Mitiq example "Use ZNE to simulate quantum many body scars with Qiskit on IBMQ backends" (mitiq.readthedocs.io); mitiq 1.0.0 and qiskit-aer 0.17.2 API sources as itemized in §19.

## 7. Repository layout

```
docs/design.md            pre-registered design + full revision history (§20)
docs/results-minimal.md   findings of the minimal experiment, traceable to results/
docs/review-package.md    review package for the human owner (commit decision)
docs/mutation-evidence.md mechanically generated mutation-sensitivity evidence (13 defects)
src/zne_scars/            all physics/statistics modules (importable, side-effect-free)
tests/                    test suite incl. the pre-registered T1–T6 properties (run pytest for the live count)
scripts/run_minimal.py    executes design §15 exactly; orchestration only
scripts/make_figures.py   regenerates figures from recorded results only
results/minimal/          the recorded experiment (deterministic, 6 files)
figures/                  generated exclusively from results/minimal/
requirements.txt          pinned environment (pip freeze --exclude-editable)
pyproject.toml            packaging + pytest configuration
```
