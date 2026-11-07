"""Job posting domain models and schemas (Module 4)."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class PostingAvailability(str, Enum):
    """Job posting availability status per Module 4 specification."""

    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"
    UNCERTAIN = "UNCERTAIN"
    UNAVAILABLE = "UNAVAILABLE"


class JobPostingCreate(BaseModel):
    """DTO for creating a new job posting record."""

    search_term_id: Optional[str] = None
    title: str = Field(..., min_length=1)
    company: str = Field(..., min_length=1)
    location: Optional[str] = None
    description: str = Field(..., min_length=1)
    requirements_extracted: Optional[List[str]] = Field(default_factory=list)
    source_url: str = Field(..., min_length=1)
    direct_apply_url: Optional[str] = None
    content_hash: str = Field(..., min_length=64, max_length=64)
    status: PostingAvailability = PostingAvailability.ACTIVE
    posting_date: Optional[str] = None


class JobPosting(BaseModel):
    """Domain model representing a stored job posting."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    search_term_id: Optional[str] = None
    title: str
    company: str
    location: Optional[str] = None
    description: str
    requirements_extracted: Optional[List[str]] = Field(default_factory=list)
    source_url: str
    direct_apply_url: Optional[str] = None
    content_hash: str
    status: PostingAvailability = PostingAvailability.ACTIVE
    posting_date: Optional[str] = None
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DiscoveryMetrics(BaseModel):
    """Job search session discovery metrics (FR-013, Module 4)."""

    query: str
    results_retrieved: int = 0
    postings_extracted: int = 0
    unique_postings_retained: int = 0
    duplicates_detected: int = 0
