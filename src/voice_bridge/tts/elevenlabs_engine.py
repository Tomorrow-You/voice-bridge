"""ElevenLabs engine -- cloud TTS, highest quality, paid.

Requires: pip install ai-voice-bridge[elevenlabs]
"""
import logging
import re
import threading
from typing import Iterator

import numpy as np
import sounddevice as sd
from elevenlabs import ElevenLabs
from elevenlabs.types.voice_settings import VoiceSettings

from voice_bridge.tts.base import TTSEngine, TextSource
from voice_bridge.tts.sentence_splitter import split_sentences
from voice_bridge.config import TTSConfig

logger = logging.getLogger(__name__)


class ElevenLabsTTS(TTSEngine):
    """Cloud TTS via ElevenLabs streaming API."""

    def __init__(self, config: TTSConfig):
        if not config.elevenlabs_api_key:
            raise ValueError(
                "ElevenLabs API key not configured. Set ELEVENLABS_API_KEY in your .env file "
                "or run 'voice-bridge setup'. Get a key at https://elevenlabs.io/app/settings/api-keys"
            )
        self.model = config.elevenlabs_model
        self.voice_id = config.elevenlabs_voice_id
        self.speed = config.elevenlabs_speed
        self.sample_rate = config.sample_rate
        self.max_chars = config.max_chars_per_request
        self._client = ElevenLabs(api_key=config.elevenlabs_api_key)
        self._stop_event = threading.Event()

    def _voice_settings(self) -> VoiceSettings:
        return VoiceSettings(speed=self.speed)

    def _chunk_text(self, text: str) -> list[str]:
        """Split text into chunks at sentence boundaries."""
        if len(text) <= self.max_chars:
            return [text]

        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current = ""
        for sentence in sentences:
            if len(current) + len(sentence) + 1 > self.max_chars:
                if current:
                    chunks.append(current)
                while len(sentence) > self.max_chars:
                    chunks.append(sentence[:self.max_chars])
                    sentence = sentence[self.max_chars:]
                current = sentence
            else:
                current = f"{current} {sentence}".strip() if current else sentence
        if current:
            chunks.append(current)
        return chunks

    def speak(self, text: str) -> None:
        """Speak text using ElevenLabs streaming API."""
        self._stop_event.clear()
        for chunk in self._chunk_text(text):
            if self._stop_event.is_set():
                break
            try:
                audio_stream = self._client.text_to_speech.stream(
                    text=chunk,
                    voice_id=self.voice_id,
                    model_id=self.model,
                    output_format="pcm_24000",
                    voice_settings=self._voice_settings(),
                )
                self._play_audio_stream(audio_stream)
            except Exception as e:
                logger.error("ElevenLabs speak failed: %s", e)
                raise

    def speak_streaming(self, text_source: TextSource) -> None:
        """Stream text to ElevenLabs, play audio as it arrives."""
        self._stop_event.clear()
        split_sentences(
            text_source,
            speak_fn=self._speak_sentence,
            stop_check=self._stop_event.is_set,
        )

    def _speak_sentence(self, text: str) -> None:
        if not text.strip():
            return
        try:
            audio_stream = self._client.text_to_speech.stream(
                text=text,
                voice_id=self.voice_id,
                model_id=self.model,
                output_format="pcm_24000",
                voice_settings=self._voice_settings(),
            )
            self._play_audio_stream(audio_stream)
        except Exception as e:
            logger.error("ElevenLabs sentence speak failed: %s", e)
            raise

    def _play_audio_stream(self, audio_stream) -> None:
        """Play PCM audio incrementally as chunks arrive."""
        try:
            with sd.OutputStream(samplerate=self.sample_rate, channels=1, dtype='float32') as stream:
                for chunk in audio_stream:
                    if self._stop_event.is_set():
                        break
                    if isinstance(chunk, bytes) and chunk:
                        arr = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
                        stream.write(arr.reshape(-1, 1))
        except sd.PortAudioError as e:
            logger.error("Audio playback failed: %s", e)

    def stop(self) -> None:
        """Stop current playback."""
        self._stop_event.set()
        sd.stop()
