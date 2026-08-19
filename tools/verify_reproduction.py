#!/usr/bin/env python
"""Compare a reproduction results directory against the canonical recorded bundle.

Enforces exactly the repository's documented reproduction claims (README §4,
docs/design.md §16), exits non-zero on any genuine mismatch, and states which
comparison mode it detected:

- SAME-PLATFORM mode (the reproduction's recorded Python version and
  platform/BLAS match the canonical `environment.json` — the same platform
  CLASS; the records deliberately contain no machine identity, so sameness of
  the physical machine cannot be detected): by default the five data files
  (steps.csv, seed_arms.csv, folded_circuits.csv, shot_values.csv,
  metrics.json) must be byte-identical, which design §16 scopes to the SAME
  hardware. A reproducer on a different physical machine of this platform
  class declares that with --different-hardware, which switches the data-file
  contract to the numerical one below while keeping every environment rule.
- OFF-PLATFORM mode (they differ): byte identity is not claimed. Files that
  are not byte-identical are compared numerically — every numeric value must
  agree to 1e-12 absolute (design §16); non-numeric cells must match exactly.
  If the values exceeding the tolerance are confined to shot-pipeline
  quantities, the report cites design §16's statistical-reproducibility caveat
  for differing qiskit-aer builds — reported as a failure with that
  explanation, never silently passed.

Trust anchor: the SEALED v0.1.0 source identity in tools/release_identity.json
(unhashed, so it can state the hash without changing it). A reproduction's
recorded (source_tree_sha256, source_identifier_note) is validated as an
ATOMIC PAIR against the two pairs real runs can have emitted — the sealed pair
and the canonical bundle's recorded pair; anything else (mixed combinations
included) is noncanonical and fails. The expectation NEVER derives from the
current working tree, which closes both failure directions at once: an edited
tree cannot validate its own runs (its runs record a non-sealed hash), and a
correct sealed-identity reproduction keeps PASSING no matter what happens to
the working tree afterwards. The tree's own hash is still recomputed and
reported — informationally — so a modified tree is visible; the loud guard
that the seal and the tree must agree lives in the test suite
(tests/test_verify_reproduction.py), where staleness surfaces as a test
failure, never as a silent wrong PASS.

`environment.json` differences are classified against a NARROW allowlist; the
default is UNEXPECTED, which fails the check in either mode:

- provenance pair: as above.
- `versions.packages.pip`: expected-tooling (deliberately unpinned; pip enters
  no computation).
- `versions.python`: expected-platform only within the documented supported
  range (3.12.x, README §4); anything else is UNEXPECTED.
- `platform.*`: expected-platform for VALUE differences only — the leaf-field
  SET must match the canonical schema exactly, with empty mappings counted as
  structure (an extra key whose value is {} is an extra field, not nothing).
  A missing or extra platform field is UNEXPECTED: legitimate off-platform
  reproduction changes values, not the metadata structure.
- EVERY other `versions.packages.*` difference — changed version, removed
  package, or extra package — is UNEXPECTED in BOTH modes. The canonical bundle
  records exactly the pinned `requirements.txt` environment (verified in the
  Phase A audit), so enforcing "match the canonical record" enforces the pins
  transitively, and additions/removals indicate a deviation from the README §4
  procedure (a clean venv from the lockfile carries nothing else).
- `parameters.*` / `design_section`: UNEXPECTED — the reproduction did not run
  the recorded configuration.

This tool deliberately lives in tools/, NOT scripts/ or src/: those trees are
inside the `source_tree_sha256` globs, and the comparison logic must stay
editable without changing the experiment's recorded source identity. (It may
freely IMPORT from scripts/ — reading hashed code does not change it.)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_IDENTITY_FILE = Path(__file__).resolve().parent / "release_identity.json"
DATA_FILES = ("steps.csv", "seed_arms.csv", "folded_circuits.csv",
              "shot_values.csv", "metrics.json")
TOLERANCE = 1e-12
PROVENANCE_FIELDS = ("source_tree_sha256", "source_identifier_note")
TOOLING_FIELDS = {"versions.packages.pip"}
SUPPORTED_PYTHON_PREFIX = "3.12."  # README §4: reproduction requires Python 3.12.x


def sealed_identity() -> tuple:
    """(hash, note) sealed for the release in tools/release_identity.json."""
    sealed = json.loads(RELEASE_IDENTITY_FILE.read_text())["sealed"]
    return sealed["source_tree_sha256"], sealed["source_identifier_note"]


def current_source_identity() -> tuple:
    """(hash, note) of the working tree, recomputed independently from the
    hashed source itself. Used only to check the tree AGAINST the sealed
    identity — never as the expectation for a reproduction's recorded values
    (a modified tree must not validate itself)."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    try:
        spec = importlib.util.spec_from_file_location(
            "run_minimal", REPO_ROOT / "scripts" / "run_minimal.py"
        )
        run_minimal = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(run_minimal)
    finally:
        sys.path.pop(0)
    return run_minimal.source_tree_hash(), run_minimal.SOURCE_IDENTIFIER_NOTE


