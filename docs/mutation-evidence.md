# Mutation-Sensitivity Evidence

Each entry below was generated mechanically by a runner script: apply the stated single mutation to the working tree, run the named test(s), capture the REAL failing output verbatim, revert, and continue. The final section proves the tree was fully reverted and the whole suite passes. Regenerate at any time by repeating the edits shown and running the named tests.

**Mutation count (mechanical, from this file's entries): 13**

## T1: boundary longitudinal coefficient -V changed to -2V (bulk/boundary distinction erased)

- **File:** `src/zne_scars/hamiltonian.py`
- **Mutation:** replace
  ```python
        coeff = -v if i in (1, num_sites) else -2.0 * v
  ```
  with
  ```python
        coeff = -2.0 * v if i in (1, num_sites) else -2.0 * v  # MUTATION
  ```
- **Test(s):** `tests/test_hamiltonian.py`
- **Captured failing output (verbatim excerpt):**

  ```
  E           AssertionError: Z coeff wrong on site 1
  E           assert -2.0 == -1.0 ± 1.0e-12
  E             
  E             comparison failed
  E             Obtained: -2.0
  E             Expected: -1.0 ± 1.0e-12
  3 failed, 6 passed in 0.16s
  ```

## T2-sign: sign flip in the R_ZZ angle (H_ZZ term implemented with the wrong sign)

- **File:** `src/zne_scars/trotter.py`
- **Mutation:** replace
  ```python
                2.0 * v * dt,
  ```
  with
  ```python
                -2.0 * v * dt,  # MUTATION
  ```
- **Test(s):** `tests/test_trotter.py`
- **Captured failing output (verbatim excerpt):**

  ```
  E           assert False
  E            +  where False = <function allclose at 0x1062698f0>(array([[-0.81107673+3.66862707e-01j,  0.08977743+1.98484024e-01j,\n         0.08977743+1.98484024e-01j,  0.04857236-2.1...7765 +7.52310788e-03j, -0.03074211+2.15663668e-01j,\n        -0.03074211+2.15663668e-01j, -0.88127891-1.25623261e-01j]]), array([[-0.88127891+1.25623261e-01j,  0.03074211+2.15663668e-01j,\n         0.03074211+2.15663668e-01j,  0.0527765 -7.5...57236+2.19700372e-02j, -0.08977743+1.98484024e-01j,\n        -0.08977743+1.98484024e-01j, -0.81107673-3.66862707e-01j]]), atol=1e-10)
  E            +    where <function allclose at 0x1062698f0> = np.allclose
  E            +    and   array([[-0.81107673+3.66862707e-01j,  0.08977743+1.98484024e-01j,\n         0.08977743+1.98484024e-01j,  0.04857236-2.1...7765 +7.52310788e-03j, -0.03074211+2.15663668e-01j,\n        -0.03074211+2.15663668e-01j, -0.88127891-1.25623261e-01j]]) = Operator([[-0.81107673+3.66862707e-01j,  0.08977743+1.98484024e-01j,\n            0.08977743+1.98484024e-01j,  0.048572...-0.03074211+2.15663668e-01j, -0.88127891-1.25623261e-01j]],\n         input_dims=(2, 2, 2, 2), output_dims=(2, 2, 2, 2)).data
  E            +      where Operator([[-0.81107673+3.66862707e-01j,  0.08977743+1.98484024e-01j,\n            0.08977743+1.98484024e-01j,  0.048572...-0.03074211+2.15663668e-01j, -0.88127891-1.25623261e-01j]],\n         input_dims=(2, 2, 2, 2), output_dims=(2, 2, 2, 2)) = Operator(<qiskit.circuit.quantumcircuit.QuantumCircuit object at 0x1075a0dd0>)
  E       AssertionError: expected ~4 (O(dt^2)); got 1.9775424990162136
  2 failed, 2 passed in 0.32s
  ```

## T2-ordering: site-to-qubit mapping reversed: q_{i-1} -> q_{L-i}

- **File:** `src/zne_scars/trotter.py`
- **Mutation:** replace
  ```python
    return site - 1
  ```
  with
  ```python
    return num_sites - site  # MUTATION
  ```
- **Test(s):** `tests/test_trotter.py`
- **Captured failing output (verbatim excerpt):**

  ```
  E       assert False
  E        +  where False = <function allclose at 0x106f850f0>(array([0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j,\n       0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, ...0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j,\n       0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j]), array([0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,\n       0., 0., 0., 0., 0., 0., 0., 0., 0., ...0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0.,\n       0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]), atol=1e-12)
  E        +    where <function allclose at 0x106f850f0> = np.allclose
  E        +    and   array([0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j,\n       0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, ...0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j,\n       0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j]) = Statevector([0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j,\n             0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0...     0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j,\n             0.+0.j],\n            dims=(2, 2, 2, 2, 2, 2)).data
  E       AssertionError: 
  E       Not equal to tolerance rtol=1e-07, atol=1e-10
  2 failed, 2 passed in 0.19s
  ```

## T3: staggering phase (-1)^i dropped from Z_pi

- **File:** `src/zne_scars/observables.py`
- **Mutation:** replace
  ```python
    return -1 if site % 2 else 1
  ```
  with
  ```python
    return 1  # MUTATION
  ```
- **Test(s):** `tests/test_observables.py`
- **Captured failing output (verbatim excerpt):**

  ```
  E       assert 0.0 == -1.0 ± 1.0e-06
  E         
  E         comparison failed
  E         Obtained: 0.0
  E         Expected: -1.0 ± 1.0e-06
  E       assert 0.0 == -1.0 ± 1.0e-12
  2 failed, 5 passed in 0.23s
  ```

## T4: nonzero noise rate leaking into the zero-noise executor path

- **File:** `src/zne_scars/executors.py`
- **Mutation:** replace
  ```python
    circ.save_expectation_value(observable, list(range(circ.num_qubits)))
    simulator = AerSimulator(method="density_matrix", noise_model=noise_model)
  ```
  with
  ```python
    circ.save_expectation_value(observable, list(range(circ.num_qubits)))
    if noise_model is None:  # MUTATION: noise leaks into the zero-noise path
        from .noise import build_noise_model
        noise_model = build_noise_model()
    simulator = AerSimulator(method="density_matrix", noise_model=noise_model)
  ```
- **Test(s):** `tests/test_zne.py::test_t4_zne_recovers_exact_value_at_zero_noise`
- **Captured failing output (verbatim excerpt):**

  ```
  E           assert np.float64(-0...5619734334869) == -0.7350297486636157 ± 1.0e-08
  E             
  E             comparison failed
  E             Obtained: -0.7285619734334869
  E             Expected: -0.7350297486636157 ± 1.0e-08
  1 failed in 1.29s
  ```

## T5: fold count off by one (one extra cx appended after fold_all)

- **File:** `src/zne_scars/zne_runner.py`
- **Mutation:** replace
  ```python
    return fold_all(circuit, scale_factor)
  ```
  with
  ```python
    folded = fold_all(circuit, scale_factor)
    folded.cx(0, 1)  # MUTATION: fold count off by one
    return folded
  ```
- **Test(s):** `tests/test_zne.py::test_t5_fold_all_triples_cx_count`
- **Captured failing output (verbatim excerpt):**

  ```
  E       assert 37 == (3 * 12)
  E        +  where 37 = two_qubit_count(<qiskit.circuit.quantumcircuit.QuantumCircuit object at 0x1115ff320>)
  1 failed in 0.80s
  ```

## T6: fidelities dict removed (single-qubit gates become foldable; sxdg leakage)

- **File:** `src/zne_scars/zne_runner.py`
- **Mutation:** replace
  ```python
    return fold_gates_at_random(
        circuit, scale_factor, seed=seed, fidelities=dict(FIDELITIES)
    )
  ```
  with
  ```python
    return fold_gates_at_random(circuit, scale_factor, seed=seed)  # MUTATION
  ```
- **Test(s):** `tests/test_zne.py::test_t6_restricted_folding_exact_grid_counts`
- **Captured failing output (verbatim excerpt):**

  ```
  E               AssertionError: single-qubit gate rz was folded at scale 1.5 (fidelities={'single': 1.0, 'double': 0.99})
  E               assert 58 == 38
  E                +  where 58 = <built-in method get of dict object at 0x11052dcc0>('rz', 0)
  E                +    where <built-in method get of dict object at 0x11052dcc0> = {'rz': 58, 'sx': 21, 'cx': 14, 'sxdg': 5, ...}.get
  E                +  and   38 = <built-in method get of dict object at 0x104c6d280>('rz', 0)
  E                +    where <built-in method get of dict object at 0x104c6d280> = {'rz': 38, 'sx': 16, 'cx': 12, 'x': 2}.get
  1 failed in 0.82s
  ```

## G1: every fold target underfolded by two folds (lambda - 1/3)

- **File:** `src/zne_scars/zne_runner.py`
- **Mutation:** replace
  ```python
    return fold_gates_at_random(
        circuit, scale_factor, seed=seed, fidelities=dict(FIDELITIES)
    )
  ```
  with
  ```python
    return fold_gates_at_random(
        circuit, scale_factor - 1.0 / 3.0 if scale_factor > 1 else scale_factor,  # MUTATION
        seed=seed, fidelities=dict(FIDELITIES)
    )
  ```
- **Test(s):** `tests/test_zne.py::test_t6_restricted_folding_exact_grid_counts`
- **Captured failing output (verbatim excerpt):**

  ```
  E           assert 14 == 18
  1 failed in 0.81s
  ```

## G2: fold seed dropped (seed=None)

- **File:** `src/zne_scars/zne_runner.py`
- **Mutation:** replace
  ```python
    return fold_gates_at_random(
        circuit, scale_factor, seed=seed, fidelities=dict(FIDELITIES)
    )
  ```
  with
  ```python
    return fold_gates_at_random(
        circuit, scale_factor, seed=None, fidelities=dict(FIDELITIES)  # MUTATION
    )
  ```
- **Test(s):** `tests/test_zne.py::test_t6_seed_threading_is_real`
- **Captured failing output (verbatim excerpt):**

  ```
  E       AssertionError: same seed must reproduce the identical folded circuit
  E       assert <qiskit.circu...t 0x11cb38fe0> == <qiskit.circu...t 0x11cb76240>
  E         
  E         Use -v to get more diff
  1 failed in 0.89s
  ```

## G3: linear_intercept returns the slope instead of the zero-noise intercept

- **File:** `src/zne_scars/zne_runner.py`
- **Mutation:** replace
  ```python
    return float(intercept)
  ```
  with
  ```python
    return float(slope)  # MUTATION
  ```
- **Test(s):** `tests/test_zne.py::test_arms_noiseless_invariance`, `tests/test_zne.py::test_arms_nominal_intercept_matches_mitiq_linear_factory`
- **Captured failing output (verbatim excerpt):**

  ```
  E           assert -4.123264800194356e-16 == -0.7350297486636157 ± 1.0e-08
  E             
  E             comparison failed
  E             Obtained: -4.123264800194356e-16
  E             Expected: -0.7350297486636157 ± 1.0e-08
  E       assert 0.03907117322990235 == -0.7294629924425432 ± 1.0e-09
  2 failed in 0.96s
  ```

## G4: clamp threshold eps ignored (magnitude<=eps values no longer flagged)

- **File:** `src/zne_scars/zne_runner.py`
- **Mutation:** replace
  ```python
    return bool(any(sign * (y - asymptote) <= eps for y in values))
  ```
  with
  ```python
    return bool(any(sign * (y - asymptote) <= 0.0 for y in values))  # MUTATION
  ```
- **Test(s):** `tests/test_zne.py::test_secondary_clamp_detection_mirrors_mitiq`
- **Captured failing output (verbatim excerpt):**

  ```
  E       assert False is True
  E        +  where False = exp_clamp_flag([1.0, 1.5, 2.0], [0.5, 0.2, 1e-07])
  1 failed in 0.80s
  ```

## G5: GIF reverted to bare division (delta denominator rule removed)

- **File:** `src/zne_scars/metrics.py`
- **Mutation:** replace
  ```python
    return improvement_factor(rms_u, rms_m, delta)
  ```
  with
  ```python
    return ImprovementFactor(value=rms_u / rms_m, is_lower_bound=False)  # MUTATION
  ```
- **Test(s):** `tests/test_metrics.py::test_gif_zero_denominator_is_flagged_lower_bound_not_exception`
- **Captured failing output (verbatim excerpt):**

  ```
  E       ZeroDivisionError: float division by zero
  1 failed in 0.03s
  ```

## G6: seed_band uses population (ddof=0) instead of sample (ddof=1) standard deviation

- **File:** `src/zne_scars/metrics.py`
- **Mutation:** replace
  ```python
    std = float(np.std(arr, ddof=1))
  ```
  with
  ```python
    std = float(np.std(arr, ddof=0))  # MUTATION
  ```
- **Test(s):** `tests/test_zne.py::test_arms_ensemble_bands_are_ddof_one`
- **Captured failing output (verbatim excerpt):**

  ```
  E           AssertionError: primary std is not the ddof=1 sample standard deviation
  E           assert 0.0003951606264015269 == 0.00048397095...1578 ± 1.0e-12
  E             
  E             comparison failed
  E             Obtained: 0.0003951606264015269
  E             Expected: 0.0004839709505611578 ± 1.0e-12
  1 failed in 0.92s
  ```

## Revert proof (after all mutations)

```
$ grep -rn MUTATION src/ tests/   (exit 1; no output = no marker left)
(no output)
$ .venv/bin/python -m pytest -q
....................................................                     [100%]
52 passed in 1.37s
```
