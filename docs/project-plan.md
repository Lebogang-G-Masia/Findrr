# Findrr: Initial Project Plan & Feasibility Evaluation

- **Document Version:** 1.0.0
- **Status:** Presented for Review (Bootstrap Gate 2)
- **Author:** Senior Software Engineer / Technical Architect / ML Engineer (Findrr AI Pair)
- **Project Owner:** Lebogang Masia
- **Last Updated:** 2026-11-02

---

## 1. Executive Summary & Purpose

Findrr is an employment-search and application-preparation application designed to help job seekers discover relevant employment opportunities, evaluate job-posting suitability, and prepare tailored, high-integrity CVs and cover letters.

The purpose of this document is to evaluate the feasibility of building Findrr across technical, operational, financial, and machine learning dimensions, establishing project boundaries, resource allocations, risk mitigations, and the high-level roadmap.

---

## 2. Project Scope & Boundaries

### 2.1 In-Scope Deliverables by Milestone

Findrr follows an iterative, milestone-driven lifecycle across five sequential phases:

- **Milestone 1: CLI Core Application Baseline**
  - Structured User Profile collection, onboarding questionnaires, document parsing (CV/resume upload, LinkedIn/GitHub profile URLs where permitted).
  - Generalised job title synthesis representing professional suitability.
  - ML-assisted alternative search-term generation and dual-encoder semantic validation.
  - Automated headful Selenium search engine queries (Google Search baseline), configurable result processing (2–10 postings per title), deduplication, and employer-authorised application link prioritization.
  - Basic application material preparation (plain text / basic structured output).
  - Purely local execution on the host laptop (Intel i5-1235U, 7.4 GiB RAM).
  
- **Milestone 2: Enhanced CLI Functionality & Tracking**
  - Multi-profile management, advanced search filtering, and enhanced job-posting deduplication.
  - Application lifecycle management (Discovered, Saved, Applied, Interviewing, Offered, Rejected).
  - Tailored CV and cover letter document export (PDF / DOCX) without fabrication.
  - Employer background research and interview preparation summaries.
  - Logging, telemetry, and error recovery enhancements.

- **Milestone 3: Desktop Web & Mobile UI (Simulated Backends)**
  - Penpot-designed and approved user interfaces:
    1. Desktop web interface.
    2. Mobile responsive interface.
  - Fully functional simulated interactions (mock APIs, reactive loading/empty/error states, form validation, client-side persistence).
  - Architecture decoupling frontend presentation from future backend services.

- **Milestone 4: Server Integration & Production Hardening**
  - Backend API integration connecting desktop and mobile frontends to the application server provided by the user.
  - Deployment of verified model artifacts and server-side inference configuration.
  - Performance optimization, caching, and robust network error recovery.

- **Milestone 5: Continuous Refinement & Optimization**
  - Performance profiling, bug fixes, model evaluation against real-world feedback, Kaggle retraining iterations, and security hardening.

### 2.2 Strict Out-of-Scope Boundaries (Project Invariants)

To ensure legal compliance, data integrity, and operational safety:
- **No Automated Application Submission:** Discovered is not applied. The system prepares materials; the user manually reviews, approves, and submits every application.
- **No Bypassing Access Restrictions:** Never bypass CAPTCHAs, bot detections, or paywalls. Prefer official APIs, respect robots.txt and site terms, and run Selenium headful by default.
- **Zero Fabrication Invariant:** Never fabricate qualifications, experiences, achievements, metrics, company details, or posting data. Missing information must be reported as gaps.
- **Strict Environment Separation:** Model training/fine-tuning occurs **only** in Kaggle notebooks executed manually by the user. Runtime inference occurs **only** on the Findrr host. No runtime training.
- **No Unapproved Third-Party Hosted Inference APIs:** All inference in Milestones 1–3 must execute locally on the host CPU.

---

## 3. Feasibility Analysis

### 3.1 Technical Feasibility

| Dimension | Evaluation | Feasibility Assessment |
|---|---|---|
| **Programming Language & Core Stack** | Python 3.11+ (Host runs Python 3.14.8 on Arch Linux). Standard packaging via `pyproject.toml`, Pydantic for validation, and SQLite for structured relational data. | **High Feasibility.** Python is the industry standard for combining web automation, document generation, and local ML inference runtimes (ONNX / PyTorch). |
| **Search & Web Automation** | Headful Selenium automation querying search engines and scraping public job boards/employer career pages. | **Medium-High Feasibility.** Rate limiting, dynamic DOM rendering, and anti-bot measures require robust delay jittering, DOM wait abstractions, and fallback parsing. Explicit adherence to non-bypass policies reduces blocking risks. |
| **Document Generation** | Extracting data from PDF/DOCX and rendering tailored templates using libraries like `python-docx` and `reportlab` / `weasyprint`. | **High Feasibility.** Templating engines (e.g. Jinja2) allow dynamic structure generation with strict data constraints preventing hallucinated content. |
| **Local Inference Runtime** | Running transformer models locally on a 12th Gen Intel Core i5-1235U with 7.4 GiB RAM. | **Feasible with Constraints.** Requires compact model architectures (< 500 MB footprint, e.g. quantized ONNX / INT8 or models under 1B parameters) to prevent out-of-memory thrashing on host CPU. |

