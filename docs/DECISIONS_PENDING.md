# Findrr: Decisions Pending

> Read at the start of every session, together with `docs/STATUS.md`.
> Record every material ambiguity here, stop the affected work, and ask the user.
> Never present an assumption as an approved requirement.
> Keep the open-item count below equal to the number of entries under "Open decisions", and mirror it in `docs/STATUS.md`.

**Open items: 1**

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
- **Update 2026-11-27 (owner preference and new evidence):**
  - The owner chose option 1 with the Google Programmable Search JSON API.
  - Google's own overview page now says the API "is not available for new customers" and will be discontinued on January 1, 2027. A new key would return 403. Option 1 therefore needs a different provider. Bing's Search API was retired in 2025.
  - The owner asked whether CAPTCHAs can be bypassed. They cannot: BR-004 and AGENTS.md forbid it. An official search API never shows a CAPTCHA, so the question does not arise there. If a posting page shows one, the run records it, and a person may solve it in the headful browser (D-001).
- **Revised options:**
  - 1a. **Brave Search API.** An independent index. Needs an API key kept outside git. Check its current free-tier limits and terms in the dependency evaluation.
  - 1b. **Google Vertex AI Search.** Google's named successor. It searches only sites you list, such as job boards, and needs a Google Cloud project with billing.
  - 2. **Official job-board APIs.** Unchanged, for example the Adzuna API; needs per-source adapters.
