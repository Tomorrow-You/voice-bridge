"""MCP server for Voice Bridge.

Exposes TTS functionality as MCP tools so that any MCP-compatible client
(Claude Desktop, Cursor, VS Code, Windsurf) can speak text aloud.

Transport: stdio (stdin/stdout JSON-RPC).
"""

import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from voice_bridge.engines import get_available_engines, create_engine, resolve_engine_name
from voice_bridge.state import read_state, write_state, read_state_value
from voice_bridge.text_filter import filter_for_tts

logger = logging.getLogger("voice_bridge.mcp")

server = Server("voice-bridge")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="speak",
            description=(
                "Speak text aloud using the configured TTS engine. "
                "Text is automatically filtered to remove code, secrets, and markdown."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to speak aloud.",
                    },
                    "engine": {
                        "type": "string",
                        "description": (
                            "TTS engine to use. If omitted, uses the configured default. "
                            "Options: edge-tts, elevenlabs, kokoro, say, espeak"
                        ),
                    },
                },
                "required": ["text"],
            },
        ),
        types.Tool(
            name="set_engine",
            description="Switch the default TTS engine.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": (
                            "Engine name: auto, edge-tts, elevenlabs, kokoro, say, espeak"
                        ),
                    },
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="get_status",
            description="Get current Voice Bridge status: mode, engine, and available engines.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="list_voices",
            description="List available voices for a TTS engine.",
            inputSchema={
                "type": "object",
                "properties": {
                    "engine": {
                        "type": "string",
                        "description": (
                            "Engine to list voices for. "
                            "If omitted, uses the current engine."
                        ),
                    },
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "speak":
        return await _handle_speak(arguments)
    elif name == "set_engine":
        return await _handle_set_engine(arguments)
    elif name == "get_status":
        return await _handle_get_status()
    elif name == "list_voices":
        return await _handle_list_voices(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def _handle_speak(arguments: dict) -> list[types.TextContent]:
    text = arguments.get("text", "")
    if not text.strip():
        return [types.TextContent(type="text", text="No text provided.")]

    filtered = filter_for_tts(text)
    if not filtered.strip():
        return [types.TextContent(type="text", text="Text was entirely filtered out (code/secrets/paths).")]

    engine_name = arguments.get("engine") or read_state_value("VOICE_BRIDGE_ENGINE", "auto")

    try:
        resolved = resolve_engine_name(engine_name)
        engine = create_engine(resolved)
        # Run blocking TTS in a thread to avoid blocking the async event loop
        await asyncio.to_thread(engine.speak, filtered)
        return [types.TextContent(type="text", text=f"Spoke {len(filtered)} characters using {resolved}.")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error speaking: {e}")]


async def _handle_set_engine(arguments: dict) -> list[types.TextContent]:
    name = arguments.get("name", "")
    if not name:
        return [types.TextContent(type="text", text="No engine name provided.")]

    try:
        # Validate engine name (allows "auto")
        if name != "auto":
            resolve_engine_name(name)

        state = read_state()
        state["VOICE_BRIDGE_ENGINE"] = name
        write_state(state)

        resolved = resolve_engine_name(name)
        return [types.TextContent(
            type="text",
            text=f"Engine set to '{name}' (resolves to '{resolved}').",
        )]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error setting engine: {e}")]


async def _handle_get_status() -> list[types.TextContent]:
    state = read_state()
    mode = state.get("VOICE_BRIDGE_MODE", "off")
    engine_setting = state.get("VOICE_BRIDGE_ENGINE", "auto")

    available = get_available_engines()
    try:
        resolved = resolve_engine_name(engine_setting)
    except RuntimeError:
        resolved = "(none available)"

    lines = [
        f"Mode: {mode}",
        f"Engine setting: {engine_setting}",
        f"Active engine: {resolved}",
        "",
        "Available engines:",
    ]
    for eng, is_available in available.items():
        marker = "✓" if is_available else "✗"
        lines.append(f"  {marker} {eng}")

    return [types.TextContent(type="text", text="\n".join(lines))]


async def _handle_list_voices(arguments: dict) -> list[types.TextContent]:
    engine_name = arguments.get("engine") or read_state_value("VOICE_BRIDGE_ENGINE", "auto")

    try:
        resolved = resolve_engine_name(engine_name)
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {e}")]

    if resolved == "edge-tts":
        return await _list_edge_tts_voices()
    elif resolved == "elevenlabs":
        return await asyncio.to_thread(_list_elevenlabs_voices)
    elif resolved == "kokoro":
        return _list_kokoro_voices()
    elif resolved == "say":
        return await asyncio.to_thread(_list_say_voices)
    elif resolved == "espeak":
        return await asyncio.to_thread(_list_espeak_voices)
    else:
        return [types.TextContent(type="text", text=f"No voice listing for engine: {resolved}")]


async def _list_edge_tts_voices() -> list[types.TextContent]:
    try:
        import edge_tts
        voices = await edge_tts.list_voices()
        # Show English voices by default, sorted by short name
        en_voices = [v for v in voices if v["Locale"].startswith("en-")]
        en_voices.sort(key=lambda v: v["ShortName"])

        lines = [f"edge-tts English voices ({len(en_voices)} of {len(voices)} total):"]
        for v in en_voices[:30]:  # Limit output
            lines.append(f"  {v['ShortName']} ({v['Gender']})")
        if len(en_voices) > 30:
            lines.append(f"  ... and {len(en_voices) - 30} more")

        return [types.TextContent(type="text", text="\n".join(lines))]
    except ImportError:
        return [types.TextContent(type="text", text="edge-tts not installed. Run: pip install ai-voice-bridge[edge]")]


def _list_elevenlabs_voices() -> list[types.TextContent]:
    try:
        from elevenlabs import ElevenLabs
        import os
        from voice_bridge.state import read_env_key

        api_key = os.getenv("ELEVENLABS_API_KEY", "") or read_env_key("ELEVENLABS_API_KEY", "")
        if not api_key:
            return [types.TextContent(type="text", text="ElevenLabs API key not configured.")]

        client = ElevenLabs(api_key=api_key)
        response = client.voices.get_all()
        voices = response.voices

        lines = [f"ElevenLabs voices ({len(voices)}):"]
        for v in voices[:20]:
            lines.append(f"  {v.name} (ID: {v.voice_id})")
        if len(voices) > 20:
            lines.append(f"  ... and {len(voices) - 20} more")

        return [types.TextContent(type="text", text="\n".join(lines))]
    except ImportError:
        return [types.TextContent(type="text", text="ElevenLabs not installed. Run: pip install ai-voice-bridge[elevenlabs]")]


def _list_kokoro_voices() -> list[types.TextContent]:
    # Kokoro has a fixed set of bundled voices
    voices = [
        "af_bella", "af_nicole", "af_sarah", "af_sky",
        "am_adam", "am_michael",
        "bf_emma", "bf_isabella",
        "bm_george", "bm_lewis",
    ]
    lines = ["Kokoro voices:"]
    for v in voices:
        lines.append(f"  {v}")
    return [types.TextContent(type="text", text="\n".join(lines))]


def _list_say_voices() -> list[types.TextContent]:
    import subprocess
    try:
        result = subprocess.run(
            ["say", "-v", "?"],
            capture_output=True, text=True, timeout=5,
        )
        voices = result.stdout.strip().splitlines()
        en_voices = [v for v in voices if "en_" in v or "en-" in v]

        lines = [f"macOS say English voices ({len(en_voices)} of {len(voices)} total):"]
        for v in en_voices[:20]:
            name = v.split()[0]
            lines.append(f"  {name}")
        if len(en_voices) > 20:
            lines.append(f"  ... and {len(en_voices) - 20} more")

        return [types.TextContent(type="text", text="\n".join(lines))]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error listing voices: {e}")]


def _list_espeak_voices() -> list[types.TextContent]:
    import subprocess
    import shutil

    cmd = "espeak-ng" if shutil.which("espeak-ng") else "espeak"
    try:
        result = subprocess.run(
            [cmd, "--voices=en"],
            capture_output=True, text=True, timeout=5,
        )
        lines = ["espeak English voices:"]
        for line in result.stdout.strip().splitlines()[:20]:
            lines.append(f"  {line.strip()}")
        return [types.TextContent(type="text", text="\n".join(lines))]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error listing voices: {e}")]


async def run_server():
    """Run the MCP server with stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


def main():
    """Entry point for the voice-bridge-mcp command."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
