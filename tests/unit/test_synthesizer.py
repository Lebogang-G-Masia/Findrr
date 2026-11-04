"""Unit tests for Generalized Job Title Synthesizer (US-002, FR-005, AC-002)."""

import pytest

from findrr.models.profile import (
    ProfileCategory,
    ProfileEntry,
    UserProfile,
)
from findrr.services.synthesizer import (
    InsufficientProfileDataError,
    TitleSynthesizer,
)


@pytest.fixture
def synthesizer():
    return TitleSynthesizer()


def _make_profile(entries):
    return UserProfile(
        id="test-profile-uuid",
        full_name="Alex River",
        email="alex.river@example.com",
        location="Cape Town",
        professional_summary="Tech professional.",
        entries=entries,
    )


def test_synthesize_software_engineer(synthesizer):
    entries = [
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.EDUCATION,
            title="BSc Computer Science",
            organization="University of Cape Town",
            is_verified=True,
        ),
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.EXPERIENCE,
            title="Software Developer",
            organization="Tech Hub",
            description="Built Python REST APIs using FastAPI and PostgreSQL.",
            is_verified=True,
        ),
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.SKILL,
            title="Python",
            is_verified=True,
        ),
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.SKILL,
            title="SQL",
            is_verified=True,
        ),
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.SKILL,
            title="FastAPI",
            is_verified=True,
        ),
    ]
    profile = _make_profile(entries)
    result = synthesizer.synthesize(profile)

    assert "Software" in result.primary_title or "Developer" in result.primary_title
    assert "Software Engineering" in result.rationale
    assert any("Python" in s for s in result.supporting_skills)
    assert result.is_active is True


def test_synthesize_data_scientist_with_seniority(synthesizer):
    entries = [
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.EDUCATION,
            title="MSc Applied Mathematics & Statistics",
            is_verified=True,
        ),
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.EXPERIENCE,
            title="Senior Machine Learning Engineer",
            organization="AI Labs",
            description="Trained deep learning transformer models in PyTorch.",
            is_verified=True,
        ),
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.SKILL,
            title="PyTorch",
            is_verified=True,
        ),
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.SKILL,
            title="Machine Learning",
            is_verified=True,
        ),
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.SKILL,
            title="Deep Learning",
            is_verified=True,
        ),
    ]
    profile = _make_profile(entries)
    result = synthesizer.synthesize(profile)

    assert "Senior" in result.primary_title
    assert "Data Science & Machine Learning" in result.rationale
    assert result.supporting_skills


def test_synthesize_fails_when_no_education_or_experience(synthesizer):
    entries = [
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.SKILL,
            title="Python",
            is_verified=True,
        ),
    ]
    profile = _make_profile(entries)

    with pytest.raises(InsufficientProfileDataError) as exc_info:
        synthesizer.synthesize(profile)

    assert "At least 1 verified Education or Experience entry" in str(exc_info.value)


def test_synthesize_fails_when_no_skills(synthesizer):
    entries = [
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.EDUCATION,
            title="BSc Computer Science",
            is_verified=True,
        ),
    ]
    profile = _make_profile(entries)

    with pytest.raises(InsufficientProfileDataError) as exc_info:
        synthesizer.synthesize(profile)

    assert "At least 1 verified Skill entry" in str(exc_info.value)


def test_synthesize_ignores_unverified_entries(synthesizer):
    entries = [
        # Unverified education and skills
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.EDUCATION,
            title="BSc Computer Science",
            is_verified=False,
        ),
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.SKILL,
            title="Python",
            is_verified=False,
        ),
    ]
    profile = _make_profile(entries)

    # Must raise error because unverified entries cannot be used for objective synthesis
    with pytest.raises(InsufficientProfileDataError):
        synthesizer.synthesize(profile)


def test_synthesize_lead_title(synthesizer):
    entries = [
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.EXPERIENCE,
            title="Lead DevOps Architect",
            description="Led cloud infrastructure migration using Kubernetes and AWS.",
            is_verified=True,
        ),
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.SKILL,
            title="Kubernetes",
            is_verified=True,
        ),
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.SKILL,
            title="Docker",
            is_verified=True,
        ),
    ]
    profile = _make_profile(entries)
    result = synthesizer.synthesize(profile)
    assert "Lead" in result.primary_title


def test_synthesize_junior_title(synthesizer):
    entries = [
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.EXPERIENCE,
            title="Junior Software Engineer",
            description="Assisted in building REST APIs in Python.",
            is_verified=True,
        ),
        ProfileEntry(
            profile_id="test-profile-uuid",
            category=ProfileCategory.SKILL,
            title="Python",
            is_verified=True,
        ),
    ]
    profile = _make_profile(entries)
    result = synthesizer.synthesize(profile)
    assert "Junior" in result.primary_title
