"""Unit tests for domain models and validation logic."""

import pytest
from pydantic import ValidationError

from findrr.models.profile import (
    ProfileCategory,
    ProfileEntryCreate,
    ProvenanceSource,
    UserProfileCreate,
)
from findrr.models.search_config import (
    RemotePreference,
    SearchBounds,
    SearchConfigurationCreate,
    SeniorityLevel,
)
from findrr.models.title import GeneralizedTitleCreate


def test_user_profile_create_valid():
    profile = UserProfileCreate(
        full_name="Jane Doe",
        email="jane.doe@example.com",
        phone="+27123456789",
        location="Johannesburg, South Africa",
        professional_summary="Experienced software engineer.",
    )
    assert profile.full_name == "Jane Doe"
    assert profile.email == "jane.doe@example.com"


def test_user_profile_create_invalid_email():
    with pytest.raises(ValidationError):
        UserProfileCreate(
            full_name="Jane Doe",
            email="not-an-email",
        )


def test_profile_entry_create_provenance():
    entry = ProfileEntryCreate(
        category=ProfileCategory.SKILL,
        title="Python",
        source=ProvenanceSource.MANUAL,
        is_verified=True,
    )
    assert entry.category == ProfileCategory.SKILL
    assert entry.source == ProvenanceSource.MANUAL
    assert entry.is_verified is True


def test_search_bounds_valid():
    bounds = SearchBounds(min_results=2, max_results=10)
    assert bounds.min_results == 2
    assert bounds.max_results == 10

    custom = SearchBounds(min_results=5, max_results=8)
    assert custom.min_results == 5
    assert custom.max_results == 8


@pytest.mark.parametrize(
    "min_r,max_r",
    [
        (1, 10),  # min below 2
        (2, 11),  # max above 10
        (8, 5),  # min > max
        (0, 15),  # completely out of bounds
    ],
)
def test_search_bounds_invalid(min_r, max_r):
    with pytest.raises(ValidationError):
        SearchBounds(min_results=min_r, max_results=max_r)


def test_search_config_create_validation():
    cfg = SearchConfigurationCreate(
        profile_id="test-id",
        target_locations=["London", "Remote"],
        remote_preference=RemotePreference.REMOTE,
        seniority_level=SeniorityLevel.SENIOR,
        min_compensation=100000.0,
        currency="GBP",
        min_results_per_title=3,
        max_results_per_title=7,
    )
    assert cfg.min_results_per_title == 3
    assert cfg.max_results_per_title == 7


def test_search_config_create_invalid_range():
    with pytest.raises(ValidationError):
        SearchConfigurationCreate(
            profile_id="test-id",
            min_results_per_title=9,
            max_results_per_title=4,
        )


def test_generalized_title_create():
    gt = GeneralizedTitleCreate(
        profile_id="test-id",
        primary_title="Senior Backend Engineer",
        rationale="Proven experience in distributed systems and Python.",
        supporting_skills=["Python", "PostgreSQL", "Docker"],
    )
    assert gt.primary_title == "Senior Backend Engineer"
    assert len(gt.supporting_skills) == 3
