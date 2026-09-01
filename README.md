<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/img/logo-dark.png">
    <img alt="stele" src="docs/img/logo-light.png" width="340">
  </picture>
</p>

<p align="center">
  <a href="LICENSE"><img alt="MIT" src="https://img.shields.io/badge/license-MIT-eda100"></a>
</p>

**Crash-proof task memory for coding agents.** Claude hit its usage limit halfway through a refactor? Resume the same task in Codex, Cursor, or a fresh session without reconstructing anything.

### Most agent memory is write-after. stele is write-ahead.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/img/lifecycle-dark.svg">
  <img alt="One task across two sessions, both running stele. Three writes land on disk before the work they describe: opening step 2, closing it, opening step 3. A rate limit interrupts with step 3 still open. A second session in a different harness resumes, reads the open step to see what was half-applied, and finishes and closes it." src="docs/img/lifecycle-light.svg" width="100%">
</picture>

Everything else writes the record last: a handoff skill at the end of a session, a summary before you close the laptop, a memory file updated once the work is done. That holds right up until the session ends without you — a usage limit, a crash, a closed laptop — and then there is nothing at all.

stele writes each step *before* the work it describes. So the record does not depend on the session surviving long enough to write it.

| | Rate limit / crash | Context compaction | Knows what was half-done | Remembers failed attempts | Never stale |
|---|:--:|:--:|:--:|:--:|:--:|
| Handoff skills, `/handoff` | ❌ | ❌ | ⚠️ | ⚠️ | ✅ |
| Memory banks, `CLAUDE.md` notes | ⚠️ | ⚠️ | ❌ | ⚠️ | ❌ |
| Planning files | ✅ | ✅ | ❌ | ❌ | ⚠️ |
| **stele** | ✅ | ✅ | ✅ | ✅ | ✅ |

## Install

```bash
npx skills@latest add johnwangwyx/stele --global
```

This installs stele into the harnesses it detects on your machine, for all your projects.

## To use

### 1. Start managing a project

> `/stele` manage this project with stele

<sub>`/` is Claude Code — Codex uses `$stele`, and other harnesses have their own way to start conversation while mentioning a skill.</sub>

New project, same sentence. On an existing repo the skill reads what is already there.

### 2. Now it is interruptible

> *(nothing to type — that is the point)*

Hit a usage limit, crash, close the laptop, switch provider, come back in three weeks. The record is already on disk, because every write happened *before* the work it describes rather than after it. Nothing needs saving on the way out.

### 3. Resume, in any harness

> `/stele` resume where it is left off

Note: You will mostly not even need the skill trigger (`/stele` or `$stele`). That first run left a pointer in `AGENTS.md` (creating it if there was none), so the next agent or harness knows to load stele.

## How it works

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/img/hierarchy-dark.svg">
  <img alt="Three nested levels. A project box holds PROJECT_CONTEXT.md with the checks, guardrails and decisions, and lives as long as the code. Inside it, task boxes each hold one unit of work with its goal, state and attempts, and outlive a single session. Inside the active task, two step boxes each cover one sitting; the step is the level written before the work happens. Closed tasks move to tasks/done and are kept whole." src="docs/img/hierarchy-light.svg" width="100%">
</picture>

Three levels, and nothing else:

**Project** — the standing facts an agent cannot cheaply derive and would otherwise get wrong: how to build and test, what not to touch, what not to run, the decisions that already bind future work.

**Task** — one unit of work that will outlive a single session. Its goal, how you would know it is finished, its current state in a few lines, and an append-only record of what was already tried and failed. That last part is the most expensive thing to lose.

**Step** — a slice of a task small enough to sit inside one sitting. This is where write-ahead happens: before touching anything, the agent records what it is about to do and which files it will touch. Afterwards it records the outcome.

That order is what makes a cold resume work. The next agent reads the project context, then the auto-generated `TASKS.md`, then the open step of whatever is still in progress. From that it can see for itself whether the work finished or stopped halfway and the touched files. Nobody has to explain anything.

The record is always one step ahead of the work. So when a session dies, everything is already saved.

### What makes it reliable

- **Each task file lists the tools and skills its plan assumed.** A `requires:` field captures them — so an agent in a harness that lacks one can say so, reach for the documented substitute, or ask, instead of finding the gap by watching something fail.
- **The task list is generated, never hand-written.** `TASKS.md` — the index in the diagram above — is rendered from the individual task files on each resume, so it is always up-to-date.
- **A step is only marked done once its check has actually run.** If a task could not be executed — no permission, a missing dependency, the wrong environment — the step stays open with attempts tracked.
- **Each task file keeps an append-only record of what was already tried and failed.** Nothing gets deleted from it. That is the most expensive thing to lose, because the next agent is drawn to the same dead end and pays full price for it a second time.
- **A decision that affects future work is promoted the moment it is made**, not when the task closes. Otherwise it sits invisible in one task file while other agents carry on without it.

### What you get as a side effect

Worth having even on a project that never gets interrupted, and the last two are for people rather than agents.

- **A project history nobody had to write.** 
- **Decisions collect into a log, each traceable to the task that produced it.**
- **"Why didn't we do X?" has an answer on disk.** 

See [`examples/stele/`](examples/stele/) for a complete, realistic instance.

## Where the protocol comes from

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/img/pass-dark.svg">
  <img alt="A mapping between the clinical I-PASS handoff protocol and stele. Patient summary maps to PROJECT_CONTEXT.md, action list to TASKS.md, situation awareness to the open step, and synthesis by the receiver — echoing the situation back — to reading the record back, confirming it, then continuing." src="docs/img/pass-light.svg" width="100%">
</picture>

**[I-PASS](https://www.ahrq.gov/teamstepps-program/curriculum/communication/tools/ipass.html)** is the shift-change handover protocol hospitals adopted once transitions proved to be where patients come to harm. The departing clinician holds context that never reached the charts or reports, and the arriving one cannot know what is missing. **It is an example of an evidence-based option for conducting a structured handoff.**

## License

MIT
