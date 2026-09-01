# The PASS protocol

A procedure for resuming software work that a different agent — or a different model, harness,
or provider — started and did not finish.

PASS is adapted from **I-PASS**, the clinical handoff protocol. In a 2014 study across nine
pediatric residency programs, introducing I-PASS was associated with roughly a 23% reduction in
medical error rates. The reason it works is not the mnemonic; it is that the receiver has to
state back what they understood, and the sender corrects them.

Both domains are solving the same problem. Harm concentrates at transitions.

## The four steps

**P — Project.** The standing context. What this project is, how to build and test it, its
conventions, and the constraints that are not visible in the code. Split by volatility:
invariants that rarely change, and current state that changes weekly. Stale invariants are more
dangerous than missing ones, because they produce confident wrong actions — so they carry a
`Last verified` date.

**A — Actions.** What is open, in priority order, and what the next concrete step is for each.
Not a narrative. A census plus next actions, one line each. Forward actions carry their trigger
where they have one — "after the build passes", "blocked until the dependency lands" — because
an ordered list without triggers loses the reason for the order.

**S — Situation.** What is happening *right now*: which task is active, which step is open, what
the tree looked like when that step started, and the command that proves whether it finished.
This is the part that decays fastest and matters most, and it is why the record is written
before the work rather than after it.

**S — Synthesis.** The receiver states back the goal, the next action, and the top risk — then
checks it. Against the machine first (run the verify command, diff the anchor), and against the
human only for what no artifact can settle.

## Why there is no I

I-PASS begins with **I**llness severity: stable, watcher, unstable. It sets reading order, so
the receiver knows which patient might page them tonight before reading about any of them.

The software analogue would be a declared field — is the tree coherent, is something untrusted,
is a migration half-applied. We deliberately do not have one, because it is **derivable**:

```
step open + worktree ≠ anchor + verify fails   ⇒ mid-surgery, reconcile before advancing
step open + worktree ≈ anchor                  ⇒ intent declared, little done
no open step + verify passes                   ⇒ coherent
```

A derived signal cannot go stale and cannot lie. A declared one can do both — and worse, the
agent that would have set it to `unstable` is exactly the agent that died before it could.

The one case that is not derivable is an untrusted assumption: "the build is green, but only
against a local dependency, not the real pipeline." Nothing in git or a test suite reveals that.
It is recorded as a `caveat:` line on the open step — a note, not a tier.

## What replaces the sender

In a clinical handoff the outgoing clinician is standing there. The receiver synthesizes, and
gets corrected on the spot. That correction is what makes the final S work.

Here the sending agent is gone. Its session ended, hit a limit, or crashed — that is the whole
premise. Two things stand in for it:

1. **Machine-checkable state.** The `verify:` command and the git `anchor:` correct the receiver
   without anyone present. This is why verify commands are mandatory rather than nice to have:
   they are carrying the load the sender carries in medicine.

2. **The human.** They are the one element constant across a harness switch. But they are a
   degraded sender — they were not watching closely, time has passed, and they may not be
   available at all. So route by who can actually settle the question: the machine for state,
   the human for intent, priority, and contradiction.

## Where the design comes from

Beyond I-PASS:

- **Write-ahead intent** — from submarine practice ("I intend to…"), where the crew announces an
  action and acts on assent. The journal entry is written before the work, so it survives the
  death of the agent doing it. A record written afterwards cannot describe a crash.
- **Verify as observable state** — from aviation checklists. "Gear down" is confirmed by three
  green lights, not by remembering the lever. Every step carries a command, not a description.
- **Abort criteria decided in advance** — from V1 speed, decision height, and NASA flight rules.
  An agent 40k tokens into a failing loop is precisely the entity that cannot decide to stop, so
  the stopping rule is written while the plan is fresh.
- **Deferred defects with an expiry** — from the aviation Minimum Equipment List. An aircraft may
  fly with something broken only if it is logged, categorized, and carries a repair deadline.
  Known-broken things are governed, not scattered as TODOs.
- **Fact separated from assessment** — from SBAR. Observations and interpretations live in
  different sections, so a reader can tell what was measured from what was guessed.
- **Scope discipline while a step is open** — from the sterile cockpit rule. Out-of-scope
  discoveries are recorded, not acted on.

## What was deliberately not copied

These industries have well-documented failure modes, and an LLM makes each of them worse,
because it will always produce something that *looks* like a valid entry.

- **Checklist fatigue.** Long checklists get filled in without being read. Few fields.
- **Copy-forward.** Clinical notes propagate stale pasted text that outlives its truth. Every
  field is either machine-checkable or cheap to leave blank.
- **Alarm fatigue.** If everything is flagged, nothing is.

The governing rule: **prefer a field a machine can check over prose a model can fake.** One
`verify:` command that runs is worth ten narrative fields.

## Following PASS without any tooling

The protocol is the valuable part; the scripts only make it faster. By hand:

```bash
grep -l '^status: in-progress' stele/tasks/*.md   # locate
cat stele/PROJECT_CONTEXT.md                     # P
cat stele/TASKS.md                               # A
cat stele/tasks/<active>.md                      # S — then run its verify:, diff its anchor
```

Then state back goal, next action, and top risk before touching anything.
