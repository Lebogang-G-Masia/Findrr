"""Exceptions for machine learning model management and inference (Module 9)."""


class FindrrError(Exception):
    """Base exception for all Findrr application errors."""

    pass


class ModelError(FindrrError):
    """Base exception for machine learning model errors."""

    pass


class ModelNotConfiguredError(ModelError):
    """Raised when an unconfigured or unrecognized model ID is requested."""

    pass


class ModelArtifactMissingError(ModelError):
    """Raised when one or more required model files are absent from disk."""

    def __init__(self, model_id: str, missing_files: list[str], path: str):
        self.model_id = model_id
        self.missing_files = missing_files
        self.path = path
        missing_str = ", ".join(missing_files)
        super().__init__(
            f"Model '{model_id}' cannot be loaded: missing required file(s) [{missing_str}] "
            f"in storage path '{path}'. Run Kaggle notebook and supply verified artifacts."
        )


class ModelIntegrityError(ModelError):
    """Raised when a model file's computed cryptographic hash mismatches manifest.json."""

    def __init__(self, model_id: str, file_name: str, expected_hash: str, actual_hash: str):
        self.model_id = model_id
        self.file_name = file_name
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
        super().__init__(
            f"Model integrity violation for '{model_id}' on file '{file_name}': "
            f"computed SHA-256 '{actual_hash}' does not match manifest '{expected_hash}'."
        )


class InferenceExecutionError(ModelError):
    """Raised when model inference execution fails during prediction or post-processing."""

    pass
