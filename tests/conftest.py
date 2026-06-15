"""Shared fixtures for macbook-ai tests.

All tests are macOS-only because the modules raise UnavailableError at import
time on other platforms. Mocking the PyObjC layer lets tests run without
triggering actual system dialogs or hardware access.
"""

import sys
import types
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Skip marker
# ---------------------------------------------------------------------------

skip_non_darwin = pytest.mark.skipif(
    sys.platform != "darwin", reason="macOS only"
)


# ---------------------------------------------------------------------------
# STT fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_stt(monkeypatch):
    """Replace the Speech and Foundation globals in the STT recognizer module."""
    import macbook_ai.stt.recognizer as mod

    mock_speech = MagicMock()
    mock_foundation = MagicMock()

    # Authorization status constants
    mock_speech.SFSpeechRecognizerAuthorizationStatusNotDetermined = 0
    mock_speech.SFSpeechRecognizerAuthorizationStatusDenied = 1
    mock_speech.SFSpeechRecognizerAuthorizationStatusRestricted = 2
    mock_speech.SFSpeechRecognizerAuthorizationStatusAuthorized = 3

    monkeypatch.setattr(mod, "Speech", mock_speech)
    monkeypatch.setattr(mod, "Foundation", mock_foundation)
    monkeypatch.setattr(mod, "_AVAILABLE", True)
    monkeypatch.setattr(
        mod,
        "_AUTH_STATUS",
        {0: "not_determined", 1: "denied", 2: "restricted", 3: "authorized"},
    )

    # Mock NSRunLoop so the loop body is a no-op
    mock_foundation.NSRunLoop.currentRunLoop.return_value.runUntilDate_ = MagicMock()
    mock_foundation.NSDate.dateWithTimeIntervalSinceNow_ = MagicMock()

    return mock_speech, mock_foundation


# ---------------------------------------------------------------------------
# TTS fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_tts(monkeypatch):
    """Replace AVFoundation and Foundation globals in the TTS synthesizer module."""
    import macbook_ai.tts.synthesizer as mod

    mock_av = MagicMock()
    mock_foundation = MagicMock()

    mock_foundation.NSRunLoop.currentRunLoop.return_value.runUntilDate_ = MagicMock()
    mock_foundation.NSDate.dateWithTimeIntervalSinceNow_ = MagicMock()

    monkeypatch.setattr(mod, "AVSpeechSynthesizer", mock_av.AVSpeechSynthesizer)
    monkeypatch.setattr(mod, "AVSpeechUtterance", mock_av.AVSpeechUtterance)
    monkeypatch.setattr(mod, "AVSpeechSynthesisVoice", mock_av.AVSpeechSynthesisVoice)
    monkeypatch.setattr(mod, "AVAudioFile", mock_av.AVAudioFile)
    monkeypatch.setattr(mod, "Foundation", mock_foundation)
    monkeypatch.setattr(mod, "_AVAILABLE", True)

    return mock_av, mock_foundation


# ---------------------------------------------------------------------------
# Foundation model fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_fm(monkeypatch):
    """Replace the FoundationModels globals in the model module."""
    import macbook_ai.foundation.model as mod

    mock_fm_module = MagicMock()
    mock_model = MagicMock()
    mock_fm_module.FMSystemLanguageModel.defaultModel.return_value = mock_model

    monkeypatch.setattr(mod, "_FM", mock_fm_module)
    monkeypatch.setattr(mod, "_AVAILABLE", True)
    monkeypatch.setattr(mod, "_DEFAULT_MODEL", mock_model)

    return mock_fm_module, mock_model
