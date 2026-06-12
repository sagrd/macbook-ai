"""macOS SFSpeechRecognizer wrapper."""

from __future__ import annotations

import asyncio
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from .._exceptions import AuthorizationError, RecognitionError, UnavailableError

if sys.platform != "darwin":
    raise UnavailableError("macbook-ai requires macOS")

try:
    import Foundation
    import Speech

    _AUTH_STATUS: dict[int, str] = {
        Speech.SFSpeechRecognizerAuthorizationStatusNotDetermined: "not_determined",
        Speech.SFSpeechRecognizerAuthorizationStatusDenied: "denied",
        Speech.SFSpeechRecognizerAuthorizationStatusRestricted: "restricted",
        Speech.SFSpeechRecognizerAuthorizationStatusAuthorized: "authorized",
    }
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False
    _AUTH_STATUS = {}


class SpeechRecognizer:
    """
    Transcribe audio files using the macOS Speech framework (SFSpeechRecognizer).

    Requires `pip install 'macbook-ai[stt]'` and Speech Recognition permission in
    System Settings > Privacy & Security > Speech Recognition.

    Usage::

        recognizer = SpeechRecognizer()
        text = recognizer.recognize_file("audio.m4a")

        # or async
        text = await recognizer.recognize_file_async("audio.m4a")
    """

    def __init__(self, locale: str = "en-US") -> None:
        if not _AVAILABLE:
            raise UnavailableError(
                "pyobjc-framework-Speech is required. "
                "Install with: pip install 'macbook-ai[stt]'"
            )
        locale_obj = Foundation.NSLocale.alloc().initWithLocaleIdentifier_(locale)
        self._recognizer = Speech.SFSpeechRecognizer.alloc().initWithLocale_(locale_obj)
        if self._recognizer is None:
            raise UnavailableError(
                f"Speech recognition is unavailable for locale '{locale}'"
            )
        self.locale = locale

    # ------------------------------------------------------------------
    # Authorization
    # ------------------------------------------------------------------

    @staticmethod
    def request_authorization() -> str:
        """
        Prompt the user for Speech Recognition permission.

        Returns one of: ``'authorized'``, ``'denied'``, ``'restricted'``,
        ``'not_determined'``. Blocks until the user responds.
        """
        if not _AVAILABLE:
            raise UnavailableError("pyobjc-framework-Speech is required.")

        done = threading.Event()
        status_ref: list[int] = [0]

        def _callback(status: int) -> None:
            status_ref[0] = status
            done.set()

        Speech.SFSpeechRecognizer.requestAuthorization_(_callback)
        done.wait()
        return _AUTH_STATUS.get(status_ref[0], "unknown")

    @staticmethod
    def authorization_status() -> str:
        """Return the current authorization status without prompting."""
        if not _AVAILABLE:
            raise UnavailableError("pyobjc-framework-Speech is required.")
        status = Speech.SFSpeechRecognizer.authorizationStatus()
        return _AUTH_STATUS.get(status, "unknown")

    # ------------------------------------------------------------------
    # Recognition
    # ------------------------------------------------------------------

    def recognize_file(self, audio_path: str | Path, timeout: float = 30.0) -> str:
        """
        Transcribe an audio file and return the best transcription string.

        :param audio_path: Path to a supported audio file (WAV, M4A, MP3, …).
        :param timeout: Maximum seconds to wait before raising ``TimeoutError``.
        :raises AuthorizationError: If Speech Recognition permission is not granted.
        :raises FileNotFoundError: If *audio_path* does not exist.
        :raises RecognitionError: If the recognizer returns an error.
        :raises TimeoutError: If recognition does not complete within *timeout*.
        """
        status = self.authorization_status()
        if status != "authorized":
            raise AuthorizationError(
                f"Speech Recognition permission is '{status}'. "
                "Call SpeechRecognizer.request_authorization() first, or grant "
                "access in System Settings > Privacy & Security > Speech Recognition."
            )

        path = Path(audio_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        url = Foundation.NSURL.fileURLWithPath_(str(path))
        request = Speech.SFSpeechURLRecognitionRequest.alloc().initWithURL_(url)

        done = threading.Event()
        result_ref: list[Optional[str]] = [None]
        error_ref: list[Optional[str]] = [None]

        def _handler(result, error) -> None:
            if error is not None:
                error_ref[0] = str(error)
                done.set()
            elif result is not None and result.isFinal():
                result_ref[0] = result.bestTranscription().formattedString()
                done.set()

        task = self._recognizer.recognitionTaskWithRequest_resultHandler_(
            request, _handler
        )

        # Spin the NSRunLoop so macOS can deliver callbacks on the main thread.
        deadline = time.monotonic() + timeout
        while not done.is_set():
            if time.monotonic() >= deadline:
                task.cancel()
                raise TimeoutError(f"Speech recognition timed out after {timeout}s")
            Foundation.NSRunLoop.currentRunLoop().runUntilDate_(
                Foundation.NSDate.dateWithTimeIntervalSinceNow_(0.05)
            )

        if error_ref[0]:
            raise RecognitionError(error_ref[0])

        return result_ref[0] or ""

    async def recognize_file_async(
        self, audio_path: str | Path, timeout: float = 30.0
    ) -> str:
        """Async version of :meth:`recognize_file`."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.recognize_file, audio_path, timeout
        )
