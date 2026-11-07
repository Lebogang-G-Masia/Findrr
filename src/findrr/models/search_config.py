"""Search configuration domain models and schemas."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import ClassVar, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RemotePreference(str, Enum):
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"
    ON_SITE = "ON_SITE"
    ANY = "ANY"


class SeniorityLevel(str, Enum):
    ENTRY = "ENTRY"
    MID = "MID"
    SENIOR = "SENIOR"
    LEAD = "LEAD"


class SearchBounds(BaseModel):
    """Enforces search limits strictly between 2 and 10 postings per title."""

    MIN_LIMIT: ClassVar[int] = 2
    MAX_LIMIT: ClassVar[int] = 10

    min_results: int = Field(default=2, ge=2, le=10, description="Minimum results (2-10)")
    max_results: int = Field(default=10, ge=2, le=10, description="Maximum results (2-10)")

    @model_validator(mode="after")
    def validate_bounds(self) -> "SearchBounds":
        if self.min_results > self.max_results:
            raise ValueError(
                f"min_results ({self.min_results}) cannot exceed max_results ({self.max_results})"
            )
        return self


class SearchConfigurationCreate(BaseModel):
    """Schema for creating or updating search configuration."""

    profile_id: str
    target_locations: List[str] = Field(default_factory=list, description="Target locations")
    remote_preference: RemotePreference = Field(default=RemotePreference.ANY)
    seniority_level: Optional[SeniorityLevel] = Field(default=None)
    min_compensation: Optional[float] = Field(default=None, ge=0.0)
    currency: str = Field(default="USD", max_length=5)
    min_results_per_title: int = Field(default=2, ge=2, le=10)
    max_results_per_title: int = Field(default=10, ge=2, le=10)

    @model_validator(mode="after")
    def validate_results_range(self) -> "SearchConfigurationCreate":
        if self.min_results_per_title > self.max_results_per_title:
            raise ValueError(
                f"min_results_per_title ({self.min_results_per_title}) "
                f"cannot exceed max_results_per_title ({self.max_results_per_title})"
            )
        return self


class SearchConfiguration(BaseModel):
    """Search configuration domain model."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    profile_id: str
    target_locations: List[str]
    remote_preference: RemotePreference = RemotePreference.ANY
    seniority_level: Optional[SeniorityLevel] = None
    min_compensation: Optional[float] = None
    currency: str = "USD"
    min_results_per_title: int = 2
    max_results_per_title: int = 10
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
