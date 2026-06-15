# macbook-ai

[![PyPI](https://img.shields.io/pypi/v/macbook-ai)](https://pypi.org/project/macbook-ai/)
[![Python](https://img.shields.io/pypi/pyversions/macbook-ai)](https://pypi.org/project/macbook-ai/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Python interface to macOS AI capabilities — speech recognition, text-to-speech, and Apple Foundation Models.

All processing is **on-device**. No API keys, no network calls.

## Requirements

- macOS 10.15 or later
- Python 3.10 or later

## Installation

```bash
# speech-to-text only
pip install "macbook-ai[stt]"

# all extras
pip install "macbook-ai[all]"
```

With uv:

```bash
uv add "macbook-ai[stt]"
```

## Speech-to-Text

Powered by the macOS `SFSpeechRecognizer` framework.

### 1. Grant permission

The first time you use recognition, macOS will prompt for access. You can trigger it explicitly:

```python
from macbook_ai.stt import SpeechRecognizer

status = SpeechRecognizer.request_authorization()
# 'authorized' | 'denied' | 'restricted' | 'not_determined'
```

If running from Terminal, you may need to enable it manually:
**System Settings > Privacy & Security > Speech Recognition > Terminal**

### 2. Transcribe a file

```python
from macbook_ai.stt import SpeechRecognizer

recognizer = SpeechRecognizer()           # defaults to en-US
text = recognizer.recognize_file("recording.m4a")
print(text)
```

### Async

```python
import asyncio
from macbook_ai.stt import SpeechRecognizer

async def main():
    recognizer = SpeechRecognizer()
    text = await recognizer.recognize_file_async("recording.m4a")
    print(text)

asyncio.run(main())
```

### Locales

```python
recognizer = SpeechRecognizer(locale="fr-FR")
recognizer = SpeechRecognizer(locale="es-ES")
recognizer = SpeechRecognizer(locale="ja-JP")
```

### Supported audio formats

Any format supported by AVFoundation: **WAV, M4A, MP3, AIFF, CAF, FLAC**, and more.

### Error handling

```python
from macbook_ai.stt import SpeechRecognizer
from macbook_ai._exceptions import AuthorizationError, RecognitionError

recognizer = SpeechRecognizer()

try:
    text = recognizer.recognize_file("recording.m4a")
except AuthorizationError:
    print("Grant Speech Recognition access in System Settings first.")
except RecognitionError as e:
    print(f"Recognition failed: {e}")
except TimeoutError:
    print("Recognition timed out — try a shorter clip or increase timeout.")
```

## Roadmap

| Module | Capability | Status |
|---|---|---|
| `macbook-ai.stt` | Speech-to-text via `SFSpeechRecognizer` | Available |
| `macbook-ai.tts` | Text-to-speech via `AVSpeechSynthesizer` | Coming soon |
| `macbook-ai.foundation` | On-device LLM via Apple Foundation Models (macOS 26+) | Coming soon |

## Development

### Running Tests

```bash
uv run pytest tests/ -v
```

### Publishing to PyPI

This project uses GitHub Actions for automated publishing. To release a new version:

1. **Update version** in `pyproject.toml`
2. **Commit and push to main**:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.1.6"
   git push origin main
   ```

The pipeline will automatically:
- Run tests on Python 3.10, 3.11, and 3.12
- Build the package
- Publish to PyPI if all tests pass

**Important**: Make sure to bump the version number in `pyproject.toml` before each push, as PyPI won't accept duplicate versions.

See [PUBLISHING.md](PUBLISHING.md) for detailed setup instructions and troubleshooting.

## License

MIT