- **Revised recommendation (superseded below):** 1a for general discovery, behind the existing search-provider interface (NFR-010), plus the option 3 clean-up in every case. Add option 2 adapters later.
- **Research 2026-11-27 (owner asked for free alternatives).** Sources are the providers' own pages, read on this date. The limits change often, so re-check them in the dependency evaluation.

  | Source | Kind | Free allowance | Notes |
  |---|---|---|---|
  | Tavily | Web search API | 1,000 credits a month, "No credit card required" | Credits per basic search are not stated on the pricing page. Usable for D-005 (finding an employer's site). |
  | Brave Search API | Web search API | Monthly free credit; the pages say both $5 and "up to $20". About 1,000 searches at $5 per 1,000 | A card is requested "to prevent abuse". Storing results needs a custom plan. The old 2,000-query free plan has ended. |
  | Adzuna | Job-listings API | Free key, "no payment details required". Limits are not published and "may vary" | Terms permit "Personal job search". Each displayed listing must carry an "Adzuna" link. Revenue-generating use needs a licence. Country list not confirmed. |
  | Greenhouse, Lever, Ashby | Employer job boards (ATS) | Keyless public JSON endpoints | Each needs the employer's board name, so they suit employer-direct follow-up, not open discovery. Lever: published postings "are publicly viewable". |
  | Jooble | Job-listings API | Key by request form; limits not stated on its page | Third-party reports mention a lifetime cap of about 500 requests per key. Unverified. |
  | Serper | Google results API | 2,500 queries once, no refill | Not ongoing. |
  | DuckDuckGo, SearXNG | — | — | No official search API. SearXNG sends bot traffic to other engines and is blocked by CAPTCHAs. Not compliant with BR-004. |

- **Revised options (2026-11-27, after research):**
  1. **Tavily** as the web-search provider behind the NFR-010 interface. Free with no card; about 1,000 searches a month.
  2. **Adzuna** as the job-listings source, plus Tavily for general search. Adzuna returns structured postings (title, company, location, salary) rather than pages to parse, and personal job search is its permitted use. It depends on country coverage.
  3. **Brave Search API.** Similar to Tavily, but needs a card.
  4. Any of the above, plus **Greenhouse, Lever and Ashby adapters** for employers the user names (keyless, Milestone 5).
- **Recommendation (after research):** Option 2, if Adzuna covers the owner's job market; otherwise option 1. Do the option 3 clean-up (evasion flags, `--no-sandbox`, robots.txt) in every case.
- **Update 2026-11-27 (owner: job market South Africa; the app must scale to many users).** Findings, from providers' own pages unless marked:
  - **No free tier is meant for a multi-user product.** Each source has a paid or licensed path for scale.
  - **Careerjet publisher API** (`search.api.careerjet.net/v4/query`): built for third-party sites that show jobs to their own users. The key comes from a free publisher account. careerjet.co.za exists and its sample job uses ZAR. Every request must carry the end user's IP address and user agent, a privacy point to handle on the Milestone 4 server. Locale list, rate limits, cost and display terms are in its publisher terms, not yet read.
  - **Adzuna:** South Africa (`za`) appears only in third-party lists; Adzuna's own pages do not confirm it. The free key covers "Personal job search". A product that "generates revenue or leads" needs a licence.
  - **Tavily:** scales on pay-as-you-go ($0.008 a credit). Its terms allow integration in the customer's own applications but forbid sharing the key with third parties.
  - **South African boards** (PNet, Careers24, CareerJunction): no public APIs were found, only third-party scrapers. Ruled out by BR-004.
  - **Jooble:** its site terms forbid bots, and no API terms were found. Ruled out for now.
  - **Common Crawl / Web Data Commons JobPosting data:** free and large, but published yearly, so too stale for live postings. Ruled out for discovery.
- **Recommendation (scalable):** Careerjet as the primary job source for South Africa, Adzuna as a second source once a live call confirms `za`, and Tavily for web search (D-005 company sites). Each sits behind the NFR-010 provider interface, so a free key can later become a paid or licensed one without changes to the core. Greenhouse, Lever and Ashby adapters are for employer-direct follow-up. Do the option 3 clean-up in every case. Before building: read Careerjet's publisher terms; run one test call per provider when the owner has keys.
- **Update 2026-11-27 (owner: completely free sources only).** From providers' own pages:
  - **Careerjet Job Search API:** "free", and Careerjet pays a "revenue share" for referred traffic. You must "declare your IP address(es)" first; "Dynamic IP addresses or serverless environments without fixed outbound IP addresses are not supported." Prohibited: building "an independent job database" or competing search, redistributing the data, AI/ML training or evaluation on it, and bulk extraction not for showing jobs to job seekers. No numeric limits stated; Careerjet may suspend use "outside the permitted scope". It is framed for partners' "websites". Display and caching rules are not stated.
  - **Employer ATS public endpoints, no key:**
    - Greenhouse and Lever (confirmed earlier);
    - Workable `GET workable.com/api/accounts/{subdomain}`;
    - Recruitee `GET {company}.recruitee.com/api/offers/`;
    - SmartRecruiters `GET api.smartrecruiters.com/v1/companies/{id}/postings`. Its docs mention API keys, so auth is unclear; the general limit is 10 requests a second.
    - Each needs the employer's identifier.
  - **Web search:** no free option permits commercial use. Marginalia's free key is "non-commercial" (results CC BY-NC-SA). Tavily's and Brave's free tiers are capped trials of paid services.
- **Free-only options:**
  - F1. **Careerjet + ATS adapters + Wikipedia** (D-005). Postings from Careerjet; employer-direct postings from ATS boards; company facts from the posting, the employer's site and Wikipedia. No web search at all. Trade-offs:
    - needs a fixed public IP, which a home connection usually lacks (the Milestone 4 server would have one);
    - Findrr must not store Careerjet postings as its own database, beyond what the user tracks;
    - postings must never be used for ML training (relevant to ML-003).
  - F2. **ATS adapters only**, over a curated list of South African employers' boards. Completely free, keyless and compliant. Coverage is limited to employers on the list that use these systems.
- **Recommendation (free-only):** F1 for Milestone 4, starting with F2 now: it works on the laptop today and stays useful at scale. Apply for Careerjet when a fixed IP is available. Do the option 3 clean-up in every case.
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
- **Status:** Resolved
- **Decision:** Option 1, template-composed targets with a deterministic content-word checker. Owner decision 2026-11-27. The owner asked to use option 2 with their Claude subscription only if that was allowed, and option 1 otherwise. Option 2 on the subscription is not allowed. The Consumer Terms (effective Oct 8, 2025, section 3) prohibit using the Services "to develop or train any artificial intelligence or machine learning algorithms or models". They also prohibit scripted or automated access except through an Anthropic API key. Option 2 can be revisited later with a separately approved generator (for example an open model run on Kaggle).
- **Recorded in:** this entry. Next: a rewritten ML-003 dataset spec and notebook 03 for review (the model spec and training methodology are user-review items).

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
- **Status:** Resolved
- **Decision:** Option 1, deterministic extractive research with no new model, from three sources: the stored posting, the employer-direct site (robots.txt checked) and the Wikipedia REST summary API. Each fact keeps its source URL and retrieval date. "Recent developments" are skipped until a news source is approved. Owner decision 2026-11-27.
- **Note:** until D-002 provides a web search source, the employer's site is used only when the posting URL is employer-direct.
- **Recorded in:** this entry. To be implemented in US-014.

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
- **Status:** Resolved
- **Decision:** Option 2, `python-docx` for DOCX and `fpdf2` for PDF. Owner decision 2026-11-27. This approves both dependencies; each still gets a dependency evaluation (`docs/process/dependency-policy.md`) in the implementing PR.
- **Recorded in:** this entry. To be implemented in US-012.

### D-012: How the model dashboard's numbers stay current
- **Raised:** 2026-11-27, owner request: "The numbers on the dashboard should NOT be a snapshot. They should update if anything changes."
- **Area:** process
- **Ambiguity:** The dashboard's data is files built on the laptop and uploaded by hand. A dashboard page can only read live data through a claude.ai connector, and there is no GitHub connector in this setup. Half the numbers (the installed bundles' manifests, the latency benchmark, sample outputs) exist only on the laptop: `models/` is git-ignored. Run history and decisions are also typed into `build.py` instead of read from a machine-readable source.
- **Why it matters:** each option changes what is committed to this public repo or adds automation that acts on the owner's account.
- **Options:**
  1. **Commit the built data and read it live from GitHub.** `build.py` writes small JSON files (metrics, benchmark and splits; no weights) to a committed folder. A git hook rebuilds them on each commit, and the dashboard reads them through a GitHub connector every time it is opened. Trade-offs: truly live for anything merged to `main`, and every reader sees the same data. Needs the owner to connect GitHub on claude.ai. Laptop-only facts change when the hook runs.
  2. **Local watcher.** A user-level systemd unit watches `models/` and `docs/`, rebuilds, and runs headless Claude Code to upload the changed files. Trade-offs: updates within a minute of any local change, with nothing new committed; works only while the laptop is on, and gives headless Claude upload rights.
  3. **Cloud routine on every push to `main`.** A scheduled-task webhook rebuilds from the repo and uploads. Trade-offs: no connector and no laptop needed, but like option 1 it needs the data committed, and every run costs usage.
