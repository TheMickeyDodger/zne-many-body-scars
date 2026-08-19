# Phase A Review Package — Sealing v0.1.0 (for the human owner)

**Purpose:** everything needed to decide whether to seal v0.1.0. **Nothing has
been committed, tagged, pushed, released, archived, or published by this work:
the entire Phase A change set exists only in the working tree, and every one of
those actions remains a human decision** (§9). Prepared 2026-08-18 at the end
of Phase A milestone M3.

## 1. What Phase A was

Baseline: the accepted v0.1.0 research artifact at commit `ae9896b` (the
recorded experiment, its pre-registered design, results note, and first review
package). Phase A prepared that artifact for a defensible, immutable, citable
release: a release-readiness audit, protection of the frozen evidence,
citation-metadata repair, a full-reproduction CI workflow with an
honest-claims assessment, draft release notes, a cold-start reproduction
protocol, a preregistration outline for the next experiment, and this package.
The scientific content was frozen throughout: **no physical, statistical, or
numerical definition changed, and the canonical evidence is byte-untouched**
(§2).

## 2. Current-state verification (what was run, what it proved)

- `pytest`: **116 passed** (52 at Phase A start; +28 canonical-guard tests,
  +36 verifier tests). Includes the seal-guard test: the suite fails if hashed
  source stops matching the sealed identity. (Counts re-measured at end of
  M3 round 4; the sweep table in §4 records its own re-execution.)
- Canonical integrity, both gates, green at every milestone boundary:
  **8/8 sha256** against the supervisor-recorded baseline AND **contents
  6 files / 2 files**. The contents gate exists because review demonstrated
  the hash baseline alone cannot detect files *added* to a frozen directory
  (finding F16).
- Sealed source identity:
  `ab751d691a4cc3fc623b6044ef70dead0b54df46c0f33f880e574f7a828d6ca2`
  (`tools/release_identity.json`), equal to the working tree, test-enforced.
  Hash lineage from the canonical `7161d655…` — including three
  review-rejected intermediates never present in any released artifact — is
  recorded in `docs/design.md` §20 Phase A rows A2-1…A2-6 (A2-5/A2-6 record
  post-seal verifier corrections in unhashed `tools/`; the hash itself last
  moved at A2-4).
- Execution evidence, with its provenance separated cleanly (this document is
  itself shipped, so it claims only what shipped artifacts record):
  - **The public determinism claim** rests on the three executions recorded in
    `docs/review-package.md` §2 (two implementer, one lead; all six files
    sha256-identical) — this is the count every repo doc states.
  - **One Phase A re-execution has shipped evidence**: `docs/design.md` §20
    row A2-4 records the lead's full run — 250.3 s wall clock, headline
    numbers reproduced exactly (GIF 1.2777, m = 39, wins = 39; shot GIF
    1.2774), five data files byte-identical to canonical.
  - Further full re-executions were performed during Phase A as internal
    verification; their transcripts exist only in the project's process
    records, not in the repository, so **this package neither counts them nor
    cites their measurements**. (Frozen headline values, for reference, from
    `results/minimal/metrics.json`: GIF 1.2777339664421639, RMS
    0.32079729685433694 → 0.25106736243976785, 39/39 reportable steps, n = 34
    excluded; shot GIF 1.2774206732205877.)
- `tools/verify_reproduction.py` exercised for real on every class it
  enforces: a fresh sealed-identity run (PASS), a pre-seal genuine run
  (correctly noncanonical), a modified-tree self-certification probe
  (correctly FAIL), platform-schema corruption (FAIL), stack drift/removed
  packages/unsupported Python (FAIL), and a simulated legitimate off-platform
  bundle (PASS).

## 3. Findings across Phase A, with final dispositions

Classification: BLOCKER (must not seal with it present) / MAJOR (fix before
seal) / MINOR (acceptable with rationale). Full detail with evidence:
`.herd/state/phaseA-audit-findings.md` (audit of record) and the canonical
review-round files in `.herd/state/reviews/`, which are the authoritative
count. **The findings caught and fixed in review are listed on purpose: the
adversarial review history is the evidence this artifact was checked.**
History cutoff: this document reflects the review record **as of canonical
round 14**. Round 10's transcript is persisted in the record like every other
round; the lead verified it as a verbatim replay of round 09, did not route
it, and it contributes no distinct findings (the round-13 pane capture was
likewise a replay, with the genuine response recovered from the reviewer's
rollout record and preserved as `…round-13-RECOVERED.md`; round 14 was
recovered the same way as a precaution). Any later rounds live in
`.herd/state/reviews/` and are not re-counted here — by design, since a
document that counts the reviews reviewing it invalidates its own count every
round.

