"""Tests for the MCP server tool handlers."""

import pytest

try:
    import mcp  # noqa: F401
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(not HAS_MCP, reason="mcp not installed"),
]


async def test_list_tools():
    from voice_bridge.mcp.server import list_tools

    tools = await list_tools()
    names = [t.name for t in tools]
    assert "speak" in names
    assert "set_engine" in names
    assert "get_status" in names
    assert "list_voices" in names
    assert len(tools) == 4


async def test_get_status():
    from voice_bridge.mcp.server import call_tool

    result = await call_tool("get_status", {})
    assert len(result) == 1
    text = result[0].text
    assert "Mode:" in text
    assert "Engine setting:" in text
    assert "Active engine:" in text
    assert "Available engines:" in text


async def test_speak_empty_text():
    from voice_bridge.mcp.server import call_tool

    result = await call_tool("speak", {"text": ""})
    assert "No text" in result[0].text


async def test_speak_filtered_out():
    from voice_bridge.mcp.server import call_tool

    # Text that is entirely code should be filtered out
    result = await call_tool("speak", {"text": "```python\nprint('hello')\n```"})
    assert "filtered out" in result[0].text


async def test_set_engine_empty():
    from voice_bridge.mcp.server import call_tool

    result = await call_tool("set_engine", {"name": ""})
    assert "No engine name" in result[0].text


async def test_set_engine_invalid():
    from voice_bridge.mcp.server import call_tool

    result = await call_tool("set_engine", {"name": "nonexistent"})
    assert "Error" in result[0].text


async def test_list_voices_invalid_engine():
    from voice_bridge.mcp.server import call_tool

    result = await call_tool("list_voices", {"engine": "nonexistent"})
    assert "Error" in result[0].text


async def test_list_voices_kokoro():
    from voice_bridge.mcp.server import call_tool

    result = await call_tool("list_voices", {"engine": "kokoro"})
    # Kokoro is likely not installed, so we get either voice list or install hint
    text = result[0].text
    assert "kokoro" in text.lower() or "Kokoro" in text


async def test_unknown_tool():
    from voice_bridge.mcp.server import call_tool

    with pytest.raises(ValueError, match="Unknown tool"):
        await call_tool("nonexistent", {})


async def test_tool_schemas_valid():
    """All tools must have valid inputSchema with type=object."""
    from voice_bridge.mcp.server import list_tools

    tools = await list_tools()
    for tool in tools:
        assert tool.inputSchema["type"] == "object"
        assert "properties" in tool.inputSchema


async def test_speak_tool_has_required_text():
    from voice_bridge.mcp.server import list_tools

    tools = await list_tools()
    speak = next(t for t in tools if t.name == "speak")
    assert "text" in speak.inputSchema["required"]