- **Recommendation:** Option 1. It is the only option where the page itself reads live data, and it has no moving parts beyond a git hook.
- **Blocked work:** live dashboard data.
- **Status:** Resolved
- **Decision:** Option 1, owner decision 2026-11-27 ("Live from GitHub"). `build.py` writes `scripts/model_dashboard/data/` (committed), reads decisions straight from this log, and a `pre-commit` hook in `scripts/model_dashboard/hooks/` rebuilds and stages the data before each commit, without ever blocking one. The dashboard reads `data/` through a GitHub connector once the owner connects GitHub on claude.ai; until then the files are uploaded by hand.
- **Update 2026-11-27:** the GitHub entry on claude.ai is the built-in integration (repository access for chats, Projects and cloud sessions), not a connector with callable tools, so the dashboard cannot read GitHub itself. Delivery uses option 3 instead: the cloud scheduled task "Findrr dashboard sync" fires when a pull request is merged into `main`, compares the merge with its parent, and uploads only changed dashboard files (no dashboard change: it stops after one `git diff`). Tested by hand on 2026-11-27 (34 s, all writes succeeded). Manage it at https://claude.ai/code/routines.
- **Recorded in:** `scripts/model_dashboard/README.md`, `build.py`, `bench.py`, `hooks/pre-commit`

### D-011: Where the model dashboard's data tool lives
- **Raised:** 2026-11-27, after building the Findrr Model Observatory (a private claude.ai dashboard about ML-001 to ML-003) at the user's request, outside the plan
- **Area:** process
- **Ambiguity:** The dashboard's data is built by two scripts (benchmark and data build). They were in a temporary folder, so the dashboard could not be refreshed after the next Kaggle run. The tool is not in the roadmap or backlog.
- **Why it matters:** the scripts depend on Findrr's bundle manifests, registry and runners, and the repo is public.
- **Options:**
  1. **In this repo, as a developer tool** (`scripts/model_dashboard/`). Trade-offs: stays in step with the manifests and runners; adds unplanned tooling to the repo, though the app never imports it.
  2. **A separate project.** Trade-offs: keeps Findrr strictly on plan; breaks silently when Findrr changes, and still needs Findrr's environment.
  3. **Pin the dashboard only.** Trade-offs: no repo change; the data can never be refreshed.
- **Recommendation:** Option 1.
- **Blocked work:** none.
- **Status:** Resolved
- **Decision:** Option 1, owner decision 2026-11-27 ("Go ahead with the in-repo PR"). The tool runs on demand only: it runs real CPU inference with the installed bundles, never trains, and writes to the git-ignored `build/model-dashboard/`.
- **Recorded in:** `scripts/model_dashboard/` (README, `bench.py`, `build.py`)

