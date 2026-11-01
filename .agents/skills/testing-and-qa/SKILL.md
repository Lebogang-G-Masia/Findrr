---
name: testing-and-qa
description: Use when writing tests, running verification, or reporting test results.
---

# Testing and Quality Assurance (Findrr)

Continuously verify that every software increment functions as specified, integrates cleanly with existing components, and satisfies its acceptance criteria.

The testing phase is described in `docs/process/sdlc.md` (Phase 5). The ML testing policy is `docs/ml/evaluation-policy.md`.

## When to Use

* When planning, designing, or executing test suites (unit, integration, system, regression, UAT, performance, security, compatibility, and usability).
* When verifying feature completion during iteration closure and evaluating increments against acceptance criteria.
* When executing machine learning testing across training (Kaggle), artifact validation, server-side inference (Module 9), and end-to-end workflows.
* When managing defects, tracking bugs, and generating test execution reports or acceptance assessments.

---

## 1. Core Definition of Done & Quality Gates

* **Code Generation Is Not Completion:** Never mark a task, feature, or iteration complete based solely on writing code. Every increment requires executed tests and documented verification results.
* **Iteration Acceptance:** At the end of each iteration, explicitly evaluate and record the increment's status against its defined acceptance criteria.
* **No Unverified ML Claims:** Never claim that real model integration has succeeded when tests were only run against mocks, stubs, or synthetic fixtures. Explicitly label any mock-backed test pass as **Integration Status: Unverified (Mocked Artifacts)**.

---

## 2. Standard Software Testing Scope

Design and execute the appropriate testing layers for each increment:
1. **Unit Testing:** Verify individual functions, classes, methods, and isolated module logic.
2. **Integration Testing:** Verify contracts, data flow, database interactions, and service boundaries between modules.
3. **System Testing:** Validate the complete, integrated application against functional specifications.
4. **Regression Testing:** Re-run existing automated test suites on every change to verify no prior functionality broke.
5. **User Acceptance Testing (UAT):** Verify workflows against end-user requirements and acceptance criteria.
6. **Performance Testing:** Measure response latency, throughput, memory usage, and resource limits under expected and peak loads.
7. **Security Testing:** Test authentication, authorization, input sanitization, dependency vulnerabilities, and model artifact integrity checks.
8. **Compatibility Testing:** Verify behavior across target operating environments, browsers/clients, runtime versions, and hardware configurations (CPU/GPU).
9. **Usability Testing:** Validate user interface clarity, error message helpfulness, and workflow consistency.

---

## 3. Machine Learning Testing Architecture

Strictly separate ML testing into four distinct categories and report their statuses independently:

### 1. Training & Evaluation Testing (Kaggle)
* Implemented inside the Kaggle notebooks (executed manually by the user).
* Verifies dataset integrity, train/validation/test split isolation, loss convergence, and evaluation metrics against baseline thresholds.

### 2. Model Artifact Validation (Server Pre-Load)
* Verifies that required artifact files exist at the configured storage path.
* Validates cryptographic checksums/hashes against the model registry.
* Verifies the presence and schema of companion files: model configurations, tokenizers, vocabularies, label mappings, and preprocessing/post-processing configs.

### 3. Application-Side Inference Testing (Module 9)
Test the server's inference pipeline for:
* **Artifact Loading:** Weights, configs, and tokenizers load into memory without error.
* **Training-Serving Skew Prevention:** Server-side input preprocessing exactly matches transformations used during Kaggle training.
* **Prediction Execution:** Forward passes execute cleanly on target device (CPU/GPU) in evaluation/no-grad mode.
* **Post-Processing & Schema Conformance:** Raw outputs map accurately to domain labels/scores and conform to typed interfaces expected by callers.
* **Failure Handling:** Missing files, corrupted weights, checksum mismatches, malformed inputs, and timeouts trigger structured errors/logs without server crashes or fabricated results.
* **Performance:** Loading time, memory footprint, and per-request/batch latency meet requirements.

### 4. End-to-End (E2E) ML Testing
* Tests complete application workflows triggered from API/UI through Module 9 using actual user-supplied trained model artifacts.
* **When Real Artifacts Are Unavailable:** Execute unit, integration, and workflow tests using deterministic mocks or controlled test fixtures. Clearly log and report that E2E model verification is pending real artifacts.

---

## 4. Defect Management & Resolution Workflow

When any test fails or a bug is discovered:
1. **Document:** Record a structured defect entry containing unique ID, title, severity/priority, affected module, reproduction steps, expected result, and actual result/stack trace.
2. **Prioritize:** Rank defects by impact on system stability, security, and iteration acceptance criteria.
3. **Investigate & Resolve:** Identify root cause and implement the fix.
4. **Retest & Regress:** Write or update automated tests covering the defect, verify the fix passes, and run the regression suite to confirm no side effects.

---

## 5. Required Deliverables per Increment

Support every tested software increment with:
* **Test Plan & Test Cases:** Scope, strategy, input conditions, and expected outcomes.
* **Automated Test Suites:** Executable unit, integration, and API/system test code in the repository.
* **Test Execution & Regression Results:** Logs or summary reports showing pass/fail counts, coverage, and regression status.
* **Defect Reports:** Log of identified bugs, root causes, resolutions, and retest verification.
* **Model Evaluation Reports:** Metrics and diagnostic outputs from Kaggle training (once supplied).
* **Model Inference Test Results:** Verification status of artifact loading, preprocessing parity, output conformance, failure handling, and latency (explicitly distinguishing **Mocked** vs. **Real Artifact** execution).
* **Acceptance Assessment:** Final checklist mapping each requirement/criterion to verification evidence and pass/fail verdicts.
