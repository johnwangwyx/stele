# Project context

## Summary

Public REST API for a document store: clients upload documents, tag them, and list or search
them. Consumed by two first-party web apps and about a dozen external integrations on API keys,
so response shapes are a compatibility surface — breaking one costs a deprecation cycle. Node 20,
Express, Postgres 15, deployed as a single service behind a load balancer.

## Invariants

_Rarely changes. If something here is wrong, an agent will act on it with confidence._

- **Checks:** `npm test` (Jest), `npm run lint`, `npm run typecheck`. All three gate CI — tests
  passing alone is not enough. One suite: `npm test -- <pattern>`
- **Run locally:** `docker compose up -d db && npm run dev` — serves on :3000
- **Prerequisites:** Postgres must be up via docker compose, and `.env` must exist (copy
  `.env.example`). Without either, every test fails with a connection error that looks like a
  code bug.
- **Layout:** HTTP handlers in `src/routes/`, business logic in `src/services/`, migrations in
  `db/migrations/` (node-pg-migrate, forward-only)
- **Conventions:** services never import from `src/routes/`; every route has a contract test in
  `test/contract/`
- **Dependencies:** exact pins, no carets. New runtime dependencies need a maintainer's sign-off;
  dev dependencies are fine to add.
- **How work lands:** branch `<type>/<short-slug>`, conventional commits, PR required, CI green
  before requesting review. Squash merge.
- **Non-obvious constraints:** `documents.created_at` is **not unique**, so it cannot be a sort
  key on its own. Migrations run automatically on deploy and are not reversible in production —
  additive changes only.

_Last verified: 2026-08-31_

## Guardrails

_Read this even if you read nothing else._

- **Do not touch:** `src/generated/` (regenerated from the OpenAPI spec by `npm run codegen` —
  edit `openapi.yaml` instead), `db/schema.sql` (dumped from migrations), `package-lock.json`
  by hand.
- **Do not run:** `npm run migrate` against anything but the local docker database — migrations
  are not reversible in production. Do not run `npm run test:e2e` casually; it provisions real
  infrastructure, takes ~40 minutes, and bills. CI runs it on merge.

## Current state

- **Active workstream:** replacing offset pagination across the public API (T-0007)
- **Open questions:** after v2 ships, should `?page=` keep working or return 400? Unresolved with
  the API consumers.

## Decisions

| Date | Decision | Why |
|---|---|---|
| 2026-08-24 | Cursor pagination with opaque base64url cursors | Offset scans stayed slow past ~50k rows even with an index, and clients saw duplicate rows when inserts landed mid-pagination. From T-0005. |
| 2026-08-24 | Cursors are opaque, never an exposed offset | Lets the encoding change without breaking the dozen external integrations. From T-0005. |
| 2026-08-28 | Sort key is `(created_at, id)`, never `created_at` alone | `created_at` is not unique — see Invariants |

## Deferred

| Item | Why tolerable | Until |
|---|---|---|
| `/search` still uses offset pagination | Low traffic, results capped at 100 | 2026-10-15 |
| No `(created_at, id)` index in staging | Staging dataset is small enough that the full sort is not noticeable | before T-0007 ships to prod |
