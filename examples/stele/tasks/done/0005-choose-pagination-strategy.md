---
id: T-0005
title: Choose a pagination strategy for the public API
status: done
last_modified_by: claude-opus-5
created_at: 2026-08-20T09:00Z
updated_at: 2026-08-24T16:40Z
scope:
  - bench/
  - docs/adr/
---

## Goal

`/documents` and `/search` both paginate with `?page=&per_page=`, which is slow and returns
duplicate rows under concurrent inserts. Decide what replaces it before committing to an
implementation.

## Done when

A recommendation is written up with measurements behind it, and whatever it settles is recorded in
PROJECT_CONTEXT so the implementation task does not have to re-derive it.

## State

Closed. Cursor pagination with opaque base64url cursors, sort key `(created_at, id)`.

Recorded in `PROJECT_CONTEXT.md` as each point was settled rather than at close: two Decisions
entries (2026-08-24), and the "`created_at` is not unique" fact into Invariants the day it was
found. Implementation is T-0007. `/search` was deliberately left on offset pagination — under
Deferred, with a date.

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

## Steps

### 1. Measure the current offset behaviour  [done]

- last_modified_by: claude-opus-5
- anchor: main@41c0e7a
- files: bench/offset-vs-keyset.md, bench/seed.ts
- intent: seed 50k rows and time page 1, page 100, page 1000 with and without an index
- done when: numbers written up in bench/offset-vs-keyset.md
- outcome: page 1000 is 430ms with an index, 470ms without — the index barely helps because
  Postgres still counts skipped rows. Confirms the problem is OFFSET, not indexing.

### 2. Prototype keyset pagination  [done]

- last_modified_by: claude-opus-5
- anchor: main@41c0e7a
- files: bench/keyset-proto.ts
- intent: same queries with a `WHERE (created_at, id) < (?, ?)` predicate
- done when: page 1000 under 20ms and no duplicates across pages
- outcome: 8ms. First attempt used `created_at` alone and produced duplicates — see
  Attempts/Pitfalls. `(created_at, id)` is correct and was promoted to Invariants.

### 3. Evaluate a materialised page-number table  [done]

- last_modified_by: claude-opus-5
- anchor: main@8bd1f92
- files: bench/pagetable-proto.sql
- intent: check whether precomputed page boundaries beat cursors for the client API
- done when: a yes/no with a reason
- outcome: no. Correct only until the next insert, and it needs a write on every insert. Recorded
  as rejected.

### 4. Write up the recommendation  [done]

- last_modified_by: claude-opus-5
- anchor: main@8bd1f92
- files: docs/adr/0004-pagination.md
- intent: cursors, opaque encoding, `(created_at, id)`, with the measurements attached
- done when: ADR merged and the decisions are in PROJECT_CONTEXT
- outcome: merged. Two entries added to PROJECT_CONTEXT Decisions. `/search` left on offset
  pagination and recorded under Deferred with a review date.
