# Findrr Model Registry & Catalog

- **Document Version:** 1.0.0
- **Status:** Initial Registry Initialized (Bootstrap Gate 4)
- **Author:** Senior Software Engineer / Technical Architect / ML Engineer (Findrr AI Pair)
- **Project Owner:** Lebogang Masia
- **Last Updated:** 2026-11-26

---

## 1. Registry Architecture & Schema

The Findrr Model Registry tracks the authoritative metadata, versions, and cryptographic integrity parameters for all machine learning models integrated into the application server (Module 9).

### Metadata Schema
Every model catalog entry defines:
- **Model ID:** Unique stable identifier (`ML-xxx`).
- **Model Name:** Canonical machine-readable model name.
- **Active Version:** Version tag following SemVer for models (`vMAJOR.MINOR.PATCH`).
- **Base Checkpoint:** Pretrained base architecture.
- **Runtime Framework:** `ONNX Runtime` or `PyTorch CPU`.
- **Target Task:** Functional capability in Findrr.
- **Artifact Location:** Storage path under `models/<name>/<version>/`.
- **Status:** Lifecycle state (`Specification Proposed` / `Notebook Authored` / `Trained` / `Verified` / `Deprecated`).
- **Bundle Checksums:** SHA-256 hashes of all required companion files.

---

## 2. Model Catalog

| Model ID | Model Name | Version | Framework | Target Task | Status | Checksum Manifest (SHA-256) |
|---|---|---|---|---|---|---|
| **ML-001** | `title-expander` | `v2.0.0` | PyTorch CPU (safetensors; see D-004) | Job title & search term expansion (Module 3) | Notebook Authored (rewritten 2026-11-26) | Pending user training on Kaggle. v1.0.0 (placeholder data) is retired and its artifacts were lost |
| **ML-002** | `similarity-evaluator` | `v1.1.0` | ONNX Runtime (INT8) | Semantic similarity & deduplication (Modules 3 & 4) | Notebook Authored (rewritten 2026-11-26) | Pending user training on Kaggle. v1.0.0 (placeholder data) is retired |
| **ML-003** | `application-tailor` | `v1.0.0-draft` | ONNX Runtime | Tailored CV/cover letter assistant (Module 5) | **Notebook superseded: do not run** (D-006) | Blocked on D-006 |

---

## 3. Active Version Pointers

```json
{
  "active_models": {
    "title_expander": {
      "model_id": "ML-001",
      "version": "v2.0.0",
      "status": "NOTEBOOK_AUTHORED",
      "artifact_path": "models/title-expander/v2.0.0/"
    },
    "similarity_evaluator": {
      "model_id": "ML-002",
      "version": "v1.1.0",
      "status": "NOTEBOOK_AUTHORED",
      "artifact_path": "models/similarity-evaluator/v1.1.0/"
    },
    "application_tailor": {
      "model_id": "ML-003",
      "version": "v1.0.0-draft",
      "status": "PROPOSED",
      "artifact_path": "models/application-tailor/v1.0.0/"
    }
  }
}
```

---

## 4. Integrity and Verification Policy

1. **No Silent Model Substitutions:** Upgrading a model requires an explicit version configuration update.
2. **Mandatory Checksums:** The application server will not load any artifact bundle unless its SHA-256 checksum matches the manifest produced during training.
3. **Mock Separation:** If artifacts are not present on the server, inference calls must be routed to explicit test fixtures and tagged `MOCK` in all application logs.


---

## 5. Load-time contract (enforced by `findrr.ml.registry`, 2026-11-26)

A bundle is loaded only if **all** of the following hold. Otherwise `findrr model inspect` reports the reason, and inference stays MOCK-labelled.
1. Every file listed in `manifest.json` exists and its SHA-256 matches.
2. `manifest.model_id` equals the registered ID, and `manifest.version` equals the registered active version.
3. Every `required_files` entry exists and is covered by the manifest.
4. `manifest.metadata.acceptance.passed` is not `false`. The notebooks record whether the approved acceptance criteria were met, and refuse to export a model that fails them unless explicitly overridden.
