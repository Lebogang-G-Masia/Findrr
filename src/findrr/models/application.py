"""Application preparation and tracking domain models (Module 5 & 6)."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ApplicationStatus(str, Enum):
    """Lifecycle status of a job application."""

    DISCOVERED = "DISCOVERED"
    SAVED = "SAVED"
    APPLIED = "APPLIED"
    INTERVIEWING = "INTERVIEWING"
    OFFERED = "OFFERED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


class DocumentType(str, Enum):
    """Type of generated application document."""

    TAILORED_CV = "TAILORED_CV"
    COVER_LETTER = "COVER_LETTER"
    COMPANY_RESEARCH = "COMPANY_RESEARCH"


class ApplicationRecord(BaseModel):
    """Domain model tracking an application opportunity."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    profile_id: str
    job_posting_id: str
    status: ApplicationStatus = ApplicationStatus.DISCOVERED
    applied_at: Optional[datetime] = None
    notes: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApplicationDocument(BaseModel):
    """Domain model for a generated document artifact associated with an application."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    application_id: str
    document_type: DocumentType
    file_path: str
    content_text: str
    model_version: Optional[str] = "deterministic-template-v1"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RequirementAnalysisResult(BaseModel):
    """Analysis result mapping posting prerequisites to verified profile facts."""

    posting_id: str
    posting_title: str
    company: str
    extracted_requirements: List[str]
    matching_skills: List[str]
    missing_prerequisites: List[str]
    match_percentage: float = 0.0


class TailoredDraftResult(BaseModel):
    """Result of tailored CV or cover letter generation."""

    application_id: str
    document_type: DocumentType
    file_path: str
    content_text: str
    is_grounded: bool = True
