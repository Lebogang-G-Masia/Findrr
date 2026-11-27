# Model Card: ML-001 title-expander

| | |
|---|---|
| Model ID / version | ML-001 v2.0.0 (evaluated); v2.1.0 pending (same model, ONNX bundle; D-004) |
| Base model | `google/flan-t5-small` (about 77M parameters, Apache 2.0) |
| Runtime | v2.0.0: PyTorch CPU + `transformers`. From v2.1.0: ONNX Runtime fp32 with a KV cache + `tokenizers`, no PyTorch (D-004) |
| Decoding | 2-beam search constrained by a token trie to 45,713 O*NET titles (`titles.json`); repeated titles impossible (D-007) |
| Specification | `docs/ml/models/title-expander.md` |
| Evaluation | `docs/ml/evaluation-reports/title-expander-2.0.0.md` |
| Status | Acceptance passed; real inference verified 2026-11-27; memory budget not met |

## Intended use

- Suggests up to 5 alternative job titles for a job search.
- Inputs: a generalised title, up to 5 skills, and a seniority level (`ANY`, `ENTRY`, `MID`, `SENIOR` or `LEAD`).
- In Module 3, every suggestion is then checked by ML-002 before it becomes a search query, and the user confirms the search terms.

## Out of scope

- Writing job descriptions, CVs or any free text: the model can only emit dictionary titles.
- Inventing titles: impossible by construction, so titles O*NET does not list are never suggested.
- Inputs other than English.

## Training data

O*NET 31.0 (U.S. Department of Labor, CC BY 4.0): occupation titles, reported titles, job titles and technology skills. No personal data and no user data. Inputs are split by wording (D-009), and extra training-only inputs were added (D-010).

## Performance (2,525 held-out input titles)

| Metric | Value | Target |
|---|---|---|
| Occupation precision (Kaggle / app runner) | 0.851 / 0.828 | >= 0.75 |
| On wording never seen in training (110 examples) | 0.936 | reported only |
| Valid titles / repetition | 1.0 / 0.0 (by construction) | >= 0.85 / < 0.05 |
| Mean latency (i5-1235U) | 407 ms | < 1,500 ms |
| RSS after load / after 20 requests | 994 MB / 1,105 MB | < 300 MB (not met) |

## Limitations and risks

- **Skills can pull results off-topic.** "Software Developer" with skills "Python, SQL, Git" returns postal-clerk titles (Automation Clerk, Mail Handler), while the same title without skills returns software titles. This was found 2026-11-27 and is identical under PyTorch and ONNX, so it is a property of the trained model. ML-002 filtering is the safeguard.
- **Ambiguous inputs drift.** For example, "Checker" gives warehouse titles, and "Data Analyst" gives survey and research titles. ML-002 filtering and user confirmation are the safeguards.
- **US-centric vocabulary** (O*NET). Titles from other labour markets may be missing or mapped to the nearest US occupation.
- **Seniority levels** rely on keyword patterns in O*NET titles. Occupations with few levelled titles fall back to neutral titles.
- **Memory.** Under PyTorch (v2.0.0), PyTorch alone costs about 520 MB, and RSS grows with use (1,248 MB after 2,525 requests). v2.1.0 runs on ONNX Runtime: about 435 MB after load locally, peak 486 MB over 400 requests, against an amended budget of < 550 MB (PROPOSED, D-004).
- **Not a fairness-audited model.** It maps titles to titles and never sees personal attributes.

## Integrity

The app loads the bundle only after SHA-256 verification against `manifest.json`, and only if the manifest records `acceptance.passed = true`.
