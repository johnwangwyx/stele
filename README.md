# stele

**Durable project and task state for AI coding agents, in plain markdown.** Stop mid-task in one
agent, start another — different model, different harness, different provider — and it picks up
where the last one stopped without being told anything.

A *stele* is an inscribed stone slab. It is why we can still read records written three thousand
years after their authors died.

## The problem

Two situations, one root cause:

1. **Your plan hits its limit mid-task.** You switch providers. The new agent has no idea what the
   project is, what you were doing, or what had already been tried and failed.
2. **A better model or harness ships.** You want to try it, but you are held in place by the
   context your current tool is managing for you.

Every existing answer is a *handoff* — you run `/handoff` and it writes a summary before you leave.
That fails in exactly the case you need it, because a session that has been rate-limited or has
crashed never gets to write anything.

stele inverts it: state goes on disk **before** each step, not after. There is nothing to hand off.

## What it looks like

```
your-project/
  AGENTS.md              <- pointer block, so any agent finds the rest
  stele/
    PROJECT_CONTEXT.md   invariants, current state, decisions, deferred defects
    TASKS.md             generated census - never edited by hand
    tasks/
      0007-cursor-pagination.md
      archive/           closed tasks, compacted on close
```

Markdown in your repo. No database, no daemon, no service, no vendor, nothing copied in that has
to stay in sync with anything. `grep` works. `git log` works. It outlives your tooling.

See [`examples/stele/`](examples/stele/) for a complete, realistic instance — a project context and
the half-finished task that goes with it, exactly as a fresh agent would find them.

## Quick start

Install the skill **once**:

```bash
git clone https://github.com/johnwangwyx/stele ~/.claude/skills/stele
```

(or `~/.codex/skills/`, `~/.config/opencode/skills/`, wherever your harness keeps skills — or just
ask your agent to install it.)

Then in any project, ever again:

> continue where we left off

There is no per-project install step. The first time the skill runs somewhere new it creates
`stele/` and writes a pointer block into the project's agent instruction file — creating `AGENTS.md`
if there is none — so the *next* agent finds the state whether or not it has this skill.

The pointer block restates the core procedure inline rather than only pointing at it. An agent that
has never heard of stele reads `AGENTS.md` and still resumes correctly.

## How it works: PASS

Adapted from **I-PASS**, the clinical handoff protocol — associated with roughly a 23% reduction in
medical errors across nine residency programs. Both fields are solving the same problem: harm
concentrates at transitions.

| | | |
|---|---|---|
| **P** | Project | Invariants and current state, split by how often they change |
| **A** | Actions | The task census, each with its next step |
| **S** | Situation | Active task, open step, the commit it started from, how you would know it finished |
| **S** | Synthesis | The receiver states back goal / next action / top risk — and checks it |

The operational form — what to read, in what order, what to do about each outcome — is in
[SKILL.md](SKILL.md).

## A task, mid-work

```markdown
---
id: T-0007
title: Migrate the /documents list endpoint from offset to cursor pagination
status: in-progress
last_modified_by: claude-opus-5
updated_at: 2026-08-31T14:02Z
scope: [src/routes/documents.ts, src/services/documents.ts]
abort_when: if a third approach to the sort key fails, stop and ask - the schema probably needs a migration first
---

## Summary
Cursor encode/decode is finished. The keyset predicate is **half-applied**: the service builds
`(created_at, id)` while the route still passes only `created_at`. Tree compiles; 3 of 9
contract tests red.

## Attempts/Pitfalls
- Keyset on `created_at` alone - duplicates across pages when two rows share a timestamp.
  `created_at` is not unique; PROJECT_CONTEXT says so under Invariants and I missed it.
- Do not expect `ORDER BY created_at, id` to be fast in staging - no index there (see Deferred),
  so the plan falls back to a full sort.

## Steps
### 2. Switch the service and route to keyset pagination  [open]
- last_modified_by: claude-opus-5
- anchor: main@a3f19c2
- files: src/services/documents.ts, src/routes/documents.ts
- intent: replace LIMIT/OFFSET with a (created_at, id) keyset predicate
- done when: all nine contract tests pass, including insert-during-pagination
- caveat: service half passes only against the local fixture, no index in staging yet
```

Four things there carry most of the weight:

- **`anchor:` + `files:` is the mechanical part.** Diff those specific files against that commit and
  "what did the dead agent actually do" is an answer, not a guess. (Diffing the whole worktree is
  not — it picks up unrelated uncommitted changes.)
- **`## Attempts/Pitfalls` is append-only.** The most expensive thing to lose is what was already
  tried and failed. Without it, the next agent pays for the same dead end at full price. Note how
  the first entry points back at an invariant that was already written down and missed — that is
  the format doing its job.
- **`caveat:` marks the untrusted-but-green.** Nothing in git or a test run can tell you the pass
  was against a fixture rather than production.
- **`abort_when` is decided at plan time.** An agent 40k tokens into a failing loop is precisely the
  entity that cannot decide to stop. Aviation commits to V1 before the roll begins. It is a
  reminder, not a mechanism — nothing counts your attempts for you.

## Task files contain no commands, on purpose

`stele/` is committed, which means task files travel through pull requests like any other file. So
they carry **no executable strings** — `done when:` is prose describing a state, never a command.

