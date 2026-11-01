---
name: pull-request
description: Use when finishing a task, preparing a PR, or checking the definition of done.
---

# Pull Request & Documentation Maintenance (Findrr)

Every Pull Request (PR) must deliver a complete, verified increment where code, tests, and documentation evolve together in lockstep.

## Core Gatekeeping Rules

1. **Documentation Sync**: Never open or approve a PR that modifies system behavior without updating the corresponding documentation in the same branch.
2. **No Untested PRs**: Code generation alone does not qualify for a PR. Include test execution results and explicitly distinguish between real and mocked ML inference.
3. **Branches Only, Never Merge**: Work only on a `feature/`, `fix/`, `docs/` or `refactor/` branch. Never commit to `main`. Never merge a PR. After opening one, record `Awaiting merge: PR #N` in `docs/STATUS.md`, start no work that depends on it, and end your turn. The user merges and tells you. If the user rejects the PR, address the feedback on the same branch and stop again.
4. **Git Hygiene & Security**: Verify that no binary model weights (`.pt`, `.pth`, `.bin`, `.safetensors`, `.onnx`), large datasets, local environment paths, or secrets/credentials are staged in the diff.

## Definition of Done

A feature or iteration is **done** only when every item below is satisfied. See `docs/process/definition-of-done.md` for the full criteria.

**Standard software:**
- [ ] Requirements analysed; design consistent with approved architecture
- [ ] Implementation satisfies approved requirements
- [ ] Acceptance criteria evaluated and passed
- [ ] Relevant automated tests executed and passing
- [ ] Regression tests passing
- [ ] Relevant documentation updated
- [ ] Known limitations and unresolved defects documented
- [ ] Implementation submitted through the required review process

**Additional criteria for ML functionality:**
- [ ] Model Specification documented
- [ ] Kaggle training notebook complete
- [ ] Training and evaluation pipelines implemented
- [ ] Model satisfies approved evaluation criteria (see `docs/ml/evaluation-policy.md`)
- [ ] Notebook exports required artifacts
- [ ] Artifact formats compatible with inference implementation
- [ ] Application successfully loads supplied artifacts
- [ ] Inference produces expected outputs and satisfies acceptance criteria
- [ ] Absence of user-provided artifacts recorded as an outstanding dependency; mocked inference **not** treated as successful integration

## Pre-PR Verification Workflow

Before generating a PR or drafting its description, execute the following checks against `git status` and `git diff`:

### 1. Documentation Maintenance Audit
Inspect the diff against the following triggers. If any area below was modified, verify that its corresponding documentation has been updated in the branch before finalizing the PR:

| If the code changes... | You must update... |
| :--- | :--- |
| **Requirements or Scope** | Requirements specification, traceability matrix, and acceptance criteria. |
| **System Architecture** | Architecture diagrams, module boundary docs, and component interaction specs. |
| **Module / UI Interfaces** | Component contracts, internal interface definitions, and UI/UX documentation. |
| **Database Structure** | ER diagrams, schema definitions, migration guides, and data dictionary docs. |
| **API Contracts** | OpenAPI/Swagger specs, endpoint documentation, request/response schemas, and error codes. |
| **Model Specifications** | Model registry metadata, input/output tensor schemas, version tags, and checksum manifests. |
| **Training Procedures** | Kaggle notebook markdown headers, hyperparameter docs, dataset attachment guides, and evaluation reports. |
| **Operational Procedures** | Deployment guides, environment variable templates (`.env.example`), artifact transfer instructions, and runbooks. |

*Note: During iteration closure or release PRs, perform a comprehensive cross-check across all documentation files to ensure zero drift between the codebase and project docs.*

### 2. Artifact & Security Audit
- Confirm `.gitignore` excludes binary ML artifacts and temporary test outputs.
- Verify no hardcoded API keys, tokens, or local user paths exist in the committed code or Kaggle notebooks.

### 3. Testing & QA Audit
- Run the relevant unit, integration, and regression test suites.
- If the PR touches ML components (Module 9 or Kaggle notebooks), verify whether tests ran against **Real Artifacts** or **Mocks/Stubs** and record the exact status.

## Required Pull Request Template

The repository template is `.github/pull_request_template.md`, and GitHub pre-fills it for new PRs. Use it for every Pull Request description. If it is missing, recreate it from the structure below and tell the user. Keep the two identical.

```markdown
## Summary
<!-- Concise explanation of what changed and why. -->

## Requirements Addressed
<!-- Requirement IDs (FR-, NFR-, BR-, ML-, AC-), module, phase or backlog items. -->

## Implementation Approach
<!-- How it was built: design, components touched, key decisions and trade-offs. -->

## Changes Made
- **Code / Modules**: 
- **Tests Added / Updated**: 
- **Configuration / Dependencies**: 
- **Database Migrations / Configuration Changes**: <!-- or "None" -->

## Screenshots
<!-- UI changes only. Otherwise write "N/A". -->

## Documentation Maintenance Checklist
<!-- Mark [x] for updated items, or [~] with "N/A - no changes to this layer" -->
- [ ] **Requirements**: Updated requirements/traceability docs (or N/A)
- [ ] **Architecture**: Updated architecture/module design docs (or N/A)
- [ ] **Interfaces**: Updated internal module/UI interface contracts (or N/A)
- [ ] **Database Structure**: Updated schema docs and migrations (or N/A)
- [ ] **API Contracts**: Updated endpoint specs and payload schemas (or N/A)
- [ ] **Model Specifications**: Updated model registry, version metadata, and schemas (or N/A)
- [ ] **Training Procedures**: Updated Kaggle notebook docs and dataset guides (or N/A)
- [ ] **Operational Procedures**: Updated setup, deployment, or artifact transfer runbooks (or N/A)

## Verification & Testing
- **Unit / Integration Tests**: <!-- Pass/Fail count and command run -->
- **Regression Suite**: <!-- Pass/Fail status -->
- **ML Integration Status**: <!-- Choose one: "N/A", "Verified with Real Artifacts", or "Unverified (Tested with Mocks/Fixtures Only)" -->

## Machine Learning Changes
<!-- If none, write "N/A". Otherwise list: new or modified Kaggle notebooks, model specifications, model integrations and inference changes, model name/version, and evaluation results (supplied by the user; never fabricated). -->

## Known Issues / Limitations
<!-- Unresolved defects, edge cases, technical debt, unverified dependencies (e.g. missing artifacts). Write "None known" only if verified. -->

## Security & Repository Hygiene
- [ ] No binary model weights or large datasets committed to Git
- [ ] No secrets, credentials, or local machine paths included
- [ ] Model artifact checksums/registry updated (if applicable)
```
