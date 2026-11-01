---
name: srs-and-traceability
description: Use when writing or changing the SRS, requirement IDs, backlog items, or the traceability matrix.
---

# Requirements Analysis & Traceability

Ensure rigorous definition, progressive refinement, and end-to-end traceability across product strategy, functional/non-functional specifications, machine learning workflows, testing, and release management.

## When to Use

* When conducting requirements analysis, identifying stakeholders, workflows, business rules, constraints, and data/integration needs.
* When authoring or updating the Software Requirements Specification (SRS) and Prioritized Product Backlog.
* When establishing, updating, or reviewing traceability matrices linking product requirements and ML assets to design, code, test cases, and releases.
* When defining machine learning requirements, model objectives, input/output tensors, inference rules, and acceptance criteria.

---

## Templates and Source Documents

* **SRS outline, ID scheme, acceptance-criteria format and backlog contents:** Follow `docs/templates/srs-outline.md`. Do not invent a different structure or ID scheme.
* **Initial specification:** `docs/spec/` (overview, modules 1-9, cross-cutting requirements) is the initial specification. It is not an approved requirement until it has been written into the SRS and the user has approved the SRS.
* **Unresolved items:** Label each item confirmed, approved, proposed, assumption or unresolved. Document every significant assumption with its potential impact. Record unresolved items in `docs/DECISIONS_PENDING.md`. Never promote an unresolved question to a requirement.

---

## 1. Requirements Analysis & Refinement

Determine what the software needs to do by translating business objectives and user needs into clear, actionable, and testable requirements.

### Key Activities & Identification
You must identify and document:
* **Functional Requirements:** What the application must do (e.g., user profile management, job search title generation, job posting discovery, model loading and inference, CV/cover letter preparation).
* **Non-Functional Requirements:** Quality attributes and operational constraints (e.g., security/privacy, external-service failure handling, performance, maintainability, inference speed, artifact handling). *Must be measurable wherever possible.*
* **Stakeholders & Context:** User categories, workflows, use cases, business rules, system constraints, external dependencies/integrations, and data requirements.
* **Module Specifications:** Inputs, outputs, and responsibilities for each module.
* **Machine Learning Requirements:** Intended responsibilities, expected inputs/outputs, training/inference requirements, training data needs, evaluation criteria, and artifact delivery/integration requirements.

### Progressive Refinement
* Analyze selected requirements at the beginning of each iteration to establish expected functionality, inputs, outputs, constraints, dependencies, and acceptance criteria.
* Refine requirements iteratively based on stakeholder feedback and previous findings.

---

## 2. Deliverables & Unique Identifiers

### Primary Deliverables
1. **Software Requirements Specification (SRS):** The authoritative source for approved application requirements (covering project purpose, scope, user characteristics, system context, functional/non-functional requirements, use cases, user stories, business rules, data/interface/integration specs, security, ML requirements, constraints, assumptions, and glossary).
2. **Prioritized Product Backlog:** Prioritized features, user stories, implementation tasks, acceptance criteria, and dependencies.

### Unique Requirement Identifiers
Use standardized tags across documentation and traceability links:
* `FR-001`: Functional requirement
* `NFR-001`: Non-functional requirement
* `BR-001`: Business rule
* `ML-001`: Machine learning requirement
* `AC-001`: Acceptance criterion (described using observable/testable outcomes, ideally Given/When/Then structures).

---

## 3. Traceability Hierarchy & Linkages

Maintain explicit bi-directional links across the entire lifecycle:

1. **Strategy & Product Layer:**
   * Business Objectives (`FR`, `NFR`, `BR`)
   * Functional Requirements
   * User Stories
   * Acceptance Criteria (`AC`)

2. **Engineering & Architecture Layer:**
   * Design Decisions
   * Implementation Components
   * Test Cases
   * Releases

3. **Machine Learning & AI Layer:**
   * Model Specifications (`ML`)
   * Training Notebooks
   * Model Versions
   * Evaluation Reports
   * Model Artifacts
   * Inference Implementations

---

## 4. Step-by-Step Workflow

1. **Analyze & Specify:** Formulate unique identifiers (`FR`, `NFR`, `BR`, `ML`, `AC`), build the SRS, and populate the prioritized backlog.
2. **Decompose to Stories:** Translate requirements into user stories with testable acceptance criteria.
3. **Bridge to Engineering & ML:** Link user stories to architecture design decisions, implementation components, model specifications, and training notebooks.
4. **Verify & Test:** Connect test cases, evaluation reports, model artifacts, and inference implementations back up to originating requirements.
5. **Audit Coverage:** Periodically review the traceability matrix to guarantee that every important requirement is fully accounted for through implementation, testing, and release.
