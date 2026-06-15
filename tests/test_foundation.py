"""Foundation Models (on-device LLM) tests."""

import asyncio
from unittest.mock import MagicMock

import pytest

from conftest import skip_non_darwin
from macbook_ai._exceptions import InferenceError, UnavailableError

pytestmark = skip_non_darwin


# ---------------------------------------------------------------------------
# LanguageModel.__init__
# ---------------------------------------------------------------------------

class TestInit:
    def test_raises_when_unavailable(self, monkeypatch):
        import macbook_ai.foundation.model as mod
        monkeypatch.setattr(mod, "_AVAILABLE", False)

        from macbook_ai.foundation import LanguageModel
        with pytest.raises(UnavailableError, match="FoundationModels"):
            LanguageModel()

    def test_creates_session_without_instructions(self, mock_fm):
        mock_fm_module, mock_model = mock_fm
        from macbook_ai.foundation import LanguageModel
        m = LanguageModel()
        mock_fm_module.FMLanguageModelSession.alloc.return_value\
            .initWithModel_.assert_called_once_with(mock_model)

    def test_creates_session_with_instructions(self, mock_fm):
        mock_fm_module, mock_model = mock_fm
        from macbook_ai.foundation import LanguageModel
        m = LanguageModel(instructions="You are a helpful assistant.")
        mock_fm_module.FMLanguageModelSession.alloc.return_value\
            .initWithModel_instructions_.assert_called_once_with(
                mock_model, "You are a helpful assistant."
            )


# ---------------------------------------------------------------------------
# respond
# ---------------------------------------------------------------------------

class TestRespond:
    async def test_returns_response_string(self, mock_fm):
        mock_fm_module, _ = mock_fm
        session_mock = MagicMock()
        mock_fm_module.FMLanguageModelSession.alloc.return_value\
            .initWithModel_.return_value = session_mock

        response_mock = MagicMock()
        response_mock.content.return_value = "The capital is Paris."

        def fake_respond(prompt, handler):
            handler(response_mock, None)

        session_mock.respondToPrompt_completionHandler_ = fake_respond

        from macbook_ai.foundation import LanguageModel
        m = LanguageModel()
        result = await m.respond("What is the capital of France?")
        assert result == "The capital is Paris."

    async def test_raises_inference_error_on_failure(self, mock_fm):
        mock_fm_module, _ = mock_fm
        session_mock = MagicMock()
        mock_fm_module.FMLanguageModelSession.alloc.return_value\
            .initWithModel_.return_value = session_mock

        def fake_respond(prompt, handler):
            handler(None, "model unavailable")

        session_mock.respondToPrompt_completionHandler_ = fake_respond

        from macbook_ai.foundation import LanguageModel
        m = LanguageModel()
        with pytest.raises(InferenceError, match="model unavailable"):
            await m.respond("hello")

    async def test_timeout_raises(self, mock_fm):
        mock_fm_module, _ = mock_fm
        session_mock = MagicMock()
        mock_fm_module.FMLanguageModelSession.alloc.return_value\
            .initWithModel_.return_value = session_mock

        # handler never called → future never resolved
        session_mock.respondToPrompt_completionHandler_ = MagicMock()

        from macbook_ai.foundation import LanguageModel
        m = LanguageModel()
        with pytest.raises(asyncio.TimeoutError):
            await m.respond("hello", timeout=0.01)

    async def test_none_response_returns_empty_string(self, mock_fm):
        mock_fm_module, _ = mock_fm
        session_mock = MagicMock()
        mock_fm_module.FMLanguageModelSession.alloc.return_value\
            .initWithModel_.return_value = session_mock

        def fake_respond(prompt, handler):
            handler(None, None)  # no error, no response object

        session_mock.respondToPrompt_completionHandler_ = fake_respond

        from macbook_ai.foundation import LanguageModel
        m = LanguageModel()
        assert await m.respond("hello") == ""

    async def test_passes_prompt_to_session(self, mock_fm):
        mock_fm_module, _ = mock_fm
        session_mock = MagicMock()
        mock_fm_module.FMLanguageModelSession.alloc.return_value\
            .initWithModel_.return_value = session_mock

        captured = {}

        def fake_respond(prompt, handler):
            captured["prompt"] = prompt
            response_mock = MagicMock()
            response_mock.content.return_value = "ok"
            handler(response_mock, None)

        session_mock.respondToPrompt_completionHandler_ = fake_respond

        from macbook_ai.foundation import LanguageModel
        m = LanguageModel()
        await m.respond("Summarise this.")
        assert captured["prompt"] == "Summarise this."


