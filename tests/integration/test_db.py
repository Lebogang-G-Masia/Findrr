"""Integration tests for SQLite persistence layer and repositories."""

import sqlite3

import pytest

from findrr.db.connection import get_connection, init_db
from findrr.db.repository import ProfileRepository, SearchConfigRepository, TitleRepository
from findrr.models.profile import (
    ProfileCategory,
    ProfileEntry,
    ProvenanceSource,
    UserProfile,
)
from findrr.models.search_config import (
    RemotePreference,
    SearchConfiguration,
)
from findrr.models.title import GeneralizedTitle


@pytest.fixture
def db_conn():
    conn = get_connection(":memory:")
    init_db(conn)
    yield conn
    conn.close()


def test_init_db_creates_all_tables(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}

    expected_tables = {
        "user_profiles",
        "profile_entries",
        "generalized_titles",
        "search_configurations",
        "search_terms",
        "job_postings",
        "application_records",
        "application_documents",
        "activity_logs",
    }
    assert expected_tables.issubset(tables)


def test_profile_crud_and_cascade_delete(db_conn):
    profile_repo = ProfileRepository(db_conn)
    title_repo = TitleRepository(db_conn)
    config_repo = SearchConfigRepository(db_conn)

    profile = UserProfile(
        id="profile-cascade-1",
        full_name="Morgan Chase",
        email="morgan@example.com",
    )
    profile_repo.save_profile(profile)

    entry = ProfileEntry(
        id="entry-1",
        profile_id=profile.id,
        category=ProfileCategory.SKILL,
        title="Python",
        source=ProvenanceSource.MANUAL,
        is_verified=True,
    )
    profile_repo.save_entries([entry])

    title = GeneralizedTitle(
        id="title-1",
        profile_id=profile.id,
        primary_title="Software Developer",
        rationale="Experienced in Python",
        supporting_skills=["Python"],
    )
    title_repo.save_title(title)

    config = SearchConfiguration(
        id="config-1",
        profile_id=profile.id,
        target_locations=["London"],
        remote_preference=RemotePreference.REMOTE,
        min_results_per_title=3,
        max_results_per_title=8,
    )
    config_repo.save_configuration(config)

    # Verify everything exists
    assert profile_repo.get_profile(profile.id) is not None
    assert len(profile_repo.get_entries(profile.id)) == 1
    assert title_repo.get_active_title(profile.id) is not None
    assert config_repo.get_configuration(profile.id) is not None

    # Delete profile and verify cascade deletes entries, title, and config
    deleted = profile_repo.delete_profile(profile.id)
    assert deleted is True
    assert profile_repo.get_profile(profile.id) is None
    assert len(profile_repo.get_entries(profile.id)) == 0
    assert title_repo.get_active_title(profile.id) is None
    assert config_repo.get_configuration(profile.id) is None


def test_search_config_check_constraint_enforcement(db_conn):
    profile_repo = ProfileRepository(db_conn)
    profile = UserProfile(
        id="profile-check-1",
        full_name="Test User",
        email="test@example.com",
    )
    profile_repo.save_profile(profile)

    cursor = db_conn.cursor()
    # Direct SQL attempting to bypass limits: min < 2
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO search_configurations (
                id, profile_id, target_locations, remote_preference,
                min_results_per_title, max_results_per_title
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("cfg-invalid-1", profile.id, "[]", "REMOTE", 1, 10),
        )

    # Direct SQL attempting to bypass limits: max > 10
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO search_configurations (
                id, profile_id, target_locations, remote_preference,
                min_results_per_title, max_results_per_title
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("cfg-invalid-2", profile.id, "[]", "REMOTE", 2, 11),
        )


def test_entry_verification_update(db_conn):
    profile_repo = ProfileRepository(db_conn)
    profile = UserProfile(
        id="profile-ver-1",
        full_name="Verification User",
        email="verify@example.com",
    )
    profile_repo.save_profile(profile)

    entry = ProfileEntry(
        id="entry-ver-1",
        profile_id=profile.id,
        category=ProfileCategory.EXPERIENCE,
        title="Junior Developer",
        is_verified=False,
    )
    profile_repo.save_entries([entry])

    loaded_entry = profile_repo.get_entries(profile.id)[0]
    assert loaded_entry.is_verified is False

    # Update verification
    profile_repo.update_entry_verification(entry.id, True)
    updated_entry = profile_repo.get_entries(profile.id)[0]
    assert updated_entry.is_verified is True
