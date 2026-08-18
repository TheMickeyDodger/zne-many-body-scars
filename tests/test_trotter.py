"""T2 (design.md §17): Trotter circuit vs exact unitary, and ordering integrity.

(a) One step at dt=1 equals exp(-iH_ZZ) exp(-iH_Z) exp(-iH_X) exactly (design §6).
(b) As dt -> 0 the one-step error vs exp(-iH dt) scales as dt^2 (first-order Trotter).
(c) Ordering probes: the Neel preparation lands on the exact little-endian basis
    index, and circuit-based <Z_pi>/L after prep + one step matches the dense
    matrix computation. These catch site-ordering reversals, which the unitary
    tests alone cannot (the MFIM is reflection-symmetric).
"""

import numpy as np
import pytest
from qiskit.quantum_info import Operator, Statevector
from scipy.linalg import expm

# macOS Accelerate BLAS emits spurious divide-by-zero/overflow/invalid
# RuntimeWarnings on complex matmul (numpy 2.2.6, this machine). Filtered for THIS
# module only. Defense: the factorization and expectation tests assert the affected
# values to atol<=1e-10; the convergence test asserts a RATIO, so it additionally
# asserts finiteness and positivity of both error norms explicitly below.
pytestmark = pytest.mark.filterwarnings(
    "ignore:(divide by zero|overflow|invalid value) encountered in matmul:RuntimeWarning"
)

from zne_scars.hamiltonian import (
    mfim_hamiltonian,
    mfim_terms,
    neel_state_index,
    neel_state_vector,
)
from zne_scars.observables import staggered_magnetization_density_op, z_pi_matrix
from zne_scars.trotter import build_circuit, neel_preparation


def test_one_step_equals_exact_factor_product():
    """Design §6, Paper Eq. (1.3): U(dt) = e^{-iH_ZZ dt} e^{-iH_Z dt} e^{-iH_X dt}."""
    for num_sites, dt in ((4, 1.0), (6, 1.0), (4, 0.3)):
        h_zz, h_z, h_x = mfim_terms(num_sites)
        expected = expm(-1j * dt * h_zz) @ expm(-1j * dt * h_z) @ expm(-1j * dt * h_x)
        circuit = build_circuit(num_sites, 1, dt=dt, include_preparation=False)
        assert np.allclose(Operator(circuit).data, expected, atol=1e-10)


def test_small_dt_second_order_convergence():
    """First-order Trotter: one-step error vs expm(-iH dt) shrinks ~ dt^2."""
    num_sites = 4
    h = mfim_hamiltonian(num_sites)

    def step_error(dt):
        circuit = build_circuit(num_sites, 1, dt=dt, include_preparation=False)
        return np.linalg.norm(Operator(circuit).data - expm(-1j * dt * h), 2)

    err_dt, err_half = step_error(0.1), step_error(0.05)
    # Explicit finiteness/positivity: this test asserts a ratio, so the usual
    # atol-on-values defense against the filtered BLAS warnings does not apply.
    assert np.isfinite(err_dt) and np.isfinite(err_half)
    assert err_dt > 0 and err_half > 0
    ratio = err_dt / err_half
    assert 3.0 < ratio < 5.0, f"expected ~4 (O(dt^2)); got {ratio}"


def test_neel_preparation_hits_exact_basis_index():
    """Design §4: |Z2> site-ordered |010101> is Qiskit index 0b101010 = 42 at L=6."""
    num_sites = 6
    state = Statevector(neel_preparation(num_sites))
    index = neel_state_index(num_sites)
    assert index == 42
    amplitudes = np.zeros(2**num_sites)
    amplitudes[index] = 1.0
    assert np.allclose(state.data, amplitudes, atol=1e-12)


def test_circuit_expectation_matches_matrix_evolution():
    """Prep + one step: circuit <Z_pi>/L equals the dense-matrix value (ordering probe)."""
    num_sites, dt = 6, 1.0
    circuit = build_circuit(num_sites, 1, dt=dt)
    circuit_value = float(
        Statevector(circuit)
        .expectation_value(staggered_magnetization_density_op(num_sites))
        .real
    )
    h_zz, h_z, h_x = mfim_terms(num_sites)
    u = expm(-1j * dt * h_zz) @ expm(-1j * dt * h_z) @ expm(-1j * dt * h_x)
    evolved = u @ neel_state_vector(num_sites)
    z_pi_diagonal = np.real(np.diag(z_pi_matrix(num_sites)))  # Z_pi is diagonal
    matrix_value = float(np.sum(np.abs(evolved) ** 2 * z_pi_diagonal) / num_sites)
    np.testing.assert_allclose(circuit_value, matrix_value, atol=1e-10)
