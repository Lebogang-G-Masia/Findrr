# Technical Design Specifications (Findrr)

- **Document Version:** 1.0.0
- **Status:** Presented for Review (Bootstrap Gate 5)
- **Author:** Senior Software Engineer / Technical Architect / ML Engineer (Findrr AI Pair)
- **Project Owner:** Lebogang Masia
- **Last Updated:** 2026-11-02

---

## 1. Domain Models & Pydantic Schemas

All core domain entities are defined using Pydantic v2 schemas to ensure runtime type safety, serialization parity, and schema validation.

### 1.1 Profile Domain Schemas
```python
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class ProvenanceSource(str, Enum):
    MANUAL = "MANUAL"
    RESUME_UPLOAD = "RESUME_UPLOAD"
    LINKEDIN = "LINKEDIN"
    GITHUB = "GITHUB"


class ProfileCategory(str, Enum):
    EDUCATION = "EDUCATION"
    EXPERIENCE = "EXPERIENCE"
    SKILL = "SKILL"
    CERTIFICATION = "CERTIFICATION"
    PROJECT = "PROJECT"


class ProfileEntryCreate(BaseModel):
    category: ProfileCategory
    title: str
    organization: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    source: ProvenanceSource = ProvenanceSource.MANUAL
    is_verified: bool = False


class UserProfileDTO(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    professional_summary: Optional[str] = None
    entries: List[ProfileEntryCreate] = Field(default_factory=list)
```

### 1.2 Search & Discovery Schemas
```python
class SearchBounds(BaseModel):
    min_results: int = Field(default=2, ge=2, le=10)
    max_results: int = Field(default=10, ge=2, le=10)


class SearchTermDTO(BaseModel):
    id: str
    term: str
    similarity_score: float
    is_accepted: bool


class JobPostingDTO(BaseModel):
    id: str
    title: str
    company: str
    location: Optional[str]
    description: str
    required_skills: List[str]
    source_url: str
    direct_apply_url: str
    content_hash: str
    status: str                          # ACTIVE | CLOSED | EXPIRED | UNCERTAIN | UNAVAILABLE
    availability_evidence: Optional[str]  # why `status` was assigned
    availability_checked_at: Optional[datetime]
    posting_date: Optional[str]           # only when the page states it
```

**Discovery contract notes (2026-11-26):**
- `findrr search run` takes its result bounds from the profile's saved search configuration. `--min` and `--max` override it only when given. `--title` replaces only the searched title; locations, remote preference and seniority still come from the profile.
- An unsolved CAPTCHA stops discovery. `DiscoveryMetrics.halted_reason` is set, the challenge page is never parsed for links, and the CLI exits with code 2.
- `findrr search run` searches the primary title, then each accepted non-MOCK term (`PostingService.discover_all_for_profile`). Each term is bounded 2–10 independently, its postings are linked through `search_term_id`, and the term is marked `SEARCHED`. A halt stops the remaining queries. `--primary-only` opts out.
- Debug snapshots (`last_search_page.html/.png`) are written to the directory of `--log-file`.
- The parser never substitutes the search query for a missing posting title. It never sets `posting_date` unless the page states one.
- Availability classification follows `docs/design/database-design.md` §3.6.

---

## 2. Service Interfaces & Contracts

### 2.1 Module 1: `ProfileService`
```python
from abc import ABC, abstractmethod


class IProfileService(ABC):
    @abstractmethod
    def create_profile(self, profile_data: UserProfileDTO) -> UserProfileDTO:
        """Create and store a new user profile."""
        pass

    @abstractmethod
    def ingest_resume(self, file_path: str) -> List[ProfileEntryCreate]:
        """Extract unverified profile entries from a resume document."""
        pass

    @abstractmethod
    def synthesize_generalized_title(self, profile_id: str) -> dict:
        """Analyze verified profile facts and synthesize a generalized job title."""
        pass
```

### 2.1a Active profile (US-017)
`findrr.services.active_profile.resolve_profile_id(profile_repo, explicit=None)` is the single rule for which profile a command acts on:
1. an explicit ID, which must exist;
2. otherwise the stored active profile, if it still exists;
3. otherwise the only profile;
4. otherwise `ProfileSelectionError`, with guidance to run `findrr profile use <id>`.

