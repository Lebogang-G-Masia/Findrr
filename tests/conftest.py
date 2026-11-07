"""Pytest configuration and global fixtures."""

import os

# Ensure tests default to mock inference unless explicitly overridden
os.environ.setdefault("FINDRR_MOCK_INFERENCE", "true")
