"""Factual grounding validation and zero-fabrication enforcement (NFR-009, BR-002)."""

import logging
import re
from typing import List, Set

from findrr.models.posting import JobPosting
from findrr.models.profile import UserProfile
from findrr.search.posting_parser import extract_skills_keywords
from findrr.services.fact_matcher import extract_verified_profile_skills

logger = logging.getLogger(__name__)


class FabricationDetectedError(ValueError):
    """Raised when generated document text asserts facts absent from verified user profile."""

    pass


class FactGroundingValidator:
    """Enforces zero-fabrication invariant on tailored application documents."""

    @classmethod
    def validate_document_grounding(
        cls,
        document_text: str,
        profile: UserProfile,
        posting: JobPosting,
        allow_missing_acknowledgement: bool = True,
    ) -> bool:
        """Verify that candidate claims in document_text are grounded in verified profile data.

        Raises FabricationDetectedError if an invented candidate credential or skill is found.
        """
        verified_skills: Set[str] = extract_verified_profile_skills(profile)

        # Contextual posting keywords (job title, company name) cited in header/summary
        posting_context_keywords: Set[str] = set()
        if posting.title:
            for kw in extract_skills_keywords(posting.title):
                posting_context_keywords.add(kw.lower())
        if posting.company:
            for kw in extract_skills_keywords(posting.company):
                posting_context_keywords.add(kw.lower())

        # Check skills mentioned in the document as skills possessed by the candidate
        mentioned_skills = extract_skills_keywords(document_text)
        missing_skills_acknowledged = cls._extract_missing_skills_acknowledged(document_text)

        unverified_claims: List[str] = []
        for skill in mentioned_skills:
            # If skill is verified in profile, passes
            if skill in verified_skills:
                continue
            # If skill is part of the posting title / company being referenced, passes
            if skill in posting_context_keywords:
                continue
            # If skill was explicitly acknowledged as missing or learning target, allowed
            if allow_missing_acknowledgement and skill in missing_skills_acknowledged:
                continue
            # If skill was neither verified nor acknowledged as missing, it's an unverified claim
            unverified_claims.append(skill)

        if unverified_claims:
            err_msg = (
                f"Zero-Fabrication Violation: Generated document claims unverified skills: "
                f"{unverified_claims}. Grounding invariant (NFR-009, BR-002) requires all claims "
                f"to be backed by verified profile facts."
            )
            logger.error(err_msg)
            raise FabricationDetectedError(err_msg)

        logger.info(
            "Factual grounding verified for document (%d verified skills confirmed)",
            len(verified_skills),
        )
        return True

    @classmethod
    def _extract_missing_skills_acknowledged(cls, text: str) -> Set[str]:
        """Extract skills that are explicitly acknowledged as missing or to be acquired."""
        acknowledged: Set[str] = set()
        patterns = [
            r"(?:eager to learn|familiarizing with|actively acquiring|working towards)\s+([^.\n]+)",
            r"(?:prerequisites to acquire|skills to develop|learning goals):\s*([^.\n]+)",
        ]
        for pat in patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                section = match.group(1)
                for kw in extract_skills_keywords(section):
                    acknowledged.add(kw)
        return acknowledged
