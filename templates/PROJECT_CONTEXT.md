# Project context

<!-- Budget: ~150 lines. The test for anything you want to add: if `ls`, `git log`, or reading a
     config file answers it, leave it out. What belongs here is what an agent cannot cheaply
     derive, or would derive wrongly.

     These sections are defaults, not a fixed schema - add your own where the project needs
     them (a glossary for a domain-heavy codebase, a runbook pointer, an escalation path).
     Keep Summary, Invariants and Guardrails; the rest are useful but not load-bearing.

     Filled-in version: examples/stele/PROJECT_CONTEXT.md -->

## Summary

<2-4 sentences: what this project is for, who consumes it, and its overall shape. This is read
first - orient the reader before they hit build commands.>

## Invariants

_Rarely changes. If something here is wrong, an agent will act on it with confidence._

- **Checks:** every command that must pass before work counts as done - build, test, lint,
  typecheck, format. Not just tests; CI will fail on the others.
- **Run locally:**
- **Prerequisites:** what must already be true or nothing works - services running, env vars,
  credentials, VPN, seeded data
- **Layout:** where the interesting code lives
- **Conventions:** things a reasonable person would get wrong
- **Dependencies:** the policy on adding or upgrading them
- **How work lands:** branch naming, commit convention, whether to open a PR, whether CI must be
  green first
- **Non-obvious constraints:** why the obvious approach does not work here

_Last verified: YYYY-MM-DD_

## Guardrails

_Read this even if you read nothing else. Kept out of the list above so it is not skimmed past._

- **Do not touch:** generated files, vendored code, codegen output, anything owned elsewhere. It
  looks hand-written, and an edit there is silently lost on the next build.
- **Do not run:** destructive or expensive commands, and what to do instead.

## Current state

_Volatile. Update whenever it stops being true._

- **Active workstream:**
- **Open questions:**

## Decisions

_Choices that bind future tasks. Promoted here when a task closes, so they outlive it._

| Date | Decision | Why |
|---|---|---|
|  |  |  |

## Deferred

_Known-broken things tolerated on purpose. Adapted from the aviation Minimum Equipment List: you
may fly with it broken only if it is logged, justified, and dated. An entry with no `Until` is a
TODO pretending to be a decision._

| Item | Why tolerable | Until |
|---|---|---|
|  |  |  |