### D-004: ML-001 runtime uses PyTorch, but ADR-0003 approved ONNX Runtime only
- **Raised:** 2026-11-26, during the pre-Iteration-6 codebase audit
- **Area:** ML / architecture
- **Ambiguity:** `TitleExpanderRunner` loads Flan-T5 via `torch` + `transformers`. ADR-0003 rejected the PyTorch CPU engine and chose ONNX Runtime. *Update 2026-11-26: the approved ML-001 model spec (§10–12) itself specifies safetensors + `AutoModelForSeq2SeqLM` + `torch.no_grad()`, so the conflict is between two approved documents. The rewritten notebook follows the spec.* `STATUS.md` lists "needs torch in .venv". `torch` is installed in `.venv` but declared nowhere. The `ml` extra added on 2026-11-26 declares only ADR-0003 packages (onnxruntime, transformers, numpy).
- **Why it matters:** this is a model compatibility and inference-architecture contract (approval gate), and `torch` is a large dependency (about 700 MB+ on CPU).
- **Options:**
  1. Export ML-001 to ONNX (seq2seq encoder/decoder, for example via `optimum`) in the Kaggle notebook, and run it with ONNX Runtime. Trade-offs: matches ADR-0003 and uses less memory; needs a notebook change, which you would run.
  2. Accept PyTorch for ML-001 only: amend ADR-0003 and declare `torch` in the `ml` extra. Trade-offs: no retraining needed; larger install and memory use.
- **Recommendation:** Option 2 short term, since it unblocks the artifacts that are already trained. Plan Option 1 for Milestone 5 optimisation.
- **Update 2026-11-27 (evidence, local, inference only):** ML-001 v2.0.0 (Kaggle run 5) is installed and passes acceptance. The open question is now its memory, against a spec budget of < 300 MB.
  - **PyTorch runner (current):** 994 MB after load, 1,105 MB after 20 requests, 1,248 MB after 2,525 requests (it grows). Importing PyTorch and `transformers` alone costs about 520 MB.
  - **ONNX prototype:** the installed weights were exported locally to an encoder and a decoder (without a KV cache). It runs on ONNX Runtime + `tokenizers` with a NumPy copy of the 2-beam constrained search, and never imports PyTorch.
  - **Fixed overhead without PyTorch:** ONNX Runtime + `findrr` 67 MB, tokenizer 32 MB, title trie 32 MB.
  - **Results on the first 200 test examples:**

    | Variant | Occupation precision | Same output as PyTorch | RSS after load | Mean latency |
    |---|---|---|---|---|
    | PyTorch (current) | 0.827 | — | 884 MB | 481 ms |
    | ONNX fp32 | **0.827** | **200 / 200** (max logit diff 6e-5) | 531 MB | 1,062 ms (no KV cache) |
    | ONNX INT8 (dynamic) | 0.728 | 107 / 200 | 254 MB | 741 ms |
    | ONNX INT8 per-channel | 0.685 | 115 / 200 | 257 MB | 491 ms |
    | ONNX INT8 per-channel, vocabulary layers fp32 | 0.714 | 125 / 200 | 382 MB | 840 ms |
    | ONNX INT8 encoder + fp32 decoder | 0.724 | — | 437 MB | 1,565 ms |

    Latencies are noisy: the laptop was also running other work.
  - **Conclusion:** fp32 ONNX is exact and saves about 450 MB, but cannot reach 300 MB. Its weights alone are about 370 MB as exported, or about 240 MB if the shared embedding is stored once. With the dynamic and per-channel INT8 settings tried here, every variant falls below the 0.75 acceptance threshold. Reaching < 300 MB would need quantisation-aware fine-tuning or a smaller model, which means retraining on Kaggle and a new evaluation.
- **Options (revised 2026-11-27):**
  1. **ONNX fp32 with a KV cache, exported in notebook 01.** The runner drops PyTorch and keeps identical outputs. Amend the ML-001 memory budget to the measured value (about 550–650 MB, PROPOSED). Trade-offs: a notebook export change (no retraining is needed, but artifacts must come from the notebook, so you re-run it) and a NumPy beam search in the runner. The KV cache is needed to bring latency back to the PyTorch level.
  2. **Keep PyTorch (former option 2).** Amend ADR-0003 and the budget to about 1.2 GB, declare `torch`, and investigate the RSS growth. Trade-offs: no work now, but the largest footprint, and a poor fit for the Milestone 4 server.
  3. **Meet < 300 MB.** Quantisation-aware fine-tuning or distillation to a smaller model on Kaggle. Trade-offs: a new training approach (needs spec and dataset approval); success is uncertain.
