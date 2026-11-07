"""Unit tests for job requirement extraction and fact matching (Module 5, FR-018, FR-019)."""

from findrr.models.posting import JobPosting, PostingAvailability
from findrr.models.profile import ProfileCategory, ProfileEntry, UserProfile
from findrr.services.fact_matcher import (
    FactMatcher,
    extract_verified_profile_skills,
    match_skills,
)


def create_test_profile(verified: bool = True) -> UserProfile:
    prof = UserProfile(
        id="prof-1",
        full_name="Sarah Connor",
        email="sarah@example.com",
    )
    prof.entries = [
        ProfileEntry(
            id="e-1",
            profile_id="prof-1",
            category=ProfileCategory.SKILL,
            title="Python, PostgreSQL, Docker, Linux",
            is_verified=verified,
        ),
        ProfileEntry(
            id="e-2",
            profile_id="prof-1",
            category=ProfileCategory.EXPERIENCE,
            title="Backend Developer",
            organization="Cyberdyne",
            description="Built microservices with FastAPI and AWS.",
            is_verified=verified,
        ),
        ProfileEntry(
            id="e-3",
            profile_id="prof-1",
            category=ProfileCategory.SKILL,
            title="Kubernetes",
            is_verified=False,  # Unverified skill
        ),
    ]
    return prof


def test_extract_verified_profile_skills():
    prof = create_test_profile(verified=True)
    skills = extract_verified_profile_skills(prof)
    assert "python" in skills
    assert "postgresql" in skills
    assert "docker" in skills
    assert "linux" in skills
    assert "fastapi" in skills
    assert "aws" in skills
    # Unverified skill must NOT be included
    assert "kubernetes" not in skills


def test_match_skills_complete_and_partial():
    verified_skills = {"python", "docker", "sql", "linux"}
    required_skills = ["Python", "Docker", "Kubernetes", "Golang"]

    matching, missing, pct = match_skills(required_skills, verified_skills)
    assert "Python" in matching
    assert "Docker" in matching
    assert "Kubernetes" in missing
    assert "Golang" in missing
    assert pct == 50.0


def test_analyze_posting_requirements():
    prof = create_test_profile(verified=True)
    posting = JobPosting(
        id="post-100",
        title="Cloud Platform Engineer",
        company="SkyNet Corp",
        description="Looking for an engineer with Python, Docker, AWS, and Kubernetes experience.",
        requirements_extracted=["python", "docker", "aws", "kubernetes"],
        source_url="https://example.com/job/100",
        content_hash="e" * 64,
        status=PostingAvailability.ACTIVE,
    )

    res = FactMatcher.analyze_posting_requirements(posting, prof)
    assert res.posting_id == "post-100"
    assert res.posting_title == "Cloud Platform Engineer"
    assert res.company == "SkyNet Corp"
    assert "python" in res.matching_skills
    assert "docker" in res.matching_skills
    assert "aws" in res.matching_skills
    assert "kubernetes" in res.missing_prerequisites
    assert res.match_percentage == 75.0
