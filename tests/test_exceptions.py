"""Exception hierarchy tests."""

import pytest

from macbook_ai._exceptions import (
    AuthorizationError,
    InferenceError,
    MacAIError,
    RecognitionError,
    SynthesisError,
    UnavailableError,
)


def test_unavailable_is_mac_ai_error():
    assert issubclass(UnavailableError, MacAIError)


def test_authorization_is_mac_ai_error():
    assert issubclass(AuthorizationError, MacAIError)


def test_recognition_is_mac_ai_error():
    assert issubclass(RecognitionError, MacAIError)


def test_synthesis_is_mac_ai_error():
    assert issubclass(SynthesisError, MacAIError)


def test_inference_is_mac_ai_error():
    assert issubclass(InferenceError, MacAIError)


def test_all_catchable_as_mac_ai_error():
    for cls in (UnavailableError, AuthorizationError, RecognitionError, SynthesisError, InferenceError):
        with pytest.raises(MacAIError):
            raise cls("test")


def test_messages_preserved():
    err = RecognitionError("something went wrong")
    assert "something went wrong" in str(err)
