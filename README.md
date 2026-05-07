# claude-todo-mirror

A Claude Code plugin that mirrors `TodoWrite` state to per-session markdown files
with hierarchical checkboxes — keep an always-visible task view open in VS Code,
Obsidian, or any markdown viewer instead of scrolling back through chat history.

## The problem

Claude Code's inline `TodoWrite` updates scroll out of view as the conversation
grows. When you want to know what's left, you scroll back through messages.
The built-in **Tasks** panel helps, but it's tied to one window and doesn't
expose a hierarchy or an external file you can pin in another editor.

## What this plugin does

On every `TodoWrite` call, a hook writes a markdown checklist for **the current
session** to `<project>/.claude/todos/session-<id>.md` and refreshes
`_index.md` with all sessions in this project. Open either file in VS Code,
Obsidian, or `tail -f` it from a terminal — it auto-updates.

### Sample output

```
# Session `abc12345-...`

**Project**: `/Users/me/code/my-app`
**Updated**: 2026-05-07 17:40:21 KST
**Progress**: 2/7 (29%)
**Now**: ▶ Verifying render_todos.py

---

- [x] Plugin scaffolding
- [x] Hook script
- [▶] Verifying render_todos.py
  - [ ] edge case: indented children
  - [ ] edge case: empty todos
- [ ] README + LICENSE
- [ ] GitHub push
```

### Hierarchy convention

`TodoWrite` items are flat by spec, so this plugin uses leading whitespace in
the `content` field as the hierarchy signal. Two spaces (or one tab) = one
indent level:

```python
TodoWrite([
    {"content": "Parent task",      "status": "in_progress", "activeForm": "Working"},
    {"content": "  Child task A",   "status": "pending",     "activeForm": "..."},
    {"content": "  Child task B",   "status": "pending",     "activeForm": "..."},
    {"content": "Sibling task",     "status": "pending",     "activeForm": "..."},
])
```

Tell Claude in your project's `CLAUDE.md` (or per-prompt) to follow that
convention when it writes nested todos.

### Status mapping

| TodoWrite status | Rendered |
| --- | --- |
| `pending` | `[ ]` |
| `in_progress` | `[▶]` |
| `completed` | `[x]` |

The first `in_progress` item is also pulled into a `Now: ▶ ...` header line so
you can see the active task at a glance.

### Per-session isolation

Each Claude Code session gets its own `session-<id>.md`. Run multiple sessions
in parallel — the plugin keeps them separate. `_index.md` summarizes all of
them in one table sorted by last activity:

```
| Session | Progress | Now | File |
| --- | --- | --- | --- |
| `abc12345` | 2/7 (29%) | Verifying render_todos.py | [session-abc...md](./...) |
| `def67890` | 4/4 (100%) | -                         | [session-def...md](./...) |
```

## Install

This repo is a **single-plugin marketplace** — `marketplace.json` is committed
at `.claude-plugin/marketplace.json` so you can install it in one shot.

In any Claude Code session:

```
/plugin marketplace add bighaeil/claude-todo-mirror
/plugin install claude-todo-mirror@claude-todo-mirror
```

Or for local development (no install needed):

```
claude --plugin-dir /path/to/claude-todo-mirror
```

After install, every `TodoWrite` call in any project will create
`.claude/todos/` under that project's root.

### Manual hook registration (without `/plugin install`)

