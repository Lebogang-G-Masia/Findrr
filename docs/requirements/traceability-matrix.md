# Findrr: Requirements Traceability Matrix

- **Document Version:** 1.0.0
- **Status:** Presented for Review (Bootstrap Gate 3)
- **Author:** Senior Software Engineer / Technical Architect / ML Engineer (Findrr AI Pair)
- **Project Owner:** Lebogang Masia
- **Last Updated:** 2026-11-02

---

## 1. Overview & Traceability Structure

This matrix maintains explicit bi-directional traceability across all project layers:
1. **Strategy & Product Layer:** Requirements (`FR`, `NFR`, `BR`, `ML`) & User Stories (`US`)
2. **Engineering Layer:** Architecture Modules, Acceptance Criteria (`AC`), and Automated Tests (`TC`)
3. **Machine Learning Layer:** Model Specifications, Kaggle Notebooks, and Artifact Manifests

---

## 2. Requirements to User Story & Verification Mapping

| Req ID | Title | Module | User Story | Acceptance Criteria | Test Target | ML Asset |
|---|---|---|---|---|---|---|
| **FR-001** | Profile Data Ingestion | Mod 1 (Profile) | `US-001` | `AC-001` | `tests/integration/test_cli.py` | N/A |
| **FR-002** | Profile Normalization | Mod 1 (Profile) | `US-001` | `AC-001` | `tests/unit/test_models.py` | N/A |
| **FR-003** | Data Provenance Tracking | Mod 1 (Profile) | `US-001` | `AC-001` | `tests/integration/test_db.py` | N/A |
| **FR-004** | User Profile Review & Edit | Mod 1 (Profile) | `US-001` | `AC-001` | `tests/integration/test_cli.py` | N/A |
| **FR-005** | Generalized Job Title Synthesis | Mod 1 (Profile) | `US-002` | `AC-002` | `tests/unit/test_synthesizer.py` | N/A |
| **FR-006** | Search Configuration | Mod 2 (Search Config) | `US-003` | `AC-004` | `tests/unit/test_services.py` | N/A |
| **FR-007** | Search Limits (2–10) | Mod 2 (Search Config) | `US-003` | `AC-004` | `tests/unit/test_models.py`, `tests/integration/test_db.py` | N/A |
| **FR-008** | Generative Search Expansion | Mod 3 (Search Terms) | `US-006` | `AC-003` | `tests/unit/test_inference_service.py`, `tests/integration/test_ml_cli.py` | Model 1 (Flan-T5) |
| **FR-009** | Semantic Similarity Scoring | Mod 3 (Search Terms) | `US-007` | `AC-003` | `tests/unit/test_inference_service.py`, `tests/integration/test_ml_cli.py` | Model 2 (MiniLM) |
| **FR-010** | Relevance Thresholding (0.70) | Mod 3 (Search Terms) | `US-007` | `AC-003` | `tests/unit/test_inference_service.py` | Model 2 (MiniLM) |
| **FR-011** | Duplicate Title Rejection (0.88) | Mod 3 (Search Terms) | `US-007` | `AC-003` | `tests/unit/test_inference_service.py` | Model 2 (MiniLM) |
| **FR-012** | Headful Selenium Automation | Mod 4 (Find Postings) | `US-008` | `AC-004` | `tests/unit/test_query_builder.py`, `tests/integration/test_search_cli.py` | N/A |
| **FR-013** | Extract 2–10 Postings/Title | Mod 4 (Find Postings) | `US-008` | `AC-004` | `tests/unit/test_search_limits.py`, `tests/integration/test_posting_service.py` | N/A |
| **FR-014** | Employer Destination Priority | Mod 4 (Find Postings) | `US-009` | `AC-004` | `tests/unit/test_link_resolver.py` | N/A |
| **FR-015** | Structured Posting Extraction | Mod 4 (Find Postings) | `US-009` | `AC-004` | `tests/unit/test_posting_parser.py` | N/A |
| **FR-016** | Duplicate Posting Filtering | Mod 4 (Find Postings) | `US-009` | `AC-004` | `tests/unit/test_posting_parser.py`, `tests/unit/test_search_limits.py`, `tests/integration/test_posting_repository.py` | N/A |
| **FR-017** | No Fabricated Search Results | Mod 4 (Find Postings) | `US-008` | `AC-004` | `tests/unit/test_search_limits.py` | N/A |
| **FR-018** | Job Requirement Extraction | Mod 5 (App Prep) | `US-010` | `AC-005` | `tests/unit/test_requirement_extract.py` | N/A |
| **FR-019** | Profile-to-Job Fact Matching | Mod 5 (App Prep) | `US-010` | `AC-005` | `tests/unit/test_fact_matcher.py` | N/A |
| **FR-020** | Tailored CV Generation | Mod 5 (App Prep) | `US-011`, `US-012` | `AC-005` | `tests/integration/test_cv_tailor.py` | Model 3 |
| **FR-021** | Tailored Cover Letter Generation | Mod 5 (App Prep) | `US-011`, `US-012` | `AC-005` | `tests/integration/test_cover_letter.py` | Model 3 |
| **FR-022** | Company Research Summary | Mod 5 (App Prep) | `US-014` | `AC-005` | `tests/unit/test_company_research.py` | N/A |
| **FR-023** | Application Status Transitions | Mod 6 (App Mgmt) | `US-015` | `AC-005` | `tests/unit/test_app_lifecycle.py` | N/A |
| **FR-024** | Submission Logging & Notes | Mod 6 (App Mgmt) | `US-015` | `AC-005` | `tests/unit/test_app_records.py` | N/A |
| **FR-025** | Search & Pipeline Metrics | Mod 7 (Dashboard) | `US-016` | `AC-005` | `tests/unit/test_dashboard_metrics.py` | N/A |
| **FR-026** | Local Model Artifact Loading | Mod 9 (Model Mgmt) | `US-004` | `AC-006` | `tests/unit/test_ml_runners.py` | Model Registry |
| **FR-027** | SHA-256 Checksum Validation | Mod 9 (Model Mgmt) | `US-004` | `AC-006` | `tests/unit/test_ml_manifest.py` | Manifests |
| **FR-028** | Graceful Diagnostic Failure | Mod 9 (Model Mgmt) | `US-004` | `AC-006` | `tests/unit/test_ml_manifest.py`, `tests/unit/test_ml_registry.py` | N/A |
| **FR-029** | Unified Inference Service | Mod 9 (Model Mgmt) | `US-005` | `AC-006` | `tests/unit/test_inference_service.py`, `tests/integration/test_ml_cli.py` | Models 1 & 2 |
| **FR-030** | Memory Lifecycle Management | Mod 9 (Model Mgmt) | `US-005` | `AC-006` | `tests/unit/test_inference_service.py` | N/A |

