# Post 4: Use Cases + Measurable Impact

**Posting slot:** Tue 2026-05-26, 9-10 AM CT
**Theme:** How devs are using it, real before/after metrics, three concrete workflows.
**CTA:** Run `measure export` and share your own delta in the comments.

> **Pre-post checklist (do this Mon 5/25):**
> 1. Run `repo-context-hooks measure experiment finish` on the baseline you started 5/21.
> 2. Capture the redacted output of `repo-context-hooks measure export --format markdown` and paste real numbers into the placeholders below (marked `[REPLACE]`).
> 3. Drop in 2 screenshots: the SVG badge before / after, and the dashboard at `docs/monitoring/`.

---

## Substack draft

### Title

What happens when you actually run `repo-context-hooks` for a week — receipts

### Body

Last Thursday I asked you to install `repo-context-hooks`, run `measure experiment start`, then go do your normal work. Today I'm going to walk through what mine looked like over the past week and how to read the output.

### My setup

- One active repo: `autoapply-ai` (a FastAPI + Chrome MV3 + Postgres + Redis stack).
- Claude Code primary, Codex as a secondary harness for parallel feature work.
- Average session length: 90 minutes.
- Auto-compaction events: roughly 4 per day.

### The headline numbers

After 7 days of normal work, `measure export --format markdown` returned:

```
Continuity score:              [REPLACE]    (baseline: [REPLACE])
Lifecycle coverage:            [REPLACE]%   (target >= 75%)
Cold starts prevented:         [REPLACE]
cold_start_time_saved_minutes: [REPLACE]
Tokens saved (est.):           [REPLACE]
Cost saved (est., USD):        $[REPLACE]
Week-1 uplift:                 +[REPLACE]
```

The two metrics I care about most:

- **`cold_start_time_saved_minutes`** — this counts `PostCompact` events and multiplies by 5 minutes, the conservative estimate of how long it would have taken to re-prime the agent from scratch. Mine landed at `[REPLACE]` minutes over the week.
- **Week-1 uplift** — the day-7 continuity score minus day-0. Anything positive means the contract is getting denser. Mine was `+[REPLACE]`.

### Three concrete use cases

**1. Long refactors that span days.** I'm in the middle of a Clerk auth refactor on `autoapply-ai`. The session log in `specs/README.md` now contains 7 timestamped decision entries — "rejected approach X because of circular import," "chose Z because of the IPv4 pooler constraint on Fly.io." Next session walks in already knowing which doors are closed.

**2. Switching between Claude Code and Codex on the same repo.** Both agents read the same `specs/README.md`. I no longer re-explain "we already decided to use the session-mode pooler" every time I switch harness.

**3. Onboarding a teammate.** This one surprised me. A friend cloned the repo to look at an issue. Their Claude Code session at `SessionStart` read my workspace contract and immediately knew the project shape, the open questions, and the next action. Zero context-loading prompt from them.

### How to read the dashboard

`repo-context-hooks measure --open` launches a local HTML dashboard at `docs/monitoring/index.html`. Three columns matter:

- **Lifecycle coverage** — what % of expected hook events actually fired. Below 25% (red badge) means your install is broken. Run `doctor`.
- **Cold starts prevented** — how many `PostCompact` reload events happened. Higher is better (means compaction fired but you didn't lose context).
- **Avg session duration** — drift here points at workflow changes, not tool problems.

### How to share your own numbers

`measure export --format markdown -o impact.md` produces a redacted impact report you can paste anywhere. Repo names get redacted to short hashes, timestamps stay, scores stay. Paste it into a PR description when you ship the install, into a LinkedIn post, into your weekly update to your manager.

### What I want from you

If you've been running the hooks for a week, drop your `cost_saved_usd` and lifecycle_coverage % in the comments. The strongest deltas will go into Thursday's roadmap post, with credit and links.

Thursday: roadmap (cross-workspace rollup is shipped, team rollup is next), how to contribute, what feedback I want.

Repo: https://github.com/narendranathe/repo-context-hooks

---

## LinkedIn draft

One week of `repo-context-hooks` running on my main repo. Receipts below.

I asked you all last Thursday to install + start an `experiment` baseline. Here's mine after 7 days of normal Claude Code + Codex work on a FastAPI + Postgres + Chrome MV3 stack:

```
Continuity score:              [REPLACE]
Lifecycle coverage:            [REPLACE]%
Cold starts prevented:         [REPLACE]
Time saved (cold starts):      [REPLACE] min
Tokens saved:                  ~[REPLACE]
Cost saved (est.):             $[REPLACE]
Week-1 uplift:                 +[REPLACE]
```

The metric I care about most: `cold_start_time_saved_minutes`. It counts every `PostCompact` event and multiplies by 5 min — the conservative estimate of how long it would take to re-prime the agent if compaction had wiped my context. Mine landed at `[REPLACE]` over the week.

Three places this paid off most:

1) Long refactors that span days. The `## Session Log` in specs/README.md now has 7 decision entries with rationale ("rejected X because circular import," "chose Z because of the IPv4 pooler"). Future-me walks in knowing which doors are closed.

2) Switching between Claude Code and Codex on the same repo. Both read the same contract. No re-explaining what we already decided.

3) Onboarding a teammate. A friend cloned the repo, Claude Code at SessionStart read the contract, they had zero ramp time on what the project even was.

If you installed it last week, run `measure export --format markdown` and post your delta. Best ones go into Thursday's roadmap post.

Install if you haven't: `pip install repo-context-hooks`
Repo: https://github.com/narendranathe/repo-context-hooks

What's the biggest "I have to re-explain this to the agent" moment that this would have saved you?

#ClaudeCode #DeveloperTools #AIAgents #LLMOps #BuildInPublic #AIEngineering #OpenSource #PythonDev
