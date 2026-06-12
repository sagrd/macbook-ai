"""
Text-to-speech via macOS AVSpeechSynthesizer.

Coming soon — will expose:

    from macbook_ai.tts import SpeechSynthesizer

    synth = SpeechSynthesizer(voice="com.apple.voice.compact.en-US.Samantha")
    synth.speak("Hello from macbook-ai")
    await synth.speak_async("Hello from macbook-ai")
    synth.save_to_file("Hello from macbook-ai", "output.caf")

Requires: pip install 'macbook-ai[tts]'
"""
