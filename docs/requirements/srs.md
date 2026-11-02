# Software Requirements Specification (SRS) for Findrr

- **Document Version:** 1.0.0
- **Status:** Presented for Review (Bootstrap Gate 3)
- **Author:** Senior Software Engineer / Technical Architect / ML Engineer (Findrr AI Pair)
- **Project Owner:** Lebogang Masia
- **Last Updated:** 2026-11-02

---

## 1. Introduction and Project Purpose

Findrr is an employment-search and application-preparation platform designed to assist job seekers in discovering suitable employment opportunities, evaluating job suitability, and generating high-integrity, customized application materials (CVs, cover letters, and employer research briefs).

The primary purpose of Findrr is to empower users with an automated, privacy-first, and transparent job-search copilot that extracts and normalizes the user's professional background into a unified User Profile, synthesizes an objective generalized job title, discovers opportunities via search engine automation, and organizes end-to-end application tracking without fabricating personal qualifications or job information.

---

## 2. Scope and Objectives

### 2.1 Scope of the System
The system encompasses:
- Onboarding, multi-source ingestion (questionnaire, resume parsing, professional URLs), and structured User Profile management.
- Objective synthesis of a primary generalized job title.
- Generative expansion of search terms and bi-encoder semantic similarity scoring.
- Automated web discovery via headful Selenium, parsing public job postings, and extracting employer-authorized application destinations.
- Context-tailored document generation (plain text, PDF, DOCX) strictly bound to user-verified facts.
- Application progress tracking (Discovered, Saved, Applied, Interviewing, Offered, Rejected).
- Local, verified model artifact loading, schema validation, and CPU-efficient inference (Module 9).

### 2.2 System Invariants (Strict Non-Negotiable Boundaries)
- **Zero Fabrication Invariant:** Never fabricate qualifications, experiences, achievements, metrics, company details, or posting data. Missing information must be reported as gaps.
- **Human-in-the-Loop Submission:** Discovered is not applied. The system automates discovery and drafting; the user explicitly reviews, confirms, and submits all job applications.
- **Access Restriction Respect:** Never bypass CAPTCHAs, bot protection, or authentication controls. Prefer authorized APIs and respect site terms.
- **Environment Decoupling:** Model training and fine-tuning execute exclusively in user-run Kaggle notebooks. Application inference executes on the Findrr host. No runtime training.
- **Local Data Privacy:** All personal professional data and credentials reside on the user's local machine for Milestones 1–3.

---

## 3. Intended Users and User Characteristics

| User Persona | Characteristics & Experience | Primary Use Case in Findrr |
|---|---|---|
| **Recent Graduate** | Limited formal industry experience; academic coursework, capstone projects, internships. | Discovering entry-level roles matching educational qualifications; tailoring resumes to highlight transferable skills. |
| **Experienced Professional** | Multiple years in industry, clear track record, targeted compensation and seniority preferences. | Rapid discovery across niche senior titles; managing multiple simultaneous applications. |
| **Career Changer** | Transitioning across disciplines; possesses transferable skills requiring nuanced semantic matching. | Discovering bridge titles; tailoring resumes to emphasize skills alignment over job-title history. |

---

## 4. Product Overview

Findrr operates as a multi-stage data processing and inference pipeline:
1. **Profile Ingestion & Synthesis:** Ingests user input -> Normalizes profile data -> Synthesizes Generalized Job Title (Module 1 & 2).
2. **Search Term Expansion & Validation:** Generates alternative titles via Model 1 -> Evaluates semantic similarity via Model 2 -> Enforces deduplication thresholds (Module 3 & 9).
3. **Automated Search & Scraping:** Headful Selenium executes Google Search -> Extracts 2–10 search results -> Parses posting content and resolves direct employer links (Module 4).
4. **Tailored Application Prep:** Matches posting requirements to verified profile facts -> Synthesizes tailored CV & cover letter drafts via Model 3 & Jinja2 templates (Module 5).
5. **Application Lifecycle Tracking:** Logs application progress and provides dashboard metrics (Module 6 & 7).

---

## 5. System Context

Findrr interacts with the following external actors and boundary systems:
- **User:** Interacts via CLI (Milestones 1–2) or Web/Mobile UI (Milestones 3–5).
- **Search Engines & Job Boards:** Google Search, public employer career portals, and ATS endpoints accessed via Selenium WebDriver.
- **Kaggle Platform:** External manual training environment providing GPU compute for model training; exports `.safetensors`/ONNX artifacts and manifests.
- **Local Storage:** SQLite relational database storing normalized profiles, search configurations, postings, and application statuses.
- **Local Filesystem:** Secure storage for model artifacts, CV exports, and run logs.

