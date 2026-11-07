"""Job requirement extraction and verified profile fact matching (Module 5, FR-018, FR-019)."""

import logging
import re
from typing import List, Set, Tuple

from findrr.models.application import RequirementAnalysisResult
from findrr.models.posting import JobPosting
from findrr.models.profile import ProfileCategory, UserProfile
from findrr.search.posting_parser import extract_skills_keywords

logger = logging.getLogger(__name__)


def extract_verified_profile_skills(profile: UserProfile) -> Set[str]:
    """Collect all verified skills and technical competencies from a user profile."""
    skills: Set[str] = set()

    for entry in profile.entries:
        if not entry.is_verified:
            continue

        if entry.category == ProfileCategory.SKILL:
            for s in entry.title.split(","):
                clean = s.strip().lower()
                if clean:
                    skills.add(clean)

        if entry.title:
            for kw in extract_skills_keywords(entry.title):
                skills.add(kw.lower())

        if entry.description:
            for kw in extract_skills_keywords(entry.description):
                skills.add(kw.lower())

        if entry.organization:
            for kw in extract_skills_keywords(entry.organization):
                skills.add(kw.lower())

    return skills


def match_skills(
    required_skills: List[str], verified_skills: Set[str]
) -> Tuple[List[str], List[str], float]:
    """Compare required job skills against verified candidate skills.

    Returns:
        Tuple of (matching_skills, missing_prerequisites, match_percentage)
    """
    if not required_skills:
        return [], [], 100.0

    matching: List[str] = []
    missing: List[str] = []

    for req in required_skills:
        req_clean = req.strip().lower()
        # Direct match or substring word boundary match
        matched = False
        if req_clean in verified_skills:
            matched = True
        else:
            for v_skill in verified_skills:
                if re.search(r"\b" + re.escape(req_clean) + r"\b", v_skill) or re.search(
                    r"\b" + re.escape(v_skill) + r"\b", req_clean
                ):
                    matched = True
                    break

        if matched:
            matching.append(req)
        else:
            missing.append(req)

    match_pct = (len(matching) / len(required_skills)) * 100.0 if required_skills else 0.0
    return matching, missing, round(match_pct, 1)


class FactMatcher:
    """Matches job posting requirements with verified facts from the UserProfile."""

    @classmethod
    def analyze_posting_requirements(
        cls, posting: JobPosting, profile: UserProfile
    ) -> RequirementAnalysisResult:
        """Perform requirement gap analysis mapping posting prerequisites to profile facts."""
        required_skills = posting.requirements_extracted or []
        if not required_skills:
            required_skills = extract_skills_keywords(posting.description)

        verified_skills = extract_verified_profile_skills(profile)
        matching, missing, pct = match_skills(required_skills, verified_skills)

        logger.info(
            "Analyzed posting '%s' against profile '%s': %d matching, %d missing (%.1f%% match)",
            posting.title,
            profile.full_name,
            len(matching),
            len(missing),
            pct,
        )

        return RequirementAnalysisResult(
            posting_id=posting.id,
            posting_title=posting.title,
            company=posting.company,
            extracted_requirements=sorted(required_skills),
            matching_skills=sorted(matching),
            missing_prerequisites=sorted(missing),
            match_percentage=pct,
        )
