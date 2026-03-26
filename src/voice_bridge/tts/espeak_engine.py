"""espeak-ng engine -- zero-dependency fallback for Linux.

Requires espeak-ng installed: apt install espeak-ng (Debian/Ubuntu)
"""
import shutil
import subprocess
from typing import Iterator

from voice_bridge.tts.base import TTSEngine


class EspeakTTS(TTSEngine):
    """Linux fallback TTS using espeak-ng (or espeak)."""

    def __init__(self, voice: str = "en", rate: int = 175):
        self.voice = voice
        self.rate = rate
        self._process: subprocess.Popen | None = None

        # Find the espeak binary
        self._cmd = shutil.which("espeak-ng") or shutil.which("espeak")
        if not self._cmd:
            raise FileNotFoundError(
                "espeak-ng not found. Install it with:\n"
                "  apt install espeak-ng    # Debian/Ubuntu\n"
                "  brew install espeak      # macOS\n"
                "  pacman -S espeak-ng      # Arch"
            )

    def speak(self, text: str) -> None:
        self._process = subprocess.Popen(
            [self._cmd, "-v", self.voice, "-s", str(self.rate), text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
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
