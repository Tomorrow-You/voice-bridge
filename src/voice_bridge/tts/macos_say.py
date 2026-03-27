"""macOS say engine -- zero-dependency fallback using the built-in say command."""
import subprocess
from typing import Iterator

from voice_bridge.tts.base import TTSEngine, TextSource
from voice_bridge.tts.sentence_splitter import split_sentences


class MacOSSayTTS(TTSEngine):
    """Zero-dependency fallback using macOS built-in say command."""

    def __init__(self, voice: str = "Samantha", rate: int = 200):
        self.voice = voice
        self.rate = rate
        self._process: subprocess.Popen | None = None

    def speak(self, text: str) -> None:
        # Use stdin to avoid ARG_MAX limits with long text
        self._process = subprocess.Popen(
            ["say", "-v", self.voice, "-r", str(self.rate)],
            stdin=subprocess.PIPE,
        )
        self._process.communicate(input=text.encode("utf-8"))

    def speak_streaming(self, text_source: TextSource) -> None:
        split_sentences(text_source, speak_fn=self.speak)

    def stop(self) -> None:
        if self._process:
            self._process.terminate()
