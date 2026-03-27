"""Base interface for all TTS engines."""

from abc import ABC, abstractmethod
from typing import Iterator, Union
import io


# Type alias for text sources that can be streamed
TextSource = Union[str, io.StringIO, Iterator[str]]


class TTSEngine(ABC):
    """Base interface for all TTS engines."""

    @abstractmethod
    def speak(self, text: str) -> None:
        """Speak text synchronously (blocking until audio finishes)."""
        ...

    @abstractmethod
    def speak_streaming(self, text_source: TextSource) -> None:
        """Speak from a streaming text source. Splits on sentence boundaries.

        Accepts a string, StringIO, or any iterator yielding text chunks.
        Text is buffered and spoken sentence-by-sentence as boundaries are detected.
        """
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop current playback immediately."""
        ...
