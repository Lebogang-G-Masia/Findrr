"""Search term generation and validation workflow (Module 3, FR-008 to FR-011)."""

import logging
import re
from typing import List, Optional

from findrr import config
from findrr.db.repository import (
    ProfileRepository,
    SearchConfigRepository,
    SearchTermRepository,
    TitleRepository,
)
from findrr.models.profile import ProfileCategory
from findrr.models.search_term import SearchTerm, TermGenerationResult, TermValidationStatus
from findrr.services.inference_service import InferenceService

logger = logging.getLogger(__name__)


class MockInferenceNotAllowedError(RuntimeError):
    """Raised when verified model artifacts are unavailable and MOCK use was not requested."""


def _normalize(term: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", term.lower()).split())


class SearchTermService:
    """Generates alternative titles (Model 1), validates them (Model 2) and stores outcomes."""

    def __init__(
        self,
        inference: InferenceService,
        profile_repo: ProfileRepository,
        title_repo: TitleRepository,
        term_repo: SearchTermRepository,
        config_repo: Optional[SearchConfigRepository] = None,
    ):
        self.inference = inference
        self.profile_repo = profile_repo
        self.title_repo = title_repo
        self.term_repo = term_repo
        self.config_repo = config_repo

    def generate_for_profile(
        self, profile_id: str, allow_mock: bool = False
    ) -> TermGenerationResult:
        """Run one generation pass for the profile's active title and persist every outcome.

        One pass only (no retry loop). Without verified artifacts this raises
        ``MockInferenceNotAllowedError`` unless ``allow_mock`` is set, in which case every
        stored term is flagged ``is_mock`` and is never used for live searches.
        """
        profile = self.profile_repo.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found.")
        title = self.title_repo.get_active_title(profile_id)
        if not title:
            raise ValueError(
                f"No active generalized title for profile {profile_id}. "
                "Run 'findrr profile synthesize' first."
            )

        mode = self.inference.title_expansion_mode()
        if mode["is_mock"] and not allow_mock:
            msg = (
                "Verified Model 1/Model 2 artifacts are not available, so search terms cannot "
                "be generated. Supply the artifacts (see 'findrr model list'), or pass "
                "--allow-mock to generate clearly labelled MOCK terms for testing only."
            )
            logger.error(msg)
            raise MockInferenceNotAllowedError(msg)

        skills = sorted(
            {
                part.strip()
                for e in profile.entries
                if e.is_verified and e.category == ProfileCategory.SKILL
                for part in e.title.split(",")
                if part.strip()
            }
        )
        seniority = None
        if self.config_repo:
            cfg = self.config_repo.get_configuration(profile_id)
            if cfg and cfg.seniority_level:
                seniority = cfg.seniority_level.value

        expansion = self.inference.expand_titles(
            generalized_title=title.primary_title, skills=skills, seniority=seniority
        )

        previous = self.term_repo.list_accepted(title.id, include_mock=True)
        seen = {_normalize(title.primary_title)} | {_normalize(t.generated_term) for t in previous}
        result = TermGenerationResult(primary_title=title.primary_title, is_mock=mode["is_mock"])

        fresh: List[str] = []
        for cand in expansion.expanded_titles:
            norm = _normalize(cand)
            if not norm:
                continue
            if norm in seen:
                result.terms.append(
                    self._term(title.id, cand, 1.0, TermValidationStatus.REJECTED_DUPLICATE, mode)
                )
                continue
            seen.add(norm)
            fresh.append(cand)

        validated = self.inference.filter_and_validate_candidates(
            primary_title=title.primary_title,
            candidates=fresh,
            existing_accepted=[t.generated_term for t in previous],
        )
        cap = config.max_accepted_terms()
        accepted_count = 0
        for v in validated:
            status = TermValidationStatus(v.status)
            if status == TermValidationStatus.ACCEPTED:
                if cap is not None and accepted_count >= cap:
                    status = TermValidationStatus.NOT_ACCEPTED_LIMIT
                else:
                    accepted_count += 1
            result.terms.append(self._term(title.id, v.term, v.similarity_score, status, mode))

        if result.terms:
            self.term_repo.save_terms(result.terms)

        if not expansion.expanded_titles:
            result.diagnostics.append("Model 1 returned no candidate titles.")
        if accepted_count == 0:
            result.diagnostics.append(
                "No new titles passed validation. Discovery will use the primary title only."
            )
        logger.info(
            "Search term generation for '%s': %d candidates, %d accepted (mock=%s)",
            title.primary_title,
            len(result.terms),
            accepted_count,
            mode["is_mock"],
        )
        return result

    def list_for_profile(self, profile_id: str) -> List[SearchTerm]:
        title = self.title_repo.get_active_title(profile_id)
        return self.term_repo.list_terms(title.id) if title else []

    @staticmethod
    def _term(title_id, text, score, status, mode) -> SearchTerm:
        return SearchTerm(
            generalized_title_id=title_id,
            generated_term=text,
            similarity_score=float(score),
            validation_status=status,
            model_version=mode["model_version"],
            is_mock=mode["is_mock"],
        )
