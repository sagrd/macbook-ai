"""macOS AVSpeechSynthesizer wrapper."""

from __future__ import annotations

import asyncio
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from .._exceptions import SynthesisError, UnavailableError

if sys.platform != "darwin":
    raise UnavailableError("macbook-ai requires macOS")

try:
    from AVFoundation import (
        AVAudioFile,
        AVSpeechSynthesisVoice,
        AVSpeechSynthesizer,
        AVSpeechUtterance,
    )

    import Foundation

    _AVAILABLE = True
except ImportError:
    AVAudioFile = None  # type: ignore[assignment,misc]
    AVSpeechSynthesisVoice = None  # type: ignore[assignment,misc]
    AVSpeechSynthesizer = None  # type: ignore[assignment,misc]
    AVSpeechUtterance = None  # type: ignore[assignment,misc]
    Foundation = None  # type: ignore[assignment]
    _AVAILABLE = False


class SpeechSynthesizer:
    """
    Synthesize speech using the macOS AVSpeechSynthesizer framework.

    Requires ``pip install 'macbook-ai[tts]'``.

    Usage::

        synth = SpeechSynthesizer()
        synth.speak("Hello from macbook-ai")

        # with a specific voice
        synth = SpeechSynthesizer(voice="com.apple.voice.compact.en-US.Samantha")

        # async
        await synth.speak_async("Hello")

        # save to file
        synth.save_to_file("Hello", "output.caf")
    """

    def __init__(
        self,
        voice: Optional[str] = None,
        rate: float = 0.5,
        volume: float = 1.0,
    ) -> None:
        """
        :param voice: AVSpeechSynthesisVoice identifier, or ``None`` for the system default.
                      Call :meth:`available_voices` to list valid identifiers.
        :param rate: Speaking rate, 0.0 (slowest) to 1.0 (fastest). Default 0.5.
        :param volume: Volume, 0.0 to 1.0. Default 1.0.
        """
        if not _AVAILABLE:
            raise UnavailableError(
                "pyobjc-framework-AVFoundation is required. "
                "Install with: pip install 'macbook-ai[tts]'"
            )
        if voice is not None:
            resolved = AVSpeechSynthesisVoice.voiceWithIdentifier_(voice)
            if resolved is None:
                raise UnavailableError(
                    f"Voice '{voice}' not found. "
                    "Call SpeechSynthesizer.available_voices() for valid identifiers."
                )
        self._synth = AVSpeechSynthesizer.alloc().init()
        self._voice_id = voice
        self._rate = rate
        self._volume = volume

    # ------------------------------------------------------------------
    # Voices
    # ------------------------------------------------------------------

    @staticmethod
    def available_voices(language: Optional[str] = None) -> list[dict]:
        """
        Return all installed voices as dicts with ``identifier``, ``name``, ``language``.

        :param language: Optional BCP-47 prefix to filter by (e.g. ``'en'``, ``'fr-FR'``).
        """
        if not _AVAILABLE:
            raise UnavailableError(
                "pyobjc-framework-AVFoundation is required. "
                "Install with: pip install 'macbook-ai[tts]'"
            )
        result = []
        for v in AVSpeechSynthesisVoice.speechVoices():
            lang = str(v.language())
            if language and not lang.startswith(language):
                continue
            result.append(
                {
                    "identifier": str(v.identifier()),
                    "name": str(v.name()),
                    "language": lang,
                }
            )
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_utterance(self, text: str) -> "AVSpeechUtterance":
        utterance = AVSpeechUtterance.speechUtteranceWithString_(text)
        if self._voice_id is not None:
            utterance.setVoice_(AVSpeechSynthesisVoice.voiceWithIdentifier_(self._voice_id))
        utterance.setRate_(self._rate)
        utterance.setVolume_(self._volume)
        return utterance

    # ------------------------------------------------------------------
    # Synthesis
    # ------------------------------------------------------------------

    def speak(self, text: str) -> None:
        """Speak *text* and block until audio playback is complete."""
        utterance = self._make_utterance(text)
        self._synth.speakUtterance_(utterance)
        while self._synth.isSpeaking():
            Foundation.NSRunLoop.currentRunLoop().runUntilDate_(
                Foundation.NSDate.dateWithTimeIntervalSinceNow_(0.05)
            )

    async def speak_async(self, text: str) -> None:
        """Async version of :meth:`speak`."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.speak, text)

    def save_to_file(
        self,
        text: str,
        output_path: str | Path,
        timeout: float = 60.0,
    ) -> None:
        """
        Synthesize *text* and write it to *output_path* as a CAF audio file.

        :param output_path: Destination path; ``.caf`` extension recommended.
        :param timeout: Maximum seconds to wait before raising ``TimeoutError``.
        :raises SynthesisError: If the audio file cannot be created.
        :raises TimeoutError: If synthesis does not complete within *timeout*.
        """
        output_path = Path(output_path).resolve()
        utterance = self._make_utterance(text)

        buffers: list = []
        done = threading.Event()

        def _callback(buffer) -> None:
            if buffer.frameLength() == 0:
                done.set()
            else:
                buffers.append(buffer)

        self._synth.writeUtterance_toBufferCallback_(utterance, _callback)

        deadline = time.monotonic() + timeout
        while not done.is_set():
            if time.monotonic() >= deadline:
                raise TimeoutError(f"save_to_file timed out after {timeout}s")
            Foundation.NSRunLoop.currentRunLoop().runUntilDate_(
                Foundation.NSDate.dateWithTimeIntervalSinceNow_(0.05)
            )

        if not buffers:
            return

        url = Foundation.NSURL.fileURLWithPath_(str(output_path))
        audio_format = buffers[0].format()
        audio_file = AVAudioFile.alloc().initForWriting_settings_error_(
            url, audio_format.settings(), None
        )
        if audio_file is None:
            raise SynthesisError(f"Could not create audio file at {output_path}")

        for buf in buffers:
            audio_file.writeFromBuffer_error_(buf, None)