If you can't or don't want to use the plugin marketplace, drop this into your
project's `.claude/settings.local.json` (or user `~/.claude/settings.json`):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "TodoWrite",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /absolute/path/to/claude-todo-mirror/scripts/render_todos.py"
          }
        ]
      }
    ]
  }
}
```

### Recommended workflow

1. Open `<project>/.claude/todos/_index.md` in VS Code (or Obsidian) and pin
   the tab.
2. Or open the active session file `session-<your-session>.md` directly.
3. Work as usual — the file refreshes on every `TodoWrite` call.

For multi-session overview, the `_index.md` is the single source of truth.

## Live terminal monitor (`/todos-watch`)

Don't want to leave an editor pinned? Run the bundled slash command from any
Claude Code session:

```
/todos-watch
```

This opens a new **macOS Terminal** window running `watch -d` against this
project's `.claude/todos/`. It refreshes once per second and highlights any
line that changes — every `TodoWrite` call shows up live without you scrolling
back through chat or copy-pasting paths.

Requirements: macOS, `watch` (`brew install watch`).
On Linux/Windows, run the script directly:

```bash
bash <plugin-dir>/scripts/watch-todos.sh "$PWD"
```

## Requirements

- Claude Code (any version that supports the plugin system + `PostToolUse` hooks)
- Python 3 (any 3.8+ available on `python3` in `PATH`)
- macOS + `watch` (only for `/todos-watch`; the core hook works on any platform)

No other dependencies — the hook is a single self-contained Python file.

## How it works

```
hooks/hooks.json
  └─ PostToolUse(matcher=TodoWrite)
       └─ scripts/render_todos.py    (reads stdin JSON, writes markdown)

commands/todos-watch.md
  └─ /todos-watch
       └─ scripts/launch-watch.sh    (osascript → new Terminal window)
            └─ scripts/watch-todos.sh   (watch -d on the mirror files)
```

The hook runs synchronously after every `TodoWrite`, parses the
`tool_input.todos` array, and rewrites the session file + index. Failures are
logged to `stderr` and never block the tool — at worst your file goes stale.

## Configuration

None. The plugin uses two well-known paths:

- `${CLAUDE_PROJECT_DIR}/.claude/todos/session-<session_id>.md`
- `${CLAUDE_PROJECT_DIR}/.claude/todos/_index.md`

Add `.claude/todos/` to your project's `.gitignore` if you don't want
session files committed.

## License

MIT — see [LICENSE](./LICENSE).

---

## 한국어 요약

Claude Code의 `TodoWrite` 결과는 인라인 마크다운으로만 출력되고 대화가 길어지면
스크롤 위로 사라집니다. 진행 상황을 보려면 매번 위로 거슬러 올라가야 하죠.

이 플러그인은 `TodoWrite` 호출이 일어날 때마다 **현재 세션의 todo를
계층 체크박스가 있는 markdown 파일로 자동 저장**합니다.

```
<프로젝트>/.claude/todos/
├── session-<세션ID>.md    # 채널별 체크리스트
└── _index.md              # 모든 채널 요약 표
```

VS Code · Obsidian · 마크다운 뷰어 등에 파일을 한 번 열어 두기만 하면, 매번
자동으로 갱신되는 살아있는 todo 뷰가 됩니다. 채팅 채널이 여러 개여도 세션
ID로 분리되어 헷갈리지 않습니다.

### 들여쓰기 규칙

```python
TodoWrite([
    {"content": "상위 작업"},
    {"content": "  하위 작업 1"},   # 2 space → 1 단계 들여쓰기
    {"content": "  하위 작업 2"},
])
```

`CLAUDE.md`에 이 규칙을 알려주면 Claude가 자동으로 계층 todo를 만들어 줍니다.

### 설치

```
/plugin marketplace add bighaeil/claude-todo-mirror
/plugin install claude-todo-mirror@claude-todo-mirror
```

또는 hook 직접 등록 (위 영어 섹션 "Manual hook registration" 참조).

### 터미널 실시간 모니터링 — `/todos-watch`

별도의 에디터를 열어두기 번거롭다면, 새 Claude Code 세션 안에서 그냥
`/todos-watch`만 입력하세요:

```
/todos-watch
```

새 **macOS Terminal** 창이 자동으로 뜨면서 1초 간격으로 갱신되는 watch가
시작됩니다 (`watch -d`로 변경된 줄은 강조 표시). 매 `TodoWrite` 호출이
스크롤 없이 곧바로 보입니다.

요구사항: macOS, `watch` (`brew install watch`).
