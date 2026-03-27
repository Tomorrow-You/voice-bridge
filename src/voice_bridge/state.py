"""Shared state file reader/writer for Voice Bridge.

The .state file is shell-sourceable (key=value pairs), used by both
the Python CLI and the bash Claude Code hook. Values are always quoted
to ensure shell safety.
"""
from voice_bridge.paths import get_state_file, get_env_file


def read_state() -> dict[str, str]:
    """Read the .state file into a dict. Handles comments and quoting."""
    state = {}
    state_file = get_state_file()
    if state_file.exists():
        for line in state_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip()
            # Strip surrounding quotes if present
            if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
                val = val[1:-1]
            state[key] = val
    return state


def read_state_value(key: str, default: str = "") -> str:
    """Read a single value from the .state file."""
    return read_state().get(key, default)


def write_state(state: dict[str, str]) -> None:
    """Write state dict to the .state file. Values are quoted for shell safety."""
    state_file = get_state_file()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    lines = [f'{k}="{v}"' for k, v in sorted(state.items())]
    state_file.write_text("\n".join(lines) + "\n")


def read_env_key(key: str, default: str = "") -> str:
    """Read a single key from .env, handling quoted values."""
    env_file = get_env_file()
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or "=" not in stripped:
                continue
            k, v = stripped.split("=", 1)
            if k.strip() == key:
                v = v.strip()
                # Strip surrounding quotes
                if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
                    v = v[1:-1]
                return v
    return default