### 3.2 Operational Feasibility

- **Solo Developer Operations:** The project is owned and driven by a single developer (Lebogang Masia) paired with the AI assistant. Workflows must remain lean, reproducible, and verifiable without requiring multi-party review bottlenecks.
- **Data Privacy & User Control:** All personal profile data and discovered job postings reside locally in SQLite on the user's workstation for Milestones 1–3. Zero leakage of personal data to external APIs.
- **Maintainability & Traceability:** Requirements trace strictly from SRS to architecture, code, tests, and Kaggle notebooks via stable requirement IDs (`FR-`, `NFR-`, `BR-`, `ML-`, `AC-`).

### 3.3 Financial Feasibility

- **Development Infrastructure:** Free tier GitHub repository, local Arch Linux developer workstation, GitHub Actions CI (free tier public/private minutes).
- **ML Training Infrastructure:** Kaggle provides 30 hours/week of free GPU (NVIDIA T4 / P100) and CPU compute, satisfying all model training and fine-tuning needs with zero capital expenditure.
- **Inference Infrastructure:** Zero cloud compute costs for Milestones 1–3 by running local CPU inference on existing hardware.
- **Overall Assessment:** The project is financially viable with **$0.00** operational expense during Milestones 1–3.

---

## 4. Machine Learning Feasibility Assessment

### 4.1 Required Machine Learning Capabilities

1. **Job Title Expansion & Search Term Generation (Module 3):**
   - *Task:* Given a user's generalised job title (e.g. "Software Developer") and profile summary, generate domain-consistent alternative titles (e.g. "Backend Engineer", "Python Developer", "Full Stack Engineer").
   - *Model Type:* Sequence-to-sequence or small instruction-tuned generative transformer.

2. **Semantic Similarity & Relevance Validation (Module 3 & Module 4):**
   - *Task:* Calculate semantic cosine similarity between generated titles and the user's primary profile suitability, filtering out irrelevant suggestions and duplicate search postings.
   - *Model Type:* Dual-encoder bi-encoder (Sentence Transformer).

3. **Tailored Application Content Alignment (Module 5):**
   - *Task:* Map job description requirements to user profile experiences and draft aligned bullet points without fabricating claims.
   - *Model Type:* Generative prompt-guided transformer or rule-augmented template hybrid.

### 4.2 Training Datasets

- **Availability:** Public taxonomies (O*NET 28.0+, European ESCO occupational classification), Kaggle Job Posting datasets, and Hugging Face public career datasets.
- **Privacy:** In compliance with project rules, **zero real user personal data** will be incorporated into training sets. Synthetic profile variations and anonymized public job postings will be used exclusively.
- **Data Management:** All dataset processing scripts and training manifests will be documented in `docs/ml/` and exported as Kaggle dataset inputs.

### 4.3 Kaggle Training Workflow Feasibility

- **Notebook Structure:** Modular Kaggle notebooks designed with fixed random seeds (`seed=42`), deterministic data loaders, and automated evaluation logging.
- **User Execution:** The user runs the notebook manually on Kaggle using free GPU accelerators (T4 or P100).
- **Artifact Export Package:** Every notebook must export:
  1. Serialized model weights (`model.safetensors` or `model.onnx`).
  2. Tokenizer configuration (`tokenizer.json`, `vocab.txt`, `tokenizer_config.json`).
  3. Pre/post-processing configurations and label mappings (`config.json`).
  4. Cryptographic integrity manifest (`manifest.json` with SHA-256 checksums).
- **Local Verification:** Downloaded artifacts are validated against the manifest before the application server accepts them.

### 4.4 Compute Constraints & Runtime Feasibility

| Constraint | Host Specification | ML Design Implication |
|---|---|---|
| **CPU** | 12th Gen Intel Core i5-1235U (10 cores: 2 P-cores, 8 E-cores, 12 threads) | Multi-threaded ONNX Runtime or PyTorch CPU inference with intra-op parallelism capped at 4 threads to prevent freezing host UI. |
| **RAM** | 7.4 GiB Total (~3.6 GiB Available during active development) | Maximum combined active model memory footprint must not exceed **1.0 GiB**. |
| **Storage** | Local NVMe SSD | Model artifacts must be under **500 MB** total download size per model. |
| **GPU** | Integrated Intel Iris Xe (no dedicated NVIDIA GPU) | No CUDA dependencies allowed in server inference dependencies. Inference runs on standard x86_64 CPU instructions (AVX2/VNNI). |

### 4.5 Candidate Model Architectures

1. **Semantic Similarity Dual-Encoder:**
   - *Candidate:* `all-MiniLM-L6-v2` or `paraphrase-MiniLM-L3-v2`.
   - *Size:* ~80 MB–120 MB.
   - *Latency:* ~15–30 ms per pair on Intel i5 CPU.
   - *Feasibility:* **Exceptional.** Easily fine-tunable on Kaggle; sub-second inference on host CPU.

