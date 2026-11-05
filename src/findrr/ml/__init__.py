"""Machine Learning and Model Management Package (Module 9)."""

from findrr.ml.base import IModelRunner
from findrr.ml.exceptions import (
    FindrrError,
    InferenceExecutionError,
    ModelArtifactMissingError,
    ModelError,
    ModelIntegrityError,
    ModelNotConfiguredError,
)
from findrr.ml.manifest import (
    ModelManifest,
    compute_sha256,
    load_manifest,
    verify_artifact_integrity,
)
from findrr.ml.registry import ModelRegistration, ModelRegistry
from findrr.ml.similarity_evaluator_runner import (
    MockSimilarityEvaluatorRunner,
    SimilarityEvaluatorRunner,
)
from findrr.ml.title_expander_runner import (
    MockTitleExpanderRunner,
    TitleExpanderRunner,
)

__all__ = [
    "IModelRunner",
    "FindrrError",
    "ModelError",
    "ModelNotConfiguredError",
    "ModelArtifactMissingError",
    "ModelIntegrityError",
    "InferenceExecutionError",
    "ModelManifest",
    "compute_sha256",
    "load_manifest",
    "verify_artifact_integrity",
    "ModelRegistration",
    "ModelRegistry",
    "MockTitleExpanderRunner",
    "TitleExpanderRunner",
    "MockSimilarityEvaluatorRunner",
    "SimilarityEvaluatorRunner",
]
