# Project context

## Summary

<1-3 tight paragraphs: what this project is for, who consumes it, and its overall shape. This is
read first - orient the reader before they hit build commands.>

## Invariants

<!-- Rarely changes. If something here is wrong, an agent will act on it with confidence. -->

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

<!-- What must not be touched or run - kept out of the list above so it is not skimmed past.
     `None` until you find the first one; do not invent entries. -->

None.

<!-- When populated:
- **Do not touch:** generated files, vendored code, codegen output, anything owned elsewhere. It
  looks hand-written, and an edit there is silently lost on the next build.
- **Do not run:** destructive or expensive commands, and what to do instead. -->

## Current state

<!-- Volatile. Update whenever it stops being true. -->

- **Active workstream:**
- **Open questions:**

## Decisions

<!-- Choices that bind future tasks, promoted here when one is made. `None` until there is one. -->

None.

<!-- | Date | Decision | Why | -->

## Deferred

<!-- Known-broken things tolerated on purpose. An entry with no `Until` is a TODO pretending to be
     a decision. `None` until something is genuinely deferred. -->

None.

<!-- | Item | Why tolerable | Until | -->
