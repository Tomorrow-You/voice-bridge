"""edge-tts engine -- free Microsoft Neural TTS, 400+ voices, no API key.

Requires: pip install voice-bridge[edge]
"""
import asyncio
import logging
import subprocess
import sys
import tempfile
import threading
from typing import Iterator

from voice_bridge.tts.base import TTSEngine

logger = logging.getLogger(__name__)


class EdgeTTSEngine(TTSEngine):
    """Free TTS via Microsoft Edge's neural voices. No API key required."""

    def __init__(self, voice: str = "en-US-GuyNeural", rate: str = "+0%"):
        self.voice = voice
        self.rate = rate
        self._stop_event = threading.Event()
        self._process: subprocess.Popen | None = None

    def speak(self, text: str) -> None:
        """Speak text using edge-tts (writes to temp file, plays with system audio)."""
        self._stop_event.clear()
        if not text.strip():
            return

        try:
            asyncio.run(self._speak_async(text))
        except Exception as e:
            logger.error("edge-tts speak failed: %s", e)
            raise

    async def _speak_async(self, text: str) -> None:
        """Generate audio via edge-tts and play it."""
        import edge_tts

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp_path = f.name

        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
        await communicate.save(tmp_path)

        if self._stop_event.is_set():
            return

        self._play_file(tmp_path)

    def _play_file(self, path: str) -> None:
        """Play an audio file using the best available system player."""
        import platform
        system = platform.system()

        if system == "Darwin":
            cmd = ["afplay", path]
        elif system == "Linux":
            # Try common Linux audio players
            import shutil
            if shutil.which("mpv"):
                cmd = ["mpv", "--no-terminal", path]
            elif shutil.which("ffplay"):
                cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path]
            elif shutil.which("aplay"):
                # aplay only handles WAV, but try it
                cmd = ["aplay", path]
            else:
                logger.error("No audio player found. Install mpv or ffmpeg.")
                return
        elif system == "Windows":
            # Use PowerShell to play audio on Windows
            cmd = ["powershell", "-c", f"(New-Object Media.SoundPlayer '{path}').PlaySync()"]
        else:
            logger.error("Unsupported platform: %s", system)
            return

        try:
            self._process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._process.wait()
        except FileNotFoundError:
            logger.error("Audio player not found: %s", cmd[0])

    def speak_streaming(self, text_iterator: Iterator[str]) -> None:
        """Accumulate text from iterator, speak sentences as they complete."""
        self._stop_event.clear()
        buffer = ""

        for text_chunk in text_iterator:
            if self._stop_event.is_set():
                break
            buffer += text_chunk

            while any(sep in buffer for sep in [". ", "! ", "? ", ".\n", "!\n", "?\n"]):
                for sep in [". ", "! ", "? ", ".\n", "!\n", "?\n"]:
                    idx = buffer.find(sep)
                    if idx != -1:
                        sentence = buffer[:idx + len(sep)]
                        buffer = buffer[idx + len(sep):]
                        if not self._stop_event.is_set():
                            self.speak(sentence)
                        break

        if buffer.strip() and not self._stop_event.is_set():
            self.speak(buffer)

    def stop(self) -> None:
        """Stop current playback."""
        self._stop_event.set()
        if self._process:
            self._process.terminate()
