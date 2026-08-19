# Cold-Start Reproduction Protocol

For an external researcher with no access to the original machine and no
knowledge of this project's history. Everything you need is in this repository;
this document tells you exactly what to run, exactly what you should see on
your platform, and how to tell a genuine failure from an expected difference.

## 0. What you are reproducing

One deterministic simulation experiment (design.md §15): MFIM scar dynamics at
L = 6 under a fully specified depolarizing noise model, with zero-noise
extrapolation, over 40 Trotter steps. The canonical recorded output is the
six-file bundle `results/minimal/`. Your run writes a fresh bundle and a
tested verifier compares the two. **A status caveat up front:** exact byte
reproduction has been demonstrated on the pinned macOS environment on the
original hardware (multiple independent runs, sha256-identical — byte identity
is a same-hardware claim, §4 Case A); the cross-platform 1e-12 expectation
below comes from the design (design.md §16) and — until cross-platform runs
are on record — is being *tested* by reproducers like you, not confirmed by
prior evidence. Either outcome of your run is information; please report it.

## 1. Requirements

- Python **3.12.x** (3.12.14 for exact byte comparison — see §4; the verifier
  rejects anything outside 3.12.x as unsupported).
- ~2 GB free RAM, any modern CPU (the run is BLAS-multithreaded).
- Network access for the initial `pip install` only. Nothing else is fetched.

