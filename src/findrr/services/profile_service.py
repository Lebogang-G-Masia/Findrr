"""Profile service layer managing user profiles, entries, and title synthesis."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from findrr.db.repository import ProfileRepository, TitleRepository
from findrr.models.profile import (
    ProfileEntry,
    ProfileEntryCreate,
    UserProfile,
    UserProfileCreate,
)
from findrr.models.title import GeneralizedTitle
from findrr.services.synthesizer import TitleSynthesizer


class ProfileService:
    """Service orchestrating profile lifecycle and title synthesis."""

    def __init__(
        self,
        profile_repo: ProfileRepository,
        title_repo: TitleRepository,
        synthesizer: Optional[TitleSynthesizer] = None,
    ):
        self.profile_repo = profile_repo
        self.title_repo = title_repo
        self.synthesizer = synthesizer or TitleSynthesizer()

    def create_profile(
        self,
        user_data: UserProfileCreate,
        entries: Optional[List[ProfileEntryCreate]] = None,
    ) -> UserProfile:
        """Create and persist a new user profile with optional initial entries."""
        profile_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        domain_entries: List[ProfileEntry] = []
        if entries:
            for e in entries:
                domain_entries.append(
                    ProfileEntry(
                        id=str(uuid.uuid4()),
                        profile_id=profile_id,
                        category=e.category,
                        title=e.title,
                        organization=e.organization,
                        start_date=e.start_date,
                        end_date=e.end_date,
                        description=e.description,
                        metadata_json=e.metadata_json,
                        source=e.source,
                        collection_date=now,
                        is_verified=e.is_verified,
                    )
                )

        profile = UserProfile(
            id=profile_id,
            full_name=user_data.full_name,
            email=user_data.email,
            phone=user_data.phone,
            location=user_data.location,
            professional_summary=user_data.professional_summary,
            created_at=now,
            updated_at=now,
            entries=domain_entries,
        )

        return self.profile_repo.save_profile(profile)

    def add_profile_entry(self, profile_id: str, entry_data: ProfileEntryCreate) -> ProfileEntry:
        """Add a single entry to an existing user profile."""
        profile = self.profile_repo.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} does not exist.")

        now = datetime.now(timezone.utc)
        entry = ProfileEntry(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            category=entry_data.category,
            title=entry_data.title,
            organization=entry_data.organization,
            start_date=entry_data.start_date,
            end_date=entry_data.end_date,
            description=entry_data.description,
            metadata_json=entry_data.metadata_json,
            source=entry_data.source,
            collection_date=now,
            is_verified=entry_data.is_verified,
        )
        self.profile_repo.save_entries([entry])
        return entry

    def get_profile(self, profile_id: str) -> Optional[UserProfile]:
        """Retrieve a user profile by ID."""
        return self.profile_repo.get_profile(profile_id)

    def list_profiles(self) -> List[UserProfile]:
        """List all registered user profiles."""
        return self.profile_repo.list_profiles()

    def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile and all cascading relational records."""
        return self.profile_repo.delete_profile(profile_id)

    def verify_entry(self, entry_id: str, is_verified: bool = True) -> bool:
        """Explicitly update the verification state of a profile entry."""
        return self.profile_repo.update_entry_verification(entry_id, is_verified)

    def delete_entry(self, entry_id: str) -> bool:
        """Delete an entry from a profile."""
        return self.profile_repo.delete_entry(entry_id)

    def synthesize_generalized_title(self, profile_id: str) -> GeneralizedTitle:
        """Synthesize an objective generalized title for a profile and persist it."""
        profile = self.profile_repo.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} does not exist.")

        title_create = self.synthesizer.synthesize(profile)
        title = GeneralizedTitle(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            primary_title=title_create.primary_title,
            rationale=title_create.rationale,
            supporting_skills=title_create.supporting_skills,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        return self.title_repo.save_title(title)

    def get_active_title(self, profile_id: str) -> Optional[GeneralizedTitle]:
        """Retrieve the currently active synthesized generalized title for a profile."""
        return self.title_repo.get_active_title(profile_id)

    def list_titles(self, profile_id: str) -> List[GeneralizedTitle]:
        """Retrieve all synthesized titles for a profile."""
        return self.title_repo.list_titles(profile_id)
