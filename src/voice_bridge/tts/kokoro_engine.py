"""Kokoro engine -- local TTS via 82M-parameter ONNX model, free and offline.

Requires: pip install ai-voice-bridge[kokoro]
Models: Download from https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
"""
import logging
import threading
from typing import Iterator

import numpy as np
import sounddevice as sd

from voice_bridge.tts.base import TTSEngine, TextSource
from voice_bridge.tts.sentence_splitter import split_sentences
from voice_bridge.paths import get_models_dir

logger = logging.getLogger(__name__)

SAMPLE_RATE = 24000


class KokoroTTS(TTSEngine):
    """Local TTS via Kokoro-82M ONNX -- zero cost, runs on CPU."""

    def __init__(self, voice: str = "bm_lewis", speed: float = 1.4):
        self.voice = voice
        self.speed = speed
        self._stop_event = threading.Event()
        self._kokoro = None  # Lazy init

    def _ensure_loaded(self):
        """Lazy-load model on first use (~1-2s cold start)."""
        if self._kokoro is not None:
            return

        models_dir = get_models_dir()
        model_path = models_dir / "kokoro-v1.0.fp16.onnx"
        voices_path = models_dir / "voices-v1.0.bin"

        if not model_path.exists() or not voices_path.exists():
            raise FileNotFoundError(
                f"Kokoro model files not found. Expected:\n"
                f"  {model_path}\n"
                f"  {voices_path}\n\n"
                f"Download from: https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0\n"
                f"Place files in: {models_dir}/"
            )

        from kokoro_onnx import Kokoro
        logger.info("Loading Kokoro model (cold start)...")
        self._kokoro = Kokoro(str(model_path), str(voices_path))
        logger.info("Kokoro model loaded.")

    def speak(self, text: str) -> None:
        """Speak text using Kokoro local TTS."""
        self._stop_event.clear()
        self._ensure_loaded()

        samples, sample_rate = self._kokoro.create(
            text, voice=self.voice, speed=self.speed, lang="en-us",
        )

        if not self._stop_event.is_set():
            sd.play(samples, samplerate=sample_rate)
            sd.wait()

    def speak_streaming(self, text_source: TextSource) -> None:
        """Accumulate text from source, speak sentences as they complete."""
        self._stop_event.clear()
        self._ensure_loaded()
        split_sentences(
            text_source,
            speak_fn=self._speak_sentence,
            stop_check=self._stop_event.is_set,
        )

    def _speak_sentence(self, text: str) -> None:
        if not text.strip() or self._stop_event.is_set():
            return
        samples, sample_rate = self._kokoro.create(
            text, voice=self.voice, speed=self.speed, lang="en-us",
        )
        if not self._stop_event.is_set():
            sd.play(samples, samplerate=sample_rate)
            sd.wait()

    def stop(self) -> None:
        self._stop_event.set()
        sd.stop()
