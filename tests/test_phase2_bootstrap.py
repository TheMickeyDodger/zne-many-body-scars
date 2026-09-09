"""Stage 1C: deterministic batching, checkpoint and resume of the bootstrap are bit-identical to
an unbatched run, on synthetic count records (no experiment, nothing outside tmp_path).
Only the LIN / QUAD / NONE paths of the frozen order are exercised; the EXP path is not invoked."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from phase2 import bootstrap as BS  # noqa: E402
from phase2.estimators import design, fit_lin_quad, intercept_weights, match_peaks, windows, find_peaks  # noqa: E402
from phase2.observables import weight_matrix  # noqa: E402
from phase2.pilot_stats import make_replicate_fn  # noqa: E402

CHECKER = ROOT / "tools" / "phase2_contract_check.py"
spec = importlib.util.spec_from_file_location("phase2_contract_check", CHECKER)
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)


def _synthetic_cell(L=4, N=12, seed=0):
    """A small synthetic cell: counts[n, k, j, 2^L], shots, realized abscissas with duplicates."""
    rng = np.random.default_rng(seed)
    D = 2**L
    counts = np.zeros((N, 8, 5, D), dtype=np.int64)
    shots = np.full((N, 8, 5), 8192, dtype=np.int64)
    X = np.zeros((N, 8, 5))
    for n in range(N):
        for k in range(8):
            X[n, k] = [1.0, 1.0 + 0.25 * (n % 3 != 0), 1.5, 1.75, 2.0]  # a duplicate abscissa on every third step
            for j in range(5):
                p = rng.dirichlet(np.ones(D) * (0.2 + 0.1 * j))
                counts[n, k, j] = rng.multinomial(8192, p)
    return counts, shots, X


def test_vectorised_multinomial_matches_sequential_contract_wording():
    counts, shots, _ = _synthetic_cell()
    flat = counts.reshape(-1, counts.shape[-1]); p_hat = flat / flat.sum(1, keepdims=True); nvec = shots.reshape(-1)
    for b in (1, 2, 17):
        rng = BS.rng_for(2, 5, b)
        seq = np.stack([rng.multinomial(int(nn), pp) for nn, pp in zip(nvec, p_hat)])
        vec = BS.resample_chunk(counts, shots, 2, 5, b, b + 1)[0].reshape(-1, counts.shape[-1])
        assert np.array_equal(seq, vec)
        # and the checker's per-record reference (list-based) agrees record by record
        rng2 = cc.bootstrap_rng(2, 5, b)
        ref = np.stack([cc.resample_counts(list(map(int, c)), int(nn), rng2) for c, nn in zip(flat, nvec)])
        assert np.array_equal(ref, vec)


def test_closed_form_intercept_weights_match_checker_normal_equations():
    rng = np.random.default_rng(1)
    for _ in range(200):
        x = np.array([1.0, 1.25, 1.5, 1.75, 2.0]) + rng.normal(0, 0.05, 5)
        y = rng.normal(size=5)
        assert intercept_weights(x, 1) @ y == pytest.approx(cc.poly_intercept(list(x), list(y), 1), abs=1e-12)
        assert intercept_weights(x, 2) @ y == pytest.approx(cc.poly_intercept(list(x), list(y), 2), abs=1e-10)
    # rank rule: LIN needs 2 distinct, QUAD 3 distinct; duplicates kept as recorded
    d = design(np.array([[[1.0, 1.0, 2.0, 2.0, 2.0]]]))
    assert d.ok_lin[0, 0] and not d.ok_quad[0, 0] and not d.ok_exp[0, 0] and d.n_distinct[0, 0] == 2
    d3 = design(np.array([[[1.0, 1.0, 1.5, 2.0, 2.0]]]))
    assert d3.ok_quad[0, 0] and d3.ok_exp[0, 0]
    y = np.array([0.9, 0.85, 0.6, 0.3, 0.35])
    assert intercept_weights(d3.X[0, 0], 1) @ y == pytest.approx(cc.poly_intercept([1, 1, 1.5, 2, 2], list(y), 1), abs=1e-12)


def test_peak_matching_matches_checker_reference_including_ties_and_fallback():
    rng = np.random.default_rng(3)
    pts = list(range(15, 24))
    for _ in range(300):
        curve = rng.normal(size=48)
        if rng.random() < 0.3:
            curve[17] = curve[18]  # tie
        ref = cc.match_peak({n: float(curve[n - 1]) for n in pts}, pts, polarity=-1.0)
        amp, t, da, dt = match_peaks(curve[None, :], pts, -1.0)
        assert da[0] and amp[0] == ref["amplitude"]
        if "NO_INTERIOR_PEAK" in ref["flags"] or "INTERP_FALLBACK" in ref["flags"]:
            assert not dt[0] and np.isnan(t[0])
        else:
            assert dt[0] and t[0] == pytest.approx(ref["timing"], abs=1e-12)


def test_find_peaks_and_windows_match_checker():
    y = np.concatenate([[np.nan], -np.cos(np.linspace(0, 6, 48) * 2.1) * np.exp(-np.linspace(0, 1, 48))])
    assert find_peaks(y) == cc.find_peaks(list(y))
    w = windows(find_peaks(y))
    ref = cc.make_windows(cc.find_peaks(list(y)))
    assert [x["points"] for x in w] == [x["points"] for x in ref]
    assert [x["flags"] for x in w] == [x["flags"] for x in ref]


def _run_variants(tmp_path, B, chunk_sizes, stop_after):
    L = 4
    counts, shots, X = _synthetic_cell(L=L)
    W = weight_matrix(L)
    d = design(X)
    sched = [{"n_ref": 5, "points": list(range(1, 10)), "flags": [], "timing_testable": True}]
    fn = make_replicate_fn(d, L, sched)
    results = {}
    # unbatched reference: one chunk holding every replicate
    paths = BS.run(counts, shots, W, 2, 5, B, B, fn, tmp_path / "unbatched")
    results["unbatched"] = BS.assemble(paths)
    for cs in chunk_sizes:
        paths = BS.run(counts, shots, W, 2, 5, B, cs, fn, tmp_path / f"chunk{cs}")
        results[f"chunk{cs}"] = BS.assemble(paths)
    # interrupted mid-cell after `stop_after` chunks, then resumed in a fresh call
    with pytest.raises(InterruptedError):
        BS.run(counts, shots, W, 2, 5, B, chunk_sizes[0], fn, tmp_path / "resume", stop_after_chunks=stop_after)
    done = sorted((tmp_path / "resume").glob("chunk_*.npz"))
    assert len(done) == stop_after
    paths = BS.run(counts, shots, W, 2, 5, B, chunk_sizes[0], fn, tmp_path / "resume")
    results["resumed"] = BS.assemble(paths)
    # every finished chunk file was reused, not recomputed (mtime unchanged)
    return results


def test_chunked_checkpointed_and_resumed_bootstrap_is_bit_identical_to_unbatched(tmp_path):
    res = _run_variants(tmp_path, B=37, chunk_sizes=(7, 10, 1), stop_after=2)
    ref = res["unbatched"]
    for name, got in res.items():
        assert got.keys() == ref.keys()
        for k in ref:
            assert got[k].shape == ref[k].shape, (name, k)
            assert np.array_equal(got[k], ref[k], equal_nan=True), (name, k)  # bit-identical incl. nan pattern
            assert got[k].tobytes() == ref[k].tobytes(), (name, k)


def test_resume_reuses_finished_chunks_and_a_partial_chunk_never_counts(tmp_path):
    L = 4
    counts, shots, X = _synthetic_cell(L=L)
    W = weight_matrix(L); d = design(X)
    sched = [{"n_ref": 5, "points": list(range(1, 10)), "flags": [], "timing_testable": True}]
    fn = make_replicate_fn(d, L, sched)
    ck = tmp_path / "ck"
    with pytest.raises(InterruptedError):
        BS.run(counts, shots, W, 2, 5, 20, 5, fn, ck, stop_after_chunks=2)
    first = {p.name: p.stat().st_mtime_ns for p in ck.glob("chunk_*.npz")}
    (ck / "chunk_000011_000016.tmp.npz").write_bytes(b"partial")  # a crashed chunk leaves only a .tmp file
    paths = BS.run(counts, shots, W, 2, 5, 20, 5, fn, ck)
    assert {p.name: p.stat().st_mtime_ns for p in ck.glob("chunk_*.npz") if p.name in first} == first
    assert len(paths) == 4 and all(p.exists() for p in paths)
    full = BS.assemble(BS.run(counts, shots, W, 2, 5, 20, 20, fn, tmp_path / "one"))
    got = BS.assemble(paths)
    assert all(np.array_equal(got[k], full[k], equal_nan=True) for k in full)


def test_percentile_interval_matches_checker_and_exact_primary_quantile():
    vals = np.array([0.1, 0.2, np.nan, 0.4, 0.3, np.nan])
    lo, hi, u, fl = BS.percentile_interval(vals, 0.025, 0.975)
    rlo, rhi, ru, rfl = cc.percentile_interval([0.1, 0.2, None, 0.4, 0.3, None], 0.025, 0.975)
    assert (lo, hi, u, fl) == (rlo, rhi, ru, rfl)
    assert BS.Q_PRIMARY[0] == 1.0 / 9600.0
    # exact primary quantile tolerates 4 undefined replicates at B = 48000 and rejects 5 (prereg §6.3)
    B = 48000
    base = np.linspace(0, 1, B)
    for u_, ok in ((4, True), (5, False)):
        v = base.copy(); v[:u_] = np.nan
        lo, hi, uu, fl = BS.percentile_interval(v, *BS.Q_PRIMARY)
        assert uu == u_ and (("UNDEFINED" not in fl) == ok)