---

## 6. Functional Requirements

### Module 1: Onboarding and User Profile Management
- **FR-001:** The system shall collect user professional information via interactive CLI prompts, structured questionnaire imports, and uploaded documents (PDF/DOCX).
- **FR-002:** The system shall normalize extracted profile information into standard schema categories: Personal Info, Professional Summary, Education, Work Experience, Skills, Certifications, Projects, and Employment Preferences.
- **FR-003:** The system shall maintain provenance metadata for every profile entry (source, collection date, verification status).
- **FR-004:** The system shall allow the user to review, edit, flag, and explicitly verify all extracted information before it is saved.
- **FR-005:** The system shall synthesize a primary Generalized Job Title reflecting the user's overall professional suitability, providing explanatory rationale and supporting skills.

### Module 2: Search Configuration Management
- **FR-006:** The system shall manage search parameters including target locations, remote/hybrid preferences, experience levels, and minimum compensation filters.
- **FR-007:** The system shall allow users to customize search result limits per title within the allowed range of 2 to 10 postings.

### Module 3: Key Search Term Generation & Validation
- **FR-008:** The system shall generate domain-relevant alternative job titles from the user's generalized job title using a generative transformer model (Model 1).
- **FR-009:** The system shall score the semantic similarity of each generated title against the primary generalized title using a dual-encoder model (Model 2).
- **FR-010:** The system shall reject generated titles with semantic similarity below the configured relevance threshold (provisional default: 0.70).
- **FR-011:** The system shall detect and filter out exact and near-duplicate job titles using string normalization and bi-encoder embedding similarity (provisional threshold: 0.88).

### Module 4: Job Posting Discovery & Scraping
- **FR-012:** The system shall automate search queries using Selenium WebDriver in headful mode by default.
- **FR-013:** The system shall extract between 2 and 10 job search results per accepted job title.
- **FR-014:** The system shall resolve and prioritize employer-authorized application destinations (career portals, ATS) over third-party aggregators.
- **FR-015:** The system shall extract structured posting fields: Job Title, Company Name, Location, Description, Required Qualifications, Application URL, and Posting Date.
- **FR-016:** The system shall detect duplicate job postings using company name, normalized title, and content hashing.
- **FR-017:** If fewer than 2 relevant postings are available, the system shall record only available results without fabricating synthetic entries.

### Module 5: Application Preparation
- **FR-018:** The system shall extract key qualification keywords and responsibilities from a selected job description.
- **FR-019:** The system shall map posting requirements to verified profile facts, highlighting matching skills and identifying missing prerequisites.
- **FR-020:** The system shall generate tailored CV documents (PDF/DOCX) using deterministic templates and model-assisted phrasing strictly derived from verified user data.
- **FR-021:** The system shall generate job-specific cover letters integrating company context and verified candidate achievements without fabricating information.
- **FR-022:** The system shall compile company research summaries (industry, mission, technologies) with source attribution.

### Module 6 & 7: Application Management & Dashboard
- **FR-023:** The system shall track application status transitions: Discovered -> Saved -> Applied -> Interviewing -> Offered -> Rejected -> Withdrawn.
- **FR-024:** The system shall record application submission dates, contact details, notes, and links to generated document versions.
- **FR-025:** The system shall provide summary metrics: total postings discovered, active applications, interview rates, and search term effectiveness.

### Module 9: Model Management & Inference Service
- **FR-026:** The system shall load model weights, tokenizers, configurations, and label mappings from a local directory.
- **FR-027:** The system shall verify the cryptographic SHA-256 checksum of every model artifact against the model registry manifest before loading.
- **FR-028:** The system shall fail gracefully with structured diagnostic logging if an artifact is missing, corrupted, or incompatible, preventing fallback to fabricated predictions.
- **FR-029:** The system shall provide a unified inference service interface for title expansion and semantic scoring across application modules.
- **FR-030:** The system shall manage model memory lifecycles, supporting explicit unloading and cache management to respect host RAM limits.

---

## 7. Non-Functional Requirements

