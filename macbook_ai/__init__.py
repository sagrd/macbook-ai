"""
macbook-ai — Python interface to macOS AI capabilities.

Quick start::

    from macbook_ai.stt import SpeechRecognizer

    r = SpeechRecognizer()
    r.request_authorization()          # once, prompts for system permission
    text = r.recognize_file("clip.m4a")
"""

__version__ = "0.1.5"
