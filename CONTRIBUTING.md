# Contributing to Voice Bridge

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/Tomorrow-You/voice-bridge.git
cd voice-bridge
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"  # Package: ai-voice-bridge on PyPI
```

To install optional engines for testing:
```bash
pip install -e ".[all,dev]"
```

## Running Tests

```bash
pytest
```

## Adding a New Engine

1. Create `src/voice_bridge/tts/your_engine.py`
2. Subclass `TTSEngine` from `voice_bridge.tts.base`
3. Implement `speak()`, `speak_streaming()`, and `stop()`
4. Register it in `src/voice_bridge/tts/__init__.py` and `AVAILABLE_ENGINES`
5. Add tests in `tests/test_your_engine.py`
6. Update the engine list in `cli.py` and `speak.py`

## Code Style

- Keep it simple. Minimal dependencies in the core package.
- Use type hints for public APIs.
- New engines should be optional dependencies (extras in pyproject.toml).

## Pull Requests

- One feature per PR
- Include tests for new functionality
- Update README if adding user-facing features
