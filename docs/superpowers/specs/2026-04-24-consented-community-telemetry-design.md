# Consented Community Telemetry Design

## Goal

Create a future path for community impact metrics without violating developer trust.

The user goal is reasonable: if developers opt in, the project should be able to say how many people use the tool and what continuity impact they are seeing. The implementation must be consent-first and privacy-preserving.

## MVP Decision

Do not implement remote upload until there is a real endpoint, published policy, and consent UX.

For the current MVP, prove impact locally:

- install hooks automatically
- write local JSONL evidence
- run `repo-context-hooks measure`
- show before/after continuity uplift on the maintainer's own machine

This is what PR #22 does.

## Why Cookies Are Not The Right Primitive

Cookies are a browser/session mechanism. `repo-context-hooks` is a CLI, hook, and skill package.

No cookies should be used by the CLI to identify users or send telemetry.

If a web dashboard exists later, cookies can be used only for normal browser session behavior on that dashboard. CLI consent should use a local config value or a consent token.

## Future Architecture

### Local CLI

Add commands:

```bash
repo-context-hooks telemetry status
repo-context-hooks telemetry enable
repo-context-hooks telemetry disable
repo-context-hooks telemetry preview
```

The enable flow must show the consent text from `docs/telemetry-policy.md`.

### MCP Server

An optional MCP server can expose telemetry tools for agents:

- `telemetry_status`
- `telemetry_preview_payload`
- `telemetry_send_event`
- `telemetry_disable`

The MCP server must refuse to send events unless explicit consent exists.

### Remote Collector

A minimal remote collector can accept redacted aggregate events:

- anonymous installation id
- package version
- adapter id
- event name
- continuity score
- estimated baseline score
- coarse OS family
- timestamp bucket

The collector must reject source code, prompts, compact summaries, issue bodies, secrets, environment values, resumes, and personal career data.

### Public Metrics

A generated public metrics artifact can be committed or published:

```json
{
  "opted_in_installations": 123,
  "active_repos_30d": 57,
  "observed_hook_events_30d": 842,
  "average_continuity_score": 86,
  "average_estimated_uplift": 61
}
```

## Product Claim Boundary

Allowed:

- "Opted-in users observed an average continuity uplift of X points."
- "N opted-in installations reported hook events in the last 30 days."
- "Claude native hooks are firing in opted-in repos."

Not allowed:

- "This improves developer productivity by X%" unless backed by a real controlled study.
- "This collects anonymous data" if any stable identifier can be linked over time without explaining it.
- "Cookies power CLI telemetry."

## Open Implementation Issue

Create a follow-up issue for consented remote telemetry after this local MVP lands:

- Add telemetry consent CLI.
- Add payload preview.
- Add redacted export.
- Add optional MCP server tool surface.
- Add remote collector only after policy and endpoint are ready.
