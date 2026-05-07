#!/usr/bin/env bash
# Launches a new macOS Terminal.app window running watch-todos.sh for the
# current Claude Code project. Invoked by the /todos-watch slash command.
#
# Project dir resolution: $CLAUDE_PROJECT_DIR (set by Claude Code), else $PWD.

set -eu

if [ "$(uname)" != "Darwin" ]; then
  echo "ERROR: /todos-watch currently supports macOS only." >&2
  echo "On Linux/Windows, run scripts/watch-todos.sh in a terminal manually:" >&2
  echo "  bash $(dirname "$0")/watch-todos.sh \"\$PWD\"" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WATCH_SCRIPT="${SCRIPT_DIR}/watch-todos.sh"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"

if [ ! -f "$WATCH_SCRIPT" ]; then
  echo "ERROR: watch-todos.sh not found at $WATCH_SCRIPT" >&2
  exit 1
fi

# Escape single quotes for embedding in AppleScript double-quoted string.
escape() {
  printf '%s' "$1" | sed "s/'/'\\\\''/g"
}

WATCH_ESC=$(escape "$WATCH_SCRIPT")
PROJECT_ESC=$(escape "$PROJECT_DIR")

osascript <<EOF
tell application "Terminal"
  activate
  do script "clear && exec bash '${WATCH_ESC}' '${PROJECT_ESC}'"
end tell
EOF

echo "Opened a new Terminal window watching: ${PROJECT_DIR}/.claude/todos/"
