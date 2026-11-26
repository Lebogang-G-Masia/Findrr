"""Tests for multi-profile support and active-profile selection (US-017)."""

import pytest

from findrr.cli.main import main
from findrr.db.connection import get_connection, init_db
from findrr.db.repository import ProfileRepository
from findrr.models.profile import UserProfile
from findrr.services.active_profile import (
    ActiveProfileStore,
    ProfileSelectionError,
    remember_active_after_create,
    resolve_profile_id,
)


@pytest.fixture
def repo(tmp_path):
    conn = get_connection(str(tmp_path / "mp.db"))
    init_db(conn)
    return ProfileRepository(conn), str(tmp_path / "mp.db")


def _add(repo, pid, name):
    return repo.save_profile(UserProfile(id=pid, full_name=name, email=f"{pid}@example.com"))


def test_no_profiles_raises(repo):
    r, _ = repo
    with pytest.raises(ProfileSelectionError, match="No profiles"):
        resolve_profile_id(r)


def test_single_profile_is_used_implicitly(repo):
    r, _ = repo
    _add(r, "p1", "One")
    assert resolve_profile_id(r) == "p1"


def test_multiple_profiles_without_active_refuse_to_guess(repo):
    r, _ = repo
    _add(r, "p1", "One")
    _add(r, "p2", "Two")
    with pytest.raises(ProfileSelectionError, match="profile use"):
        resolve_profile_id(r)
    ActiveProfileStore(r.conn).set("p2")
    assert resolve_profile_id(r) == "p2"
    assert resolve_profile_id(r, "p1") == "p1"  # explicit wins
    with pytest.raises(ProfileSelectionError, match="not found"):
        resolve_profile_id(r, "missing")


def test_stale_active_profile_is_ignored(repo):
    r, _ = repo
    _add(r, "p1", "One")
    ActiveProfileStore(r.conn).set("deleted-id")
    assert resolve_profile_id(r) == "p1"


def test_creating_second_profile_does_not_switch_active(repo):
    r, _ = repo
    _add(r, "p1", "One")
    assert remember_active_after_create(r, "p1") == "p1"
    _add(r, "p2", "Two")
    assert remember_active_after_create(r, "p2") == "p1"
    assert resolve_profile_id(r) == "p1"


def test_existing_single_user_keeps_implicit_profile_when_adding_one(repo):
    r, _ = repo
    _add(r, "p1", "One")  # created before US-017: no stored active profile
    _add(r, "p2", "Two")
    assert remember_active_after_create(r, "p2") == "p1"


def test_cli_profile_use_and_list_marker(repo, tmp_path, capsys):
    r, db = repo
    _add(r, "p1", "One")
    _add(r, "p2", "Two")
    log = ["--log-file", str(tmp_path / "l.log")]
    assert main(["--db-path", db, *log, "config", "show"]) == 1
    assert "none is active" in capsys.readouterr().err

    assert main(["--db-path", db, *log, "profile", "use", "p2"]) == 0
    assert "Active profile: Two" in capsys.readouterr().out

    assert main(["--db-path", db, *log, "profile", "list"]) == 0
    out = capsys.readouterr().out
    assert "* ID: p2" in out and "  ID: p1" in out

    assert main(["--db-path", db, *log, "profile", "use", "nope"]) == 1