- **Recommendation (revised):** Option 1. It removes PyTorch, changes no output, and gives a budget that is honest and measured. Option 3 can be evaluated in Milestone 5 if memory matters on the server.
- **Blocked work:** declaring `torch`; the ML-001 runtime and memory budget.
- **Status:** Resolved
- **Decision:** Option 1 (revised), ONNX fp32 with a KV cache. Owner decision 2026-11-27. The ML-001 memory budget becomes < 550 MB RSS, a PROPOSED value confirmed by merging the implementing PR.
- **Recorded in:**
  - `src/findrr/ml/t5_onnx_decoding.py`, `src/findrr/ml/t5_onnx_export.py`, `TitleExpanderRunner`, registry (ML-001 v2.1.0);
  - `notebooks/01_train_title_expander.ipynb`;
  - `docs/ml/models/title-expander.md` §10–12 and §14, `docs/ml/training/title-expander.md`, ADR-0003 (update).

### D-010: ML-001 occupation precision 0.603; the model under-fits its training data
- **Raised:** 2026-11-27, after the user's fourth Kaggle run of `01_train_title_expander.ipynb` (v2.0.0, input-title split from D-009). Revised the same day with local evidence; the first version blamed the repetition penalty, which the evidence below rules out as the main cause.
- **Area:** ML
- **Evidence (Kaggle run 4):** occupation precision **0.603** (target >= 0.75), valid ratio 1.0, repetition 0.0, AC-ML-001.1 5, precision on never-seen wording 0.561 (110 examples). ROUGE-L 0.366, BLEU-4 0.278.
- **Bundle note:** the bundle the user downloaded records `occupation_precision` threshold **0.0** and `acceptance.passed: true`, so the threshold was edited in the Kaggle copy. It must not be installed as an accepted model.
- **Evidence (local inference with that bundle on the laptop, 500 seeded inputs; no training):**

  | Experiment | Occupation precision |
  |---|---|
  | Test inputs, current decoding (2 beams, penalty 1.2) | 0.585 (Kaggle on all 2,525: 0.603) |
  | Penalty off (1.0) | 0.591 |
  | Penalty off, 4 beams | 0.568 |
  | Remaining titles locked to the first title's occupation and its Primary-Short related ones | 0.635 |
  | **Training inputs** (seen 5 times), penalty off | **0.727** |

  - Precision by output position: 0.69, 0.63, 0.61, 0.56, 0.47. Even the first title is wrong 31% of the time.
  - The samples show prefix drift, e.g. "Rig Hand" -> "Rig Operator, Rig Hand, Rig Mechanic*, Jig Hand*, Jig Worker*".
  - Decoding changes do not reach 0.75. The model has not learned the training mapping well, so this is under-fitting rather than a generalisation gap.
  - Training uses 5,310 anchors (input titles); O*NET has 45,512 comma-free job titles for the same occupations that are never used as inputs.
- **Ambiguity:** the training recipe and dataset construction are spec content (§10, §14), so changing them needs your approval.
- **Options:**
  1. **Train longer and with more input titles (recommended).**
     - 15 epochs instead of 5.
     - Add O*NET job titles as extra training-only anchors (capped per occupation, level ANY), skipping any wording that is a val or test anchor.
     - Drop the redundant penalty.
     - Also report precision on a training sample, so one run shows whether it still under-fits.

     Trade-offs: same model and app; Kaggle run time grows (roughly 1 hour on a T4); success likely but not certain.
  2. **Option 1 plus `flan-t5-base` (250M parameters).** Trade-offs: more capacity; about 3 times slower CPU inference and a 1 GB bundle; touches D-004.
  3. **Lock decoding to the first title's occupation** in the notebook and runner. Trade-offs: measured +0.04 only; worth adding later on top of option 1.
- **Recommendation:** Option 1; if it still falls short, option 2 with the same data.
- **Blocked work:** ML-001 export and real Module 3 inference.
- **Status:** Resolved
- **Decision:** Option 1, owner go-ahead 2026-11-27 ("How do I train it more job titles?" / "There's no PR"). Implemented in PR #36; merging the PR approves the training-recipe change.
- **Recorded in:** `scripts/generate_kaggle_notebooks.py`, `notebooks/01_train_title_expander.ipynb`, `src/findrr/ml/title_expander_runner.py`, `docs/ml/models/title-expander.md` §10 and §14, `docs/ml/training/title-expander.md`, `docs/design/technical-specs.md`

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
