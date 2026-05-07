#!/usr/bin/env bash
# Live-watch helper for claude-todo-mirror.
#
# Usage:
#   watch-todos.sh [PROJECT_DIR]
#
# Resolution order for PROJECT_DIR:
#   1. $1 argument
#   2. $CLAUDE_PROJECT_DIR env var
#   3. current working directory
#
# Refreshes every 10s and highlights diffs. Shows the project-wide _index.md
# on top, then the most recently updated session file below it.

set -u

PROJECT_DIR="${1:-${CLAUDE_PROJECT_DIR:-$PWD}}"
TODOS_DIR="${PROJECT_DIR%/}/.claude/todos"

if ! command -v watch >/dev/null 2>&1; then
  echo "ERROR: 'watch' is not installed." >&2
  echo "Install it with: brew install watch" >&2
  exit 1
fi

watch -n 10 -d "
  echo '== INDEX (${TODOS_DIR}/_index.md) ==';
  if [ -f \"${TODOS_DIR}/_index.md\" ]; then
    cat \"${TODOS_DIR}/_index.md\";
  else
    echo '(no _index.md yet — waiting for first TodoWrite call)';
  fi;
  echo;
  echo '== LATEST SESSION ==';
  LATEST=\$(find \"${TODOS_DIR}\" -maxdepth 1 -name 'session-*.md' -type f 2>/dev/null | xargs stat -f '%m %N' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-);
  if [ -n \"\$LATEST\" ]; then
    echo \"-- \$(basename \"\$LATEST\") --\";
    cat \"\$LATEST\";
  else
    echo '(no session-*.md yet)';
  fi
"