class _EmptyMapping:
    """Sentinel leaf standing for an empty dict, so container structure is
    validated recursively INCLUDING empty mappings: without it, an extra key
    whose value is {} would produce no leaf, escape classification entirely,
    and silently pass (review round-11 finding). Compares equal only to
    itself, so an empty mapping on one side never equals a real value."""

    def __repr__(self) -> str:
        return "<empty mapping>"

    def __eq__(self, other) -> bool:
        return isinstance(other, _EmptyMapping)

    def __hash__(self) -> int:
        return hash(_EmptyMapping)


EMPTY_MAPPING = _EmptyMapping()

# Sentinel distinguishing a key that is ABSENT from one that is present with a
# JSON null value; equal only to itself, never to None.
_MISSING = object()


def flatten(mapping: dict, prefix: str = "") -> dict:
    """Flatten nested dicts to {dotted.path: leaf_value}. Empty dicts become
    an EMPTY_MAPPING sentinel leaf (never dropped); a container-vs-leaf type
    change therefore always surfaces as differing/missing keys."""
    flat = {}
    for key, value in mapping.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            if value:
                flat.update(flatten(value, path + "."))
            else:
                flat[path] = EMPTY_MAPPING
        else:
            flat[path] = value
    return flat


def detect_mode(canonical_env: dict, repro_env: dict) -> str:
    """same-platform iff recorded Python version and platform block match."""
    same = (
        canonical_env["versions"]["python"] == repro_env["versions"]["python"]
        and canonical_env["platform"] == repro_env["platform"]
    )
    return "same-platform" if same else "off-platform"


def classify_provenance_pair(canonical_env: dict, repro_env: dict,
                             sealed: tuple) -> list:
    """Validate (source_tree_sha256, source_identifier_note) as an ATOMIC pair
    against the two pairs real runs can have emitted: the canonical bundle's
    recorded pair and the sealed release pair. Returns [(field, kind, detail)]
    for the provenance fields that differ from canonical (empty if identical)."""
    canonical_pair = tuple(canonical_env.get(f) for f in PROVENANCE_FIELDS)
    repro_pair = tuple(repro_env.get(f) for f in PROVENANCE_FIELDS)
    differing = [f for f, a, b in zip(PROVENANCE_FIELDS, canonical_pair, repro_pair)
                 if a != b]
    if not differing:
        return []
    if repro_pair == sealed:
        detail = "pair matches the sealed v0.1.0 release identity"
        return [(f, "expected-provenance", detail) for f in differing]
    if repro_pair == canonical_pair:
        return []  # unreachable given `differing`, kept for clarity
    detail = ("provenance (source_tree_sha256, source_identifier_note) matches "
              "neither the canonical recorded pair nor the sealed release pair "
              "as a whole — no real run emitted this combination; the "
              "reproduction is noncanonical")
    return [(f, "UNEXPECTED", detail) for f in differing]