**Fixed during Phase A (work tree):**

| # | Sev | Finding | Disposition |
|---|---|---|---|
| F1 | BLOCKER | `run_minimal.py` default `--out` was the canonical evidence directory | Guards, rebuilt three times under review (case-insensitive alias bypass; cross-target hole; absent-dir case edge) into `scripts/_canonical_guard.py`: both scripts refuse both frozen dirs by filesystem identity + case-fold reservation; 28 tests |
| F9 | MAJOR | CITATION.cff: pseudonym as family name; unreleased `date-released`; no DOI path | Entity-form author; date removed with at-release instructions; commented Zenodo path; no invented DOI |
| F14 | MAJOR | "Exactly two fields differ" reproduction claim unstable (pip unpinned) | pip drift permitted and normalized (`expected-tooling`), stated everywhere the claim appears |
| F16 | MAJOR | Wrong script could POLLUTE the other frozen dir; sha baseline blind to additions | Shared cross-target guard; contents gate added to acceptance |
| F17 | MAJOR | Verifier blessed materially different stacks off-platform | Narrow allowlist; any non-pip package change/removal/addition fails in both modes |
| F18/F19 | MAJOR | Provenance values unvalidated; then the round-3 fix let a modified tree validate itself and condemned genuine pre-edit runs | Sealed identity in unhashed `tools/release_identity.json`; atomic (hash, note) pair validation; expectation never derived from the working tree; loud seal-staleness test |
| F20 | MAJOR | Platform allowlist accepted structural corruption | Platform leaf-set schema enforced; values only may differ (completed at r11: empty `{}` containers now count as structure — the r04-era fix missed them) |
| F2 | MAJOR | Present-tense claim about nonexistent `results/minimal-repro/` | Rewritten to past tense pointing at the recorded identity (review-package §1/§2); design tree annotated |
| F3 | MAJOR | Reproduction-count inconsistency (2 vs 3 across docs) | Aligned to the three executions evidenced in the shipped review package (the public determinism count). Of the later Phase A runs, exactly one is claimable and claimed — the lead's, via its shipped record in design §20 A2-4 (§2 of this package cites it only through that record); the remaining Phase A runs have herd-state evidence only and are not claimed anywhere, including here |
| F4 | MAJOR | Provenance metadata asserted "repository has no commits" (false since first commit) | Corrected for future runs; frozen canonical file untouched (true at recording) |
| F5/F7/F10/F11 | MINOR | README layout omissions; missing pyproject license; unignored repro dirs; stray file `1` | All fixed (layout complete; `license = {text = "Apache-2.0"}`; `.gitignore` covers `results/repro/`+`figures-repro/`; stray file removed) |
| F12 | MINOR | `docs/review-package.md` stale present tense | Dated header annotation; no rewrite of the historical record |
| F15 | MINOR | Canonical PDF embeds `/CreationDate` (5 bytes differ on regeneration; PNG byte-identical) | Recorded; per-file expectations stated in the protocol; no code change |
| — | — | Every finding raised in adversarial review is enumerated round-by-round in the table below (the audit rows above cover the F-numbered audit findings; several review findings map onto them, noted per row) | see "Review findings, complete" |

**Review findings, complete — every rejected finding, with the round it was
DISCOVERED and the round whose work FIXED it** (canonical transcripts:
`.herd/state/reviews/20260818-193101-44abb3-round-01.md` … `round-14.md`,
plus the `…-RECOVERED.md` rollout recoveries for rounds 13–14;
"fixed in rN" means the fix landed in the work reviewed at round N):

