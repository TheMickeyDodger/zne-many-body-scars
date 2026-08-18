"""Mixed-field Ising model Hamiltonian (design.md §3) and exact references (§12.2).

Conventions (design.md §4, binding): physical site i in {1, ..., L} maps to
Qiskit qubit q_{i-1}; qubit 0 is the least-significant bit of a statevector
index (Qiskit little-endian). All dense matrices here use that same ordering,
so they compose directly with qiskit.quantum_info objects.
"""

from __future__ import annotations

import numpy as np
from scipy.linalg import expm

V_DEFAULT = 1.0
OMEGA_DEFAULT = 0.24

_I2 = np.eye(2, dtype=complex)
PAULI_X = np.array([[0, 1], [1, 0]], dtype=complex)
PAULI_Z = np.array([[1, 0], [0, -1]], dtype=complex)


def op_on_qubit(op: np.ndarray, qubit: int, num_qubits: int) -> np.ndarray:
    """Embed a 1-qubit operator on `qubit` (little-endian: qubit 0 least significant)."""
    left = np.eye(2 ** (num_qubits - 1 - qubit), dtype=complex)
    right = np.eye(2**qubit, dtype=complex)
    return np.kron(np.kron(left, op), right)


def site_operator(op: np.ndarray, site: int, num_sites: int) -> np.ndarray:
    """Operator on physical site i in {1..L}: site i -> qubit q_{i-1} (design §4)."""
    return op_on_qubit(op, site - 1, num_sites)


def mfim_terms(
    num_sites: int, v: float = V_DEFAULT, omega: float = OMEGA_DEFAULT
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (H_ZZ, H_Z, H_X) of design §3, Paper Eq. (1.2). Open boundary conditions.

    H_ZZ = V sum_{i=1}^{L-1} Z_i Z_{i+1}
    H_Z  = -2V sum_{i=2}^{L-1} Z_i - V (Z_1 + Z_L)   (boundary field halved)
    H_X  = Omega sum_{i=1}^{L} X_i
    """
    dim = 2**num_sites
    h_zz = np.zeros((dim, dim), dtype=complex)
    h_z = np.zeros((dim, dim), dtype=complex)
    h_x = np.zeros((dim, dim), dtype=complex)
    for i in range(1, num_sites):  # bonds (i, i+1), i = 1..L-1
        h_zz += v * site_operator(PAULI_Z, i, num_sites) @ site_operator(
            PAULI_Z, i + 1, num_sites
        )
    for i in range(1, num_sites + 1):
        coeff = -v if i in (1, num_sites) else -2.0 * v
        h_z += coeff * site_operator(PAULI_Z, i, num_sites)
        h_x += omega * site_operator(PAULI_X, i, num_sites)
    return h_zz, h_z, h_x


def mfim_hamiltonian(
    num_sites: int, v: float = V_DEFAULT, omega: float = OMEGA_DEFAULT
) -> np.ndarray:
    """Full MFIM Hamiltonian H = H_ZZ + H_Z + H_X (design §3)."""
    h_zz, h_z, h_x = mfim_terms(num_sites, v, omega)
    return h_zz + h_z + h_x


def neel_state_index(num_sites: int) -> int:
    """Basis index of |Z2> = |0101...>_site: even sites i carry |1>, i.e. qubits q_{i-1}."""
    return sum(1 << (i - 1) for i in range(2, num_sites + 1, 2))


def neel_state_vector(num_sites: int) -> np.ndarray:
    vec = np.zeros(2**num_sites, dtype=complex)
    vec[neel_state_index(num_sites)] = 1.0
    return vec


def continuous_time_expectation(
    num_sites: int,
    time: float,
    observable: np.ndarray,
    v: float = V_DEFAULT,
    omega: float = OMEGA_DEFAULT,
    initial_state: np.ndarray | None = None,
) -> float:
    """Exact continuous-time reference <psi(t)| O |psi(t)> (design §12.2)."""
    state = neel_state_vector(num_sites) if initial_state is None else initial_state
    u_t = expm(-1j * time * mfim_hamiltonian(num_sites, v, omega))
    evolved = u_t @ state
    return float(np.real(np.vdot(evolved, observable @ evolved)))
