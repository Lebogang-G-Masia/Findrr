"""Runtime configuration values read from the environment (and `.env`, loaded by the CLI).

Numeric thresholds here are PROVISIONAL (BR-006): they ship as configuration defaults
until evaluated and approved, and can be overridden without code changes.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# PROVISIONAL (FR-010): minimum cosine similarity for a generated title to be accepted.
DEFAULT_RELEVANCE_THRESHOLD = 0.70
# PROVISIONAL (FR-011): similarity at or above which a title is a near-duplicate.
DEFAULT_DEDUP_THRESHOLD = 0.88


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = float(raw)
    except ValueError:
        logger.error("Invalid %s=%r (not a number); using default %s", name, raw, default)
        return default
    if not 0.0 <= value <= 1.0:
        logger.error("Invalid %s=%r (must be 0-1); using default %s", name, raw, default)
        return default
    return value


def relevance_threshold() -> float:
    """Return the configured relevance threshold (env FINDRR_RELEVANCE_THRESHOLD)."""
    return _float_env("FINDRR_RELEVANCE_THRESHOLD", DEFAULT_RELEVANCE_THRESHOLD)


def dedup_threshold() -> float:
    """Return the configured near-duplicate threshold (env FINDRR_DEDUP_THRESHOLD)."""
    return _float_env("FINDRR_DEDUP_THRESHOLD", DEFAULT_DEDUP_THRESHOLD)


def max_accepted_terms() -> Optional[int]:
    """Optional cap on accepted search terms per run (env FINDRR_MAX_ACCEPTED_TERMS).

    No default: the Module 3 spec requires a maximum, but no value has been evaluated or
    approved, so none is invented. Unset means no cap beyond what Model 1 returns.
    """
    raw = os.getenv("FINDRR_MAX_ACCEPTED_TERMS")
    if raw is None or raw.strip() == "":
        return None
    try:
        value = int(raw)
    except ValueError:
        logger.error("Invalid FINDRR_MAX_ACCEPTED_TERMS=%r (not an integer); no cap applied", raw)
        return None
    if value < 1:
        logger.error("Invalid FINDRR_MAX_ACCEPTED_TERMS=%r (must be >= 1); no cap applied", raw)
        return None
    return value
