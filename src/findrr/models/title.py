"""Generalized job title domain models and schemas."""

import uuid
from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class GeneralizedTitleCreate(BaseModel):
    """Schema for creating a synthesized generalized job title."""

    profile_id: str
    primary_title: str = Field(..., min_length=1, description="Synthesized target title")
    rationale: str = Field(..., min_length=1, description="Justification for the title")
    supporting_skills: List[str] = Field(
        default_factory=list, description="Skills supporting title"
    )
    is_active: bool = Field(default=True)


class GeneralizedTitle(BaseModel):
    """Synthesized generalized job title domain model."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    profile_id: str
    primary_title: str
    rationale: str
    supporting_skills: List[str]
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
