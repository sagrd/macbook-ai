"""Text-to-speech tests."""

import threading
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from conftest import skip_non_darwin
from macbook_ai._exceptions import SynthesisError, UnavailableError

pytestmark = skip_non_darwin


# ---------------------------------------------------------------------------
# SpeechSynthesizer.__init__
# ---------------------------------------------------------------------------

class TestInit:
    def test_raises_when_unavailable(self, monkeypatch):
        import macbook_ai.tts.synthesizer as mod
        monkeypatch.setattr(mod, "_AVAILABLE", False)

        from macbook_ai.tts import SpeechSynthesizer
        with pytest.raises(UnavailableError, match="pyobjc-framework-AVFoundation"):
            SpeechSynthesizer()

    def test_raises_for_unknown_voice(self, mock_tts):
        mock_av, _ = mock_tts
        mock_av.AVSpeechSynthesisVoice.voiceWithIdentifier_.return_value = None

        from macbook_ai.tts import SpeechSynthesizer
        with pytest.raises(UnavailableError, match="Voice"):
            SpeechSynthesizer(voice="com.invalid.voice")

    def test_accepts_valid_voice(self, mock_tts):
        mock_av, _ = mock_tts
        mock_av.AVSpeechSynthesisVoice.voiceWithIdentifier_.return_value = MagicMock()

        from macbook_ai.tts import SpeechSynthesizer
        synth = SpeechSynthesizer(voice="com.apple.voice.compact.en-US.Samantha")
        assert synth._voice_id == "com.apple.voice.compact.en-US.Samantha"

    def test_default_rate_and_volume(self, mock_tts):
        from macbook_ai.tts import SpeechSynthesizer
        synth = SpeechSynthesizer()
        assert synth._rate == 0.5
        assert synth._volume == 1.0

    def test_custom_rate_and_volume(self, mock_tts):
        from macbook_ai.tts import SpeechSynthesizer
        synth = SpeechSynthesizer(rate=0.3, volume=0.8)
        assert synth._rate == 0.3
        assert synth._volume == 0.8


# ---------------------------------------------------------------------------
# available_voices
# ---------------------------------------------------------------------------

class TestAvailableVoices:
    def test_raises_when_unavailable(self, monkeypatch):
        import macbook_ai.tts.synthesizer as mod
        monkeypatch.setattr(mod, "_AVAILABLE", False)

        from macbook_ai.tts import SpeechSynthesizer
        with pytest.raises(UnavailableError):
            SpeechSynthesizer.available_voices()

    def test_returns_list_of_dicts(self, mock_tts):
        mock_av, _ = mock_tts
        v1 = MagicMock()
        v1.identifier.return_value = "com.apple.voice.compact.en-US.Samantha"
        v1.name.return_value = "Samantha"
        v1.language.return_value = "en-US"

        v2 = MagicMock()
        v2.identifier.return_value = "com.apple.voice.compact.fr-FR.Thomas"
        v2.name.return_value = "Thomas"
        v2.language.return_value = "fr-FR"

        mock_av.AVSpeechSynthesisVoice.speechVoices.return_value = [v1, v2]

        from macbook_ai.tts import SpeechSynthesizer
        voices = SpeechSynthesizer.available_voices()

        assert len(voices) == 2
        assert voices[0] == {
            "identifier": "com.apple.voice.compact.en-US.Samantha",
            "name": "Samantha",
            "language": "en-US",
        }

    def test_filters_by_language_prefix(self, mock_tts):
        mock_av, _ = mock_tts
        v_en = MagicMock()
        v_en.identifier.return_value = "en-id"
        v_en.name.return_value = "Samantha"
        v_en.language.return_value = "en-US"

        v_fr = MagicMock()
        v_fr.identifier.return_value = "fr-id"
        v_fr.name.return_value = "Thomas"
        v_fr.language.return_value = "fr-FR"

        mock_av.AVSpeechSynthesisVoice.speechVoices.return_value = [v_en, v_fr]

        from macbook_ai.tts import SpeechSynthesizer
        voices = SpeechSynthesizer.available_voices(language="en")
        assert len(voices) == 1
        assert voices[0]["language"] == "en-US"

    def test_no_filter_returns_all(self, mock_tts):
        mock_av, _ = mock_tts
        voices_data = []
        for lang in ("en-US", "fr-FR", "ja-JP", "es-ES"):
            v = MagicMock()
            v.identifier.return_value = f"id-{lang}"
            v.name.return_value = f"name-{lang}"
            v.language.return_value = lang
            voices_data.append(v)

        mock_av.AVSpeechSynthesisVoice.speechVoices.return_value = voices_data

        from macbook_ai.tts import SpeechSynthesizer
        assert len(SpeechSynthesizer.available_voices()) == 4


