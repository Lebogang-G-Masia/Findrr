# Evaluation Report: ML-001 title-expander v2.0.0

- **Model:** `google/flan-t5-small`, fully fine-tuned, safetensors. Decoding is constrained to O*NET titles (D-007).
- **Notebook:** `notebooks/01_train_title_expander.ipynb` as merged in PR #36 (D-009 input-title split, D-010 extra training inputs and 15 epochs)
- **Trained by:** the project owner on Kaggle (T4 GPU), run 5. Bundle exported 2026-11-27T07:44:09Z.
- **Bundle:** `models/title-expander/v2.0.0/` (not in git). `manifest.json` SHA-256 `f4ec8281…1b0e`; `model.safetensors` SHA-256 `f6af0170…fd478`; `titles.json` SHA-256 `9ce05bfa…63238`
- **Report date:** 2026-11-27
- **Status:** Acceptance **passed**. Integrated with real inference (verified 2026-11-27). The memory budget is **not met** (see §5 and D-004).

## 1. Evidence sources

| Source | What it is |
|---|---|
| Kaggle run 5 (user) | `evaluation_summary` and `metadata.acceptance` in the bundle manifest (unedited threshold 0.75) |
| Local re-evaluation (agent, 2026-11-27) | The installed bundle run through the app's `TitleExpanderRunner` on the user's laptop (Intel i5-1235U, 7.4 GiB RAM) over the full test set, rebuilt with the notebook's own code from O*NET 31.0 (archive SHA-256 verified). Inference only. |

## 2. Data

- O*NET 31.0 (CC BY 4.0). Public data only, with no personal data.
- 42,624 train, 2,720 val and 2,525 test examples, split by normalised input title (D-009). Every test occupation also appears in training, but no test wording is used as a training input. 110 test examples use wording never seen in training at all, as input or target.

## 3. Acceptance criteria (spec, as amended by D-007, D-009 and D-010)

| Criterion | Kaggle | Laptop (app runner) | Target | Result |
|---|---|---|---|---|
| Occupation precision (same occupation or Primary-Short related) | 0.851 | 0.828 | >= 0.75 | Pass |
| Valid title ratio | 1.0 | 1.0 | >= 0.85 | Pass |
| Repetition rate | 0.0 | 0.0 | < 0.05 | Pass |
| AC-ML-001.1 distinct titles for "Software Developer" | 5 | 5 | >= 3 | Pass |
| AC-ML-001.2 mean latency | n/a | 407 ms (p95 620 ms, max 3,814 ms) over 2,525 requests | < 1,500 ms | Pass |
| SHA-256 verification | n/a | all files verified (`findrr model inspect ML-001`) | 100% | Pass |

**Why the laptop precision is lower:** the app runner removes the input title from its suggestions (`TitleExpanderRunner.expand`), and the notebook does not. The laptop returns 4.34 titles per request on average instead of 4.98, and the removed titles always count as hits. The notebook also decodes in padded batches of 64, while the app decodes one request at a time.

## 4. Reported metrics (not gated)

| Metric | Kaggle | Laptop |
|---|---|---|
| Occupation precision on never-seen wording (110 examples) | 0.936 | 0.936 |
| Occupation precision on a 500-example training sample | 0.880 | n/a |
| ROUGE-L / BLEU-4 against one 5-title reference (D-007: not a quality measure) | 0.683 / 0.640 | n/a |
| Requests with no title / runner errors | n/a | 0 / 0 |

## 5. Memory (spec: < 300 MB active RAM): NOT MET

Each figure is RSS for one process that loads only this model and runs 20 requests.

| Stage | RSS |
|---|---|
| Bare `findrr` import | 33 MB |
| After load (PyTorch, transformers, fp32 weights, title trie) | 994 MB |
| After 20 requests | 1,105 MB |
| After 2,525 requests (full test run) | 1,248 MB |

Importing PyTorch and `transformers` alone costs about 520 MB, and the fp32 weights are 308 MB. RSS also keeps growing with use, which needs investigation before Milestone 4. The runtime choice is open decision D-004.

## 6. Qualitative findings

- **Typical good output:** Truck Driver → CDL Driver, Line Haul Driver, Log Truck Driver; Meat Packer → Meat Processor, Boning Room Worker; Casino Shift Manager → Pit Boss, Floor Supervisor.
- **Ambiguous or uncommon inputs drift:**
  - "Checker" (O*NET: Cashiers) → Loader, Receiver;
  - Data Analyst → Market Survey Representative, Research Interviewer;
  - Mechanical Engineer → materials-engineering titles.

  Module 3's ML-002 check at 0.70 removes most of these; for Data Analyst, only Research Scientist (0.73) remains.
- **Titles come only from O*NET** (constraint), so the model cannot suggest titles that O*NET does not list.
