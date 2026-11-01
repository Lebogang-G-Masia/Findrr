---
name: close-iteration
description: Use after the user has merged the pull request, to close the iteration: backlog, docs, versioning, STATUS.md and next priorities.
---

# Iteration Closure & Retrospective

Manage the formal closure of development iterations, ensuring seamless backlog grooming, documentation synchronization, retrospective analysis, and planning for the subsequent iteration.

## When to Use

* Following the review, approval, and merging of Pull Requests for a completed iteration increment.
* During iteration closure to reconcile the product backlog against delivered features.
* When synchronizing all project documentation to prevent drift from the updated codebase.
* When conducting retrospectives, recording unresolved issues, capturing improvements, and establishing priorities for the next iteration.

---

## 1. Iteration Closure Workflow

**Precondition:** The user has told you the PR was merged into `main`. If they have not, do not start. Check `docs/STATUS.md` for `Awaiting merge`, and ask.

Execute and document the following steps upon completing an iteration:

0. **Sync and Verify:** Switch to `main` and pull. Confirm the merge actually happened (merge commit or PR state). Do not assume it.

1. **Update Product Backlog:** Reconcile the product backlog, marking completed user stories and tasks as done, adjusting estimates, and incorporating newly identified requirements.
2. **Update Project Documentation:** Ensure all documentation (SRS, architecture, database schemas, API specs, model registries, and operational runbooks) is fully updated to reflect changes introduced during the iteration (use the Documentation Maintenance Checklist in the `pull-request` skill).
3. **Record Completed Iteration:** Archive iteration deliverables, test results, acceptance assessments, and merge logs.
4. **Record Unresolved Issues:** Document any known limitations, technical debt, or unaddressed defects identified during testing.
5. **Identify Potential Improvements:** Capture process, architectural, tooling, or workflow enhancements surfaced during the iteration.
6. **Recommend Next Priorities:** Formulate data-driven recommendations and priority queues for the upcoming iteration.
7. **Versioning and Release Notes:** Follow `docs/process/versioning.md`. If the iteration completes a release, choose the SemVer version (`vMAJOR.MINOR.PATCH`), write release notes, and follow `docs/process/release-deployment.md`. Milestones are not releases. Record model versions separately from the app version. Do not tag or publish a release without the user's approval.
8. **Update STATUS.md:** Update `docs/STATUS.md`: remove the `Awaiting merge: PR #N` entry, clear "Open PR" and "Current branch", update "Current iteration", "Current milestone" and "Latest release" if they changed, update the Documents and Model status tables, add a session-log entry, and set "Next step" (normally `/start-iteration`).
9. **Update DECISIONS_PENDING.md:** Move resolved decisions out of the open list, add newly found ambiguities, and update the open-item count in `STATUS.md`.

---

## 2. Iteration Loop & Continuity

* **Iterative Lifecycle:** Repeat this closure workflow for all subsequent iterations across the project lifecycle.
* **Governance Rule:** Ensure all closure artifacts are recorded in the repository before starting implementation work in the next iteration.
* **Stop:** After updating `docs/STATUS.md`, report the closure summary and wait for the user to run `/start-iteration`. Do not start the next iteration on your own.
