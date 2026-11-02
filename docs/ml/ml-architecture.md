# Machine Learning Architecture Document (Findrr)

- **Document Version:** 1.0.0
- **Status:** Presented for Review (Bootstrap Gate 4)
- **Author:** Senior Software Engineer / Technical Architect / ML Engineer (Findrr AI Pair)
- **Project Owner:** Lebogang Masia
- **Last Updated:** 2026-11-02

---

## 1. Executive Summary & Core Principles

The Findrr machine learning system provides intelligent natural language understanding and text generation capabilities to power job search expansion, semantic relevance filtering, and tailored application preparation.

The machine learning architecture is governed by four immutable architectural invariants:
1. **Strict Training vs. Inference Decoupling:** Training and fine-tuning execute exclusively in user-run Kaggle notebooks leveraging cloud GPU accelerators. Runtime inference executes exclusively on the Findrr application server (the user's laptop for Milestones 1–3) using local CPU runtimes. Zero runtime training occurs on the host.
2. **Cryptographic Integrity & Complete Bundle Binding:** Every model artifact transferred from Kaggle is packaged as a complete, self-contained bundle (weights, tokenizer, configuration, label mappings, and SHA-256 cryptographic manifest). The application server validates checksums before loading and rejects corrupted, unverified, or tampered artifacts.
3. **Fail-Closed, Zero-Fabrication Diagnostics:** If a model is missing, corrupt, or throws an inference error, the system logs diagnostic details and returns a typed error. The system never falls back to fabricated predictions, synthetic data, or silent mocks during live operation.
4. **Local Hardware Adaptation:** Memory and compute consumption are strictly bounded to accommodate the host environment (12th Gen Intel Core i5-1235U, 7.4 GiB RAM), with total active model footprint capped at <= 1.0 GiB.

---

## 2. Environment Architecture & Separation

```
+---------------------------------------------------------------------------------+
|                               TRAINING ENVIRONMENT                              |
|                          (Kaggle Cloud Infrastructure)                          |
|                                                                                 |
|   +-----------------------+     +--------------------+     +----------------+   |
|   | Public Taxonomies     | --> | Deterministic      | --> | Artifact       |   |
|   | (O*NET, ESCO, Kaggle) |     | Training Notebooks |     | Export Bundle  |   |
|   +-----------------------+     | (Fixed Seeds, T4)  |     | (.safetensors, |   |
|                                 +--------------------+     |  manifest.json)|   |
+--------------------------------------------------------------------+------------+
                                                                     |
                                          Manual User Transfer       | (Integrity
                                          & Checksum Verification    |  Manifest)
                                                                     v
+---------------------------------------------------------------------------------+
|                               INFERENCE ENVIRONMENT                             |
|                        (Findrr Host Server - Local CPU)                         |
|                                                                                 |
|   +--------------------+     +---------------------+     +------------------+   |
|   | Model Registry &   | --> | Unified Inference   | --> | App Modules      |   |
|   | Integrity Verifier |     | Service (Module 9)  |     | (Modules 3, 4, 5)|   |
|   +--------------------+     +---------------------+     +------------------+   |
+---------------------------------------------------------------------------------+
```

### 2.1 Training Environment: Kaggle
- **Platform:** Kaggle Notebooks (Python 3.10+ container).
- **Accelerators:** Dedicated NVIDIA T4 or P100 GPUs (free 30 hrs/week allocation).
- **Execution Mode:** Manual execution by the user; notebooks run start-to-finish in a single non-interactive or batch session.
- **Reproducibility:** Pinned library versions (`requirements.txt`), fixed random seeds (`seed=42`), deterministic data splitting, and explicit evaluation metric logging.
- **Data Governance:** Only public datasets (O*NET 28.0+, ESCO, synthetic variations) are utilized. Real user personal information is strictly prohibited from training datasets.

### 2.2 Inference Environment: Findrr Application Host
- **Host Hardware:** 12th Gen Intel Core i5-1235U (10 cores, 12 threads), 7.4 GiB RAM, Arch Linux x86_64.
- **Runtime:** CPU-optimized runtimes (ONNX Runtime and PyTorch CPU) compiled with AVX2/VNNI vector extensions. No CUDA dependencies.
- **Resource Constraints:** Active memory footprint for all loaded models <= 1.0 GiB; thread pool allocation capped at 4 threads to prevent host UI freezing.

---

## 3. Module 9: Centralized Model Management & Serving

Individual application modules (Modules 3, 4, 5) never interact with model weights directly. All loading, validation, lifecycle management, and execution are centralized in **Module 9**.

### 3.1 Complete Artifact Bundle Specification
A trained model is only complete when all companion artifacts are present in `models/<model_id>/<version>/`:
1. **Weights:** Serialized in `.safetensors` or `.onnx` format (safe, zero arbitrary code execution).
2. **Tokenizer:** `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`, and `vocab.txt`/`vocab.json`.
3. **Model Configuration:** `config.json` containing architecture parameters, hyperparameter tags, and max sequence lengths.
4. **Pre/Post-Processing Specs:** `preprocess_config.json` defining normalization, truncation limits, and label mapping dictionaries.
5. **Cryptographic Manifest:** `manifest.json` containing SHA-256 hashes of every file in the bundle, export timestamp, base model version, and Kaggle run metadata.

### 3.2 Model Registry Architecture
The model registry maintains two representations:
- **Human-Readable Specification:** [`docs/ml/model-registry.md`](file:///home/witness/Projects/Findrr/docs/ml/model-registry.md) recording purpose, architecture, version history, and evaluation scores.
- **Machine-Readable Registry:** Stored as `models/registry.json` (or resolved from environment configuration), defining active version pointers and required file checksums.

### 3.3 Artifact Integrity Verification Lifecycle
```
[Inference Service Request]
           │
           ▼
[Check Model Cache] ──(Hit)──► [Execute Forward Pass]
           │ (Miss)
           ▼
[Resolve Artifact Location from Registry]
           │
           ▼
[Verify All Required Files Exist on Disk] ──(Missing)──► [Log Error & Raise ArtifactMissingError]
           │
           ▼
[Compute SHA-256 Hashes of Files]
           │
           ▼
[Match Hashes against manifest.json] ──(Mismatch)──► [Log Error & Raise ArtifactCorruptedError]
           │
           ▼
[Load Weights into ONNX/PyTorch Engine]
           │
           ▼
[Bind Tokenizer & Preprocessors]
           │
           ▼
[Cache in Memory Pool] ──► [Execute Forward Pass]
```

### 3.4 Unified 8-Step Inference Pipeline
Every inference call through `InferenceService` executes the following sequence:
1. **Receive Request:** Typed request object specifying model ID, input text or text pairs, and inference parameters.
2. **Validate Input:** Input schema validation (checking string lengths, empty inputs, formatting).
3. **Preprocess:** Apply exact tokenization, padding, truncation, and tensor formatting matching the training notebook.
4. **Execute Prediction:** Run forward-pass inference in evaluation mode (`torch.no_grad()`, `eval()` or ONNX session run).
5. **Post-process:** Map raw logits or embeddings to normalized domain outputs (e.g. cosine similarities, decoded text strings).
6. **Validate Output:** Output schema check (verifying bounds, checking for NaN/Inf, length validation).
7. **Record Telemetry:** Log execution latency, model version, device, and real vs. mock execution flag.
8. **Return Response:** Return structured, typed response object.

---

## 4. Model Portfolio & Responsibilities

Findrr incorporates three specialized models across its core workflow:

| Model ID | Name | Role & Purpose | Consuming Module | Base Architecture | Format & Size |
|---|---|---|---|---|---|
| **ML-001** | `title-expander` | Generates alternative search terms from generalized titles | Module 3 (Search Terms) | `google/flan-t5-small` | `.safetensors` / ONNX (~240 MB) |
| **ML-002** | `similarity-evaluator` | Evaluates semantic similarity for title relevance and deduplication | Module 3 & Module 4 | `sentence-transformers/all-MiniLM-L6-v2` | ONNX INT8 (~65 MB) |
| **ML-003** | `application-tailor` | Generates tailored phrasing matching profile facts to job postings | Module 5 (Application Prep) | `Qwen2.5-0.5B-Instruct` / `Flan-T5` | Quantized ONNX (~350 MB) |

---

## 5. Resource Management & Performance Budget

| Parameter | Budget Limit | Architectural Strategy |
|---|---|---|
| **Max Combined Model RAM** | **1.0 GiB** | Sequential model loading; unload Expander when search phase ends before loading Tailor assistant. |
| **Expander Latency (CPU)** | **< 1,500 ms** per generation | Beam search restricted to `num_beams=2` or greedy decoding with max new tokens = 32. |
| **Similarity Latency (CPU)** | **< 50 ms** per pair | ONNX Runtime INT8 quantization with multi-threaded matrix multiplication. |
| **Max Artifact Download Size** | **< 500 MB** per model | Compression and removal of optimizer states, training checkpoints, and unused tensors. |
| **Thread Concurrency** | **4 CPU threads** | `OMP_NUM_THREADS=4` and `intra_op_num_threads=4` to leave 6 CPU cores free for host system. |

---

## 6. Testing, QA & Mock Isolation

In adherence to project rules:
- **No Mock Masking:** Mocks are never reported as real integrations. Tests using synthetic stubs are explicitly tagged `@pytest.mark.mock_inference` and logged as `MOCK`.
- **Pre-PR Verification:** Pull requests must explicitly specify `ML Integration Status: N/A`, `Verified with Real Artifacts`, or `Unverified (Tested with Mocks Only)`.
- **Integrity Test Harness:** Unit tests verify that tampered files, corrupt manifests, or truncated weight files trigger immediate, structured diagnostic failures.
