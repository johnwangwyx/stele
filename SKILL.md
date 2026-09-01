---
name: stele
description: Durable project and task state as a skill, so any coding agent can resume work another agent started. Use at session start, when resuming after a break, crash, rate limit, or context compaction, when switching agents or harnesses (Claude Code, Codex, Cursor, Gemini CLI, Kiro, Copilot), when the user says "continue where we left off" / "pick up where I stopped" / "what was I working on", and before and after any substantial piece of work so the next session can continue it without being told anything. Sets itself up on first use in a project - there is no separate install step.
---

# stele

Keep project and task state on disk so work survives the session doing it. The record is written **before** each step, not at session exit - a session that hits a rate limit or crashes never gets to write a summary.

```
stele/
  PROJECT_CONTEXT.md    invariants, current state, decisions, deferred defects
  TASKS.md              generated census - never edit by hand
  tasks/
    0007-slug.md        one live task per file, flat, stable path
    done/               closed tasks, kept whole
```

## 1. Bootstrap

Two independent checks, both cheap. Run them at the start of any session in a project you have not already checked this session.

**1.1 Does `./stele/` exist?**

If not, create `stele/tasks/done/`, then `stele/PROJECT_CONTEXT.md` from [templates/PROJECT_CONTEXT.md](templates/PROJECT_CONTEXT.md) - filling in what you can infer from the repo. Leave a field blank rather than guessing.

Do not write `TASKS.md` by hand. Generate it:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/index.py
```

It creates the file if absent and prints any invariant violations (§6 covers the fallback if that path does not resolve). Then continue with the user's actual request.

**1.2 Is the pointer block present?** Check independently of 1.1

If not, add the block to every one of these the project already has: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`, `.cursor/rules/stele.mdc`, `.kiro/steering/stele.md` etc. If it has none, create `AGENTS.md`.

Keep the block to a pointer. It exists so the next agent knows the skill applies here — not to carry a copy of the procedure, which would drift from this file and duplicate it into every instruction file the project has:

```markdown
<!-- stele:begin - managed block, replaced in place when stele runs -->
## Project state (stele)

Task state for this project lives in `stele/`, maintained by the **stele** skill. Load that skill
before doing anything else — including before a direct instruction, which may already be half-done.

If the stele skill is not installed in this harness, say so before continuing. `stele/TASKS.md` and the files under `stele/tasks/` are plain markdown and still readable, but nothing will maintain them, and the state will silently go stale.
<!-- stele:end -->
```

## 2. Resume: PASS

Run before editing anything, even given a direct instruction - it may already be half-done.

**Regenerate first.** Before reading anything, rebuild the census from the task files:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/index.py
```

Now `TASKS.md` cannot be stale, and any invariant violation is printed before you act on the state — a task parked with a step still open, two tasks sharing an id, a torn frontmatter block. Read those errors; they change what you do next.

Without Python, read `TASKS.md` as a hint and confirm it against the task files themselves: `grep -rlE --exclude-dir=done '^status: *"?in-progress' stele/tasks/ 2>/dev/null`. No output means no active task. Frontmatter always wins over a census you could not regenerate.

**P - Project.** Read `stele/PROJECT_CONTEXT.md`. `## Invariants` is fact - note its `Last verified` date. `## Current state` is recent but checkable.

**A - Actions.** Read `stele/TASKS.md` — fresh, from the step above. Never read `tasks/done/` during a resume.

**S - Situation.** Read only the active task file(s), and reconcile every open step per the table below - each has its own `anchor:` and `files:`, so reconcile them one at a time.

**S - Synthesis.** State back the goal, the next action, and the top risk in three lines. Then act - unless something diverges, in which case ask (§4).

**Then claim.** Only now write to a *task file*: set `last_modified_by:` and `updated_at:`, and open a step. Regenerating the census above is the one exception — it is derived, so a bad write is fixed by running it again. A half-written task file is not.

### Reconciling an open step

| Observation | Meaning | Do |
|---|---|---|
| `files:` unchanged since `anchor:` | declared, barely started | Start the step as written. |
| `files:` changed, tree does not build | a session stopped mid-edit | Reconcile first. Read the diff against `intent:`, then finish the step or roll back to the anchor. Do not advance the plan. |
| `files:` changed, tree builds, `done when` looks satisfied | finished but unrecorded | Confirm with the project's `Test:` command, write the `outcome:`, close the step. |
| No open step, tree clean | coherent | Advance to the next action. |
| No open step, tree dirty | unjournalled work | Do **not** start a new task. Diff against `HEAD`, attribute the changes to a task or open one for them, then continue. |

