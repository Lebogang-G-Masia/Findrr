# Findrr: Project Status

> Read at the start of every session. Update at the end of every session.
> Record only facts. Mark anything not actually performed and verified as **unverified** or **not started**.
> Keep this file short. Move old session-log entries into `docs/archive/` when the log exceeds 5 entries.

## Snapshot

| Field | Value |
|---|---|
| Last updated | 2026-11-26 |
| Current milestone | Milestone 2 (Additional Functionality) |
| Current phase | Milestone 2, Iteration 5 (Completed) |
| Current iteration | Milestone 2, Iteration 5 |
| Current branch | fix/execution-and-invariant-fixes |
| Open PR | PR #TBD |
| Latest release | None |

## Current task

Pre-Iteration-6 codebase audit and fixes, requested by the user on 2026-11-26. Execution and invariant fixes are on `fix/execution-and-invariant-fixes`. Module 3 wiring follows in its own PR. After that comes Iteration 6 (US-014).

## Awaiting merge or approval

- Approve D-002 (discovery source vs robots.txt and Google terms). Unblocks: compliant, unattended live discovery.
- Approve D-003 (DOCX/PDF library). Unblocks: US-012 and the Milestone 2 gate.
- Approve D-004 (torch for ML-001, or ONNX export). Unblocks: real ML-001 inference.
- Re-supply the model artifacts. `models/` (ML-001 and ML-002 v1.0.0, plus `manifest.json`) no longer exists on disk. It was lost alongside the 2026-11-26 deletion of `src/` and is gitignored, so it cannot be restored from git. Copy the Kaggle outputs to `models/<name>/v1.0.0/`. Unblocks: real inference (currently labelled MOCK).
- Optional: run `notebooks/03_train_application_tailor.ipynb` on Kaggle. Unblocks: real ML-003.

## Next step

1. Self-merge the fix PR when CI is green.
2. Wire Module 3 (search-term generation) into discovery: a separate PR.
3. Start Iteration 6 (US-014) via `/autonomous-run`.

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

See `docs/DECISIONS_PENDING.md`. Count of open items: 3

## Session log (newest first)

| Date | Summary | Branch / PR |
|---|---|---|
| 2026-11-26 | Codebase audit: ran lint, the 133-test suite, the full CLI flow on a scratch DB and one live headful search (CAPTCHA). Fixed: saved search bounds ignored; CAPTCHA page scraped; misleading halt message; snapshot location; availability marked ACTIVE without evidence (now evidence-based, stored via additive migration); fabricated posting date and title; apply-link resolution; unverified claims in CV and cover-letter templates; wrong closed count; hard-coded thresholds; `.env` never loaded and `.env.example` listing unread variables; manifest path traversal; crash on closed input; undeclared ML runtime deps. 147 tests pass. Raised D-002, D-003 and D-004, and corrected the backlog (US-012, Module 3 wiring). Opened PR #TBD. | fix/execution-and-invariant-fixes / PR #TBD |
| 2026-11-26 | Repo made public by the user. Scanned tracked files and history for secrets and personal data: none found, apart from the author email in `pyproject.toml`. Configured and verified `main` branch protection. On user instruction, replaced the never-merge rule with a self-merge policy (`open-pr` §3) across AGENTS.md, workflows and the pull-request skill. Opened PR #16. | docs/self-merge-policy / PR #16 |
| 2026-11-26 | PR #15 (autonomous-run workflow) merged by the agent on explicit user instruction (`6c2fbb5`). | main |
| 2026-11-26 | Found unexplained unstaged deletion of all source/tests/notebooks on `main`; restored them from `9442c70` on user's instruction (133 tests pass). Added `.agents/workflows/autonomous-run.md` and an AGENTS.md pointer. Opened PR #15. | docs/autonomous-run-workflow / PR #15 |
| 2026-11-07 | PR #14 merged into `main` by user. Switched to `main`, pulled merge commit `9442c70`. Deleted local branch. Closed Milestone 2, Iteration 5. Application status tracking, metrics dashboard, Model 3 notebook and runners verified. | main |
| 2026-11-07 | Milestone 2, Iteration 5 implemented: application lifecycle status transitions (`findrr apply status`), search & application metrics dashboard (`findrr dashboard`), Model 3 Kaggle notebook (`notebooks/03_train_application_tailor.ipynb`), and Model 3 runners. 133 tests passing with 84% coverage. Opened PR #14. | feature/iteration-5-app-tracking-and-model-3 / PR #14 |
| 2026-11-07 | PR #13 merged into `main` by user. Switched to `main`, pulled merge commit `9295ee6`. Deleted local fix branch. Google /goto?url= redirect link extraction and CI check ignore rules verified. | main |
| 2026-11-07 | Fix for Google /goto?url= redirect link extraction and CI check ignore rules implemented. 121 tests passing with 85% coverage. Opened PR #13. | fix/support-google-goto-redirects / PR #13 |
| 2026-11-07 | PR #12 merged into `main` by user. Switched to `main`, pulled merge commit `4d9a1f7`. Deleted local fix branch. Human-in-the-loop CAPTCHA completion prompt in headful CLI and persistent Chrome profile verified. | main |
