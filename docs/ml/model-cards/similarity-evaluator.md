# Model Card: ML-002 similarity-evaluator

| | |
|---|---|
| Model ID / version | ML-002 v1.1.0 |
| Base model | `sentence-transformers/all-MiniLM-L6-v2` (about 22M parameters, Apache 2.0) |
| Runtime | ONNX Runtime CPU, INT8 dynamic quantisation, `tokenizers` (no PyTorch) |
| Specification | `docs/ml/models/similarity-evaluator.md` |
| Evaluation | `docs/ml/evaluation-reports/similarity-evaluator-1.1.0.md` |
| Status | Acceptance passed; real inference verified 2026-11-27 |

## Intended use

- Scores how similar two short texts are (cosine of mean-pooled embeddings, clamped to 0 to 1).
- Used in Findrr for:
  - Module 3: checking that generated alternative titles stay faithful to the user's title (relevance threshold 0.70, provisional);
  - Module 4: detecting duplicate postings (threshold 0.88, provisional).
- Inputs are job titles or short posting texts, truncated at 128 tokens.

## Out of scope

- Ranking candidates for hiring decisions, or judging a person's suitability for a job.
- Long documents: text past 128 tokens is ignored.
- Languages other than English: the training data is English O*NET titles only.

## Training data

O*NET 31.0 (U.S. Department of Labor, CC BY 4.0). Positive pairs are titles of the same occupation, with in-batch negatives. No personal data and no user data.

## Performance (held-out occupations, 800 pairs)

| Metric | Value | Target |
|---|---|---|
| Precision at 0.70 | 0.963 | >= 0.90 |
| "Software Developer" / "Software Engineer" | 0.908 | >= 0.85 |
| "Software Developer" / "Dental Assistant" | 0.252 | < 0.30 |
| Latency per pair (i5-1235U) | 2.8 ms | < 50 ms |
| RSS after load | 119 MB (about 86 MB above the bare package) | < 100 MB |

Pearson 0.745 and Spearman 0.767 against proxy labels are reported only (D-008).

## Limitations and risks

- **Strict at 0.70.** Only 38% of same-occupation test pairs reach the threshold, so valid alternative titles can be filtered out. Lowering the threshold trades precision for recall and needs evaluation and approval.
- **US-centric vocabulary.** O*NET reflects US job titles. Titles common elsewhere (for example South African or British usage) may score lower.
- **Proxy evaluation.** No human-labelled benchmark exists, so the correlation figures measure agreement with O*NET structure.
- **Not a fairness-audited model.** It compares job titles and is never applied to personal attributes.

## Integrity

The app loads the bundle only after SHA-256 verification against `manifest.json`, and only if the manifest records `acceptance.passed = true`.
