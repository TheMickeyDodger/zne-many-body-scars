"""Read-only access to tools/phase2_contract.json (the single source of truth)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .identity import REPO_ROOT

DEFAULT_CONTRACT = REPO_ROOT / "tools" / "phase2_contract.json"


@lru_cache(maxsize=4)
def load(path: str | Path = DEFAULT_CONTRACT) -> dict:
    return json.loads(Path(path).read_text())


def constant(c: dict, cid: str):
    return c["constants"][cid]["value"]


def cells_by_index(c: dict) -> dict[int, dict]:
    out = {}
    for cell in c["phase2b"]["matrix_cells"] + c["phase2b"]["control_cells"]:
        out[int(cell["cell_index"])] = cell
    return out


def steps_of(cell: dict) -> list[int]:
    lo, hi = cell["steps"].split("..")
    return list(range(int(lo), int(hi) + 1))


def seed_simulator(cell_index: int, n: int, k: int, j: int) -> int:
    """EQ-B18: 10^6 * cell_index + 100 n + 10 k + j (k = seed index 0..7, j = scale index 0..4)."""
    return 10**6 * cell_index + 100 * n + 10 * k + j


BOOT_SEED_BASE = 20260907
