---
name: start-iteration
description: Use at the start of each iteration to plan scope, analyse requirements and design the increment, and to create the working branch before implementing.
---

# Iteration Planning, Requirements Analysis & System Design

Govern the preparatory phases of each development iteration, ensuring rigorous planning, detailed requirements analysis, and robust architectural system design before implementation begins.

## When to Use

* At the start of a new iteration to review the roadmap and backlog, establish scope, and identify deliverables.
* When conducting detailed requirements analysis for selected user stories, defining acceptance criteria, business rules, edge cases, and machine learning requirements.
* When designing the system architecture for an increment, identifying affected components, database migrations, API contracts, UI/UX changes, and ML notebook/inference integration.

---

## Step 0: Session Start and Branch Setup

Before planning anything:
1. **Read State:** Read `docs/STATUS.md` and `docs/DECISIONS_PENDING.md`.
2. **Check Preconditions:** Confirm bootstrap gates 1-5 and "Final approval to begin implementation" are **Approved** in `STATUS.md`. If not, stop and tell the user which are outstanding. Confirm there is no `Awaiting merge` entry. If there is one, stop and wait for the user.
3. **Respect Open Decisions:** Do not work on anything blocked by an open item in `docs/DECISIONS_PENDING.md`.
4. **Sync:** Switch to `main` and pull the latest changes.
5. **Create the Branch:** Create a new branch from `main` using the prefix that fits the work: `feature/`, `fix/`, `docs/` or `refactor/` (for example `feature/iteration-N-short-name`). Never work on `main`.
6. **Update STATUS.md:** Set "Current iteration" and "Current branch", and set the current task.

---

## Step 1: Iteration Planning

Review project direction and establish clear boundaries for the upcoming iteration:
* **Review Roadmap & Backlog:** Evaluate the high-level roadmap and current product backlog priorities.
* **Select Requirements:** Identify the specific user stories and features targeted for the iteration.
* **Establish Scope:** Define clear iteration objectives and expected deliverables.
* **Assess Risks & Dependencies:** Identify technical, operational, and scheduling dependencies or risks.
* **ML Work Planning:** Pinpoint any relevant model-development (Kaggle notebooks) or server-side inference work required during the iteration.

---

## Step 2: Requirements Analysis

Analyze selected requirements deeply to eliminate ambiguity and define testable outcomes:
* **Analyze & Detail:** Examine selected requirements, identify missing information, surface edge cases, and define business rules.
* **Acceptance Criteria:** Establish clear, testable acceptance criteria (ideally Given/When/Then).
* **Documentation Update:** Update the Software Requirements Specification (SRS) and product backlog.
* **Material Approvals:** Request explicit approval for any material requirement changes.
* **Machine Learning Requirements:** For ML functionality, explicitly establish:
  * Model purpose and expected inputs/outputs
  * Training data specifications
  * Evaluation methodology and metrics
  * Inference requirements and server-side artifact expectations
  * Deployment constraints

---

## Step 3: System Design

Design the technical implementation approach and architecture for the iteration:
* **Component Impact:** Identify all affected codebase components and review existing architecture.
* **Implementation Approach:** Determine how features will be built and integrated.
* **Database & Interfaces:** Identify required database schema changes and define explicit API and interface contracts.
* **UI/UX Design:** Determine user interface and experience changes (incorporating Penpot design approvals where applicable).
* **Decision Documentation:** Record significant technical decisions and architectural trade-offs.
* **Approval Gate:** Obtain explicit user approval for any material architectural changes.
* **Machine Learning Design:** For ML functionality, establish Kaggle training notebook design, expected artifact formats/checksums, server-side model loading, and inference integration patterns (Module 9).

---

## Hand-off to Development

When Steps 1-3 are complete, update `docs/STATUS.md` (current task, "Next step" = implement on the current branch). Record any new ambiguity in `docs/DECISIONS_PENDING.md`. If Step 2 or Step 3 needs material approval from the user, stop and wait before implementing. Otherwise implement on the branch, run `/open-pr` when finished, and never merge.