Compare `files:` specifically, not the whole worktree - a bare `git diff` against the anchor also picks up unrelated uncommitted changes and stele's own writes.

Without git, `anchor:` is unusable. Fall back to the project's `Test:` command plus `done when:`, and say explicitly that you could not establish what the previous session changed.

### Choosing among several active tasks

Sort by `updated_at`, newest first. `last_modified_by` is **provenance, not a lock** - `harness@model` for whoever wrote the file last. It confers no claim, but the harness half is a warning label: a plan written under a different harness may assume tools you do not have, so check the task's `requires:` before trusting its steps.

- `updated_at` within the last 30 minutes: another agent may be working right now. Ask the user before adopting it.
- Older: adopt it, and re-establish state from the artifacts rather than trusting the journal.

Nothing active: complete PASS anyway, then ask what to work on. Do not silently start the top todo.

## 3. Writing state as you work

Every field is listed under **Field reference** at the end of this section. Full task skeleton: [templates/task.md](templates/task.md). A filled-in example with the project context that goes with it: [examples/stele/](examples/stele/).

### When to create, update, and close

Three hard triggers. Skipping the last one is the most likely failure in practice — a `tasks/` directory that only ever grows.

**Create a task** before the first step of any work that will outlive this session: more than one sitting, more than a couple of files, or anything another agent might have to finish. A throwaway single-session edit does not need one. Allocate the id from the highest in `tasks/` and `tasks/done/`.

**Update the task** whenever you open or close a step, learn something that changes the plan, or make a decision. Every write sets `updated_at` and `last_modified_by`. A stale `updated_at` on live work makes the task look abandoned, and the next agent will adopt it out from under you.

**Close the task before you tell the user the work is done** — not afterwards, not next session. If you are about to report completion and the task is still `in-progress`, you have skipped a step.

### Open a step before acting

Open a step before: editing files, running anything over ~2 minutes, anything hard to reverse (migration, deploy, delete, force-push, publish), or a decision that binds future work.

Two may be open at once, for genuinely independent threads. Their `files:` must not overlap - if they do, a resuming agent cannot tell which step a change belongs to, and the reconcile is guesswork. Prefer one.

```markdown
### 2. Switch the service and route to keyset pagination  [open]
- last_modified_by: claude-code@Opus-5
- anchor: main@a3f19c2
- files: src/services/documents.ts, src/routes/documents.ts
- intent: replace LIMIT/OFFSET with a (created_at, id) keyset predicate
- done when: all nine contract tests pass, including insert-during-pagination
- caveat: service half passes only against the local fixture, no index in staging yet
```

**On a long step, keep it current.** Add findings to `intent:` or a `note:` bullet as you learn them. A step that dies at minute 38 should not read like minute 0.

### Close a step

Mark `[done]`, add `outcome:`, then rewrite `## State` - 3-5 lines, **replaced, not appended**. It is the condensed course of the work and the first thing the next agent reads, so a stale State is worse than none. Restore coherence first: the tree should build and the declared files should all be in one state.

Interpretation may go in State, but must carry its evidence and be marked as a guess. A reader has to be able to tell what was measured from what was inferred, or the next agent inherits a hypothesis as ground truth.

### Record what failed

Append to `## Attempts/Pitfalls` whenever an approach is abandoned *or* you discover something that will bite the next person: what happened, why, and the evidence. **Append-only.** A later agent will be drawn to the same dead end, and this is the only thing that stops it paying twice. Choices local to this task go here too - a decision is a rejected alternative plus a chosen one.

### Promote what outlives the task

A decision or a discovered constraint that binds work **beyond this task** goes into `PROJECT_CONTEXT.md` the moment you make it - Decisions, Invariants, or Guardrails as fits - citing the task id. Not at close: it binds other agents now, and buffering it keeps it invisible until the task ends.

### Close a task

1. Close any open step, and rewrite `## State` to describe where the work ended up.
2. Check nothing still needs promoting - closed tasks are not read on resume, so a lesson left only in `tasks/done/` is lost.
3. Set `status: done`, `git mv stele/tasks/0007-slug.md stele/tasks/done/`, then regenerate the census (§6).

A closed task keeps exactly the shape it had - same sections, every step `[done]` with its `outcome:`. Do not compact it or delete the step log. That log is the evidence of what was actually done, and it costs nothing to keep.

### Commit it

`stele/` is worthless on another machine if it never leaves this one. Commit it with the work it describes, or on its own when a session ends. Task ids are allocated from the highest id in `tasks/` **and** `tasks/done/`.

