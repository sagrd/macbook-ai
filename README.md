# macbook-ai

[![PyPI](https://img.shields.io/pypi/v/macbook-ai)](https://pypi.org/project/macbook-ai/)
[![Python](https://img.shields.io/pypi/pyversions/macbook-ai)](https://pypi.org/project/macbook-ai/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Python interface to macOS AI capabilities — speech recognition, text-to-speech, and LLM via Apple Foundation Models.

All processing is **on-device**. No API keys, no network calls.

## Requirements

- macOS 10.15 or later
- Python 3.10 or later
- The first time you use Speech-to-Text, macOS will prompt for access. You may need to enable it manually: **System Settings > Privacy & Security > Speech Recognition > Terminal**



## Installation

```bash
pip install macbook-ai
```

With uv:

```bash
uv add macbook-ai
```

**Note**: Foundation Models require macOS 15.6+ and `pyobjc-framework-FoundationModels` (install separately when available on PyPI).

## Features

### Speech-to-Text (STT)

Powered by the macOS `SFSpeechRecognizer` framework.

#### Grant Permission

The first time you use recognition, macOS will prompt for access. You can trigger it explicitly:

```python
from macbook_ai.stt import SpeechRecognizer

status = SpeechRecognizer.request_authorization()
# Returns: 'authorized' | 'denied' | 'restricted' | 'not_determined'
```

If running from Terminal, you may need to enable it manually:
**System Settings > Privacy & Security > Speech Recognition > Terminal**

#### Transcribe Audio Files

```python
from macbook_ai.stt import SpeechRecognizer

recognizer = SpeechRecognizer()  # defaults to en-US
text = recognizer.recognize_file("recording.m4a")
print(text)
```

#### Async Support

```python
import asyncio
from macbook_ai.stt import SpeechRecognizer

async def main():
    recognizer = SpeechRecognizer()
    text = await recognizer.recognize_file_async("recording.m4a")
    print(text)

asyncio.run(main())
```

#### Multiple Languages

```python
recognizer = SpeechRecognizer(locale="fr-FR")
recognizer = SpeechRecognizer(locale="es-ES")
recognizer = SpeechRecognizer(locale="ja-JP")
```

#### Supported Audio Formats

Any format supported by AVFoundation: **WAV, M4A, MP3, AIFF, CAF, FLAC**, and more.

#### Error Handling

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

---

### Text-to-Speech (TTS)

Powered by the macOS `AVSpeechSynthesizer` framework.

#### Basic Usage

```python
from macbook_ai.tts import SpeechSynthesizer

synth = SpeechSynthesizer()
synth.speak("Hello from macbook-ai")
```

#### Async Support

```python
import asyncio
from macbook_ai.tts import SpeechSynthesizer

async def main():
    synth = SpeechSynthesizer()
    await synth.speak_async("Hello from macbook-ai")

asyncio.run(main())
```

#### Custom Voices and Settings

```python
# List available voices
voices = SpeechSynthesizer.available_voices(language="en")
for voice in voices:
    print(f"{voice['name']} ({voice['identifier']})")

# Use a specific voice
synth = SpeechSynthesizer(
    voice="com.apple.voice.compact.en-US.Samantha",
    rate=0.5,   # 0.0 (slowest) to 1.0 (fastest)
    volume=1.0  # 0.0 to 1.0
)
synth.speak("Hello in Samantha's voice")
```

#### Save to Audio File

```python
synth = SpeechSynthesizer()
synth.save_to_file("Hello world", "output.caf")
```

---

### Apple Foundation Models (macOS 15.6+)

On-device language model — no API keys, no network calls.

**Note**: Requires macOS 15.6+ and `pyobjc-framework-FoundationModels` (not yet on PyPI).

#### Basic Usage

```python
import asyncio
from macbook_ai.foundation import LanguageModel

async def main():
    model = LanguageModel()
    
    # Get complete response
    response = await model.respond("What is the capital of France?")
    print(response)

asyncio.run(main())
```

#### Streaming Responses

```python
import asyncio
from macbook_ai.foundation import LanguageModel

async def main():
    model = LanguageModel()
    
    async for chunk in model.stream("Write a haiku about Python"):
        print(chunk, end="", flush=True)

asyncio.run(main())
```

#### With System Instructions

```python
model = LanguageModel(instructions="You are a helpful coding assistant.")
response = await model.respond("Explain list comprehensions")
print(response)
```

## Development

### Running Tests

```bash
uv run pytest tests/ -v
```

### Publishing to PyPI

This project uses GitHub Actions for **secure, tag-based publishing**.

**To publish a new version:**

1. **Update version** in `pyproject.toml`:
   ```bash
   # Edit pyproject.toml, bump version to 0.1.7
   git add pyproject.toml
   git commit -m "Bump version to 0.1.7"
   git push origin main
   ```

2. **Create and push a release tag**:
   ```bash
   git tag v0.1.7
   git push origin v0.1.7
   ```

The pipeline will automatically:
- Run tests on Python 3.10, 3.11, and 3.12
- Verify the tag matches the version in `pyproject.toml`
- Build the package
- Publish to PyPI if all checks pass

**Security**: Only tagged releases are published. This prevents accidental or malicious publishes from regular commits.

See [PUBLISHING.md](PUBLISHING.md) for detailed setup and [SECURITY.md](SECURITY.md) for security best practices.

## License

MIT
