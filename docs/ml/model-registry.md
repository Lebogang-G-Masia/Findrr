# Findrr Model Registry & Catalog

- **Document Version:** 1.0.0
- **Status:** Initial Registry Initialized (Bootstrap Gate 4)
- **Author:** Senior Software Engineer / Technical Architect / ML Engineer (Findrr AI Pair)
- **Project Owner:** Lebogang Masia
- **Last Updated:** 2026-11-02

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
| **ML-001** | `title-expander` | `v1.0.0-draft` | PyTorch / ONNX | Job title & search term expansion (Module 3) | Specification Proposed | Pending user training on Kaggle |
| **ML-002** | `similarity-evaluator` | `v1.0.0-draft` | ONNX Runtime | Semantic similarity & deduplication (Modules 3 & 4) | Specification Proposed | Pending user training on Kaggle |
| **ML-003** | `application-tailor` | `v1.0.0-draft` | ONNX Runtime | Tailored CV/cover letter assistant (Module 5) | Specification Proposed | Pending user training on Kaggle |

---

## 3. Active Version Pointers

```json
{
  "active_models": {
    "title_expander": {
      "model_id": "ML-001",
      "version": "v1.0.0-draft",
      "status": "PROPOSED",
      "artifact_path": "models/title-expander/v1.0.0/"
    },
    "similarity_evaluator": {
      "model_id": "ML-002",
      "version": "v1.0.0-draft",
      "status": "PROPOSED",
      "artifact_path": "models/similarity-evaluator/v1.0.0/"
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
