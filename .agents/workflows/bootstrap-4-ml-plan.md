---
name: bootstrap-4-ml-plan
description: Use after bootstrap-3 is approved to write the ML architecture document and model specifications, then stop for user approval.
---

# Machine Learning Development Plan & Model Specifications

Establish the authoritative Machine Learning Development Plan and individual Model Specifications for all AI/ML models required by the approved Findrr scope, ensuring strict alignment before any training notebooks or pipelines are developed.

## When to Use

* During the machine learning planning phase after establishing the initial SRS and product backlog.
* When identifying, specifying, and documenting all machine learning models required across application modules.
* When defining model architectures, pretrained options, training/fine-tuning methodologies, dataset requirements, and Kaggle compute needs.
* When establishing server-side artifact formats, loading requirements, inference pipelines, and task-appropriate evaluation criteria.
* When authoring the Machine Learning Architecture Document and individual Model Specifications.

---

## 1. Core Model Specification Framework (13-Point Checklist)

For **every** machine learning model required by the approved application scope, you must define and document:

1. **Purpose:** The explicit functional role and objectives of the model within Findrr.
2. **Module Dependencies:** The application modules that depend on the model's outputs.
3. **Inputs & Outputs:** Exact expected input schemas/features and output tensor shapes or structured predictions.
4. **Architectures:** Evaluation of appropriate model architectures.
5. **Pretrained Models:** Identification of suitable pretrained base checkpoints.
6. **Training Methodology:** Determination of whether the model will be trained from scratch, fine-tuned, or adapted from an existing checkpoint.
7. **Datasets:** Required training, validation, and test datasets.
8. **Training & Evaluation Procedures:** Loss functions, optimization strategies, training duration, and evaluation metrics (e.g., Precision, Recall, F1, Accuracy, ROC-AUC, semantic similarity, ranking metrics).
9. **Kaggle Computational Requirements:** Hardware specifications, accelerators (GPU/TPU), and runtime limits required for training on Kaggle.
10. **Artifact Formats:** Expected model artifact formats (e.g., `safetensors`, ONNX) and companion files (tokenizers, vocabularies, label mappings, normalization configs).
11. **Server-Side Loading Requirements:** Application server loading rules, integrity checks (SHA-256 checksums), and complete bundle binding (Module 9).
12. **Inference Requirements:** Preprocessing parity, forward-pass execution (no-grad/eval mode), post-processing, schema validation, and latency/batching constraints.
13. **Acceptance Criteria:** Specific, measurable performance thresholds and behavioral criteria the model must satisfy before integration.

---

## 2. Primary Deliverables & Governance Rules

* **Primary Deliverables:**
  1. **Machine Learning Architecture Document:** Comprehensive overview of all project ML components, data pipelines, and serving infrastructure.
  2. **Individual Model Specifications:** Detailed standalone specifications for each model covering the 13-point checklist above.
* **Governance Rule:** **Do not develop training notebooks based on unapproved assumptions about model architectures or datasets.** All model parameters and specifications must be explicitly documented and approved in the model specifications before implementation begins.

---

## 3. Approval Gate

When the ML Architecture Document and every Model Specification are drafted, update `docs/STATUS.md`:
- Set gate "4. Machine Learning Development Plan" to **Presented for review**.
- Record what was completed, which model specifications are proposed vs. approved, and any assumptions or unresolved items.
- Record every open question in `docs/DECISIONS_PENDING.md` and update the open-item count in `STATUS.md`.
- Set "Next step" to `/bootstrap-5-design`.

Then **stop and wait for the user to review and approve the ML Development Plan and Model Specifications**. Do not start `/bootstrap-5-design`, and do not write any training notebook, until the user approves. When the user approves, set the gate to **Approved** and "Approved by user" to **Yes**.
