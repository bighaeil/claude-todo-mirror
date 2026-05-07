#!/usr/bin/env python3
"""
claude-todo-mirror — PostToolUse hook for TodoWrite.

Reads JSON payload from stdin (Claude Code hook protocol), extracts the
TodoWrite tool input, and writes a per-session markdown file + a global
index that you can keep open in any editor for an always-visible task view.

Output layout (relative to the project root / CLAUDE_PROJECT_DIR):

    .claude/todos/
    ├── session-<session_id>.md      # per-session checklist
    └── _index.md                    # all sessions summary

Hierarchy convention:
    The TodoWrite content field with leading whitespace is treated as a
    nested item. 2 spaces (or 1 tab) = 1 indent level.

    [
      {"content": "Parent task"},
      {"content": "  Child task A"},
      {"content": "  Child task B"},
    ]

Status mapping:
    pending      → [ ]
    in_progress  → [▶]
    completed    → [x]

Exit code is always 0 (non-blocking) — failures are logged to stderr.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS_BOX = {
    "pending": "[ ]",
    "in_progress": "[▶]",
    "completed": "[x]",
}


def parse_indent(content: str) -> tuple[int, str]:
    """Return (level, stripped_text). 2 spaces or 1 tab = 1 level."""
    stripped_left = content.lstrip(" \t")
    leading = content[: len(content) - len(stripped_left)]
    if "\t" in leading:
        level = leading.count("\t")
    else:
        level = len(leading) // 2
    return level, stripped_left.rstrip()


def render_session_md(session_id: str, todos: list[dict[str, Any]], project_root: str) -> str:
    now_str = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")

    if not todos:
        return (
            f"# Session `{session_id[:12]}`\n\n"
            f"**Project**: `{project_root}`\n"
            f"**Updated**: {now_str}\n\n"
            "_(todo list cleared)_\n"
        )

    total = len(todos)
    done = sum(1 for t in todos if t.get("status") == "completed")
    in_prog = [t for t in todos if t.get("status") == "in_progress"]
    pct = round(done / total * 100) if total else 0

    lines: list[str] = []
    lines.append(f"# Session `{session_id[:12]}`")
    lines.append("")
    lines.append(f"**Project**: `{project_root}`")
    lines.append(f"**Updated**: {now_str}")
    lines.append(f"**Progress**: {done}/{total} ({pct}%)")
    if in_prog:
        active = in_prog[0]
        active_form = active.get("activeForm") or active.get("content", "")
        _, active_body = parse_indent(active_form)
        lines.append(f"**Now**: ▶ {active_body}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for t in todos:
        status = t.get("status", "pending")
        box = STATUS_BOX.get(status, "[ ]")
        content = t.get("content", "")
        level, body = parse_indent(content)
        indent = "  " * level
        if status == "in_progress":
            active_form = t.get("activeForm")
            if active_form:
                _, body = parse_indent(active_form)
        lines.append(f"{indent}- {box} {body}")

    return "\n".join(lines) + "\n"


def _extract_meta(text: str) -> dict[str, str]:
    meta = {"progress": "-", "now": "-", "updated": "-"}
    for line in text.splitlines():
        if line.startswith("**Progress**:"):
            meta["progress"] = line.split(":", 1)[1].strip()
        elif line.startswith("**Now**:"):
            meta["now"] = line.split(":", 1)[1].strip().lstrip("▶ ").strip() or "-"
        elif line.startswith("**Updated**:"):
            meta["updated"] = line.split(":", 1)[1].strip()
    return meta


def update_index(todos_dir: Path) -> None:
    session_files = sorted(todos_dir.glob("session-*.md"))
    rows: list[dict[str, Any]] = []
    for sf in session_files:
        try:
            text = sf.read_text(encoding="utf-8")
        except Exception:
            continue
        sid_full = sf.stem.replace("session-", "")
        meta = _extract_meta(text)
        mtime = datetime.fromtimestamp(sf.stat().st_mtime, tz=timezone.utc).astimezone()
        rows.append(
            {
                "sid_short": sid_full[:8],
                "sid_full": sid_full,
                "progress": meta["progress"],
                "now": meta["now"],
                "updated": meta["updated"],
                "mtime": mtime,
                "fname": sf.name,
            }
        )

    rows.sort(key=lambda r: r["mtime"], reverse=True)

    now_str = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    out: list[str] = []
    out.append("# Claude Todo Mirror — Index")
    out.append("")
    out.append(f"_Last refresh: {now_str}_")
    out.append("")
    if not rows:
        out.append("_(no sessions yet)_")
    else:
        out.append("| Session | Progress | Now | File |")
        out.append("| --- | --- | --- | --- |")
        for r in rows:
            now_cell = (r["now"] or "-").replace("|", "/")
            out.append(
                f"| `{r['sid_short']}` | {r['progress']} | {now_cell} | "
                f"[{r['fname']}](./{r['fname']}) |"
            )
    out.append("")

    (todos_dir / "_index.md").write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception as exc:
        print(f"[claude-todo-mirror] stdin parse failed: {exc}", file=sys.stderr)
        return 0

    session_id = payload.get("session_id") or "unknown"
    cwd = (
        payload.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )

    tool_input = payload.get("tool_input") or {}
    todos = tool_input.get("todos") or []
    if not todos:
        tr = payload.get("tool_response") or {}
        if isinstance(tr, dict):
            todos = tr.get("todos") or []

    try:
        project_root = Path(cwd)
        todos_dir = project_root / ".claude" / "todos"
        if (todos_dir / ".paused").exists():
            return 0
        todos_dir.mkdir(parents=True, exist_ok=True)

        md = render_session_md(session_id, todos, str(project_root))
        out_path = todos_dir / f"session-{session_id}.md"
        out_path.write_text(md, encoding="utf-8")

        update_index(todos_dir)
    except Exception as exc:
        print(f"[claude-todo-mirror] write failed: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
