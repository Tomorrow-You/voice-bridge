"""Base interface for all TTS engines."""

from abc import ABC, abstractmethod
from typing import Iterator


class TTSEngine(ABC):
    """Base interface for all TTS engines."""

    @abstractmethod
    def speak(self, text: str) -> None:
        """Speak text synchronously (blocking until audio finishes)."""
        ...

    @abstractmethod
    def speak_streaming(self, text_iterator: Iterator[str]) -> None:
        """Speak from a streaming text source. Starts audio ASAP."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop current playback immediately."""
        ...
