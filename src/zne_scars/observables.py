"""Staggered magnetization Z_pi = sum_i (-1)^i Z_i, reported as <Z_pi>/L (design.md §5).

Site/bit conventions per design §4: site i -> qubit q_{i-1}; a Qiskit count
string b[L-1]...b[0] has site i at character index L-i (site 1 rightmost).
This module is the single audited place where count strings are decoded.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
from qiskit.quantum_info import SparsePauliOp

from .hamiltonian import PAULI_Z, site_operator


def staggered_sign(site: int) -> int:
    """(-1)^i for physical site i (1-based)."""
    return -1 if site % 2 else 1


def z_pi_matrix(num_sites: int) -> np.ndarray:
    """Dense Z_pi = sum_i (-1)^i Z_i (unnormalized)."""
    dim = 2**num_sites
    out = np.zeros((dim, dim), dtype=complex)
    for site in range(1, num_sites + 1):
        out += staggered_sign(site) * site_operator(PAULI_Z, site, num_sites)
    return out


def staggered_magnetization_density_op(num_sites: int) -> SparsePauliOp:
    """SparsePauliOp for Z_pi / L. Pauli labels are Qiskit-ordered (q_{L-1}...q_0)."""
    labels, coeffs = [], []
    for site in range(1, num_sites + 1):
        qubit = site - 1
        labels.append("I" * (num_sites - 1 - qubit) + "Z" + "I" * qubit)
        coeffs.append(staggered_sign(site) / num_sites)
    return SparsePauliOp(labels, coeffs=np.array(coeffs, dtype=complex))


def expectation_from_counts(counts: Mapping[str, float], num_sites: int) -> float:
    """<Z_pi>/L from a Qiskit counts mapping (keys b[L-1]...b[0]; values may be
    integer shot counts or float weights/probabilities)."""
    total = 0.0
    weight_sum = 0.0
    for raw_key, weight in counts.items():
        key = raw_key.replace(" ", "")
        if len(key) != num_sites:
            raise ValueError(f"count key {raw_key!r} does not match L={num_sites}")
        value = 0.0
        for site in range(1, num_sites + 1):
            bit = key[num_sites - site]  # site i is character L-i (site 1 rightmost)
            z_i = 1.0 if bit == "0" else -1.0
            value += staggered_sign(site) * z_i
        total += weight * value
        weight_sum += weight
    if weight_sum == 0:
        raise ValueError("empty counts")
    return total / (weight_sum * num_sites)
