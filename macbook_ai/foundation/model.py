"""Apple Foundation Models (on-device LLM) wrapper."""

from __future__ import annotations

import asyncio
import sys
import threading
from typing import AsyncIterator, Optional

from .._exceptions import InferenceError, UnavailableError

if sys.platform != "darwin":
    raise UnavailableError("macbook-ai requires macOS")

# FoundationModels requires macOS 26+. The PyObjC binding package is
# pyobjc-framework-FoundationModels. Class/method names below reflect the
# expected Objective-C overlay; adjust if Apple's headers differ.
try:
    import FoundationModels as _FM

    _DEFAULT_MODEL = _FM.FMSystemLanguageModel.defaultModel()  # type: ignore[attr-defined]
    _AVAILABLE = True
except (ImportError, AttributeError):
    _FM = None  # type: ignore[assignment]
    _DEFAULT_MODEL = None
    _AVAILABLE = False


class LanguageModel:
    """
    Run prompts against Apple's on-device Foundation Model (macOS 26+).

    No network calls are made. Requires macOS 26 and the FoundationModels
    framework (``pyobjc-framework-FoundationModels``).

    Usage::

        model = LanguageModel()
        response = await model.respond("Summarise this text: …")

        async for chunk in model.stream("Write a poem about Swift"):
            print(chunk, end="", flush=True)
    """

    def __init__(self, instructions: Optional[str] = None) -> None:
        """
        :param instructions: Optional system-level instructions for the session.
        :raises UnavailableError: If the FoundationModels framework is not available.
        """
        if not _AVAILABLE:
            raise UnavailableError(
                "FoundationModels framework is not available. "
                "Requires macOS 26+ and: pip install pyobjc-framework-FoundationModels"
            )
        if instructions is not None:
            session_cls = _FM.FMLanguageModelSession  # type: ignore[attr-defined]
            self._session = session_cls.alloc().initWithModel_instructions_(
                _DEFAULT_MODEL, instructions
            )
        else:
            session_cls = _FM.FMLanguageModelSession  # type: ignore[attr-defined]
            self._session = session_cls.alloc().initWithModel_(_DEFAULT_MODEL)

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    async def respond(self, prompt: str, timeout: float = 30.0) -> str:
        """
        Send *prompt* and return the complete response string.

        :raises InferenceError: If the model returns an error.
        :raises TimeoutError: If the model does not respond within *timeout* seconds.
        """
        loop = asyncio.get_event_loop()
        future: asyncio.Future[str] = loop.create_future()

        def _handler(response, error) -> None:
            if error is not None:
                loop.call_soon_threadsafe(
                    future.set_exception, InferenceError(str(error))
                )
            else:
                text = str(response.content()) if response is not None else ""
                loop.call_soon_threadsafe(future.set_result, text)

        self._session.respondToPrompt_completionHandler_(prompt, _handler)
        return await asyncio.wait_for(future, timeout=timeout)

    async def stream(self, prompt: str, timeout: float = 30.0) -> AsyncIterator[str]:
        """
        Send *prompt* and yield response text incrementally as it is generated.

        :raises InferenceError: If the model returns an error.
        :raises TimeoutError: If the first chunk is not received within *timeout* seconds.
        """
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue[tuple[str, str | None]] = asyncio.Queue()

        def _chunk_handler(chunk, is_final: bool, error) -> None:
            if error is not None:
                loop.call_soon_threadsafe(queue.put_nowait, ("error", str(error)))
            elif is_final:
                loop.call_soon_threadsafe(queue.put_nowait, ("done", None))
            else:
                text = str(chunk.text()) if chunk is not None else ""
                loop.call_soon_threadsafe(queue.put_nowait, ("chunk", text))

        self._session.streamResponseToPrompt_chunkHandler_(prompt, _chunk_handler)

        while True:
            kind, value = await asyncio.wait_for(queue.get(), timeout=timeout)
            if kind == "error":
                raise InferenceError(value)
            if kind == "done":
                return
            yield value  # type: ignore[misc]
