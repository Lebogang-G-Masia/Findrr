# Evaluation Report: ML-001 title-expander v2.1.0

- **Model:** the v2.0.0 weights (`google/flan-t5-small`, fully fine-tuned in run 5), exported to ONNX fp32 with a KV-cached decoder (D-004). Decoding is constrained to O*NET titles (D-007).
- **Notebook:** `notebooks/01_train_title_expander.ipynb` as merged in PRs #40 and #41. The run reused the accepted v2.0.0 bundle (`REUSE_BUNDLE_DIR`); nothing was retrained.
- **Exported by:** the project owner on Kaggle. Bundle exported 2026-11-27T14:04:34Z. The manifest records the reused bundle: v2.0.0, exported 2026-11-27T07:44:09Z, `manifest.json` SHA-256 `f4ec8281…1b0e`.
- **Bundle:** `models/title-expander/v2.1.0/` (not in git). SHA-256 of key files:
  - `manifest.json` `20714e6f…af75`
  - `encoder.onnx` `9ca74570…022c`
  - `decoder.onnx` `2404403d…0a49`
  - `embeddings.npy` `70e194d0…8ba7`
  - `titles.json` `9ce05bfa…3238`, the same file as in v2.0.0
- **Report date:** 2026-11-27
- **Status:** Acceptance **passed**. Integrated with real inference (verified 2026-11-27). The memory budget (< 550 MB, D-004) is **met**.

## 1. Evidence sources

| Source | What it is |
|---|---|
| Kaggle run (user) | `evaluation_summary`, `metadata.acceptance` and `metadata.onnx_parity` in the bundle manifest. The notebook computed them on the exported ONNX files on CPU, using the same decoding code as the app (`t5_onnx_decoding`). |
| Local re-evaluation (agent, 2026-11-27) | The installed bundle run on the user's laptop (Intel i5-1235U, 7.4 GiB RAM) with the app's ONNX code. The test set was rebuilt with the notebook's own code from O*NET 31.0 (archive SHA-256 verified). Inference only. |

## 2. Data

The weights, data and split are unchanged from v2.0.0 (see `title-expander-2.0.0.md` §2): 42,624 train, 2,720 val and 2,525 test examples, split by input title (D-009).

## 3. Acceptance criteria (spec, as amended by D-004, D-007, D-009 and D-010)

| Criterion | Kaggle (ONNX) | Laptop (app ONNX path) | Target | Result |
|---|---|---|---|---|
| Occupation precision | 0.851 | 0.828 | >= 0.75 | Pass |
| Valid title ratio | 1.0 | 1.0 | >= 0.85 | Pass |
| Repetition rate | 0.0 | 0.0 | < 0.05 | Pass |
| AC-ML-001.1 distinct titles for "Software Developer" | 5 | 5 | >= 3 | Pass |
| AC-ML-001.2 mean latency | n/a | 456 ms (p95 704 ms, max 1,843 ms) over 2,525 requests | < 1,500 ms | Pass |
| Memory (D-004, PROPOSED and confirmed by merging PR #40) | n/a | 425 MB after load, 486 MB peak | < 550 MB RSS | Pass |
| SHA-256 verification | n/a | all files verified (`findrr model inspect ML-001`) | 100% | Pass |

The laptop precision is lower than Kaggle's for the reason given in the v2.0.0 report: the app runner drops the input title from its suggestions, and the notebook does not.

## 4. Equivalence with v2.0.0

v2.1.0 changes only the runtime, so its outputs should equal v2.0.0's. The evidence says they do:

- **Every Kaggle metric is identical** to v2.0.0's to full floating-point precision. That covers 11 values: occupation precision 0.8505, precision on never-seen wording 0.9362, training-sample precision 0.8795, ROUGE-L, BLEU-4 and the other metrics.
- **ONNX parity checked during export:** encoder difference 3.7e-7, decoder logit difference 3.8e-5 over 7 steps; output scale 1.0.
- **Laptop:** on the first 200 test examples, the installed bundle's suggestions are identical to the v2.0.0 PyTorch runner's in 200 of 200 cases.
- `encoder.onnx` and `decoder.onnx` are not byte-identical to the agent's local prototype export. They were produced by a different PyTorch version (Kaggle 2.11.0), but their outputs match.

## 5. Memory and latency

Each figure is RSS for one process that loads only this model. PyTorch and `transformers` are never imported (checked with `sys.modules`).

| Stage | v2.0.0 (PyTorch) | v2.1.0 (ONNX) |
|---|---|---|
| Interpreter | n/a | 13 MB |
| After load | 994 MB | 425–426 MB (app runner: 447 MB, loads in 1.9 s) |
| Peak over 200 requests | n/a | 482 MB |
| Full test run (2,525 requests): end / peak | 1,248 MB / n/a | 447 MB / 486 MB |

Latency over the first 200 test examples: 434 ms mean, 644 ms p95. Over the full test set (2,525 requests): 456 ms mean, 704 ms p95, 1,843 ms max (v2.0.0 under PyTorch: 407 ms mean, 3,814 ms max).

The laptop's full-test-set precision of 0.828 equals v2.0.0's under PyTorch. Memory does not grow with use: RSS ends the full run at 447 MB, where v2.0.0 grew to 1,248 MB. Mean latency is about 12% higher than under PyTorch, but tail latency is lower, and both stay well within budget.

## 6. Qualitative findings

The outputs equal v2.0.0's, so its findings still apply (see `title-expander-2.0.0.md` §6). Re-checked through the app runner on 2026-11-27:

| Input | Output |
|---|---|
| Truck Driver | CDL Driver, Driver, Heavy and Tractor-Trailer Truck Drivers, Line Haul Driver, Log Truck Driver |
| Software Developer | Application Developer, Application Integration Engineer, Developer, DevOps Engineer, Infrastructure Engineer |
| Software Developer + Python, SQL, Git | Automation Clerk, Computer Forwarding System Markup Clerk, Distribution Clerk, Flat Sorting Machine Clerk, Mail Handler (**open defect**) |
| Registered Nurse + Patient care | APN, Board Certified Clinical Nurse Specialist, Clinical Nurse Specialists, CNS, Critical Care CNS |
| Data Analyst + SQL, Excel | Biometrician, Biostatistical Consultant, Biostatistician, Biostatisticians, Research Scientist |

The skills defect is still open, and fixing it needs retraining with user approval. Other findings:

- The model can return both singular and plural forms of one title, such as "Biostatistician" and "Biostatisticians". Both come from O*NET.
- It can also return an O*NET occupation name, such as "Heavy and Tractor-Trailer Truck Drivers".

Both are noted for the retraining investigation.
