"""Search configuration service layer."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from findrr.db.repository import ProfileRepository, SearchConfigRepository
from findrr.models.search_config import (
    RemotePreference,
    SearchBounds,
    SearchConfiguration,
    SearchConfigurationCreate,
)


class SearchConfigService:
    """Service managing job search configuration and strict limit bounds."""

    def __init__(
        self,
        config_repo: SearchConfigRepository,
        profile_repo: ProfileRepository,
    ):
        self.config_repo = config_repo
        self.profile_repo = profile_repo

    def save_configuration(self, config_data: SearchConfigurationCreate) -> SearchConfiguration:
        """Create or update search configuration for a profile."""
        profile = self.profile_repo.get_profile(config_data.profile_id)
        if not profile:
            raise ValueError(f"Profile {config_data.profile_id} does not exist.")

        # Ensure bounds are valid
        SearchBounds(
            min_results=config_data.min_results_per_title,
            max_results=config_data.max_results_per_title,
        )

        existing = self.config_repo.get_configuration(config_data.profile_id)
        now = datetime.now(timezone.utc)
        config_id = existing.id if existing else str(uuid.uuid4())
        created_at = existing.created_at if existing else now

        config = SearchConfiguration(
            id=config_id,
            profile_id=config_data.profile_id,
            target_locations=config_data.target_locations,
            remote_preference=config_data.remote_preference,
            seniority_level=config_data.seniority_level,
            min_compensation=config_data.min_compensation,
            currency=config_data.currency,
            min_results_per_title=config_data.min_results_per_title,
            max_results_per_title=config_data.max_results_per_title,
            created_at=created_at,
            updated_at=now,
        )
        return self.config_repo.save_configuration(config)

    def get_configuration(self, profile_id: str) -> Optional[SearchConfiguration]:
        """Retrieve search configuration for a profile."""
        return self.config_repo.get_configuration(profile_id)

    def set_search_bounds(
        self, profile_id: str, min_results: int, max_results: int
    ) -> SearchConfiguration:
        """Update search bounds, strictly enforcing the 2 to 10 limit range."""
        bounds = SearchBounds(min_results=min_results, max_results=max_results)
        existing = self.get_configuration(profile_id)
        if not existing:
            # Create with default preferences
            create_dto = SearchConfigurationCreate(
                profile_id=profile_id,
                target_locations=[],
                remote_preference=RemotePreference.ANY,
                min_results_per_title=bounds.min_results,
                max_results_per_title=bounds.max_results,
            )
            return self.save_configuration(create_dto)

        create_dto = SearchConfigurationCreate(
            profile_id=profile_id,
            target_locations=existing.target_locations,
            remote_preference=existing.remote_preference,
            seniority_level=existing.seniority_level,
            min_compensation=existing.min_compensation,
            currency=existing.currency,
            min_results_per_title=bounds.min_results,
            max_results_per_title=bounds.max_results,
        )
        return self.save_configuration(create_dto)
