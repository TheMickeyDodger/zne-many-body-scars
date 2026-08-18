"""Two-tier depolarizing noise model (design.md §8).

p1 = 1e-3 on sx, sxdg, x; p2 = 1e-2 on cx; rz noiseless (virtual on IBM devices).
sxdg is covered defensively: Aer noise is keyed by instruction name and
SXGate.inverse() is SXdgGate, so inverse-inserting tools must not be able to
smuggle in a noiseless single-qubit instruction (design §8, test T6).
"""

from __future__ import annotations

from dataclasses import dataclass

from qiskit_aer.noise import NoiseModel, depolarizing_error

P1_DEFAULT = 1e-3
P2_DEFAULT = 1e-2


@dataclass(frozen=True)
class NoiseConfig:
    """Single source of truth for the §8 rates. Threaded to BOTH the executor's
    NoiseModel and the lambda_eff exposure weights (§10). Which disagreements
    the arms runner detects — and the declaration-honesty gap that remains for
    custom executors — is defined in zne_runner.resolve_noise_config; for
    executors built from this object (make_density_matrix_executor) the tag and
    the simulated model share one config, so no gap exists on that path."""

    p1: float = P1_DEFAULT
    p2: float = P2_DEFAULT

    def build_model(self) -> NoiseModel:
        return build_noise_model(self.p1, self.p2)
ONE_QUBIT_NOISY_GATES = ("sx", "sxdg", "x")
TWO_QUBIT_NOISY_GATES = ("cx",)
CLEAN_GATES = ("rz",)


def build_noise_model(p1: float = P1_DEFAULT, p2: float = P2_DEFAULT) -> NoiseModel:
    model = NoiseModel(basis_gates=list(CLEAN_GATES + ONE_QUBIT_NOISY_GATES + TWO_QUBIT_NOISY_GATES))
    if p1 > 0:
        model.add_all_qubit_quantum_error(
            depolarizing_error(p1, 1), list(ONE_QUBIT_NOISY_GATES)
        )
    if p2 > 0:
        model.add_all_qubit_quantum_error(
            depolarizing_error(p2, 2), list(TWO_QUBIT_NOISY_GATES)
        )
    return model


def noisy_instruction_names(model: NoiseModel) -> set[str]:
    """Instruction names the model attaches noise to."""
    return set(model.noise_instructions)