## 2. Setup and self-check

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt   # fully pinned lockfile
.venv/bin/python -m pip install -e .
.venv/bin/python -m pytest -q                          # must be fully green
```

The suite includes a seal-guard test: it fails if the hashed source does not
match the sealed release identity in `tools/release_identity.json`. **Exact
scope of that check:** the seal covers `src/**/*.py`, `scripts/*.py`,
`pyproject.toml`, and `requirements.txt` — the code and pins that produce the
recorded numbers. It does NOT cover `tools/` (including the verifier itself
and the seal file), `tests/`, `docs/`, or `.github/`; a modification there is
invisible to the seal, so if you need assurance about those files too, compare
your checkout against the release tag or archive rather than relying on this
test. Install **only** the lockfile into the venv: extra packages will
(correctly) fail verification later.

## 3. Run

```bash
.venv/bin/python scripts/run_minimal.py --out results/repro
```

≈ 250 s wall clock on the reference machine (Apple-silicon laptop, all cores,
~13× CPU parallelism); on fewer cores expect roughly 5–15 minutes (the same
estimate the CI assessment uses for a 2–4-core runner). The script refuses to write into the
frozen `results/minimal/` or `figures/` directories (including case-variant
spellings), so a stray invocation cannot damage the canonical evidence.

## 4. Verify — one command

```bash
.venv/bin/python tools/verify_reproduction.py --canonical results/minimal --repro results/repro
```

The verifier exits 0 only if every check for your detected situation passes,
and its output names the situation. **Yes, this works for you on Linux** — it
detects your platform case itself; you do not need the pinned machine. What it
enforces, per situation:

### Case A — pinned platform class (macOS, arm64, Accelerate BLAS, Python 3.12.14)

- Mode reported: `same-platform`. This detects the platform **class**, not the
  physical machine — the recorded environment deliberately contains no machine
  identity, so the verifier cannot tell the original machine from another
  M-series Mac. Two sub-cases:
  - **Same physical machine:** the five data files (`steps.csv`,
    `seed_arms.csv`, `folded_circuits.csv`, `shot_values.csv`, `metrics.json`)
    must be **byte-identical** (design.md §16 scopes byte identity to the same
    hardware).
  - **Different machine of this class:** declare it —
    `tools/verify_reproduction.py --different-hardware` — and the data-file
    contract becomes numerical (1e-12) as in Case B, with every
    `environment.json` rule unchanged. Without the flag, a byte mismatch that
    is numerically identical is reported with exactly this diagnosis and a
    pointer to the flag, so an honest reproduction is never silently labeled a
    discrepancy.
- `environment.json` may differ from canonical in exactly:
  - `source_tree_sha256` + `source_identifier_note` — validated together as a
    pair against the sealed release identity. The canonical bundle predates
    three documented post-recording changes to hashed source, none touching
    any computation: canonical-overwrite guards for the frozen directories
    (including the added `scripts/_canonical_guard.py`), a corrected
    `source_identifier_note` wording, and `pyproject.toml` license metadata —
    complete history in design.md §20, Phase A rows A2-1 through A2-6;
  - `versions.packages.pip` — the packaging tool is deliberately unpinned and
    enters no computation.

### Case B — same OS/BLAS, different Python 3.12.x patch

- Mode reported: `off-platform` (the recorded Python version differs).
- Byte identity is **not** claimed. Non-identical files are compared
  numerically: every number must agree to **1e-12 absolute**; every
  non-numeric cell exactly. `versions.python` differing within 3.12.x is
  expected; everything else as in Case A.

### Case C — different OS / CPU / BLAS (e.g. Linux x86_64)

- Mode reported: `off-platform`.
- Numeric comparison at 1e-12 as in Case B. Legitimately differing fields:
  `platform.system`, `platform.machine`, `platform.blas.*` (**values only** —
  if the field *structure* differs, your `environment.json` is malformed and
  the verifier fails), `versions.python` within 3.12.x, and pip.
- **Pinned packages must match exactly** — `mitiq==1.0.0`,
  `qiskit-aer==0.17.2`, `numpy==2.2.6`, etc. A changed, missing, or extra
  package fails verification; that is a deviation from §2, not a platform
  effect.
- **Known caveat, declared in advance (design.md §16):** the 8192-shot
  secondary pipeline is deterministic *given a fixed qiskit-aer build*, and
  your platform's wheel is a different build. If shot-derived values exceed
  1e-12, the verifier fails **with an explicit note citing §16** and tells you
  whether the density-matrix primary pipeline — the basis of the
  pre-registered verdict — reproduced. Please report this outcome (see §6);
  it is a finding about cross-platform shot determinism, not noise in the
  protocol.

## 5. Figures — exact expectations per file

Figures are regenerated from recorded CSV only, never from simulation:

```bash
.venv/bin/python scripts/make_figures.py --results results/repro --out figures-repro
```

- `minimal_experiment.png`: byte-identical to `figures/minimal_experiment.png`
  on the pinned environment (verified); on other platforms/matplotlib builds,
  no byte claim — compare visually.
- `minimal_experiment.pdf`: byte identity is **not claimed** on any platform.
  The evidence behind that: the PDF embeds a Matplotlib `/CreationDate`
  timestamp, and the one measured pinned-environment regeneration differed
  from the canonical file in exactly 5 bytes, all inside `/CreationDate` —
  metadata, not content.
- The repository's claim about figures is provenance (generated exclusively
  from `results/*/steps.csv`), not byte identity (README §4).

## 6. When something differs: triage and reporting

Work down this list; the first match is your answer.

1. **Verifier reports an UNEXPECTED `environment.json` field.** Your
   environment deviates from §2 (extra/missing/changed package, unsupported
   Python, or an edited source tree — the message says which). Rebuild the
   venv from the lockfile on a supported Python and rerun. Not a discrepancy.
2. **Verifier fails only on shot-pipeline quantities, off-platform, with the
   §16 note.** The declared caveat of §4 Case C. Report it (below) with your
   platform details — this is wanted data.
3. **Verifier fails on density-matrix quantities beyond 1e-12, or on byte
   identity in Case A, with a clean environment report.** This is a
   **candidate genuine discrepancy**. Please do not rationalize it away:
   rerun once to confirm it is stable, then report it.
4. **Figures differ** beyond §5's stated expectations while the data files
   verify: report as a figure-toolchain observation; the scientific claim is
   unaffected (figures carry no byte claim).

**Where to report:** open an issue at
<https://github.com/TheMickeyDodger/zne-many-body-scars/issues> and attach
(a) the complete verifier output, (b) your `results/repro/environment.json`,
and (c) for case 3, the differing file(s) or the verifier's listed locations.
The verifier's output is designed to be the complete evidence of what you saw.
