# Findrr: Project Status

> Read at the start of every session. Update at the end of every session.
> Record only facts. Mark anything not actually performed and verified as **unverified** or **not started**.
> Keep this file short. Move old session-log entries into `docs/archive/` when the log exceeds 5 entries.

## Snapshot

| Field | Value |
|---|---|
| Last updated | 2026-11-07 |
| Current milestone | Milestone 1 (Core CLI Baseline Complete) |
| Current phase | Bug Fix & Search Reliability |
| Current iteration | Hotfix |
| Current branch | fix/search-logging-and-link-extraction |
| Open PR | PR #11 (https://github.com/Lebogang-G-Masia/Findrr/pull/11) |
| Latest release | None |

## Current task

Bug fix: PR #11 opened to resolve Google Search link extraction failure (handling relative `/url?q=` paths and regional Google domains), cookie consent dialog dismissal, automated HTML/screenshot diagnostic dumps on 0 results, and comprehensive file logging (`logs/findrr.log`). Awaiting user review and merge.

## Awaiting merge or approval

- Awaiting merge: PR #11

## Next step

User reviews and merges PR #11.

## Blockers

1. **GitHub Branch Protection on Private Repo**: GitHub API returned `HTTP 403: Upgrade to GitHub Pro or make this repository public to enable this feature.` Native branch protection/rulesets on private repos require GitHub Pro/Team. Branch protection on `main` cannot be enforced via API on a free private repository. *(Note: Penpot MCP access was verified and unblocked on 2026-11-02).*

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
| Private GitHub repository created | Verified (`Lebogang-G-Masia/Findrr` created and pushed) |
| `main` branch protection configured | Blocked by GitHub plan (HTTP 403: requires GitHub Pro or public repo) |
| GitHub access (gh or MCP) works | Verified (`gh` authenticated as `Lebogang-G-Masia`) |
| Penpot MCP access works | Verified (Connected to active design file `UI Design`, read operations validated) |
| Python environment initialised | Verified (Python 3.14.8 on Arch Linux; `pyproject.toml`, `.env.example`) |
| Laptop hardware, OS and GPU documented | Verified (Intel i5-1235U, 7.4GiB RAM, Arch Linux, no dedicated GPU) |
| CI (lint, tests, file-size check, secret scan) running | Verified (GitHub Actions PR run `41440805215` and push run `41440800224` all 4 checks passed) |

## Model status

| Model | Spec approved | Notebook written | Trained by user | Artifacts supplied | Integration verified (real inference) |
|---|---|---|---|---|---|
| `title-expander` (ML-001) | Approved (Gate 4) | Yes (`notebooks/01_train_title_expander.ipynb`) | Yes | Yes (v1.0.0, SHA-256 verified) | Pending (needs `torch` in .venv) |
| `similarity-evaluator` (ML-002) | Approved (Gate 4) | Yes (`notebooks/02_train_similarity_evaluator.ipynb`) | Yes | Yes (v1.0.0, SHA-256 verified) | Verified (real ONNX inference: 0.7755) |
| `application-tailor` (ML-003) | Approved (Gate 4) | No | No | No | No |

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

See `docs/DECISIONS_PENDING.md`. Count of open items: 0

## Session log (newest first)

| Date | Summary | Branch / PR |
|---|---|---|
| 2026-11-07 | Fix for search link extraction (relative /url?q= and regional Google domains), cookie consent dismissal, debug snapshot dumping on 0 results, and comprehensive file logging (logs/findrr.log) implemented. 116 tests passing with 85% coverage. Opened PR #11. | fix/search-logging-and-link-extraction / PR #11 |
| 2026-11-07 | PR #10 merged into `main` by user. Switched to `main`, pulled merge commit `f1653fe`. Deleted local fix branch. Model 2 real ONNX inference verified live on CPU (0.7755). Milestone 1 baseline complete. | main |
| 2026-11-07 | Fix for ONNX LayerNormalization batch size mismatch implemented and verified against real trained Model 2 artifacts (similarity score: 0.7755). Added FINDRR_DOCS_DIR support. 106 tests passing with 85% coverage. Opened PR #10. | fix/onnx-evaluator-batching / PR #10 |
| 2026-11-07 | PR #9 merged into `main` by user. Switched to `main`, pulled merge commit `b80705a8ce0b09804e84e55e094f6153648eb4cb`. Deleted local feature branch. Closed Milestone 1, Iteration 4. Milestone 1 Core CLI baseline complete (105 tests passing, 86% coverage). Ready for Milestone 2. | main |
| 2026-11-07 | Milestone 1, Iteration 4 implemented and verified (US-010, US-011). Job requirement keyword extraction, profile-to-job fact matching, zero-fabrication grounding validation, deterministic CV and cover letter drafting, and `findrr apply` CLI commands added. 105 tests passing with 86% coverage. Opened PR #9. | feature/iteration-4-app-prep / PR #9 |
