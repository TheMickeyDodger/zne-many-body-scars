"""Shared canonical-directory write guard for the run scripts (Phase A, A2).

Refuses an output directory that is — by filesystem identity, not name — ANY of
the repository's frozen canonical directories (results/minimal/ and figures/),
or a path inside one, unless the caller passed the explicit override flag.
"Writing" includes merely ADDING files: a foreign file in a frozen directory
falsifies its documented contents (6 recorded files / 2 committed figures) even
when no recorded file is overwritten. Both run scripts guard against BOTH
directories through this one implementation, so the two cannot drift apart
(reviewer round-2 finding: per-script guards each protected only their own
target, letting the wrong script pollute the other's).

This module deliberately lives in scripts/ and is therefore part of the hashed
source tree (`scripts/*.py` glob): the guard runs inside the experiment
process, and code that runs there must stay covered by the recorded source
identity. The cost — a future guard fix changes `source_tree_sha256` — is
accepted in preference to importing unhashed code into the recorded run.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_RESULTS = REPO_ROOT / "results" / "minimal"
CANONICAL_FIGURES = REPO_ROOT / "figures"
FROZEN_DIRS = (CANONICAL_RESULTS, CANONICAL_FIGURES)


def _hits(out: Path, canonical: Path) -> bool:
    """True if writing into `out` would write into `canonical`. Three layers:
    resolved-path prefix (covers not-yet-existing paths and symlink aliases,
    and still applies if the canonical directory does not exist); a
    case-folded name-reservation check, so case-variant spellings of a frozen
    directory are refused on EVERY filesystem whether or not the directory
    currently exists (on a case-sensitive filesystem this over-refuses a
    technically distinct name — accepted: such names are reserved); then
    filesystem identity of the candidate and every existing ancestor against
    the canonical directory (the authoritative check for spellings that name
    the same inode, which Path.resolve() does NOT normalize)."""
    resolved = out.resolve()
    canonical_resolved = canonical.resolve()
    if resolved.is_relative_to(canonical_resolved):
        return True
    folded, folded_canonical = str(resolved).lower(), str(canonical_resolved).lower()
    if folded == folded_canonical or folded.startswith(folded_canonical + os.sep):
        return True
    try:
        canonical_stat = canonical.stat()
    except OSError:
        return False  # canonical absent: no inode to compare; the checks above stand
    for candidate in (resolved, *resolved.parents):
        try:
            if os.path.samestat(candidate.stat(), canonical_stat):
                return True
        except OSError:
            continue  # this prefix does not exist yet
    return False


def resolve_out_dir(raw: str, allow_canonical: bool,
                    canonicals: tuple = FROZEN_DIRS) -> Path:
    """Refuse an output directory that would write into any frozen canonical
    directory — by filesystem identity, not name — unless the caller passed
    the explicit override flag. The guarantee: refusal happens before
    output-directory creation, simulation, plotting, or any write to a
    canonical directory (module import itself may still write ordinary
    bytecode/font caches elsewhere)."""
    out = Path(raw)
    for canonical in canonicals:
        if _hits(out, canonical) and not allow_canonical:
            raise SystemExit(
                f"refusing to write into the frozen canonical directory "
                f"{canonical} — writing includes adding files, which would "
                f"falsify its documented contents. Use a fresh --out directory, "
                f"or pass --allow-canonical-overwrite only if you deliberately "
                f"intend to modify canonical artifacts."
            )
    return out
