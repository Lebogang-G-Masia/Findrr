"""Pytest configuration and global fixtures."""

import os

# Ensure tests default to mock inference unless explicitly overridden
os.environ.setdefault("FINDRR_MOCK_INFERENCE", "true")
# Ensure tests write application documents to writable temporary path
os.environ.setdefault("FINDRR_DOCS_DIR", "/tmp/findrr_test_docs")
# Ensure tests write browser profile to writable temporary path
os.environ.setdefault("FINDRR_CHROME_PROFILE_DIR", "/tmp/findrr_test_chrome_profile")
