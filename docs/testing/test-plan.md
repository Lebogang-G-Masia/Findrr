# Findrr Test Plan & Verification Strategy

- **Document Version:** 1.0.0
- **Status:** Presented for Review (Bootstrap Gate 5)
- **Author:** Senior Software Engineer / Technical Architect / ML Engineer (Findrr AI Pair)
- **Project Owner:** Lebogang Masia
- **Last Updated:** 2026-11-02

---

## 1. Testing Philosophy & Quality Target

Findrr adheres to a **Test-Driven & Verification-First** methodology. Code generation alone does not qualify as completed work; every feature increment must be verified by automated tests and documented in pull request descriptions.

### Quality Targets:
- **Code Coverage:** >= 80% line coverage across domain and application services.
- **Requirements Traceability:** 100% of functional requirements (`FR-xxx`) and acceptance criteria (`AC-xxx`) must map to automated tests.
- **Zero Silent Failures:** Corrupted model artifacts, missing files, or blocked web requests must produce explicit errors and test assertions.

---

## 2. Testing Pyramid & Test Types

```
               / \
              /   \
             / E2E \       CLI Workflow End-to-End Tests
            /-------\
           /  Integ  \     Selenium Mock/Live, SQLite DB, ML Engine
          /-----------\
         /    Unit     \   Pydantic Validation, Fact Grounding, Parsing
        /---------------\
```

### 2.1 Unit Tests (`tests/unit/`)
- Fast, in-memory execution (< 5 seconds total).
- Tests individual domain models, validation constraints, link extraction regexes, and template formatting.
- `test_profile_schema.py`: Verifies Pydantic schemas and provenance metadata.
- `test_fact_grounding.py`: Verifies `FactGroundingValidator` rejects invented skills or false claims.
- `test_artifact_validator.py`: Verifies SHA-256 hash matching and rejection of tampered files.

### 2.2 Integration Tests (`tests/integration/`)
- Tests interactions between services and local infrastructure.
- `test_sqlite_storage.py`: Verifies relational constraints, cascade deletions, and index performance.
- `test_inference_service.py`: Tests `InferenceService` model loading, lifecycle management, and CPU tensor execution.
- `test_selenium_driver.py`: Verifies WebDriver startup, headful configuration, and delay jittering.

### 2.3 End-to-End CLI Tests (`tests/e2e/`)
- Tests complete user journeys in the CLI using simulated user inputs (Click/Rich runner).
- Journey 1: Onboarding -> Profile Creation -> Generalized Title Synthesis.
- Journey 2: Search Configuration -> Term Expansion -> Posting Extraction -> Application Draft.

---

## 3. Machine Learning Testing & Mock Isolation

In strict adherence to project rules:
1. **Mock Fixture Isolation:** When real model weights are not present, test suites utilize deterministic stubs tagged with `@pytest.mark.mock_inference`.
2. **Explicit Labeling:** Test runners log whether tests executed against `REAL_ARTIFACTS` or `MOCK_FIXTURES`.
3. **No Mocks as Real Verification:** A test passing against mock fixtures is never recorded as proof of model integration.
4. **Integrity Negative Testing:** Test suites explicitly inject corrupt bytes into model weights to assert that `ModelIntegrityError` is raised.

---

## 4. Test Execution & CI Automation

### 4.1 Local Test Commands
```bash
# Run unit and integration tests
pytest tests/ -v

# Run with coverage report
pytest --cov=src/findrr --cov-report=term-missing tests/

# Run pre-commit guardrail scripts
python scripts/check_file_sizes.py
python scripts/check_secrets.py
```

### 4.2 CI Pipeline Enforcements
Every PR into `main` automatically runs:
1. `Lint & Code Quality` (Ruff check and format)
2. `Test Suite` (Pytest against Python 3.12 runner)
3. `File Size & Model Artifact Check` (Strictly blocks files > 5 MB and binary weights)
4. `Secret Scanner` (Gitleaks and pattern validator)