| Found | Sev | Finding | Fixed |
|---|---|---|---|
| r01 | BLOCKER | Guard bypass: case-insensitive filesystem aliases (`results/MINIMAL` same inode, allowed) — F1's round-1 "fixed" status was false | r02 (identity-aware guard) |
| r01 | MAJOR | "Exactly two fields differ" claim unstable — pip recorded but unpinned (= audit F14) | r02 (drift permitted + normalized) |
| r01 (lead) | MAJOR | README §4 inline check misreported expected off-platform differences as reproduction failure | r02 (tested verifier tool) |
| r01 | MINOR | Shipped `shasum` verification printed hashes without comparing them — could not fail | r02 (tool exits non-zero) |
| r01 | MINOR | PDF `/CreationDate` time dependence missing from the audit (= audit F15) | r02 (recorded, per-file expectations) |
| r02 | MAJOR | Cross-target pollution: each script guarded only its own frozen dir; sha baseline blind to added files (= F16) | r03 (shared guard; contents gate) |
| r02 | MAJOR | Off-platform mode blessed materially different stacks — fake Python 3.9.1 / mitiq 2.0.0 / numpy-removed bundle PASSed (= F17) | r03 (narrow allowlist) |
| r02 | MAJOR | Provenance fields classified by name, values never validated — `"deadbeef"` PASSed (= F18) | r03 (value validation) |
| r02 | MINOR | Audit self-contradiction: superseded hash still presented as the future-run value | r03 |
| r02 | MINOR | "Before any computation or filesystem write" guard claim overstated | r03 (scoped wording) |
| r03 | MAJOR | Working-tree-derived expectation: a modified tree validated itself; and (lead, live) a genuine pre-edit run was condemned — both directions (= F19) | r04 (sealed identity, atomic pair) |
| r03 | MAJOR | Platform allowlist accepted structural corruption — deleted/added platform fields PASSed (= F20) | r04 (schema enforcement) |
| r03 | MINOR | README still said package fields "legitimately differ" off-platform after the verifier was narrowed | r04 |
| r03 | MINOR | design.md A2-1 pointer named the wrong row for the final hash | r04 |
| r03 | MINOR | Absent-directory + case-alias guard edge | r04 (unconditional case-fold layer — the final hash change) |
| r05 | MAJOR | Incomplete provenance enumeration of the canonical→sealed delta (release notes + protocol; lead finding) | r06 |
| r05 | MAJOR | "Every number traceable to frozen data" — false for test-count and runtime | r06 (claim narrowed, ops numbers labeled) |
| r05 | MAJOR | p₂=0 mask outcome-dependent (`r(n) > 0` in the mask) while claiming E₀-only — could exclude disconfirming sign flips | r06 (E₀-only mask; sign flips → pre-declared "model inadequate") |
| r05 | MAJOR | Outcome table licensed apportioning the combined-noise gap from a single-arm control | r06 (isolated-channel licensing; factorial pre-declared) |
| r05 | MAJOR | Seal-test overclaim in the protocol ("proves … unmodified") + PDF "never byte-identical" as impossibility theorem | r06 (exact scope; observation-as-evidence) |
| r05 | MINOR×3 | Ambiguous interval boundaries; "is published" (nothing is); runtime estimates conflicting between docs | r06 |
| r06 | MAJOR | Model-adequacy gate asymmetric: r(n) > 1 lacked a deterministic verdict — a decision path open to post-hoc choice | r07 (symmetric gate, frozen tolerance) |
| r06 | MAJOR | Additivity criterion freezable after seeing this control's g₁; "2×2" listed three arms | r07 (freeze before either new arm; four cells named) |
| r06 | MAJOR | Seal overclaim survived in two files the r05 fix did not open (CI assessment, workflow) → standing substance-sweep directive | r07 |
| r07 | MAJOR | The 10⁻⁹ tolerance justification assumed the hypothesis under test (heuristic attenuation + untested §16 figure) | r08-accepted work (honest frozen-policy framing) |
| r07 | MAJOR | H-L unbounded below — a negative fitted rate would have confirmed "locality suppression" | r08-accepted work (H-L ≥ 0; anti-attenuation verdict) |
| r09 | MAJOR×5 + MINOR | This package: missing sweep table; execution-count contradiction with F3; incomplete findings history; outline "NOT REVIEWED" false; residual risks dropping inherited items; "two figures" miscount | M3 r2 revision (fixes confirmed correct at r11) |
| r10 | — | Transcript persisted in the record like every round; lead-verified line by line as a verbatim replay of round 09 citing content that no longer existed, and therefore NOT routed | no distinct findings to dispose of |
| r11 | MAJOR×4 + MINOR | Two verifier defects three earlier rounds missed: empty `{}` containers escaped platform-schema classification (lead-reproduced PASS); "same-platform" detection conflated platform class with same hardware, false-negativing honest different-machine reproductions. Plus: execution/review counts still internally contradictory; residual-risk list incomplete vs the historical package's §6; one sweep row overbroad on CI | M3 r3 revision: sentinel-leaf structure validation + regression tests; `--different-hardware` declaration with claim narrowed to same-hardware everywhere; explicit history cutoff; risk list completed item-by-item; sweep row narrowed |
| r12 | MAJOR×2 + MINOR | The SIBLING of the empty-container bug in the other direction: `dict.get()` mapped a missing key and an explicit JSON null both to `None`, so an extra null field — or a required field set to null — escaped classification (lead-reproduced PASS); the shipped gate counts had gone stale after r3/r4 added tests (this package, sweep row, release notes) — the deeper defect being that sweep rows were executed once and treated as standing; transcript citation stopped at round-09 and round 10 was described as excluded from the record | M3 r4 revision: `_MISSING` sentinel separates membership from value, null-valued defined platform fields rejected as "absence in disguise", regression tests for all three shapes; third-form hunt performed (metrics.json comparison, CSV comparison, mode detection, provenance pair — each already membership-aware, verified); every sweep verification re-executed with counts corrected; citation range and round-10 description fixed |
| r13 | MAJOR | (Pane capture was a replay of r12; genuine response recovered from the rollout record.) One sweep row had drifted again after the r4 edits — "33 verifier tests", citations stopping at A2-5 — contradicting the same document's §2 accounting and its own re-execution assertion. Reviewer confirmed the membership/value separation, hardware disclosure, cutoff, canonical evidence, and seal scope sound; a list-valued platform probe confirmed contract-consistent (leaf membership preserved, values free) — no code change | M3 r5 revision: row corrected to 36 tests / A2-6; full row-by-row re-verification battery run after all edits; two further precision fixes from that battery (hash-row self-reference qualifier; "all inherited items" wording) |
| r14 | MAJOR | (Recovered from the rollout record as a precaution; genuine.) The `minimal-repro` sweep row's stated verification — "ls results/ shows only minimal/" — was factually false against the tree, where legitimate gitignored `results/repro/` reproduction output also exists: the claim was true but its stated verification did not verify it. "No other material blocker remains." | M3 r6 revision (this one): verification made path-specific (`test ! -e results/minimal-repro`); every remaining row's stated verification executed once more and confirmed to produce its stated result; cutoff advanced to r14 with the replay/recovery incidents described |

