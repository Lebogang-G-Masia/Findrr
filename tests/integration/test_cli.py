"""Integration tests for Findrr CLI interface and workflows."""

from io import StringIO
from unittest.mock import patch

import pytest

from findrr.cli.main import main
from findrr.db.connection import get_connection
from findrr.db.repository import ProfileRepository, SearchConfigRepository, TitleRepository


@pytest.fixture
def test_db_path(tmp_path):
    db_file = tmp_path / "findrr_test.db"
    return str(db_file)


def test_cli_init_db(test_db_path):
    exit_code = main(["--db-path", test_db_path, "init-db"])
    assert exit_code == 0

    conn = get_connection(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_profiles'")
    assert cursor.fetchone() is not None
    conn.close()


def test_cli_profile_questionnaire_success(test_db_path):
    # Simulated user inputs:
    # 1. Full name
    # 2. Email
    # 3. Phone
    # 4. Location
    # 5. Summary
    # 6. Add education? yes
    # 7. Degree
    # 8. Institution
    # 9. Start date
    # 10. End date
    # 11. Notes
    # 12. Add education? no
    # 13. Add experience? yes
    # 14. Job title
    # 15. Company
    # 16. Start date
    # 17. End date
    # 18. Description
    # 19. Add experience? no
    # 20. Skills
    # 21. Verification approval: yes
    inputs = [
        "Sarah Connor",
        "sarah@example.com",
        "+1234567890",
        "Los Angeles, CA",
        "Systems and Security Specialist",
        "y",
        "BSc Computer Engineering",
        "Caltech",
        "2018-09",
        "2022-06",
        "First class honours",
        "n",
        "y",
        "DevOps Engineer",
        "Cyberdyne",
        "2022-07",
        "CURRENT",
        "Managed Docker containers, Linux servers, and CI/CD pipelines",
        "n",
        "Linux, Docker, Python, Bash, CI/CD",
        "y",  # Explicit verification approval (FR-004)
    ]

    with patch("builtins.input", side_effect=inputs):
        exit_code = main(["--db-path", test_db_path, "profile", "create"])
        assert exit_code == 0

    conn = get_connection(test_db_path)
    profile_repo = ProfileRepository(conn)
    profiles = profile_repo.list_profiles()
    assert len(profiles) == 1
    assert profiles[0].full_name == "Sarah Connor"
    assert len(profiles[0].entries) == 7  # 1 edu + 1 exp + 5 skills
    assert all(e.is_verified for e in profiles[0].entries)
    conn.close()


def test_cli_profile_questionnaire_cancelled_on_review(test_db_path):
    inputs = [
        "John Doe",
        "john@example.com",
        "",
        "",
        "",
        "n",
        "n",
        "Python",
        "n",  # Rejected verification approval
    ]

    with patch("builtins.input", side_effect=inputs):
        exit_code = main(["--db-path", test_db_path, "profile", "create"])
        assert exit_code == 0

    conn = get_connection(test_db_path)
    profile_repo = ProfileRepository(conn)
    profiles = profile_repo.list_profiles()
    assert len(profiles) == 0  # Nothing saved
    conn.close()


def test_cli_synthesize_title(test_db_path):
    # Setup profile first
    inputs = [
        "David Clark",
        "david@example.com",
        "",
        "London",
        "",
        "y",
        "BSc Computer Science",
        "UCL",
        "",
        "",
        "",
        "n",
        "y",
        "Senior Software Engineer",
        "FinTech Corp",
        "",
        "",
        "Developed microservices in Python and SQL",
        "n",
        "Python, SQL, FastAPI, Docker",
        "y",
    ]
    with patch("builtins.input", side_effect=inputs):
        main(["--db-path", test_db_path, "profile", "create"])

    captured_out = StringIO()
    with patch("sys.stdout", captured_out):
        exit_code = main(["--db-path", test_db_path, "profile", "synthesize"])
    assert exit_code == 0
    output = captured_out.getvalue()
    assert "Synthesized Generalized Job Title" in output
    assert "Senior" in output or "Software Engineer" in output


def test_cli_search_config(test_db_path):
    # Setup profile
    inputs = [
        "David Clark",
        "david@example.com",
        "",
        "London",
        "",
        "y",
        "BSc CS",
        "UCL",
        "",
        "",
        "",
        "n",
        "n",
        "Python",
        "y",
    ]
    with patch("builtins.input", side_effect=inputs):
        main(["--db-path", test_db_path, "profile", "create"])

    # Configure search:
    # 1. Target locations
    # 2. Remote preference (2: REMOTE)
    # 3. Seniority (4: SENIOR)
    # 4. Min compensation
    # 5. Currency
    # 6. Min results
    # 7. Max results
    config_inputs = [
        "London, Remote",
        "2",
        "4",
        "85000",
        "GBP",
        "3",
        "7",
    ]
    with patch("builtins.input", side_effect=config_inputs):
        exit_code = main(["--db-path", test_db_path, "config", "set"])
        assert exit_code == 0

    # Show config
    captured_out = StringIO()
    with patch("sys.stdout", captured_out):
        exit_code = main(["--db-path", test_db_path, "config", "show"])
    assert exit_code == 0
    output = captured_out.getvalue()
    assert "London, Remote" in output
    assert "REMOTE" in output
    assert "3 to 7 postings" in output


def test_cli_profile_list_and_show(test_db_path):
    inputs = [
        "Alice Smith",
        "alice@example.com",
        "",
        "Berlin",
        "Python enthusiast",
        "n",
        "n",
        "Python",
        "y",
    ]
    with patch("builtins.input", side_effect=inputs):
        main(["--db-path", test_db_path, "profile", "create"])

    # Test profile list
    captured_out = StringIO()
    with patch("sys.stdout", captured_out):
        exit_code = main(["--db-path", test_db_path, "profile", "list"])
    assert exit_code == 0
    assert "Alice Smith" in captured_out.getvalue()

    # Test profile show
    captured_out = StringIO()
    with patch("sys.stdout", captured_out):
        exit_code = main(["--db-path", test_db_path, "profile", "show"])
    assert exit_code == 0
    assert "Alice Smith" in captured_out.getvalue()
    assert "Berlin" in captured_out.getvalue()


def test_cli_onboard_wizard(test_db_path):
    # Wizard runs:
    # 1. Profile questionnaire
    # 2. Synthesize title
    # 3. Search configuration setup
    wizard_inputs = [
        # Personal
        "Bob Taylor",
        "bob@example.com",
        "+4412345678",
        "Manchester, UK",
        "Backend engineer",
        # Education
        "y",
        "BSc Software Engineering",
        "Manchester",
        "2019-09",
        "2022-06",
        "",
        "n",
        # Experience
        "y",
        "Backend Developer",
        "CloudCo",
        "2022-07",
        "CURRENT",
        "Developed microservices in Python and SQL",
        "n",
        # Skills
        "Python, SQL, PostgreSQL, Docker",
        # Verify approval
        "y",
        # Search Config
        "Manchester, Remote",
        "1",  # ANY
        "3",  # MID
        "60000",
        "GBP",
        "2",  # min
        "8",  # max
    ]
    with patch("builtins.input", side_effect=wizard_inputs):
        exit_code = main(["--db-path", test_db_path, "onboard"])
    assert exit_code == 0

    conn = get_connection(test_db_path)
    profile_repo = ProfileRepository(conn)
    title_repo = TitleRepository(conn)
    config_repo = SearchConfigRepository(conn)

    profiles = profile_repo.list_profiles()
    assert len(profiles) == 1
    active_title = title_repo.get_active_title(profiles[0].id)
    assert active_title is not None
    cfg = config_repo.get_configuration(profiles[0].id)
    assert cfg is not None
    assert cfg.min_results_per_title == 2
    assert cfg.max_results_per_title == 8
    conn.close()
