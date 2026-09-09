"""Aer executions: exact density-matrix probabilities, seeded shot counts, statevector references."""
from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from .observables import counts_to_vector


def dm_probabilities(circ: QuantumCircuit, noise_model) -> np.ndarray:
    """Computational-basis probability vector from the exact density matrix (all qubits)."""
    c = circ.copy()
    c.save_probabilities()
    sim = AerSimulator(method="density_matrix", noise_model=noise_model)
    res = sim.run(c).result()
    return np.asarray(res.data(0)["probabilities"], dtype=float)


def dm_expectation_zpi(circ: QuantumCircuit, observable, noise_model) -> float:
    """v0.1.0-identical save_expectation_value path (Phase 2A cross-check)."""
    c = circ.copy()
    c.save_expectation_value(observable, list(range(c.num_qubits)))
    sim = AerSimulator(method="density_matrix", noise_model=noise_model)
    return float(sim.run(c).result().data(0)["expectation_value"])


def shot_counts(circ: QuantumCircuit, noise_model, seed_simulator: int, shots: int,
                method: str = "density_matrix") -> tuple[np.ndarray, int, str]:
    """Seeded counts over 2^L outcomes (ascending integer of the Qiskit-ordered string),
    the actual shot total, and the Aer method actually used."""
    c = circ.copy()
    c.measure_all()
    sim = AerSimulator(noise_model=noise_model, method=method)
    res = sim.run(c, shots=shots, seed_simulator=seed_simulator).result()
    counts = res.get_counts(0)
    vec = counts_to_vector(counts, circ.num_qubits)
    used = res.results[0].metadata.get("method", method)
    return vec, int(vec.sum()), str(used)


def statevector_probabilities(circ: QuantumCircuit) -> np.ndarray:
    return np.asarray(Statevector(circ).probabilities(), dtype=float)
