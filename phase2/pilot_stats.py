"""Stage 1B/1C partial-cost statistics: LIN, QUAD and NONE paths of the frozen order only.

The EXP path (log mode, clamp rule, avoid_log) is NOT invoked here: its zero-sign / linear-fit
convention is under human decision (A-2). Every number produced by this module is therefore a
PARTIAL cost measurement, never a complete feasibility figure.
"""
from __future__ import annotations

import numpy as np

from .estimators import CellDesign, PEAK_OBS, POLARITY, fit_lin_quad, match_peaks
from .observables import mloc_sign

EXTS = ("NONE", "LIN", "QUAD")


def curves_lin_quad_none(d: CellDesign, V: np.ndarray, L: int) -> np.ndarray:
    """est[b, n, 3 ext, 4 curve quantities] (nan = undefined); steps 2-4 for NONE/LIN/QUAD."""
    lin, quad = fit_lin_quad(d, V)
    none = V[:, :, :, 0, :]
    ms = mloc_sign(L)
    B, N = V.shape[:2]
    est = np.full((B, N, 3, 4), np.nan)
    for e, arr in enumerate((none, lin, quad)):
        zpi, pret, mi, mj, mij = (arr[..., i] for i in range(5))
        est[:, :, e, 0] = zpi.mean(axis=2)
        est[:, :, e, 1] = pret.mean(axis=2)
        est[:, :, e, 2] = (ms * mi).mean(axis=2)
        est[:, :, e, 3] = (mij - mi * mj).mean(axis=2)
    return est


def make_replicate_fn(d: CellDesign, L: int, schedule: list[dict]):
    def fn(V: np.ndarray) -> dict[str, np.ndarray]:
        est = curves_lin_quad_none(d, V, L)
        out = {"est": est}
        for e, ename in enumerate(EXTS):
            for qi, obs in enumerate(PEAK_OBS):
                for k, win in enumerate(schedule, start=1):
                    if "UNAVAILABLE" in win["flags"]:
                        continue
                    amp, t, da, dt = match_peaks(est[:, :, e, qi], win["points"], POLARITY[obs])
                    out[f"amp_{ename}_{obs}_{k}"] = amp
                    out[f"t_{ename}_{obs}_{k}"] = t
        return out
    return fn
