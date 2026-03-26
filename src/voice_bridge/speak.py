"""
vb-speak: Pipe text to speech.

Usage:
    echo "Hello" | vb-speak                       # Auto-detect best engine
    echo "Hello" | vb-speak --engine edge-tts      # Specific engine
    echo "Hello" | vb-speak --engine say            # macOS say
    echo "Hello" | vb-speak --dry-run               # Print text, don't speak
    echo "Hello" | vb-speak --stream                # Stream mode (sentence-by-sentence)
"""
import argparse
import sys

from voice_bridge.config import load_config
from voice_bridge.engines import create_engine, get_available_engines


def main():
    valid_engines = list(get_available_engines().keys()) + ["auto"]

    parser = argparse.ArgumentParser(description="Speak text from stdin or arguments")
    parser.add_argument("text", nargs="*", help="Text to speak (or pipe via stdin)")
    parser.add_argument("--engine", choices=valid_engines, default=None,
                        help="TTS engine (default: from config or auto)")
    parser.add_argument("--voice", default=None, help="Voice ID or name override")
    parser.add_argument("--dry-run", action="store_true", help="Print filtered text instead of speaking")
    parser.add_argument("--stream", action="store_true",
                        help="Stream mode: speak each sentence as it arrives")
    args = parser.parse_args()

    config = load_config()
    engine_name = args.engine or config.tts.engine

    # Stream mode: read stdin, filter, then stream to engine
    if args.stream and not args.text and not sys.stdin.isatty():
        import io
        from voice_bridge.text_filter import filter_for_tts
        raw = sys.stdin.read()
        filtered = filter_for_tts(raw)
        if args.dry_run:
            print(filtered)
            return
        if not filtered.strip():
            return
        engine = create_engine(engine_name, config.tts)
        if args.voice and hasattr(engine, "voice_id"):
            engine.voice_id = args.voice
        engine.speak_streaming(io.StringIO(filtered))
        return

    # Batch mode: read all text, then speak
    if args.text:
        text = " ".join(args.text)
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(1)

    from voice_bridge.text_filter import filter_for_tts
    text = filter_for_tts(text)

    if args.dry_run:
        print(text)
        return

    if not text.strip():
        return

    engine = create_engine(engine_name, config.tts)
    if args.voice and hasattr(engine, "voice_id"):
        engine.voice_id = args.voice

    engine.speak(text)


if __name__ == "__main__":
    main()
