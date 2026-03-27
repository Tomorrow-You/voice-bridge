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

const MIN_PYTHON = [3, 10];

function findPython() {
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
          return cmd;
        }
      }
    } catch {
      // Command not found, try next
    }
  }
  return null;
}

function isPackageInstalled(python) {
  try {
    execFileSync(python, ["-c", "import voice_bridge"], { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

function main() {
  const python = findPython();
  if (!python) {
    process.stderr.write(
      `Error: Python ${MIN_PYTHON.join(".")}+ is required but not found.\n` +
        "Install Python from https://python.org or via your package manager.\n"
    );
    process.exit(1);
  }

  if (!isPackageInstalled(python)) {
    process.stderr.write("Installing ai-voice-bridge[mcp]...\n");
    try {
      execFileSync(python, ["-m", "pip", "install", "ai-voice-bridge[mcp]"], {
        stdio: "inherit",
      });
    } catch {
      process.stderr.write(
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
    process.stderr.write(`Failed to start MCP server: ${err.message}\n`);
    process.exit(1);
  });

  child.on("exit", (code) => {
    process.exit(code ?? 0);
  });
}

main();
