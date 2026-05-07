#!/usr/bin/env bash
# Remove the .paused flag for the current project so render_todos.py
# resumes mirroring on the next TodoWrite call.

set -euo pipefail

if [[ -z "${CLAUDE_PROJECT_DIR:-}" ]]; then
  echo "ERROR: CLAUDE_PROJECT_DIR is not set — cannot locate project todos dir." >&2
  exit 1
fi

flag="${CLAUDE_PROJECT_DIR}/.claude/todos/.paused"
if [[ -f "$flag" ]]; then
  rm -f "$flag"
  echo "OK — resumed (removed $flag)"
else
  echo "OK — already resumed (no flag at $flag)"
fi
