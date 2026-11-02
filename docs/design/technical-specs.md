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
```

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
