"""macOS say engine -- zero-dependency fallback using the built-in say command."""
import subprocess
from typing import Iterator

from voice_bridge.tts.base import TTSEngine


class MacOSSayTTS(TTSEngine):
    """Zero-dependency fallback using macOS built-in say command."""

    def __init__(self, voice: str = "Samantha", rate: int = 200):
        self.voice = voice
        self.rate = rate
        self._process: subprocess.Popen | None = None

    def speak(self, text: str) -> None:
        self._process = subprocess.Popen(
            ["say", "-v", self.voice, "-r", str(self.rate), text]
        )
        self._process.wait()

    def speak_streaming(self, text_iterator: Iterator[str]) -> None:
        buffer = ""
        for chunk in text_iterator:
            buffer += chunk
            while ". " in buffer or ".\n" in buffer:
                for sep in [". ", ".\n"]:
                    idx = buffer.find(sep)
                    if idx != -1:
                        sentence = buffer[:idx + 1]
                        buffer = buffer[idx + len(sep):]
                        self.speak(sentence)
                        break
        if buffer.strip():
            self.speak(buffer)

    def stop(self) -> None:
        if self._process:
            self._process.terminate()
