"""edge-tts engine -- free Microsoft Neural TTS, 400+ voices, no API key.

Requires: pip install ai-voice-bridge[edge]
"""
import asyncio
import logging
import os
import subprocess
import tempfile
import threading
from typing import Iterator

from voice_bridge.tts.base import TTSEngine, TextSource
from voice_bridge.tts.sentence_splitter import split_sentences

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine, handling the case where an event loop already exists."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        # Already inside an event loop (Jupyter, MCP server, async framework).
        # Run in a separate thread with its own event loop.
        result = None
        exception = None

        def _thread_target():
            nonlocal result, exception
            try:
                result = asyncio.run(coro)
            except Exception as e:
                exception = e

        t = threading.Thread(target=_thread_target)
        t.start()
        t.join(timeout=30)
        if t.is_alive():
            raise TimeoutError("edge-tts coroutine timed out after 30s")
        if exception:
            raise exception
        return result
    else:
        return asyncio.run(coro)


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
            _run_async(self._speak_async(text))
        except Exception as e:
            logger.error("edge-tts speak failed: %s", e)
            raise

    async def _speak_async(self, text: str) -> None:
        """Generate audio via edge-tts and play it."""
        import edge_tts

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(tmp_fd)
        try:
            communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
            await communicate.save(tmp_path)

            if self._stop_event.is_set():
                return

            self._play_file(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _play_file(self, path: str) -> None:
        """Play an audio file using the best available system player."""
        import platform
        import shutil
        system = platform.system()

        if system == "Darwin":
            cmd = ["afplay", path]
        elif system == "Linux":
            if shutil.which("mpv"):
                cmd = ["mpv", "--no-terminal", path]
            elif shutil.which("ffplay"):
                cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path]
            else:
                logger.error("No audio player found. Install mpv or ffmpeg.")
                return
        elif system == "Windows":
            # Media.SoundPlayer only supports WAV, not MP3. Use mpv/ffplay instead.
            if shutil.which("ffplay"):
                cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path]
            elif shutil.which("mpv"):
                cmd = ["mpv", "--no-terminal", path]
            else:
                logger.error(
                    "No audio player found on Windows. Install ffmpeg or mpv."
                )
                return
        else:
            logger.error("Unsupported platform: %s", system)
            return

        try:
            self._process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._process.wait()
        except FileNotFoundError:
            logger.error("Audio player not found: %s", cmd[0])

    def speak_streaming(self, text_source: TextSource) -> None:
        """Accumulate text from source, speak sentences as they complete.

        Uses queued mode so the next sentence can be generated while the
        current one plays, reducing gaps between sentences.
        """
        self._stop_event.clear()
        split_sentences(
            text_source,
            speak_fn=self.speak,
            stop_check=self._stop_event.is_set,
            queued=True,
        )

    def stop(self) -> None:
        """Stop current playback."""
        self._stop_event.set()
        if self._process:
            self._process.terminate()
