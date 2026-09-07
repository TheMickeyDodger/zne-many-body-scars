# CI Reproduction: What Is Verified, What Is Not (A3 assessment)

> **[2026-09-06, post-release annotation — read first.]** The "NEVER RUN"
> status line and the "never run" table cell below are **historical**: true
> when this assessment was written (2026-08-18) and since superseded. The
> entire A3 assessment body below this note is retained unedited; its
> present-tense statements are present-tense relative to 2026-08-18. This
> annotation records the one run now on record, exactly as observed, and
> upgrades **no** claim in either direction.
>
> **The run.** `.github/workflows/full-reproduction.yml` was dispatched once,
> as an **operator-approved run of the existing workflow** (this task's agents
> neither triggered, cancelled, re-ran, nor modified any workflow): run
> `34063462240`, `head_sha` `1822597ed5e222ac770e0f619d0bfa62e8276c20`,
> `created_at` `2026-09-06T22:15:05Z`, **`conclusion=failure`**, updated
> `2026-09-06T22:24:00Z`; public record:
> <https://github.com/TheMickeyDodger/zne-many-body-scars/actions/runs/34063462240>.
> Steps that **succeeded**: checkout and setup, the
> pinned dependency install, the unit suite (including the sealed-identity
> guard test), the full experiment re-execution into the guarded fresh
> directory, and the upload of the `reproduction-bundle` artifact (artifact id
> `9998323512`, SHA-256
> `e255fd5d7dd1e4e9d442c57dea1c01d8914da0c66644e044c60807ad72e7bb9c`). The
> step that **failed, exit 1**: "Verify against the canonical bundle". Failed
> log: `gh run view 34063462240 --log-failed`.
>
> **Two different verdicts appeared in the log, and they must not be
> conflated.** The experiment step printed its own rounded headline,
> `VERDICT (§13, density-matrix primary): PASS | GIF=1.2777 | m=39 wins=39`
> — that is the re-executed experiment's *pre-registered §13 verdict at
> display precision*. The verifier step then printed
> `VERDICT: FAIL — 609 problem(s).` — that is the *comparison verdict* at the
> §16 tolerance. The first line is **not** a verifier pass and is **not**
> evidence of cross-platform reproduction; the primary pipeline did **not**
> pass the verifier.
>
> **Per-file verifier result** (off-platform mode, 1e-12 absolute, as the
> table below pre-declared):
>
> | Canonical file | Verifier result |
> |---|---|
> | `steps.csv` | not byte-identical; numeric comparison **FAILED — 6 values beyond 1e-12** |
> | `seed_arms.csv` | not byte-identical; numeric comparison **FAILED — 603 values beyond 1e-12** |
> | `folded_circuits.csv` | not byte-identical; numerically identical to 1e-12 |
> | `metrics.json` | not byte-identical; numerically identical to 1e-12 |
> | `shot_values.csv` | **byte-identical** |
>
> The six `steps.csv` deviations, verbatim from the log (`file:line:column`,
> line 1 being the header, so line 5 is the $n = 4$ row):
>
> ```
> steps.csv:2:shot_if_value:            |14.045502698582332  - 14.04550269858587|   > 1e-12
> steps.csv:5:if_value:                 |20.172922906976577  - 20.172922906978435|  > 1e-12
> steps.csv:37:shot_secondary_estimate: |-0.3860895477526625 - -0.3860895486044606| > 1e-12
> steps.csv:37:shot_secondary_std:      |0.5092171015108129  - 0.5092171025894241|  > 1e-12
> steps.csv:38:shot_secondary_estimate: |-0.3225737945912299 - -0.3225737931254321| > 1e-12
> steps.csv:38:shot_secondary_std:      |0.23798390899683874 - 0.23798390844059475| > 1e-12
> ```
>
> **Independently re-derived counts and maxima** (absolute deviation vs the
> canonical bundle). Every number in this annotation is reproducible from
> public inputs without re-running the experiment. From the repository root,
> with the pinned `.venv` and an authenticated `gh` (the artifact is public;
> `gh` supplies the download token GitHub requires):
>
> ```bash
> # 1. Retrieve the run's uploaded artifact (id 9998323512) and check its digest
> gh api repos/TheMickeyDodger/zne-many-body-scars/actions/artifacts/9998323512 --jq .digest
> #    -> sha256:e255fd5d7dd1e4e9d442c57dea1c01d8914da0c66644e044c60807ad72e7bb9c
> gh api -X GET repos/TheMickeyDodger/zne-many-body-scars/actions/artifacts/9998323512/zip > ci-bundle.zip
> shasum -a 256 ci-bundle.zip      # expect e255fd5d7dd1e4e9d442c57dea1c01d8914da0c66644e044c60807ad72e7bb9c
> unzip -q ci-bundle.zip -d ci-bundle   # exactly six files: the §16 bundle
> # 2. The verifier's verdict, unchanged tool, same command CI ran
> .venv/bin/python tools/verify_reproduction.py --canonical results/minimal --repro ci-bundle
> #    -> ... VERDICT: FAIL — 609 problem(s).   (exit 1)
> # 3. Counts and maxima per file (reads both bundles, writes nothing)
> .venv/bin/python -c "import csv; C='results/minimal'; R='ci-bundle'
> for f in ['steps.csv','seed_arms.csv','folded_circuits.csv','shot_values.csv']:
>     a=list(csv.reader(open(f'{C}/{f}'))); b=list(csv.reader(open(f'{R}/{f}'))); assert a[0]==b[0] and len(a)==len(b), f
>     n=0; fails=0; mx=0.0; bycol={}
>     for ra,rb in zip(a[1:],b[1:]):
>         for h,x,y in zip(a[0],ra,rb):
>             try: fx,fy=float(x),float(y)
>             except ValueError: continue
>             if fx!=fx or fy!=fy: continue
>             n+=1; d=abs(fx-fy); mx=max(mx,d)
>             if d>1e-12: fails+=1; bycol[h]=bycol.get(h,0)+1
>     print(f,'byte_identical',open(f'{C}/{f}','rb').read()==open(f'{R}/{f}','rb').read(),'finite_numeric_cells',n,'beyond_1e-12',fails,'max_abs_delta',mx,'by_column',bycol)"
> # 4. The failed step's own log
> gh run view 34063462240 --log-failed
> ```
>
> Public record of the run and artifact:
> <https://github.com/TheMickeyDodger/zne-many-body-scars/actions/runs/34063462240>
> and
> <https://github.com/TheMickeyDodger/zne-many-body-scars/actions/runs/34063462240/artifacts/9998323512>.
> Steps 2 and 3 above were executed on 2026-09-06 against the retrieved
> artifact and reproduced the verifier verdict and the table below exactly.
> *Optional, non-normative internal audit provenance* (Herd working state, not
> shipped with the released artifact, not needed to verify any claim here):
> `.herd/state/task-evidence-20260906/ci-numeric-audit.json`,
> `lead-env/ci-numeric-recheck.log`, `ci-artifact-local-verifier.log`, and
> `executor/public-command-tests.log`. Results:
>
> | File | Values beyond 1e-12 / values compared | Max abs deviation |
> |---|---|---|
> | `steps.csv` | 6 / 1396 | 1.4657978164578367e-09 |
> | `seed_arms.csv` | 603 / 4156 | 1.4563966227454372e-08 |
> | `folded_circuits.csv` | 0 / 10560 | 1.1102230246251565e-16 |
> | `shot_values.csv` | 0 / 4800 (byte-identical) | 0 |
>
> Within `seed_arms.csv`'s 603 failures, the **non-shot** column
> `secondary_avoid_log` contributes **298** and `shot_secondary_avoid_log`
> contributes **305** (example: `seed_arms.csv:2:secondary_avoid_log:
> |-0.8838112234362765 - -0.8838112226706908| > 1e-12`).
>
> **This is not a shot-pipeline-only outcome.** `steps.csv:5:if_value` (the
> density-matrix primary's IF at $n = 4$) and the `secondary_avoid_log` column
> of `seed_arms.csv` are density-matrix-derived quantities that exceeded 1e-12.
> Moreover the raw `shot_values.csv` was byte-identical, so the pre-declared
> "known legitimate failure mode" of claims-ledger item 2 below (cross-platform
> shot determinism across `qiskit-aer` builds) does **not** by itself account
> for this outcome. That is stated plainly and left there.
>
> **What was identical and what differed** (read from the artifact's
> `environment.json`, retrieved by step 1 above, compared with
> `results/minimal/environment.json` and `tools/release_identity.json`;
> optional internal record: the Lead's read-only provenance check,
> `lead-env/ci-numeric-recheck.log`). The CI run's `environment.json`
> recorded `source_tree_sha256`
> `ab751d691a4cc3fc623b6044ef70dead0b54df46c0f33f880e574f7a828d6ca2`, which
> **equals** the sealed v0.1.0 identity in `tools/release_identity.json`, and
> its `source_identifier_note` equals the sealed note — the run executed the
> sealed release source, and the verifier's provenance validation is not what
> failed. `versions.python` was 3.12.14 on both sides (the workflow pins it).
> Pinned package versions were **identical** between the canonical bundle and
> the CI run — zero package differences. The platform fields differed exactly
> as the table below predicted: canonical Darwin / arm64 / BLAS `accelerate`
> (version `unknown`) vs CI Linux / x86_64 / BLAS `scipy-openblas` 0.3.29.
> The deviation is therefore not attributable to a source-identity,
> Python-version, or dependency-pin mismatch. **The cause of the >1e-12
> deviations is unresolved and open.** This annotation offers no causal
> explanation and proposes no fix.
>
> **Claim status — nothing upgraded, nothing loosened.** This is a real,
> unresolved, reportable cross-platform reproduction finding — exactly what
> claims-ledger item 3 below anticipated ("a red run does not automatically
> mean the artifact is broken ... the verifier's per-file, per-field output is
> the claim"). design.md §16's cross-platform 1e-12 expectation is **now
> tested and NOT confirmed** by the one run on record: it is not
> demonstrated, and **no tolerance is changed** — 1e-12 stands as written, in
> the verifier and in every document. The ledger continues to govern any
> future claim change. This finding does **not** invalidate the v0.1.0
> verdict, which is defined by the pre-registered §13 metrics on the recorded
> canonical data; it is a statement about cross-platform reproduction and
> nothing further in either direction. **Local evidence, kept separate:** the
> local pinned suite still passes (116 passed, `.venv/bin/python -m pytest -q` —
> a runnable check, not a pointer;
> Python 3.12.14 on the macOS/arm64 platform class — the records deliberately
> hold no machine identity, README §4 and design.md §16/A2-5, so no claim is
> made here that the local machine is the original canonical machine), and the
> same-hardware byte-identity claim as scoped in README §4 and design.md §16 is
> unaffected by this Linux-runner result.
> Closing this finding requires no code, science, or pin change from this
> documentation task; any such change is a separate, escalated decision.

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
