"""Shared sentence-splitting utility for streaming TTS engines.

All engines use this to split buffered text at sentence boundaries,
ensuring consistent behavior across engines.
"""
from typing import Callable, Iterator

# Sentence-ending patterns: punctuation followed by whitespace or newline
SENTENCE_BOUNDARIES = [". ", "! ", "? ", ".\n", "!\n", "?\n"]


def split_sentences(text_iterator: Iterator[str], speak_fn: Callable[[str], None],
                    stop_check: Callable[[], bool] = lambda: False) -> None:
    """Buffer text from an iterator and call speak_fn for each complete sentence.

    Args:
        text_iterator: Source of text chunks (lines, characters, or blocks).
        speak_fn: Called with each complete sentence to speak.
        stop_check: Returns True if playback should stop.
    """
    buffer = ""

    for text_chunk in text_iterator:
        if stop_check():
            break
        buffer += text_chunk

        while not stop_check():
            best_idx = -1
            best_sep_len = 0
            for sep in SENTENCE_BOUNDARIES:
                idx = buffer.find(sep)
                if idx != -1 and (best_idx == -1 or idx < best_idx):
                    best_idx = idx
                    best_sep_len = len(sep)
            if best_idx == -1:
                break
            sentence = buffer[:best_idx + best_sep_len]
            buffer = buffer[best_idx + best_sep_len:]
            if sentence.strip():
                speak_fn(sentence)

    # Flush remaining buffer
    if buffer.strip() and not stop_check():
        speak_fn(buffer)
