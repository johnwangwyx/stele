---
id: T-0001
title: <imperative one-line summary>
status: todo
last_modified_by:
created_at: YYYY-MM-DDTHH:MMZ
updated_at: YYYY-MM-DDTHH:MMZ
scope:
  - <file glob this task may touch - required when agents run in parallel>
abort_when: <the stopping rule, decided now while the plan is fresh, e.g. "if a third approach fails, stop and ask">
requires:
  tools:
    - id: <tool or MCP tool name>
      why: <what it is for>
      fallback: <shell equivalent, or "none - ask the user, do not guess">
  skills:
    - id: <skill name>
      fallback: <manual equivalent>
---

<!-- status: todo | in-progress | blocked | paused | done
     last_modified_by: the agent or model name that last wrote this file
     Do not put trailing `#` comments on frontmatter values - they are parsed as part
     of the value. Section names matter: the parser looks for `## Steps` exactly.
     See examples/stele/ for a filled-in version of this file, plus the project
     context that goes with it. -->

## Goal

<What outcome this task is for, and why it is worth doing. One paragraph.>

## Done when

<How anyone can tell the whole task is finished. Prose, not a command - the agent works out
how to check it using the Build/Test commands in PROJECT_CONTEXT.>

## Summary

<3-5 lines, rewritten (not appended) at each step close. The condensed course of the work -
the first thing the next agent reads. Say plainly if the tree is mid-edit.>

## Assessment

<Interpretation, kept separate from observation, with the evidence for it. "Probably the
non-unique sort column - two fixture rows share a timestamp and both appear on consecutive
pages." If you have no evidence, say so.>

## Attempts/Pitfalls

_Append-only. Never delete an entry: a later agent will be drawn to the same dead end, and
this is the only thing that stops it paying for the same failure twice._

- <approach> - abandoned because <reason>. Evidence: <log line, error, measurement>
- <gotcha discovered - something that will bite the next person even though nobody tried it>

## Decisions

- <choice made inside this task. Promote to PROJECT_CONTEXT.md on close if it binds future work.>

## Steps

<!-- Open a step BEFORE acting: editing files, anything over ~2 minutes, anything hard to
     reverse, or a decision that binds future work. Five lines, not a paragraph. Written
     ahead of the work so it survives the session doing it. Update `intent` and add findings
     as you go on a long step - a step that dies at minute 38 should not read like minute 0. -->

### 1. <what this step does>  [open]

- last_modified_by: <agent or model name>
- anchor: <branch>@<sha> — the commit this step started from
- files: <comma-separated files this step will touch, on one line>
- intent: <what you are about to do>
- done when: <how the next agent can tell this step finished>
- caveat: <optional - something that looks fine but is not trusted, e.g. "green only against
  the local fixture">
- outcome: <filled in at close, then mark the heading [done]>