# ---------------------------------------------------------------------------
# speak
# ---------------------------------------------------------------------------

class TestSpeak:
    def test_speak_calls_speakUtterance(self, mock_tts):
        mock_av, mock_foundation = mock_tts
        synth_instance = MagicMock()
        synth_instance.isSpeaking.side_effect = [True, True, False]
        mock_av.AVSpeechSynthesizer.alloc.return_value.init.return_value = synth_instance

        from macbook_ai.tts import SpeechSynthesizer
        s = SpeechSynthesizer()
        s.speak("Hello")

        synth_instance.speakUtterance_.assert_called_once()

    def test_speak_waits_until_done(self, mock_tts):
        """isSpeaking is polled until it returns False."""
        mock_av, _ = mock_tts
        synth_instance = MagicMock()
        # Returns True twice before finishing
        synth_instance.isSpeaking.side_effect = [True, True, False]
        mock_av.AVSpeechSynthesizer.alloc.return_value.init.return_value = synth_instance

        from macbook_ai.tts import SpeechSynthesizer
        s = SpeechSynthesizer()
        s.speak("Hello")

        assert synth_instance.isSpeaking.call_count == 3

    def test_utterance_uses_custom_rate(self, mock_tts):
        mock_av, _ = mock_tts
        utterance_mock = MagicMock()
        mock_av.AVSpeechUtterance.speechUtteranceWithString_.return_value = utterance_mock
        synth_instance = MagicMock()
        synth_instance.isSpeaking.return_value = False
        mock_av.AVSpeechSynthesizer.alloc.return_value.init.return_value = synth_instance

        from macbook_ai.tts import SpeechSynthesizer
        s = SpeechSynthesizer(rate=0.8)
        s.speak("test")

        utterance_mock.setRate_.assert_called_once_with(0.8)

    def test_utterance_uses_custom_volume(self, mock_tts):
        mock_av, _ = mock_tts
        utterance_mock = MagicMock()
        mock_av.AVSpeechUtterance.speechUtteranceWithString_.return_value = utterance_mock
        synth_instance = MagicMock()
        synth_instance.isSpeaking.return_value = False
        mock_av.AVSpeechSynthesizer.alloc.return_value.init.return_value = synth_instance

        from macbook_ai.tts import SpeechSynthesizer
        s = SpeechSynthesizer(volume=0.5)
        s.speak("test")

        utterance_mock.setVolume_.assert_called_once_with(0.5)

    def test_utterance_sets_voice_when_provided(self, mock_tts):
        mock_av, _ = mock_tts
        voice_mock = MagicMock()
        mock_av.AVSpeechSynthesisVoice.voiceWithIdentifier_.return_value = voice_mock
        utterance_mock = MagicMock()
        mock_av.AVSpeechUtterance.speechUtteranceWithString_.return_value = utterance_mock
        synth_instance = MagicMock()
        synth_instance.isSpeaking.return_value = False
        mock_av.AVSpeechSynthesizer.alloc.return_value.init.return_value = synth_instance

        from macbook_ai.tts import SpeechSynthesizer
        s = SpeechSynthesizer(voice="com.apple.voice.compact.en-US.Samantha")
        s.speak("test")

        utterance_mock.setVoice_.assert_called_once_with(voice_mock)

    def test_no_voice_set_on_utterance_when_none(self, mock_tts):
        mock_av, _ = mock_tts
        utterance_mock = MagicMock()
        mock_av.AVSpeechUtterance.speechUtteranceWithString_.return_value = utterance_mock
        synth_instance = MagicMock()
        synth_instance.isSpeaking.return_value = False
        mock_av.AVSpeechSynthesizer.alloc.return_value.init.return_value = synth_instance

        from macbook_ai.tts import SpeechSynthesizer
        s = SpeechSynthesizer()
        s.speak("test")

        utterance_mock.setVoice_.assert_not_called()