2. **Search Term Generative Expander:**
   - *Candidate:* Fine-tuned `google/flan-t5-small` (80M parameters, ~300 MB) or quantized `google/flan-t5-base` (250M parameters, INT8 ~250 MB).
   - *Latency:* ~300–800 ms per generation sequence on host CPU.
   - *Feasibility:* **High.** Flan-T5 architectures run reliably on CPU without specialized acceleration.

3. **CV & Cover Letter Synthesis:**
   - *Approach:* Hybrid deterministic template engine (Jinja2) paired with an extractive transformer or small generative model (e.g., quantized Flan-T5 or Qwen2.5-0.5B-Instruct in ONNX format).
   - *Feasibility:* **High.** Rule-guided templating guarantees the "Zero Fabrication" invariant while the model assists in phrasing and vocabulary alignment.

### 4.6 Cross-Dependencies

- CLI Module 1 (Profile) must stabilize its JSON schema before Module 3 (Search Terms) and Module 5 (CV Tailoring) can lock their input representations.
- Model specifications and evaluation criteria must be formally approved before Kaggle training notebooks are drafted.
- Model artifacts must be supplied and integrity-verified before real inference testing replaces initial test fixtures/mocks.

---

## 5. Resources, Roles & Tooling Stack

### 5.1 Project Roles & Responsibilities

- **Project Owner & Sole Developer:** Lebogang Masia
  - Direction, requirements approval, pull request merges, Kaggle notebook manual execution, artifact provisioning.
- **AI Pair Engineer & Architect:** Antigravity (DeepMind Advanced Agentic Assistant)
  - Formal SDLC execution, architecture specification, test-driven implementation on branches, PR preparation, Kaggle notebook authoring.

### 5.2 Technology Stack

- **Backend & Core:** Python 3.11+, Pydantic v2, SQLite3, SQLAlchemy/SQLModel (evaluated in Milestone 1).
- **Search & Scraping:** Selenium WebDriver (headful mode), BeautifulSoup4, Requests.
- **ML & Inference:** Hugging Face Transformers, Sentence-Transformers, ONNX Runtime, Safetensors.
- **Testing & QA:** Pytest, Pytest-Cov, Unittest.
- **Code Quality & Guardrails:** Ruff, Gitleaks, custom file-size validators (< 5MB git limit).
- **Design:** Penpot MCP (for Milestone 3 Web & Mobile UI designs).

---

## 6. Risk Assessment & Mitigation Strategies

| Risk ID | Risk Description | Severity | Likelihood | Mitigation Strategy |
|---|---|---|---|---|
| **RSK-01** | **Search Engine / Board Bot Detection**<br>Google Search or job portals block Selenium during discovery. | High | Medium | Enforce headful Selenium by default, human-like interaction delays (jitter), randomized user agents, and abstract search providers so DuckDuckGo or direct board search can be substituted. |
| **RSK-02** | **Host Memory Exhaustion (OOM)**<br>Local inference exceeds available 7.4 GiB host RAM. | High | Medium | Strict model size limits (< 500 MB), INT8 / ONNX quantization, explicit model unloading / caching policies, and CPU thread limits. |
| **RSK-03** | **Hallucination in Generated Documents**<br>Generative models invent fake achievements or skills. | Critical | Low | Strict architectural separation: Use models only for phrasing/selection; assemble final CVs/cover letters exclusively from verified User Profile facts using deterministic templating. Report missing data as gaps. |
| **RSK-04** | **Kaggle Notebook Reproducibility Drift**<br>Kaggle environment changes produce non-reproducible artifacts. | Medium | Low | Pin exact pip package versions in notebook setup cells, record environment fingerprints, fix random seeds, and validate output checksums against the manifest. |
| **RSK-05** | **Private Repo Branch Protection Constraints**<br>GitHub Free tier blocks branch protection on private repos. | Low | High | Enforce branch and PR discipline via tooling/agent rules; solo developer self-review and required CI runs ensure main remains pristine. |
| **RSK-06** | **Penpot MCP Disconnection**<br>Penpot MCP plugin unavailable for UI design. | Medium | Medium | Flagged as blocker for Milestone 3/Bootstrap Step 5; CLI core (Milestone 1–2) can proceed unimpeded while connection is finalized. |

---

## 7. Project Governance & Definition of Done

Findrr strictly adheres to:
1. **Branch Protection & Review:** Work occurs exclusively on feature/fix/docs branches; only the user merges PRs into `main`.
2. **Synchronized Documentation:** No PR is approved without corresponding updates to requirements, architecture, or test docs.
3. **Verified ML Status:** Explicit differentiation in PRs between `MOCK` fixtures and `Verified with Real Artifacts`.
4. **Approval Gates:** Progression between roadmap milestones and bootstrap phases requires explicit user sign-off.
