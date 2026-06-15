"""Speech-to-text tests."""

import threading
from unittest.mock import MagicMock, patch

import pytest

from conftest import skip_non_darwin
from macbook_ai._exceptions import AuthorizationError, RecognitionError, UnavailableError

pytestmark = skip_non_darwin


# ---------------------------------------------------------------------------
# SpeechRecognizer.__init__
# ---------------------------------------------------------------------------

class TestInit:
    def test_raises_when_unavailable(self, monkeypatch):
        import macbook_ai.stt.recognizer as mod
        monkeypatch.setattr(mod, "_AVAILABLE", False)

        from macbook_ai.stt import SpeechRecognizer
        with pytest.raises(UnavailableError, match="pyobjc-framework-Speech"):
            SpeechRecognizer()

    def test_raises_for_unsupported_locale(self, mock_stt):
        mock_speech, mock_foundation = mock_stt
        mock_speech.SFSpeechRecognizer.alloc.return_value.initWithLocale_.return_value = None

        from macbook_ai.stt import SpeechRecognizer
        with pytest.raises(UnavailableError, match="locale"):
            SpeechRecognizer(locale="xx-XX")

    def test_stores_locale(self, mock_stt):
        mock_speech, _ = mock_stt
        from macbook_ai.stt import SpeechRecognizer
        r = SpeechRecognizer(locale="fr-FR")
        assert r.locale == "fr-FR"


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------

class TestAuthorization:
    def test_request_auth_raises_when_unavailable(self, monkeypatch):
        import macbook_ai.stt.recognizer as mod
        monkeypatch.setattr(mod, "_AVAILABLE", False)

        from macbook_ai.stt import SpeechRecognizer
        with pytest.raises(UnavailableError):
            SpeechRecognizer.request_authorization()

    def test_request_auth_returns_authorized(self, mock_stt):
        mock_speech, _ = mock_stt

        def fake_request(callback):
            callback(3)  # 3 = authorized

        mock_speech.SFSpeechRecognizer.requestAuthorization_ = fake_request

        from macbook_ai.stt import SpeechRecognizer
        assert SpeechRecognizer.request_authorization() == "authorized"

    def test_request_auth_returns_denied(self, mock_stt):
        mock_speech, _ = mock_stt

        def fake_request(callback):
            callback(1)  # 1 = denied

        mock_speech.SFSpeechRecognizer.requestAuthorization_ = fake_request

        from macbook_ai.stt import SpeechRecognizer
        assert SpeechRecognizer.request_authorization() == "denied"

    def test_authorization_status_raises_when_unavailable(self, monkeypatch):
        import macbook_ai.stt.recognizer as mod
        monkeypatch.setattr(mod, "_AVAILABLE", False)

        from macbook_ai.stt import SpeechRecognizer
        with pytest.raises(UnavailableError):
            SpeechRecognizer.authorization_status()

    def test_authorization_status_returns_string(self, mock_stt):
        mock_speech, _ = mock_stt
        mock_speech.SFSpeechRecognizer.authorizationStatus.return_value = 3

        from macbook_ai.stt import SpeechRecognizer
        assert SpeechRecognizer.authorization_status() == "authorized"


# ---------------------------------------------------------------------------
# recognize_file
# ---------------------------------------------------------------------------