### 7.1 Performance & Resource Efficiency
- **NFR-001 (Host Memory Footprint):** Total active memory consumed by loaded machine learning models and inference runtimes shall not exceed **1.0 GiB** on the host.
- **NFR-002 (Inference Latency):** Dual-encoder semantic similarity scoring shall execute in under **50 ms** per pair on the host CPU. Generative title expansion shall complete within **1,500 ms** per request.
- **NFR-003 (Automation Rate Limiting):** Selenium search requests shall enforce randomized polite delays (jitter between 2.0 and 5.0 seconds) to prevent triggering anti-bot protections.

### 7.2 Security & Data Privacy
- **NFR-004 (Zero Credential Leakage):** No credentials, API tokens, session cookies, or personal identities shall be written to git repositories or unencrypted log files.
- **NFR-005 (Local Data Encryption):** Local SQLite databases and profile documents shall be stored within the user's private workspace permissions.
- **NFR-006 (Untrusted Web Input Sanitization):** All scraped HTML content, external job descriptions, and user-provided URLs shall be treated as untrusted and sanitized against prompt injection and malicious markup.

### 7.3 Reliability & Availability
- **NFR-007 (Network Resilience):** Web discovery and scraping operations shall handle network timeouts, HTTP 429/503 errors, and DOM navigation failures gracefully with exponential backoff and structured error logs.
- **NFR-008 (Model Integrity Verification):** The application shall reject any model artifact whose computed SHA-256 hash does not match `manifest.json`.
- **NFR-009 (Zero Hallucination Invariant):** Tailored CVs and cover letters shall contain zero factual claims absent from the user-verified profile.

### 7.4 Maintainability & Extensibility
- **NFR-010 (Modular Search Architecture):** Search provider implementations shall adhere to an abstract search interface, allowing alternate providers (e.g. DuckDuckGo, direct ATS APIs) to be substituted without modifying core logic.
- **NFR-011 (Traceability):** 100% of functional requirements and user stories shall be traceable to implementation modules, automated tests, and verification artifacts.

---

## 8. Use Cases and User Workflows

### UC-01: User Onboarding and Profile Creation
1. User starts Findrr onboarding in CLI.
2. User provides professional background (manual prompt or CV upload).
3. System extracts, normalizes, and presents profile categories for user review.
4. User confirms or amends entries.
5. System synthesizes primary Generalized Job Title with supporting justification.
6. User approves profile and title.

### UC-02: Job Discovery and Posting Extraction
1. User initiates search workflow for approved Generalized Job Title.
2. System expands alternative search terms (Model 1) and validates similarity (Model 2).
3. User selects validated titles to search.
4. System launches headful Selenium, executes search, and scrapes 2–10 postings per title.
5. System resolves direct employer links, filters duplicates, and stores postings in SQLite.
6. System displays discovered postings in CLI summary table.

### UC-03: Tailored Application Preparation
1. User selects a discovered job posting.
2. System extracts job requirements and compares against User Profile.
3. System identifies matching qualifications and flags any missing prerequisites.
4. System generates tailored CV and cover letter draft.
5. User reviews, edits, and exports document (PDF/DOCX).
6. System updates posting status to "Saved" or "Applied" upon user confirmation.

---

## 9. User Stories

- **US-001 (Profile Intake):** As a job seeker, I want to import or enter my professional qualifications so that Findrr maintains a comprehensive profile of my skills and experience.
- **US-002 (Objective Title Synthesis):** As a job seeker, I want Findrr to identify an objective generalized job title so that my job search is grounded in market-aligned roles.
- **US-003 (Search Expansion):** As a job seeker, I want Findrr to generate semantically relevant alternative job titles so that I discover postings using varying industry terminologies.
- **US-004 (Relevance Filtering):** As a job seeker, I want generated titles to be validated against semantic thresholds so that irrelevant search avenues are filtered out automatically.
- **US-005 (Automated Search):** As a job seeker, I want Findrr to search for open positions via Selenium and retrieve direct employer application links so that I avoid low-quality aggregator traps.
- **US-006 (Zero-Fabrication Tailoring):** As a job seeker, I want tailored CVs and cover letters generated from my verified profile facts so that my applications are targeted without inventing false credentials.
- **US-007 (Application Pipeline):** As a job seeker, I want to track the status of my applications from discovery through interview so that my employment search is organized.
- **US-008 (Model Integrity):** As a system operator, I want model artifacts verified via cryptographic checksums so that corrupted or tampered models are rejected prior to execution.

---

## 10. Acceptance Criteria

### AC-001 (verifies FR-001, FR-002, FR-004)
- **Given** a user provides a CV file or answers onboarding prompts,
- **When** the profile extraction pipeline executes,
- **Then** the extracted data is structured into normalized categories, presented to the user for confirmation, and saved only after user approval.