`remember_active_after_create` keeps the current profile active when another is created.

### 2.2 Module 3: `SearchTermService`
```python
class ISearchTermService(ABC):
    @abstractmethod
    def expand_titles(self, generalized_title: str, skills: List[str]) -> List[str]:
        """Invoke Model 1 to generate alternative candidate titles."""
        pass

    @abstractmethod
    def validate_and_filter(
        self, primary_title: str, candidate_titles: List[str], threshold: float = 0.70
    ) -> List[SearchTermDTO]:
        """Invoke Model 2 to score semantic similarity and reject duplicates."""
        pass
```

**Implementation (2026-11-26):** `findrr.services.search_term_service.SearchTermService.generate_for_profile(profile_id, allow_mock=False)` runs **one** generation pass (no retry loop) in this order:
1. Model 1 expands the active title, using verified skills and the saved seniority.
2. Exact duplicates are rejected, using normalised strings against the primary title and earlier accepted terms.
3. Model 2 scores relevance and near-duplicates (FR-010 and FR-011 thresholds from `findrr.config`).
4. The optional cap `FINDRR_MAX_ACCEPTED_TERMS` applies. It has no default, because no value is approved.
5. Every outcome is persisted.

If either model would run as MOCK, it raises `MockInferenceNotAllowedError` unless `allow_mock` is set. MOCK terms are stored with `is_mock=1` and are never searched. CLI: `findrr terms generate [--allow-mock]` and `findrr terms list`.

### 2.3 Module 4: `JobDiscoveryService`
```python
class IJobDiscoveryService(ABC):
    @abstractmethod
    def discover_postings(
        self, search_term: str, location: str, limit: int = 10
    ) -> List[JobPostingDTO]:
        """Execute headful Selenium search, resolve employer links, and return postings."""
        pass
```

### 2.4 Module 5: `ApplicationPrepService`
```python
class IApplicationPrepService(ABC):
    @abstractmethod
    def analyze_requirements(self, posting_id: str) -> List[str]:
        """Extract required skills and prerequisites from posting description."""
        pass

    @abstractmethod
    def generate_tailored_cv(
        self, profile_id: str, posting_id: str, output_format: str = "PDF"
    ) -> str:
        """Generate tailored CV strictly grounded in verified facts, returning file path."""
        pass
```

### 2.5 Module 9: `InferenceService`
```python
class IInferenceService(ABC):
    @abstractmethod
    def generate_text(self, model_id: str, prompt: str, **kwargs) -> str:
        """Execute text generation forward pass on CPU."""
        pass

    @abstractmethod
    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """Execute bi-encoder embedding and return cosine similarity."""
        pass

    @abstractmethod
    def verify_model_integrity(self, model_id: str, version: str) -> bool:
        """Verify SHA-256 checksums of all model bundle artifacts against manifest."""
        pass
```

---

### 2.6 Configuration (`findrr.config`)
The CLI loads `.env` at startup (`python-dotenv`); real environment variables take precedence. These thresholds are **provisional** (BR-006) until they are evaluated and approved:

| Variable | Default | Requirement |
|---|---|---|
| `FINDRR_RELEVANCE_THRESHOLD` | 0.70 | FR-010 |
| `FINDRR_DEDUP_THRESHOLD` | 0.88 | FR-011 |

An invalid value (not a number, or outside 0–1) logs an error and falls back to the default.

### 2.7 Document generation (Module 5)
CV and cover-letter templates state only facts from verified profile entries or from the posting. They add no adjectives, proficiency levels, achievements or fallback skill claims. A section with no verified facts is omitted. Dates appear only as the user entered them. Output is Markdown; DOCX and PDF are not implemented (D-003).

## 3. Error Handling & Exception Hierarchy

```python
class FindrrError(Exception):
    """Base exception for all Findrr application errors."""

    pass


class ModelIntegrityError(FindrrError):
    """Raised when an artifact checksum mismatch is detected."""

    pass


class ModelArtifactMissingError(FindrrError):
    """Raised when required model files are absent from disk."""

    pass


class FactGroundingViolationError(FindrrError):
    """Raised when generated text contains claims absent from verified profile facts."""

    pass


class ScrapingBlockedError(FindrrError):
    """Raised when a web destination blocks automation or presents CAPTCHA."""

    pass
```
