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

- **Awaiting merge: PR #22** (user-review category: training notebooks, model versions, artifact load contract). Unblocks: Kaggle training runs.
- After merging: run `notebooks/01_train_title_expander.ipynb` and `02_train_similarity_evaluator.ipynb` on Kaggle (GPU T4, Internet on), then extract the bundles into `models/title-expander/v2.0.0/` and `models/similarity-evaluator/v1.1.0/`. Do **not** run notebook 03.
- Decide D-002, D-003, D-004, D-005 and D-006.

## Next step

1. User answers D-002 to D-005 and re-supplies the model artifacts.
2. Then resume `/autonomous-run`, in this order:
   - US-014 (after D-005);
   - US-012 DOCX/PDF (after D-003);
   - D-002 discovery changes;
   - real ML verification once the artifacts are back.
3. Milestone 3 needs the Penpot MCP connected in the session, then design approval.

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

See `docs/DECISIONS_PENDING.md`. Count of open items: 5

## Session log (newest first)

| Date | Summary | Branch / PR |
|---|---|---|
| 2026-11-26 | PR #21 (runner contracts) self-merged after green CI. Rewrote the ML-001 and ML-002 notebooks to their specs: checksum-verified O*NET 31.0 data, occupation-disjoint splits, runner-identical prompts and pooling, all spec metrics measured, export blocked on failed acceptance, app manifest schema. ML-001 v2.0.0 and ML-002 v1.1.0. The registry now rejects wrong ID or version, missing required files and failed acceptance. Marked notebook 03 DO NOT RUN and raised D-006. Fixed registry dir precedence and test env leakage. 177 tests pass. Opened PR #22 (awaiting user merge). | feature/ml-notebooks-spec-alignment / PR #22 |
| 2026-11-26 | Notebook review requested by the user: none of the three notebooks meets its approved spec (details in the notebook PR). Fixed the ML-003 runner: manifest path, integrity-call arguments, real greedy autoregressive generation, explicit `InferenceExecutionError` instead of silently substituting MOCK output, and the training system prompt. Removed unverified wording from the ML-003 mock. Aligned ML-001 runner levels to `ANY/ENTRY/MID/SENIOR/LEAD`. 167 tests pass. Opened PR #21. | fix/ml-runner-contracts / PR #21 |
| 2026-11-26 | PR #19 (US-017) self-merged after green CI (`a015277`). The autonomous run paused: all remaining work is gated (D-002 to D-005, model artifacts, Penpot designs). 160 tests pass on `main`. | docs/iteration-6-closure |
| 2026-11-26 | Iteration 6 started. US-014 requirements analysis raised D-005 (blocked). Implemented US-017: an active profile stored in `app_settings`, `profile use`, an active marker in `profile list`, no silent switching on create, and every default-profile call site routed through one resolver. 160 tests pass. Opened PR #19. | feature/iteration-6-multi-profile / PR #19 |
| 2026-11-26 | PR #18 (Module 3 wiring) self-merged after green CI (`e908dd4`). | main |
| 2026-11-26 | Wired Module 3 into discovery. Added `findrr terms generate/list` and `SearchTermService` (one pass; refuses MOCK unless `--allow-mock`; persists all outcomes). `search run` now searches accepted non-MOCK terms with term linkage and halt handling. Additive `search_terms` columns. 153 tests pass. Opened PR #18. | feature/module-3-search-term-pipeline / PR #18 |
| 2026-11-26 | PR #17 (audit fixes) self-merged after green CI (`d649fca`). | main |