### Field reference

Only the six marked **indexed** are read by tooling. Everything else exists for whoever reads the file, so add fields of your own freely — nothing will trip over them.

#### Frontmatter (task-level fields)

| Field | | What it is |
|---|---|---|
| `id` | indexed, required | `T-0007`. Unique across `tasks/` **and** `tasks/done/`. |
| `title` | indexed, required | One imperative line. |
| `status` | indexed, required | `todo` / `in-progress` / `blocked` / `paused` / `done`. |
| `last_modified_by` | indexed | Which harness and model last wrote this file, as `harness@model` — `claude-code@Opus-5`. Provenance, not a lock: it confers no claim on the task. |
| `created_at` | indexed | ISO timestamp. |
| `updated_at` | indexed | ISO timestamp, set on **every** write. Drives the freshness check when several tasks are active, so a stale one makes live work look abandoned. |
| `blocked_on` | prose | What the task is waiting on. Only meaningful with `status: blocked`. |
| `requires` | prose | Tools or skills the plan assumed, each with `why` and a `fallback`. The fallback is the portable part: "needs tool X" only tells the next agent it is stuck, whereas `fallback: none - ask the user` converts a silent wrong answer into a question. |

#### Step bullets

None of these are parsed. They are what a resuming agent actually reads, and they are the difference between reconciling and guessing.

| Field | What it is |
|---|---|
| `last_modified_by` | Which harness and model opened or closed this step, as `harness@model`. |
| `anchor` | `branch@sha` — the commit the step started from. Half of the reconcile. |
| `files` | Comma-separated, **one line** — a nested list is not what the next agent expects to read. The other half of the reconcile: diff *these* files against the anchor, not the whole worktree. |
| `intent` | What you are about to do. Written before acting; that is the whole point. |
| `done when` | Prose describing the finished state. Never a command — task files carry no executable content. |
| `caveat` | Something green but untrusted, e.g. "passes only against the local fixture". |
| `note` | Findings picked up during a long step. |
| `outcome` | Filled in at close, then mark the heading `[done]`. |

The one thing in the body that **is** parsed is the `[open]` marker on a `###` step heading. At most 2 per task; a non-active task must have none.

#### Sections

`## Goal`, `## Done when`, `## State`, `## Attempts/Pitfalls`, `## Steps` — see the subsections above for what belongs in each. A closed task keeps the same five.

## 4. Asking the human

They are the one constant across a harness switch, so they are the sender in the final S is the I-PAAS framwork. But they were not watching closely - that is why they delegated - so spend their attention only where an artifact cannot answer or you have concerns.

**Settle with the machine:** what changed, whether the tree builds, which task is active, whether tests pass. Never ask a human what a command can tell you; it trains them to rubber-stamp.

**Ask the human:** is this still worth doing, which comes first, does decision X still stand, and anywhere the record contradicts reality.

Surface divergence only, never the whole reconstruction. Closed questions, 2-4 options, three lines maximum. If nothing diverges, say nothing and proceed.

**Record important answer** in the task file, or in `PROJECT_CONTEXT.md` if it binds future work. Human attention is the scarcest resource here; never spend it twice on the same question.

## 5. Rules

Checked by `index.py` (§6):

- At most 2 steps `[open]` per task; a non-active task must have none.
- At most 3 tasks `in-progress`.
- Unique `id` across `tasks/` and `tasks/done/`; valid `status`; frontmatter closes with `---`.
- `TASKS.md` matches the task files.

## 6. Regenerating the census

`TASKS.md` is derived from the task files: `## Active` first, sorted by `updated_at` descending, then `## Todo`, `## Blocked`, `## Paused`, then `## Done` with the 20 most recently closed. One line per task — id and title, plus `last_modified_by` and `updated_at` on active ones. Flag any task that still has a step open.

`## Done` exists so you can see what has already been done without opening anything in `tasks/done/`.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/index.py
python3 ${CLAUDE_SKILL_DIR}/scripts/index.py --check   # exit 1 on drift; for CI
```

It finds `stele/` by walking up from wherever you are, so it works from a subdirectory too. Pass `--root <path>/stele` only to point at a different project, and note that a relative `--root` resolves against your current directory, not the script's.

If `${CLAUDE_SKILL_DIR}` is not substituted - it is Claude Code-specific - try `~/.claude/skills/stele/scripts/index.py` or the equivalent for your harness, and if you cannot find it, maintain `TASKS.md` by hand to the shape above and check §5 yourself. That works; it just loses the automatic checks.