class TestRecognizeFile:
    def _make_recognizer(self, mock_stt):
        mock_speech, _ = mock_stt
        mock_speech.SFSpeechRecognizer.authorizationStatus.return_value = 3
        from macbook_ai.stt import SpeechRecognizer
        return SpeechRecognizer()

    def test_raises_when_not_authorized(self, mock_stt, tmp_path):
        mock_speech, _ = mock_stt
        mock_speech.SFSpeechRecognizer.authorizationStatus.return_value = 1  # denied
        from macbook_ai.stt import SpeechRecognizer
        r = SpeechRecognizer()
        audio = tmp_path / "clip.wav"
        audio.write_bytes(b"RIFF")
        with pytest.raises(AuthorizationError):
            r.recognize_file(str(audio))

    def test_raises_for_missing_file(self, mock_stt):
        r = self._make_recognizer(mock_stt)
        with pytest.raises(FileNotFoundError):
            r.recognize_file("/does/not/exist.wav")

    def test_returns_transcription_on_success(self, mock_stt, tmp_path):
        mock_speech, mock_foundation = mock_stt
        audio = tmp_path / "clip.wav"
        audio.write_bytes(b"RIFF")

        best = MagicMock()
        best.formattedString.return_value = "hello world"
        result_mock = MagicMock()
        result_mock.isFinal.return_value = True
        result_mock.bestTranscription.return_value = best

        def fake_task(request, handler):
            handler(result_mock, None)
            return MagicMock()

        mock_speech.SFSpeechRecognizer.alloc.return_value.initWithLocale_.return_value\
            .recognitionTaskWithRequest_resultHandler_ = fake_task

        r = self._make_recognizer(mock_stt)
        text = r.recognize_file(str(audio))
        assert text == "hello world"

    def test_raises_recognition_error(self, mock_stt, tmp_path):
        mock_speech, _ = mock_stt
        audio = tmp_path / "clip.wav"
        audio.write_bytes(b"RIFF")

        def fake_task(request, handler):
            handler(None, "something went wrong")
            return MagicMock()

        mock_speech.SFSpeechRecognizer.alloc.return_value.initWithLocale_.return_value\
            .recognitionTaskWithRequest_resultHandler_ = fake_task

        r = self._make_recognizer(mock_stt)
        with pytest.raises(RecognitionError):
            r.recognize_file(str(audio))

    def test_raises_timeout(self, mock_stt, tmp_path):
        """Recognition that never fires the handler raises TimeoutError."""
        mock_speech, _ = mock_stt
        audio = tmp_path / "clip.wav"
        audio.write_bytes(b"RIFF")

        task_mock = MagicMock()

        def fake_task(request, handler):
            # handler never called → timeout
            return task_mock

        mock_speech.SFSpeechRecognizer.alloc.return_value.initWithLocale_.return_value\
            .recognitionTaskWithRequest_resultHandler_ = fake_task

        r = self._make_recognizer(mock_stt)
        with pytest.raises(TimeoutError):
            r.recognize_file(str(audio), timeout=0.01)

        task_mock.cancel.assert_called_once()

    def test_non_final_results_ignored(self, mock_stt, tmp_path):
        """Intermediate (non-final) results do not end recognition early."""
        mock_speech, _ = mock_stt
        audio = tmp_path / "clip.wav"
        audio.write_bytes(b"RIFF")

        calls = []

        def fake_task(request, handler):
            # first call: non-final; second call: final
            intermediate = MagicMock()
            intermediate.isFinal.return_value = False
            handler(intermediate, None)
            calls.append("intermediate")

            best = MagicMock()
            best.formattedString.return_value = "done"
            final = MagicMock()
            final.isFinal.return_value = True
            final.bestTranscription.return_value = best
            handler(final, None)
            return MagicMock()

        mock_speech.SFSpeechRecognizer.alloc.return_value.initWithLocale_.return_value\
            .recognitionTaskWithRequest_resultHandler_ = fake_task

        r = self._make_recognizer(mock_stt)
        assert r.recognize_file(str(audio)) == "done"
        assert "intermediate" in calls

    def test_empty_result_returns_empty_string(self, mock_stt, tmp_path):
        mock_speech, _ = mock_stt
        audio = tmp_path / "clip.wav"
        audio.write_bytes(b"RIFF")

        result_mock = MagicMock()
        result_mock.isFinal.return_value = True
        result_mock.bestTranscription.return_value.formattedString.return_value = ""

        def fake_task(request, handler):
            handler(result_mock, None)
            return MagicMock()

        mock_speech.SFSpeechRecognizer.alloc.return_value.initWithLocale_.return_value\
            .recognitionTaskWithRequest_resultHandler_ = fake_task

        r = self._make_recognizer(mock_stt)
        assert r.recognize_file(str(audio)) == ""


# ---------------------------------------------------------------------------
# recognize_file_async
# ---------------------------------------------------------------------------

class TestRecognizeFileAsync:
    async def test_async_delegates_to_sync(self, mock_stt, tmp_path):
        mock_speech, _ = mock_stt
        mock_speech.SFSpeechRecognizer.authorizationStatus.return_value = 3
        audio = tmp_path / "clip.wav"
        audio.write_bytes(b"RIFF")

        best = MagicMock()
        best.formattedString.return_value = "async result"
        result_mock = MagicMock()
        result_mock.isFinal.return_value = True
        result_mock.bestTranscription.return_value = best

        def fake_task(request, handler):
            handler(result_mock, None)
            return MagicMock()

        mock_speech.SFSpeechRecognizer.alloc.return_value.initWithLocale_.return_value\
            .recognitionTaskWithRequest_resultHandler_ = fake_task

        from macbook_ai.stt import SpeechRecognizer
        r = SpeechRecognizer()
        text = await r.recognize_file_async(str(audio))
        assert text == "async result"
