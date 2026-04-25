# Telemetry Policy

`repo-context-hooks` is local-only by default.

Remote telemetry is off by default and must require explicit opt-in before any data leaves a developer's machine.

## Current Behavior

The current MVP writes local JSONL evidence so developers can prove hooks and repo continuity are working on their own machine.

Current local telemetry may include:

- timestamp
- lifecycle event name
- event source
- hashed repo id
- repo folder name
- git branch name
- continuity score
- estimated baseline score
- counts such as next-work items or open issues
- local evidence-log path

Current local telemetry does not leave the machine unless the user chooses to share it.

## Future Remote Telemetry

Future remote telemetry may be added only as an explicit opt-in feature.

Before remote telemetry is enabled, the product must show developers:

- what data is collected
- why it is collected
- where it is sent
- how it is stored
- how to disable it
- how to request deletion when account-level identity exists

Consent must be revocable. Remote collection must stop after consent is revoked.

## What Must Never Be Collected

- No source code
- No prompts
- No compact summaries
- No issue bodies
- No secrets
- No API keys
- No environment variable values
- No resume or personal career data
- No full local filesystem inventory

## Cookies

No cookies are used by the CLI.

Cookies may only be used later by an optional web dashboard for normal browser session behavior. They must not be used to silently identify CLI users or bypass telemetry consent.

For CLI, hooks, skills, and MCP flows, consent should be represented by a local config value or consent token, not browser cookies.

## Public Aggregate Metrics

If a community telemetry server is added later, the public repo may show aggregate metrics such as:

- number of opted-in installations
- number of opted-in active repos
- number of observed local hook events
- average continuity score
- average estimated uplift
- platform readiness distribution

Public metrics must be aggregate-only and must not expose individual repo names, usernames, local paths, prompts, source code, or organization identities without a separate explicit publishing step.

## Recommended Consent Text

```text
repo-context-hooks can optionally send privacy-preserving usage metrics to the maintainer so the community can see adoption and continuity impact.

Collected: anonymous install id, package version, platform adapter, lifecycle event counts, continuity score, estimated baseline score, and coarse OS/runtime information.

Never collected: source code, prompts, compact summaries, issue bodies, secrets, environment values, resumes, or personal files.

Remote telemetry is optional and can be disabled at any time.
```
