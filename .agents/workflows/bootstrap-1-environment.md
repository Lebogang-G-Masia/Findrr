---
name: bootstrap-1-environment
description: Use at the very start of the project to create the private repository, branch protection, documentation skeleton, tooling and environment, then stop for user approval.
---

# GitHub Repository & Project Initialization

Establish the foundational project environment, private GitHub repository, repository protections, and initial directory structures for Findrr.

## When to Use

* At the very beginning of the project before any implementation work starts.
* When setting up the private GitHub repository and configuring branch protections.
* When establishing initial repository layouts, documentation structures, and development environments.
* When auditing or verifying tool access, hardware/OS constraints, and model training/inference environments.

---

## 1. Project Environment Setup

Execute and verify the following initialization steps:

1. **Verify Tooling Access:** Verify access to required development tools and connected services. Explicitly verify that the Penpot MCP is connected and usable (create or read a test file), and record the result in `docs/STATUS.md` under "Penpot MCP access works". If it is unavailable, report it and ask the user; UI design cannot start without it.
2. **Create Private Repository:** Create a private GitHub repository for Findrr.
3. **Establish Repository Structure:** Set up the initial codebase directory layout. Include `.github/pull_request_template.md` (it ships with the project files; commit it and check that its content matches the template in the `pull-request` skill).
4. **Create Documentation Skeleton:** Using `docs/process/documentation-map.md` as the reference, create the placeholder files for every document listed in that table, at exactly the paths it gives (do not invent other locations; skip the archived master prompt, which already exists). Record which files were created in `docs/STATUS.md`.
5. **Initialize Development Environment:** Set up local runtimes, package managers, and configuration templates (`.env.example`).
6. **Set Up Continuous Integration:** Create a CI workflow (for example GitHub Actions) that runs lint, the test suite, a file-size check (to block model weights and large datasets) and a secret scan. Push it, confirm it actually runs and passes on a branch, and record the check names and result in `docs/STATUS.md` under "CI ... running". Required status checks in step 7 can only name checks that exist.
7. **Configure Repository Protections:** Apply the protections in section 2 below, including the CI checks from step 6 as required checks. Set up branch protections suitable for a solo developer (ensuring approval rules do not block self-review/merging). Verify the resulting settings before recording them in `docs/STATUS.md`.
8. **Document Constraints:** Record available hardware, operating system, and development constraints.
9. **Identify ML Environments:** Document anticipated model-training (Kaggle) and server-side inference environments.

* **Verification Rule:** Do not claim a task has been completed unless it has actually been performed and verified.

---

## 2. GitHub Repository Protections

Configure repository protections (where supported by GitHub) while accommodating the fact that the user is currently the sole developer:

* Prevent direct pushes to `main`.
* Prevent force pushes to `main`.
* Require pull requests for changes to `main`.
* Require relevant automated checks (the CI checks from step 6) to pass.
* Require review feedback to be resolved.
* Restrict repository administration to authorized users.
* Protect important release references where appropriate.
* **Solo Developer Accommodation:** Do not introduce approval requirements that prevent the user from reviewing and merging their own pull requests.
* **Permissions & Truthfulness:** If lacking required GitHub permissions, identify this as a blocker and request access. Do not claim repository configurations have been completed unless they have been explicitly verified.

---

## 3. Approval Gate

When all setup steps are verified, update `docs/STATUS.md` with:
- What was completed and verified
- Any outstanding blockers or permissions issues
- The next step (`/bootstrap-2-plan`)

Then **stop and wait for the user's confirmation** before proceeding to the planning phase.
