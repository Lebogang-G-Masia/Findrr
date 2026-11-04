"""Profile domain models and schemas."""

import re
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


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
    """Schema for creating a profile entry."""

    category: ProfileCategory
    title: str = Field(..., min_length=1, description="Degree, Job Title, or Skill Name")
    organization: Optional[str] = Field(default=None, description="University, Employer, etc.")
    start_date: Optional[str] = Field(default=None, description="ISO-8601 YYYY-MM or YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="ISO-8601 or CURRENT")
    description: Optional[str] = Field(default=None, description="Responsibilities or achievements")
    metadata_json: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional attributes"
    )
    source: ProvenanceSource = Field(default=ProvenanceSource.MANUAL)
    is_verified: bool = Field(default=False)


class ProfileEntry(BaseModel):
    """Normalized profile entry domain model."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    profile_id: str
    category: ProfileCategory
    title: str
    organization: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    source: ProvenanceSource = ProvenanceSource.MANUAL
    collection_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_verified: bool = False


class UserProfileCreate(BaseModel):
    """Schema for creating a user profile."""

    full_name: str = Field(..., min_length=1, description="User full legal or preferred name")
    email: str = Field(..., description="Valid contact email address")
    phone: Optional[str] = Field(default=None, description="Contact phone number")
    location: Optional[str] = Field(default=None, description="City, Region, Country")
    professional_summary: Optional[str] = Field(default=None, description="Summary statement")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip()
        if not EMAIL_REGEX.match(v):
            raise ValueError(f"Invalid email address: {v}")
        return v


class UserProfile(BaseModel):
    """User profile domain model."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    full_name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    professional_summary: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    entries: List[ProfileEntry] = Field(default_factory=list)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip()
        if not EMAIL_REGEX.match(v):
            raise ValueError(f"Invalid email address: {v}")
        return v
