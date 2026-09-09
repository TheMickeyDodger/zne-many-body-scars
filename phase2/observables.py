"""Observable weights over the 2^L computational-basis outcomes (prereg §4.5, EQ-B1).

Outcome index i is the integer value of the Qiskit-ordered count string
b_{L-1}...b_0 (qubit 0 = site 1 is the least-significant bit, design.md §4).
Z_s = +1 for bit value 0. All five raw quantities are linear in the outcome
probabilities, so a value is `p @ W` with W the [2^L, 5] weight matrix.
"""
from __future__ import annotations

import numpy as np

RAW_QUANTITIES = ("ZPI", "PRET", "M_I", "M_J", "M_IJ")
RAW_INDEX = {q: i for i, q in enumerate(RAW_QUANTITIES)}


def central_site(L: int) -> int:
    """i* = L/2 (site 2, 3, 4 for L = 4, 6, 8)."""
    return L // 2


def z_of_site(L: int, site: int) -> np.ndarray:
    idx = np.arange(2**L)
    bit = (idx >> (site - 1)) & 1
    return np.where(bit == 0, 1.0, -1.0)


def neel_index(L: int) -> int:
    """|Z2> = |0101...>_site: even sites carry |1>, i.e. bits s-1 for even s."""
    return sum(1 << (s - 1) for s in range(2, L + 1, 2))


def state_index_from_site_string(site_string: str) -> int:
    """Site-ordered bitstring (site 1 first) -> outcome index."""
    L = len(site_string)
    return sum(int(site_string[s - 1]) << (s - 1) for s in range(1, L + 1))


def count_string_of_index(L: int, index: int) -> str:
    return format(index, f"0{L}b")


def weight_matrix(L: int, return_index: int | None = None) -> np.ndarray:
    """[2^L, 5] weights for ZPI, PRET, M_I, M_J, M_IJ. `return_index` is the
    outcome index of the state whose return probability PRET is (default |Z2>)."""
    if return_index is None:
        return_index = neel_index(L)
    dim = 2**L
    w = np.zeros((dim, 5))
    zpi = np.zeros(dim)
    for s in range(1, L + 1):
        zpi += ((-1) ** s) * z_of_site(L, s)
    w[:, 0] = zpi / L
    w[return_index, 1] = 1.0
    i_star = central_site(L)
    zi, zj = z_of_site(L, i_star), z_of_site(L, i_star + 1)
    w[:, 2], w[:, 3], w[:, 4] = zi, zj, zi * zj
    return w


def mloc_sign(L: int) -> float:
    return float((-1) ** central_site(L))


def counts_to_vector(counts: dict[str, int], L: int) -> np.ndarray:
    v = np.zeros(2**L, dtype=np.int64)
    for key, c in counts.items():
        v[int(key.replace(" ", ""), 2)] += int(c)
    return v


def values_from_probabilities(p: np.ndarray, W: np.ndarray) -> np.ndarray:
    """p: [..., 2^L] probabilities -> [..., 5] raw quantities."""
    return p @ W
