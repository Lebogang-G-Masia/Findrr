"""Unit and service tests for ProfileService and SearchConfigService."""

import pytest

from findrr.db.connection import get_connection, init_db
from findrr.db.repository import ProfileRepository, SearchConfigRepository, TitleRepository
from findrr.models.profile import (
    ProfileCategory,
    ProfileEntryCreate,
    UserProfileCreate,
)
from findrr.services.profile_service import ProfileService
from findrr.services.search_config_service import SearchConfigService


@pytest.fixture
def services():
    conn = get_connection(":memory:")
    init_db(conn)
    profile_repo = ProfileRepository(conn)
    title_repo = TitleRepository(conn)
    config_repo = SearchConfigRepository(conn)
    p_service = ProfileService(profile_repo, title_repo)
    c_service = SearchConfigService(config_repo, profile_repo)
    yield p_service, c_service
    conn.close()


def test_profile_service_lifecycle(services):
    p_service, _ = services

    user_data = UserProfileCreate(
        full_name="Elena Rostova",
        email="elena@example.com",
        location="Dublin, Ireland",
    )
    profile = p_service.create_profile(user_data)
    assert profile.id is not None
    assert profile.full_name == "Elena Rostova"

    # Add entry
    entry_dto = ProfileEntryCreate(
        category=ProfileCategory.SKILL,
        title="TypeScript",
        is_verified=False,
    )
    entry = p_service.add_profile_entry(profile.id, entry_dto)
    assert entry.title == "TypeScript"
    assert entry.is_verified is False

    # Verify entry
    assert p_service.verify_entry(entry.id, True) is True
    updated_profile = p_service.get_profile(profile.id)
    assert updated_profile.entries[0].is_verified is True

    # Delete entry
    assert p_service.delete_entry(entry.id) is True
    assert len(p_service.get_profile(profile.id).entries) == 0

    # Delete profile
    assert p_service.delete_profile(profile.id) is True
    assert p_service.get_profile(profile.id) is None


def test_search_config_service_bounds(services):
    p_service, c_service = services

    profile = p_service.create_profile(
        UserProfileCreate(full_name="Dan Miller", email="dan@example.com")
    )

    # Set bounds
    config = c_service.set_search_bounds(profile.id, min_results=3, max_results=9)
    assert config.min_results_per_title == 3
    assert config.max_results_per_title == 9

    # Re-retrieve
    retrieved = c_service.get_configuration(profile.id)
    assert retrieved is not None
    assert retrieved.min_results_per_title == 3
    assert retrieved.max_results_per_title == 9

    # Invalid bounds raise ValueError
    with pytest.raises(ValueError):
        c_service.set_search_bounds(profile.id, min_results=1, max_results=10)

    with pytest.raises(ValueError):
        c_service.set_search_bounds(profile.id, min_results=4, max_results=15)
