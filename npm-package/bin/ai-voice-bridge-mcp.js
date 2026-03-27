#!/usr/bin/env node

/**
 * npm shim for Voice Bridge MCP server.
 *
 * Checks for Python 3.10+, installs the pip package if needed,
 * then launches the MCP server connected to stdio.
 *
 * Usage in Claude Desktop / Cursor config:
 *   { "command": "npx", "args": ["ai-voice-bridge"] }
 */

const { execFileSync, spawn } = require("child_process");
const os = require("os");

const MIN_PYTHON = [3, 10];

function warn(msg) {
  process.stderr.write(`[voice-bridge] ${msg}\n`);
}

function findPython() {
  let bestFound = null; // track any Python we find (even if too old)

  for (const cmd of ["python3", "python"]) {
    try {
      const version = execFileSync(cmd, ["--version"], {
        encoding: "utf-8",
        stdio: ["ignore", "pipe", "pipe"],
      }).trim();
      const match = version.match(/Python (\d+)\.(\d+)/);
      if (match) {
        const major = parseInt(match[1], 10);
        const minor = parseInt(match[2], 10);
        if (
          major > MIN_PYTHON[0] ||
          (major === MIN_PYTHON[0] && minor >= MIN_PYTHON[1])
        ) {
          return { cmd, version };
        }
        // Python found but too old
        bestFound = { cmd, version };
      }
    } catch {
      // Command not found, try next
    }
  }
  return bestFound ? { cmd: null, version: bestFound.version } : null;
}

function isPackageInstalled(python) {
  try {
    execFileSync(python, ["-c", "import voice_bridge"], { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

function hasPip(python) {
  try {
    execFileSync(python, ["-m", "pip", "--version"], {
      stdio: ["ignore", "pipe", "pipe"],
    });
    return true;
  } catch {
    return false;
  }
}

function checkAudioEnvironment() {
  const platform = os.platform();

  if (platform === "darwin") {
    // macOS always has afplay
    return;
  }

  const players =
    platform === "win32"
      ? ["ffplay", "mpv"]
      : ["mpv", "ffplay", "aplay", "paplay"];

  for (const player of players) {
    try {
      execFileSync(platform === "win32" ? "where" : "which", [player], {
        stdio: ["ignore", "pipe", "pipe"],
      });
      return; // found one
    } catch {
      // not found, try next
    }
  }

  const installHint =
    platform === "win32"
      ? "Install ffmpeg (includes ffplay): https://ffmpeg.org/download.html\n" +
        "  Or install mpv: https://mpv.io/installation/"
      : "Install an audio player:\n" +
        "  Ubuntu/Debian: sudo apt install mpv   (or: sudo apt install ffmpeg)\n" +
        "  Fedora/RHEL:   sudo dnf install mpv\n" +
        "  Arch:          sudo pacman -S mpv";

  warn(
    "WARNING: No audio player detected.\n" +
      "  Voice Bridge requires mpv, ffplay, or another audio player to produce sound.\n" +
      "  The MCP server will start, but speak commands will fail silently.\n\n" +
      `  ${installHint}\n`
  );

  // Check if we're likely headless (no DISPLAY on Linux, no audio device)
  if (platform === "linux" && !process.env.DISPLAY && !process.env.WAYLAND_DISPLAY && !process.env.PULSE_SERVER) {
    warn(
      "WARNING: No display server or PulseAudio detected — this may be a headless environment.\n" +
        "  TTS audio playback requires a machine with speakers or audio output.\n" +
        "  Remote sessions (SSH, containers, CI) typically cannot play audio.\n"
    );
  }
}

function pythonInstallHint() {
  const platform = os.platform();
  if (platform === "darwin") {
    return (
      "Install Python on macOS:\n" +
      "  brew install python@3.12     (recommended)\n" +
      "  Or download from https://python.org/downloads/"
    );
  } else if (platform === "win32") {
    return (
      "Install Python on Windows:\n" +
      "  winget install Python.Python.3.12\n" +
      "  Or download from https://python.org/downloads/"
    );
  } else {
    return (
      "Install Python on Linux:\n" +
      "  Ubuntu/Debian: sudo apt install python3 python3-pip\n" +
      "  Fedora/RHEL:   sudo dnf install python3 python3-pip\n" +
      "  Arch:          sudo pacman -S python python-pip\n" +
      "  Or download from https://python.org/downloads/"
    );
  }
}

function main() {
  const result = findPython();

  if (!result || !result.cmd) {
    if (result && result.version) {
      // Python found but too old
      warn(
        `ERROR: Found ${result.version}, but Python ${MIN_PYTHON.join(".")}+ is required.\n\n` +
          `  ${pythonInstallHint()}\n`
      );
    } else {
      // No Python at all
      warn(
        `ERROR: Python ${MIN_PYTHON.join(".")}+ is required but not found on this system.\n\n` +
          `  ${pythonInstallHint()}\n`
      );
    }
    process.exit(1);
  }

  const python = result.cmd;

  // Check audio environment before proceeding
  checkAudioEnvironment();

  if (!isPackageInstalled(python)) {
    if (!hasPip(python)) {
      const platform = os.platform();
      const pipHint =
        platform === "linux"
          ? "  Ubuntu/Debian: sudo apt install python3-pip\n" +
            "  Fedora/RHEL:   sudo dnf install python3-pip"
          : `  ${python} -m ensurepip --upgrade`;
      warn(
        "ERROR: pip is not available. Install pip first:\n" +
          `  ${pipHint}\n\n` +
          "Then retry, or install manually:\n" +
          `  ${python} -m pip install "ai-voice-bridge[mcp]"\n`
      );
      process.exit(1);
    }

    warn("Installing ai-voice-bridge[mcp]...");
    try {
      execFileSync(python, ["-m", "pip", "install", "ai-voice-bridge[mcp]"], {
        stdio: "inherit",
      });
    } catch {
      warn(
        "Failed to install ai-voice-bridge. Try manually:\n" +
          `  ${python} -m pip install "ai-voice-bridge[mcp]"\n`
      );
      process.exit(1);
    }
  }

  // Launch the MCP server, connecting stdio directly
  const child = spawn(python, ["-m", "voice_bridge.mcp.server"], {
    stdio: "inherit",
  });

  child.on("error", (err) => {
    warn(`Failed to start MCP server: ${err.message}`);
    process.exit(1);
  });

  child.on("exit", (code) => {
    process.exit(code ?? 0);
  });
}

main();
