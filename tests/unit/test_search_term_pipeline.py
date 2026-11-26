"""Tests for the Module 3 search-term pipeline and its use by discovery (FR-008 to FR-011)."""

from unittest.mock import MagicMock

import pytest

from findrr.cli.main import main
from findrr.db.connection import get_connection, init_db
from findrr.db.repository import (
    PostingRepository,
    ProfileRepository,
    SearchConfigRepository,
    SearchTermRepository,
    TitleRepository,
)
from findrr.models.posting import DiscoveryMetrics
from findrr.models.profile import ProfileCategory, ProfileEntry, UserProfile
from findrr.models.search_term import TermSearchStatus, TermValidationStatus
from findrr.models.title import GeneralizedTitle
from findrr.services.inference_service import TitleExpansionResult, ValidatedCandidate
from findrr.services.posting_service import PostingService
from findrr.services.search_term_service import (
    MockInferenceNotAllowedError,
    SearchTermService,
)


@pytest.fixture
def env(tmp_path):
    db = str(tmp_path / "terms.db")
    conn = get_connection(db)
    init_db(conn)
    profiles = ProfileRepository(conn)
    titles = TitleRepository(conn)
    prof = profiles.save_profile(
        UserProfile(
            id="prof-1",
            full_name="T P",
            email="t@example.com",
            entries=[
                ProfileEntry(
                    profile_id="prof-1",
                    category=ProfileCategory.SKILL,
                    title="Python, SQL",
                    is_verified=True,
                )
            ],
        )
    )
    title = titles.save_title(
        GeneralizedTitle(
            profile_id=prof.id, primary_title="Data Analyst", rationale="r", supporting_skills=[]
        )
    )
    return conn, db, prof, title


def _fake_inference(candidates, scores, is_mock=False):
    inf = MagicMock()
    inf.title_expansion_mode.return_value = {
        "is_mock": is_mock,
        "model_version": "ML-001 v1.0.0 / ML-002 v1.0.0",
    }
    inf.expand_titles.return_value = TitleExpansionResult(
        generalized_title="Data Analyst",
        expanded_titles=candidates,
        model_id="ML-001",
        model_version="1.0.0",
        is_mock=is_mock,
    )

    def validate(primary_title, candidates, existing_accepted=None, **_):
        out = []
        for c in candidates:
            s = scores[c]
            status = "ACCEPTED" if s >= 0.7 else "REJECTED_LOW_SCORE"
            out.append(
                ValidatedCandidate(
                    term=c, similarity_score=s, status=status, model_version="1.0.0", is_mock=False
                )
            )
        return out

    inf.filter_and_validate_candidates.side_effect = validate
    return inf


def _service(conn, inf):
    return SearchTermService(
        inf,
        ProfileRepository(conn),
        TitleRepository(conn),
        SearchTermRepository(conn),
        SearchConfigRepository(conn),
    )


def test_refuses_mock_without_explicit_opt_in(env):
    conn, _, prof, _ = env
    svc = _service(conn, _fake_inference([], {}, is_mock=True))
    with pytest.raises(MockInferenceNotAllowedError):
        svc.generate_for_profile(prof.id)


def test_generates_validates_and_persists_terms(env):
    conn, _, prof, title = env
    inf = _fake_inference(
        ["BI Analyst", "data analyst", "Chef"], {"BI Analyst": 0.82, "Chef": 0.2}
    )
    result = _service(conn, inf).generate_for_profile(prof.id)
    by_term = {t.generated_term: t.validation_status for t in result.terms}
    assert by_term["BI Analyst"] == TermValidationStatus.ACCEPTED
    assert by_term["data analyst"] == TermValidationStatus.REJECTED_DUPLICATE  # same as primary
    assert by_term["Chef"] == TermValidationStatus.REJECTED_LOW_SCORE
    stored = SearchTermRepository(conn).list_terms(title.id)
    assert len(stored) == 3 and not any(t.is_mock for t in stored)

    # A second pass treats earlier accepted terms as previously accepted.
    again = _service(conn, inf).generate_for_profile(prof.id)
    assert {t.generated_term: t.validation_status for t in again.terms}["BI Analyst"] == (
        TermValidationStatus.REJECTED_DUPLICATE
    )


def test_max_accepted_terms_cap(env, monkeypatch):
    conn, _, prof, _ = env
    monkeypatch.setenv("FINDRR_MAX_ACCEPTED_TERMS", "1")
    inf = _fake_inference(
        ["BI Analyst", "Data Scientist"], {"BI Analyst": 0.9, "Data Scientist": 0.8}
    )
    result = _service(conn, inf).generate_for_profile(prof.id)
    statuses = [t.validation_status for t in result.terms]
    assert statuses.count(TermValidationStatus.ACCEPTED) == 1
    assert TermValidationStatus.NOT_ACCEPTED_LIMIT in statuses


def test_discovery_searches_accepted_non_mock_terms(env):
    conn, _, prof, title = env
    _service(conn, _fake_inference(["BI Analyst"], {"BI Analyst": 0.9})).generate_for_profile(
        prof.id
    )
    mock_svc = _service(conn, _fake_inference(["Mock Title"], {"Mock Title": 0.9}, is_mock=True))
    mock_svc.generate_for_profile(prof.id, allow_mock=True)

    engine = MagicMock()
    engine.discover.side_effect = lambda **kw: ([], DiscoveryMetrics(query=kw["title"]))
    terms = SearchTermRepository(conn)
    svc = PostingService(
        PostingRepository(conn),
        ProfileRepository(conn),
        TitleRepository(conn),
        SearchConfigRepository(conn),
        engine,
        term_repo=terms,
    )
    results = svc.discover_all_for_profile(prof.id)
    searched = [c.kwargs["title"] for c in engine.discover.call_args_list]
    assert searched == ["Data Analyst", "BI Analyst"]  # MOCK term skipped
    bi = [t for t in terms.list_terms(title.id) if t.generated_term == "BI Analyst"][0]
    assert engine.discover.call_args_list[1].kwargs["search_term_id"] == bi.id
    assert bi.search_status == TermSearchStatus.SEARCHED
    assert len(results) == 2


def test_discovery_stops_after_halt(env):
    conn, _, prof, _ = env
    _service(conn, _fake_inference(["BI Analyst"], {"BI Analyst": 0.9})).generate_for_profile(
        prof.id
    )
    engine = MagicMock()
    halted = DiscoveryMetrics(query="q", halted_reason="CAPTCHA")
    engine.discover.return_value = ([], halted)
    svc = PostingService(
        PostingRepository(conn),
        ProfileRepository(conn),
        TitleRepository(conn),
        SearchConfigRepository(conn),
        engine,
        term_repo=SearchTermRepository(conn),
    )
    results = svc.discover_all_for_profile(prof.id)
    assert engine.discover.call_count == 1
    assert results[-1]["metrics"].halted_reason == "CAPTCHA"


def test_cli_terms_generate_without_artifacts_fails_clearly(env, tmp_path, monkeypatch, capsys):
    _, db, _, _ = env
    monkeypatch.setenv("FINDRR_MODELS_DIR", str(tmp_path / "no-models"))
    code = main(["--db-path", db, "--log-file", str(tmp_path / "l.log"), "terms", "generate"])
    assert code == 1
    assert "MODEL ARTIFACTS UNAVAILABLE" in capsys.readouterr().err
