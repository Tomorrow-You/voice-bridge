"""Tests for the audio queue."""

import threading
import time

from voice_bridge.tts.audio_queue import AudioQueue
from voice_bridge.tts.sentence_splitter import split_sentences


def test_queue_plays_all_sentences():
    """All queued sentences should be spoken in order."""
    spoken = []

    def fake_speak(text):
        spoken.append(text)

    q = AudioQueue(fake_speak)
    q.put("First.")
    q.put("Second.")
    q.put("Third.")
    q.drain()

    assert spoken == ["First.", "Second.", "Third."]


def test_queue_cancel_stops_playback():
    """Cancel should stop processing remaining sentences."""
    spoken = []
    barrier = threading.Event()

    def slow_speak(text):
        spoken.append(text)
        if text == "First.":
            barrier.set()
            time.sleep(0.5)  # Simulate slow playback

    q = AudioQueue(slow_speak)
    q.put("First.")
    q.put("Second.")
    q.put("Third.")

    barrier.wait()  # Wait until first sentence starts
    q.cancel()

    # First was spoken, but not all remaining should have played
    assert "First." in spoken
    assert len(spoken) <= 2  # At most first + one more


def test_queue_handles_empty():
    """Draining an empty queue should not hang."""
    spoken = []
    q = AudioQueue(lambda t: spoken.append(t))
    q.drain()
    assert spoken == []


def test_split_sentences_queued_mode():
    """Queued mode should process all sentences via the queue."""
    spoken = []

    def fake_speak(text):
        spoken.append(text.strip())

    chunks = iter(["Hello world. ", "How are you? ", "Fine thanks."])
    split_sentences(chunks, fake_speak, queued=True)

    assert "Hello world." in spoken
    assert "How are you?" in spoken
    assert "Fine thanks." in spoken


def test_split_sentences_queued_with_stop():
    """Stop check between chunks should cancel the queue."""
    spoken = []
    stop = threading.Event()

    def fake_speak(text):
        spoken.append(text.strip())
        stop.set()  # Signal stop after first sentence
        time.sleep(0.1)  # Simulate playback time

    def slow_chunks():
        """Yield chunks with delays so stop check can fire between them."""
        yield "First. "
        time.sleep(0.15)  # Give worker time to play and set stop
        yield "Second. "
        time.sleep(0.15)
        yield "Third."

    split_sentences(slow_chunks(), fake_speak, stop_check=stop.is_set, queued=True)

    assert "First." in spoken
    assert len(spoken) <= 2  # Should stop before Third
