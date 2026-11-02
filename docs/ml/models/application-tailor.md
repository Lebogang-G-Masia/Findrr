# Model Specification: Application Tailoring Assistant (ML-003)

- **Model ID:** `ML-003`
- **Model Name:** `application-tailor`
- **Target Release:** Milestone 2 (Additional Functionality)
- **Status:** Proposed (Bootstrap Gate 4)
- **Author:** Senior Software Engineer / Technical Architect / ML Engineer (Findrr AI Pair)
- **Project Owner:** Lebogang Masia
- **Last Updated:** 2026-11-02

---

## 1. Purpose
The Application Tailoring Assistant assists in contextualizing verified user experiences and qualifications against job description keywords and responsibilities. It generates natural language phrasing, summary statements, and cover letter sentences that emphasize matching skills **without fabricating any factual claims**.

## 2. Module Dependencies
- **Upstream Producer:** Module 1 (User Profile) and Module 4 (Job Posting text).
- **Downstream Consumer:** Module 5 (Application Preparation) consumes structured phrasing fragments and embeds them into deterministic document templates (Jinja2).

## 3. Inputs & Outputs
- **Input Schema:** Structured prompt payload containing:
  ```json
  {
    "target_role": "Backend Engineer",
    "company": "Acme Corp",
    "job_requirements": ["Python", "FastAPI", "PostgreSQL", "CI/CD"],
    "verified_user_facts": [
      "Built REST APIs using Python and FastAPI for 3 years",
      "Maintained PostgreSQL database clusters",
      "Configured automated GitHub Actions workflows"
    ],
    "requested_artifact": "professional_summary"
  }
  ```
- **Output Schema:** Structured JSON containing tailored sentences:
  ```json
  {
    "summary_statement": "Backend Engineer with 3 years of experience developing robust REST APIs using Python and FastAPI, managing PostgreSQL clusters, and automating CI/CD workflows.",
    "matched_skills": ["Python", "FastAPI", "PostgreSQL", "CI/CD"],
    "missing_skills": []
  }
  ```

## 4. Model Architecture Evaluation
- **Architecture Type:** Small instruction-tuned generative transformer.
- **Evaluated Options:**
  - *Large Language Models (7B+ parameters):* Exceeds host memory limits (> 4 GiB VRAM/RAM), too slow for CPU inference without dedicated GPU.
  - *Small Instruct Model (0.5B to 1.5B parameters):* Compact memory footprint (~350–500 MB in INT4/INT8 quantization), fast CPU generation, and reliable instruction adherence when constrained to JSON schemas.
- **Selected Architecture:** Small Instruction-Tuned Transformer (e.g. `Qwen2.5-0.5B-Instruct` or `google/flan-t5-base`).

## 5. Pretrained Base Checkpoint
- **Base Checkpoint:** `Qwen/Qwen2.5-0.5B-Instruct` (or `google/flan-t5-base`).
- **Justification:** High parameter efficiency, native support for JSON-constrained decoding, sub-second token generation on CPU, and INT8 quantized ONNX graph size under 350 MB.

## 6. Training Methodology
- **Approach:** Parameter-Efficient Instruction Fine-Tuning (LoRA) on Kaggle.
- **Task:** Constrained text rewriting and fact-guided summarization enforcing strict negative constraints (penalizing claims outside the input facts).
- **Optimization:** SFTTrainer / Hugging Face TRL, learning rate $1 \times 10^{-4}$, 3 epochs, cosine learning rate scheduler.

## 7. Datasets
- **Source Datasets:**
  - Synthetic paired profile-job description alignment datasets (generated and validated against factual grounding heuristics).
  - Open-source resume-job description alignment corpora (anonymized and scrubbed of PII).
- **Privacy & Compliance:** 100% anonymized/synthetic. **Zero real user data.**
- **Splits:** 80% Train, 10% Validation, 10% Test.

## 8. Training & Evaluation Procedures
- **Loss Function:** Causal language modeling loss with factual consistency penalty.
- **Evaluation Metrics:**
  - Factual Consistency Score: Precision of extracted entities and claims in output against input facts (Goal: 1.0).
  - Schema Adherence: Percentage of valid JSON responses generated (Goal: 100%).
- **Evaluation Criteria Thresholds:**
  - Factual Precision = 1.0 (Zero invented entities).
  - JSON Schema Compliance >= 0.99.

## 9. Kaggle Computational Requirements
- **Accelerator:** 1x NVIDIA T4 or P100 GPU (Kaggle free tier).
- **Estimated Runtime:** ~45–60 minutes for 3 epochs.
- **RAM / Disk:** Standard Kaggle GPU session.

## 10. Artifact Formats & Export Bundle
The Kaggle notebook must package and export `application_tailor_bundle.tar.gz` containing:
- `model.onnx` (quantized INT8 ONNX graph, ~350 MB).
- `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`.
- `config.json` (max generation length = 256, temperature = 0.2).
- `manifest.json` (cryptographic SHA-256 hashes, export date, evaluation scores).

## 11. Server-Side Loading Requirements (Module 9)
- Verify all required files exist in `models/application-tailor/v1.0.0/`.
- Validate SHA-256 checksums against `manifest.json`.
- Initialize ONNX Runtime `InferenceSession` with CPUExecutionProvider.

## 12. Inference Requirements
- **Execution Mode:** ONNX Runtime CPU session.
- **Sampling Parameters:** Greedy decoding (`do_sample=false`) or low temperature ($T=0.1$) to enforce determinism.
- **Post-Inference Validation:** Run deterministic string containment check ensuring every named entity in output exists in verified profile input facts.
- **Latency Budget:** < 3,000 ms per summary generation on host Intel i5 CPU.
- **Memory Footprint:** < 450 MB active RAM.

## 13. Acceptance Criteria
- **AC-ML-003.1:** 100% of generated skill mentions and experience statements map strictly to provided input facts.
- **AC-ML-003.2:** The model fails gracefully if input facts are contradictory or empty.
- **AC-ML-003.3:** Cryptographic SHA-256 validation passes with 100% fidelity.
