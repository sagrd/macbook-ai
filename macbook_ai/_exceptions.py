"""Package-wide exception hierarchy."""


class MacAIError(Exception):
    """Base exception for all macai errors."""


class UnavailableError(MacAIError):
    """Raised when a capability or its dependencies are not available."""


class AuthorizationError(MacAIError):
    """Raised when the required system permission has not been granted."""


class RecognitionError(MacAIError):
    """Raised when speech recognition fails."""


class SynthesisError(MacAIError):
    """Raised when speech synthesis fails."""


class InferenceError(MacAIError):
    """Raised when on-device LLM inference fails."""
