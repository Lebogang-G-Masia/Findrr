"""Unit tests for DocumentGenerator (Module 5, FR-020, FR-021)."""

from pathlib import Path

import pytest

from findrr.models.application import DocumentType, RequirementAnalysisResult
from findrr.models.posting import JobPosting, PostingAvailability
from findrr.models.profile import ProfileCategory, ProfileEntry, UserProfile
from findrr.services.document_generator import DocumentGenerator


@pytest.fixture
def sample_profile() -> UserProfile:
    return UserProfile(
        id="user-10",
        full_name="Morgan Reed",
        email="morgan@example.com",
        phone="+1-555-0199",
        location="San Francisco, CA",
        entries=[
            ProfileEntry(
                id="e1",
                profile_id="user-10",
                category=ProfileCategory.SKILL,
                title="Python, Django, PostgreSQL, Docker",
                is_verified=True,
            ),
            ProfileEntry(
                id="e2",
                profile_id="user-10",
                category=ProfileCategory.EXPERIENCE,
                title="Senior Backend Engineer",
                organization="Acme Systems",
                start_date="2021-01",
                end_date="2024-03",
                description="Designed high-throughput APIs using Python and PostgreSQL.",
                is_verified=True,
            ),
            ProfileEntry(
                id="e3",
                profile_id="user-10",
                category=ProfileCategory.EDUCATION,
                title="B.S. Computer Science",
                organization="University of Tech",
                end_date="2020",
                is_verified=True,
            ),
            ProfileEntry(
                id="e4",
                profile_id="user-10",
                category=ProfileCategory.CERTIFICATION,
                title="AWS Certified Solutions Architect",
                organization="Amazon Web Services",
                is_verified=True,
            ),
            ProfileEntry(
                id="e5",
                profile_id="user-10",
                category=ProfileCategory.PROJECT,
                title="Findrr Search Engine",
                description="Deterministic employment search and tailored CV generation.",
                is_verified=True,
            ),
        ],
    )


@pytest.fixture
def sample_posting() -> JobPosting:
    return JobPosting(
        id="post-20",
        title="Staff Backend Engineer",
        company="Global FinTech",
        location="San Francisco, CA",
        description="Seeking expert with Python, PostgreSQL, and Docker.",
        requirements_extracted=["python", "postgresql", "docker"],
        source_url="https://fintech.example.com/jobs/20",
        content_hash="b" * 64,
        status=PostingAvailability.ACTIVE,
    )


@pytest.fixture
def sample_analysis() -> RequirementAnalysisResult:
    return RequirementAnalysisResult(
        posting_id="post-20",
        posting_title="Staff Backend Engineer",
        company="Global FinTech",
        extracted_requirements=["python", "postgresql", "docker"],
        matching_skills=["python", "postgresql", "docker"],
        missing_prerequisites=[],
        match_percentage=100.0,
    )


def test_generate_tailored_cv(
    tmp_path: Path,
    sample_profile: UserProfile,
    sample_posting: JobPosting,
    sample_analysis: RequirementAnalysisResult,
):
    gen = DocumentGenerator(storage_dir=tmp_path)
    res = gen.generate_tailored_cv(
        application_id="app-1",
        profile=sample_profile,
        posting=sample_posting,
        analysis=sample_analysis,
    )

    assert res.application_id == "app-1"
    assert res.document_type == DocumentType.TAILORED_CV
    assert res.is_grounded is True
    assert Path(res.file_path).exists()

    content = Path(res.file_path).read_text(encoding="utf-8")
    assert "# Morgan Reed" in content
    assert "San Francisco, CA | morgan@example.com | +1-555-0199" in content
    assert "Staff Backend Engineer" in content
    assert "Global FinTech" in content
    assert "Senior Backend Engineer - Acme Systems" in content
    assert "**B.S. Computer Science**, University of Tech (2020)" in content
    assert "**AWS Certified Solutions Architect** — Amazon Web Services" in content
    assert "### Findrr Search Engine" in content


def test_generate_cover_letter(
    tmp_path: Path,
    sample_profile: UserProfile,
    sample_posting: JobPosting,
    sample_analysis: RequirementAnalysisResult,
):
    gen = DocumentGenerator(storage_dir=tmp_path)
    res = gen.generate_cover_letter(
        application_id="app-1",
        profile=sample_profile,
        posting=sample_posting,
        analysis=sample_analysis,
    )

    assert res.application_id == "app-1"
    assert res.document_type == DocumentType.COVER_LETTER
    assert res.is_grounded is True
    assert Path(res.file_path).exists()

    content = Path(res.file_path).read_text(encoding="utf-8")
    assert "Dear Hiring Team at Global FinTech," in content
    assert "Staff Backend Engineer" in content
    assert "Morgan Reed" in content
    assert "morgan@example.com" in content


FABRICATED_PHRASES = [
    "results-driven",
    "proven",
    "high-quality outcomes",
    "scalable, maintainable",
    "from day one",
    "Verified Proficiency",
    "hands-on",
    "industry best practices",
    "core technical competencies",
]


def test_documents_contain_no_unverified_claims(
    tmp_path: Path,
    sample_profile: UserProfile,
    sample_posting: JobPosting,
    sample_analysis: RequirementAnalysisResult,
):
    gen = DocumentGenerator(storage_dir=tmp_path)
    cv = gen.generate_tailored_cv("app-1", sample_profile, sample_posting, sample_analysis)
    letter = gen.generate_cover_letter("app-1", sample_profile, sample_posting, sample_analysis)
    for text in (cv.content_text, letter.content_text):
        for phrase in FABRICATED_PHRASES:
            assert phrase.lower() not in text.lower(), phrase
    # Skill casing is preserved as the user entered it.
    assert "PostgreSQL" in cv.content_text
    assert "Senior Backend Engineer at Acme Systems (2021-01 — 2024-03)" in letter.content_text


def test_cover_letter_omits_sections_without_profile_facts(tmp_path: Path, sample_posting):
    bare = UserProfile(id="u", full_name="Ada Bare", email="ada@example.com", entries=[])
    analysis = RequirementAnalysisResult(
        posting_id="post-20",
        posting_title="Staff Backend Engineer",
        company="Global FinTech",
        extracted_requirements=["python"],
        matching_skills=[],
        missing_prerequisites=["python"],
        match_percentage=0.0,
    )
    gen = DocumentGenerator(storage_dir=tmp_path)
    letter = gen.generate_cover_letter("app-2", bare, sample_posting, analysis)
    cv = gen.generate_tailored_cv("app-2", bare, sample_posting, analysis)
    assert "skills" not in letter.content_text.lower()
    assert "most recent" not in letter.content_text
    assert "## Skills" not in cv.content_text
    assert "Present" not in cv.content_text
