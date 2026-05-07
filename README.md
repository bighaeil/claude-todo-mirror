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
at `.claude-plugin/marketplace.json` so you can install it via the standard
plugin commands.

> **Heads up**: `/plugin ...` commands only work in the Claude Code **CLI**
> (terminal), not in the Desktop app. Once installed, slash commands like
> `/todos-watch` work in both Desktop and CLI.

Open a Claude Code CLI session and enter these two commands **separately**
(do not paste them on the same line — Claude Code parses the second one as
part of the first command's URL):

```
/plugin marketplace add bighaeil/claude-todo-mirror
```

Then, on its own:

```
/plugin install claude-todo-mirror@claude-todo-mirror
```

When the install dialog asks for scope, **"Install for you (user scope)"** is
the right choice for personal use — the plugin becomes available across every
project and any Claude Code surface (CLI, Desktop).

For local development without going through the marketplace:

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

> **Prerequisite** — this command depends on the macOS `watch` CLI. Without
> it, the new Terminal window opens but immediately exits with
> `command not found: watch`.
>
> ```bash
> brew install watch
> ```
>
> The core hook (`TodoWrite` → markdown mirroring) only needs Python 3 and
> works on any OS. `watch` is a dependency **for the terminal live view
> only** — if you open the markdown files directly in VS Code or Obsidian,
> you don't need it.

Don't want to leave an editor pinned? Run the bundled slash command from any
Claude Code session:

```
/todos-watch
```

This opens a new **macOS Terminal** window running `watch -d` against this
project's `.claude/todos/`. It refreshes every 10 seconds and highlights any
line that changes — every `TodoWrite` call shows up live without you scrolling
back through chat or copy-pasting paths.

### Environment compatibility

| Environment | `/todos-watch` | Fallback |
| --- | --- | --- |
| macOS + `watch` installed | Works | — |
| macOS + `watch` missing | Fails | `brew install watch` |
| Linux | Unsupported (osascript-based) | Run `bash <plugin-dir>/scripts/watch-todos.sh "$PWD"` directly |
| Windows | Unsupported | Same as Linux, via WSL or git-bash |

The `<plugin-dir>` path under `~/.claude/plugins/cache/claude-todo-mirror/` is
the script's location once installed via the marketplace.

## Pause and resume mirroring (`/todos-pause`, `/todos-resume`)

Want to keep the plugin installed but temporarily stop markdown mirroring
(e.g. during a quick scratchpad session you don't want to record)? Two
slash commands toggle a per-project flag:

```
/todos-pause     # creates .claude/todos/.paused → mirroring suspended
/todos-resume    # removes the flag → mirroring active again
```

When `.paused` exists, every `TodoWrite` call still triggers the hook, but
`render_todos.py` short-circuits on the flag and writes nothing — no
`session-*.md` updates, and any open `/todos-watch` monitor stays frozen.

Notes:

- The flag is **per-project** (one flag per `${CLAUDE_PROJECT_DIR}/.claude/todos/`).
  Pausing one project does not affect mirroring in another.
- `TodoWrite` token usage is **not affected** — Claude still calls the tool
  based on its own judgment. Only the file mirroring is suppressed.
- The `.paused` file itself is empty; you can also create or remove it
  manually with `touch` / `rm` if you prefer.

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
            └─ short-circuits early if .claude/todos/.paused exists

commands/todos-watch.md
  └─ /todos-watch
       └─ scripts/launch-watch.sh    (osascript → new Terminal window)
            └─ scripts/watch-todos.sh   (watch -d on the mirror files)

commands/todos-pause.md
  └─ /todos-pause
       └─ scripts/pause.sh           (touch .claude/todos/.paused)

commands/todos-resume.md
  └─ /todos-resume
       └─ scripts/resume.sh          (rm -f .claude/todos/.paused)
```

The hook runs synchronously after every `TodoWrite`, parses the
`tool_input.todos` array, and rewrites the session file + index. Failures are
logged to `stderr` and never block the tool — at worst your file goes stale.

## Configuration

None. The plugin uses three well-known paths under `${CLAUDE_PROJECT_DIR}/.claude/todos/`:

- `session-<session_id>.md` — per-session checklist (auto-generated by the hook)
- `_index.md` — summary table of all sessions in the project (auto-regenerated)
- `.paused` — empty toggle flag; when present, the hook writes nothing.
  Created by `/todos-pause`, removed by `/todos-resume`. You can also create
  or remove it manually with `touch` / `rm`.

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

> **주의**: `/plugin ...` 명령은 **Claude Code 터미널 CLI에서만** 동작합니다
> (Desktop 앱에서는 안 됨). 설치 후 `/todos-watch` 같은 슬래시 명령은 Desktop과
> CLI 양쪽에서 모두 사용 가능합니다.

CLI 세션에서 두 명령을 **각각 따로** 입력하세요 — 한 줄에 같이 붙이면 Claude
Code가 두 번째 명령을 첫 명령의 URL 일부로 해석해서 실패합니다.

```
/plugin marketplace add bighaeil/claude-todo-mirror
```

그 다음 별도로:

```
/plugin install claude-todo-mirror@claude-todo-mirror
```

설치 스코프 선택 다이얼로그가 뜨면 **"Install for you (user scope)"** 권장
— 모든 프로젝트에서 사용 가능하고 Desktop에서도 슬래시 명령이 잡힙니다.

또는 hook 직접 등록 (위 영어 섹션 "Manual hook registration" 참조).

### 터미널 실시간 모니터링 — `/todos-watch`

`/todos-watch`로 새 macOS Terminal 창에서 todo 변경을 실시간 확인할 수 있습니다.
사전에 `brew install watch` 필요 (macOS 기본 미설치).

상세 사전 요구사항·OS 호환성·Linux/Windows 대안은 위 영문 섹션
[Live terminal monitor (`/todos-watch`)](#live-terminal-monitor-todos-watch)
를 참조하세요.

### 미러링 일시정지·재개 — `/todos-pause`, `/todos-resume`

플러그인은 그대로 두고 markdown 미러링만 잠시 끄고 싶을 때 사용합니다.

- `/todos-pause` → 현재 프로젝트의 `.claude/todos/.paused` flag 생성. 이후
  `TodoWrite` 호출이 일어나도 markdown 파일은 갱신되지 않습니다 (열어둔
  `/todos-watch` 모니터도 정지된 상태로 보임).
- `/todos-resume` → flag 제거. 다음 `TodoWrite` 호출부터 다시 갱신됩니다.

flag는 **프로젝트별**이라 다른 프로젝트의 미러링에는 영향 없습니다. 또한
`TodoWrite`의 토큰 사용 자체는 그대로 — Claude가 도구를 호출하는 것은 막지
않고 markdown 저장만 중단합니다.

상세는 위 영문 섹션 [Pause and resume mirroring](#pause-and-resume-mirroring-todos-pause-todos-resume) 참조.
