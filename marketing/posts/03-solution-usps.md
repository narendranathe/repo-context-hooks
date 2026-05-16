# Post 3: The Solution + 10 USPs

**Posting slot:** Thu 2026-05-21, 9-10 AM CT
**Theme:** What the product does, the 10 USPs, how to install, how to use, why unique.
**CTA:** Install and run `measure experiment start` to capture your own baseline.

---

## Substack draft

### Title

`repo-context-hooks`: a git-tracked workspace contract for your AI coding agent

### Body

Tuesday I laid out the problem — Claude Code's compaction drops 20-30% of detail per event, Auto Memory is non-deterministic, CLAUDE.md is static. The gap is a contract that is deterministic AND stateful AND lives in your repo.

This post is the solution and the 10 things that make it different.

### What it does, in one sentence

`repo-context-hooks` installs four Anthropic lifecycle hooks (`SessionStart` / `PreCompact` / `PostCompact` / `SessionEnd`) and maintains a git-tracked workspace contract in your repo so the next agent session resumes with real state instead of a lossy summary.

### How to install

```
pip install repo-context-hooks
repo-context-hooks install --platform claude
repo-context-hooks doctor
```

That is the whole install. Zero runtime dependencies (`pyproject.toml` declares `dependencies = []`). `doctor` confirms the hooks are wired correctly. Auto-detect mode (no `--platform` flag) installs to every detected agent at once.

### How to use it

You don't. After install, the hooks fire on their own at the lifecycle events. Open Claude Code in any repo. The first time, it scaffolds `specs/README.md`, `UBIQUITOUS_LANGUAGE.md`, and an AUTO:REPO_CONTEXT block. Every subsequent session reads them at `SessionStart` and appends to them at `PreCompact` and `SessionEnd`.

The optional manual surface is `checkpoint --message "..."` — call it when you want to capture a semantic decision the hooks can't infer (the "why," not the "what"). Decision goes under `## Session Log` in `specs/README.md`. Future-you and future-agent both read it.

### Why developers should care — the 10 USPs

1. **Your agent's memory lives in `git`, not `~/.claude/`.** `specs/README.md` and `UBIQUITOUS_LANGUAGE.md` are checked in, diff-able, PR-reviewable. Auto Memory, claude-mem, and Context Mode all store machine-local blobs no teammate can review.
2. **Deterministic, not lossy.** `PreCompact` appends an exact snapshot: branch, last 3 commits, working changes. No LLM summarization in the loop.
3. **Bound to the four Anthropic hook events.** `SessionStart` / `PreCompact` / `PostCompact` / `SessionEnd`. Wired automatically. Directly addresses the gap closed-as-Not-Planned in anthropics/claude-code#13112.
4. **Cross-harness with one contract.** 9 platform adapters — Claude (native), Codex, Cursor, Replit, Windsurf, Ollama, Kimi, Lovable, OpenClaw. Same contract, different agent.
5. **Self-measuring with public proof.** Every install produces `continuity_score`, `cold_start_time_saved_minutes`, `tokens_saved`, `cost_saved_usd`, and a three-color SVG badge auto-rendered to `docs/badge.svg`. Receipts, not vibes.
6. **Before/after experiment mode.** `measure experiment start | finish` captures your baseline before installing hooks, then re-measures after a week. The delta is a redacted impact report you can paste into a PR, a LinkedIn post, or your manager's Slack.
7. **Zero runtime dependencies. One-line install.** Already shown above. No venv hell, no transitive CVEs.
8. **Privacy by design.** SHA-256 hashed repo IDs. No source, prompts, PR bodies, or filesystem inventory leaves your machine. `--no-telemetry` bakes opt-out into the hook command string itself so it survives shell restarts.
9. **CI-ready operational tooling.** `doctor --all-platforms`, `recommend --json`, `verify`, `--dry-run`, `--clean-ghosts`, public-surface contract. Drops into a CI gate without a 50-line shell wrapper.
10. **Supply-chain integrity by default.** GitHub Actions OIDC trusted publishing. Sigstore attestations. `gh attestation verify`. Dependabot. CodeQL. Installable inside enterprise procurement.

### Why it's unique

The unoccupied seam in this market is **repo-tracked, deterministic, lifecycle-bound** continuity. Every direct competitor breaks at least one of those:

- **CLAUDE.md** — deterministic, repo-tracked. Not lifecycle-bound. Static.
- **Auto Memory** — lifecycle-bound, deterministic in writes. Not repo-tracked (`~/.claude/`). Non-deterministic in *what* gets written.
- **claude-mem** — lifecycle-bound, repo-aware. LLM-summarized (lossy). SQLite + chromadb, not git.
- **Context Mode** — lifecycle-bound, multi-platform. Per-project SQLite blob, not in git, not reviewable.

We are the only tool that puts a diff-able workspace contract in your repo and writes to it on a hook event. That is the seam.

### What's next in the series

- **Tue 5/26:** Real `measure experiment` deltas from a week of hooked sessions on a Python service.
- **Thu 5/28:** Roadmap, contribution guide, and what I want feedback on.

Try it today and run `measure experiment start` so you have a baseline ready when Tuesday's post drops:

```
pip install repo-context-hooks
repo-context-hooks install --platform claude
repo-context-hooks measure experiment start
```

Then go do your normal work for a few days.

Repo: https://github.com/narendranathe/repo-context-hooks

---

## LinkedIn draft

10 reasons developers should care about `repo-context-hooks` — the open-source Python package that fixes Claude Code's context loss after compaction.

(Threading off Tuesday's post on why compaction drops 20-30% of detail per event.)

1. Your agent's memory lives in `git`, not `~/.claude/`. PR-reviewable workspace contract.
2. Deterministic snapshots — branch + last 3 commits + working changes. No LLM summarization.
3. Wired to the four Anthropic lifecycle hooks: SessionStart / PreCompact / PostCompact / SessionEnd.
4. Cross-harness — same contract works on Claude, Codex, Cursor, Replit, Windsurf, Ollama, Kimi, Lovable, OpenClaw.
5. Self-measuring — every install emits continuity_score, cold_start_time_saved_minutes, tokens_saved, cost_saved_usd, and an SVG badge.
6. Before/after experiment mode — `measure experiment start | finish` proves the impact with a redacted shareable report.
7. Zero runtime dependencies. One-line install: `pip install repo-context-hooks`.
8. Privacy by design — SHA-256 hashed repo IDs, no source/prompts/PR bodies collected, no remote collector.
9. CI-ready — `doctor`, `verify`, `--dry-run`, public-surface contract. Drops into a gate.
10. Supply-chain hardened — OIDC trusted publishing, Sigstore, attestations, Dependabot, CodeQL.

The unique seam: every competitor (CLAUDE.md, Auto Memory, claude-mem, Context Mode) breaks at least one of {repo-tracked, deterministic, lifecycle-bound}. We are the only tool that hits all three.

Install + start a baseline experiment right now so you have data ready for next week's post:

```
pip install repo-context-hooks
repo-context-hooks install --platform claude
repo-context-hooks measure experiment start
```

Repo: https://github.com/narendranathe/repo-context-hooks

Which of these 10 USPs matters most to your workflow? Curious where the priority sits for working devs vs platform teams.

#ClaudeCode #AIAgents #DeveloperTools #OpenSource #LLMOps #PythonDev #DevTooling #AIEngineering
