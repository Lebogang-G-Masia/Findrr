"""Unit tests for FactGroundingValidator (NFR-009, BR-002)."""

import pytest

from findrr.models.posting import JobPosting, PostingAvailability
from findrr.models.profile import ProfileCategory, ProfileEntry, UserProfile
from findrr.services.grounding_validator import FabricationDetectedError, FactGroundingValidator


@pytest.fixture
def sample_profile() -> UserProfile:
    return UserProfile(
        id="user-1",
        full_name="Alex Developer",
        email="alex@example.com",
        location="Remote",
        entries=[
            ProfileEntry(
                id="e1",
                profile_id="user-1",
                category=ProfileCategory.SKILL,
                title="Python, SQL, Docker",
                is_verified=True,
            ),
            ProfileEntry(
                id="e2",
                profile_id="user-1",
                category=ProfileCategory.SKILL,
                title="Rust",
                is_verified=False,  # Unverified!
            ),
            ProfileEntry(
                id="e3",
                profile_id="user-1",
                category=ProfileCategory.EXPERIENCE,
                title="Backend Engineer",
                organization="TechCorp",
                is_verified=True,
            ),
        ],
    )


@pytest.fixture
def sample_posting() -> JobPosting:
    return JobPosting(
        id="post-1",
        title="Senior Python Engineer",
        company="PyData Inc",
        location="Remote",
        description="Looking for Python and SQL developer with Docker experience.",
        source_url="https://pydata.example.com/jobs/1",
        content_hash="a" * 64,
        status=PostingAvailability.ACTIVE,
    )


def test_grounding_validator_passes_when_all_skills_verified(
    sample_profile: UserProfile, sample_posting: JobPosting
):
    doc_text = (
        "# Alex Developer\n"
        "alex@example.com | Remote\n\n"
        "## Professional Summary\n"
        "Experienced developer proficient in Python and SQL with Docker experience."
    )
    assert (
        FactGroundingValidator.validate_document_grounding(doc_text, sample_profile, sample_posting)
        is True
    )


def test_grounding_validator_fails_when_unverified_skill_claimed(
    sample_profile: UserProfile, sample_posting: JobPosting
):
    # 'Kubernetes' is not in sample_profile, and 'Rust' is unverified
    doc_text = "# Alex Developer\n## Core Competencies\n- Python\n- Kubernetes"
    with pytest.raises(FabricationDetectedError) as exc_info:
        FactGroundingValidator.validate_document_grounding(doc_text, sample_profile, sample_posting)
    assert "Zero-Fabrication Violation" in str(exc_info.value)
    assert "kubernetes" in str(exc_info.value).lower()


def test_grounding_validator_allows_acknowledged_missing_prerequisites(
    sample_profile: UserProfile, sample_posting: JobPosting
):
    # Mentioning an unverified skill under an acknowledged missing section
    doc_text = "# Alex Developer\nGrounded in Python and Docker.\n\nLearning goals: Kubernetes, Go"
    assert (
        FactGroundingValidator.validate_document_grounding(
            doc_text, sample_profile, sample_posting, allow_missing_acknowledgement=True
        )
        is True
    )


def test_grounding_validator_fails_acknowledged_if_flag_disabled(
    sample_profile: UserProfile, sample_posting: JobPosting
):
    doc_text = "# Alex Developer\nGrounded in Python and Docker.\n\nLearning goals: Kubernetes"
    with pytest.raises(FabricationDetectedError):
        FactGroundingValidator.validate_document_grounding(
            doc_text, sample_profile, sample_posting, allow_missing_acknowledgement=False
        )
