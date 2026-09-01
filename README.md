# stele

**Durable project and task state for AI coding agents, in plain markdown.** Stop mid-task in
one agent, start another agent — different model, different harness, different provider — and
it picks up where the last one stopped without being told anything.

A *stele* is an inscribed stone slab. It is why we can still read records written three
thousand years after their authors died.

## The problem

Two situations, same root cause:

1. **Your plan hits its limit mid-task.** You switch providers. The new agent has no idea what
   the project is, what you were doing, or what had already been tried.
2. **A better model or harness ships.** You want to try it, but you are held in place by the
   context your current tool is managing for you.

Every existing answer is a *handoff* — you run `/handoff` and it writes a summary before you
leave. That fails in exactly the case you need it, because a session that has hit a rate limit
or crashed never gets to write anything.

stele inverts it. State is written **while** work happens, before each step rather than after.
There is nothing to hand off, because the record is already on disk.

## What it looks like

```
your-project/
  AGENTS.md              <- pointer block, so any agent finds the rest
  stele/
    PROJECT_CONTEXT.md   invariants + current state + decisions + deferred defects
    TASKS.md             generated census - never edited by hand
    tasks/
      0007-migrate-retry-mode.md
      archive/           closed tasks, compacted on close
```

Four markdown files and a directory. No database, no daemon, no service, no vendor, and
nothing copied into your repo that has to stay in sync with anything. `grep` works. `git log`
works. It outlives your tooling.

## Quick start

Install the skill **once**:

```bash
git clone https://github.com/johnwangwyx/stele ~/.claude/skills/stele
```

(or `~/.codex/skills/`, `~/.config/opencode/skills/`, or wherever your harness keeps skills -
or just ask your agent to install it for you.)

Then in any project, ever again:

> continue where we left off

That's it. There is no per-project install step. The first time the skill runs somewhere it
has never run before, it creates `stele/` and writes a pointer block into the project's agent
instruction file - creating `AGENTS.md` if none exists - so the *next* agent finds the state
whether or not it has this skill installed.

The pointer block restates the core procedure inline rather than only pointing at it. An agent
that has never heard of stele reads `AGENTS.md` and still resumes correctly.

## How it works: PASS

Adapted from **I-PASS**, the clinical handoff protocol — associated with roughly a 23% reduction
in medical errors across nine residency programs. Both fields are solving the same problem:
harm concentrates at transitions.

| | | |
|---|---|---|
| **P** | Project | Invariants and current state, split by how often they change |
| **A** | Actions | The task census, plus each task's next step and its trigger |
| **S** | Situation | Active task, open step, the tree state when it opened, the command that proves it done |
| **S** | Synthesis | The receiver states back goal / next action / top risk — and checks it |

The full protocol, including what it deliberately does *not* copy from medicine and aviation,
is in [PROTOCOL.md](PROTOCOL.md).

## A task, mid-work

```markdown
---
id: T-0007
title: Migrate retry mode to STANDARD
status: in-progress
owner: claude-code/sess-4f2a
updated_at: 2026-08-31T14:02Z
scope: [src/retry/**]
abort_when: build fails 3x on this approach - stop and ask
requires:
  tools:
    - id: github.create_pull_request
      fallback: gh pr create --title ... --body-file ...
---

## Attempts
- Bumped the SDK in config only - NoClassDefFoundError, the dependency tree lacks the sibling
  artifact. Evidence: build.log:412

## Steps
### 2. Update RetryConfig  [open]
- opened: 2026-08-31T14:02Z by claude-opus-5 / claude-code
- anchor: main@a3f19c2, dirty
- files: src/retry/RetryConfig.java
- intent: set retryMode STANDARD, add token-bucket test
- verify: `./gradlew test --tests RetryConfigTest`
```

Four things there carry most of the weight:

- **`verify:` is a command, not a description.** From aviation checklists: "gear down" is
  confirmed by three green lights, not by remembering the lever. The next agent *runs* it
  instead of guessing whether the step finished.