The alternative is a real hole. If the protocol told every agent to run a command out of a task file
at session start, then anyone who can land a commit could get code executed on your machine the
moment you said "continue where we left off" — before you had stated any intent. Build and test
commands live in `PROJECT_CONTEXT.md` instead: one place, changed rarely, conspicuous in review.

An agent reconciling a step therefore uses the project's own `Build:` / `Test:` commands and its own
judgment, and treats anything written inside a task file as untrusted text.

## What is actually checked

`scripts/index.py` enforces these — drift is a failing exit code rather than a surprise:

- One step `[open]` per task; a non-active task must have none (a parked task sitting on a
  half-edited tree is the trap this catches)
- At most 3 tasks `in-progress`
- Unique `id`, valid `status`, frontmatter that closes properly — an unterminated frontmatter block
  is what a torn write looks like, and it would otherwise make an open step invisible
- Steps under `## Steps` exactly — a heading like `## Step log` parses to nothing and would
  silently report a mid-edit tree as coherent
- `TASKS.md` matches the task files

```bash
python3 ~/.claude/skills/stele/scripts/index.py --root ./stele
python3 ~/.claude/skills/stele/scripts/index.py --root ./stele --check   # exit 1 on drift; for CI
```

These are **not** checked, and calling them conventions rather than invariants is the honest
framing: disjoint `scope:` between parallel agents, no secrets, stable task paths, and the size
budgets. A rule nothing verifies is a rule you have to hold yourself.

The script is an accelerator, not a dependency. An agent that cannot locate it maintains the census
by hand from the shape documented in the skill.

## What "write-ahead" does and does not buy

Written *ahead* of the work: intent, the files about to change, the commit being changed from, and
how you would know the step finished. Written *after*: the outcome, the summary, the attempt that
failed.

So a step that dies at minute 38 of 40 leaves the next agent the plan plus a diff — not the
reasoning from minute 37, unless the agent kept the step current as it went (which the skill tells
it to do). That is a large improvement on a handoff that was never written, and it is less than "the
whole record is on disk." Both things are true.

## Why there is no severity flag

I-PASS opens with illness severity — stable, watcher, unstable — to set reading order. The software
equivalent would be a field saying whether the tree is coherent. stele has none, because it is
derivable:

```
files changed since anchor + tree does not build  ->  mid-edit, reconcile before advancing
files unchanged since anchor                      ->  declared, barely started
no open step + tree builds                        ->  coherent
```

A derived signal cannot go stale or lie. A declared one can do both — and the agent that would have
set it to `unstable` is exactly the agent that died before it could.

## What replaces the sender

In a clinical handoff the outgoing clinician is standing there: the receiver states back what they
understood and gets corrected on the spot. That correction is what makes the final S work.

Here the sending agent is gone — that is the premise. Two things stand in:

- **The artifacts.** `anchor:`, `files:`, and the project's own tests correct the receiver with
  nobody present.
- **The human.** The one element constant across a harness switch — but a degraded sender. They were
  not watching closely, time has passed, and they may not be available. So route by who can settle
  the question: artifacts for state, the human for intent, priority, and contradiction. Never ask a
  human what a command can answer; it trains them to rubber-stamp.

## What was deliberately not copied

High-reliability industries have well-documented failure modes, and an LLM makes each worse, because
it will always produce something that *looks* like a valid entry.

- **Checklist fatigue.** Long checklists get filled in without being read. Few fields.
- **Copy-forward.** Clinical notes propagate stale pasted text that outlives its truth and causes
  harm. Every field is either derivable from the repo or cheap to leave blank.
- **Alarm fatigue.** If everything is flagged, nothing is.

## Harness support

On first run the skill adds its pointer block to every agent instruction file the project already
uses — `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`, `.cursor/rules/`,
`.kiro/steering/` — and creates `AGENTS.md` if there are none. It asks before editing files that
already exist, since those are yours.

`AGENTS.md` alone covers Codex, Cursor, Copilot, Gemini CLI, opencode and Kiro. The block is
delimited by `<!-- stele:begin -->` / `<!-- stele:end -->`, so it is replaced rather than duplicated,
and the presence check runs every session — a rollback or a manual delete gets repaired instead of
silently leaving the project undiscoverable.

**Requires git** for `anchor:` reconciliation, and a shell for the census script. Without git the
skill says so and falls back to the project's tests plus `done when:`; without a shell it degrades
to reading and writing the markdown by hand.

## Prior art

Not the first attempt at this, and the honest framing is a different angle rather than a better one:

- [ai-memory](https://github.com/akitaonrails/ai-memory) — a Rust daemon with lifecycle hooks into
  ~20 harnesses and a git-backed wiki. Far more capable, far more to install. Its per-harness
  support matrix is the best public catalogue of where handoff actually breaks.
- [beads](https://github.com/gastownhall/beads) — a git-backed work graph as agent memory.
  Substantial overlap; a Go binary with its own CLI rather than markdown any agent can read.
- [planning-with-files](https://github.com/OthmanAdi/planning-with-files) — persistent plans and
  recovery after compaction.
- The many `handoff` / `session-handoff` skills — write-at-exit summaries, which is the failure mode
  described at the top.

What stele does differently: **write-ahead rather than write-at-exit**, a protocol you can follow
with no tooling at all, and task files that carry no executable content.

Credit where it is due: I-PASS (Starmer et al.), SBAR, the aviation Minimum Equipment List and
checklist literature, and David Marquet's "I intend to…" — all of them doing versions of this
problem with real consequences attached.

## License

MIT
