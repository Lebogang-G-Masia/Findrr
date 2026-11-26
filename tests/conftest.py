"""Pytest configuration and global fixtures."""
import os

import pytest

# Ensure tests default to mock inference unless explicitly overridden
os.environ.setdefault("FINDRR_MOCK_INFERENCE", "true")
# Ensure tests write application documents to writable temporary path
os.environ.setdefault("FINDRR_DOCS_DIR", "/tmp/findrr_test_docs")
# Ensure tests write browser profile to writable temporary path
os.environ.setdefault("FINDRR_CHROME_PROFILE_DIR", "/tmp/findrr_test_chrome_profile")


@pytest.fixture(autouse=True)
def _isolate_environment():
    """Restore os.environ after each test.

    The CLI loads a local `.env` (python-dotenv) into the process environment; without this,
    values from a developer's .env (e.g. FINDRR_MODELS_DIR) leak into later tests.
    """
    import os

    saved = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(saved)
