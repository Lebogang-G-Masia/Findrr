#!/usr/bin/env python3
"""Check that no files exceed the maximum allowed size or contain forbidden binary ML artifacts."""

import os
import sys

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
FORBIDDEN_EXTENSIONS = {
    ".pt",
    ".pth",
    ".bin",
    ".safetensors",
    ".onnx",
    ".h5",
    ".tflite",
    ".mlmodel",
    ".pkl",
    ".joblib",
}

IGNORED_DIRS = {".git", ".venv", "venv", "__pycache__"}


def check_files(root_dir="."):
    violations = []

    for root, dirs, files in os.walk(root_dir):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for file_name in files:
            path = os.path.join(root, file_name)
            ext = os.path.splitext(file_name)[1].lower()

            if ext in FORBIDDEN_EXTENSIONS:
                violations.append(f"Forbidden ML model/binary artifact extension '{ext}': {path}")

            try:
                size = os.path.getsize(path)
                if size > MAX_FILE_SIZE_BYTES:
                    violations.append(
                        f"File size exceeds limit ({size / (1024*1024):.2f} MB > 5 MB): {path}"
                    )
            except OSError as e:
                violations.append(f"Could not check file size for {path}: {e}")

    if violations:
        print("CI File-Size & Artifact Check FAILED:")
        for v in violations:
            print(f"  - {v}")
        return 1

    print("CI File-Size & Artifact Check PASSED: No oversized files or binary model weights found.")
    return 0


if __name__ == "__main__":
    sys.exit(check_files())
