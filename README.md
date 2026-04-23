# repo-context-hooks

Repo-native continuity for coding agents.

`repo-context-hooks` keeps interrupted work, next-step context, and handoff notes in the repository instead of leaving them trapped in chat history. The goal is simple: a new session should be able to reopen the repo, understand the work in progress, and continue without rediscovering everything from scratch.

```bash
python -m pip install -e .
repo-context-hooks install --platform claude
repo-context-hooks install --platform codex
```

Phase 1 is intentionally narrow: Claude is the native path, while Cursor and Codex are useful but partial integrations.

## Why Repo-Native Continuity

Coding sessions rarely fail because the model forgot a fact. They fail because the useful state of the work never made it back into the repo.

When that happens, the next session has to reconstruct:

- what changed
- what was interrupted
- what tradeoffs were already decided
- what should happen next

`repo-context-hooks` narrows that problem to a repo contract teams can inspect in git. Product intent stays public in `README.md`. Engineering continuity stays in `specs/README.md`. The agent workflow becomes easier to review, critique, and resume.

## How It Works

The continuity loop is repo-first:

1. start from checked-in project context
2. capture useful tactical state before an interruption or compact event
3. reload from repo state instead of relying on fragile session memory
4. leave the next session a cleaner handoff than the one you inherited

The mechanism depends on platform surfaces that vary by agent. Claude can automate more of the loop. Cursor and Codex still benefit from the same repo contract, but through narrower continuity surfaces.

![Lifecycle flow diagram showing an interrupted bugfix, a checkpoint written to specs/README.md, and the next session resuming from repo state](assets/diagrams/lifecycle-flow.svg)

## Tested In Phase 1

The public support story in this phase is intentionally narrow and explicit. These are the platforms tested in Phase 1:

- Claude (`native`): strongest support for repo hooks, session transitions, and continuity checkpoints.
- Cursor (`partial`): supports the repo contract and instruction surfaces, but not full Claude-style lifecycle parity.
- Codex (`partial`): supports repo-native continuity through checked-in repo docs and `AGENTS.md`, but not native lifecycle hooks.

## Platform Support

The support tiers are `native`, `partial`, and `planned`.

See [docs/platforms.md](docs/platforms.md) for the support matrix, platform-specific caveats, and the current claim boundary. The short version is that we do not claim universal agent support, and we do not claim hook parity for Cursor or Codex.

## Concrete Stories

The visuals in this repo are about specific interrupted-work situations, not abstract architecture theater.

### Interrupted Task Recovery

A compact event lands in the middle of a bugfix. The useful checkpoint is written back into the repo so the next session can resume with context instead of re-explaining the problem.

![Repo contract diagram showing the open PR story in README.md, handoff notes in specs/README.md, and a Cursor or Codex session re-entering with repo context](assets/diagrams/repo-contract.svg)

### Before And After Handoffs

Without a checked-in continuity contract, teams repeat themselves. With one, the next session can reopen the repo and keep moving.

![Before and after continuity comparison showing repeated bug explanation versus resuming from checked-in continuity](assets/diagrams/before-after-continuity.svg)

## See Also

- [Platform support](docs/platforms.md)
- [Architecture](docs/architecture.md)
- [Competitive analysis](docs/competitive-analysis.md)
- [Planned platform roadmap](docs/launch/platform-roadmap.md)
- [Animation plan](docs/demo/animation-plan.md)
- [Minimal repo example](examples/minimal-repo/)
- [Multi-project example](examples/multi-project/)

## Development

```bash
python -m pip install -e .
python -m pytest -q --basetemp .pytest-tmp-readme-full
```

Pull requests are welcome when they make the repo contract clearer, more durable, or easier to adopt without widening the product claims beyond what the implementation supports.

## License

MIT