### AC-002 (verifies FR-005)
- **Given** an approved User Profile,
- **When** the generalized title synthesis executes,
- **Then** it produces a primary job title, an explanatory rationale, and a list of supporting qualifications.

### AC-003 (verifies FR-008, FR-009, FR-010)
- **Given** an approved Generalized Job Title,
- **When** Model 1 generates candidate alternative titles,
- **Then** Model 2 computes cosine similarity for each candidate, and any candidate scoring below 0.70 is rejected.

### AC-004 (verifies FR-012, FR-013, FR-014, FR-017)
- **Given** an accepted job title and search preferences,
- **When** Selenium executes the search in headful mode,
- **Then** between 2 and 10 results per title are extracted, employer-authorized links are prioritized, and actual counts are recorded without fabricating results.

### AC-005 (verifies FR-020, FR-021, NFR-009)
- **Given** a verified User Profile and a target job posting,
- **When** a tailored CV and cover letter are generated,
- **Then** 100% of skills, experiences, and qualifications in the generated output map directly to verified profile entries, with zero fabricated claims.

### AC-006 (verifies FR-026, FR-027, FR-028, NFR-008)
- **Given** a model artifact directory and manifest,
- **When** the inference service loads the model,
- **Then** it validates the SHA-256 checksum against `manifest.json`; if a mismatch occurs, it raises an explicit error and logs diagnostic details without serving predictions.

---

## 11. Business Rules

- **BR-001 (User Submission Authority):** Under no circumstances shall Findrr automatically submit an application on a user's behalf.
- **BR-002 (Factual Grounding):** No generated CV, resume summary, or cover letter may contain claims, credentials, or metrics absent from the user-verified profile.
- **BR-003 (Search Bounds):** Search result processing per job title is strictly bounded between 2 and 10 postings. Never synthesize postings if fewer than 2 exist.
- **BR-004 (Ethical Automation):** Web scraping must operate headful by default, introduce randomized human delay jitter, and respect robots.txt and site terms.
- **BR-005 (Model Training Isolation):** No model training or fine-tuning shall occur on the local application host or at runtime. All training occurs via user-executed Kaggle notebooks.
- **BR-006 (Provisional Thresholds):** All numerical thresholds (similarity thresholds, limit bounds) must be declared provisional until empirically evaluated.

---

## 12. Data Requirements

### 12.1 Core Relational Entities
- `UserProfile`: User ID, contact info, professional summary, metadata, verification timestamps.
- `ProfileEntry`: Foreign key to UserProfile, category (Education, Experience, Skill, Project), provenance source, verified flag.
- `GeneralizedTitle`: Foreign key to UserProfile, primary title, justification, alternative titles, creation date.
- `SearchTerm`: Alternative title, source title ID, semantic similarity score, acceptance status (Accepted, Rejected, Duplicate).
- `JobPosting`: Posting ID, source URL, resolved employer URL, title, company, location, description text, extracted requirements, date discovered.
- `ApplicationRecord`: Posting ID, profile snapshot ID, current status, date applied, generated CV path, generated cover letter path, notes.

### 12.2 Data Integrity & Provenance
Every piece of profile data tracks:
- `source`: User input, resume file upload, LinkedIn URL, GitHub URL.
- `collection_date`: ISO-8601 timestamp.
- `verification_status`: Unverified (extracted) vs. Verified (user-confirmed).

---

## 13. Interface Requirements

- **CLI Interface (Milestones 1–2):** Interactive command-line interface built with standard terminal UX (clear tables, progress spinners, color-coded status tags, confirmation dialogs).
- **Desktop Web Interface (Milestone 3+):** Responsive web layout designed and approved in Penpot, featuring dashboard views, profile editors, posting cards, and document previewers.
- **Mobile Web Interface (Milestone 3+):** Touch-friendly responsive mobile layout designed and approved in Penpot.

---

## 14. Integration Requirements

- **Search Engine Providers:** Abstract WebDriver integration supporting headful Google Search automation.
- **Document Exporters:** Python PDF and DOCX generation engines (`reportlab`, `python-docx`).
- **Kaggle Notebook Artifact Transfer:** File-based transfer importing model weights (`.safetensors`/ONNX), tokenizers, and `manifest.json`.

---

## 15. Security and Privacy Requirements

