"""Base circuits, folding variants and realized scales (prereg §4.3, contract §C4.2).

Base circuits come from the sealed v0.1.0 builder and transpiler (read-only).
LOCAL folding is the sealed `fold_two_qubit` (mitiq fold_gates_at_random with
fidelities {single: 1.0, double: 0.99}). GLOBAL folding is the §C4.2 arithmetic
on the transpiled operation list without measurements.
"""
from __future__ import annotations

from functools import lru_cache

from qiskit import QuantumCircuit
from qiskit.circuit.library import CXGate, RZGate, SXGate, SXdgGate, XGate

from zne_scars.trotter import build_circuit, site_to_qubit, transpile_to_basis
from zne_scars.zne_runner import fold_two_qubit

NOISY_1Q = ("sx", "sxdg", "x")
INSTRUCTION_NAMES = ("rz", "sx", "sxdg", "x", "cx")


def preparation_from_site_string(L: int, site_string: str) -> QuantumCircuit:
    """X gates on the sites whose site-ordered bit is '1' (site 1 first)."""
    qc = QuantumCircuit(L)
    for s in range(1, L + 1):
        if site_string[s - 1] == "1":
            qc.x(site_to_qubit(s, L))
    return qc


@lru_cache(maxsize=None)
def base_circuit(L: int, n: int, site_string: str | None = None) -> QuantumCircuit:
    """Transpiled base circuit for (L, n): Neel preparation (default) or the given
    product state, followed by n Trotter steps; basis {rz, sx, x, cx}, opt 0, seed 7."""
    if site_string is None:
        raw = build_circuit(L, n)
    else:
        raw = preparation_from_site_string(L, site_string)
        raw.compose(build_circuit(L, n, include_preparation=False), inplace=True)
    return transpile_to_basis(raw)


def op_counts(circ: QuantumCircuit) -> dict[str, int]:
    return {k: int(v) for k, v in circ.count_ops().items() if k not in ("measure", "barrier")}


def cx_count(circ: QuantumCircuit) -> int:
    return int(circ.count_ops().get("cx", 0))


def one_q_noisy_count(circ: QuantumCircuit) -> int:
    ops = circ.count_ops()
    return sum(int(ops.get(g, 0)) for g in NOISY_1Q)


def realized_scales(base: QuantumCircuit, folded: QuantumCircuit) -> tuple[float, float]:
    """(lambda_r on cx, lambda_r^(1) on noisy single-qubit gates), EQ-B2."""
    cb, c1 = cx_count(base), one_q_noisy_count(base)
    if cb == 0:
        raise ValueError("base circuit has no cx")
    return cx_count(folded) / cb, one_q_noisy_count(folded) / c1


def fold_local(base: QuantumCircuit, lam: float, seed: int) -> QuantumCircuit:
    return fold_two_qubit(base, lam, seed=seed)


def _inverse(instr):
    name = instr.operation.name
    if name == "cx":
        return CXGate(), instr.qubits
    if name == "x":
        return XGate(), instr.qubits
    if name == "sx":
        return SXdgGate(), instr.qubits
    if name == "sxdg":
        return SXGate(), instr.qubits
    if name == "rz":
        return RZGate(-float(instr.operation.params[0])), instr.qubits
    raise ValueError(f"no inverse rule for {name}")


def fold_global(base: QuantumCircuit, lam: float) -> QuantumCircuit:
    """§C4.2: U, q copies of (U^dag, U), then (S^dag, S) with S the suffix of
    n_p = round(f * m / 2) operations, q, f = divmod(lam - 1, 2)."""
    ops = [ci for ci in base.data if ci.operation.name not in ("measure", "barrier")]
    if len(ops) != len(base.data):
        raise ValueError("base circuit must carry no measurements or barriers")
    q, f = divmod(lam - 1, 2)
    q = int(q)
    out = QuantumCircuit(base.num_qubits)

    def append_list(lst):
        for ci in lst:
            out.append(ci.operation, ci.qubits)

    def append_dag(lst):
        for ci in reversed(lst):
            gate, qubits = _inverse(ci)
            out.append(gate, qubits)

    append_list(ops)
    for _ in range(q):
        append_dag(ops)
        append_list(ops)
    if f > 0:
        n_p = round(f * len(ops) / 2)
        suffix = ops[len(ops) - n_p:] if n_p > 0 else []
        append_dag(suffix)
        append_list(suffix)
    return out


def fold(base: QuantumCircuit, folding: str, lam: float, seed: int) -> QuantumCircuit:
    if folding == "LOCAL":
        return fold_local(base, lam, seed)
    if folding == "GLOBAL":
        return fold_global(base, lam)
    raise ValueError(folding)


def instructions_record(circ: QuantumCircuit) -> list[dict]:
    """A-CIRC style list: name, Qiskit qubit indices, params in radians."""
    rec = []
    for ci in circ.data:
        rec.append({"name": ci.operation.name,
                    "qubits": [circ.find_bit(q).index for q in ci.qubits],
                    "params": [float(p) for p in ci.operation.params]})
    return rec


def check_every_instruction_has_channel(circ: QuantumCircuit, noisy_names: set[str]) -> None:
    """T6-style: every instruction is rz or carries a channel."""
    bad = {ci.operation.name for ci in circ.data} - noisy_names - {"rz", "measure", "barrier"}
    if bad:
        raise ValueError(f"instructions without a channel: {sorted(bad)}")
