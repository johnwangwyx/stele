---
id: T-0001
title: <imperative one-line summary>
status: todo
owner:
created_at: YYYY-MM-DDTHH:MMZ
updated_at: YYYY-MM-DDTHH:MMZ
scope:
  - <file glob this task may touch - required when agents run in parallel>
abort_when: <the stopping rule, decided now while the plan is fresh. e.g. "build fails 3x on this approach - stop and ask">
requires:
  tools:
    - id: <tool or MCP tool name>
      why: <what it is for>
      fallback: <shell equivalent, or "none - ask the user, do not guess">
  skills:
    - id: <skill name>
      fallback: <manual equivalent>
---

## Goal

<What outcome this task is for. One paragraph.>

## Done when

`<command that proves the whole task is finished>`

## Summary

<3-5 lines, rewritten (not appended) at each step close. This is the first thing the next
agent reads - it is the condensed course of the work, not the log.>

## Assessment

<Interpretation, kept separate from observation, with the evidence that supports it.
"Probably a race condition in the retry path - two threads hit RetryConfig at build.log:412."
If you have no evidence, say so.>

## Attempts

_Append-only. Never delete an entry: a later agent will be tempted by the same dead end,
and this is the only thing that stops it paying for the same failure twice._

- <approach> - abandoned because <reason>. Evidence: <log line, error, benchmark>

## Decisions

- <choice made inside this task. Promote to PROJECT_CONTEXT.md on close if it binds future work.>

## Steps

<!-- Open a step BEFORE acting - editing files, anything over ~2 minutes, anything
     hard to reverse, or any decision that binds future work. Five lines, not a paragraph.
     Written ahead of the work so it survives the session that was doing it. -->

### 1. <what this step does>  [open]

- opened: YYYY-MM-DDTHH:MMZ by <model> / <harness>
- anchor: <branch>@<sha>, clean|dirty
- files: <the files this step will touch>
- intent: <what you are about to do>
- verify: `<command that proves this step is done>`
- caveat: <optional - something green but untrusted, e.g. "passes only against a local dep">
- outcome: <filled in at close, then mark the heading [done]>
