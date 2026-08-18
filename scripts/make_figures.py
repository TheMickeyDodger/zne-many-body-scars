#!/usr/bin/env python
"""Regenerate every figure from recorded results ONLY (design.md §15, M3 C3).

Reads results/minimal/steps.csv; performs no simulation and no physics — plotting
only. Run:  .venv/bin/python scripts/make_figures.py [--results DIR] [--out DIR]
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results/minimal")
    parser.add_argument("--out", default="figures")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    with (Path(args.results) / "steps.csv").open() as f:
        rows = list(csv.DictReader(f))
    n = [int(r["n"]) for r in rows]
    col = lambda name: [float(r[name]) for r in rows]
    ed, e0 = col("ed_reference"), col("e0_trotter")
    noisy = col("e_noisy_dm")
    zne, band = col("zne_primary_mean"), col("zne_primary_std")
    secondary = col("secondary_estimate")
    eps_u, eps_m = col("eps_u"), col("eps_m")

    fig, (top, bottom) = plt.subplots(
        2, 1, figsize=(8.5, 7.5), sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1.0]},
    )
    top.plot(n, ed, color="0.55", ls=":", lw=1.4, label="exact continuous-time (ED)")
    top.plot(n, e0, color="black", lw=1.6, marker=".", ms=5,
             label=r"noiseless Trotter $E_0$")
    top.plot(n, noisy, color="tab:red", lw=1.2, marker="s", ms=3.5,
             label="unmitigated noisy (density matrix)")
    top.plot(n, zne, color="tab:blue", lw=1.4, marker="o", ms=3.5,
             label=r"ZNE primary ($\lambda_r$ linear), seed mean")
    top.fill_between(n, [z - s for z, s in zip(zne, band)],
                     [z + s for z, s in zip(zne, band)],
                     color="tab:blue", alpha=0.25,
                     label=r"$\pm$1 sd folding-seed spread")
    top.plot(n, secondary, color="tab:green", lw=1.0, ls="--", marker="^", ms=3,
             label=r"secondary ExpFactory(asymptote=0)")
    top.axhline(0.0, color="0.85", lw=0.8, zorder=0)
    top.set_ylabel(r"$\langle Z_\pi(t)\rangle / L$")
    top.legend(fontsize=8, loc="lower right", ncol=2)
    top.set_title(
        r"MFIM scar dynamics under two-tier depolarizing noise, $L=6$, "
        r"$V{=}1$, $\Omega{=}0.24$, $\Delta t{=}1$ (design §15)",
        fontsize=10,
    )

    bottom.plot(n, eps_u, color="tab:red", lw=1.2, marker="s", ms=3.5,
                label=r"$\varepsilon_u$ (unmitigated)")
    bottom.plot(n, eps_m, color="tab:blue", lw=1.2, marker="o", ms=3.5,
                label=r"$\varepsilon_m$ (ZNE primary)")
    bottom.axhline(0.01, color="0.6", ls=":", lw=1,
                   label=r"$\varepsilon_{\min}$ relevance filter")
    bottom.set_yscale("log")
    bottom.set_xlabel(r"$Vt = n$ (Trotter steps)")
    bottom.set_ylabel("absolute error")
    bottom.legend(fontsize=8, loc="lower right")

    fig.tight_layout()
    for suffix in ("png", "pdf"):
        fig.savefig(out / f"minimal_experiment.{suffix}", dpi=200)
    print(f"wrote {out}/minimal_experiment.png and .pdf from {args.results}/steps.csv")


if __name__ == "__main__":
    main()
