---
description: Pause TodoWrite markdown mirroring for this project (creates .paused flag)
allowed-tools: Bash(bash:*)
---

Status: !`bash ${CLAUDE_PLUGIN_ROOT}/scripts/pause.sh`

Mirroring paused for this project. From now on, every `TodoWrite` call in this project still runs the hook, but the hook short-circuits early — no `.claude/todos/session-*.md` will be updated and any open `/todos-watch` monitor will appear frozen.

Run `/todos-resume` to re-enable. (Note: this only stops the *file mirroring*; Claude still calls `TodoWrite` based on its own judgment, so token usage from the tool call itself is unchanged.)
