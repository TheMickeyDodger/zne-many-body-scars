"""Tests for tools/verify_reproduction.py (Phase A rounds 2-4).

The tool is the single executable form of the repository's reproduction claims:
same-platform → byte identity of the five data files; off-platform → numeric
agreement to 1e-12. Provenance is validated as an ATOMIC PAIR against the
SEALED release identity (tools/release_identity.json) and the canonical
recorded pair — never against the current working tree, which closes both
round-3/4 failure directions: a modified tree cannot validate its own runs,
and a correct sealed-identity reproduction keeps passing after later tree
edits. Platform differences may change VALUES only, never the metadata schema.
Fixtures are small synthetic bundles — the real canonical directory is never
involved; identities are injected so tests are hermetic. The final test is the
LOUD seal guard: it recomputes the real working tree's identity and fails if
the seal has gone stale.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location(
    "verify_reproduction", ROOT / "tools" / "verify_reproduction.py"
)
vr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vr)

SEALED_HASH = "ssss-sealed-release-hash"
SEALED_NOTE = "sealed release note"
SEALED = (SEALED_HASH, SEALED_NOTE)
CANONICAL_HASH = "aaaa-canonical-hash"
CANONICAL_NOTE = "canonical note"

BASE_ENV = {
    "parameters": {"L": 6, "noise": {"p1": 0.001, "p2": 0.01}},
    "versions": {"python": "3.12.14",
                 "packages": {"mitiq": "1.0.0", "numpy": "2.2.6", "pip": "26.2.1",
                              "qiskit-aer": "0.17.2"}},
    "platform": {"system": "Darwin", "machine": "arm64",
                 "blas": {"name": "accelerate", "version": ""}},
    "source_tree_sha256": CANONICAL_HASH,
    "source_identifier_note": CANONICAL_NOTE,
    "design_section": "docs/design.md §15",
}

CSV_TEXT = "n,value,shot_value,mode\n1,0.5,0.51,log\n2,-0.25,-0.24,log\n"
METRICS = {"gif_value": 1.2777, "shot_pipeline": {"gif_value": 1.2774}, "note": "x"}


def write_bundle(root: Path, env: dict, csv_text: str = CSV_TEXT,
                 metrics: dict = METRICS) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "environment.json").write_text(json.dumps(env, indent=2, sort_keys=True))
    for name in ("steps.csv", "seed_arms.csv", "folded_circuits.csv", "shot_values.csv"):
        (root / name).write_text(csv_text)
    (root / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True))
    return root


def env_variant(**overrides) -> dict:
    env = json.loads(json.dumps(BASE_ENV))
    for dotted, value in overrides.items():
        keys = dotted.split("__")
        target = env
        for key in keys[:-1]:
            target = target[key]
        if value is None:
            target.pop(keys[-1], None)
        else:
            target[keys[-1]] = value
    return env


def run(canon: Path, repro: Path, current_identity: tuple = SEALED):
    """current_identity defaults to the sealed pair (a clean tree); tests for
    a modified tree inject something else."""
    lines = []
    code = vr.verify(canon, repro, echo=lines.append,
                     current_identity=current_identity, sealed=SEALED)
    return code, "\n".join(lines)


# ------------------------------------------------ provenance: the atomic pair

def test_identical_bundles_pass_same_platform(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", BASE_ENV)
    code, out = run(canon, repro)
    assert code == 0
    assert "same-platform" in out and "PASS" in out


def test_sealed_pair_reproduction_passes(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", env_variant(
        source_tree_sha256=SEALED_HASH,
        source_identifier_note=SEALED_NOTE,
        versions__packages__pip="27.0",
    ))
    code, out = run(canon, repro)
    assert code == 0
    assert "expected-provenance — pair matches the sealed v0.1.0 release identity" in out
    assert "versions.packages.pip: expected-tooling" in out


def test_sealed_pair_reproduction_passes_even_with_modified_working_tree(tmp_path):
    """Round-4 supplement, direction 1 (lead1's live false-FAIL): a correct
    sealed-identity reproduction must PASS regardless of the current working
    tree's state — tree divergence is reported, not failed."""
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", env_variant(
        source_tree_sha256=SEALED_HASH, source_identifier_note=SEALED_NOTE))
    code, out = run(canon, repro,
                    current_identity=("someone-edited-the-tree", "edited note"))
    assert code == 0
    assert "working tree: MODIFIED" in out
    assert "PASS" in out


