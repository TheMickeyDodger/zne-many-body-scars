"""First-order Trotter circuit for the MFIM (design.md §6-§7, Paper Fig. 1).

One step implements U(dt) = exp(-i H_ZZ dt) exp(-i H_Z dt) exp(-i H_X dt)
(design §6, Paper Eq. (1.3)); the circuit applies the H_X layer first.
Gate angles (design §7, Paper Fig. 1 caption), with R_P(theta) = exp(-i theta P / 2):
  theta^X_i  = 2 Omega dt              (all sites)
  theta^Z_i  = -4 V dt (bulk), -2 V dt (sites 1 and L)
  theta^ZZ_i = 2 V dt                  (all bonds)
"""

from __future__ import annotations

from qiskit import QuantumCircuit, transpile

from .hamiltonian import OMEGA_DEFAULT, V_DEFAULT

BASIS_GATES = ("rz", "sx", "x", "cx")  # design §7
SEED_TRANSPILER = 7  # design §16
DT_DEFAULT = 1.0  # design §6


def site_to_qubit(site: int, num_sites: int) -> int:
    """The single audited site->qubit mapping (design §4): site i -> qubit q_{i-1}."""
    if not 1 <= site <= num_sites:
        raise ValueError(f"site {site} outside 1..{num_sites}")
    return site - 1


def neel_preparation(num_sites: int) -> QuantumCircuit:
    """Prepare |Z2> = |0101...>_site from |0...0>: X on even sites (design §4)."""
    circuit = QuantumCircuit(num_sites)
    for site in range(2, num_sites + 1, 2):
        circuit.x(site_to_qubit(site, num_sites))
    return circuit


def append_trotter_step(
    circuit: QuantumCircuit,
    num_sites: int,
    v: float = V_DEFAULT,
    omega: float = OMEGA_DEFAULT,
    dt: float = DT_DEFAULT,
) -> None:
    """Append one first-order Trotter step (H_X layer, H_Z layer, H_ZZ bond layers)."""
    for site in range(1, num_sites + 1):
        circuit.rx(2.0 * omega * dt, site_to_qubit(site, num_sites))
    for site in range(1, num_sites + 1):
        theta_z = -2.0 * v * dt if site in (1, num_sites) else -4.0 * v * dt
        circuit.rz(theta_z, site_to_qubit(site, num_sites))
    # Bonds (i, i+1) commute within H_ZZ; schedule even-qubit-index bonds, then odd.
    for start in (1, 2):
        for site in range(start, num_sites, 2):
            circuit.rzz(
                2.0 * v * dt,
                site_to_qubit(site, num_sites),
                site_to_qubit(site + 1, num_sites),
            )


def build_circuit(
    num_sites: int,
    num_steps: int,
    v: float = V_DEFAULT,
    omega: float = OMEGA_DEFAULT,
    dt: float = DT_DEFAULT,
    include_preparation: bool = True,
) -> QuantumCircuit:
    """Neel preparation (optional) followed by `num_steps` Trotter steps."""
    circuit = (
        neel_preparation(num_sites) if include_preparation else QuantumCircuit(num_sites)
    )
    for _ in range(num_steps):
        append_trotter_step(circuit, num_sites, v, omega, dt)
    return circuit


def transpile_to_basis(
    circuit: QuantumCircuit, seed_transpiler: int = SEED_TRANSPILER
) -> QuantumCircuit:
    """Transpile to {rz, sx, x, cx} at optimization_level=0 (design §7: load-bearing —
    an optimizing pass would cancel the G G^dagger G folds inserted by ZNE)."""
    return transpile(
        circuit,
        basis_gates=list(BASIS_GATES),
        optimization_level=0,
        seed_transpiler=seed_transpiler,
    )
