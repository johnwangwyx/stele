---
id: T-0007
title: Migrate all retry config from ADAPTIVE to STANDARD
status: in-progress
owner: claude-code/sess-4f2a
created_at: 2026-08-30T11:20Z
updated_at: 2026-08-31T14:02Z
scope:
  - src/retry/**
  - src/client/**
abort_when: build fails 3x on the same approach - stop and ask rather than widening the change
requires:
  tools:
    - id: github.create_pull_request
      why: open the PR once tests are green
      fallback: gh pr create --title ... --body-file ...
  skills:
    - id: build-analyzer
      fallback: "./gradlew build > build.log 2>&1; tail -50 build.log"
---

<!-- A worked example: a task partway through, written by an agent that then hit a rate limit.
     Note that frontmatter must be the very first thing in the file. Everything a fresh agent
     needs in order to continue is already here - nobody wrote a handoff. -->

## Goal

Every retry configuration in the service uses ADAPTIVE mode, which self-throttles under load and
has caused two latency incidents. Move all 7 call sites to STANDARD with an explicit token
bucket, and prove the throttling behaviour with a test.

## Done when

`./gradlew test` is green and `grep -rn "ADAPTIVE" src/` returns nothing.

## Summary

Inventory done: 7 call sites, all funnel through `RetryConfig`. Changing `RetryConfig` alone
covers 5 of them; `LegacyClient` and `BatchClient` construct their own retry policy inline and
need separate edits. Currently mid-edit on `RetryConfig` — the token-bucket test is written but
the config change is not finished, so the tree does not compile.

## Assessment

The two latency incidents are *probably* ADAPTIVE's self-throttling rather than downstream
slowness: both show client-side backoff growing while downstream p99 stayed flat
(dashboard link in the ticket, and `build.log:412` from the repro run). Not proven — nobody has
reproduced it under controlled load.

## Attempts

- Bumped the SDK version in the config file only, hoping the default changed - failed with
  NoClassDefFoundError, the dependency set lacks the sibling artifact. Evidence: build.log:412
- Tried setting the mode via environment variable at startup - the SDK reads it before our
  config loads, so it is ignored. Evidence: RetryConfigTest#envOverride fails.

## Decisions

- Explicit token bucket over the SDK default (10 tokens, 0.5 refill) so behaviour under load is
  ours rather than the SDK's. Promote to PROJECT_CONTEXT on close - it binds future clients.

## Steps

### 1. Inventory every retry call site  [done]

- opened: 2026-08-30T11:20Z by claude-opus-5 / claude-code
- anchor: main@9c1e044, clean
- intent: find everything constructing a retry policy
- verify: `grep -rn "RetryMode\|retryMode" src/ | wc -l`
- outcome: 7 sites. 5 via RetryConfig, plus LegacyClient:88 and BatchClient:141 inline.

### 2. Update RetryConfig and add the token-bucket test  [open]

- opened: 2026-08-31T14:02Z by claude-opus-5 / claude-code
- anchor: main@a3f19c2, dirty
- files: src/retry/RetryConfig.java, src/retry/RetryConfigTest.java
- intent: set retryMode STANDARD with an explicit 10-token bucket, assert throttling under 50 rps
- verify: `./gradlew test --tests RetryConfigTest`
- caveat: the test passes against the local dependency override only - not yet run against the
  real pipeline, so treat green here as provisional
