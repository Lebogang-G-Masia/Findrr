"""Abstract base class for machine learning model execution runners."""

from abc import ABC, abstractmethod


class IModelRunner(ABC):
    """Lifecycle contract for server-side model runners."""

    @abstractmethod
    def load(self) -> None:
        """Load model weights, tokenizers, and configs into memory."""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Unload model from memory and perform resource cleanup."""
        pass

    @abstractmethod
    def is_loaded(self) -> bool:
        """Return True if model is currently resident in memory."""
        pass

    @property
    @abstractmethod
    def is_mock(self) -> bool:
        """Return True if this runner represents a simulated mock rather than real weights."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Return the active model version string."""
        pass
