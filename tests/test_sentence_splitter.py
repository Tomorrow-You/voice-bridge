"""Tests for the shared sentence splitter."""
from voice_bridge.tts.sentence_splitter import split_sentences


def test_splits_on_period():
    chunks = iter(["Hello world. How are you. Fine."])
    spoken = []
    split_sentences(chunks, speak_fn=spoken.append)
    assert len(spoken) == 3
    assert "Hello world." in spoken[0]
    assert "How are you." in spoken[1]
    assert "Fine." in spoken[2]


def test_splits_on_exclamation():
    chunks = iter(["Wow! That is great! Cool."])
    spoken = []
    split_sentences(chunks, speak_fn=spoken.append)
    assert len(spoken) == 3


def test_splits_on_question():
    chunks = iter(["How? Why? OK."])
    spoken = []
    split_sentences(chunks, speak_fn=spoken.append)
    assert len(spoken) == 3


def test_splits_on_newline_boundaries():
    chunks = iter(["First sentence.\nSecond sentence.\n"])
    spoken = []
    split_sentences(chunks, speak_fn=spoken.append)
    assert len(spoken) == 2


def test_flushes_remainder():
    chunks = iter(["No period at end"])
    spoken = []
    split_sentences(chunks, speak_fn=spoken.append)
    assert spoken == ["No period at end"]


def test_skips_empty_sentences():
    chunks = iter(["  . .  Real sentence. "])
    spoken = []
    split_sentences(chunks, speak_fn=spoken.append)
    # Only non-empty sentences should be spoken
    for s in spoken:
        assert s.strip()


def test_stop_check_halts_processing():
    call_count = 0

    def counting_speak(text):
        nonlocal call_count
        call_count += 1

    chunks = iter(["First. Second. Third. Fourth."])
    # Stop after first sentence
    stop_after_one = lambda: call_count >= 1
    split_sentences(chunks, speak_fn=counting_speak, stop_check=stop_after_one)
    assert call_count == 1


def test_multiple_chunks():
    """Text arriving in small chunks still splits correctly."""
    chunks = iter(["Hello ", "world. ", "How are ", "you. ", "Fine."])
    spoken = []
    split_sentences(chunks, speak_fn=spoken.append)
    assert len(spoken) == 3


def test_empty_input():
    chunks = iter([""])
    spoken = []
    split_sentences(chunks, speak_fn=spoken.append)
    assert spoken == []


def test_whitespace_only():
    chunks = iter(["   \n\n  "])
    spoken = []
    split_sentences(chunks, speak_fn=spoken.append)
    assert spoken == []
