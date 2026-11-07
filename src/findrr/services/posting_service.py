"""Posting service orchestrating job discovery, deduplication, and persistence (Module 4)."""

import logging
import uuid
from typing import Any, Dict, List, Optional

from findrr.db.repository import (
    PostingRepository,
    ProfileRepository,
    SearchConfigRepository,
    TitleRepository,
)
from findrr.models.posting import JobPosting
from findrr.models.search_config import SearchBounds
from findrr.search.engine import IJobDiscoveryEngine, JobDiscoveryEngine

logger = logging.getLogger(__name__)


class PostingService:
    """Service managing end-to-end job search discovery workflows."""

    def __init__(
        self,
        posting_repo: PostingRepository,
        profile_repo: ProfileRepository,
        title_repo: TitleRepository,
        config_repo: SearchConfigRepository,
        discovery_engine: Optional[IJobDiscoveryEngine] = None,
    ):
        self.posting_repo = posting_repo
        self.profile_repo = profile_repo
        self.title_repo = title_repo
        self.config_repo = config_repo
        self.discovery_engine = discovery_engine or JobDiscoveryEngine()

    def discover_for_profile(
        self,
        profile_id: str,
        custom_min: Optional[int] = None,
        custom_max: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute discovery for the active generalized title of a user profile."""
        profile = self.profile_repo.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found.")

        active_title = self.title_repo.get_active_title(profile_id)
        if not active_title:
            raise ValueError(f"No active generalized job title found for profile {profile_id}.")

        config = self.config_repo.get_configuration(profile_id)
        target_locations = config.target_locations if config else []
        remote_pref = config.remote_preference.value if config else "ANY"
        seniority = config.seniority_level.value if config and config.seniority_level else None

        min_results = custom_min or (config.min_results_per_title if config else 2)
        max_results = custom_max or (config.max_results_per_title if config else 10)

        # Enforce canonical bounds 2 to 10
        min_results = max(SearchBounds.MIN_LIMIT, min(SearchBounds.MAX_LIMIT, min_results))
        max_results = max(SearchBounds.MIN_LIMIT, min(SearchBounds.MAX_LIMIT, max_results))
        if min_results > max_results:
            min_results = max_results

        return self.discover_postings_for_title(
            title=active_title.primary_title,
            target_locations=target_locations,
            remote_preference=remote_pref,
            seniority_level=seniority,
            search_term_id=None,
            min_results=min_results,
            max_results=max_results,
        )

    def discover_postings_for_title(
        self,
        title: str,
        target_locations: Optional[List[str]] = None,
        remote_preference: Optional[str] = None,
        seniority_level: Optional[str] = None,
        search_term_id: Optional[str] = None,
        min_results: int = 2,
        max_results: int = 10,
    ) -> Dict[str, Any]:
        """Execute discovery for a specific title and store deduplicated results in the database."""
        extracted_creates, metrics = self.discovery_engine.discover(
            title=title,
            target_locations=target_locations,
            remote_preference=remote_preference,
            seniority_level=seniority_level,
            search_term_id=search_term_id,
            min_results=min_results,
            max_results=max_results,
        )

        saved_postings: List[JobPosting] = []
        db_duplicates = 0

        for create_dto in extracted_creates:
            existing = self.posting_repo.get_by_content_hash(create_dto.content_hash)
            if existing:
                db_duplicates += 1
                logger.info(
                    "Duplicate posting already in DB: %s (%s)",
                    existing.title,
                    existing.company,
                )
                continue

            posting = JobPosting(
                id=str(uuid.uuid4()),
                search_term_id=create_dto.search_term_id,
                title=create_dto.title,
                company=create_dto.company,
                location=create_dto.location,
                description=create_dto.description,
                requirements_extracted=create_dto.requirements_extracted,
                source_url=create_dto.source_url,
                direct_apply_url=create_dto.direct_apply_url,
                content_hash=create_dto.content_hash,
                status=create_dto.status,
                posting_date=create_dto.posting_date,
            )
            saved = self.posting_repo.save_posting(posting)
            saved_postings.append(saved)

        metrics.unique_postings_retained = len(saved_postings)
        metrics.duplicates_detected += db_duplicates

        return {
            "title": title,
            "postings": saved_postings,
            "metrics": metrics,
        }

    def list_postings(self, limit: int = 50) -> List[JobPosting]:
        """List stored job postings."""
        return self.posting_repo.list_all_postings(limit=limit)
