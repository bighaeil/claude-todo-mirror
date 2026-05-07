#!/usr/bin/env bash
# Create the .paused flag for the current project so render_todos.py
# becomes a no-op until /todos-resume is run.

set -euo pipefail

if [[ -z "${CLAUDE_PROJECT_DIR:-}" ]]; then
  echo "ERROR: CLAUDE_PROJECT_DIR is not set — cannot locate project todos dir." >&2
  exit 1
fi

todos_dir="${CLAUDE_PROJECT_DIR}/.claude/todos"
mkdir -p "$todos_dir"
touch "$todos_dir/.paused"

echo "OK — paused (flag at $todos_dir/.paused)"
