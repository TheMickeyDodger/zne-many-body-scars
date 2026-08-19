# CI Reproduction: What Is Verified, What Is Not (A3 assessment)

**Status: the workflow (`.github/workflows/full-reproduction.yml`) exists and is
YAML-valid, but has NEVER RUN.** Nothing in this repository may describe its
checks as demonstrated until a run is on record. This document states exactly
what a green (or red) run would mean, ahead of time, so the claim is fixed
before the evidence exists.

## The two workflows

| Workflow | Trigger | Runtime | Verifies |
|---|---|---|---|
| `tests.yml` (unchanged) | push / PR to main | 53 s observed for the then-52-test suite (run 32196123194); the suite is 105 tests at M2 state | The unit suite on ubuntu-latest with the pinned requirements — including, once the Phase A work is committed, the sealed-identity guard test. It executes **no experiment** and makes **no reproduction claim**. |
| `full-reproduction.yml` (new, never run) | `workflow_dispatch` only | expected minutes-scale; see below | Full re-execution of the minimal experiment plus comparison against the canonical bundle via `tools/verify_reproduction.py`. |

CI has never verified byte identity of the experiment outputs, and no document
in this repository claims it has.

## Why the full-reproduction job is technically sound to attempt

- The pinned `requirements.txt` installs on `ubuntu-latest` and the suite passes
  (observed: run 32196123194, 53 s).
- A full experiment run costs **250.3 s wall clock** on the pinned
  macOS/arm64 machine (measured by the project lead; reproducing
  `VERDICT PASS, GIF=1.2777, m=39, wins=39`). Local user CPU is ~700–900 s
  across ~13 threads, so a standard 2–4-core runner should need roughly
  6–15 minutes of compute — well inside a 45-minute ceiling. This is a runtime
  *estimate*, not a measurement; the first run will supply the number.

## Exactly which comparisons apply on a Linux runner

`environment.json` fields, enumerated (this is the off-platform contract
enforced by `tools/verify_reproduction.py`, which the job calls — the job adds
no comparison logic of its own):

| Field | On ubuntu-latest | Verifier treatment |
|---|---|---|
| `source_tree_sha256` + `source_identifier_note` | equal the sealed pair iff the run was produced by the sealed **hashed experiment source** (`src/**/*.py`, `scripts/*.py`, `pyproject.toml`, `requirements.txt` — the seal does not cover `tools/`, `tests/`, `docs/`, or `.github/`; whole-checkout integrity is a property of the commit the workflow ran against, shown in the run's own metadata, not of the seal) | validated **atomically** against `tools/release_identity.json` (or the canonical pair); anything else fails as noncanonical |
| `versions.python` | pinned to 3.12.14 in the workflow, so **must match** | in-range drift (3.12.x) would be tolerated; the pin removes even that |
| `versions.packages.*` except pip | **must match** — installed from the same lockfile | any change, removal, or extra package fails |
| `versions.packages.pip` | may differ (workflow upgrades pip) | expected-tooling |
| `platform.system` / `machine` / `blas.*` | **cannot match** (Linux / x86_64 / non-Accelerate BLAS) | expected-platform, values only — the field set must be structurally identical |
| `parameters.*`, `design_section` | must match | any difference fails |

Data files: byte identity is documented **only** for the pinned Python 3.12.14
macOS environment on the same physical hardware (README §4; design §16), so
the Linux job compares **numerically at 1e-12 absolute** on every numeric
value, with exact match required for every non-numeric cell. The workflow, the verifier's own output, and this document
all say so; no blanket `diff` is involved anywhere.

## The claims ledger — before the first run

1. **design.md §16's cross-platform 1e-12 agreement is a design expectation.**
   The workflow *tests* it; it has not *demonstrated* it. If and when a run is
   recorded, the claim may be upgraded — only to the tolerance actually
   observed, and only in documents updated after that run.
2. **Known legitimate failure mode, declared in advance:** §16 claims only
   *statistical* reproducibility for the 8192-shot secondary pipeline across
   differing qiskit-aer builds, and a Linux wheel is a different build of the
   pinned `qiskit-aer==0.17.2`. If shot-derived values exceed 1e-12, the
   verifier fails with an explicit note citing §16 while confirming whether the
   density-matrix primary (the pre-registered verdict's basis) reproduced. That
   outcome would be a **reportable finding about cross-platform shot
   determinism — not a reason to loosen the tolerance silently**. Any tolerance
   change must be made in the open, in the verifier, with the observed values
   recorded.
3. A red run therefore does not automatically mean the artifact is broken, and
   a green run does not mean byte identity — the verifier's per-file,
   per-field output is the claim, and the uploaded `reproduction-bundle`
   artifact preserves the evidence either way.

## Deliberate design decisions

- **Trigger `workflow_dispatch` only.** The job is minutes of compute with no
  new information on ordinary pushes; the 53-second unit job already covers
  those. Run it deliberately: before sealing a release, after any accepted
  hashed-source change (with the seal updated first — otherwise the pytest step
  fails on the seal-guard test, by design), or to answer an environment
  question. No schedule: an unattended failure of expectation (2) would sit
  unnoticed, and this repository prefers findings to be looked at.
- **Python pinned to 3.12.14 exactly.** Buys: `versions.python` drops out of
  the legitimately-different set, and the run stays inside README §4's
  supported range by construction. Does not buy: byte identity on Linux
  (platform/BLAS still differ). Cost: if the runner image ever drops the 3.12.14
  build, the job fails at setup — visibly, which is the correct failure mode
  for a pin.
- **Canonical safety.** The job writes only `results/repro/` (the guarded
  default) and uploads it as a CI artifact. The M1 guards refuse both frozen
  directories — including merely adding files — and no
  `--allow-canonical-overwrite` appears anywhere in CI. The canonical bundle is
  opened read-only by the verifier.
- **Comparison logic is not duplicated.** The job's verification step is one
  call to `tools/verify_reproduction.py` — the single tested entry point
  (covered by its own test file; run `pytest` for the live count) that already
  distinguishes same-platform from off-platform and validates provenance
  against the sealed identity. The workflow contains zero comparison logic to
  rot.

## Validation status of the workflow file itself

YAML syntax checked locally; action versions (`checkout@v7`, `setup-python@v7`,
`upload-artifact@v7`) match or track the repository's existing workflow and the
actions' current major releases (verified read-only via the GitHub API). The
workflow has not been executed: executing it requires pushing it to GitHub,
which is outside this milestone's authority. First execution and any claim
upgrade that follows are release-owner decisions.
