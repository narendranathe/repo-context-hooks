# LinkedIn Launch Post

I’ve been spending a lot of time working with coding agents lately, and one problem kept showing up in real repos: context gets fragile fast.

Claude Code made that pain especially visible for me. But when I spent more time with the docs, it was also clear that the building blocks were already there: session lifecycle hooks, compact boundaries, startup hooks, and repo-local workflows.

So I built something for my own projects and packaged it into something other developers can use too:

`repo-context-hooks`

What it does:

- loads useful project context when a new session starts
- checkpoints tactical state before compact
- restores continuity after compact
- keeps the source of truth inside the repo

It is not a memory database or hosted platform. It is a practical repo workflow built around hooks, `README.md`, and `specs/README.md`.

I took inspiration from Claude Code's hook model and from several memory/plugin projects out there, but narrowed the problem to the thing I actually needed in daily work: repo context continuity.

If you’re building with agents and want a cleaner handoff story, check it out:

`https://github.com/narendranathe/repo-context-hooks`
