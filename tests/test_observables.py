"""T3 (design.md §17): <Z_pi>/L = -1 on |Z2> and +1 on |Z2'>; counts-based and
statevector/density-matrix estimators agree on random states."""

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from zne_scars.executors import density_matrix_expectation
from zne_scars.observables import (
    expectation_from_counts,
    staggered_magnetization_density_op,
    z_pi_matrix,
)
from zne_scars.trotter import neel_preparation

L = 6


def test_neel_state_extremal_values_from_counts():
    """Design §5: <Z_pi>/L = -1 on |Z2> (Qiskit count key '101010') and +1 on |Z2'>."""
    assert expectation_from_counts({"101010": 8192}, L) == pytest.approx(-1.0)
    assert expectation_from_counts({"010101": 8192}, L) == pytest.approx(+1.0)


def test_neel_state_extremal_value_from_statevector():
    value = Statevector(neel_preparation(L)).expectation_value(
        staggered_magnetization_density_op(L)
    )
    assert float(value.real) == pytest.approx(-1.0, abs=1e-12)


def test_operator_definitions_agree():
    """SparsePauliOp (Z_pi/L) and the dense z_pi_matrix are the same operator."""
    dense = staggered_magnetization_density_op(L).to_matrix()
    np.testing.assert_allclose(dense, z_pi_matrix(L) / L, atol=1e-12)


def _random_state_circuit(seed: int) -> QuantumCircuit:
    rng = np.random.default_rng(seed)
    circuit = QuantumCircuit(L)
    for q in range(L):
        circuit.rx(float(rng.uniform(0, 2 * np.pi)), q)
        circuit.rz(float(rng.uniform(0, 2 * np.pi)), q)
    for q in range(L - 1):
        circuit.cx(q, q + 1)
    for q in range(L):
        circuit.ry(float(rng.uniform(0, 2 * np.pi)), q)
    return circuit


@pytest.mark.parametrize("seed", [7, 11, 13])
def test_counts_and_matrix_estimators_agree_on_random_states(seed):
    """Feed the exact outcome distribution to the counts decoder: it must reproduce
    the statevector expectation exactly (no shot noise involved)."""
    circuit = _random_state_circuit(seed)
    state = Statevector(circuit)
    exact = float(state.expectation_value(staggered_magnetization_density_op(L)).real)
    counts_value = expectation_from_counts(state.probabilities_dict(), L)
    assert counts_value == pytest.approx(exact, abs=1e-10)


@pytest.mark.parametrize("seed", [7])
def test_density_matrix_estimator_agrees_noiselessly(seed):
    """Noise-free density-matrix executor equals the statevector value."""
    circuit = _random_state_circuit(seed)
    exact = float(
        Statevector(circuit)
        .expectation_value(staggered_magnetization_density_op(L))
        .real
    )
    dm_value = density_matrix_expectation(
        circuit, staggered_magnetization_density_op(L), noise_model=None
    )
    assert dm_value == pytest.approx(exact, abs=1e-10)