- **Local Storage Isolation:** All user databases, extracted profile records, and generated documents remain local to the host system.
- **Secret Scanning:** Git pre-commit hooks and CI pipelines strictly reject any commits containing API keys, private keys, or credentials.
- **Sanitization:** Scraped HTML from external job boards is stripped of script tags, tracking pixels, and malicious payloads before parsing.

---

## 16. Machine Learning Requirements

### ML-001: Job Title Expander Model (Module 3)
- **Model Purpose:** Generate relevant alternative job titles from a generalized title and profile summary.
- **Model Architecture:** Sequence-to-sequence transformer (e.g. `google/flan-t5-small` or quantized `flan-t5-base`).
- **Inputs:** JSON string `{"title": str, "skills": list[str]}`.
- **Outputs:** List of candidate job title strings `list[str]`.
- **Training Approach:** Parameter-efficient fine-tuning (LoRA) or full fine-tuning on Kaggle using occupational title taxonomies (O*NET/ESCO).
- **Evaluation Criteria:** Rouge-L, BLEU, and domain taxonomy coverage >= 0.80.
- **Artifact Format:** `model.safetensors` or ONNX, tokenizer configs, `manifest.json` (< 350 MB).

### ML-002: Dual-Encoder Semantic Similarity Evaluator (Module 3 & 4)
- **Model Purpose:** Compute dense semantic embeddings and cosine similarity between job titles and posting texts.
- **Model Architecture:** Bi-encoder Sentence Transformer (e.g. `all-MiniLM-L6-v2`).
- **Inputs:** Text pair `(text_a: str, text_b: str)`.
- **Outputs:** Float cosine similarity score `[-1.0, 1.0]`.
- **Training Approach:** Contrastive fine-tuning on Kaggle with paired title synonyms and negative hard pairs.
- **Evaluation Criteria:** Cosine Pearson correlation >= 0.85 on test validation pairs.
- **Artifact Format:** ONNX / PyTorch CPU model (< 100 MB).

### ML-003: Tailored Application Content Assistant (Module 5)
- **Model Purpose:** Assist in drafting aligned bullet points and cover letter sentences matching job requirements to verified user facts.
- **Model Architecture:** Small instruction-tuned generative model (e.g. `Qwen2.5-0.5B-Instruct` ONNX or Flan-T5) constrained by strict template schemas.
- **Evaluation Criteria:** Factual consistency check (100% precision on named entities mapping to profile).
- **Artifact Format:** Quantized INT8 ONNX (< 450 MB).

---

## 17. Model Inference Requirements

- **Unified Registry:** All models must be cataloged in `docs/ml/model-registry.md` with associated SHA-256 checksums, version tags, and input/output contracts.
- **Cold-Start Validation:** The inference service shall verify model integrity and dependencies at startup before advertising readiness.
- **Fallback Behavior:** If a model fails to load or inference fails, the system returns an explicit error log and disables dependent features; it shall **never** return mocked or fabricated predictions in production mode.

---

## 18. System Constraints

- **Host Hardware:** 12th Gen Intel Core i5-1235U, 7.4 GiB RAM, integrated graphics, Arch Linux x86_64.
- **Network Access:** Required only for Selenium web scraping and GitHub version control.
- **Git Repository Size:** Binary model weights, datasets, and large files (> 5 MB) are strictly forbidden from git tracking.

---

## 19. Assumptions and Dependencies

- The user maintains access to a Kaggle account to manually execute training notebooks.
- Web search engines remain accessible via standard browser automation without CAPTCHAs under polite request throttling.
- External job sites maintain parseable DOM structures for title, company, and description.

---

## 20. Known Limitations

- Real-time job board scraping is subject to structural DOM changes on third-party sites, requiring adaptable selector heuristics.
- Local CPU inference on 7.4 GiB RAM limits simultaneous loaded models; models must be loaded on-demand or sequentialized.
- LinkedIn automated scraping is heavily restricted; user-provided text or exported data is prioritized over direct authenticated scraping.

---

## 21. Glossary

- **ATS:** Applicant Tracking System used by employers (e.g. Greenhouse, Lever, Workday).
- **Generalized Job Title:** Standardized occupational classification synthesized from user qualifications representing overall suitability.
- **Dual-Encoder:** Machine learning architecture that encodes two text sequences into dense vectors independently to compute cosine similarity.
- **Provenance:** The origin, extraction history, and verification state of an item of information.
- **Zero Fabrication:** The strict invariant that no application data or candidate claims may be invented or hallucinated.
