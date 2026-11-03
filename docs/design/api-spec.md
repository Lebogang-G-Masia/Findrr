# API Specification (Findrr)

- **Document Version:** 1.0.0
- **Status:** Presented for Review (Bootstrap Gate 5)
- **Author:** Senior Software Engineer / Technical Architect / ML Engineer (Findrr AI Pair)
- **Project Owner:** Lebogang Masia
- **Last Updated:** 2026-11-02

---

## 1. Overview & Phased API Architecture

Findrr's communication architecture spans two distinct operational modes across the project roadmap:
1. **Milestones 1–3 (In-Process Service Contracts):** Direct Python in-process calls between the Presentation layer (CLI) and Application Services.
2. **Milestones 4–5 (Client-Server REST APIs):** HTTP/JSON REST endpoints hosted on the user's application server to serve Desktop Web and Mobile frontends.

---

## 2. In-Process Service Contracts (Milestones 1–3)

All services return Pydantic data models or raise typed subclasses of `FindrrError`.

| Service | Method Signature | Description |
|---|---|---|
| **ProfileService** | `get_active_profile() -> UserProfileDTO` | Retrieves verified active profile |
| **ProfileService** | `synthesize_title(profile_id) -> GeneralizedTitleDTO` | Analyzes facts and produces title |
| **SearchTermService** | `generate_and_validate(title, skills) -> List[SearchTermDTO]` | Expands titles and filters by similarity |
| **DiscoveryService** | `search(term, location, limit) -> List[JobPostingDTO]` | Executes Selenium discovery |
| **AppPrepService** | `create_tailored_cv(profile_id, posting_id, fmt) -> str` | Renders CV without fabrication |
| **InferenceService** | `score_similarity(text_a, text_b) -> float` | Evaluates cosine similarity via Model 2 |

---

## 3. Anticipated REST API Endpoints (Milestones 4–5)

### 3.1 Profile Endpoints
- `GET /api/v1/profile/active`
  - Returns current user profile with verified entries.
- `POST /api/v1/profile`
  - Creates or updates profile data.
- `POST /api/v1/profile/synthesize-title`
  - Synthesizes primary generalized job title.

### 3.2 Search & Discovery Endpoints
- `POST /api/v1/search/expand-terms`
  - Payload: `{"title": str, "skills": list[str]}`
  - Returns: `{"candidate_terms": list[SearchTermDTO]}`
- `POST /api/v1/search/discover`
  - Payload: `{"term": str, "location": str, "limit": int}`
  - Returns: `{"postings": list[JobPostingDTO], "total_discovered": int}`

### 3.3 Application Preparation & Tracking Endpoints
- `POST /api/v1/applications/tailor-cv`
  - Payload: `{"profile_id": str, "posting_id": str, "format": "PDF"}`
  - Returns: Binary file download or relative file URI.
- `GET /api/v1/applications`
  - Returns list of tracked applications and their statuses.
- `PATCH /api/v1/applications/{id}/status`
  - Updates status (`SAVED`, `APPLIED`, `INTERVIEWING`, `OFFERED`, `REJECTED`).

### 3.4 Model Management & Health Endpoints
- `GET /api/v1/models/health`
  - Returns status of loaded models, active versions, and verification checksum results.
