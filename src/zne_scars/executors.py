"""Executors: deterministic density-matrix primary, seeded shot-based secondary,
and the exact noiseless statevector reference (design.md §8, §12, §16).

NOTE: no `from __future__ import annotations` here. Mitiq's Executor detects the
executor's return type from its annotation object; PEP 563 stringized annotations
("float" instead of float) break that detection (verified against mitiq 1.0.0:
FloatLike membership is checked by object identity, and the string "float" is
not in the list).
"""

from collections.abc import Callable

from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel

from .noise import NoiseConfig
from .observables import expectation_from_counts

SHOTS_DEFAULT = 8192  # design §8 (Paper Sec. III and the Example both use 8192)


def statevector_expectation(circuit: QuantumCircuit, observable: SparsePauliOp) -> float:
    """Exact noiseless expectation of the (transpiled) circuit — the primary
    comparison target E_0 (design §12.1)."""
    return float(Statevector(circuit).expectation_value(observable).real)


def density_matrix_expectation(
    circuit: QuantumCircuit,
    observable: SparsePauliOp,
    noise_model: NoiseModel | None = None,
) -> float:
    """Deterministic noisy expectation Tr[rho O] via AerSimulator(method='density_matrix')
    with a save_expectation_value instruction — zero shot noise (design §8)."""
    circ = circuit.copy()
    circ.save_expectation_value(observable, list(range(circ.num_qubits)))
    simulator = AerSimulator(method="density_matrix", noise_model=noise_model)
    result = simulator.run(circ).result()
    return float(result.data(0)["expectation_value"])


def shot_expectation(
    circuit: QuantumCircuit,
    noise_model: NoiseModel | None,
    seed_simulator: int,
    shots: int = SHOTS_DEFAULT,
) -> float:
    """Seeded shot-based <Z_pi>/L from computational-basis counts (design §8, §16)."""
    circ = circuit.copy()
    circ.measure_all()
    simulator = AerSimulator(noise_model=noise_model)
    result = simulator.run(circ, shots=shots, seed_simulator=seed_simulator).result()
    return expectation_from_counts(result.get_counts(0), circuit.num_qubits)


def make_density_matrix_executor(
    observable: SparsePauliOp, noise: NoiseConfig | None
) -> Callable[[QuantumCircuit], float]:
    """Executor closure for mitiq's execute_with_zne and the §10 arms runner.

    Takes a NoiseConfig (not a bare NoiseModel) so the same rates build the
    simulated noise AND are carried on the closure as `.noise_config`, letting
    zne_runner detect a lambda_eff/executor rate mismatch (F9): the config is
    the single source of truth. Pass None for the noiseless reference path.
    """
    model = noise.build_model() if noise is not None else None

    def executor(circuit: QuantumCircuit) -> float:
        return density_matrix_expectation(circuit, observable, model)

    executor.noise_config = noise  # type: ignore[attr-defined]
    return executor


def declare_noise(
    executor: Callable[[QuantumCircuit], float], noise: NoiseConfig | None
) -> Callable[[QuantumCircuit], float]:
    """Explicitly declare a custom executor's simulated noise configuration
    (F9): tag with the NoiseConfig it simulates, or with None if it is genuinely
    noiseless. zne_runner refuses to compute lambda_eff for undeclared executors.
    The declaration is the caller's assertion — it must match what the executor
    actually simulates."""
    executor.noise_config = noise  # type: ignore[attr-defined]
    return executor
