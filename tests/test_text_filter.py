from voice_bridge.text_filter import filter_for_tts


def test_strips_code_blocks():
    text = "Here's the fix:\n```python\ndef foo():\n    pass\n```\nThat should work."
    result = filter_for_tts(text)
    assert "def foo" not in result
    assert "That should work" in result


def test_strips_secret_patterns():
    text = "The key is sk-abc123def456ghijklmnopqrst. Don't share it."
    result = filter_for_tts(text)
    assert "sk-abc123" not in result
    assert "[redacted]" in result


def test_preserves_normal_text():
    text = "I've updated the configuration. The changes look good."
    result = filter_for_tts(text)
    assert result == text


def test_truncates_long_text():
    text = "Word " * 1000  # 5000 chars
    result = filter_for_tts(text)
    assert len(result) <= 4000


def test_strips_file_paths():
    text = "I edited /Users/someone/project/file.py to fix the bug."
    result = filter_for_tts(text)
    assert "/Users/someone" not in result


def test_strips_urls():
    text = "Check the docs at https://example.com/docs for details."
    result = filter_for_tts(text)
    assert "https://example.com" not in result
    assert "Check the docs at" in result
    assert "for details" in result


def test_strips_extended_paths():
    text = "Found config at /opt/homebrew/etc/config.yaml and /Library/LaunchAgents/com.foo.plist."
    result = filter_for_tts(text)
    assert "/opt/homebrew" not in result
    assert "/Library/LaunchAgents" not in result


def test_strips_markdown_tables():
    text = "Results:\n| Name | Score |\n|------|-------|\n| Alice | 95 |\n| Bob | 87 |\nDone."
    result = filter_for_tts(text)
    assert "|" not in result
    assert "Done" in result


def test_strips_list_markers():
    text = "Steps:\n- First thing\n- Second thing\n* Third thing\n1. Fourth thing"
    result = filter_for_tts(text)
    assert "- First" not in result
    assert "* Third" not in result
    assert "1. Fourth" not in result
    assert "First thing" in result
    assert "Fourth thing" in result


def test_strips_inline_code():
    text = "Run the `voice-bridge test` command to check."
    result = filter_for_tts(text)
    assert "`" not in result
    assert "Run the" in result


def test_strips_markdown_headers():
    text = "## Section Title\nSome content here."
    result = filter_for_tts(text)
    assert "##" not in result
    assert "Section Title" in result


def test_strips_bold_italic():
    text = "This is **bold** and *italic* text."
    result = filter_for_tts(text)
    assert "**" not in result
    assert "*italic*" not in result
    assert "bold" in result
    assert "italic" in result


def test_strips_github_tokens():
    text = "Token: ghp_abcdefghijklmnopqrstuvwxyz0123456789."
    result = filter_for_tts(text)
    assert "ghp_" not in result
    assert "[redacted]" in result


def test_strips_aws_keys():
    text = "Key: AKIAIOSFODNN7EXAMPLE."
    result = filter_for_tts(text)
    assert "AKIA" not in result


def test_strips_pem_keys():
    text = "-----BEGIN PRIVATE KEY----- some data -----END PRIVATE KEY-----"
    result = filter_for_tts(text)
    assert "BEGIN PRIVATE KEY" not in result


def test_collapses_blank_lines():
    text = "First paragraph.\n\n\n\n\nSecond paragraph."
    result = filter_for_tts(text)
    assert "\n\n\n" not in result
    assert "First paragraph" in result
    assert "Second paragraph" in result


def test_empty_input():
    assert filter_for_tts("") == ""
    assert filter_for_tts("   ") == ""


def test_only_code_blocks():
    text = "```python\nprint('hello')\n```"
    result = filter_for_tts(text)
    assert result == ""
