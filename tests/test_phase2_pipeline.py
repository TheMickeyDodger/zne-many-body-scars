"""Independent validation of the Phase 2 pipeline pieces against the sealed v0.1.0 code and the
checker's reference arithmetic (small circuits; no bundle written; EXP path not invoked)."""
from __future__ import annotations

import importlib.util
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
pytestmark = pytest.mark.filterwarnings("ignore::RuntimeWarning")  # sealed hamiltonian.py Accelerate matmul warnings

from phase2 import circuits as C, noise as N, simulate as S, references as R  # noqa: E402
from phase2.observables import counts_to_vector, neel_index, values_from_probabilities, weight_matrix, RAW_INDEX  # noqa: E402
from zne_scars.executors import density_matrix_expectation, statevector_expectation  # noqa: E402
from zne_scars.observables import expectation_from_counts, staggered_magnetization_density_op  # noqa: E402

spec = importlib.util.spec_from_file_location("phase2_contract_check", ROOT / "tools/phase2_contract_check.py")
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)


@pytest.mark.parametrize("L", [4, 6])
def test_zpi_weights_agree_with_the_sealed_count_decoder(L):
    rng = np.random.default_rng(0)
    W = weight_matrix(L)
    for _ in range(20):
        counts = {format(i, f"0{L}b"): int(c) for i, c in enumerate(rng.multinomial(8192, rng.dirichlet(np.ones(2**L)))) if c}
        vec = counts_to_vector(counts, L)
        v = values_from_probabilities(vec / vec.sum(), W)
        assert v[RAW_INDEX["ZPI"]] == pytest.approx(expectation_from_counts(counts, L), abs=1e-14)
        assert 0 <= v[RAW_INDEX["PRET"]] <= 1
        assert abs(v[RAW_INDEX["M_IJ"]]) <= 1


def test_pret_index_is_the_neel_count_string():
    assert format(neel_index(4), "04b") == "1010" and format(neel_index(6), "06b") == "101010" and format(neel_index(8), "08b") == "10101010"


@pytest.mark.parametrize("L,n", [(4, 3), (6, 2)])
def test_dm_probability_path_matches_sealed_expectation_path(L, n):
    base = C.base_circuit(L, n)
    nm = N.dep(1.0)
    W = weight_matrix(L)
    p = S.dm_probabilities(base, nm)
    zpi = values_from_probabilities(p, W)[RAW_INDEX["ZPI"]]
    ref = density_matrix_expectation(base, staggered_magnetization_density_op(L), nm)
    assert zpi == pytest.approx(ref, abs=1e-12)
    e0 = values_from_probabilities(S.statevector_probabilities(base), W)[RAW_INDEX["ZPI"]]
    assert e0 == pytest.approx(statevector_expectation(base, staggered_magnetization_density_op(L)), abs=1e-12)


def test_global_fold_matches_checker_arithmetic_and_inverse_rules():
    base = C.base_circuit(4, 2)
    ops = [ci.operation.name for ci in base.data]
    for lam in (1.0, 1.25, 1.5, 1.75, 2.0, 3.0):
        folded = C.fold_global(base, lam)
        names = [ci.operation.name for ci in folded.data]
        ref, lam_r, lam_1 = cc.fold_global_counts(ops, lam)
        assert names == ref
        lr, lr1 = C.realized_scales(base, folded)
        assert lr == pytest.approx(lam_r) and lr1 == pytest.approx(lam_1)
    # unitary identity of the fold: the folded circuit equals the base circuit noiselessly
    from qiskit.quantum_info import Statevector
    for lam in (1.5, 2.0):
        assert np.allclose(Statevector(C.fold_global(base, lam)).data, Statevector(base).data, atol=1e-10)


def test_local_fold_is_deterministic_and_folds_only_cx():
    base = C.base_circuit(4, 2)
    a = C.fold_local(base, 1.5, 1003); b = C.fold_local(base, 1.5, 1003)
    assert C.instructions_record(a) == C.instructions_record(b)
    oa, ob = C.op_counts(base), C.op_counts(a)
    assert ob["cx"] > oa["cx"] and all(ob.get(g, 0) == oa.get(g, 0) for g in ("sx", "x", "rz"))
    C.check_every_instruction_has_channel(a, {"sx", "sxdg", "x", "cx"})


def test_shot_counts_are_seed_deterministic_and_sum_to_shots():
    base = C.fold_local(C.base_circuit(4, 2), 2.0, 1000)
    nm = N.dep(1.0)
    v1, n1, m1 = S.shot_counts(base, nm, 4000210, 8192, method="density_matrix")
    v2, _, _ = S.shot_counts(base, nm, 4000210, 8192, method="density_matrix")
    v3, _, _ = S.shot_counts(base, nm, 4000211, 8192, method="density_matrix")
    assert np.array_equal(v1, v2) and not np.array_equal(v1, v3) and n1 == 8192 and m1 == "density_matrix"


def test_readout_transform_is_stochastic_and_matches_single_qubit_case():
    T = N.classical_readout_transform(1, N.readout_matrix(0.02))
    assert np.allclose(T, N.readout_matrix(0.02))
    T4 = N.classical_readout_transform(4, N.readout_matrix(0.02))
    assert np.allclose(T4.sum(axis=0), 1.0)
    p = np.zeros(16); p[0] = 1.0
    assert (T4 @ p)[0] == pytest.approx(0.98**4)


def test_ed_reference_matches_recorded_v010_value_at_L6_n19():
    ed, resid, orth = R.ed_curve(6, 19)
    assert resid <= 1e-10 and orth <= 1e-10
    assert ed[18, RAW_INDEX["ZPI"]] == pytest.approx(-0.8309868670981677, abs=1e-12)
