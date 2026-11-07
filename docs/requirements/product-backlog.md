# Findrr: Prioritized Product Backlog

- **Document Version:** 1.0.0
- **Status:** Presented for Review (Bootstrap Gate 3)
- **Author:** Senior Software Engineer / Technical Architect / ML Engineer (Findrr AI Pair)
- **Project Owner:** Lebogang Masia
- **Last Updated:** 2026-11-02

---

## 1. Backlog Overview and Prioritization Methodology

Work items are organized hierarchically:
- **Epics:** High-level system capabilities aligned with application modules and milestones.
- **User Stories (`US-xxx`):** Deliverable increments capturing user needs, linked directly to Functional Requirements (`FR-xxx`) and Acceptance Criteria (`AC-xxx`).
- **Implementation Tasks:** Concrete engineering activities for development iterations.

**Prioritization Scale:**
- **Must Have (M):** Mandatory baseline for the milestone to be considered viable.
- **Should Have (S):** Important feature that adds substantial value; can be deferred to a follow-up iteration within the milestone if time-constrained.
- **Could Have (C):** Desirable enhancement or optimization for later iterations.

---

## 2. Milestone 1 Backlog: CLI Core Application Baseline

### Epic 1: User Profile Ingestion & Generalized Title Synthesis (Module 1 & 2)

#### US-001: Interactive CLI Profile Questionnaire
- **Priority:** Must Have (M)
- **Target Milestone:** Milestone 1 (Iteration 1)
- **Addresses:** `FR-001`, `FR-002`, `FR-004`, `AC-001`
- **Description:** As a job seeker, I want to input my educational background, work experiences, skills, and employment preferences via an interactive CLI prompt so that Findrr constructs my initial profile.
- **Tasks:**
  - [x] Implement CLI interactive prompt loop with validation (Pydantic models).
  - [x] Implement SQLite schema and storage for `UserProfile` and `ProfileEntry`.
  - [x] Add verification confirmation step before committing profile to database.
- **Dependencies:** Core database schema setup.

#### US-002: Generalized Job Title Synthesis
- **Priority:** Must Have (M)
- **Target Milestone:** Milestone 1 (Iteration 1)
- **Addresses:** `FR-005`, `AC-002`
- **Description:** As a job seeker, I want the system to analyze my verified profile entries and synthesize an objective Generalized Job Title with supporting justification so that my job search targets market-aligned roles.
- **Tasks:**
  - [x] Implement rule-based profile analyzer extracting primary skills and domain clusters.
  - [x] Synthesize primary title, justification text, and supporting qualification tags.
  - [x] Store synthesized title in `GeneralizedTitle` table.
- **Dependencies:** `US-001`.

#### US-003: Search Configuration Setup
- **Priority:** Must Have (M)
- **Target Milestone:** Milestone 1 (Iteration 1)
- **Addresses:** `FR-006`, `FR-007`
- **Description:** As a job seeker, I want to configure target locations, remote/hybrid preferences, and search limit bounds (2–10) so that subsequent searches match my criteria.
- **Tasks:**
  - [x] Add search config prompt in CLI.
  - [x] Store configuration with provisional default bounds in SQLite.
- **Dependencies:** `US-001`.

---

### Epic 2: ML Model Management & Inference Service (Module 9)

#### US-004: Model Artifact Loading & SHA-256 Checksum Verification
- **Priority:** Must Have (M)
- **Target Milestone:** Milestone 1 (Iteration 2)
- **Addresses:** `FR-026`, `FR-027`, `FR-028`, `NFR-008`, `AC-006`
- **Description:** As a system operator, I want the inference service to load model artifacts from disk only after validating cryptographic checksums against `manifest.json` so that corrupted or unverified models are never executed.
- **Tasks:**
  - [x] Implement `ModelRegistry` reader and SHA-256 hash calculator.
  - [x] Implement strict loading gate raising structured errors upon checksum mismatch.
  - [x] Add explicit diagnostic logging for missing or corrupted artifacts.