# ---------------------------------------------------------------------------
# speak_async
# ---------------------------------------------------------------------------

class TestSpeakAsync:
    async def test_speak_async_delegates_to_speak(self, mock_tts):
        mock_av, _ = mock_tts
        synth_instance = MagicMock()
        synth_instance.isSpeaking.return_value = False
        mock_av.AVSpeechSynthesizer.alloc.return_value.init.return_value = synth_instance

        from macbook_ai.tts import SpeechSynthesizer
        s = SpeechSynthesizer()
        await s.speak_async("Hello async")

        synth_instance.speakUtterance_.assert_called_once()


# ---------------------------------------------------------------------------
# save_to_file
# ---------------------------------------------------------------------------

class TestSaveToFile:
    def _make_buffer(self, frame_length: int):
        buf = MagicMock()
        buf.frameLength.return_value = frame_length
        buf.format.return_value = MagicMock()
        buf.format.return_value.settings.return_value = {}
        return buf

    def test_writes_buffers_to_audio_file(self, mock_tts, tmp_path):
        mock_av, mock_foundation = mock_tts
        synth_instance = MagicMock()
        mock_av.AVSpeechSynthesizer.alloc.return_value.init.return_value = synth_instance

        buf1 = self._make_buffer(1024)
        buf2 = self._make_buffer(512)
        sentinel = self._make_buffer(0)  # signals end

        audio_file_mock = MagicMock()
        mock_av.AVAudioFile.alloc.return_value.initForWriting_settings_error_.return_value = (
            audio_file_mock
        )

        def fake_write(utterance, callback):
            callback(buf1)
            callback(buf2)
            callback(sentinel)

        synth_instance.writeUtterance_toBufferCallback_ = fake_write

        from macbook_ai.tts import SpeechSynthesizer
        s = SpeechSynthesizer()
        out = tmp_path / "out.caf"
        s.save_to_file("Hello", str(out))

        assert audio_file_mock.writeFromBuffer_error_.call_count == 2

    def test_raises_synthesis_error_if_file_creation_fails(self, mock_tts, tmp_path):
        mock_av, _ = mock_tts
        synth_instance = MagicMock()
        mock_av.AVSpeechSynthesizer.alloc.return_value.init.return_value = synth_instance

        buf = self._make_buffer(1024)
        sentinel = self._make_buffer(0)

        def fake_write(utterance, callback):
            callback(buf)
            callback(sentinel)

        synth_instance.writeUtterance_toBufferCallback_ = fake_write
        mock_av.AVAudioFile.alloc.return_value.initForWriting_settings_error_.return_value = None

        from macbook_ai.tts import SpeechSynthesizer
        from macbook_ai._exceptions import SynthesisError
        s = SpeechSynthesizer()
        with pytest.raises(SynthesisError):
            s.save_to_file("Hello", str(tmp_path / "out.caf"))

    def test_timeout_raises(self, mock_tts, tmp_path):
        mock_av, _ = mock_tts
        synth_instance = MagicMock()
        mock_av.AVSpeechSynthesizer.alloc.return_value.init.return_value = synth_instance

        # callback never fired → timeout
        synth_instance.writeUtterance_toBufferCallback_ = MagicMock()

        from macbook_ai.tts import SpeechSynthesizer
        s = SpeechSynthesizer()
        with pytest.raises(TimeoutError):
            s.save_to_file("Hello", str(tmp_path / "out.caf"), timeout=0.01)

    def test_no_buffers_returns_without_writing(self, mock_tts, tmp_path):
        """If only the sentinel (zero-length) buffer arrives, no file is written."""
        mock_av, _ = mock_tts
        synth_instance = MagicMock()
        mock_av.AVSpeechSynthesizer.alloc.return_value.init.return_value = synth_instance

        sentinel = self._make_buffer(0)

        def fake_write(utterance, callback):
            callback(sentinel)

        synth_instance.writeUtterance_toBufferCallback_ = fake_write

        from macbook_ai.tts import SpeechSynthesizer
        s = SpeechSynthesizer()
        # Should not raise
        s.save_to_file("", str(tmp_path / "out.caf"))
        mock_av.AVAudioFile.alloc.assert_not_called()