def classify_env_diffs(canonical_env: dict, repro_env: dict, mode: str,
                       sealed: tuple) -> list:
    """Return [(dotted_field, classification, detail)] for every differing
    leaf. Default classification is UNEXPECTED; see module docstring for the
    narrow allowlist."""
    a, b = flatten(canonical_env), flatten(repro_env)
    diffs = list(classify_provenance_pair(canonical_env, repro_env, sealed))
    for field in sorted(set(a) | set(b)):
        if field in PROVENANCE_FIELDS:
            continue  # handled atomically above
        # Key MEMBERSHIP is compared separately from values via the _MISSING
        # sentinel: dict.get() would map a missing key and an explicit JSON
        # null both to None, letting an extra null-valued field (or a required
        # field set to null) compare equal and escape classification entirely
        # (review round-12 finding — the absence/presence sibling of the
        # empty-container bug).
        canonical_value = a.get(field, _MISSING)
        repro_value = b.get(field, _MISSING)
        if canonical_value == repro_value:
            continue
        detail = ""
        if field in TOOLING_FIELDS:
            kind = "expected-tooling"
        elif field == "versions.python":
            if isinstance(repro_value, str) and repro_value.startswith(SUPPORTED_PYTHON_PREFIX):
                kind = "expected-platform"
            else:
                kind, detail = "UNEXPECTED", (
                    f"Python {repro_value!r} is outside the supported "
                    f"{SUPPORTED_PYTHON_PREFIX}x range (README §4)")
        elif field.startswith("platform."):
            if field not in a:
                kind, detail = "UNEXPECTED", (
                    f"extra platform field not in the canonical schema — "
                    "legitimate off-platform reproduction changes values, "
                    "not the metadata structure")
            elif field not in b:
                kind, detail = "UNEXPECTED", (
                    "required platform field missing from the reproduction — "
                    "legitimate off-platform reproduction changes values, "
                    "not the metadata structure")
            elif repro_value is None or isinstance(repro_value, _EmptyMapping):
                kind, detail = "UNEXPECTED", (
                    "required platform field set to null/empty — expected-platform "
                    "covers real value differences only, not absence in disguise")
            else:
                kind = "expected-platform"
        elif field.startswith("versions.packages."):
            kind = "UNEXPECTED"
            package = field.rsplit(".", 1)[1]
            if repro_value is _MISSING:
                detail = f"package {package!r} missing from the reproduction environment"
            elif canonical_value is _MISSING:
                detail = f"extra package {package!r} not in the canonical pinned environment"
            else:
                detail = (f"pinned-environment package {package!r} differs "
                          f"({canonical_value!r} → {repro_value!r}); the 1e-12 claim "
                          "holds only under the pinned environment (design §16)")
        else:
            kind = "UNEXPECTED"
            detail = "the reproduction did not run the recorded configuration"
        diffs.append((field, kind, detail))
    return diffs


def _numbers_close(a, b, tol: float) -> bool:
    return abs(a - b) <= tol


def compare_json_values(a, b, tol: float, path: str = "") -> list:
    """Recursive compare; numbers by absolute tolerance, everything else exact.
    Returns a list of (path, description) mismatches."""
    if isinstance(a, bool) or isinstance(b, bool):  # bool before int: exact
        return [] if a == b else [(path, f"{a!r} != {b!r}")]
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return [] if _numbers_close(a, b, tol) else [(path, f"|{a} - {b}| > {tol}")]
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            return [(path, f"key sets differ: {sorted(set(a) ^ set(b))}")]
        out = []
        for key in a:
            out.extend(compare_json_values(a[key], b[key], tol, f"{path}.{key}".lstrip(".")))
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [(path, f"list lengths differ: {len(a)} != {len(b)}")]
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out.extend(compare_json_values(x, y, tol, f"{path}[{i}]"))
        return out
    return [] if a == b else [(path, f"{a!r} != {b!r}")]


def compare_csv_numeric(canonical_path: Path, repro_path: Path, tol: float) -> list:
    """Cell-by-cell compare; floats by absolute tolerance, other cells exact.
    Returns a list of (location, description) mismatches."""
    import csv

    with canonical_path.open(newline="") as f:
        rows_a = list(csv.reader(f))
    with repro_path.open(newline="") as f:
        rows_b = list(csv.reader(f))
    if not rows_a or not rows_b or rows_a[0] != rows_b[0]:
        return [(canonical_path.name, "headers differ")]
    if len(rows_a) != len(rows_b):
        return [(canonical_path.name, f"row counts differ: {len(rows_a)} != {len(rows_b)}")]
    header = rows_a[0]
    mismatches = []
    for i, (ra, rb) in enumerate(zip(rows_a[1:], rows_b[1:]), start=2):
        if len(ra) != len(rb):
            mismatches.append((f"{canonical_path.name}:{i}", "column counts differ"))
            continue
        for col, (ca, cb) in zip(header, zip(ra, rb)):
            if ca == cb:
                continue
            try:
                fa, fb = float(ca), float(cb)
            except ValueError:
                mismatches.append((f"{canonical_path.name}:{i}:{col}", f"{ca!r} != {cb!r}"))
                continue
            if not _numbers_close(fa, fb, tol):
                mismatches.append(
                    (f"{canonical_path.name}:{i}:{col}", f"|{ca} - {cb}| > {tol}")
                )
    return mismatches


