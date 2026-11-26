# Findrr: Decisions Pending

> Read at the start of every session, together with `docs/STATUS.md`.
> Record every material ambiguity here, stop the affected work, and ask the user.
> Never present an assumption as an approved requirement.
> Keep the open-item count below equal to the number of entries under "Open decisions", and mirror it in `docs/STATUS.md`.

**Open items: 6**

## Open decisions

### D-002: Job-discovery source conflicts with robots.txt and site terms (BR-004)
- **Raised:** 2026-11-26, during the pre-Iteration-6 codebase audit
- **Area:** security / requirements / architecture
- **Ambiguity:** ADR-0004 and US-008 approve automated Google Search via Selenium. BR-004 and the AGENTS.md hard rules require respecting robots.txt and site terms. Google's robots.txt contains `Disallow: /search`, and Google's terms prohibit automated queries. Also:
  - the driver sets `--disable-blink-features=AutomationControlled` and a hard-coded Chrome 128 user agent, which hide automation from bot detection;
  - `--no-sandbox` weakens browser security;
  - posting pages are fetched without any robots.txt check.
- **Why it matters:** two approved sources conflict, so the agent must not resolve this silently. A live run on 2026-11-26 got a CAPTCHA on the first query from a fresh profile, so discovery cannot work unattended in practice. Hiding automation also comes close to the "never bypass access restrictions" rule.
- **Options:**
  1. **Official search API for discovery.** Google Programmable Search JSON API (free tier of 100 queries per day, needs an API key) or Bing or Brave Search APIs. Fetch only robots-permitted posting pages, with a plain browser identity. Trade-offs: needs an API key stored outside git and a new external integration (approval and dependency evaluation); most compliant and reliable.
  2. **Official job-board APIs** (for example Adzuna, Greenhouse or Lever public job-board APIs) as primary sources, with search as a fallback. Trade-offs: best data quality and terms compliance, but per-source adapters and coverage gaps outside supported boards and regions.
  3. **Keep Selenium on Google, made explicit.** Remove the evasion flags and `--no-sandbox`, add robots.txt checks for posting pages, and record your written acceptance of the Google terms risk. Trade-offs: least work, but still conflicts with BR-004 for the search step, and CAPTCHAs will stay frequent.
- **Recommendation:** Option 1 now (NFR-010 already provides an abstract search-provider interface), plus the clean-up from Option 3 (remove the evasion flags and `--no-sandbox`, check robots.txt for posting pages) in every case. Consider Option 2 adapters in Milestone 5.
- **Blocked work:** changes to the search driver, the discovery source and robots handling. Unattended live discovery is not possible until this is decided.
- **Status:** Open

### D-003: DOCX/PDF export (US-012) was marked done but is not implemented
- **Raised:** 2026-11-26, during the pre-Iteration-6 codebase audit
- **Area:** requirements / process
- **Ambiguity:** The backlog ticked "Integrate python-docx for DOCX generation", but no DOCX or PDF code exists and `python-docx` is not a dependency. `DocumentGenerator` writes Markdown only. The backlog entry has been corrected to unchecked. Implementing it needs a new dependency.
- **Why it matters:** US-012 is part of the Milestone 2 completion gate ("DOCX/PDF export verified"). Adding a library is a significant dependency that needs approval.
- **Options:**
  1. `python-docx` (MIT licence, about 1 MB, pure Python) for DOCX, and PDF via LibreOffice headless conversion if it is installed. Trade-offs: small dependency; PDF depends on a system tool.
  2. `python-docx` for DOCX plus `fpdf2` (LGPL, pure Python) for PDF. Trade-offs: two dependencies; PDF layout is basic but needs no system tools.
  3. DOCX only for now and defer PDF. Trade-offs: smallest scope; the milestone gate would need re-scoping.
- **Recommendation:** Option 2. Both libraries are pure Python and work offline, and the output stays fully deterministic and grounded.
- **Blocked work:** US-012 implementation.
- **Status:** Open

