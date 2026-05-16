# Post 1: Teaser / Origin Story

**Posting slot:** Fri 2026-05-15 or Mon 2026-05-18, 9-10 AM CT
**Theme:** Why I built this. Setup for the rest of the series.
**CTA:** Subscribe to the Substack series + star the repo.

---

## Substack draft

### Title

Your coding agent has amnesia. I shipped the fix as an open-source Python package.

### Body

Every Claude Code user I know has hit this exact moment.

You are 90 minutes deep into refactoring a service. The agent has finally figured out the test fixtures, the weird async pattern, the one helper that breaks if you import it before logging is configured. Then the context bar fills up. Claude compacts. You watch a useful, specific conversation collapse into a 200-word summary, and the agent comes back having forgotten which file you were even editing.

I lost a whole afternoon to this last quarter. Not once. Twice.

The Anthropic team has shipped two responses so far. CLAUDE.md gives you a static document the agent reads at startup. Auto Memory lets the agent itself decide what to remember, stored under `~/.claude/projects/<project>/memory/`. Both help. Neither survives the actual failure mode I keep hitting, which is: the agent forgets the **tactical** state — which branch I'm on, which 3 commits I shipped this session, what I tried that failed.

I started writing hand-rolled `plan.md` + `context.md` + `tasks.md` files into every repo. It worked, but I was maintaining them manually, and every time I switched between Claude Code and Codex the contract was different.

So I built `repo-context-hooks`.

It is a 100% open-source Python package. One-line install:

```
pip install repo-context-hooks
repo-context-hooks install --platform claude
```

It registers four hooks at the agent's lifecycle events — `SessionStart`, `PreCompact`, `PostCompact`, `SessionEnd` — and writes a deterministic workspace contract into `specs/README.md` in your repo. Not into `~/.claude/`. Into the repo. Where git can see it. Where your teammate can review it. Where `git blame` works.

PreCompact fires, the hook writes branch + last 3 commits + working changes into `specs/README.md`. PostCompact fires, the agent reads that file and resumes with real tactical state, not a lossy LLM summary.

Over the next two weeks I'm going to walk through:

- **Tue 5/19:** Why context compaction is a deeper problem than it looks, with real data from anthropics/claude-code issue threads.
- **Thu 5/21:** The 10 things that make `repo-context-hooks` different from CLAUDE.md, Auto Memory, claude-mem, and Context Mode.
- **Tue 5/26:** Real before/after metrics — what `measure experiment` actually shows after a week of hooked sessions.
- **Thu 5/28:** Where the roadmap is going (cross-workspace rollup is shipped; team rollup is next), and how to contribute.

If you spend your days inside Claude Code or Codex on a real codebase, **subscribe** so you don't miss the rest. The first technical deep-dive lands Tuesday.

Repo (star it if any of this resonates): https://github.com/narendranathe/repo-context-hooks

---

## LinkedIn draft

I just open-sourced a Python package that fixes the single most expensive failure mode in Claude Code: context loss after compaction.

If you've used Claude Code on a real codebase for more than 30 minutes, you've hit this. You are deep into a refactor, the agent has finally loaded the right mental model of the codebase, and then the context bar fills. Compaction fires. Two paragraphs of summary later, the agent is asking which file it was editing.

CLAUDE.md and Auto Memory help but they store everything in `~/.claude/`. Machine-local. Not in git. Your teammates can't review what the agent "knows." Worse, the summary is LLM-generated — it drops branch state, the last 3 commits, what you tried that failed. The tactical context that matters most.

`repo-context-hooks` flips the storage decision. It wires the four Anthropic lifecycle hooks (SessionStart / PreCompact / PostCompact / SessionEnd) and writes a deterministic workspace contract directly into your repo at `specs/README.md`. Diff-able. PR-reviewable. Survives compaction by design.

One line to install:

`pip install repo-context-hooks && repo-context-hooks install --platform claude`

Zero runtime dependencies. Works across Claude Code, Codex, Cursor, Replit, Windsurf, Ollama, Kimi, Lovable, and OpenClaw with the same contract.

Over the next two weeks I'll be publishing a 5-post series: the problem, the solution, the 10 USPs, real before/after metrics, and the roadmap.

Star the repo if you want to follow along: https://github.com/narendranathe/repo-context-hooks

What's the worst context loss moment you've hit with an AI coding assistant? Drop it in the comments.

#ClaudeCode #AIAgents #DeveloperTools #OpenSource #AIEngineering #ContextEngineering #BuildInPublic