def test_modified_tree_run_cannot_validate_itself(tmp_path):
    """Round-4 reviewer reproduction (direction 2): a run from an edited tree
    records that tree's hash; it must be reported noncanonical, never PASS —
    even though the hash matches the current working tree exactly."""
    modified = ("e0255c07-modified-tree-hash", "current emitted note")
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", env_variant(
        source_tree_sha256=modified[0], source_identifier_note=modified[1]))
    code, out = run(canon, repro, current_identity=modified)
    assert code == 1
    assert "noncanonical" in out
    assert "UNEXPECTED" in out


def test_mixed_pair_sealed_hash_with_canonical_note_fails(tmp_path):
    """Atomicity: combinations no real run emitted must fail."""
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", env_variant(
        source_tree_sha256=SEALED_HASH))  # note stays canonical
    code, out = run(canon, repro)
    assert code == 1
    assert "neither the canonical recorded pair nor the sealed release pair" in out


def test_mixed_pair_canonical_hash_with_sealed_note_fails(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", env_variant(
        source_identifier_note=SEALED_NOTE))  # hash stays canonical
    code, out = run(canon, repro)
    assert code == 1
    assert "neither the canonical recorded pair nor the sealed release pair" in out


def test_arbitrary_provenance_hash_fails(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", env_variant(source_tree_sha256="deadbeef"))
    code, out = run(canon, repro)
    assert code == 1
    assert "source_tree_sha256: UNEXPECTED" in out and "noncanonical" in out


def test_missing_provenance_hash_fails(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", env_variant(source_tree_sha256=None))
    code, out = run(canon, repro)
    assert code == 1
    assert "source_tree_sha256: UNEXPECTED" in out


# --------------------------------------------------- environment allowlist

def test_unexpected_parameter_difference_fails(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", env_variant(parameters__noise__p2=0.02))
    code, out = run(canon, repro)
    assert code == 1
    assert "parameters.noise.p2: UNEXPECTED" in out and "FAIL" in out


def test_non_pip_package_difference_is_unexpected_same_platform(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", env_variant(versions__packages__numpy="2.3.0"))
    code, out = run(canon, repro)
    assert code == 1
    assert "versions.packages.numpy: UNEXPECTED" in out


def test_extra_package_is_unexpected(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", env_variant(versions__packages__ipython="9.0"))
    code, out = run(canon, repro)
    assert code == 1
    assert "versions.packages.ipython: UNEXPECTED" in out
    assert "extra package" in out


def test_data_byte_difference_fails_same_platform(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", BASE_ENV)
    (repro / "steps.csv").write_text(CSV_TEXT.replace("0.5", "0.5000001"))
    code, out = run(canon, repro)
    assert code == 1
    assert "steps.csv: NOT byte-identical" in out


def test_missing_data_file_fails(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", BASE_ENV)
    (repro / "seed_arms.csv").unlink()
    code, out = run(canon, repro)
    assert code == 1
    assert "seed_arms.csv: MISSING" in out


# ----------------------------------------- same platform class, different hardware

NEAR_CSV = CSV_TEXT.replace("-0.25", "-0.2500000000000001")  # within 1e-12


def test_same_platform_byte_mismatch_without_flag_fails_with_hardware_hint(tmp_path):
    """Round-11 finding 2: an honest run on a different machine of the same
    platform class fails byte identity; the failure must say why and name the
    flag, not report a bare discrepancy."""
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", BASE_ENV, csv_text=NEAR_CSV)
    code, out = run(canon, repro)
    assert code == 1
    assert "numerically identical" in out
    assert "--different-hardware" in out
    assert "SAME hardware" in out


def test_different_hardware_declaration_switches_to_numerical_contract(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", BASE_ENV, csv_text=NEAR_CSV)
    lines = []
    code = vr.verify(canon, repro, echo=lines.append, current_identity=SEALED,
                     sealed=SEALED, different_hardware=True)
    out = "\n".join(lines)
    assert code == 0
    assert "--different-hardware declared" in out
    assert "numerically identical" in out


def test_different_hardware_does_not_relax_numeric_tolerance(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", BASE_ENV,
                         csv_text=CSV_TEXT.replace("-0.25", "-0.2501"))
    code = vr.verify(canon, repro, echo=lambda *_: None, current_identity=SEALED,
                     sealed=SEALED, different_hardware=True)
    assert code == 1


def test_different_hardware_does_not_relax_environment_rules(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", env_variant(versions__packages__numpy="2.3.0"))
    code = vr.verify(canon, repro, echo=lambda *_: None, current_identity=SEALED,
                     sealed=SEALED, different_hardware=True)
    assert code == 1


# -------------------------------------------------------------- off-platform

OFF_ENV = env_variant(
    versions__python="3.12.11",
    platform__system="Linux",
    platform__machine="x86_64",
)


def test_off_platform_detected_and_tiny_numeric_drift_passes(tmp_path):
    """A legitimate off-platform reproduction — platform VALUES differ, schema
    intact, pinned packages exact — must PASS (no false positive)."""
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", OFF_ENV,
                         csv_text=CSV_TEXT.replace("-0.25", "-0.2500000000000001"))
    code, out = run(canon, repro)
    assert code == 0
    assert "off-platform" in out
    assert "numerically identical" in out
    assert "versions.python: expected-platform" in out
    assert "platform.system: expected-platform" in out


def test_off_platform_stack_drift_fails(tmp_path):
    fake = env_variant(
        versions__python="3.9.1",
        platform__system="Linux",
        versions__packages__mitiq="2.0.0",
    )
    fake["versions"]["packages"]["qiskit-aer"] = "0.99"
    fake["versions"]["packages"].pop("numpy")
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", fake)
    code, out = run(canon, repro)
    assert code == 1
    assert "versions.python: UNEXPECTED" in out and "3.9.1" in out
    assert "versions.packages.mitiq: UNEXPECTED" in out
    assert "versions.packages.qiskit-aer: UNEXPECTED" in out
    assert "versions.packages.numpy: UNEXPECTED" in out


def test_unsupported_python_version_fails_even_with_matching_data(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", env_variant(versions__python="3.13.1"))
    code, out = run(canon, repro)
    assert code == 1
    assert "versions.python: UNEXPECTED" in out
    assert "outside the supported" in out


# ------------------------------------------------- platform schema (round 4)

def test_removed_platform_field_is_unexpected(tmp_path):
    """Round-4 reviewer reproduction: deleting platform.machine must FAIL."""
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", env_variant(platform__machine=None))
    code, out = run(canon, repro)
    assert code == 1
    assert "platform.machine: UNEXPECTED" in out
    assert "missing from the reproduction" in out


def test_removed_nested_platform_field_is_unexpected(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", env_variant(platform__blas__name=None))
    code, out = run(canon, repro)
    assert code == 1
    assert "platform.blas.name: UNEXPECTED" in out


def test_extra_platform_field_is_unexpected(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", env_variant(platform__bogus_extra="x"))
    code, out = run(canon, repro)
    assert code == 1
    assert "platform.bogus_extra: UNEXPECTED" in out
    assert "extra platform field" in out


def test_extra_EMPTY_platform_mapping_is_unexpected(tmp_path):
    """Round-11 reviewer reproduction: platform.system='Linux' (off-platform)
    plus platform.bogus_empty={} passed, because flatten() dropped empty dicts.
    Empty containers are structure and must be classified."""
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    corrupted = env_variant(platform__system="Linux")
    corrupted["platform"]["bogus_empty"] = {}
    repro = write_bundle(tmp_path / "repro", corrupted)
    code, out = run(canon, repro)
    assert code == 1
    assert "platform.bogus_empty: UNEXPECTED" in out


def test_missing_EMPTY_mapping_from_canonical_side_is_unexpected(tmp_path):
    canon_env = json.loads(json.dumps(BASE_ENV))
    canon_env["platform"]["empty_but_required"] = {}
    canon = write_bundle(tmp_path / "canon", canon_env)
    repro = write_bundle(tmp_path / "repro", BASE_ENV)
    code, out = run(canon, repro)
    assert code == 1
    assert "platform.empty_but_required: UNEXPECTED" in out
    assert "missing from the reproduction" in out


def test_equal_empty_mappings_on_both_sides_pass(tmp_path):
    env = json.loads(json.dumps(BASE_ENV))
    env["platform"]["shared_empty"] = {}
    canon = write_bundle(tmp_path / "canon", env)
    repro = write_bundle(tmp_path / "repro", json.loads(json.dumps(env)))
    code, out = run(canon, repro)
    assert code == 0


def test_extra_NULL_platform_field_is_unexpected(tmp_path):
    """Round-12 reviewer reproduction (sibling of the empty-container bug):
    platform.system='Linux' plus platform.bogus_null=null passed, because
    dict.get() mapped missing and explicit null both to None. Membership must
    be compared separately from values."""
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    corrupted = env_variant(platform__system="Linux")
    corrupted["platform"]["bogus_null"] = None
    repro = write_bundle(tmp_path / "repro", corrupted)
    code, out = run(canon, repro)
    assert code == 1
    assert "platform.bogus_null: UNEXPECTED" in out


def test_required_platform_field_set_to_null_is_unexpected(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    nulled = json.loads(json.dumps(BASE_ENV))
    nulled["platform"]["machine"] = None  # present, but null — not merely missing
    repro = write_bundle(tmp_path / "repro", nulled)
    code, out = run(canon, repro)
    assert code == 1
    assert "platform.machine: UNEXPECTED" in out


def test_package_set_to_null_is_unexpected(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    nulled = json.loads(json.dumps(BASE_ENV))
    nulled["versions"]["packages"]["numpy"] = None
    repro = write_bundle(tmp_path / "repro", nulled)
    code, out = run(canon, repro)
    assert code == 1
    assert "versions.packages.numpy: UNEXPECTED" in out


def test_container_replaced_by_leaf_is_unexpected(tmp_path):
    """Type change: platform.blas dict -> string must surface as structure."""
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", env_variant(platform__blas="accelerate"))
    code, out = run(canon, repro)
    assert code == 1
    assert "platform.blas.name: UNEXPECTED" in out  # canonical leaves missing
    assert "platform.blas: UNEXPECTED" in out       # new leaf not in schema


def test_structurally_malformed_environment_fails_cleanly(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", env_variant(platform=None))
    code, out = run(canon, repro)
    assert code == 2
    assert "structurally malformed" in out


# --------------------------------------------------------- numeric comparison

def test_off_platform_numeric_drift_beyond_tolerance_fails(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", OFF_ENV,
                         csv_text=CSV_TEXT.replace("-0.25", "-0.2501"))
    code, out = run(canon, repro)
    assert code == 1
    assert "FAIL" in out


def test_off_platform_shot_only_failures_cite_section16_caveat(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", OFF_ENV)
    (repro / "shot_values.csv").write_text(CSV_TEXT.replace("0.51", "0.52"))
    metrics = json.loads(json.dumps(METRICS))
    metrics["shot_pipeline"]["gif_value"] = 1.279
    (repro / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True))
    code, out = run(canon, repro)
    assert code == 1
    assert "shot-pipeline" in out and "§16" in out


def test_off_platform_string_cell_difference_fails(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    repro = write_bundle(tmp_path / "repro", OFF_ENV,
                         csv_text=CSV_TEXT.replace("log", "avoid_log"))
    code, out = run(canon, repro)
    assert code == 1


def test_missing_environment_json_fails_cleanly(tmp_path):
    canon = write_bundle(tmp_path / "canon", BASE_ENV)
    empty = tmp_path / "empty"
    empty.mkdir()
    code, out = run(canon, empty)
    assert code == 2
    assert "not found" in out


# ------------------------------------------- the LOUD seal-staleness guard

def test_sealed_identity_matches_the_working_tree():
    """Fails loudly whenever hashed source changes without a deliberate update
    of tools/release_identity.json — staleness surfaces here, as a test
    failure, never as a silent wrong verification result."""
    assert vr.current_source_identity() == vr.sealed_identity(), (
        "hashed source (src/**/*.py, scripts/*.py, pyproject.toml, "
        "requirements.txt) changed without updating the sealed release "
        "identity in tools/release_identity.json — update it deliberately "
        "if the change is legitimate"
    )