### D-004: ML-001 runtime uses PyTorch, but ADR-0003 approved ONNX Runtime only
- **Raised:** 2026-11-26, during the pre-Iteration-6 codebase audit
- **Area:** ML / architecture
- **Ambiguity:** `TitleExpanderRunner` loads Flan-T5 via `torch` + `transformers`. ADR-0003 rejected the PyTorch CPU engine and chose ONNX Runtime. *Update 2026-11-26: the approved ML-001 model spec (§10–12) itself specifies safetensors + `AutoModelForSeq2SeqLM` + `torch.no_grad()`, so the conflict is between two approved documents. The rewritten notebook follows the spec.* `STATUS.md` lists "needs torch in .venv". `torch` is installed in `.venv` but declared nowhere. The `ml` extra added on 2026-11-26 declares only ADR-0003 packages (onnxruntime, transformers, numpy).
- **Why it matters:** this is a model compatibility and inference-architecture contract (approval gate), and `torch` is a large dependency (about 700 MB+ on CPU).
- **Options:**
  1. Export ML-001 to ONNX (seq2seq encoder/decoder, for example via `optimum`) in the Kaggle notebook, and run it with ONNX Runtime. Trade-offs: matches ADR-0003 and uses less memory; needs a notebook change, which you would run.
  2. Accept PyTorch for ML-001 only: amend ADR-0003 and declare `torch` in the `ml` extra. Trade-offs: no retraining needed; larger install and memory use.
- **Recommendation:** Option 2 short term, since it unblocks the artifacts that are already trained. Plan Option 1 for Milestone 5 optimisation.
- **Blocked work:** declaring `torch`; real ML-001 integration claims.
- **Status:** Open

### D-005: Company research (US-014): sources and how summaries are produced
- **Raised:** 2026-11-26, during Iteration 6 requirements analysis
- **Area:** requirements / architecture / ML / security
- **Ambiguity:** FR-022 and Module 5 §C require company research "with source attribution" from "reliable sources", but no source is approved. Open points:
  - which sources to use;
  - how to find the employer's website (web search is blocked by D-002);
  - whether summaries are generated by a model (no approved model) or extracted;
  - how to cover "recent developments" (needs a news source).
- **Why it matters:** this involves external integrations, scraping compliance and the no-fabrication rule for company information. A wrong choice risks invented company facts or breaches of site terms.
- **Options:**
  1. **Deterministic, extractive research, no new model.** Use three sources:
     - the stored posting text;
     - the employer's own site, only when a posting URL is employer-direct (homepage and about page, fetched once with a robots.txt check);
     - Wikipedia's official REST summary API (CC BY-SA, with attribution).

     Each fact is stored with its source URL and retrieval date. Missing fields are marked "Not found". Skip "recent developments" until a news source is approved. Trade-offs: no fabrication risk; summaries are excerpts, not prose; adds Wikipedia as an external integration.
  2. Option 1 plus a news API (for example GNews or NewsAPI) for recent developments. Trade-offs: an API key and terms; a free tier is limited.
  3. Generative summaries with a new fine-tuned model (Kaggle). Trade-offs: needs a model spec, dataset and evaluation approval; fabrication risk must be controlled.
- **Recommendation:** Option 1 now, Option 2 later if wanted. Option 3 is not recommended: extraction meets FR-022 without fabrication risk.
- **Blocked work:** US-014 implementation.
- **Status:** Open

### D-006: ML-003 (application tailor) training data and notebook rewrite
- **Raised:** 2026-11-26, during the notebook review requested by the user
- **Area:** ML
- **Ambiguity:** The spec's dataset is "synthetic paired profile-job description datasets (generated and validated against factual grounding heuristics)", but no generation method or validation rule is approved. The current notebook's targets contain fabricated claims, so the dataset approach must be decided before the notebook is rewritten. The notebook is marked DO NOT RUN.
- **Why it matters:** this model writes CV and cover-letter text. Training targets with any unsupported claim teach fabrication, breaking BR-002 and NFR-009.
- **Options:**
  1. **Template-composed targets.** Every target sentence is assembled only from spans copied from the input facts, plus a fixed list of neutral connectors ("Applying for the X role at Y.", "Experience includes:"). A deterministic checker rejects any example whose target contains a content word absent from the inputs. Inputs are built from O*NET task statements and software skills, so no personal data is involved. Trade-offs: fully verifiable and zero fabrication by construction, but the phrasing is plain.
  2. **LLM-paraphrased targets, filtered.** Generate fluent targets with a larger model on Kaggle, then keep only examples that pass the same deterministic content-word checker. Trade-offs: more natural text; needs approval for using a generator model, and the yield after filtering is uncertain.
  3. **Drop ML-003 for now.** The deterministic templates (already fact-only since 2026-11-26) cover FR-020 and FR-021. Revisit in Milestone 5. Trade-offs: no ML phrasing benefit; nothing to train.
