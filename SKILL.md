---
name: stele
description: Durable project and task state in plain markdown, so any coding agent can resume work another agent started. Use at session start, when resuming after a break, crash, rate limit, or context compaction, when switching agents or harnesses (Claude Code, Codex, Cursor, Gemini CLI, Kiro, Copilot), when the user says "continue where we left off" / "pick up where I stopped" / "what was I working on", and before and after any substantial piece of work so the next session can continue it without being told anything. Sets itself up on first use in a project - no separate install step.
---

# stele

Keep project and task state on disk so work survives the session doing it. The record is
written **before** each step, not at session exit - a session that hits a rate limit or
crashes never gets to write a summary.

Nothing here is harness-specific. Any agent that can read files can follow it.

## 1. Bootstrap - only when `stele/` is missing

Check first: if `./stele/` exists, skip to §2. Otherwise create it now, then continue with
the user's actual request. Do not ask permission for this; it is six files and no
destructive change.

```
stele/
  PROJECT_CONTEXT.md    from the template below
  TASKS.md              from the template below
  tasks/                empty
  tasks/archive/        empty
```

Then add the pointer block (§1.2) so the *next* agent finds this without being told.

### 1.1 Starting files

`stele/PROJECT_CONTEXT.md` - fill in what you can infer from the repo, leave the rest blank
rather than guessing:

```markdown
# Project context

## Invariants
_Rarely changes. Wrong entries here cause confidently wrong actions._

- **What this is:**
- **Build:**
- **Test:**
- **Run locally:**
- **Layout:**
- **Conventions:**
- **Non-obvious constraints:**

_Last verified: YYYY-MM-DD_

## Current state
_Volatile. Update whenever it stops being true._

- **Active workstream:**
- **Known broken / deferred:**
- **Open questions:**

## Decisions
_Choices that bind future tasks. Promoted here when a task closes._

| Date | Decision | Why |
|---|---|---|

## Deferred
_Known-broken things tolerated on purpose. An entry with no `Until` is a TODO pretending
to be a decision._

| Item | Why tolerable | Until |
|---|---|---|
```

`stele/TASKS.md` - a generated census. Start it empty with the four headings: `## Active`,
`## Todo`, `## Blocked`, `## Paused`.

### 1.2 The pointer block

`stele/` is invisible to a fresh agent unless something points at it. Insert the block
below into the project's agent instruction files.

**Where:** add it to every one of these that already exists - `AGENTS.md`, `CLAUDE.md`,
`GEMINI.md`, `.github/copilot-instructions.md`, `.cursor/rules/stele.mdc`,
`.kiro/steering/stele.md`. If none exist, create `AGENTS.md` (plural - that is the
cross-harness convention, read by Codex, Cursor, Copilot, Gemini CLI, opencode and Kiro).

**How:** the block is delimited by markers. If the markers are already present, replace
what is between them. If not, append the whole block. Never add a second copy, and never
disturb the file's existing content - it is the user's.

For `.cursor/rules/stele.mdc`, prefix the file with:
`---\ndescription: stele project state - read before acting\nalwaysApply: true\n---`

The block deliberately restates the core procedure rather than only pointing at it, so an
agent that does not have this skill installed can still follow it correctly:

