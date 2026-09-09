"""Phase 2B noise models (prereg §4.2). DEP reuses the sealed v0.1.0 construction."""
from __future__ import annotations

import numpy as np
from qiskit_aer.noise import (NoiseModel, ReadoutError, amplitude_damping_error,
                              depolarizing_error, phase_damping_error)

from zne_scars.noise import (CLEAN_GATES, ONE_QUBIT_NOISY_GATES, P1_DEFAULT, P2_DEFAULT,
                             TWO_QUBIT_NOISY_GATES, build_noise_model)

P_RO = 0.02
BASIS = list(CLEAN_GATES + ONE_QUBIT_NOISY_GATES + TWO_QUBIT_NOISY_GATES)


def _empty() -> NoiseModel:
    return NoiseModel(basis_gates=BASIS)


def dep(kappa: float, p1: float = P1_DEFAULT, p2: float = P2_DEFAULT) -> NoiseModel:
    return build_noise_model(kappa * p1, kappa * p2)


def deph(kappa: float, p1: float = P1_DEFAULT, p2: float = P2_DEFAULT) -> NoiseModel:
    m = _empty()
    m.add_all_qubit_quantum_error(phase_damping_error(kappa * p1), list(ONE_QUBIT_NOISY_GATES))
    e2 = phase_damping_error(kappa * p2).tensor(phase_damping_error(kappa * p2))
    m.add_all_qubit_quantum_error(e2, list(TWO_QUBIT_NOISY_GATES))
    return m


def amp(p1: float = P1_DEFAULT, p2: float = P2_DEFAULT) -> NoiseModel:
    m = _empty()
    m.add_all_qubit_quantum_error(amplitude_damping_error(p1), list(ONE_QUBIT_NOISY_GATES))
    e2 = amplitude_damping_error(p2).tensor(amplitude_damping_error(p2))
    m.add_all_qubit_quantum_error(e2, list(TWO_QUBIT_NOISY_GATES))
    return m


def readout_matrix(p_ro: float = P_RO) -> np.ndarray:
    return np.array([[1 - p_ro, p_ro], [p_ro, 1 - p_ro]])


def ro_shot(p1: float = P1_DEFAULT, p2: float = P2_DEFAULT, p_ro: float = P_RO) -> NoiseModel:
    m = dep(1.0, p1, p2)
    m.add_all_qubit_readout_error(ReadoutError(readout_matrix(p_ro)))
    return m


def classical_readout_transform(L: int, per_qubit: list[np.ndarray] | np.ndarray) -> np.ndarray:
    """Tensor-product transition matrix T[j, i] = P(read j | true i) over 2^L outcomes
    (qubit 0 least significant); the DM-pipeline readout for RO and CAL."""
    mats = [per_qubit] * L if isinstance(per_qubit, np.ndarray) and per_qubit.shape == (2, 2) else list(per_qubit)
    T = np.array([[1.0]])
    for q in range(L):  # kron order: highest qubit leftmost
        T = np.kron(mats[q], T)
    return T


def model_for(noise_model: str, kappa: float, pipeline: str, p1: float, p2: float):
    """(NoiseModel or None, classical readout matrix or None) for a cell and pipeline."""
    if noise_model == "DEP":
        return dep(kappa, p1, p2), None
    if noise_model == "DEPH":
        return deph(kappa, p1, p2), None
    if noise_model == "AMP":
        return amp(p1, p2), None
    if noise_model == "RO":
        if pipeline == "SHOT":
            return ro_shot(p1, p2), None
        return dep(1.0, p1, p2), readout_matrix()
    raise ValueError(f"{noise_model} not runnable here")