- **Recommendation:** Option 1 now, with Option 2 as a later improvement. Both also need:
  - a fact-precision metric over the summary text, not just the skills list;
  - an INT8 export under the 450 MB budget;
  - pinned libraries;
  - the app manifest schema.
- **Blocked work:** rewriting and running `notebooks/03_train_application_tailor.ipynb`.
- **Status:** Open

### D-010: ML-001 occupation precision 0.603; the repetition penalty works against correct answers
- **Raised:** 2026-11-27, after the user's fourth Kaggle run of `01_train_title_expander.ipynb` (v2.0.0, input-title split from D-009)
- **Area:** ML
- **Evidence (Kaggle run 4):** occupation precision **0.603** (target >= 0.75, failed), up from 0.478 on the occupation-disjoint split. The other criteria were not reported as failing. The sample predictions were not yet shared.
- **Evidence (local, no training; the same test split rebuilt with the notebook's code):**
  - Decoding uses `repetition_penalty=1.2` (notebook and runner). Since D-007 it is redundant: the title constraint already makes repeats impossible, and repetition was 0.0 with the penalty off (PR #31 check).
  - The penalty acts on tokens, not titles, and correct answers share words: in **97%** of gold outputs a word recurs across titles, and **56%** of gold titles share a word with an earlier title (e.g. "CEO, Executive Director, Executive Vice President"). So every right sibling title after the first is penalised, pushing decoding towards titles of other occupations.
- **Ambiguity:** the decoding settings (`num_beams=2`, `repetition_penalty=1.2`) are part of the approved notebook and runner contract; changing them needs your approval.
- **Options:**
  1. **Drop the penalty (1.0) in the notebook, `preprocess_config.json` and the runner; also report, without gating, precision with `num_beams=4` (recommended).** Trade-offs: one Kaggle re-run; directly removes a known bias; the beam-4 figure shows whether a wider beam is worth its CPU cost, without committing to it.
  2. **Also train longer (e.g. 10 epochs) in the same run.** Trade-offs: no evidence yet that the model is under-trained; if precision rises, the cause is ambiguous.
  3. **Wait for the 15 sample predictions before changing anything.** Trade-offs: no re-run wasted on a guess, but it costs a round trip, and the penalty is a defect either way.
- **Recommendation:** Option 1, and please paste the 15 sample predictions from the evaluation cell with the next run.
- **Blocked work:** ML-001 export and real Module 3 inference.
- **Status:** Open

## Entry template

Copy this block for each new decision. Number entries `D-001`, `D-002`, and so on, and never reuse a number.

```markdown
### D-NNN: Short title
- **Raised:** YYYY-MM-DD, during <workflow, iteration or document>
- **Area:** requirements | architecture | security | UX | ML | process
- **Ambiguity:** What is unclear or undecided.
- **Why it matters:** What depends on it, and what a wrong guess would cost.
- **Options:**
  1. Option A. Trade-offs.
  2. Option B. Trade-offs.
- **Recommendation:** Which option, and why.
- **Blocked work:** What has been paused until this is decided.
- **Status:** Open
```

## Resolved decisions

Move an entry here when the user decides. Change its status to Resolved, and add the decision, the date, and the document updated to reflect it.

### D-009: ML-001 occupation precision 0.478; the 0.75 threshold was calibrated against an unfair baseline
- **Raised:** 2026-11-26, after the user's third Kaggle run of `01_train_title_expander.ipynb` (v2.0.0, constrained decoding with the PR #31 fix)
- **Area:** ML
- **Evidence (Kaggle run 3, held-out test occupations):**

  | Criterion | Value | Target | Result |
  |---|---|---|---|
  | Occupation precision | 0.478 | >= 0.75 | Failed |
  | Valid title ratio | 1.000 | >= 0.85 | Passed |
  | Repetition rate | 0.0001 | < 0.05 | Passed |
  | AC-ML-001.1 distinct titles | 5 | >= 3 | Passed |

  The constraint now works as intended: every title is real, there are no repeats, and outputs carry 5 titles. The sample predictions were not yet shared.
- **Evidence (local, no training; same O*NET 31.0 split rebuilt with the notebook's own code):**
  - The split is occupation-disjoint: the 87 test occupations never appear in training. Only **17.5%** of their reference titles ever appear as a training target, so the model has almost never generated the right titles for a test occupation. The best it can do is emit titles of a *related training* occupation.
  - That is reachable in principle: every test occupation has a Primary-Short related occupation in training, so a perfect choice among training titles scores 1.0.
  - **My 0.736 baseline (PR #27) was unfair.** It drew random titles from the same SOC broad group (e.g. 15-125x; PR #27 called it the minor group) *including the test occupation's own titles*, which the model never saw. Restricted to titles the model saw as training targets:

    | Baseline (random training-target titles) | Occupation precision |
    |---|---|
    | Same SOC broad group (e.g. 15-125x) | 0.579 |
    | Same detailed SOC code, sibling O*NET occupations (e.g. 15-1252.xx) | 0.489 |
    | Same SOC major group (e.g. 15) | 0.094 |

  - The model (0.478) scores below a random training title from the right broad group (0.579). The samples will show whether it picks the wrong family or the wrong occupation within it.
- **Ambiguity:** the approved threshold (0.75) asks for better than the broad-group baseline, but that baseline assumed the model could output the test occupation's own titles. With an occupation-disjoint split it cannot have learned them. In the app, by contrast, every O*NET occupation is known: the dictionary is fixed, and a user's title maps to one of those occupations. The current split therefore tests a harder task than the deployed one.
- **Why it matters:** ML-001 blocks real Module 3 inference. The threshold and the split are approved acceptance criteria and spec content, so only you can change them.
- **Options:**
  1. **Split by input title within occupations (recommended).** Every occupation contributes to training; test examples use anchor titles (inputs) and skill combinations never seen in training. Keep the 0.75 threshold, which is now a fair test against the 0.736 baseline. Also report held-out-occupation precision without gating it, as a generalisation check. Trade-offs: it matches the deployed task (known dictionary, unseen user wording); test targets overlap training targets, so it measures correct association rather than open-ended generalisation. It needs a spec change (§10 split, §14) and a notebook change, and you re-run notebook 01.
  2. **Keep the occupation-disjoint split and recalibrate the threshold** against the fair baseline (for example >= 0.60, just above 0.579). Trade-offs: smallest change, but the current model (0.478) still fails, so it also needs option 3.
  3. **Stronger model or training on the current split** (more epochs, or `flan-t5-base` at 250M parameters). Trade-offs: no spec change for the metric; success is uncertain; a larger model affects CPU latency and touches D-004.
- **Recommendation:** Option 1. It evaluates what Findrr does with the model and keeps the approved threshold meaningful. Please also paste the 15 sample predictions from the evaluation cell: they show whether errors are near-misses (related family) or unrelated.
- **Blocked work:** ML-001 export and real Module 3 inference.
- **Status:** Resolved
- **Decision:** Option 1, owner decision 2026-11-26. The 0.75 threshold is unchanged. Held-out-occupation precision cannot be measured on a model trained on every occupation, so the notebook instead reports precision on test inputs whose wording never appears in training (22 anchors, 110 examples).
- **Recorded in:** `scripts/generate_kaggle_notebooks.py`, `notebooks/01_train_title_expander.ipynb`, `docs/ml/models/title-expander.md` §8, §10 and §14, `docs/ml/training/title-expander.md`

### D-008: ML-002 failed acceptance on Pearson r; the proxy labels cap it
- **Raised:** 2026-11-26, after the user's first Kaggle run of `02_train_similarity_evaluator.ipynb` (v1.1.0)
- **Area:** ML
- **Evidence (Kaggle run, exported INT8 ONNX model, held-out occupations):**

  | Criterion | Value | Target | Result |
  |---|---|---|---|
  | Pearson r vs graded labels | 0.745 | >= 0.85 | Failed |
  | Precision at 0.70 | 0.963 | >= 0.90 | Passed |
  | AC-ML-002.1 synonyms ("Software Developer" / "Software Engineer") | 0.894 | >= 0.85 | Passed |
  | AC-ML-002.2 distinct ("Software Developer" / "Dental Assistant") | 0.248 | < 0.30 | Passed |

  The notebook correctly refused to export. Spearman rho and ONNX/PyTorch parity were printed in cell 12 but not yet shared.
- **Evidence (local, no training):** the same 800 test pairs, rebuilt with the notebook's own code (labels 0/1/2/3: 306/89/99/306), scored with the *untrained* base model `all-MiniLM-L6-v2`:
  - Pearson 0.614, Spearman 0.629, precision at 0.70 1.00. Fine-tuning raised Pearson by about 0.13.
  - Mean score per label: 0 = 0.19, 1 = 0.31, 2 = 0.35, 3 = 0.48.
  - The proxy labels disagree with meaning in both directions:
    - label 3 (same O*NET occupation) includes "Crystal Grower" / "Probe Operator", "Casino Gaming Regulator" / "SIU Clinical Investigator" and "Animal Sticker" / "Abalone Processor";
    - label 1 (Primary-Long related) includes "Doctor" / "DO Physician" and "Communications Officer" / "Communications Op".
- **Ambiguity:** the spec (§8) sets Pearson r >= 0.85 "against human-labeled semantic similarity benchmarks". No such benchmark exists, so §14 substituted proxy labels from O*NET structure. A 4-level taxonomy label is not a similarity score: broad O*NET occupations group lexically and semantically distant titles. A model would have to learn those groupings, not title meaning, to reach 0.85. Pushing for it would hurt Findrr's actual uses (title faithfulness and duplicate detection).
- **Why it matters:** ML-002 gates Module 3 title validation and Module 4 deduplication. Its thresholds are approved acceptance criteria, so only you can change them.
- **Options:**
  1. **Gate on the task metrics; report Pearson and Spearman without gating (recommended).** The approved uses are threshold decisions (0.70 relevance, 0.88 duplicate). Keep precision at 0.70 >= 0.90, AC-ML-002.1 and AC-ML-002.2. Add, as PROPOSED thresholds for you to set:
     - recall of same-occupation pairs at 0.70;
     - false-duplicate rate at 0.88 on unrelated and related pairs.

     Also clean the proxy: drop "All Other" catch-all occupations (7 of 102 test occupations) from same-occupation pairs, and print per-label means. Trade-offs: needs a spec change (§8 and §14) and a notebook change, and you re-run notebook 02. The gate measures what the app does with the scores.
  2. **Keep Pearson as a gate with a lower threshold on the proxy** (for example 0.70, which this run passes, against a base-model value of 0.61). Trade-offs: smallest change; you could re-run unchanged with only the threshold edited. Still gates on a metric that rewards learning O*NET groupings.
  3. **Try to reach 0.85 with a stronger model or training** (more epochs, hard negatives from related tiers, or `all-mpnet-base-v2`). Trade-offs: no spec change for the metric, but success is uncertain because of label noise. A larger model is a model change against the latency (< 50 ms) and memory (< 100 MB) budgets.
  4. **Build a small human-labelled benchmark** (a few hundred public title pairs that you score), as the spec intended. Trade-offs: the most faithful to §8, but it takes your time, and its labels must stay out of training.
- **Recommendation:** Option 1. It keeps the gate on behaviour Module 3 and Module 4 depend on, and it stops rewarding taxonomy artefacts. Option 4 can follow in Milestone 5.

  Please also paste the full cell 12 output (Spearman and ONNX parity) for the evaluation report.
- **Blocked work:** ML-002 export and real Module 3 and Module 4 similarity inference.
- **Status:** Resolved
- **Decision:** Option 1, reduced to its core: remove Pearson r from the acceptance gate but keep reporting it (with Spearman rho). Owner decision 2026-11-26. No new gated metrics and no change to the evaluation pairs; the gate is precision at 0.70 >= 0.90, AC-ML-002.1 and AC-ML-002.2.
- **Recorded in:** `scripts/generate_kaggle_notebooks.py`, `notebooks/02_train_similarity_evaluator.ipynb`, `docs/ml/models/similarity-evaluator.md` §8 and §14, `docs/ml/training/similarity-evaluator.md`, `docs/requirements/srs.md` (ML-002 evaluation criteria)

### D-007: ML-001 failed acceptance; ROUGE-L target is unreachable by design
- **Raised:** 2026-11-26, after the user's first Kaggle run of `01_train_title_expander.ipynb` (v2.0.0)
- **Area:** ML
- **Evidence (Kaggle run, held-out occupations, 2,585 test examples):**

  | Metric | Value | Target |
  |---|---|---|
  | ROUGE-L | 0.194 | >= 0.75 |
  | Valid title ratio | 0.554 | >= 0.85 |
  | Repetition rate | 0.580 | < 0.05 |
  | AC-ML-001.1 distinct titles | 3 | >= 3 (passed) |

  The notebook correctly refused to export.
- **Evidence (local, no training):** ROUGE-L of *ideal* answers against the same test references.

  | Answer | ROUGE-L |
  |---|---|
  | 5 different valid titles of the same occupation | 0.273 |
  | The exact reference titles in another order | 0.643 |
  | 3 reference titles + 2 other valid ones | 0.656 |

  A test occupation has a median of 39 valid titles; the reference is one arbitrary sorted list of 5.
- **Ambiguity:** Is the problem the model, the metric, or both? The answer is both:
  - **Metric:** ROUGE-L >= 0.75 is unreachable by any correct answer except the exact reference list in exact order. It measures agreement with one arbitrary sample, not title quality.
  - **Model:** repetition (0.58) and invalid titles (0.55) are genuine defects. Unconstrained Flan-T5-small loops and invents titles for occupations it has not seen.
- **Why it matters:** ML-001 feeds Module 3. Invented titles become real search queries, and the spec's acceptance criteria cannot be met as written. Changing metrics, thresholds, decoding or architecture all need approval.
- **Options:**
  1. **Constrained generation (recommended).** Keep fine-tuned Flan-T5. Restrict decoding to real O*NET titles via a prefix trie over the 46k-title dictionary (shipped in the bundle as `titles.json`, about 1 MB), and block repeating an already-generated title.

     The dictionary contains every O*NET title. That is not test leakage at inference: the app ships the same dictionary. Training stays occupation-disjoint.

     Replace ROUGE-L with set metrics against the occupation's full title set:
     - **occupation precision:** generated titles that belong to the same occupation, or to a Primary-Short related one;
     - **distinct titles per request.**

     Valid ratio becomes 1.0 and repetition 0.0 by construction, so they turn into hard invariants. Trade-offs: needs approval of the new metric and its threshold; adds a trie step to the runner; the model can only suggest titles O*NET knows.
  2. **Unconstrained generation, tuned.** Add `no_repeat_ngram_size=3` and dedupe, train longer or use `flan-t5-base` (about 250M parameters, model change), and replace ROUGE-L with the same set metrics. Trade-offs: keeps open vocabulary, but invented titles remain likely, and the valid-ratio target may still fail.
  3. **Retrieval instead of generation.** Use the ML-002 embeddings to return the nearest O*NET titles; no generative model. Trade-offs: simplest and most reliable, but drops Model 1 and changes FR-008 ("generative transformer model"). That is a requirements change.
- **Recommendation:** Option 1. It keeps the approved generative, fine-tuned design (FR-008); it makes invented titles impossible, which matters because they become live search queries; and it replaces a metric no correct answer can pass with one that measures what Module 3 needs.

  The occupation-precision threshold must come from you. A reference point I can compute before you choose: the score of the current gold lists under the new metric (1.0 by construction) and of a same-major-group random baseline.
- **Blocked work:** ML-001 retraining; real Module 3 inference.
- **Status:** Resolved
- **Decision:** Option 1, constrained generation. Owner decision 2026-11-26. The occupation-precision threshold 0.75 is PROPOSED and is confirmed by merging the implementing PR.
- **Recorded in:** `src/findrr/ml/title_constraint.py`, `TitleExpanderRunner`, `notebooks/01_train_title_expander.ipynb`, `docs/ml/models/title-expander.md` §8, §10, §12 and §14

### D-001: Handling CAPTCHA Interception and Browser Session Persistence in Job Discovery
- **Decision:** Option A: Human-in-the-loop manual completion prompt in headful CLI + persistent Chrome profile directory (`chrome_profile/`).
- **Decided:** 2026-11-07
- **Recorded in:** `src/findrr/search/driver.py`, `src/findrr/search/engine.py`, `docs/spec/modules/04-find-postings.md`
- **Summary:** When Google redirects to `google.com/sorry/index` or displays a bot challenge, Findrr halts execution, alerts the user in the CLI, and keeps the headful Chrome window open for the user to solve the challenge manually. Using a persistent `chrome_profile/` ensures solved tokens and session cookies are remembered across searches.
