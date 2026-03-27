"""Shared sentence-splitting utility for streaming TTS engines.

All engines use this to split buffered text at sentence boundaries,
ensuring consistent behavior across engines.
"""
from typing import Callable, Iterator

# Sentence-ending patterns: punctuation followed by whitespace or newline
SENTENCE_BOUNDARIES = [". ", "! ", "? ", ".\n", "!\n", "?\n"]


def split_sentences(text_iterator: Iterator[str], speak_fn: Callable[[str], None],
                    stop_check: Callable[[], bool] = lambda: False,
                    queued: bool = False) -> None:
    """Buffer text from an iterator and call speak_fn for each complete sentence.

    Args:
        text_iterator: Source of text chunks (lines, characters, or blocks).
        speak_fn: Called with each complete sentence to speak.
        stop_check: Returns True if playback should stop.
        queued: If True, sentences are queued and played in a background thread,
                allowing overlap between generation and playback.
    """
    if queued:
        from voice_bridge.tts.audio_queue import AudioQueue
        aq = AudioQueue(speak_fn)
        emit = aq.put
        check = lambda: stop_check() or aq.is_cancelled
    else:
        emit = speak_fn
        check = stop_check

    buffer = ""

    for text_chunk in text_iterator:
        if check():
            break
        buffer += text_chunk

        while not check():
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
                emit(sentence)

    # Flush remaining buffer
    if buffer.strip() and not check():
        emit(buffer)

    if queued:
        if check():
            aq.cancel()
        else:
            aq.drain()