- **Dependencies:** None.

#### US-005: Local Inference Engine Architecture
- **Priority:** Must Have (M)
- **Target Milestone:** Milestone 1 (Iteration 2)
- **Addresses:** `FR-029`, `FR-030`, `NFR-001`, `NFR-002`
- **Description:** As an application module, I want a unified inference service interface to request predictions without managing PyTorch/ONNX runtime lifecycles.
- **Tasks:**
  - [x] Implement `InferenceService` singleton with thread-capped CPU execution.
  - [x] Add model memory lifecycle management (lazy loading and explicit unloading).
  - [x] Implement test fixture harness distinguishing mock inference from verified models.
- **Dependencies:** `US-004`.

---

### Epic 3: Search Term Generation & Validation (Module 3)

#### US-006: Generative Search Term Expansion (Model 1)
- **Priority:** Must Have (M)
- **Target Milestone:** Milestone 1 (Iteration 2)
- **Addresses:** `FR-008`, `ML-001`, `AC-003`
- **Description:** As a job seeker, I want the system to generate alternative job titles using Model 1 so that my search covers varied industry terminology.
- **Tasks:**
  - [x] Define Model 1 specification (`docs/ml/models/title-expander.md`).
  - [x] Author Kaggle training notebook for fine-tuning Flan-T5 on O*NET taxonomies.
  - [x] Implement inference adapter invoking Model 1 via `InferenceService`.
- **Dependencies:** `US-002`, `US-005`.

#### US-007: Bi-Encoder Semantic Similarity Scoring (Model 2)
- **Priority:** Must Have (M)
- **Target Milestone:** Milestone 1 (Iteration 2)
- **Addresses:** `FR-009`, `FR-010`, `FR-011`, `ML-002`, `AC-003`
- **Description:** As a job seeker, I want candidate titles evaluated for semantic similarity and deduplicated using Model 2 so that only relevant and distinct titles are presented.
- **Tasks:**
  - [x] Define Model 2 specification (`docs/ml/models/similarity-evaluator.md`).
  - [x] Author Kaggle notebook for sentence-transformer fine-tuning and ONNX export.
  - [x] Implement cosine similarity evaluation and threshold filtering (provisional threshold: 0.70).
  - [x] Implement duplicate rejection (provisional threshold: 0.88).
- **Dependencies:** `US-005`, `US-006`.

---

### Epic 4: Automated Job Posting Discovery & Extraction (Module 4)

#### US-008: Headful Selenium Search Automation
- **Priority:** Must Have (M)
- **Target Milestone:** Milestone 1 (Iteration 3)
- **Addresses:** `FR-012`, `FR-013`, `NFR-003`, `BR-004`, `AC-004`
- **Description:** As a job seeker, I want the system to run automated Google Search queries for accepted titles in headful mode with polite throttling so that search engines are queried without anti-bot blocks.
- **Tasks:**
  - [x] Configure headful Selenium WebDriver with random delay jitter (2.0–5.0s).
  - [x] Implement search query builder combining title and location preferences.
  - [x] Extract 2 to 10 search results per title, recording actual retrieved counts.
- **Dependencies:** `US-003`, `US-007`.

#### US-009: Job Posting Content Extraction & Employer Link Resolution
- **Priority:** Must Have (M)
- **Target Milestone:** Milestone 1 (Iteration 3)
- **Addresses:** `FR-014`, `FR-015`, `FR-016`, `FR-017`, `AC-004`
- **Description:** As a job seeker, I want job posting details extracted and employer-authorized application links prioritized so that I can apply directly rather than through third-party boards.
- **Tasks:**
  - [x] Implement HTML parser extracting Title, Company, Location, Description, and Link.
  - [x] Add destination link resolver prioritizing direct ATS/company URLs over boards.
  - [x] Implement deduplication filter using title and company content hashing.
  - [x] Store extracted postings in `JobPosting` table.
- **Dependencies:** `US-008`.

---