```markdown
<!-- stele:begin - managed block, edits here are overwritten -->
## Project state (stele)

Durable task state lives in `stele/`. Read it before anything else - including before a
direct instruction, which may already be half-done.

1. `grep -l '^status: in-progress' stele/tasks/*.md` to find the active task(s).
2. Read `stele/PROJECT_CONTEXT.md`, then `stele/TASKS.md`, then the active task file.
   Do not read `stele/tasks/archive/`.
3. In the active task find the step marked `[open]`, then reconcile it against reality:
   - Run its `verify:` command. Compare the worktree to its `anchor:` commit.
   - `verify` fails **and** files differ from the anchor: a previous session died
     mid-edit. Finish or roll back that step before starting anything new.
   - `verify` passes: the step finished but was not recorded. Write its outcome, continue.
   - No open step but the worktree is dirty: work happened without being journalled.
     Attribute it to a task before doing more.
4. State back the goal, the next concrete action, and the top risk. Ask the user only
   where the record contradicts itself or where intent is genuinely unclear.

While working, append to the active task's `## Steps` **before** you act - your intent, the
files you will touch, the current git sha, and a `verify:` command that will prove the step
finished. Written afterwards it is worthless: a session that is rate-limited or crashes
never gets to write anything.

Never delete entries under `## Attempts`. Never hand-edit `stele/TASKS.md`.
<!-- stele:end -->
```

## 2. Every session: resume with PASS

Run this before editing anything, even given a direct instruction.

**Locate.** `grep -l '^status: in-progress' stele/tasks/*.md`. Frontmatter always wins over
`TASKS.md` on any disagreement - the census is generated and can be stale.

**P - Project.** Read `stele/PROJECT_CONTEXT.md`. `## Invariants` is fact; `## Current
state` is recent but checkable.

**A - Actions.** Read `stele/TASKS.md`. Never read `tasks/archive/` during a resume.

**S - Situation.** Read only the active task file(s). For the open step: run its `verify:`,
compare the worktree to its `anchor:`, and resolve per the table below.

**S - Synthesis.** State back the goal, the next action, and the top risk in three lines.
Then act - unless something diverges, in which case ask (§4).

**Then claim.** Only now write: set `owner:` and `updated_at:`, and open a step. Never write
during the steps above; a crash mid-write corrupts the state you are about to rely on.

### Resolving the situation

| Observation | Meaning | Do |
|---|---|---|
| Step open, worktree ≠ anchor, `verify` fails | mid-surgery, a session died partway | Reconcile first: finish the step's declared files, or roll back to the anchor. Do not advance the plan. |
| Step open, worktree ≈ anchor | intent declared, little done | Continue the step. |
| Step open, `verify` passes | done but unrecorded | Close the step with its outcome, continue. |
| No open step, `verify` passes | coherent | Advance to the next action. |
| No open step, worktree dirty | work done without journalling | Do **not** start a new task. Diff against `HEAD`, attribute the changes, then continue. |

### Picking the task

- One `in-progress` → that one.
- Several → newest `updated_at` first, then: `owner` is this session → resume. `owner`
  differs and `updated_at` < 30 min → another agent is live, pick something else. `owner`
  differs and ≥ 30 min → abandoned, adopt it and re-run `verify:` before trusting the journal.
- None → finish PASS anyway, then ask what to work on. Do not silently start the top todo.

## 3. Writing state as you work

### Open a step before acting

MUST open a step before: editing files, running anything over ~2 minutes, anything
hard to reverse (migration, deploy, delete, force-push, publish), or a decision that binds
future work. Five lines, not a paragraph.

```markdown
### 3. Switch the client retry mode to STANDARD  [open]
- opened: 2026-08-31T14:02Z by claude-opus-5 / claude-code
- anchor: main@a3f19c2, clean
- files: src/retry/RetryConfig.java, src/client/HttpClientFactory.java
- intent: set retryMode STANDARD, add token-bucket test
- verify: `./gradlew test --tests RetryConfigTest`
```

`verify:` MUST be a command, not a description. A checklist item is a state you can observe,
not an action you remember taking. If nothing can prove it mechanically, write
`verify: none - <what a human must look at>`.

Add `caveat:` for anything green but untrusted ("passes only against a local dependency").

### Close a step

Mark `[done]`, add `outcome:`, then rewrite `## Summary` - 3-5 lines, replaced not appended.
Restore coherence first: the tree should build and the declared files should all be in the
same state.

### Record what failed

Append to `## Attempts` whenever an approach is abandoned: what was tried, why it was
dropped, and the evidence (`build.log:412`, an error, a benchmark). **Append-only.** A later
agent will be drawn to the same dead end, and this is the only thing that stops it paying
for the failure twice.

### Keep fact separate from assessment

`## Summary` and `outcome:` are observations. Interpretation - "probably a race condition" -
goes in `## Assessment` with the evidence for it. A reader must be able to tell what was
measured from what was guessed, or the next agent inherits a hypothesis as ground truth.

### Close a task

1. Close any open step.
2. Compact: keep goal, outcome, decisions, failed attempts, verification. Delete the
   play-by-play.
3. Promote anything binding future work into `PROJECT_CONTEXT.md` `## Decisions`.
4. `git mv stele/tasks/0007-slug.md stele/tasks/archive/`
5. Regenerate `TASKS.md`.

### New task frontmatter

```yaml
---
id: T-0007
title: <imperative one-line summary>
status: todo            # todo | in-progress | blocked | paused | done
owner:                  # harness/session that holds the lease
created_at: 2026-08-31T14:02Z
updated_at: 2026-08-31T14:02Z
scope: [src/retry/**]   # required when agents run in parallel
abort_when: <stopping rule, decided now while the plan is fresh>
requires:
  tools:
    - id: <tool or MCP tool name>
      why: <what for>
      fallback: <shell equivalent, or "none - ask the user, do not guess">
---
```

`abort_when` matters because an agent 40k tokens into a failing loop is precisely the entity
that cannot decide to stop. Aviation commits to V1 before the roll begins.

`fallback` is what makes `requires` portable. "Needs tool X" only tells the next agent it is
blocked; a fallback lets a different harness degrade gracefully, and
`fallback: none - ask the user` usefully converts a silent wrong answer into a question.

## 4. Asking the human

The human is the one constant across a harness switch, so they are the sender in the final S.
But they were not watching closely - that is why they delegated - so spend their attention
only where an artifact cannot answer.

**Settle with the machine:** did the step finish, what changed, which task is active, do the
tests pass. Never ask a human what a command can tell you; that trains them to rubber-stamp.

**Ask the human:** is this still worth doing, which comes first, does decision X still stand,
and anywhere the record contradicts reality ("journal says done, verify fails - did you revert
something?").

Surface divergence only, never the whole reconstruction. Closed questions, 2-4 options, three
lines maximum. If nothing diverges, say nothing and proceed.

No human available: do not guess. Re-derive from artifacts where you can; otherwise set
`status: blocked` with `blocked_on:` naming the question and pick up something unambiguous.
Fabricating missing state is the only unrecoverable failure here.

**Record every answer** in the task file, or in `PROJECT_CONTEXT.md` if it binds future work.
Human attention is the scarcest resource here; never spend it twice on the same question.

## 5. Invariants

- One `in-progress` task per owner, at most 3 total. Park with `status: paused` before
  starting another.
- Closing or parking a task MUST close its open step. A non-active task with an open step is
  a broken tree the next agent will skip straight past.
- Parallel agents MUST declare `scope:`. Disjoint scopes are safe at any count; overlapping
  scopes are unsafe at two.
- `TASKS.md` is generated. Fix drift by regenerating, never by editing.
- Task paths are stable - status lives in frontmatter, not in directory names. The only move
  is into `archive/` on close.
- No secrets, tokens, internal hostnames, or customer data. This directory gets committed.

## 6. Regenerating the census

`TASKS.md` is derived from `stele/tasks/*.md`. Render `## Active` first, sorted by
`updated_at` descending, each row carrying the task id, title, open step, anchor, owner,
timestamp, and next action. Flag any task that has an open step. Then `## Todo`,
`## Blocked`, `## Paused`.

This skill ships `scripts/index.py`, which does it deterministically and also checks the
invariants in §5. If you can locate this skill on disk, prefer it:

```bash
python3 <skill-dir>/scripts/index.py --root ./stele          # regenerate
python3 <skill-dir>/scripts/index.py --root ./stele --check   # exit 1 on drift or violations
```

If you cannot locate it, maintain `TASKS.md` by hand to the shape above and verify §5
yourself. A project that only ever has hand-maintained census files still works; it just
loses the automatic drift and lease checks.

## 7. Size budgets

Exceeding these makes the system cost more than it saves.

| File | Budget |
|---|---|
| `PROJECT_CONTEXT.md` | ~150 lines |
| `TASKS.md` | one line per task |
| task file | ~200 lines; roll old steps into `## Log (archived)` |
| session read | `PROJECT_CONTEXT` + `TASKS` + active task files only |
