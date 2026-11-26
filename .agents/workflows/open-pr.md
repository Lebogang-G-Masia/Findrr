---
name: open-pr
description: Use when an increment is implemented and tested, to review it, open the pull request, and either merge it under the merge policy or hand it to the user.
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
7. **Create Pull Request:** Draft and open the PR using `.github/pull_request_template.md` (format also in the `pull-request` skill). Do not merge yet.
8. **Wait for CI:** Run `gh pr checks <N> --watch`. If a check fails, fix it on the branch and push. After 3 failed attempts, stop and hand the PR to the user.
9. **Merge or Hand Off:** Apply the merge policy (Section 3).
   - **Self-merge allowed:** run `gh pr merge <N> --merge --delete-branch`, switch to `main`, pull, and verify with `gh pr view <N> --json state,mergedAt` that the state is `MERGED`. Then run `close-iteration`.
   - **User review required:** update `docs/STATUS.md`. Set "Open PR" and "Current branch", and add `Awaiting merge: PR #N (<reason it needs review>)` under "Awaiting merge or approval". Set "Next step" to "User reviews and merges PR #N". Add a session-log entry. Present the changes, test results, known limitations and PR link, then wait. Start no work that depends on it.

---

## 2. Machine Learning Disclosures in PRs

For any Pull Request involving machine learning functionality, you must explicitly identify and document:
* New or modified **Kaggle training notebooks**.
* Updated **model specifications** and registry metadata.
* **Model integrations** and server-side inference functionality (Module 9).
* Whether test execution used **Real Artifacts** or **Mocked/Synthetic Fixtures** (explicitly noting unverified mock status if real artifacts are pending).

---

## 3. Merge Policy

The user authorised self-merging on 2026-11-26. You may merge your own PR only when **every** condition below holds:
1. All required checks (`Lint & Code Quality`, `Test Suite`, `File Size & Model Artifact Check`, `Secret Scanner`) pass on the PR's **latest** commit, as `gh pr checks` reports them.
2. Steps 1-7 above are complete, and the diff holds no secrets, personal data or model artifacts. The repo is public.
3. The PR is not in a **user-review category**:
   - a new or changed UI design, or UI code that implements a design the user has not approved,
   - a new or changed model specification, architecture, dataset, training methodology, artifact format or compatibility contract,
   - a new Kaggle training notebook, or a material change to one,
   - a new significant dependency (`docs/process/dependency-policy.md`),
   - security, privacy, authentication or scraping-compliance controls,
   - a release, a version tag or release notes,
   - a change to `AGENTS.md` hard rules, this merge policy or branch protection,
   - anything else on `docs/process/approval-gates.md` that the user has not already approved in writing (in chat, or in a resolved `DECISIONS_PENDING.md` entry).
4. The user has not asked to review this PR, and no unresolved review comment from the user is on it.

Routine work that implements already-approved requirements and designs may be self-merged. This covers features, fixes, tests, refactors, docs and closure records.

**Never:**
- merge with `--admin`,
- bypass, weaken or disable branch protection or CI,
- force-push to `main`,
- merge a PR that another person opened,
- merge to get past a failing check.

If the user later rejects a self-merged change, revert it through a new PR.

## 4. User-Review PRs

When a PR needs user review, record `Awaiting merge: PR #N` and wait.
- **Merged by the user:** verify the merge from the PR state, then run `close-iteration`.
- **Changes requested:** address them on the same branch, push, update `docs/STATUS.md` and wait again. Do not merge it yourself, even after the fixes. The user merges a user-review PR.