---

## 3. Non-Functional Requirements Traceability

| Req ID | Target Metric | Verification Method | Enforcement Layer |
|---|---|---|---|
| **NFR-001** | Host active model RAM <= 1.0 GiB | Test memory footprint assertion in Pytest | `InferenceService` memory manager |
| **NFR-002** | Dual-encoder latency < 50ms; Expander < 1,500ms | Benchmark test suite (`tests/benchmarks/`) | ONNX Runtime CPU execution |
| **NFR-003** | Scraping delay jitter 2.0s–5.0s | WebDriver wrapper interceptor test | `SeleniumSearchDriver` |
| **NFR-004** | Zero credential/secret leakage | CI Gitleaks & `scripts/check_secrets.py` | Pre-commit & GitHub Actions |
| **NFR-005** | Local data privacy | File permission and SQLite path tests | Local environment configuration |
| **NFR-006** | Untrusted HTML/input sanitization | BeautifulSoup security sanitization test | `PostingParser` |
| **NFR-007** | Network resilience (backoff retry) | Mocked network timeout integration test | `SearchService` retry decorator |
| **NFR-008** | Cryptographic artifact verification | Tampered artifact test verifying reject | `ArtifactValidator` |
| **NFR-009** | Zero factual hallucination | Diff validation between CV & verified profile | `DocumentGenerator` validator |
| **NFR-010** | Modular search provider interface | Unit tests with mock search provider | `SearchProviderInterface` |
| **NFR-011** | 100% requirements traceability | Audit check linking SRS to test plan | `TraceabilityMatrix` audit script |

---

## 4. Machine Learning Asset Traceability

| Model Identifier | Functional Purpose | Architecture | Kaggle Notebook | Target Artifacts | Validation Metric |
|---|---|---|---|---|---|
| **ML-001** | Job Title Expander | `google/flan-t5-small` | `notebooks/01_title_expansion_training.ipynb` | `title_expander.safetensors`, `config.json`, `manifest.json` | ROUGE-L >= 0.80 |
| **ML-002** | Semantic Evaluator | `all-MiniLM-L6-v2` | `notebooks/02_similarity_evaluator_training.ipynb` | `similarity_evaluator.onnx`, `tokenizer.json`, `manifest.json` | Pearson r >= 0.85 |
| **ML-003** | Application Tailoring Assistant | `Qwen2.5-0.5B-Instruct` INT8 | `notebooks/03_application_tailoring_training.ipynb` | `tailor_assistant.onnx`, `config.json`, `manifest.json` | Entity precision = 1.0 |