### Epic 5: Baseline Application Preparation (Module 5)

#### US-010: Job Requirement Keyword Analysis
- **Priority:** Must Have (M)
- **Target Milestone:** Milestone 1 (Iteration 4)
- **Addresses:** `FR-018`, `FR-019`
- **Description:** As a job seeker, I want the system to compare a job description against my profile, identifying matching skills and surfacing missing prerequisites.
- **Tasks:**
  - [x] Implement keyword and skill extraction from posting text.
  - [x] Map extracted requirements to verified `UserProfile` skills and experiences.
  - [x] Generate structured gap analysis table in CLI (`findrr apply analyze`).
- **Dependencies:** `US-001`, `US-009`.

#### US-011: Basic Tailored Application Draft Generation
- **Priority:** Must Have (M)
- **Target Milestone:** Milestone 1 (Iteration 4)
- **Addresses:** `FR-020`, `NFR-009`, `BR-002`, `AC-005`
- **Description:** As a job seeker, I want a tailored CV summary and cover letter text generated strictly from my verified profile facts without fabrication.
- **Tasks:**
  - [x] Implement deterministic plain-text templating engine strictly bound to verified profile data.
  - [x] Enforce zero-fabrication validation check verifying all generated claims exist in profile (`FactGroundingValidator`).
  - [x] Save draft text to local storage (`findrr apply draft`, `findrr apply list`, `findrr apply show`).
- **Dependencies:** `US-010`.

---

## 3. Milestone 2 Backlog: Additional Functionality

### Epic 6: Advanced Document Generation & Company Research (Module 5)
- **US-012 (DOCX/PDF Export):** Export tailored CVs and cover letters formatted in standard PDF and DOCX formats (`FR-020`, Should Have).
- **US-013 (Model 3 Content Tailoring):** Integrate fine-tuned Kaggle Model 3 for stylistic alignment and natural phrasing (`ML-003`, Should Have).
- **US-014 (Company Research Summaries):** Gather company mission, industry overview, and recent tech stack details with source attribution for interview prep (`FR-022`, Should Have).

### Epic 7: Comprehensive Application Lifecycle Tracking (Module 6 & 7)
- **US-015 (Status Tracking Pipeline):** Track application statuses (Saved -> Applied -> Interviewing -> Offered) with submission dates and notes (`FR-023`, `FR-024`, Must Have).
- **US-016 (CLI Search & Application Dashboard):** Display summary metrics, active pipelines, and search term effectiveness (`FR-025`, Should Have).
- **US-017 (Multi-Profile Support):** Enable creating and switching between multiple specialized profiles for distinct career paths (`FR-001` enhancement, Could Have).

---

## 4. Milestone 3 Backlog: User Interface Development

### Epic 8: Penpot-Approved Desktop Web UI
- **US-018 (Desktop Web UI):** Implement desktop interface with simulated mock APIs, form validation, and reactive states matching approved Penpot designs (Must Have).

### Epic 9: Penpot-Approved Mobile Responsive UI
- **US-019 (Mobile Interface):** Implement mobile-responsive interface with touch-friendly navigation and simulated workflows matching approved Penpot designs (Must Have).

---

## 5. Milestone 4 Backlog: Server Integration & Production Hardening

### Epic 10: Server API Integration & Production Model Serving
- **US-020 (Backend API Integration):** Connect desktop and mobile interfaces to the user-supplied backend application server (Must Have).
- **US-021 (Server-Side Inference Deployment):** Deploy verified model artifacts to the application server and verify live inference (Must Have).
- **US-022 (Authentication & Security Hardening):** Implement secure user authentication and session management on the supplied server (Must Have).

---

## 6. Milestone 5 Backlog: Continuous Refinement & Optimization

- **US-023 (Performance Optimization):** Profile and optimize memory, latency, and database query efficiency.
- **US-024 (Model Evaluation & Retraining):** Evaluate model inference accuracy against real-world feedback and author retrained Kaggle notebooks.
