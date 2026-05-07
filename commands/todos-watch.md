---
description: Open a new Terminal window that live-watches this project's TodoWrite mirror files (macOS only)
allowed-tools: Bash(bash:*)
---

Launcher output: !`bash ${CLAUDE_PLUGIN_ROOT}/scripts/launch-watch.sh`

A new macOS Terminal window has been opened. It refreshes every second and highlights any line that changes — every `TodoWrite` call from this session shows up live without scrolling back through chat.

If the launcher output above shows an ERROR, common causes:
- Not running on macOS (the launcher uses `osascript` / Terminal.app)
- `watch` not installed (`brew install watch`)
- `${CLAUDE_PLUGIN_ROOT}` not expanded (plugin not loaded — install via `/plugin install`)
