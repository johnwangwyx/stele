---
name: stele
description: Harness-agnostic project and task state so any coding agent can resume work another agent started. Use at session start, when resuming after a break, crash, rate limit, or context compaction, when switching agents or harnesses (Claude Code, Codex, Cursor, Gemini CLI, Kiro, Copilot), when the user says "continue where we left off" / "pick up where I stopped" / "what was I working on", and before and after any substantial piece of work so the next session can continue it without being told anything.
---

# stele

Keep durable project and task state on disk, in plain markdown, so work survives the
session that was doing it. Any agent in any harness can pick it up.

The record is written **while** work happens, not at the end. There is no handoff step,
because a handoff cannot be written by a session that has already died.

## Structure

```
stele/
  PROJECT_CONTEXT.md    invariants + current state
  TASKS.md              generated census — never edit by hand
  PROTOCOL.md           the PASS procedure (travels with the project)
  tasks/
    0007-slug.md        one live task per file, flat, stable path
    archive/            closed tasks, compacted
  bin/index.py          regenerates TASKS.md, validates invariants
```

Task files are the source of truth. `TASKS.md` is a rendered index — regenerate it, never
hand-edit it.

## Resume: run PASS at the start of every session

MUST run before editing anything, even when the user gives a direct instruction — the
instruction may already be half-done.

**1. Locate.** Regenerate and validate the census:

```bash
python3 stele/bin/index.py
```

If there is no shell, read `stele/TASKS.md` `## Active` as a hint, then confirm it against
the task files with `grep -l '^status: in-progress' stele/tasks/*.md`. Frontmatter wins over
the census on any disagreement.

**2. P — Project.** Read `stele/PROJECT_CONTEXT.md`. Treat `## Invariants` as fact and
`## Current state` as recent-but-checkable.

**3. A — Actions.** Read `stele/TASKS.md`. Do not read `tasks/archive/`.

**4. S — Situation.** Read only the active task file(s). For the open step:
   - run its `verify:` command
   - compare the worktree against its `anchor:` (`git status --short`, `git diff --stat <sha>`)
   - resolve what actually happened, per the table below

**5. S — Synthesis.** State back, in three lines: the goal, the next concrete action, and
the top risk. Then act — unless something diverges, in which case ask (see *Asking the
human*).

**6. Claim.** Only now write: set `owner:` and `updated_at:` on the task, and open a step.
Never write in steps 1–5; a crash mid-write corrupts the state you are about to rely on.

### Resolving the situation

| Observation | Meaning | Do |
|---|---|---|
| Step open, worktree ≠ anchor, `verify` fails | mid-surgery — a previous agent died partway | Reconcile first: finish the step's declared file list, or roll back to the anchor. Do not advance the plan. |
| Step open, worktree ≈ anchor | intent declared, little done | Continue the step normally. |
| No open step, `verify` passes | coherent | Advance to the next action. |
| No open step, worktree dirty | work was done without journaling | Do **not** start a new task. Diff against `HEAD`, attribute the changes to a task or open one for them, then continue. |
| Step open, `verify` passes | step likely completed but unrecorded | Close the step with its outcome, then continue. |

### Picking the task

- Exactly one `in-progress` → that one.
- Several → sort by `updated_at` descending, then:
  - `owner` is this session → resume it.
  - `owner` differs, `updated_at` < 30 min → another agent is live. Pick a different task.
  - `owner` differs, `updated_at` ≥ 30 min → abandoned. Adopt it, and re-run `verify:`
    before trusting anything the journal claims.
- None `in-progress` → still complete PASS steps 2–3, then ask the user what to work on.
  Do not silently start the top `todo`.

## Write state as you work

### Open a step — before acting, not after

MUST open a step before: editing files, running anything over ~2 minutes, any hard-to-reverse
operation (migration, deploy, delete, force-push, publish), or making a decision that binds
future work.

Append to `## Steps`, keep it to five lines, and mark it `[open]`:

```markdown
### 3. Switch the client retry mode to STANDARD  [open]
- opened: 2026-08-31T14:02Z by claude-opus-5 / claude-code
- anchor: main@a3f19c2, clean
- files: src/retry/RetryConfig.java, src/client/HttpClientFactory.java
- intent: set retryMode STANDARD, add token-bucket test
- verify: `<command that proves this step is done>`
```

