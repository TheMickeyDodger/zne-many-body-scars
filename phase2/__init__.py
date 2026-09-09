"""Phase 2 implementation package (outside every sealed path).

Imports the sealed v0.1.0 modules (`zne_scars`) read-only. Its identity is
sha256 over sorted `phase2/**/*.py` plus `requirements-phase2.txt`
(docs/phase2-analysis-contract.md §C6.3), computed by `phase2.identity`.
"""
