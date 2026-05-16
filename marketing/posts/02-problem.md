# Post 2: The Problem

**Posting slot:** Tue 2026-05-19, 9-10 AM CT
**Theme:** Why context compaction is a fundamental architectural problem, with data.
**CTA:** Read the next post Thursday + open a GitHub discussion if you have a worse story.

---

## Substack draft

### Title

The 20-30% you lose every time Claude Code compacts

### Body

Claude Code's auto-compaction is one of the most-used features in any developer agent, and one of the least-discussed. Most people understand it as "the agent summarizes the conversation when it runs out of room." That framing is wrong in a way that matters.

Compaction is not a summary. It is a **lossy re-encoding**. The original tokens are gone. What you get back is a model-generated narrative of what just happened. That narrative is biased toward "what happened" and away from "why" and "subtle details" — and one community-run measurement put the retention loss at 20-30% per compaction event (source at the bottom).

Here is what the loss looks like in practice. I ran a real session last week, refactoring a FastAPI app. Pre-compact, the agent knew:

- I was on branch `feat/clerk-auth-refactor`.
- The last 3 commits were `1f9acd8`, `b054def`, `c755497`.
- I had tried two approaches to the JWT verification and rejected the first because it caused a circular import.
- The working tree had 4 modified files and 1 untracked spec.

Post-compact, the agent still knew "we are refactoring auth." It had no idea about the branch, the commits, the circular import attempt, or the working tree. The next 10 minutes were me re-priming it.

You can see this problem ratify itself in the Claude Code issue tracker. Issue [#13112](https://github.com/anthropics/claude-code/issues/13112) — "auto compact is the worst. every time it happens i feel like claude code has forgotten everything." Closed Not Planned. Issue [#43733](https://github.com/anthropics/claude-code/issues/43733) — community-filed request for a `PreCompact` hook so users can write their own state. The community wrote it themselves because the platform did not.

Auto Memory helps a bit. It stores opinions about your project in `~/.claude/projects/<project>/memory/MEMORY.md` and reads the first 200 lines at session start. But Auto Memory is **non-deterministic by design** — the docs say Claude "decides what's worth remembering." When I read my own MEMORY.md, half the entries are anecdotes the model thought were interesting; none of them tell the next session what branch I was on.

CLAUDE.md is the inverse — fully deterministic, but **static**. You write it by hand. It tells the agent who you are, not where you stopped.

What is missing is a contract that is both **deterministic** (a hook wrote it on a fixed event, not the model when it felt like it) and **stateful** (it captures the tactical state of your last session, not just your preferences).

That contract is what `repo-context-hooks` writes. Specifically:

- On `PreCompact`, it appends branch + last 3 commits + changed files to `specs/README.md`.
- On `SessionEnd`, it captures the same state plus an auto-commit snapshot.
- On `SessionStart` and `PostCompact`, the next agent reads that file before doing anything else.

It is in the repo. It is committed to git. Your teammate can read it. CI can read it. **The state belongs to you, not to `~/.claude/`.**

Thursday I'll walk through the 10 things that make this design different from CLAUDE.md, Auto Memory, claude-mem, and Context Mode (the closest direct competitor). If you've hit a worse compaction story than mine, drop it in the GitHub discussions — I want to add the strongest ones to the post.

Sources:
- [BSWEN: Why Claude Loses Context After Compaction](https://docs.bswen.com/blog/2026-02-09-claude-context-loss-compaction/) — the 20-30% retention measurement
- [Anthropic Auto Memory docs](https://code.claude.com/docs/en/memory) — "Claude decides what's worth remembering"
- [anthropics/claude-code#13112](https://github.com/anthropics/claude-code/issues/13112)
- [anthropics/claude-code#43733](https://github.com/anthropics/claude-code/issues/43733)

---

## LinkedIn draft

Quick technical post about a failure mode every Claude Code user has hit.

Auto-compaction isn't a summary. It's a lossy re-encoding. The original tokens are gone. What you get back is an LLM-generated narrative of what happened — and community measurements put the retention loss at 20-30% per event.

What you lose first, every time:
- Which branch you're on
- The last 3 commits you shipped this session
- The approach you just tried and rejected
- The working-tree diff

What survives:
- "We're refactoring auth"

That gap is the entire reason post-compact sessions feel like starting over. And it has been hit so many times that the GitHub issue is literally titled "auto compact is the worst" (anthropics/claude-code#13112 — closed Not Planned). Someone else opened anthropics/claude-code#43733 asking for a `PreCompact` hook the user could control.

The community shipped the hook themselves. Anthropic exposed the lifecycle events; people are writing handlers.

`repo-context-hooks` is one of those handlers. On `PreCompact`, it writes branch + last 3 commits + changed files into `specs/README.md` in your repo. Deterministic. Diff-able. Committed to git. The next session reads the file at `SessionStart` and resumes with real tactical state instead of a vibes summary.

Auto Memory and CLAUDE.md don't cover this gap. Auto Memory is non-deterministic by design. CLAUDE.md is deterministic but static. The contract you actually need is deterministic AND stateful — and it has to live in the repo, not in `~/.claude/`, so your team can review it.

Tomorrow's post (Thursday) is the 10-USP breakdown vs every competitor in the space.

Try it: `pip install repo-context-hooks`
Repo: https://github.com/narendranathe/repo-context-hooks

What's the worst compaction story you've hit? I'm collecting the strongest ones for the next post.

#ClaudeCode #AIEngineering #DeveloperTools #LLMOps #OpenSource #ContextEngineering #PromptEngineering
