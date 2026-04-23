# LinkedIn Launch Post

I have been working heavily with coding agents, and one problem kept showing up in real repos:

the agent can be smart, but the project context still gets fragile.

Claude Code made that pain especially visible because compaction and session boundaries happen right when the work gets serious. But reading the docs more closely changed how I thought about the problem. Claude Code already exposes useful primitives: session start hooks, compact boundaries, and repo-local workflows.

So I built something for my own workflow and packaged it for other developers:

`repo-context-hooks`

The idea is simple: stop treating context as chat memory and start treating it as repo infrastructure.

What it does:

- loads useful project context when a session starts
- checkpoints tactical state before compact
- restores continuity after compact
- keeps durable handoff context in repo files
- maps the same repo contract into different agent surfaces

Current support:

- Claude as the native lifecycle-hook path
- Cursor, Codex, Replit, Windsurf, Lovable, OpenClaw, Ollama, and Kimi as explicit partial integrations

The important part is the honesty. This is not a memory database. It is not a hosted knowledge graph. It does not pretend every agent has the same hooks.

It is a practical continuity layer for teams that want new agent sessions to re-enter from the repo instead of rediscovering the project every time.

If you are building with agents and want a cleaner handoff story, check it out:

https://github.com/narendranathe/repo-context-hooks
