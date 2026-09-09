"""Noiseless references: E_0 (statevector of the transpiled circuit) and E^ED (dense eigh), prereg §4.5."""
from __future__ import annotations

import numpy as np

from zne_scars.hamiltonian import mfim_hamiltonian

from .circuits import base_circuit
from .observables import neel_index, values_from_probabilities, weight_matrix
from .simulate import statevector_probabilities

ED_RESIDUAL_MAX = 1e-10


def e0_curve(L: int, n_max: int, site_string: str | None = None, W: np.ndarray | None = None) -> np.ndarray:
    """[n_max, 5] raw quantities of the noiseless statevector at n = 1..n_max."""
    W = weight_matrix(L) if W is None else W
    return np.stack([values_from_probabilities(statevector_probabilities(base_circuit(L, n, site_string)), W) for n in range(1, n_max + 1)])


def eigendecomposition(L: int):
    H = mfim_hamiltonian(L)
    eps, V = np.linalg.eigh(H)
    # einsum avoids the macOS Accelerate complex-matmul path that emits spurious overflow warnings
    HV = np.einsum("ij,jk->ik", H, V)
    resid = max(np.linalg.norm(HV[:, j] - eps[j] * V[:, j]) for j in range(len(eps)))
    gram = np.einsum("ji,jk->ik", V.conj(), V)
    orth = np.max(np.abs(gram - np.eye(len(eps))))
    return eps, V, float(resid), float(orth)


def ed_curve(L: int, n_max: int, initial_index: int | None = None, W: np.ndarray | None = None):
    """[n_max, 5] continuous-time exact quantities at t = n (dt = 1); plus (residual, orthonormality defect)."""
    W = weight_matrix(L) if W is None else W
    eps, V, resid, orth = eigendecomposition(L)
    psi0 = np.zeros(2**L, complex)
    psi0[neel_index(L) if initial_index is None else initial_index] = 1.0
    c = np.einsum("ji,j->i", V.conj(), psi0)
    rows = []
    for n in range(1, n_max + 1):
        psi = np.einsum("ij,j->i", V, np.exp(-1j * eps * n) * c)
        rows.append(values_from_probabilities(np.abs(psi) ** 2, W))
    return np.stack(rows), resid, orth
