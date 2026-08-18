"""T1 (design.md §17): H is Hermitian; boundary coefficients exactly -V, bulk -2V.

Coefficients are extracted by Pauli-trace projection, coeff(P) = Tr(P H) / 2^L,
which is exact because distinct Pauli strings are trace-orthogonal.
"""

import numpy as np
import pytest

# macOS Accelerate BLAS emits spurious divide-by-zero/overflow/invalid
# RuntimeWarnings on complex matmul/kron (numpy 2.2.6, this machine). Filtered for
# THIS module only. Defense: every quantity computed through those operations here
# is itself asserted — hermiticity to atol 1e-12 and each Pauli-trace coefficient
# to abs=1e-12 — so genuine numerical corruption fails the assertions.
pytestmark = pytest.mark.filterwarnings(
    "ignore:(divide by zero|overflow|invalid value) encountered in matmul:RuntimeWarning"
)

from zne_scars.hamiltonian import (
    OMEGA_DEFAULT,
    PAULI_X,
    PAULI_Z,
    V_DEFAULT,
    mfim_hamiltonian,
    site_operator,
)

L_VALUES = (4, 5, 6)


def _pauli_coeff(h: np.ndarray, pauli_string: np.ndarray, num_sites: int) -> float:
    coeff = np.trace(pauli_string @ h) / 2**num_sites
    assert abs(coeff.imag) < 1e-12
    return float(coeff.real)


@pytest.mark.parametrize("num_sites", L_VALUES)
def test_hermitian(num_sites):
    h = mfim_hamiltonian(num_sites)
    assert np.allclose(h, h.conj().T, atol=1e-12)


@pytest.mark.parametrize("num_sites", L_VALUES)
def test_boundary_and_bulk_longitudinal_field(num_sites):
    """Design §3: -V Z on sites 1 and L (halved boundary field), -2V Z in the bulk."""
    h = mfim_hamiltonian(num_sites)
    for site in range(1, num_sites + 1):
        expected = -V_DEFAULT if site in (1, num_sites) else -2.0 * V_DEFAULT
        coeff = _pauli_coeff(h, site_operator(PAULI_Z, site, num_sites), num_sites)
        assert coeff == pytest.approx(expected, abs=1e-12), f"Z coeff wrong on site {site}"


@pytest.mark.parametrize("num_sites", L_VALUES)
def test_zz_and_transverse_coefficients(num_sites):
    """Design §3: +V on every Z_i Z_{i+1} bond, Omega on every X_i."""
    h = mfim_hamiltonian(num_sites)
    for site in range(1, num_sites):
        zz = site_operator(PAULI_Z, site, num_sites) @ site_operator(
            PAULI_Z, site + 1, num_sites
        )
        assert _pauli_coeff(h, zz, num_sites) == pytest.approx(V_DEFAULT, abs=1e-12)
    for site in range(1, num_sites + 1):
        x = site_operator(PAULI_X, site, num_sites)
        assert _pauli_coeff(h, x, num_sites) == pytest.approx(OMEGA_DEFAULT, abs=1e-12)
