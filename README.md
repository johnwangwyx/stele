<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/img/logo-dark.png">
    <img alt="stele" src="docs/img/logo-light.png" width="340">
  </picture>
</p>

**Durable task state for AI coding agents, as a skill.**

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/img/lifecycle-dark.svg">
  <img alt="One task across two sessions, both running stele. Three writes land on disk before the work they describe: opening step 2, closing it, opening step 3. A rate limit interrupts with step 3 still open. A second session in a different harness resumes, reads the open step to see what was half-applied, and finishes and closes it." src="docs/img/lifecycle-light.svg" width="100%">
</picture>

Existing solutions write the record last: a handoff skill at the end of a session, a summary before you close the laptop. That works right up until the session ends without you — a usage limit, a crash — and then there is nothing at all. Writing first makes you resumable at every point, not just the ones you planned for.

## Install

Since you are already here, and you have an agent. Install in one line. 😉

> Install https://github.com/johnwangwyx/stele as a skill under your framework.

## To use

### 1. Start managing a project

> `/stele` manage this project with stele

<sub>`/` is Claude Code — Codex uses `$stele`, and other harnesses have their own way to start conversation while mentioning a skill.</sub>

New project, same sentence. On an existing repo the skill reads what is already there.

### 2. Now it is interruptible

Hit a usage limit, crash, close the laptop, switch provider, come back in three weeks. The record is already on disk, because every write happened *before* the work it describes rather than after it. Nothing needs saving on the way out.

### 3. Resume, in any harness

> `/stele` resume where it is left off

Note: You will mostly not even need the skill trigger (`/stele` or `$stele`). That first run left a pointer in `AGENTS.md` (creating it if there was none), so the next agent or harness knows to load stele.

## The protocol, The Inspiration

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/img/pass-dark.svg">
  <img alt="A mapping between the clinical I-PASS handoff protocol and stele. Patient summary maps to PROJECT_CONTEXT.md, action list to TASKS.md, situation awareness to the open step, and synthesis by the receiver — echoing the situation back — to reading the record back, confirming it, then continuing." src="docs/img/pass-light.svg" width="100%">
</picture>

**[I-PASS](https://www.ahrq.gov/teamstepps-program/curriculum/communication/tools/ipass.html)** is the shift-change handover protocol hospitals adopted once transitions proved to be where patients come to harm. The departing clinician holds context that never reached the charts or reports, and the arriving one cannot know what is missing. **It is an example of an evidence-based option for conducting a structured handoff.**

## How it works

Three levels, and nothing else:

**Project** — the standing facts an agent cannot cheaply derive and would otherwise get wrong: how to build and test, what not to touch, what not to run, the decisions that already bind future work.

**Task** — one unit of work that will outlive a single session. Its goal, how you would know it is finished, its current state in a few lines, and an append-only record of what was already tried and failed. That last part is the most expensive thing to lose.

**Step** — a slice of a task small enough to sit inside one sitting. This is where write-ahead happens: before touching anything, the agent records what it is about to do and which files it will touch. Afterwards it records the outcome.

That ordering is what makes a cold resume tractable. The next agent opens the files the step named, runs the project's checks, and can tell *finished but never recorded* from *stopped halfway* — without asking anyone. And because the record is written before the work, a session that dies has already written everything except the step it died inside.

See [`examples/stele/`](examples/stele/) for a complete, realistic instance.

## License

MIT
