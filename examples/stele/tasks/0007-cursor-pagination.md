---
id: T-0007
title: Migrate the /documents list endpoint from offset to cursor pagination
status: in-progress
last_modified_by: claude-opus-5
created_at: 2026-08-30T11:20Z
updated_at: 2026-08-31T14:02Z
scope:
  - src/routes/documents.ts
  - src/services/documents.ts
  - test/contract/documents.test.ts
requires:
  tools:
    - id: github.create_pull_request
      why: open the PR once the contract tests pass
      fallback: gh pr create --title ... --body-file ...
---

## Goal

`GET /documents` paginates with `?page=&per_page=`, which scans the whole table and returns
duplicate rows when inserts land mid-pagination. Move it to opaque cursors, keeping the old
parameters working for one release.

## Done when

`/documents` accepts `?cursor=&limit=`; the contract tests cover first page, middle page, last
page, and empty result; paginating a table that receives inserts mid-scan returns no duplicates;
and `?page=` still works and is marked deprecated in the OpenAPI spec.

## State

Cursor encode/decode is finished and unit-tested. The route and service both accept `cursor`, but
the keyset predicate is **half-applied**: `services/documents.ts` builds the `(created_at, id)`
predicate while `routes/documents.ts` still passes only `created_at` through. Tree compiles; 3 of 9
contract tests red. Next: finish the route half, then re-run the suite.

Guess, not proven: the duplicates are the non-unique `created_at` rather than a transaction
isolation problem — two fixture rows share a timestamp and both appear on consecutive pages. Not
tested under genuine concurrent inserts.

## Attempts/Pitfalls

_Append-only. A later agent will be drawn to the same dead ends._

- Keyset on `created_at` alone — returns duplicates across pages whenever two rows share a
  timestamp, and the fixture has three such pairs. `created_at` is not unique; PROJECT_CONTEXT says
  so under Invariants and I missed it.
- Encoding the cursor as raw JSON in the query string — breaks on the `+` in timestamps once
  URL-decoded. Switched to base64url.
- Do not add `ORDER BY created_at DESC, id DESC` expecting it to be fast in staging: there is no
  `(created_at, id)` index there (see PROJECT_CONTEXT Deferred), so the plan falls back to a full
  sort. A fast local query is not evidence about staging.
- Chose a translation shim for `?page=` over dual code paths through the service — one place to
  delete when the deprecation lands. Task-local, so not promoted.

## Steps

### 1. Add cursor encode/decode helpers  [done]

- last_modified_by: claude-opus-5
- anchor: main@9c1e044
- files: src/services/cursor.ts, test/unit/cursor.test.ts
- intent: base64url encode/decode of `{created_at, id}` with a version prefix
- done when: round-trip unit tests pass for normal, empty, and malformed input
- outcome: done, 6 unit tests green. Malformed cursors throw `BadRequest`, mapped to 400 in the
  route layer.

### 2. Switch the service and route to keyset pagination  [open]

- last_modified_by: claude-opus-5
- anchor: main@a3f19c2
- files: src/services/documents.ts, src/routes/documents.ts
- intent: replace LIMIT/OFFSET with a `(created_at, id)` keyset predicate, and keep `?page=`
  working through a translation shim
- done when: all nine contract tests in `test/contract/documents.test.ts` pass, including the
  insert-during-pagination case
- caveat: the service half passes its unit tests, but only against the small local fixture and
  with no `(created_at, id)` index in staging — do not read a fast local query as evidence about
  production behaviour
