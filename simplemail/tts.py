"""Text-to-speech support for SimpleMail."""

import threading
from typing import Optional


class TTSEngine:
    """Wraps pyttsx3 for reading emails aloud."""

    def __init__(self):
        self._engine = None
        self._thread: Optional[threading.Thread] = None
        self._speaking = False

    def _ensure_engine(self):
        """Lazily initialize the TTS engine."""
        if self._engine is None:
            try:
                import pyttsx3
                self._engine = pyttsx3.init()
                self._engine.setProperty("rate", 140)  # Slower for accessibility
                self._engine.setProperty("volume", 1.0)
            except Exception:
                self._engine = None

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    def speak(self, text: str):
        """Read text aloud in a background thread."""
        self.stop()
        self._ensure_engine()
        if not self._engine:
            return

        def _worker():
            self._speaking = True
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception:
                pass
            finally:
                self._speaking = False

        self._thread = threading.Thread(target=_worker, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop speaking."""
        if self._engine and self._speaking:
            try:
                self._engine.stop()
            except Exception:
                pass
        self._speaking = False

    def cleanup(self):
        """Clean up the TTS engine."""
        self.stop()
        self._engine = None