`verify:` MUST be a command, not a description. A checklist item is a state you can observe,
not an action you remember taking. If nothing can prove it mechanically, write
`verify: none — <what a human must look at>`.

### Close a step

Mark `[done]`, add `outcome:`, then rewrite `## Summary` (3–5 lines, replace — do not append).
Restore coherence before closing: the tree should compile and the declared files should all be
in the same state.

### Record what failed

Append to `## Attempts` whenever an approach is abandoned: what was tried, why it was dropped,
and the evidence (`build.log:412`, an error string, a benchmark). **Append-only — never delete
an attempt.** A later agent will be tempted by the same dead end, and this is the only thing
that stops it paying for it again.

### Separate fact from assessment

`## Summary` and step `outcome:` are observations. Anything interpretive — "I think this is a
race condition" — goes in `## Assessment` with the evidence that supports it. A reader must be
able to tell what was measured from what was guessed; otherwise the next agent inherits a
hypothesis as if it were ground truth.

### Close a task

1. Close any open step.
2. Compact: keep goal, outcome, decisions, failed attempts, and verification. Delete the
   play-by-play.
3. Promote anything that binds future work into `PROJECT_CONTEXT.md` `## Decisions`.
4. `git mv stele/tasks/0007-slug.md stele/tasks/archive/`
5. Re-run `python3 stele/bin/index.py`.

## Asking the human

The human is the one constant across a harness switch, so they are the sender in the final S.
But they were not watching closely — that is why they delegated — so spend their attention
only where an artifact cannot answer.

Settle with the machine: did the step finish, what changed, which task is active, do the tests
pass. **Never ask a human what a command can tell you** — that trains them to rubber-stamp.

Ask the human: is this task still worth doing, which of these comes first, does decision X still
stand, and any place the record contradicts reality ("journal says done, verify fails — did you
revert something?").

Rules: surface divergence only, never the whole reconstruction. Closed questions with 2–4
options. Three lines maximum. If nothing diverges, say nothing and proceed.

If no human is available, do not guess. Re-derive from artifacts where possible; otherwise set
`status: blocked` with `blocked_on:` naming the question, and pick up something unambiguous.
Fabricating missing state is the only unrecoverable failure here.

**Record every answer** in the task file, or in `PROJECT_CONTEXT.md` if it binds future work.
Human attention is the scarcest resource in this system; never spend it twice on the same
question.

## Invariants

- At most **one `in-progress` task per owner**, and at most **3 in total**. Park a task
  (`status: paused`) before starting another.
- Closing or parking a task MUST close its open step. A non-active task with an open step means
  a broken tree that the next agent will skip past — `index.py` flags it.
- Parallel agents MUST declare `scope:` (file globs). Disjoint scopes are safe at any count;
  overlapping scopes are unsafe at two.
- `TASKS.md` is generated. Fix drift by regenerating, never by editing.
- Task paths are stable. Status lives in frontmatter, not in the directory. The only move is
  into `archive/` on close.
- No secrets, tokens, internal hostnames, or customer data — this directory is committed.

## Size budgets

Exceeding these makes the system cost more than it saves.

| File | Budget |
|---|---|
| `PROJECT_CONTEXT.md` | ~150 lines |
| `TASKS.md` | one line per task |
| task file | ~200 lines; roll old steps into `## Log (archived)` |
| session read | `PROJECT_CONTEXT` + `TASKS` + active task files only |

Never read `tasks/archive/` during a resume. Search it only when hunting specific history.

## Install

```bash
python3 scripts/install.py            # in the target project root
python3 scripts/install.py --dry-run  # show what would change
```

Creates `stele/`, copies `PROTOCOL.md` and `bin/index.py` into it, and writes an idempotent
pointer block into `AGENTS.md` and `CLAUDE.md`, plus any other harness config already present
(`.cursor/rules/`, `.kiro/steering/`, `GEMINI.md`, `.github/copilot-instructions.md`).

The copies are deliberate: the project carries its own protocol and tooling, so an agent with
this skill *not* installed can still follow it. Re-run install to update them.
