"""Threaded audio queue for overlapping TTS generation with playback.

Allows the next sentence to be generated while the current one plays,
reducing gaps between sentences during streaming.
"""

import queue
import threading
from typing import Callable

_SENTINEL = None  # Signals the playback thread to stop


class AudioQueue:
    """Queue that runs speak_fn in a background thread.

    Usage:
        q = AudioQueue(engine.speak)
        q.put("First sentence.")
        q.put("Second sentence.")  # queued while first plays
        q.drain()  # wait for all to finish

        q.cancel()  # stop immediately, clear remaining
    """

    def __init__(self, speak_fn: Callable[[str], None], maxsize: int = 8):
        self._speak_fn = speak_fn
        self._queue: queue.Queue[str | None] = queue.Queue(maxsize=maxsize)
        self._cancelled = threading.Event()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self):
        while not self._cancelled.is_set():
            try:
                item = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if item is _SENTINEL:
                self._queue.task_done()
                break

            if not self._cancelled.is_set():
                try:
                    self._speak_fn(item)
                except Exception:
                    pass  # Engine errors shouldn't crash the queue
            self._queue.task_done()

    def put(self, text: str) -> None:
        """Add a sentence to the playback queue."""
        if not self._cancelled.is_set():
            self._queue.put(text)

    def drain(self) -> None:
        """Wait for all queued sentences to finish playing."""
        if not self._cancelled.is_set():
            self._queue.put(_SENTINEL)
            self._thread.join()

    def cancel(self) -> None:
        """Cancel playback and discard remaining queue."""
        self._cancelled.set()
        # Drain the queue to unblock any waiting put()
        try:
            while True:
                self._queue.get_nowait()
                self._queue.task_done()
        except queue.Empty:
            pass
        self._queue.put(_SENTINEL)
        self._thread.join(timeout=2)

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled.is_set()
