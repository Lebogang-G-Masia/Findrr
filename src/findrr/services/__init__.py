"""Service layer package."""

from findrr.services.application_service import ApplicationService
from findrr.services.document_generator import DocumentGenerator
from findrr.services.fact_matcher import FactMatcher
from findrr.services.grounding_validator import FabricationDetectedError, FactGroundingValidator
from findrr.services.inference_service import (
    InferenceService,
    SimilarityResult,
    TitleExpansionResult,
    ValidatedCandidate,
)
from findrr.services.posting_service import PostingService
from findrr.services.profile_service import ProfileService
from findrr.services.search_config_service import SearchConfigService
from findrr.services.synthesizer import InsufficientProfileDataError, TitleSynthesizer

__all__ = [
    "ProfileService",
    "SearchConfigService",
    "TitleSynthesizer",
    "InsufficientProfileDataError",
    "InferenceService",
    "TitleExpansionResult",
    "SimilarityResult",
    "ValidatedCandidate",
    "PostingService",
    "ApplicationService",
    "FactMatcher",
    "FactGroundingValidator",
    "FabricationDetectedError",
    "DocumentGenerator",
]
