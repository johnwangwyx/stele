#!/usr/bin/env python3
"""stele - install durable task state into a project.

Creates stele/, copies the protocol and the indexer into it, and writes an idempotent
pointer block into every harness instruction file this project uses.

The protocol and indexer are copied rather than referenced on purpose: the project then
carries its own instructions, so an agent that does not have this skill installed can
still follow them. Re-run to update the copies.

Usage:
    python3 scripts/install.py                  install into the current directory
    python3 scripts/install.py --root PATH      install into another project
    python3 scripts/install.py --dry-run        show what would change
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

BEGIN = "<!-- stele:begin - managed block, edits here are overwritten -->"
END = "<!-- stele:end -->"

POINTER = f"""{BEGIN}
## Project state (stele)

This repo keeps durable task state in `stele/`. Before doing anything else, including when
given a direct instruction - it may already be half-done:

1. Run `python3 stele/bin/index.py` (or read `stele/TASKS.md`) to find what is active.
2. Read `stele/PROJECT_CONTEXT.md` and the active task file in `stele/tasks/`.
3. Follow the PASS procedure in `stele/PROTOCOL.md`: run the open step's `verify:`, compare
   the worktree against its `anchor:`, then state back the goal, next action, and top risk
   before editing anything.

Write progress into the active task file **as you work**, not at the end of the session -
a session that hits a limit or crashes never gets to write a summary.
{END}"""

# Shared instruction files: always written, since these two cover most harnesses.
ALWAYS = ["AGENTS.md", "CLAUDE.md"]

# Shared instruction files: only touched when the project already uses them.
IF_PRESENT_FILES = ["GEMINI.md", ".github/copilot-instructions.md"]

# Dedicated files we fully own, created only when the harness directory exists.
IF_PRESENT_DIRS = {
    ".cursor/rules": (
        "stele.mdc",
        "---\ndescription: stele project state - read before acting\nalwaysApply: true\n---\n\n",
    ),
    ".kiro/steering": ("stele.md", ""),
}


def upsert_block(path: Path, dry: bool) -> str:
    """Insert or replace the managed block in a shared instructions file."""
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if BEGIN in existing and END in existing:
        head = existing.split(BEGIN)[0]
        tail = existing.split(END, 1)[1]
        new = head + POINTER + tail
        action = "updated block in"
    else:
        if not existing:
            new = POINTER + "\n"
        elif existing.endswith("\n\n"):
            new = existing + POINTER + "\n"
        elif existing.endswith("\n"):
            new = existing + "\n" + POINTER + "\n"
        else:
            new = existing + "\n\n" + POINTER + "\n"
        action = "added block to" if existing else "created"
    if new == existing:
        return f"unchanged        {path}"
    if not dry:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new, encoding="utf-8")
    return f"{action:16} {path}"


def write_owned(path: Path, prefix: str, dry: bool) -> str:
    content = prefix + POINTER + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return f"unchanged        {path}"
    if not dry:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return f"{'wrote':16} {path}"


def copy(src: Path, dst: Path, dry: bool, overwrite: bool) -> str:
    if dst.exists() and not overwrite:
        return f"kept existing    {dst}"
    if dst.exists() and dst.read_text(encoding="utf-8") == src.read_text(encoding="utf-8"):
        return f"unchanged        {dst}"
    if not dry:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    return f"{'copied':16} {dst}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".", help="project root to install into")
    ap.add_argument("--dry-run", action="store_true", help="print planned changes only")
    args = ap.parse_args()

    skill = Path(__file__).resolve().parent.parent
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"stele: {root} is not a directory", file=sys.stderr)
        return 2

    stele = root / "stele"
    dry = args.dry_run
    actions: list[str] = []

    for d in (stele / "tasks" / "archive", stele / "bin"):
        if not d.is_dir():
            if not dry:
                d.mkdir(parents=True, exist_ok=True)
            actions.append(f"{'created dir':16} {d}")

    # Copied every run so the project tracks the installed version.
    actions.append(copy(skill / "PROTOCOL.md", stele / "PROTOCOL.md", dry, overwrite=True))
    actions.append(copy(skill / "scripts" / "index.py", stele / "bin" / "index.py", dry, overwrite=True))
    actions.append(
        copy(skill / "templates" / "task.md", stele / "bin" / "task-template.md", dry, overwrite=True)
    )

    # Never overwritten - these hold the project's own content.
    actions.append(
        copy(skill / "templates" / "PROJECT_CONTEXT.md", stele / "PROJECT_CONTEXT.md", dry, overwrite=False)
    )
    actions.append(copy(skill / "templates" / "TASKS.md", stele / "TASKS.md", dry, overwrite=False))

    for name in ALWAYS:
        actions.append(upsert_block(root / name, dry))
    for name in IF_PRESENT_FILES:
        target = root / name
        already_used = target.exists()
        in_existing_dir = target.parent != root and target.parent.is_dir()
        if already_used or in_existing_dir:
            actions.append(upsert_block(target, dry))
    for rel, (filename, prefix) in IF_PRESENT_DIRS.items():
        if (root / rel).is_dir():
            actions.append(write_owned(root / rel / filename, prefix, dry))

    print(f"stele -> {root}{'  (dry run)' if dry else ''}\n")
    for a in actions:
        print(f"  {a}")

    if not dry:
        print(
            "\nNext:\n"
            "  1. Fill in stele/PROJECT_CONTEXT.md - invariants first, they are what agents trust.\n"
            "  2. Create a task: copy stele/bin/task-template.md to stele/tasks/0001-<slug>.md\n"
            "  3. Run: python3 stele/bin/index.py\n"
            "  4. Commit stele/ - durability across machines and agents is the point."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
