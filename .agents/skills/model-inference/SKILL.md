---
name: model-inference
description: Use when writing or changing model loading, the model registry, the inference service, or artifact integrity checks.
---

# Model Management and Inference (Findrr Server)

Provide centralized, application-wide functionality (Module 9) to manage, verify, load, and execute inference using trained machine learning model artifacts on the Findrr application server.

The authoritative specification is `docs/spec/modules/09-model-management.md`. Read it before changing model loading, the registry, or inference code.

## When to Use

* When building or maintaining server-side model loading pipelines, artifact registries, version validators, and checksum verifiers.
* When implementing unified inference services, preprocessing/post-processing pipelines, or telemetry for machine learning features.
* When developing test mocks, stubs, or controlled test fixtures for ML models when actual artifacts are unavailable.
* When configuring device placement (CPU/GPU), caching, lifecycle management, and resource optimization for model serving.

---

## 1. Core Operational Boundaries

* **Local Server Execution Only:** Inference runs exclusively on the Findrr application server using user-supplied model artifacts. Never rely on Kaggle for runtime inference.
* **No Runtime Training:** Never execute model training or fine-tuning during application startup or runtime.
* **Centralized Service:** Individual application modules must request predictions through the unified inference service rather than implementing independent model-loading or execution logic.
* **Git Exclusion:** Never commit binary model artifacts (weights, large vocabularies, serialized pipelines) to Git by default. Ensure artifact storage paths are listed in `.gitignore` and referenced strictly via environment or application configuration.
* **Repository Deliverables:** Commit all model-loading code, inference service implementations, model specifications, registry manifests, integrity checksums, and test mocks/fixtures to the repository.

---

### Additional Constraints

* **No Hard-Coded Artifacts:** Never hard-code model artifacts, weights or artifact file names into application source code. Locate artifacts only through configuration and the registry.
* **Name and Version Identity:** Every trained model must be identifiable by its name and version. Never load or report a model without both.
* **No Server-Side Training:** Do not train or fine-tune models on the application server unless the user has explicitly approved an exception.
* **No Hosted Substitutes:** Do not replace the Kaggle training strategy with a hosted training service. Do not use an external hosted inference API in place of server-side inference unless the user has explicitly approved it.
* **No Unmodified Pretrained Substitute:** Do not use an unmodified pretrained model as a replacement for required project-specific training or fine-tuning unless that approach is documented and the user has approved it.
* **Detect Missing or Incompatible Artifacts:** Implement a mechanism that identifies missing, corrupt or incompatible artifacts. It must return an explicit error and write a log entry. It must never return fabricated results.
* **Compatibility and Dependencies:** Keep the inference implementation compatible with the training notebook (preprocessing, tokenizers, label maps, formats). Verify that each artifact is compatible with the application and its runtime dependencies. Document all model dependencies and runtime requirements.
* **Versioning:** Model versions are tracked separately from the application version. See `docs/process/versioning.md`.

---

## 2. Artifact Availability & Test Mocking

* **Never Assume Artifacts Exist:** Do not assume trained model artifacts are present on the server unless explicitly supplied and verified by the user.
* **Explicit Mocks and Stubs:** When real artifacts are unavailable during development or testing, provide controlled mocks, stubs, or test fixtures.
* **Strict Separation:** Clearly distinguish mocked inference from real model inference via explicit configuration flags, response metadata, and log entries.
* **No Silent Fallbacks:** Never silently substitute an unrelated model, fallback heuristic, or external inference API when a required model artifact is unavailable.

---

## 3. Model Registry & Version Management

Maintain a structured model registry (configuration manifest/metadata schema) resolving active model versions from application configuration. Model updates must require explicit configuration changes and never silently alter runtime behavior. Model versions are tracked independently from application software versions; see `docs/process/versioning.md` for the versioning scheme that applies to both.