**Accepted with rationale (open by design):**

| # | Sev | Item | Rationale |
|---|---|---|---|
| F6 | MINOR | `tests.yml` pins floating `python-version: "3.12"` | Unit-test job only; no doc claims CI verifies reproduction; the full-repro workflow pins 3.12.14 |
| F8 | MINOR | No named copyright holder (LICENSE is the verbatim Apache-2.0 template; no NOTICE) | Apache-2.0 does not require it; naming a holder for a pseudonymous author is the owner's call — **human decision, §8** |
| F13 | MINOR | README requires Python 3.12.x while pyproject allows ≥3.11 | Installability vs reproduction requirement; both statements true and scoped |

## 4. The M3 consistency sweep — shipped surface, text against code and artifacts

Method: every shipped file (README, all docs, CITATION.cff, pyproject.toml,
both workflows, tools, tests) read against the code and recorded artifacts —
not against other prose. The M2 per-fix substance-sweep tables (attached to
the round reports in `.herd/state/`) are the baseline; rows below marked
"corrected (M3…)" are discrepancies this sweep itself exposed and fixed.
**A sweep row records a verification executed at a moment in time, not a
standing guarantee: every command in the "what verifies it" column was
RE-EXECUTED against the current tree at the end of M3 round 6 (2026-08-18),
each one confirmed to actually produce its stated result** — two rows have
been the cautionary examples: "Test counts" went stale when later fixes added
tests, and the `minimal-repro` row's verification wording was falsified by
legitimate reproduction output until made path-specific.