def _is_shot_location(location: str) -> bool:
    """Whether a mismatch location belongs to the shot pipeline (design §16's
    statistical-reproducibility caveat for differing Aer builds)."""
    if location.startswith("shot_values.csv"):
        return True
    if location.startswith("metrics.json") and "shot_pipeline" in location:
        return True
    parts = location.split(":")
    return len(parts) == 3 and parts[2].startswith("shot_")


def verify(canonical_dir: Path, repro_dir: Path, tol: float = TOLERANCE,
           echo=print, current_identity: tuple | None = None,
           sealed: tuple | None = None, different_hardware: bool = False) -> int:
    """Run the full comparison; returns the process exit code (0 = pass).
    `current_identity` (working-tree hash/note) and `sealed` (release identity)
    default to live values; tests inject both. `different_hardware` is the
    caller's declaration that the reproduction ran on a different physical
    machine of the same platform class: the recorded environment deliberately
    contains no machine identity, so machine sameness CANNOT be detected from
    the records and byte identity (design §16: same hardware only) is then not
    the right requirement — the declaration switches the data-file comparison
    to the numerical (1e-12) contract while keeping every environment rule of
    same-platform mode."""
    canonical_env_path = canonical_dir / "environment.json"
    repro_env_path = repro_dir / "environment.json"
    for path in (canonical_env_path, repro_env_path):
        if not path.is_file():
            echo(f"FAIL: {path} not found — is the directory a complete bundle?")
            return 2
    canonical_env = json.loads(canonical_env_path.read_text())
    repro_env = json.loads(repro_env_path.read_text())
    for label, env in (("canonical", canonical_env), ("reproduction", repro_env)):
        if not (isinstance(env.get("versions"), dict)
                and isinstance(env["versions"].get("python"), str)
                and isinstance(env["versions"].get("packages"), dict)
                and isinstance(env.get("platform"), dict)):
            echo(f"FAIL: {label} environment.json is structurally malformed "
                 "(missing versions.python / versions.packages / platform)")
            return 2
    if sealed is None:
        try:
            sealed = sealed_identity()
        except Exception as error:  # noqa: BLE001
            echo(f"FAIL: cannot read the sealed release identity "
                 f"({RELEASE_IDENTITY_FILE}): {error}")
            return 2
    if current_identity is None:
        try:
            current_identity = current_source_identity()
        except Exception as error:  # noqa: BLE001 - report, never skip validation
            echo(f"FAIL: cannot recompute the working tree's source identity "
                 f"({error}); provenance validation is mandatory")
            return 2

    failures = []

    # ---- working-tree state: reported, never used as the expectation ----
    # (Informational: a run made from a modified tree records that tree's hash
    # and will fail the pair validation below on its own merits. A correct
    # sealed-identity reproduction must keep passing regardless of the current
    # tree state, so tree divergence is NOT itself a verification failure —
    # the loud seal-vs-tree guard lives in the test suite.)
    if current_identity != sealed:
        echo("working tree: MODIFIED relative to the sealed release identity "
             f"({current_identity[0][:12]}… vs sealed {sealed[0][:12]}…, "
             "tools/release_identity.json) — runs made from this tree will "
             "be reported noncanonical; if the hashed-source change is "
             "legitimate, update the sealed identity deliberately")
    else:
        echo(f"working tree: matches the sealed release identity ({sealed[0][:12]}…)")

    mode = detect_mode(canonical_env, repro_env)
    numerical_data_contract = (mode == "off-platform") or different_hardware
    echo(f"comparison mode detected: {mode}"
         + (" (numerical data contract: --different-hardware declared)"
            if mode == "same-platform" and different_hardware else ""))
    if mode == "same-platform" and not different_hardware:
        echo("  (recorded Python version and platform/BLAS match — the same "
             "platform CLASS; machine identity is not recorded and cannot be "
             "verified. The five data files must be byte-identical, which "
             "design §16 scopes to the SAME hardware: if this reproduction ran "
             "on a different physical machine of this platform class, re-run "
             "with --different-hardware for the numerical contract instead)")
    elif mode == "same-platform":
        echo("  (same platform class, different physical machine by caller "
             f"declaration: byte identity is not required; numeric agreement "
             f"to {tol} is — design §16)")
    else:
        echo("  (recorded Python version or platform/BLAS differ: byte identity "
             f"is not claimed; numeric agreement to {tol} is required — design §16)")

    # ---- the five data files ----
    for name in DATA_FILES:
        a, b = canonical_dir / name, repro_dir / name
        if not b.is_file():
            failures.append((name, "missing from reproduction directory"))
            echo(f"{name}: MISSING")
            continue
        if a.read_bytes() == b.read_bytes():
            echo(f"{name}: byte-identical")
            continue
        if name.endswith(".json"):
            mismatches = compare_json_values(
                json.loads(a.read_text()), json.loads(b.read_text()), tol, name
            )
        else:
            mismatches = compare_csv_numeric(a, b, tol)
        if not numerical_data_contract:
            failures.append((name, "not byte-identical (required for same-hardware "
                                   "reproduction on the same platform class)"))
            if mismatches:
                echo(f"{name}: NOT byte-identical — FAIL (byte identity required; "
                     f"values also differ numerically beyond {tol})")
            else:
                echo(f"{name}: NOT byte-identical — FAIL as declared, but "
                     f"numerically identical to {tol}: consistent with a "
                     "different physical machine of the same platform class "
                     "(design §16 scopes byte identity to the SAME hardware). "
                     "If that is your situation, re-run with --different-hardware.")
            continue
        if mismatches:
            failures.extend(mismatches)
            echo(f"{name}: not byte-identical; numeric comparison FAILED "
                 f"({len(mismatches)} value(s) beyond {tol}):")
            for location, description in mismatches[:10]:
                echo(f"    {location}: {description}")
            if len(mismatches) > 10:
                echo(f"    … and {len(mismatches) - 10} more")
        else:
            echo(f"{name}: not byte-identical; numerically identical to {tol}")

    # ---- environment.json field classification (narrow allowlist) ----
    env_diffs = classify_env_diffs(canonical_env, repro_env, mode, sealed)
    if env_diffs:
        echo("environment.json differing fields:")
        for field, kind, detail in env_diffs:
            echo(f"    {field}: {kind}" + (f" — {detail}" if detail else ""))
            if kind == "UNEXPECTED":
                failures.append((f"environment.json:{field}",
                                 detail or "unexpected difference"))
    else:
        echo("environment.json: identical")

    # ---- verdict ----
    if failures:
        shot_only = all(_is_shot_location(loc) for loc, _ in failures)
        echo(f"\nVERDICT: FAIL — {len(failures)} problem(s).")
        if mode == "off-platform" and shot_only:
            echo("note: every failing value is a shot-pipeline quantity; design §16 "
                 "claims only statistical reproducibility for the shot pipeline "
                 "across differing qiskit-aer builds. This remains a failure of "
                 "the 1e-12 check and is reported as such — but the density-matrix "
                 "primary pipeline reproduced, which is the pre-registered verdict's "
                 "basis.")
        return 1
    echo("\nVERDICT: PASS — every check for the detected mode passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a reproduction of the minimal experiment against the "
                    "canonical recorded bundle (see module docstring).")
    parser.add_argument("--canonical", default="results/minimal")
    parser.add_argument("--repro", default="results/repro")
    parser.add_argument("--tolerance", type=float, default=TOLERANCE)
    parser.add_argument(
        "--different-hardware", action="store_true",
        help="declare that the reproduction ran on a different physical machine "
             "of the same platform class (machine identity is not recorded, so "
             "this cannot be auto-detected): the data-file contract becomes "
             "numerical (1e-12, design §16) instead of byte identity; all "
             "environment rules are unchanged",
    )
    args = parser.parse_args()
    return verify(Path(args.canonical), Path(args.repro), args.tolerance,
                  different_hardware=args.different_hardware)


if __name__ == "__main__":
    sys.exit(main())