Every registered model entry must record:
* `model_id`: Unique model identifier
* `name`: Model name
* `version`: Semantic or explicit version string
* `purpose`: Functional role within Findrr
* `architecture`: Model architecture name
* `training_approach`: Trained from scratch, fine-tuned, or adapted
* `base_model`: Pretrained base checkpoint (if applicable)
* `dataset_reference`: Identifier or reference to the training dataset
* `training_date`: Date the artifact was produced
* `artifact_location`: Relative path within the configured model storage directory
* `runtime_dependencies`: Required library/framework versions
* `evaluation_results`: Summary of validation metrics from training
* `configuration`: Required runtime/inference parameters
* `integrity`: SHA-256 checksums (or equivalent cryptographic hashes) for each required file

---

## 4. Security, Integrity & Complete Bundle Loading

Treat model artifacts as application dependencies, and as untrusted external input until verified. Do not load arbitrary or unverified model files.

### Integrity & Compatibility Verification
* Before loading any model into memory, verify that all required files exist at the configured `artifact_location`.
* Validate file checksums against the registry's `integrity` hashes. Reject unverified, arbitrary, or corrupted files.
* Verify compatibility with current runtime dependencies and hardware.
* Where practical, maintain checksums or equivalent integrity information.
* Document artifact sources, versions, and configurations.
* Take appropriate precautions when downloading, transferring, and loading externally sourced model artifacts (verify the source and checksum before placing files in the model storage location).
* Prefer safe serialization formats (e.g., `safetensors`, ONNX) or restrict deserialization mechanisms to prevent arbitrary code execution.

### Complete Bundle Loading
Do not assume model weights alone are sufficient. A model loader must load and bind the complete artifact bundle:
* Model weights and architecture/configuration definitions
* Tokenizers and supporting vocabularies
* Preprocessing configurations (normalization stats, image transforms, text cleaners)
* Post-processing configurations (thresholds, calibration parameters)
* Label mappings (index-to-label and label-to-index dictionaries)
* Model-specific runtime metadata

---

## 5. Unified Inference Execution Pipeline

Expose a consistent service through which application modules can request predictions following an 8-step sequence:
1. **Receive Request:** Accept a typed request specifying the target capability/model and raw input payload.
2. **Validate Input:** Enforce schema, type, dimension, and boundary constraints on raw input.
3. **Preprocess:** Apply the loaded model's exact preprocessing pipeline, tokenization, and tensor formatting.
4. **Execute Prediction:** Run forward-pass inference in no-grad/evaluation mode using the cached model instance.
5. **Post-process:** Map raw logits/embeddings to domain labels, confidence scores, or structured outputs using post-processing config and label mappings.
6. **Validate Output:** Verify post-processed output meets expected schema and numerical validity (no `NaN`/`Inf` values).
7. **Record Telemetry:** Log execution metadata (model ID, version, latency, batch size, device used, mock vs. real status).
8. **Return Response:** Return a structured response object to the calling module.

---

## 6. Failure Handling & Runtime Performance

### Failure Handling
If a required model is missing, fails checksum verification, is incompatible, or throws an inference error:
* Log a structured error identifying `model_id`, `version`, artifact path, and exact failure cause.
* Return an explicit, typed error to the calling module.
* Never fabricate, guess, or return empty/default predictions that make callers behave as though inference succeeded.

### Runtime Performance & Resource Management
Design the model manager to match server physical CPU, GPU, and RAM constraints:
* **Device Placement:** Automatically detect and configure CPU or GPU execution based on server availability and configuration.
* **Caching & Lifecycle:** Load and cache active models in memory (singleton or managed pool pattern) to avoid per-request disk I/O. Provide explicit teardown/unload methods to free memory and GPU VRAM during shutdown or version swaps.
* **Concurrency & Batching:** Ensure thread/async safety for concurrent inference requests and support batch processing where throughput is prioritized.
* **Memory & Latency:** Enforce evaluation mode and disable gradient tracking during inference to minimize memory footprint and latency.
