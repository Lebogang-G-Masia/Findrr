"""Regression tests for execution and invariant fixes (search bounds, CAPTCHA halt, migration)."""

import sqlite3
from unittest.mock import MagicMock

from findrr.db.connection import get_connection, init_db
from findrr.db.repository import (
    PostingRepository,
    ProfileRepository,
    SearchConfigRepository,
    TitleRepository,
)
from findrr.models.posting import DiscoveryMetrics
from findrr.models.profile import UserProfile
from findrr.models.search_config import RemotePreference, SearchConfiguration
from findrr.models.title import GeneralizedTitle
from findrr.search.engine import JobDiscoveryEngine
from findrr.services.posting_service import PostingService


def _env(tmp_path, min_r=3, max_r=4):
    conn = get_connection(str(tmp_path / "t.db"))
    init_db(conn)
    profiles = ProfileRepository(conn)
    titles = TitleRepository(conn)
    configs = SearchConfigRepository(conn)
    prof = profiles.save_profile(UserProfile(full_name="T P", email="t@example.com"))
    titles.save_title(
        GeneralizedTitle(
            profile_id=prof.id, primary_title="Data Analyst", rationale="r", supporting_skills=[]
        )
    )
    configs.save_configuration(
        SearchConfiguration(
            profile_id=prof.id,
            target_locations=["Cape Town"],
            remote_preference=RemotePreference.HYBRID,
            min_results_per_title=min_r,
            max_results_per_title=max_r,
        )
    )
    engine = MagicMock()
    engine.discover.return_value = ([], DiscoveryMetrics(query="q"))
    svc = PostingService(PostingRepository(conn), profiles, titles, configs, engine)
    return svc, engine, prof


def test_saved_search_bounds_are_used_when_cli_gives_none(tmp_path):
    svc, engine, prof = _env(tmp_path)
    svc.discover_for_profile(prof.id, custom_min=None, custom_max=None)
    kwargs = engine.discover.call_args.kwargs
    assert (kwargs["min_results"], kwargs["max_results"]) == (3, 4)
    assert kwargs["target_locations"] == ["Cape Town"]


def test_title_override_keeps_profile_preferences(tmp_path):
    svc, engine, prof = _env(tmp_path)
    svc.discover_for_profile(prof.id, title_override="BI Developer")
    kwargs = engine.discover.call_args.kwargs
    assert kwargs["title"] == "BI Developer"
    assert kwargs["remote_preference"] == "HYBRID"
    assert kwargs["max_results"] == 4


def test_unresolved_captcha_halts_without_scraping(tmp_path, monkeypatch):
    driver = MagicMock()
    driver.current_url = "https://www.google.com/sorry/index?continue=x"
    driver.title = "Sorry..."
    driver.page_source = '<a href="https://support.google.com/x">help</a>'
    engine = JobDiscoveryEngine(
        driver_factory=lambda headless: driver,
        prompt_hook=lambda msg: (_ for _ in ()).throw(EOFError()),
        snapshot_dir=str(tmp_path),
    )
    import findrr.search.engine as eng

    monkeypatch.setattr(eng, "polite_delay", lambda *a, **k: 0.0)
    postings, metrics = engine.discover("Data Analyst")
    assert postings == []
    assert metrics.halted_reason and "CAPTCHA" in metrics.halted_reason
    driver.quit.assert_called_once()


def test_init_db_migrates_existing_postings_table(tmp_path):
    db = tmp_path / "old.db"
    raw = sqlite3.connect(db)
    raw.execute(
        "CREATE TABLE job_postings (id TEXT PRIMARY KEY, search_term_id TEXT, title TEXT NOT NULL,"
        " company TEXT NOT NULL, location TEXT, description TEXT NOT NULL,"
        " requirements_extracted TEXT, source_url TEXT NOT NULL, direct_apply_url TEXT,"
        " content_hash TEXT NOT NULL UNIQUE, status TEXT NOT NULL DEFAULT 'ACTIVE',"
        " posting_date TEXT, discovered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    raw.commit()
    raw.close()
    conn = get_connection(str(db))
    init_db(conn)
    init_db(conn)  # idempotent
    cols = {r[1] for r in conn.execute("PRAGMA table_info(job_postings)")}
    assert {"availability_evidence", "availability_checked_at"} <= cols


def test_availability_evidence_is_persisted(tmp_path):
    from datetime import datetime, timezone

    from findrr.models.posting import JobPostingCreate, PostingAvailability

    svc, engine, prof = _env(tmp_path)
    dto = JobPostingCreate(
        title="Analyst",
        company="Acme",
        description="Role text",
        source_url="https://acme.example.com/1",
        content_hash="e" * 64,
        status=PostingAvailability.UNCERTAIN,
        availability_evidence="No closing date or closure statement found on the page",
        availability_checked_at=datetime(2026, 11, 26, tzinfo=timezone.utc),
    )
    engine.discover.return_value = ([dto], DiscoveryMetrics(query="q"))
    saved = svc.discover_for_profile(prof.id)["postings"][0]
    stored = svc.posting_repo.get_posting(saved.id)
    assert stored.availability_evidence == dto.availability_evidence
    assert stored.availability_checked_at is not None