| Claim | Where stated | What verifies it | Disposition |
|---|---|---|---|
| Superseded hashes never presented as current | all shipped files | per-value grep (re-executed): `7161d655` only as canonical; `65da0408`/`d4da589a`/`9f38c189` only inside design §20 supersession-annotated history rows and this row's own search terms; `ab751d69` current in seal/release-notes/design; `e0255c07…` only as a synthetic test fixture (and, like the superseded values, in this row's own search terms) | already correct |
| Execution/reproduction counts (public determinism claim = 3) | README:3, README determinism ¶, results-minimal:3, this package §2 | `docs/review-package.md` §2 (the shipped record) | corrected (M3: results-minimal:3 aligned; M3 r2: this package's §2 de-conflated from internal Phase A activity) |
| No document claims the never-run full-reproduction workflow verified anything; the one recorded CI run (unit-test workflow, run 32196123194) is claimed only as what it was — installation + unit suite | all docs, both workflows | grep + the CI assessment's own ledger; full-repro workflow absent on remote | corrected (M3 r3: the claim as previously written — "CI verified anything" — was overbroad, since the unit-test run did verify installation and tests) |
| Seal scope (what matching the seal proves) | protocol §2, CI assessment, workflow header, release notes, seal file, tests, README | the hash globs in `source_tree_hash()`; M2-r3 substance table re-checked | already correct |
| Verifier behavior vs prose describing it | README §4, protocol §4 cases, assessment table, design §20 A2-4/A2-5/A2-6 | read against `tools/verify_reproduction.py` (atomic pair vs sealed identity; pip-only tooling; 3.12.x range; platform values-not-schema **including empty containers and null/missing membership**; 1e-12; 36 verifier tests, re-measured) | corrected (M3 r3: r11 showed the code did not yet enforce the declared structure guarantee — empty `{}` containers escaped; fixed with sentinel leaves, A2-5. M3 r4: the null/missing membership sibling, fixed with the `_MISSING` sentinel, A2-6. M3 r5: this row itself had drifted — it still said 33 tests and stopped at A2-5 after the r4 changes — corrected in the full re-verification pass below) |
| Byte-identity claims and platform conditions | README §4 + determinism ¶, protocol §§0/4/5, release notes, CI assessment | design §16 (which always scoped byte identity to same hardware); the verifier's mode semantics | corrected (M3 r3: prose and verifier conflated platform CLASS with same hardware; byte identity now stated as a same-hardware claim everywhere, and the verifier gained the `--different-hardware` declaration so honest different-machine reproductions get the numerical contract instead of a false discrepancy) |
| Test counts | README §7 ("live count"), release notes (labeled operational), assessment (dated "105 at M2 state" + live-count phrasing), mutation-evidence | re-executed: pytest = 116 total; guard file = 28; verifier file = 36 | corrected (M3: mutation-evidence annotation; M3 r4: this table's own previous values had gone stale — a sweep row is a verification executed once, so every row was re-executed at end of milestone, see note above the table) |
| Timing numbers | README ("few minutes"), protocol / release notes / assessment / outline (≈250 s) | labeled operational; the one shipped measurement is design §20 A2-4 (250.3 s); none in the frozen bundle | corrected (M3 r2: this package no longer cites unshipped run times) |
| Repository layout / file-list enumerations | README §7, release-notes contents list, design §17 tree | `git ls-files` + per-path existence check | corrected (M3: README §7 completed incl. this package; design tree annotated; M3 r2: "two figures" → one two-panel figure in two formats) |
| `results/minimal` = 6 files, `figures` = 2 files | README §7, this package | `ls` counts + contents manifest | already correct |
| Headline result numbers | README §2, release notes, results-minimal | `metrics.json` / `steps.csv` (re-verified during M2) | already correct |
| `results/minimal-repro/` existence claims | results-minimal (was present-tense), design §17 tree, review-package §1 | `test ! -e results/minimal-repro` (path-specific; the earlier "ls results/ shows only minimal/" wording was falsified by the legitimate gitignored `results/repro/` reproduction output and did not actually test the claim) | corrected (M3: F2 rewrite + annotations; review-package left as annotated historical record; M3 r6: verification command made path-specific) |
| Review status of the p₂=0 outline | outline banner, this package §7 | `.herd/state/reviews/` rounds 05–08 | corrected (M3 r2: "NOT REVIEWED" was false — reviewed as a draft artifact, not approved for execution) |
| Findings-history completeness | this package §3 | the persisted review-round files (authoritative; cutoff stated in §3) | corrected (M3 r2: complete round-by-round enumeration, discovery separated from fix; M3 r3: explicit cutoff replaces a self-invalidating round count) |
| Residual-risk completeness | this package §8 | inherited qualifications in results-minimal §§5/8/9, review-package §6, design §18 | corrected (M3 r2 and r3: all inherited items carried forward and ranked, checked item-by-item against review-package §6) |
| CITATION.cff vs release reality | CITATION.cff | version = pyproject 0.1.0; entity author; no date-released; no DOI; CFF 1.2.0 by inspection | already correct |
| `tests.yml` untouched by Phase A | workflow | `git diff` empty | already correct |
| Historical documents unrewritten | design §20, review-package | annotation-only policy; dated annotations present | deliberately left (annotated, per policy) |

## 5. Files changed (entire Phase A change set, uncommitted)

**Modified:** `scripts/run_minimal.py`, `scripts/make_figures.py` (guards +
provenance-note fix; computation bodies untouched — verified by the byte
identity of §2), `pyproject.toml` (license metadata), `.gitignore` (repro
dirs), `CITATION.cff` (F9), `README.md` (§4 verification procedure, §7 layout,
determinism scoping), `docs/results-minimal.md` (verification procedure; F2/F3),
`docs/design.md` (§17 dated annotations; §20 Phase A history rows A2-1…A2-6),
`docs/review-package.md` (F12 annotation only), `docs/mutation-evidence.md`
(dated annotation: captures predate suite growth).

**New:** `scripts/_canonical_guard.py` (shared frozen-dir guard — the one
hashed addition), `tools/verify_reproduction.py` + `tools/release_identity.json`
(tested verifier + sealed identity, unhashed), `tests/test_out_guard.py` +
`tests/test_verify_reproduction.py` (64 tests at end of M3), `.github/workflows/
full-reproduction.yml` (manual full-repro job), `docs/ci-reproduction-assessment.md`,
`docs/release-notes-v0.1.0.md` (DRAFT), `docs/reproduction-protocol.md`,
`docs/prereg-p2zero-outline.md` (draft outline), this package.

## 6. Reproducibility-workflow assessment (summary; full text in `docs/ci-reproduction-assessment.md`)

The full-reproduction workflow **has never run** (confirmed against the
remote). A green run would demonstrate: pinned environment installs on
ubuntu-latest; hashed experiment source matches the sealed identity; a fresh
execution matches canonical under the verifier's off-platform contract (1e-12
numeric agreement; byte identity where it happens to hold). It would NOT
demonstrate byte identity in general, or anything about hardware. Design §16's
cross-platform 1e-12 agreement remains an **expectation the workflow tests but
has not demonstrated**; a pre-declared legitimate failure mode exists (shot
pipeline under a different qiskit-aer build), which would be a reportable
finding, not grounds for silent tolerance changes. First execution requires
pushing — a human decision.

## 7. Companion drafts (nothing published)

- `docs/release-notes-v0.1.0.md` — DRAFT; publishing is the owner's act.
- `docs/reproduction-protocol.md` — ships with the release; external
  reproducers on other platforms will be generating the first cross-platform
  evidence, and the protocol says so.
- `docs/prereg-p2zero-outline.md` — draft outline only. As a draft artifact it
  WAS adversarially reviewed (M2 rounds 05–08, three rejections materially
  reshaping its mask, gate, tolerance framing, intervals, and additivity
  clause); it is NOT an approved preregistration for execution, is not
  executed, is not part of the v0.1.0 evidence, and self-declares that one
  analysis branch is not yet freezable.

## 8. Residual risks, ranked

A reader deciding from this document alone gets the full list, checked
item-by-item against the historical package's §6 so nothing inherited is
dropped — the scientific qualifications first, because they bound what a citer
of v0.1.0 may conclude; then verification-tooling risks; then
release-engineering risks.

1. **Interpretation risk (inherited, open by nature): much of the primary
   metric's reward is amplitude restoration.** A cheating constant-rescale
   oracle captures ≈68% of the primary's RMS reduction, and a two-parameter
   oracle beats even the pre-registered secondary
   (`docs/results-minimal.md` §9). The result ships with this qualification
   inline everywhere it is stated; the risk is a citer dropping it.
2. **Interpretation risk (inherited): late-depth uninformativeness.** For
   n ≳ 35 the pre-registered metrics cannot distinguish ZNE failure from
   absence of remaining signal (design §13); no claim is made there, and none
   may be derived from this artifact.
3. **Open scientific question (inherited): the single-qubit contribution to
   the attenuation discrepancy is unresolved** (results note §8; design §11's
   Γ₁ arithmetic). The p₂ = 0 control that would address its isolated part is
   outlined only — unexecuted, unapproved for execution (§7).
4. **Cross-platform reproduction is untested.** The first Linux run may fail
   the 1e-12 check on shot-pipeline quantities (declared caveat). Mitigation:
   the verifier reports it precisely; the assessment pre-commits the honest
   response. Not a seal blocker: the shipped claim is scoped to what has run.
5. **API-documentation/version uncertainty (inherited, distinct from
   installability).** Aer API documentation was verified at 0.17.1 against
   installed 0.17.2 — flagged UNVERIFIED at patch level in design §16/§19 —
   and the mitiq 1.0.0 changelog's "ZNE bug fix" is unexamined in detail
   (design §18.8). A patch-level behavioral difference would surface as a
   reproduction discrepancy rather than being predictable in advance.
6. **Custom-executor declaration gap (inherited).** The λ_eff/declaration
   consistency check is only as strong as the declaration: a custom executor
   tagged with rates it does not actually simulate defeats it (a closure's
   true noise is not introspectable). Module-built executors — the only kind
   this artifact uses or documents — have no such gap; the risk attaches to
   third parties extending the code.
7. **One unasserted verification path (inherited).** The ED reference in the
   run script relies on corroboration against the Trotter curve rather than a
   direct assertion (the related macOS Accelerate spurious-warning filters
   are test-module-local and load-bearing; a BLAS change could unmask
   warnings). Operational, not scientific: the recorded numbers themselves
   are cross-checked.
8. **Future installability.** The byte and 1e-12 claims are conditional on
   the pinned versions (`mitiq==1.0.0`, `qiskit-aer==0.17.2`, Python < 3.13)
   remaining installable; upstream removals would degrade reproduction from
   turnkey to best-effort — visibly, not silently, thanks to the pins and the
   environment record.
9. **Seal scope is partial by design.** `tools/`, `tests/`, `docs/`,
   `.github/` are outside the hash; their integrity rides on the release
   tag's commit identity. Stated explicitly in three shipped documents.
10. **Seal maintenance burden.** Any future edit to hashed source requires a
    deliberate seal update (test-enforced, loud). Process friction, not
    silent error.
11. **ExpFactory-secondary advantage may not transfer** beyond this simulated
    configuration — inherited v0.1.0 scoping, stated wherever the result is.

## 9. Recommendation: **GO** — seal v0.1.0, subject to the human decisions below

The evidence base is frozen and byte-verified, every BLOCKER/MAJOR finding is
fixed or explicitly accepted with rationale, the guards make accidental
evidence destruction implausible, verification is a single tested command, and
the release-facing claims were adversarially reviewed against the artifacts
through the adversarial review history recorded in `.herd/state/reviews/`
(cutoff per §3). The decisions that remain are the owner's alone, in order:

1. **Commit** the Phase A work tree (the herd's commit gate; nothing is staged
   as final until you approve it).
2. **Tag** v0.1.0 — the tag's commit identity is what covers the unhashed
   files (§8, risk 9).
3. **GitHub Release** — using `docs/release-notes-v0.1.0.md` if its text is
   acceptable to you.
4. **Zenodo archive**, then update `CITATION.cff` with the real DOI and
   `date-released` (the file contains exact instructions; nothing is
   pre-filled or invented).
5. **Copyright-holder question (F8):** whether to assert
   "Copyright 2026 TheMickeyDodger" (or a legal name) in LICENSE/NOTICE, or
   leave the template as-is. Either is defensible; it is an identity decision,
   not a technical one.
6. Optionally: first dispatch of the full-reproduction workflow after the
   push, which begins converting §6's expectations into evidence.
