# Findrr: Project Status

> Read at the start of every session. Update at the end of every session.
> Record only facts. Mark anything not actually performed and verified as **unverified** or **not started**.
> Keep this file short. Move old session-log entries into `docs/archive/` when the log exceeds 5 entries.

## Snapshot

| Field | Value |
|---|---|
| Last updated | 2026-11-26 |
| Current milestone | Milestone 2 (Additional Functionality) |
| Current phase | Milestone 2, Iteration 6 (US-017 done; US-014 blocked on D-005) |
| Current iteration | Milestone 2, Iteration 6 |
| Current branch | fix/ml-runner-contracts |
| Open PR | PR #21 |
| Latest release | None |

## Current task

The autonomous run is paused: every remaining item is gated on the user (see below). Iteration 6 delivered US-017 (PR #19). US-014 waits for D-005.

## Awaiting merge or approval

- **Awaiting merge: PR #30** (user review: notebook 02 acceptance change, D-008). Pearson r no longer gates ML-002; it is still reported. After merging, re-run notebook 02 on Kaggle, extract the bundle into `models/similarity-evaluator/v1.1.0/`, run `findrr model inspect ML-002`, and paste the full cell 12 output.
- **Run on Kaggle** (GPU T4, Internet on): `notebooks/01_train_title_expander.ipynb` and `02_train_similarity_evaluator.ipynb`. Extract the bundles into `models/title-expander/v2.0.0/` and `models/similarity-evaluator/v1.1.0/`, run `findrr model inspect ML-001` / `ML-002`, and share the printed metrics. Do **not** run notebook 03. Unblocks: real Module 3 inference, evaluation reports and model cards.
- **Re-run `notebooks/01_train_title_expander.ipynb` on Kaggle** (from `main`; Run > Restart & clear first). PR #27 was merged by the user on 2026-11-26, confirming the occupation-precision threshold of 0.75. Paste the metrics block and sample predictions.
- Decide D-002 (discovery source), D-003 (DOCX/PDF), D-004 (ML-001 runtime), D-005 (company research) and D-006 (ML-003 data).

## Next step

1. When the notebook metrics arrive: write `docs/ml/evaluation-reports/` and `docs/ml/model-cards/` from the evidence, and verify real inference end to end.
2. When decisions arrive: resume `/autonomous-run` (US-014, US-012, D-002 changes, the ML-003 rewrite).

## Blockers

- Live discovery needs a person to solve the Google CAPTCHA (see D-002).
- Real inference for all models is blocked until the artifacts are re-supplied.

## Bootstrap and approval tracker

| Gate | Status | Approved by user |
|---|---|---|
| 1. Environment and repository | Approved | Yes |
| 2. Initial Project Plan and Roadmap | Approved | Yes |
| 3. SRS and Product Backlog | Approved | Yes |
| 4. Machine Learning Development Plan | Approved | Yes |
| 5. Initial Architecture and Design | Approved | Yes |
| Final approval to begin implementation | Approved | Yes |

Statuses: Not started / In progress / Presented for review / Approved / Changes requested.

## Environment verification

Mark an item verified only after the check has actually been run.

| Item | Status |
|---|---|
| GitHub repository | Verified (`Lebogang-G-Masia/Findrr`; made **public** by the user on 2026-11-26) |
| `main` branch protection configured | Verified 2026-11-26 via API read-back: PR required (0 approvals), 4 required checks, admins enforced, force push and deletion blocked |
| GitHub access (gh or MCP) works | Verified (`gh` authenticated as `Lebogang-G-Masia`) |
| Penpot MCP access works | Verified (Connected to active design file `UI Design`, read operations validated) |
| Python environment initialised | Verified (Python 3.14.8 on Arch Linux; `pyproject.toml`, `.env.example`) |
| Laptop hardware, OS and GPU documented | Verified (Intel i5-1235U, 7.4GiB RAM, Arch Linux, no dedicated GPU) |
| CI (lint, tests, file-size check, secret scan) running | Verified (GitHub Actions PR run `41440805215` and push run `41440800224` all 4 checks passed) |

## Model status

| Model | Spec approved | Notebook written | Trained by user | Artifacts supplied | Integration verified (real inference) |
|---|---|---|---|---|---|
| `title-expander` (ML-001) | Approved (Gate 4) | Yes (`notebooks/01_train_title_expander.ipynb`) | Yes | **Missing from disk since 2026-11-26** (needs re-supply) | No (also see D-004) |
| `similarity-evaluator` (ML-002) | Approved (Gate 4) | Yes (`notebooks/02_train_similarity_evaluator.ipynb`) | Yes | **Missing from disk since 2026-11-26** (needs re-supply) | Previously verified (0.7755); not re-verifiable until re-supplied |
| `application-tailor` (ML-003) | Approved (Gate 4) | Yes (`notebooks/03_train_application_tailor.ipynb`) | No | No | No |

## Documents

| Document | Status |
|---|---|
| Project Plan | Approved (`docs/project-plan.md`) |
| SRS | Approved (`docs/requirements/srs.md`) |
| Product Backlog | Approved (`docs/requirements/product-backlog.md`) |
| Software Architecture Document | Authored and presented (`docs/design/software-architecture.md`) |
| Technical Design Specifications | Authored and presented (`docs/design/technical-specs.md`) |
| Database Design Document | Authored and presented (`docs/design/database-design.md`) |
| API Specification | Authored and presented (`docs/design/api-spec.md`) |
| Machine Learning Architecture Document | Approved (`docs/ml/ml-architecture.md`) |
| Model Specifications | Approved (`docs/ml/models/`) |
| Model Registry | Initialized (`docs/ml/model-registry.md`) |
| UI/UX designs | Skeleton created (`docs/design/ui-ux.md`; Penpot MCP verified, design starts in M3) |
| Test Plan | Authored and presented (`docs/testing/test-plan.md`) |
| Architecture Decision Records | Authored ADRs 0001–0004 (`docs/adr/`) |

## Open decisions

See `docs/DECISIONS_PENDING.md`. Count of open items: 6

## Session log (newest first)

| Date | Summary | Branch / PR |
|---|---|---|
| 2026-11-26 | D-008 resolved by the user: Pearson r removed from the ML-002 acceptance gate and kept as a reported metric. Updated the notebook generator and notebook 02, the model spec (§8, §14), the training doc and the SRS ML-002 criteria; added a regression test. | feature/ml-002-ungate-pearson / PR #30 |
| 2026-11-26 | PR #27 (ML-001 constrained decoding) merged by the user (`2a2463a`). This confirms occupation precision >= 0.75 as the ML-001 acceptance threshold. Verified that PR #28 (D-008, from another session) merged consistently with #27 (docs only; 6 open decisions). 189 tests pass on `main`. Next: re-run notebook 01; decide D-008. | docs/record-pr-27-merge |
| 2026-11-26 | First Kaggle run of ML-002 v1.1.0 (user): the acceptance gate stopped the export. Pearson r 0.745 (target 0.85) failed; precision at 0.70 0.963, AC-ML-002.1 0.894 and AC-ML-002.2 0.248 passed. Local analysis on the rebuilt test pairs: the untrained base model scores Pearson 0.614, and the O*NET proxy labels disagree with title meaning in both directions. Raised D-008. | docs/d-008-ml-002-acceptance |
| 2026-11-26 | D-007 resolved by the user: option 1. Implemented `findrr.ml.title_constraint` (token trie over 45,712 O*NET titles; no invented or repeated titles), embedded verbatim in notebook 01. The runner decodes with it and requires `titles.json`. Occupation precision replaces ROUGE-L (threshold 0.75 PROPOSED, from baselines 0.007/0.12/0.736). Fixed a stray-bracket bug in title cleaning. End-to-end smoke test passed (untrained base model, no training). 189 tests pass. Opened PR #27. | feature/ml-001-constrained-decoding / PR #27 |
| 2026-11-26 | First Kaggle run of ML-001 v2.0.0 (user): the acceptance gate stopped the export. ROUGE-L 0.194, valid ratio 0.554, repetition 0.580, AC-ML-001.1 passed. Local analysis: ideal answers score ROUGE-L 0.27–0.66, so the 0.75 target is unreachable; repetition and invalid titles are real model defects. Raised D-007. | docs/d-007-ml-001-evaluation |
| 2026-11-26 | User report: notebook 01 failed on Kaggle (Python 3.13) with `cannot import name 'is_flax_available'`. The environment cell imported the preinstalled transformers 5.x before the pinned 4.46.3 install, mixing versions. The report now reads metadata only, and a version-guard cell says to restart if the versions are mixed. Verified in a Python 3.13 + torch 2.15 environment: all imports, both trainer argument sets and both tokenizers work (no training). Regression test added. | fix/notebook-import-order |
