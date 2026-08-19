"""Canonical-overwrite guards for the run scripts (Phase A / A2, rounds 1-3).

results/minimal/ (frozen recorded evidence) and figures/ (committed canonical
figures) must be impossible to write into accidentally — where "write" includes
merely ADDING files — from EITHER script, unless --allow-canonical-overwrite is
passed explicitly. One shared implementation (scripts/_canonical_guard.py)
protects both directories in both scripts, so the two cannot drift apart
(reviewer round-2 finding: per-script guards left the cross-target hole open).

These tests exercise the shared guard directly against temporary stand-in
canonical directories — the real canonical directories are never written — and
the argparse wiring end-to-end via subprocess for the refusal paths only. The
guarantee tested at the CLI level: refusal happens before output-directory
creation, simulation, plotting, or any write to a canonical directory (module
import itself may write ordinary bytecode/font caches elsewhere, which is why
the claim is scoped this way).
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def _load_script(name: str):
    if name in sys.modules:  # share one instance, as `import` inside the scripts does
        return sys.modules[name]
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(SCRIPTS))
    return module


guard = _load_script("_canonical_guard")
run_minimal = _load_script("run_minimal")
make_figures = _load_script("make_figures")


def _fs_is_case_insensitive(base: Path) -> bool:
    """Detect the actual filesystem behavior at `base` instead of assuming it."""
    probe = base / "case_probe_lower"
    probe.mkdir()
    return (base / "CASE_PROBE_LOWER").exists()


# ---------------------------------------------------------------- guard function

def test_both_scripts_share_the_single_guard_implementation():
    """Anti-drift: the scripts must use the SAME function object, not copies."""
    assert run_minimal.resolve_out_dir is guard.resolve_out_dir
    assert make_figures.resolve_out_dir is guard.resolve_out_dir


def test_guard_protects_both_frozen_directories_by_default():
    assert guard.FROZEN_DIRS == (ROOT / "results" / "minimal", ROOT / "figures")
    assert run_minimal.CANONICAL_RESULTS in guard.FROZEN_DIRS
    assert make_figures.CANONICAL_FIGURES in guard.FROZEN_DIRS


def test_guard_refuses_every_listed_canonical(tmp_path):
    """Cross-target semantics: with two canonicals, BOTH are refused."""
    canon_a, canon_b = tmp_path / "canon_a", tmp_path / "canon_b"
    canon_a.mkdir(), canon_b.mkdir()
    for target in (canon_a, canon_b, canon_a / "sub", canon_b / "sub"):
        with pytest.raises(SystemExit, match="refusing to write"):
            guard.resolve_out_dir(str(target), False, canonicals=(canon_a, canon_b))


def test_guard_refuses_canonical_directory(tmp_path):
    canonical = tmp_path / "canon"
    canonical.mkdir()
    with pytest.raises(SystemExit, match="refusing to write"):
        guard.resolve_out_dir(str(canonical), False, canonicals=(canonical,))


def test_guard_refuses_subdirectory_of_canonical(tmp_path):
    canonical = tmp_path / "canon"
    canonical.mkdir()
    with pytest.raises(SystemExit, match="refusing to write"):
        guard.resolve_out_dir(str(canonical / "sub"), False, canonicals=(canonical,))


def test_guard_refuses_symlink_alias_of_canonical(tmp_path):
    canonical = tmp_path / "canon"
    canonical.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(canonical)
    with pytest.raises(SystemExit, match="refusing to write"):
        guard.resolve_out_dir(str(alias), False, canonicals=(canonical,))


def test_guard_refuses_case_variant_alias_of_canonical(tmp_path):
    """Round-1 BLOCKER regression: on a case-insensitive filesystem a
    differently-cased spelling is the same inode but a different resolved
    string; the guard must refuse by filesystem identity."""
    if not _fs_is_case_insensitive(tmp_path):
        pytest.skip("filesystem at tmp_path is case-sensitive; alias cannot exist")
    canonical = tmp_path / "canon"
    canonical.mkdir()
    for alias in ("CANON", "Canon", "cAnOn"):
        assert os.path.samefile(tmp_path / alias, canonical)  # precondition
        with pytest.raises(SystemExit, match="refusing to write"):
            guard.resolve_out_dir(str(tmp_path / alias), False, canonicals=(canonical,))


def test_guard_refuses_case_variant_subdirectory(tmp_path):
    if not _fs_is_case_insensitive(tmp_path):
        pytest.skip("filesystem at tmp_path is case-sensitive; alias cannot exist")
    canonical = tmp_path / "canon"
    canonical.mkdir()
    with pytest.raises(SystemExit, match="refusing to write"):
        guard.resolve_out_dir(str(tmp_path / "CANON" / "sub"), False,
                              canonicals=(canonical,))


def test_guard_refuses_dotdot_traversal_into_canonical(tmp_path):
    canonical = tmp_path / "canon"
    canonical.mkdir()
    (tmp_path / "elsewhere").mkdir()
    with pytest.raises(SystemExit, match="refusing to write"):
        guard.resolve_out_dir(str(tmp_path / "elsewhere" / ".." / "canon"),
                              False, canonicals=(canonical,))


def test_guard_refuses_case_variant_of_absent_canonical_on_any_filesystem(tmp_path):
    """Round-3 reviewer MINOR: with the canonical directory ABSENT there is no
    inode to compare, so the case-folded name-reservation layer must refuse
    case-variant spellings — on every filesystem, no skip (deliberate
    over-refusal on case-sensitive systems: the names are reserved)."""
    canonical = tmp_path / "ghost"  # never created
    for alias in ("GHOST", "Ghost", "gHoSt"):
        with pytest.raises(SystemExit, match="refusing to write"):
            guard.resolve_out_dir(str(tmp_path / alias), False, canonicals=(canonical,))
    with pytest.raises(SystemExit, match="refusing to write"):
        guard.resolve_out_dir(str(tmp_path / "GHOST" / "sub"), False,
                              canonicals=(canonical,))


def test_guard_case_reservation_applies_to_existing_canonical_too(tmp_path):
    """The case-fold layer is unconditional, so case variants are refused even
    where the filesystem would treat them as distinct directories."""
    canonical = tmp_path / "canon"
    canonical.mkdir()
    with pytest.raises(SystemExit, match="refusing to write"):
        guard.resolve_out_dir(str(tmp_path / "CANON"), False, canonicals=(canonical,))


def test_guard_nonexistent_canonical_is_safe_and_still_name_guarded(tmp_path):
    """Defined behavior when a canonical directory does not exist: no crash,
    fresh directories allowed, and the canonical NAME is still refused via the
    resolved-path prefix check."""
    canonical = tmp_path / "ghost"  # never created
    fresh = tmp_path / "repro"
    assert guard.resolve_out_dir(str(fresh), False, canonicals=(canonical,)) == fresh
    with pytest.raises(SystemExit, match="refusing to write"):
        guard.resolve_out_dir(str(canonical), False, canonicals=(canonical,))
    with pytest.raises(SystemExit, match="refusing to write"):
        guard.resolve_out_dir(str(canonical / "sub"), False, canonicals=(canonical,))


def test_guard_permits_fresh_directory(tmp_path):
    canon_a, canon_b = tmp_path / "canon_a", tmp_path / "canon_b"
    canon_a.mkdir(), canon_b.mkdir()
    fresh = tmp_path / "repro"
    assert guard.resolve_out_dir(str(fresh), False,
                                 canonicals=(canon_a, canon_b)) == fresh


def test_guard_override_permits_canonical(tmp_path):
    canonical = tmp_path / "canon"
    canonical.mkdir()
    out = guard.resolve_out_dir(str(canonical), True, canonicals=(canonical,))
    assert out == canonical


# ---------------------------------------------------------------- parser wiring

def test_run_minimal_default_out_is_fresh_and_guarded():
    args = run_minimal.build_parser().parse_args([])
    assert args.out == "results/repro"
    assert args.allow_canonical_overwrite is False


def test_make_figures_defaults_read_canonical_write_fresh():
    args = make_figures.build_parser().parse_args([])
    assert args.results == "results/minimal"  # read-only input: canonical is safe
    assert args.out == "figures-repro"
    assert args.allow_canonical_overwrite is False


# ------------------------------------------------- end-to-end refusal (scripts)
# Refusal fires before output-directory creation or any write to a canonical
# directory, so these subprocess runs are cheap and never touch the canonical
# directories (module import may write ordinary bytecode caches, nothing else).

CROSS_TARGET_CASES = [
    # own frozen dir
    ("run_minimal.py", "results/minimal"),
    ("run_minimal.py", "results/minimal/sub"),
    ("make_figures.py", "figures"),
    # the OTHER script's frozen dir (round-2 reviewer finding: cross-target)
    ("run_minimal.py", "figures"),
    ("run_minimal.py", "figures/sub"),
    ("make_figures.py", "results/minimal"),
    ("make_figures.py", "results/minimal/sub"),
]


@pytest.mark.parametrize(("script", "out_arg"), CROSS_TARGET_CASES)
def test_script_refuses_canonical_out_argument(script, out_arg):
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / script), "--out", out_arg],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode != 0
    assert "refusing to write" in proc.stderr


CASE_VARIANT_CASES = [
    ("run_minimal.py", "results/MINIMAL", "results/minimal"),
    ("run_minimal.py", "RESULTS/minimal", "results/minimal"),
    ("run_minimal.py", "FIGURES", "figures"),         # cross-target case variant
    ("make_figures.py", "FIGURES", "figures"),
    ("make_figures.py", "results/MINIMAL", "results/minimal"),  # cross-target
]


@pytest.mark.parametrize(("script", "out_arg", "canonical"), CASE_VARIANT_CASES)
def test_script_refuses_case_variant_canonical_out_argument(script, out_arg, canonical):
    """Round-1 BLOCKER regression at the real CLI against the real canonical
    directories (read-only: refusal fires before any write)."""
    try:
        alias_is_canonical = os.path.samefile(ROOT / out_arg, ROOT / canonical)
    except OSError:
        alias_is_canonical = False
    if not alias_is_canonical:
        pytest.skip("repository filesystem is case-sensitive; alias does not exist")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / script), "--out", out_arg],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode != 0
    assert "refusing to write" in proc.stderr
