"""Domain models package."""

from findrr.models.posting import (
    DiscoveryMetrics,
    JobPosting,
    JobPostingCreate,
    PostingAvailability,
)
from findrr.models.profile import (
    ProfileCategory,
    ProfileEntry,
    ProfileEntryCreate,
    ProvenanceSource,
    UserProfile,
    UserProfileCreate,
)
from findrr.models.search_config import (
    RemotePreference,
    SearchBounds,
    SearchConfiguration,
    SearchConfigurationCreate,
    SeniorityLevel,
)
from findrr.models.title import (
    GeneralizedTitle,
    GeneralizedTitleCreate,
)

__all__ = [
    "ProfileCategory",
    "ProfileEntry",
    "ProfileEntryCreate",
    "ProvenanceSource",
    "UserProfile",
    "UserProfileCreate",
    "RemotePreference",
    "SeniorityLevel",
    "SearchBounds",
    "SearchConfiguration",
    "SearchConfigurationCreate",
    "GeneralizedTitle",
    "GeneralizedTitleCreate",
    "PostingAvailability",
    "JobPosting",
    "JobPostingCreate",
    "DiscoveryMetrics",
]
