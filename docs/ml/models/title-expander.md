# Model Specification: Job Title Expander (ML-001)

- **Model ID:** `ML-001`
- **Model Name:** `title-expander`
- **Target Release:** Milestone 1 (Core CLI)
- **Status:** Proposed (Bootstrap Gate 4)
- **Author:** Senior Software Engineer / Technical Architect / ML Engineer (Findrr AI Pair)
- **Project Owner:** Lebogang Masia
- **Last Updated:** 2026-11-02

---

## 1. Purpose
The Job Title Expander generates context-aware, industry-standard alternative job titles and related search queries from an approved primary Generalized Job Title and supporting user profile skills. Its goal is to broaden search discovery across differing corporate and regional job naming conventions.

## 2. Module Dependencies
- **Upstream Producer:** Module 1 (Onboarding & Profile Management) provides the approved Generalized Job Title and top skills.
- **Downstream Consumer:** Module 3 (Generate Key Search Terms) consumes generated titles for semantic validation and search queue population.

## 3. Inputs & Outputs
- **Input Schema:** JSON payload containing:
  ```json
  {
    "generalized_title": "Software Developer",
    "skills": ["Python", "FastAPI", "SQL", "Docker"],
    "seniority_preference": "Mid-Level"
  }
  ```
- **Input Text Representation:** Formatted sequence:
  `"expand titles: Software Developer | skills: Python, FastAPI, SQL, Docker | level: Mid-Level"`
- **Output Schema:** Structured sequence of comma-separated candidate titles:
  `"Backend Engineer, Python Developer, Software Engineer, API Developer"`
- **Output Post-processing:** Split into a cleaned list of unique strings (`list[str]`), trimmed of whitespace and punctuation.

## 4. Model Architecture Evaluation
- **Architecture Type:** Sequence-to-sequence encoder-decoder transformer.
- **Evaluated Options:**
  - *GPT-2 / Causal Decoder:* Unidirectional attention; prone to repetition and unconstrained rambling on short title inputs.
  - *Flan-T5 (Encoder-Decoder):* Bidirectional encoder captures context well; instruction-tuned decoder produces crisp, constrained string sequences.
- **Selected Architecture:** Seq2seq Transformer (Flan-T5 architecture).

## 5. Pretrained Base Checkpoint
- **Base Checkpoint:** `google/flan-t5-small` (~80M parameters).
- **Justification:** Compact footprint (~300 MB in FP32, ~150 MB in FP16/INT8), exceptional instruction adherence for prompt-based generation, and fast inference on host CPU.

## 6. Training Methodology
- **Approach:** Parameter-Efficient Fine-Tuning (LoRA) or full fine-tuning on Kaggle.
- **Task:** Sequence-to-sequence generation mapping occupational taxonomy profiles to clusters of alternate market job titles.
- **Optimization:** AdamW optimizer, learning rate $3 \times 10^{-4}$, linear warmup with cosine decay, FP16 mixed precision.

## 7. Datasets
- **Source Datasets:**
  - U.S. Bureau of Labor Statistics O*NET 28.0+ Occupational Title Synonyms & Alternate Titles.
  - European Commission ESCO (European Skills, Competences, Qualifications and Occupations) multilingual hierarchy (English subset).
  - Anonymized public Kaggle job posting titles mapped to standardized roles.
- **Privacy & Compliance:** 100% public occupational taxonomies. **Zero real user data.**
- **Splits:** 80% Train, 10% Validation, 10% Test (stratified by occupational domain; disjoint titles to prevent data leakage).

## 8. Training & Evaluation Procedures
- **Loss Function:** Cross-entropy loss over target token sequences.
- **Evaluation Metrics:**
  - Token-level: ROUGE-L and BLEU-4 against gold standard taxonomy synonyms.
  - Domain Coverage: Percentage of generated titles present in approved occupational dictionaries.
- **Evaluation Criteria Thresholds:**
  - ROUGE-L >= 0.75
  - Valid Domain Title Ratio >= 0.85
  - Generation repetition rate < 0.05

## 9. Kaggle Computational Requirements
- **Accelerator:** 1x NVIDIA T4 GPU (Kaggle free tier).
- **Estimated Runtime:** ~45–60 minutes for 5 epochs over 25,000 paired title sequences.
- **RAM / Disk:** Standard Kaggle GPU session (16 GB GPU VRAM, 30 GB disk space).

## 10. Artifact Formats & Export Bundle
The Kaggle notebook must package and export `title_expander_bundle.tar.gz` containing:
- `model.safetensors` (trained weights, ~150 MB in FP16).
- `config.json` (model architecture configuration).
- `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`, `spiece.model`.
- `preprocess_config.json` (max input length = 128, max output length = 64).
- `manifest.json` (cryptographic SHA-256 hashes, date, base checkpoint, evaluation results).

## 11. Server-Side Loading Requirements (Module 9)
- Check all files exist in `models/title-expander/v1.0.0/`.
- Compute SHA-256 hashes and match against `manifest.json`.
- Reject loading with `ArtifactCorruptedError` if any checksum differs.
- Load via Hugging Face `AutoModelForSeq2SeqLM` and `AutoTokenizer` in evaluation mode.

## 12. Inference Requirements
- **Execution Mode:** CPU inference using `torch.no_grad()`, `eval()`.
- **Generation Settings:** Greedy decoding or beam search (`num_beams=2`), temperature = 0.3, max new tokens = 48, repetition penalty = 1.2.
- **Latency Budget:** < 1,500 ms per generation request on host Intel i5 CPU.
- **Memory Footprint:** < 300 MB active RAM.

## 13. Acceptance Criteria
- **AC-ML-001.1:** The model generates at least 3 distinct alternative titles for standard roles (e.g. "Software Developer" yields "Backend Engineer", "Python Developer", "Full Stack Developer").
- **AC-ML-001.2:** Average inference latency is < 1,500 ms across 50 benchmark requests on host CPU.
- **AC-ML-001.3:** Cryptographic SHA-256 validation passes with 100% fidelity.

## 14. Implementation notes (proposed 2026-11-26, approved when the notebook PR is merged)
- **Version:** `2.0.0`. The input level vocabulary is now `ANY|ENTRY|MID|SENIOR|LEAD` (the app's `SeniorityLevel`), replacing the free text "Mid-Level". This is an incompatible input change, hence the major version.
- **Datasets:** O*NET 31.0 only (reported titles, job titles, software skills). ESCO is not used. Its bulk download needs a manual portal request, and O*NET alone gives about 26.5k examples, close to the ~25k planned.
- **Precision:** FP32 instead of FP16, because T5 overflows in FP16 on a T4.
- **Acceptance is enforced:** the notebook does not export a model that fails §8 unless explicitly overridden. An overridden bundle is marked `acceptance.passed=false`, and the app refuses to load it.
- **Inference:** the bundle stays safetensors + `AutoModelForSeq2SeqLM` (§10–11). This conflicts with ADR-0003 (ONNX only); see D-004.
