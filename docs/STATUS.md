# Findrr: Project Status

> Read at the start of every session. Update at the end of every session.
> Record only facts. Mark anything not actually performed and verified as **unverified** or **not started**.
> Keep this file short. Move old session-log entries into `docs/archive/` when the log exceeds 5 entries.

## Snapshot

| Field | Value |
|---|---|
| Last updated | 2026-11-28 |
| Current milestone | Milestone 2 (Additional Functionality) |
| Current phase | Milestone 2, Iteration 6 (US-017 done; US-014 blocked on D-005) |
| Current iteration | Milestone 2, Iteration 6 |
| Current branch | refactor/claude-skills-migration |
| Open PR | see "Awaiting merge or approval" |
| Latest release | None |

## Current task

The autonomous run is paused: every remaining item is gated on the user (see below). Iteration 6 delivered US-017 (PR #19). US-014 waits for D-005.

## Awaiting merge or approval

- Awaiting merge: PR #50 (migration of skills and workflows to `.claude/skills/`; moves the merge-policy file and edits an AGENTS.md §2 path, so it needs user review). Unblocks: nothing else depends on it.
- Decide D-002 (discovery source): the chosen Google Programmable Search JSON API is closed to new customers and ends on 2027-01-01. Free-only sources researched (see D-002): recommended ATS adapters (Greenhouse, Lever, Workable, Recruitee) now, plus Careerjet once a fixed IP is available.

## Next step

1. US-012 DOCX/PDF export (D-003: `python-docx` + `fpdf2`).
2. US-014 company research, extractive (D-005).
3. ML-003 dataset spec and notebook 03 rewrite with template-composed targets (D-006); user review before any Kaggle run.
4. ML-001 quality finding: skills can pull results off-topic ("Software Developer" + "Python, SQL, Git" → postal clerks). Investigate the training data (how O*NET skills are sampled per occupation) and propose a fix; it needs your approval before retraining.
5. When D-002 is decided: search-provider change and driver clean-up.

## Blockers

- Live discovery needs a person to solve the Google CAPTCHA (see D-002).

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
| `title-expander` (ML-001) | Approved (Gate 4; amended by D-004, D-007, D-009, D-010) | Yes (v2.1.0 ONNX export, PR #40) | Yes (run 5, 2026-11-27; v2.0.0) | Yes (`models/title-expander/v2.1.0/`, SHA-256 verified; v2.0.0 superseded) | **Yes**, 2026-11-27 (v2.1.0 ONNX): all Kaggle metrics identical to v2.0.0; laptop precision 0.828, 456 ms mean, peak 486 MB, no PyTorch |
| `similarity-evaluator` (ML-002) | Approved (Gate 4; amended by D-008) | Yes (`notebooks/02_train_similarity_evaluator.ipynb`) | Yes (2026-11-26) | Yes (`models/similarity-evaluator/v1.1.0/`, SHA-256 verified) | **Yes**, 2026-11-27: Kaggle values reproduced exactly; 119 MB after PR #37 |
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

See `docs/DECISIONS_PENDING.md`. Count of open items: 1

## Session log (newest first)

| Date | Summary | Branch / PR |
|---|---|---|
| 2026-11-28 | Antigravity retired: moved all 10 workflows and 7 skills from `.agents/` to `.claude/skills/<name>/SKILL.md` (`git mv`), rewrote every description to say concretely when to use it, repointed the merge policy to `.claude/skills/open-pr/SKILL.md` §3 (AGENTS.md, `pull-request` skill, project plan) and deleted `.agents/`. Added `CLAUDE.md` (imports `AGENTS.md`) and ignored `.claude/settings.local.json`. Claude Code lists all 17 skills. Lint, tests and CI scripts pass locally. Opened PR #50 (user review). | refactor/claude-skills-migration / PR #50 |
| 2026-11-27 | D-002: researched free discovery sources from the providers' own pages (Tavily, Brave, Adzuna, Greenhouse, Lever, Ashby, Jooble, Serper, DuckDuckGo and SearXNG); options and recommendation revised. D-006 option 1 reconfirmed by the owner (pivot to a text generator only if needed). | docs/d002-free-provider-research |
| 2026-11-27 | Owner decisions recorded: D-003 option 2 (`python-docx` + `fpdf2`), D-005 option 1 (extractive research), D-006 option 1. For D-006, the owner preferred option 2 on their Claude subscription only if allowed; the Consumer Terms forbid using the Services to train models and forbid scripted access without an API key. D-002 stays open: the chosen Google Programmable Search JSON API is closed to new customers and ends on 2027-01-01; options revised. | docs/record-d002-d006-decisions |
| 2026-11-27 | Dashboard Development tab shows a "Project status" section parsed from this file (snapshot, model table, model-related open items, recent model work); the build now reads real-inference verification from the model table instead of a hard-coded list. New idle-machine benchmark of the current bundles: ML-001 v2.1.0 (ONNX) 391 ms mean per request, peak process memory 481 MB (budget < 550 MB); ML-002 v1.1.0 3.1 ms per pair. | feature/dashboard-project-status |
| 2026-11-27 | Installed and verified ML-001 v2.1.0 (user's Kaggle re-export of the v2.0.0 weights to ONNX, no retraining). SHA-256 verified; every Kaggle metric identical to v2.0.0 (precision 0.851); ONNX parity 3.8e-5. Laptop, full test set through the app's ONNX path: precision 0.828, 456 ms mean latency, RSS 426 MB after load and 486 MB peak (budget < 550 MB), no PyTorch; 200/200 suggestions identical to v2.0.0 PyTorch. Wrote `title-expander-2.1.0.md`; model card, registry (Verified) and spec (memory budget approved via PR #40) updated. The skills defect remains. | docs/ml-001-v2.1.0-evaluation / PR #44 |
| 2026-11-27 | D-012 delivery: claude.ai's GitHub entry is an integration, not a callable connector, so the dashboard is kept current by the cloud scheduled task "Findrr dashboard sync" (fires on PRs merged into `main`; uploads only changed dashboard files). Hand-tested: 34 s, all writes succeeded. Trigger configured in the claude.ai form by the owner; this PR's merge is its first live test. | docs/dashboard-sync-routine |
| 2026-11-27 | D-011 and D-012 (owner decisions): added `scripts/model_dashboard/`, the source and data of the Findrr Model Observatory dashboard: `page.html`, `dashboard.json`, `bench.py`, `build.py`, committed `data/`, and a `pre-commit` hook that rebuilds and stages `data/` before each commit (never blocks; no-op without the bundles). Decisions are parsed from this log. Not part of the app; real CPU inference only, no training. Laptop benchmark on an idle machine (before PR #37): ML-001 mean 611 ms per request (budget 1,500), ML-002 5.7 ms per pair (budget 50). A run on a saturated machine (load 13) was discarded; `bench.py` now refuses to save busy runs. The build follows the registry: after PR #40 it shows ML-001 v2.1.0 awaiting its Kaggle run, with metrics from v2.0.0. Hook not yet installed (`git config core.hooksPath scripts/model_dashboard/hooks`); GitHub connector for live reads not yet connected. | feature/model-dashboard-tool / PR #38 |
| 2026-11-27 | D-004 resolved by the user: option 1, ONNX fp32 with a KV cache. New `t5_onnx_decoding` (NumPy beam search, shared with the notebook) and `t5_onnx_export` (decoder step written against the weights, parity-checked). `TitleExpanderRunner` no longer uses PyTorch. ML-001 v2.1.0 registry entry. Notebook 01 exports and evaluates the ONNX files, and can reuse an accepted v2.0.0 bundle without retraining. Local evidence on the v2.0.0 weights: logit difference 3.8e-5, 200/200 outputs identical to PyTorch, 435 MB after load, peak 486 MB over 400 requests (was 994–1,248 MB). Found: skills can pull ML-001 off-topic. Opened PR #40 (user review). | feature/ml-001-onnx-kv-cache / PR #40 |
| 2026-11-27 | Installed ML-002 v1.1.0 and ML-001 v2.0.0 (run 5) bundles; both pass acceptance and real inference is verified. Local full test-set re-evaluation through the app runners: ML-001 precision 0.828 (Kaggle 0.851; the runner drops the input title), 407 ms; ML-002 identical to Kaggle, 2.8 ms per pair. PR #37 (self-merged): the ML-002 tokenizer no longer pulls in PyTorch, 659 → 119 MB with identical scores. Wrote evaluation reports and model cards and marked both models Verified in the registry. A local ML-001 ONNX prototype gives identical outputs at 531 MB; INT8 variants fall to 0.685–0.728. D-004 updated with the evidence. | docs/ml-001-002-evaluation-reports |
| 2026-11-27 | D-010 option 1 implemented: up to 30 O*NET job titles per occupation as training-only inputs (train 42,624 examples, 22,967 input titles; val/test unchanged, no overlap), 15 epochs, repetition penalty off (runner reads it from `preprocess_config.json`), training-sample precision reported. 193 tests pass. | feature/ml-001-more-anchors / PR #36 |
| 2026-11-27 | D-010 revised with local inference on the run-4 bundle (500 inputs): penalty off 0.591, 4 beams 0.568, first-title occupation lock 0.635, training inputs 0.727. The model under-fits; decoding changes cannot reach 0.75. Found the bundle's threshold edited to 0.0. | docs/d-010-revised |
| 2026-11-27 | ML-001 Kaggle run 4 (user, input-title split): occupation precision 0.603 (target 0.75) failed. Local analysis: `repetition_penalty=1.2` penalises shared words, and 97% of gold outputs repeat a word across titles; the constraint already prevents repeats. Raised D-010. | docs/d-010-ml-001-decoding |
| 2026-11-26 | D-009 resolved by the user: option 1. Notebook 01 now splits by input title (hashed per normalised anchor; no wording crosses splits; every occupation trained on). Local data prep: 21,304/2,720/2,525 examples, no anchor overlap, test occupations all in training; broad-group baseline 0.732, same-detailed-SOC 0.929. Reports precision on never-seen wording (110 examples). 192 tests pass. | feature/ml-001-title-split |
| 2026-11-26 | ML-001 Kaggle run 3 (user, with the PR #31 fix): occupation precision 0.478 (target 0.75) failed; valid ratio 1.0, repetition 0.0001 and AC-ML-001.1 5 passed. Local analysis: the occupation-disjoint split means only 17.5% of test reference titles were ever training targets, and the 0.736 baseline behind the 0.75 threshold wrongly included the test occupations' own titles; the fair broad-group baseline is 0.579. Raised D-009. | docs/d-009-ml-001-precision |
| 2026-11-26 | ML-001 Kaggle run 2 (constrained decoding, user): occupation precision 0.521 (target 0.75), valid ratio 1.0, repetition 0.280 (target < 0.05), AC-ML-001.1 2 (target 3). The repetition was a bug in `TitleTrieConstraint`: a repeat was blocked only once complete, so beam search spelled it out and then had to stop. Each node now counts titles below it, and branches whose titles are all used are closed. Verified with the real tokenizer and batched beam search, with the repetition penalty off: repetition 0.0 on 96 test inputs. 191 tests pass. Re-run needed. | fix/title-constraint-dead-ends |
| 2026-11-26 | D-008 resolved by the user: Pearson r removed from the ML-002 acceptance gate and kept as a reported metric. Updated the notebook generator and notebook 02, the model spec (§8, §14), the training doc and the SRS ML-002 criteria; added a regression test. | feature/ml-002-ungate-pearson / PR #30 |
| 2026-11-26 | PR #27 (ML-001 constrained decoding) merged by the user (`2a2463a`). This confirms occupation precision >= 0.75 as the ML-001 acceptance threshold. Verified that PR #28 (D-008, from another session) merged consistently with #27 (docs only; 6 open decisions). 189 tests pass on `main`. Next: re-run notebook 01; decide D-008. | docs/record-pr-27-merge |
| 2026-11-26 | First Kaggle run of ML-002 v1.1.0 (user): the acceptance gate stopped the export. Pearson r 0.745 (target 0.85) failed; precision at 0.70 0.963, AC-ML-002.1 0.894 and AC-ML-002.2 0.248 passed. Local analysis on the rebuilt test pairs: the untrained base model scores Pearson 0.614, and the O*NET proxy labels disagree with title meaning in both directions. Raised D-008. | docs/d-008-ml-002-acceptance |
| 2026-11-26 | D-007 resolved by the user: option 1. Implemented `findrr.ml.title_constraint` (token trie over 45,712 O*NET titles; no invented or repeated titles), embedded verbatim in notebook 01. The runner decodes with it and requires `titles.json`. Occupation precision replaces ROUGE-L (threshold 0.75 PROPOSED, from baselines 0.007/0.12/0.736). Fixed a stray-bracket bug in title cleaning. End-to-end smoke test passed (untrained base model, no training). 189 tests pass. Opened PR #27. | feature/ml-001-constrained-decoding / PR #27 |
| 2026-11-26 | First Kaggle run of ML-001 v2.0.0 (user): the acceptance gate stopped the export. ROUGE-L 0.194, valid ratio 0.554, repetition 0.580, AC-ML-001.1 passed. Local analysis: ideal answers score ROUGE-L 0.27–0.66, so the 0.75 target is unreachable; repetition and invalid titles are real model defects. Raised D-007. | docs/d-007-ml-001-evaluation |
| 2026-11-26 | User report: notebook 01 failed on Kaggle (Python 3.13) with `cannot import name 'is_flax_available'`. The environment cell imported the preinstalled transformers 5.x before the pinned 4.46.3 install, mixing versions. The report now reads metadata only, and a version-guard cell says to restart if the versions are mixed. Verified in a Python 3.13 + torch 2.15 environment: all imports, both trainer argument sets and both tokenizers work (no training). Regression test added. | fix/notebook-import-order |
