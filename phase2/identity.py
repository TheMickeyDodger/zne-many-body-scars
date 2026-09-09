"""Phase 2 source identity and environment record (contract §C2.2 B-ENV, §C6.3)."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
V010_SEALED_IDENTITY = "ab751d691a4cc3fc623b6044ef70dead0b54df46c0f33f880e574f7a828d6ca2"
AER_SHOT_METHOD = "density_matrix"


def phase2_source_files(root: Path = REPO_ROOT) -> list[Path]:
    files = sorted((root / "phase2").rglob("*.py"))
    req = root / "requirements-phase2.txt"
    return files + [req]


def phase2_source_sha256(root: Path = REPO_ROOT) -> str:
    """sha256 over the sorted `phase2/**/*.py` files and `requirements-phase2.txt`:
    for each file, its repo-relative POSIX path, a NUL, the bytes, a NUL."""
    h = hashlib.sha256()
    for p in phase2_source_files(root):
        h.update(p.relative_to(root).as_posix().encode())
        h.update(b"\0")
        h.update(p.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def contract_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pip_freeze() -> dict[str, str]:
    out = subprocess.run([sys.executable, "-m", "pip", "freeze", "--exclude-editable"],
                         capture_output=True, text=True, check=True).stdout
    pkgs = {}
    for line in out.splitlines():
        if "==" in line:
            n, v = line.split("==", 1)
            pkgs[n] = v
    return pkgs


def platform_record() -> dict:
    import psutil
    return {
        "system": platform.system(), "release": platform.release(),
        "machine": platform.machine(), "python": platform.python_version(),
        "processor": platform.processor(), "cpu_count": os.cpu_count(),
        "memory_total_bytes": int(psutil.virtual_memory().total),
    }


def environment_record(root: Path = REPO_ROOT) -> dict:
    return {
        "python": sys.version,
        "packages": pip_freeze(),
        "platform": platform_record(),
        "phase2_source_sha256": phase2_source_sha256(root),
        "v010_sealed_identity": V010_SEALED_IDENTITY,
        # Load-bearing determinism facts (Lead directive, 2026-09-08): the shot pipeline runs Aer with the
        # method fixed explicitly to density_matrix (Aer's automatic choice at L <= 8; same-seed counts are
        # byte-identical there, whereas statevector trajectories are 25-60x slower AND give different counts),
        # and every shot circuit is executed on its own because Aer batch jobs advance seeds as
        # base + 2113 * i, not the contract's base + j (evidence 1b-01; enumerated deviation record D-1).
        "aer_shot_method": AER_SHOT_METHOD,
        "aer_shot_execution": "one circuit per run call with its own seed_simulator; batch jobs never used",
    }


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n")
