# Evaluation Report: ML-002 similarity-evaluator v1.1.0

- **Model:** `sentence-transformers/all-MiniLM-L6-v2`, contrastively fine-tuned (MultipleNegativesSymmetricRankingLoss), exported to ONNX INT8 with mean pooling
- **Notebook:** `notebooks/02_train_similarity_evaluator.ipynb` (as merged in PR #30; D-008)
- **Trained by:** the project owner on Kaggle (T4 GPU). Bundle exported 2026-11-26T18:59:21Z.
- **Bundle:** `models/similarity-evaluator/v1.1.0/` (not in git). `manifest.json` SHA-256 `943d2314…dc1e6`; `model.onnx` SHA-256 `f93e2689…cfa84`
- **Report date:** 2026-11-27
- **Status:** Acceptance **passed**. Integrated with real inference (verified 2026-11-27).

## 1. Evidence sources

| Source | What it is |
|---|---|
| Kaggle run (user) | `evaluation_summary` and `metadata.acceptance` in the bundle manifest, computed in the notebook on the exported INT8 model |
| Local re-evaluation (agent, 2026-11-27) | The installed bundle run through the app's `SimilarityEvaluatorRunner` on the user's laptop (Intel i5-1235U, 7.4 GiB RAM). The test pairs were rebuilt with the notebook's own code from O*NET 31.0 (archive SHA-256 verified). Inference only; nothing was trained. |

## 2. Data

- O*NET 31.0 (CC BY 4.0). Public data only, with no personal data.
- Training: 39,927 same-occupation title pairs. Splits are by occupation, stratified by SOC major group (80/10/10).
- Test: 800 graded pairs from held-out occupations. The labels are a proxy (spec §14):

  | Label | Meaning | Pairs |
  |---|---|---|
  | 3 | same occupation | 306 |
  | 2 | Primary-Short related | 99 |
  | 1 | Primary-Long related | 89 |
  | 0 | different major group | 306 |

## 3. Acceptance criteria (spec §8 and §13, as amended by D-008)

| Criterion | Kaggle | Laptop (app runner) | Target | Result |
|---|---|---|---|---|
| Precision of pairs scored >= 0.70 (label >= 2) | 0.9630 | 0.9630 | >= 0.90 | Pass |
| AC-ML-002.1 "Software Developer" / "Software Engineer" | 0.9083 | 0.9083 | >= 0.85 | Pass |
| AC-ML-002.2 "Software Developer" / "Dental Assistant" | 0.2516 | 0.2516 | < 0.30 | Pass |
| AC-ML-002.3 latency per pair | n/a | 2.8 ms mean, 4.1 ms p95 | < 50 ms | Pass |
| Latency, batch of 20 pairs (40 distinct texts) | n/a | about 70 ms median | < 150 ms | Pass |
| AC-ML-002.4 SHA-256 verification | n/a | all files verified (`findrr model inspect ML-002`) | 100% | Pass |

The laptop values equal the Kaggle values to at least four decimal places. The app runner therefore reproduces the notebook's tokenisation, pooling and normalisation.

## 4. Reported metrics (not gated)

| Metric | Value |
|---|---|
| Pearson r vs graded labels | 0.745 (the former target of 0.85 was removed by D-008: the proxy labels cap it) |
| Spearman rho | 0.767 |
| INT8 ONNX vs PyTorch embedding cosine | 0.972 |
| Untrained base model on the same pairs (laptop) | Pearson 0.614, Spearman 0.629 |
| Mean score by label 0 / 1 / 2 / 3 | 0.30 / 0.48 / 0.52 / 0.64 |
| Recall of same-occupation pairs at 0.70 | 0.376 |
| Pairs scoring >= 0.88 (duplicate threshold) by label 0 / 1 / 2 / 3 | 0 / 0 / 1 / 20 |

## 5. Memory (spec §12: < 100 MB active RAM)

Each figure is RSS for one process that loads only this model and runs 20 requests.

| Runner | After load | Peak | Note |
|---|---|---|---|
| Before PR #37 (`transformers.AutoTokenizer`) | 659 MB | 660 MB | the tokenizer import pulled in PyTorch |
| After PR #37 (`tokenizers` library) | 119 MB | 120 MB | the bare `findrr` package import is 33 MB, so the model's share is about 86 MB |

PR #37 left the scores unchanged: the maximum absolute difference over all 800 test pairs is 0.0.

## 6. Findings and limitations

- **Conservative at 0.70.** When the model scores a pair at or above 0.70, the pair is almost always related (precision 0.96). But only 38% of same-occupation pairs reach 0.70. Some of these are label noise: broad O*NET occupations group distant titles, such as "Crystal Grower" and "Probe Operator". Module 3 will still reject some valid alternative titles at this threshold. The threshold is a provisional configuration value.
- **Duplicate threshold 0.88** produced no cross-occupation false duplicates in this test set (one Primary-Short pair).
- **Proxy labels.** No human-labelled title-similarity benchmark exists for this domain, so correlation figures measure agreement with O*NET structure, not with human judgement (D-008).