# ---------------------------------------------------------------------------
# stream
# ---------------------------------------------------------------------------

class TestStream:
    async def test_yields_chunks(self, mock_fm):
        mock_fm_module, _ = mock_fm
        session_mock = MagicMock()
        mock_fm_module.FMLanguageModelSession.alloc.return_value\
            .initWithModel_.return_value = session_mock

        def fake_stream(prompt, handler):
            for word in ("Hello", " ", "world"):
                chunk = MagicMock()
                chunk.text.return_value = word
                handler(chunk, False, None)
            handler(None, True, None)  # is_final=True signals end

        session_mock.streamResponseToPrompt_chunkHandler_ = fake_stream

        from macbook_ai.foundation import LanguageModel
        m = LanguageModel()
        chunks = []
        async for chunk in m.stream("Write something."):
            chunks.append(chunk)

        assert chunks == ["Hello", " ", "world"]

    async def test_stream_raises_on_error(self, mock_fm):
        mock_fm_module, _ = mock_fm
        session_mock = MagicMock()
        mock_fm_module.FMLanguageModelSession.alloc.return_value\
            .initWithModel_.return_value = session_mock

        def fake_stream(prompt, handler):
            handler(None, False, "inference failed")

        session_mock.streamResponseToPrompt_chunkHandler_ = fake_stream

        from macbook_ai.foundation import LanguageModel
        m = LanguageModel()
        with pytest.raises(InferenceError, match="inference failed"):
            async for _ in m.stream("hello"):
                pass

    async def test_stream_timeout_on_no_chunks(self, mock_fm):
        mock_fm_module, _ = mock_fm
        session_mock = MagicMock()
        mock_fm_module.FMLanguageModelSession.alloc.return_value\
            .initWithModel_.return_value = session_mock

        # handler never called → queue.get() times out
        session_mock.streamResponseToPrompt_chunkHandler_ = MagicMock()

        from macbook_ai.foundation import LanguageModel
        m = LanguageModel()
        with pytest.raises(asyncio.TimeoutError):
            async for _ in m.stream("hello", timeout=0.01):
                pass

    async def test_stream_empty_response(self, mock_fm):
        """A stream that immediately sends is_final yields nothing."""
        mock_fm_module, _ = mock_fm
        session_mock = MagicMock()
        mock_fm_module.FMLanguageModelSession.alloc.return_value\
            .initWithModel_.return_value = session_mock

        def fake_stream(prompt, handler):
            handler(None, True, None)

        session_mock.streamResponseToPrompt_chunkHandler_ = fake_stream

        from macbook_ai.foundation import LanguageModel
        m = LanguageModel()
        chunks = [c async for c in m.stream("hello")]
        assert chunks == []

    async def test_stream_concatenates_to_full_response(self, mock_fm):
        """Joining all chunks produces the complete text."""
        mock_fm_module, _ = mock_fm
        session_mock = MagicMock()
        mock_fm_module.FMLanguageModelSession.alloc.return_value\
            .initWithModel_.return_value = session_mock

        words = ["The", " ", "quick", " ", "brown", " ", "fox"]

        def fake_stream(prompt, handler):
            for w in words:
                chunk = MagicMock()
                chunk.text.return_value = w
                handler(chunk, False, None)
            handler(None, True, None)

        session_mock.streamResponseToPrompt_chunkHandler_ = fake_stream

        from macbook_ai.foundation import LanguageModel
        m = LanguageModel()
        result = "".join([c async for c in m.stream("hello")])
        assert result == "The quick brown fox"
