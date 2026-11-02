# Model Specification: Semantic Similarity Evaluator (ML-002)

- **Model ID:** `ML-002`
- **Model Name:** `similarity-evaluator`
- **Target Release:** Milestone 1 (Core CLI)
- **Status:** Proposed (Bootstrap Gate 4)
- **Author:** Senior Software Engineer / Technical Architect / ML Engineer (Findrr AI Pair)
- **Project Owner:** Lebogang Masia
- **Last Updated:** 2026-11-02

---

## 1. Purpose
The Semantic Similarity Evaluator computes dense embedding representations and cosine similarity scores between text pairs. It is utilized to:
1. Validate that generated alternative job titles remain semantically faithful to the user's generalized title.
2. Filter out duplicate job search terms.
3. Eliminate duplicate scraped job postings across different job portals.

## 2. Module Dependencies
- **Upstream Producer:** Module 3 (Search Terms) and Module 4 (Find Postings).
- **Downstream Consumer:** Module 3 validation pipeline and Module 4 deduplication service.

## 3. Inputs & Outputs
- **Input Schema:** A text pair `(text_a: str, text_b: str)` or batched list of pairs `list[tuple[str, str]]`.
  - Example: `("Software Developer", "Backend Engineer")`
- **Output Schema:** Float scalar cosine similarity score $S \in [-1.0, 1.0]$:
  - Example: `0.84`
- **Output Post-processing:** Clamped to `[0.0, 1.0]` for relevance scoring.

## 4. Model Architecture Evaluation
- **Architecture Type:** Bi-Encoder (Dual-Encoder) Sentence Transformer.
- **Evaluated Options:**
  - *Cross-Encoder (BERT/RoBERTa):* High accuracy, but $O(N \times M)$ comparisons require full joint attention pass for every pair; too slow for deduplication and live filtering.
  - *Bi-Encoder (Dual-Encoder):* Encodes text into 384-dimensional dense vectors independently; similarity is calculated via fast dot-product / cosine similarity ($O(1)$ after encoding). Ideal for scalable batch scoring.
- **Selected Architecture:** Bi-Encoder Sentence Transformer.

## 5. Pretrained Base Checkpoint
- **Base Checkpoint:** `sentence-transformers/all-MiniLM-L6-v2` (~22M parameters).
- **Justification:** Compact footprint (~80 MB in PyTorch, ~45 MB in ONNX INT8), 384-dimensional dense embeddings, excellent balance of semantic accuracy and blazing CPU inference speed (~15–25 ms per pair).

## 6. Training Methodology
- **Approach:** Domain adaptation / contrastive fine-tuning on Kaggle.
- **Task:** MultipleNegativesRankingLoss or CosineSimilarityLoss on paired job titles and occupational synonym descriptions.
- **Optimization:** AdamW optimizer, learning rate $2 \times 10^{-5}$, warmup ratio 0.1, FP16 mixed precision.

## 7. Datasets
- **Source Datasets:**
  - O*NET 28.0+ Related Occupations and Alternate Titles pairs (positive pairs).
  - Negative hard-mining pairs across disparate occupational domains (e.g. "Software Developer" vs. "Hardware Technician").
  - Job title synonym pairs from public career taxonomies.
- **Privacy & Compliance:** 100% public taxonomies. **Zero real user data.**
- **Splits:** 80% Train, 10% Validation, 10% Test (stratified by occupational category).

## 8. Training & Evaluation Procedures
- **Loss Function:** `MultipleNegativesRankingLoss` with symmetric cross-entropy.
- **Evaluation Metrics:**
  - Cosine Pearson correlation ($r$) and Spearman rank correlation ($\rho$) against human-labeled semantic similarity benchmarks.
  - Accuracy at classification thresholds (0.70 relevance, 0.88 duplicate).
- **Evaluation Criteria Thresholds:**
  - Pearson correlation $r \ge 0.85$ on test set.
  - Title similarity precision >= 0.90 at relevance threshold 0.70.

## 9. Kaggle Computational Requirements
- **Accelerator:** 1x NVIDIA T4 GPU (Kaggle free tier).
- **Estimated Runtime:** ~25–35 minutes for 4 epochs over 40,000 text pairs.
- **RAM / Disk:** Standard Kaggle GPU session.

## 10. Artifact Formats & Export Bundle
The Kaggle notebook must package and export `similarity_evaluator_bundle.tar.gz` containing:
- `model.onnx` (quantized INT8 ONNX graph, ~45 MB).
- `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`, `vocab.txt`.
- `config.json` (embedding dimension = 384, max sequence length = 128, pooling = "mean").
- `preprocess_config.json` (lowercase = true, strip_accents = true).
- `manifest.json` (cryptographic SHA-256 hashes, export date, evaluation scores).

## 11. Server-Side Loading Requirements (Module 9)
- Verify all required files exist in `models/similarity-evaluator/v1.0.0/`.
- Validate SHA-256 checksums against `manifest.json`.
- Initialize ONNX Runtime `InferenceSession` with CPUExecutionProvider and 4 execution threads.

## 12. Inference Requirements
- **Execution Mode:** ONNX Runtime CPU session.
- **Forward Pass:** Tokenize inputs -> execute ONNX session -> apply mean pooling over token embeddings -> compute vector dot product / cosine norm.
- **Latency Budget:** < 50 ms per text pair on host Intel i5 CPU; < 150 ms for batch of 20 candidate pairs.
- **Memory Footprint:** < 100 MB active RAM.

## 13. Acceptance Criteria
- **AC-ML-002.1:** Semantic similarity of synonymous titles (e.g. "Software Developer" vs "Software Engineer") evaluates >= 0.85.
- **AC-ML-002.2:** Semantic similarity of distinct titles (e.g. "Software Developer" vs "Dental Assistant") evaluates < 0.30.
- **AC-ML-002.3:** Average latency is < 50 ms per text pair on host CPU.
- **AC-ML-002.4:** Cryptographic SHA-256 validation passes with 100% fidelity.
