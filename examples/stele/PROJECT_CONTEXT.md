# Project context

## Invariants

_Rarely changes. Wrong entries here cause confidently wrong actions._

- **What this is:** REST API for a document store. Node 20, Express, Postgres 15.
- **Build:** `npm run build`
- **Test:** `npm test` (Jest). One suite: `npm test -- <pattern>`
- **Run locally:** `docker compose up -d db && npm run dev` — serves on :3000
- **Layout:** HTTP handlers in `src/routes/`, business logic in `src/services/`, migrations in
  `db/migrations/` (node-pg-migrate, forward-only)
- **Conventions:** services never import from `src/routes/`; every route has a contract test in
  `test/contract/`
- **Non-obvious constraints:** `documents.created_at` is **not unique**, so it cannot be a sort
  key on its own. Migrations run automatically on deploy and are not reversible in production —
  additive changes only.

_Last verified: 2026-08-31_

## Current state

_Volatile. Update whenever it stops being true._

- **Active workstream:** replacing offset pagination across the public API (T-0007)
- **Known broken / deferred:** see Deferred below
- **Open questions:** after v2 ships, should `?page=` keep working or return 400? Unresolved with
  the API consumers.

## Decisions

_Choices that bind future tasks. Promoted here when a task closes, so they outlive it._

| Date | Decision | Why |
|---|---|---|
| 2026-08-24 | Cursor pagination with opaque base64url cursors | Offset scans got slow past ~50k rows, and clients saw duplicate rows when inserts landed mid-pagination |
| 2026-08-28 | Sort key is `(created_at, id)`, never `created_at` alone | `created_at` is not unique — see Invariants |

## Deferred

_Known-broken things tolerated on purpose. Adapted from the aviation Minimum Equipment List:
you may fly with it broken only if it is logged, justified, and dated. An entry with no `Until`
is a TODO pretending to be a decision._

| Item | Why tolerable | Until |
|---|---|---|
| `/search` still uses offset pagination | Low traffic, results capped at 100 | 2026-10-15 |
| No `(created_at, id)` index in staging | Staging dataset is small enough that the full sort is not noticeable | before T-0007 ships to prod |
