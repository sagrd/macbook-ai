# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install in editable mode with dev deps
uv sync --group dev

# Run tests
pytest

# Run a single test file
pytest tests/path/to/test_file.py

# Build the package
uv build
```

## Architecture

**macbook-ai** is a Python library exposing macOS native AI capabilities via PyObjC bindings. All processing is on-device — no API keys or network calls.

### Module layout

- `macbook_ai/stt/` — **Implemented.** Wraps `SFSpeechRecognizer` (Speech framework). Entry point: `SpeechRecognizer` class in `recognizer.py`.
- `macbook_ai/tts/` — **Planned.** Will wrap `AVSpeechSynthesizer`.
- `macbook_ai/foundation/` — **Planned.** Will use Apple's on-device Foundation Models (macOS 26+).
- `macbook_ai/_exceptions.py` — Exception hierarchy: `MacAIError` → `UnavailableError`, `AuthorizationError`, `RecognitionError`.

### Key patterns in the STT implementation

**PyObjC callback bridging**: macOS framework callbacks don't fire unless the `NSRunLoop` is spinning. The sync recognition method manually ticks the run loop in a 50ms loop until a `threading.Event` is set by the callback.

**Async support**: `recognize_file_async` delegates to `recognize_file` via `loop.run_in_executor` — the sync method does the NSRunLoop spinning in a thread pool worker.

**Availability guard**: PyObjC imports are wrapped in `try/except ImportError` at module load time; `_AVAILABLE` flag gates all methods. This allows the module to import on non-macOS for documentation purposes, though instantiation raises `UnavailableError`.

**Optional dependencies**: `pyobjc-framework-Speech` is a core dep (always installed). `pyobjc-framework-AVFoundation` is under the `tts` extra. New modules should follow this pattern — add a new optional extra in `pyproject.toml` rather than making everything mandatory.
