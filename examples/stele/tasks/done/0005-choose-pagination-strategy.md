---
id: T-0005
title: Choose a pagination strategy for the public API
status: done
last_modified_by: claude-opus-5
created_at: 2026-08-20T09:00Z
updated_at: 2026-08-24T16:40Z
---

<!-- A closed task, compacted on close: goal, outcome and Attempts/Pitfalls kept; the
     step-by-step play-by-play deleted. Closed tasks are not read during a resume, so anything
     that had to survive was promoted to PROJECT_CONTEXT when it was decided - see Outcome. -->

## Goal

`/documents` and `/search` both paginate with `?page=&per_page=`, which is slow and returns
duplicate rows under concurrent inserts. Decide what replaces it before committing to an
implementation.

## Outcome

Cursor pagination with opaque base64url cursors, sort key `(created_at, id)`.

Promoted to `PROJECT_CONTEXT.md` as each was settled, not at close: two entries in Decisions
(2026-08-24), and the "`created_at` is not unique" fact into Invariants the day it was found.
Implementation is T-0007. `/search` was left on offset pagination on purpose — recorded under
Deferred with a date.

## Attempts/Pitfalls

- Keyset on `created_at` alone looked sufficient until a fixture query returned duplicate rows —
  `created_at` is not unique. Promoted to Invariants immediately, because it is not obvious from
  the schema, which has no unique constraint to hint at it.
- A materialised page-number table. Rejected: needs a write on every insert and still drifts under
  concurrent writes, so it trades one correctness bug for a slower one.
- "Just add an index and keep `OFFSET`" — measured at 50k rows and still 400ms+, because Postgres
  counts the skipped rows regardless of the index. Evidence: `bench/offset-vs-keyset.md`.
- Do not expose the sort key in the cursor as plain text. An early prototype did, and one
  integration immediately started constructing its own cursors by hand — which is why the chosen
  cursors are opaque.
