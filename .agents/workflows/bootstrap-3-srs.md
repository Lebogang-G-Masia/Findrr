---
name: bootstrap-3-srs
description: Use after bootstrap-2 is approved to write the initial SRS and prioritised product backlog, then stop for user approval.
---

# Initial Requirements Specification & Analysis

Conduct rigorous requirements analysis across all application descriptions and modules to establish the foundational product scope, architecture boundaries, and machine learning specifications for Findrr.

## When to Use

* At the start of requirements analysis after initial planning.
* When analyzing application descriptions, modules, and workflows to identify missing or ambiguous requirements.
* When specifying user profiles, module responsibilities, database entities, data requirements, job relevance criteria, document generation, app management, integrations, and security/privacy rules.
* When defining machine learning requirements, model purposes, training/fine-tuning workflows, datasets, evaluation criteria, artifacts, and server-side inference pipelines.
* When authoring the initial Software Requirements Specification (SRS) and Prioritized Product Backlog.

---

## 1. Core Requirements Analysis Scope

Analyze all application modules and descriptions to explicitly establish:

* **User Profile Specification:** Complete structure of user profiles, preferences, and professional data.
* **User Workflows:** End-to-end supported user workflows across all features.
* **Module Responsibilities & Relationships:** Purpose, inputs, outputs, and inter-module dependencies for every application module.
* **Database Entities:** Required database schemas, core entities, and relationships.
* **Job Posting Data Requirements:** Structure, attributes, and extraction rules for job postings.
* **Job Relevance Criteria:** Scoring methodology, weights, thresholds, and distinction between title relevance and professional suitability.
* **Document-Generation Requirements:** Specifications for tailored CVs and cover letters.
* **Application-Management Workflow:** Tracking pipeline from discovered opportunities to submitted applications, interviews, and offers.
* **External Integrations:** Required third-party services and APIs.
* **Security & Privacy Requirements:** Data protection, access control, and credential handling rules.
* **Functional & Non-Functional Requirements:** Actionable capabilities and measurable quality attributes.

---

## 2. Machine Learning Requirements Scope

Establish comprehensive specifications for all AI/ML components:

* **Model Identification:** Required machine learning models and their exact functional purposes.
* **Training & Fine-Tuning Requirements:** Training approaches (scratch, fine-tuning, adaptation) executed via Kaggle notebooks.
* **Dataset Specifications:** Required training datasets, formats, and preprocessing rules.
* **Evaluation Criteria:** Task-appropriate evaluation metrics (Precision, Recall, F1, Accuracy, ROC-AUC, semantic similarity, ranking metrics) and acceptance thresholds.
* **Artifact Requirements:** Expected model artifact formats (e.g., `safetensors`, ONNX), sizes, checksums, and companion files (tokenizers, vocabularies, label mappings).
* **Server-Side Inference Requirements:** Integration rules for loading and executing inference on the Findrr application server (Module 9).

---

## 3. Ambiguity Resolution & Proactive Functionality

* **Identify Gaps:** Actively surface missing, contradictory, or ambiguous requirements across application descriptions.
* **Proactive Inclusion:** Identify and incorporate additional functionality necessary to achieve the application's objectives.
* **No Silent Omission:** Never silently omit necessary functionality merely because it was not explicitly described in initial prompts.

---

## 4. Primary Deliverables

Produce and record:
1. **Initial Software Requirements Specification (SRS):** The authoritative, comprehensive document covering project purpose, scope, user characteristics, functional/non-functional requirements, use cases, user stories, acceptance criteria, business rules, data/interface/integration specs, security, and machine learning requirements.
2. **Prioritized Product Backlog:** Initial prioritized features, user stories, implementation tasks, acceptance criteria, and cross-dependencies.

---

## 5. Approval Gate

When the deliverables are ready, update `docs/STATUS.md` with:
- What was completed, which requirements were confirmed, and which remain unresolved
- All open questions and ambiguities recorded in `docs/DECISIONS_PENDING.md`
- The next step (`/bootstrap-4-ml-plan`)

Then **stop and wait for the user to review and approve the initial SRS and Product Backlog** before proceeding to the ML development plan.
