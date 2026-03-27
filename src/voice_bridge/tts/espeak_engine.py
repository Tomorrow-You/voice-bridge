"""espeak-ng engine -- zero-dependency fallback for Linux.

Requires espeak-ng installed: apt install espeak-ng (Debian/Ubuntu)
"""
import shutil
import subprocess
from typing import Iterator

from voice_bridge.tts.base import TTSEngine, TextSource
from voice_bridge.tts.sentence_splitter import split_sentences


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
        # Use --stdin to avoid ARG_MAX limits with long text
        self._process = subprocess.Popen(
            [self._cmd, "-v", self.voice, "-s", str(self.rate), "--stdin"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._process.communicate(input=text.encode("utf-8"))

    def speak_streaming(self, text_source: TextSource) -> None:
        split_sentences(text_source, speak_fn=self.speak)

    def stop(self) -> None:
        if self._process:
            self._process.terminate()
