"""Search term (Module 3) domain models."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TermValidationStatus(str, Enum):
    """Validation outcome for a generated search term (FR-009, FR-010, FR-011)."""

    ACCEPTED = "ACCEPTED"
    REJECTED_LOW_SCORE = "REJECTED_LOW_SCORE"
    REJECTED_DUPLICATE = "REJECTED_DUPLICATE"
    NOT_ACCEPTED_LIMIT = "NOT_ACCEPTED_LIMIT"


class TermSearchStatus(str, Enum):
    """Whether an accepted term has been used by the Find Postings module."""

    PENDING = "PENDING"
    SEARCHED = "SEARCHED"


class SearchTerm(BaseModel):
    """A generated alternative job title and its validation record."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generalized_title_id: str
    generated_term: str
    similarity_score: float
    validation_status: TermValidationStatus
    model_version: str  # e.g. "ML-001 v1.0.0 / ML-002 v1.0.0"
    is_mock: bool = False
    search_status: TermSearchStatus = TermSearchStatus.PENDING
    last_searched_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TermGenerationResult(BaseModel):
    """Outcome of one generation pass, including diagnostics when too few terms pass."""

    primary_title: str
    terms: List[SearchTerm] = Field(default_factory=list)
    is_mock: bool = False
    diagnostics: List[str] = Field(default_factory=list)

    @property
    def accepted(self) -> List[SearchTerm]:
        return [t for t in self.terms if t.validation_status == TermValidationStatus.ACCEPTED]