- **`anchor:` is the git state when the step opened.** "What did the dead agent actually do"
  becomes a diff rather than an inference.
- **`## Attempts` is append-only.** The most expensive thing to lose is what was already tried
  and failed. Without it, the next agent pays for the same dead end at full price.
- **`abort_when` is decided at plan time.** An agent 40k tokens into a failing loop is precisely
  the entity that cannot decide to stop. Aviation commits to V1 before the roll starts.

## The invariants

The skill states these, and `scripts/index.py` enforces them - so drift is a failing exit code
rather than a surprise:

- Task files are the source of truth; `TASKS.md` is generated. Fix drift by regenerating.
- Status lives in frontmatter, not in directory names. Paths are stable, so cross-references
  survive. The only move is into `archive/` on close.
- One `in-progress` task per owner, at most three total. Parallel agents declare `scope:`.
- Closing or parking a task must close its open step — otherwise the census flags a task that
  looks skippable but is sitting on a half-edited tree.
- No secrets. This directory is committed.
- Size budgets: `PROJECT_CONTEXT.md` ~150 lines, one line per task in the census, ~200 per task
  file. A context system that costs 30k tokens to read is worse than none.

```bash
python3 ~/.claude/skills/stele/scripts/index.py --root ./stele
python3 ~/.claude/skills/stele/scripts/index.py --root ./stele --check   # exit 1 on drift
```

The script is an accelerator, not a dependency. If an agent cannot find it, it maintains the
census by hand from the shape given in the skill - it just loses the automatic drift and lease
checks. Same principle as the `fallback:` field on a task's `requires:` block.

## Why there is no severity flag

I-PASS opens with illness severity — stable, watcher, unstable — to set reading order. The
software equivalent would be a field saying whether the tree is coherent. stele does not have
one, because it is derivable:

```
step open + worktree != anchor + verify fails   ->  mid-surgery, reconcile before advancing
step open + worktree ~= anchor                  ->  intent declared, little done
no open step + verify passes                    ->  coherent
```

A derived signal cannot go stale or lie. A declared one can do both — and the agent that would
have set it to `unstable` is exactly the agent that died before it could.

## Harness support

On first run in a project, the skill adds its pointer block to every agent instruction file the
project already uses - `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`,
`.cursor/rules/`, `.kiro/steering/` - and creates `AGENTS.md` if there are none.

`AGENTS.md` alone covers Codex, Cursor, Copilot, Gemini CLI, opencode and Kiro. The block is
delimited by `<!-- stele:begin -->` / `<!-- stele:end -->` markers, so it is replaced rather
than duplicated on later runs, and the rest of the file - which is yours - is left alone.

## Prior art

stele is not the first attempt at this, and the honest framing is that it takes a different
angle rather than a better one:

- [ai-memory](https://github.com/akitaonrails/ai-memory) — a Rust daemon with lifecycle hooks
  into ~20 harnesses and a git-backed wiki. Far more capable, far more to install. Its
  per-harness support matrix is the best public catalogue of where handoff actually breaks.
- [beads](https://github.com/gastownhall/beads) — a git-backed work graph as agent memory.
  Overlaps substantially; a Go binary with its own CLI rather than markdown any agent can read.
- [planning-with-files](https://github.com/OthmanAdi/planning-with-files) — persistent plans and
  recovery after compaction.
- The many `handoff` / `session-handoff` skills — write-at-exit summaries, which is the failure
  mode described at the top.

What stele does differently: **write-ahead rather than write-at-exit**, a **documented protocol**
you can follow with no tooling at all, and **machine-checkable state** (`verify:`, `anchor:`)
instead of prose a model can fake.

Credit where it is due: I-PASS (Starmer et al.), SBAR, the aviation Minimum Equipment List and
checklist literature, and David Marquet's "I intend to…" — all of which are doing versions of
this problem with real consequences attached.

## License

MIT
