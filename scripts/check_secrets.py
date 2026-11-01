#!/usr/bin/env python3
"""Basic pattern-based secret scanner for local pre-commit and CI sanity checks."""

import os
import re
import sys

SUSPICIOUS_PATTERNS = [
    (re.compile(r"(?i)ghp_[0-9a-zA-Z]{36}"), "GitHub Personal Access Token"),
    (re.compile(r"(?i)gho_[0-9a-zA-Z]{36}"), "GitHub OAuth Token"),
    (re.compile(r"(?i)glpat-[0-9a-zA-Z\-_]{20}"), "GitLab Personal Access Token"),
    (re.compile(r"(?i)xox[baprs]-[0-9a-zA-Z]{10,48}"), "Slack Token"),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "Private Key"),
    (re.compile(r"(?i)aws_access_key_id\s*=\s*['\"][A-Z0-9]{20}['\"]"), "AWS Access Key"),
    (re.compile(r"(?i)aws_secret_access_key\s*=\s*['\"][A-Za-z0-9/+=]{40}['\"]"), "AWS Secret Key"),
    (
        re.compile(
            r"(?i)(?:api_key|apikey|secret_key|private_key)"
            r"\s*=\s*['\"][0-9a-zA-Z_\-]{20,}['\"]"
        ),
        "Generic API Key/Secret",
    ),
]

IGNORED_DIRS = {".git", ".venv", "venv", "__pycache__"}
IGNORED_FILES = {".env.example"}


def check_secrets(root_dir="."):
    violations = []

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for file_name in files:
            if file_name in IGNORED_FILES:
                continue

            path = os.path.join(root, file_name)

            # Skip binary or very large files
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        for pattern, desc in SUSPICIOUS_PATTERNS:
                            if pattern.search(line):
                                violations.append(f"{desc} detected at {path}:{line_num}")
            except OSError as e:
                violations.append(f"Could not read {path}: {e}")

    if violations:
        print("CI Secret Scan FAILED:")
        for v in violations:
            print(f"  - {v}")
        return 1

    print("CI Secret Scan PASSED: No exposed secrets or private keys found.")
    return 0


if __name__ == "__main__":
    sys.exit(check_secrets())
