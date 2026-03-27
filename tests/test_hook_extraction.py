"""Tests for the hook's Python text extraction logic.

Tests the inline Python that runs inside claude_hook.sh to extract
speakable text from Claude's JSON response.
"""
import json
import re


def _extract_text(response_json: dict, mode: str = "off") -> str | None:
    """Reproduce the hook's Python extraction logic for testing."""
    msg = response_json.get('last_assistant_message', '')
    if not msg:
        return None

    # Mode 1: Single-turn -- check for <speak> tags
    speak_match = re.search(r'<speak>(.*?)</speak>', msg, re.DOTALL)
    if speak_match:
        return speak_match.group(1).strip()[:2000]

    # Mode 2: Always-on -- speak entire response
    if mode == 'always':
        return msg[:2000]

    return None


def test_extracts_speak_tags():
    data = {"last_assistant_message": "Here is the answer. <speak>Your status is good.</speak> More text."}
    result = _extract_text(data, "off")
    assert result == "Your status is good."


def test_speak_tags_multiline():
    data = {"last_assistant_message": "<speak>Line one.\nLine two.</speak>"}
    result = _extract_text(data, "off")
    assert result == "Line one.\nLine two."


def test_speak_tags_truncate_at_2000():
    long_text = "A" * 3000
    data = {"last_assistant_message": f"<speak>{long_text}</speak>"}
    result = _extract_text(data, "off")
    assert len(result) == 2000


def test_always_mode_returns_full_response():
    data = {"last_assistant_message": "This is a regular response without tags."}
    result = _extract_text(data, "always")
    assert result == "This is a regular response without tags."


def test_always_mode_truncates():
    data = {"last_assistant_message": "X" * 3000}
    result = _extract_text(data, "always")
    assert len(result) == 2000


def test_off_mode_no_tags_returns_none():
    data = {"last_assistant_message": "Just a normal response."}
    result = _extract_text(data, "off")
    assert result is None


def test_empty_message_returns_none():
    data = {"last_assistant_message": ""}
    assert _extract_text(data, "off") is None
    assert _extract_text(data, "always") is None


def test_missing_key_returns_none():
    assert _extract_text({}, "off") is None
    assert _extract_text({}, "always") is None


def test_speak_tags_preferred_over_always():
    """Even in always mode, <speak> tags should be used if present."""
    data = {"last_assistant_message": "Preamble. <speak>Tagged text.</speak> More."}
    result = _extract_text(data, "always")
    assert result == "Tagged text."
