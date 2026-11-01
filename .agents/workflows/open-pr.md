---
name: open-pr
description: Use when an increment is implemented and tested, to review it, open the pull request, record the hand-off in STATUS.md and stop.
---

# Review & Pull Request Workflow

Manage the formal review, verification, and Pull Request (PR) submission process for every completed implementation increment in Findrr.

## When to Use

* Following the completion of coding, testing, and QA verification for a feature branch (implementation and testing).
* When auditing documentation synchronization prior to opening a PR.
* When compiling implementation summaries, test execution results, known limitations, and ML-specific disclosures (notebooks, model specs, inference changes).
* When opening the Pull Request and presenting changes for user review.

---

## 1. Review & Pull Request Workflow

Execute and verify the following sequence before submitting any change:

1. **Review Implementation:** Inspect code changes, diffs, and architectural compliance against approved specifications.
2. **Verify Documentation:** Ensure all relevant documentation has been updated in lockstep with code changes (use the Documentation Maintenance Checklist in the `pull-request` skill).
3. **Prepare Implementation Summary:** Summarize the architectural approach and modules touched.
4. **Prepare Test Results:** Compile unit, integration, and regression test execution reports.
5. **Identify Known Limitations:** Document any edge cases, technical debt, or unaddressed issues.
6. **Confirm Branch:** Confirm the work is on a `feature/`, `fix/`, `docs/` or `refactor/` branch and not on `main`. Push the branch.
7. **Create Pull Request:** Draft and open the PR using `.github/pull_request_template.md` (format also in the `pull-request` skill). Do not merge it.
8. **Record the Hand-off in STATUS.md:** Update `docs/STATUS.md`: set "Open PR" and "Current branch", add `Awaiting merge: PR #N` under "Awaiting merge or approval", set "Next step" to "User reviews and merges PR #N, then runs `/close-iteration`", and add a session-log entry.
9. **Present for Review and Stop:** Present the changes, test results, known limitations and PR link to the user, then **end your turn**.

---

## 2. Machine Learning Disclosures in PRs

For any Pull Request involving machine learning functionality, you must explicitly identify and document:
* New or modified **Kaggle training notebooks**.
* Updated **model specifications** and registry metadata.
* **Model integrations** and server-side inference functionality (Module 9).
* Whether test execution used **Real Artifacts** or **Mocked/Synthetic Fixtures** (explicitly noting unverified mock status if real artifacts are pending).

---

## 3. Strict Gatekeeping Rule: Never Merge, Stop After the PR

* **Never merge.** Do not merge any pull request. Only the user merges.
* **Stop after opening the PR.** Once `Awaiting merge: PR #N` is recorded in `docs/STATUS.md`, start no work that depends on the PR and end your turn.
* **Resume only when told.** Continue when the user says the PR has been merged (then run `/close-iteration`) or gives review feedback.
* **If the user rejects or requests changes:** address the feedback on the same branch, update the PR, and update `docs/STATUS.md`. Then stop again. Do not merge.
