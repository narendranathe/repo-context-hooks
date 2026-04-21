# Repo Context Hooks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename `repohandoff` into `repo-context-hooks`, preserve legacy CLI aliases, publish a community-ready GitHub repo, and add launch assets that explain the product honestly and clearly.

**Architecture:** Keep the installer and bundle behavior stable while moving the Python package from `graphify` to `repo_context_hooks`. Add a primary `repo-context-hooks` CLI, keep `repohandoff` and `graphify` as compatibility aliases, then rewrite the README/docs/examples around repo-local context continuity instead of generic memory claims.

**Tech Stack:** Python 3.9+, setuptools, argparse, pytest, git, GitHub CLI

---

## File Map

### Modify

- `pyproject.toml`
  Purpose: rename the published package, switch console scripts to the new module, and update setuptools package discovery.
- `README.md`
  Purpose: turn the repo landing page into a public, community-shareable product page.
- `docs/competitive-analysis.md`
  Purpose: explain adjacent tools honestly and sharpen the differentiation.
- `docs/positioning.md`
  Purpose: define the one-line pitch, longer pitch, and category language for reuse.
- `tests/test_installer.py`
  Purpose: update imports and keep existing installer behavior locked during the rename.

### Create

- `repo_context_hooks/__init__.py`
  Purpose: package version export under the new module name.
- `repo_context_hooks/__main__.py`
  Purpose: module entry point for `python -m repo_context_hooks`.
- `repo_context_hooks/cli.py`
  Purpose: new public CLI implementation with `repo-context-hooks` as the primary help/program name.
- `repo_context_hooks/installer.py`
  Purpose: installer logic under the new module path.
- `tests/test_cli.py`
  Purpose: lock CLI naming and non-git repo behavior.
- `tests/test_bundle_integrity.py`
  Purpose: verify bundle assets remain complete after the module move.
- `docs/architecture.md`
  Purpose: explain hook flow, repo contract, and installation model.
- `examples/minimal-repo/README.md`
  Purpose: example user-facing README for a minimal repo using the package.
- `examples/minimal-repo/specs/README.md`
  Purpose: example engineering-memory file that shows the expected contract.
- `examples/multi-project/README.md`
  Purpose: example layout for teams managing several repos or workstreams.
- `docs/launch/linkedin.md`
  Purpose: launch-ready LinkedIn copy.
- `docs/launch/substack.md`
  Purpose: launch-ready Substack draft with the full builder story.

### Delete

- `graphify/__init__.py`
- `graphify/__main__.py`
- `graphify/cli.py`
- `graphify/installer.py`

The `graphify/bundle/` contents should move into `repo_context_hooks/bundle/` rather than being deleted.

## Task 1: Create An Isolated Implementation Worktree

**Files:**
- Modify: none
- Create: none
- Test: working tree sanity only

- [ ] **Step 1: Create the implementation worktree**

```bash
git worktree add ..\repo-context-hooks-impl -b feat/repo-context-hooks
```

- [ ] **Step 2: Switch into the worktree and verify the branch**

Run: `Set-Location ..\repo-context-hooks-impl; git branch --show-current`
Expected: `feat/repo-context-hooks`

- [ ] **Step 3: Run the baseline test suite before touching code**

Run: `python -m pytest -q --basetemp .pytest-tmp`
Expected: `3 passed`

- [ ] **Step 4: Verify the branch starts clean**

```bash
git status --short
```

Expected: no output

## Task 2: Rename The Python Module And Make `repo-context-hooks` The Primary CLI

**Files:**
- Modify: `pyproject.toml`
- Create: `repo_context_hooks/__init__.py`, `repo_context_hooks/__main__.py`, `repo_context_hooks/cli.py`, `repo_context_hooks/installer.py`
- Delete: `graphify/__init__.py`, `graphify/__main__.py`, `graphify/cli.py`, `graphify/installer.py`
- Test: `tests/test_installer.py`, `tests/test_cli.py`

- [ ] **Step 1: Write the failing CLI test for the new public module**

Create `tests/test_cli.py`:

```python
from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from repo_context_hooks.cli import _install, build_parser


def test_build_parser_uses_public_name() -> None:
    parser = build_parser()
    assert parser.prog == "repo-context-hooks"
    assert "repo context continuity" in parser.description.lower()


def test_install_skips_repo_hooks_outside_git_repo(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    def fake_install_skills(platform: str, force: bool = False, home=None):
        return tmp_path, {"context-handoff-hooks": "installed"}

    monkeypatch.setattr(
        "repo_context_hooks.cli.install_skills",
        fake_install_skills,
    )

    args = Namespace(
        platform="codex",
        force=False,
        skip_repo_hooks=False,
        repo_root=str(tmp_path),
    )

    assert _install(args) == 0
    out = capsys.readouterr().out
    assert "Installed platform skills to:" in out
    assert "Repo hooks skipped: target is not a git repository." in out
```

- [ ] **Step 2: Run the new test to confirm the rename has not been implemented yet**

Run: `python -m pytest tests/test_cli.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'repo_context_hooks'`

- [ ] **Step 3: Move the package directory to the new module name**

```bash
git mv graphify repo_context_hooks
```

- [ ] **Step 4: Replace package metadata and entry points**

Update `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "repo-context-hooks"
version = "0.1.0"
description = "Hook-based repo context continuity for coding agents."
readme = "README.md"
requires-python = ">=3.9"
license = { text = "MIT" }
authors = [{ name = "Narendranath Edara" }]
dependencies = []

[project.scripts]
repo-context-hooks = "repo_context_hooks.cli:main"
repohandoff = "repo_context_hooks.cli:main"
graphify = "repo_context_hooks.cli:main"

[tool.setuptools]
include-package-data = true

[tool.setuptools.packages.find]
where = ["."]
include = ["repo_context_hooks*"]

[tool.setuptools.package-data]
repo_context_hooks = ["bundle/**/*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 5: Replace the CLI module with the new public wording**

Update `repo_context_hooks/cli.py`:

```python
from __future__ import annotations

import argparse
from pathlib import Path

from .installer import PLATFORMS, install_repo_hooks, install_skills


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-context-hooks",
        description="Install repo context continuity skills and lifecycle hooks.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    install = subparsers.add_parser(
        "install",
        help="Install skills for a platform and optionally configure repo hooks.",
    )
    install.add_argument(
        "--platform",
        required=True,
        choices=PLATFORMS,
        help="Target platform for skill installation.",
    )
    install.add_argument(
        "--repo-root",
        default=".",
        help="Repository root for hook setup (default: current directory).",
    )
    install.add_argument(
        "--skip-repo-hooks",
        action="store_true",
        help="Install platform skills only.",
    )
    install.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing installed skills.",
    )
    return parser


def _install(args: argparse.Namespace) -> int:
    target, statuses = install_skills(platform=args.platform, force=args.force)
    print(f"Installed platform skills to: {target}")
    for skill, state in statuses.items():
        print(f"- {skill}: {state}")

    if args.skip_repo_hooks:
        print("Skipped repo hook installation (--skip-repo-hooks).")
        return 0

    repo_root = Path(args.repo_root).resolve()
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        print(
            "Repo hooks skipped: target is not a git repository. "
            "Use --repo-root on a repo or omit --skip-repo-hooks in a repo directory."
        )
        return 0

    installed = install_repo_hooks(repo_root)
    print("Installed repo hooks:")
    for name, path in installed.items():
        print(f"- {name}: {path}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "install":
        return _install(args)
    parser.error("Unknown command")
    return 2
```

- [ ] **Step 6: Restore package boilerplate and keep installer behavior unchanged**

Update `repo_context_hooks/__init__.py`:

```python
__all__ = ["__version__"]

__version__ = "0.1.0"
```

Update `repo_context_hooks/__main__.py`:

```python
from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
```

Keep `repo_context_hooks/installer.py` byte-for-byte identical to the moved `graphify/installer.py` so this task only changes naming, not installer behavior.

- [ ] **Step 7: Update the installer test imports**

Update `tests/test_installer.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from repo_context_hooks.installer import (
    install_repo_hooks,
    install_skills,
    platform_skill_dir,
)


def test_platform_skill_dir() -> None:
    home = Path("/tmp/demo-home")
    assert platform_skill_dir("codex", home=home) == home / ".codex" / "skills"
    assert platform_skill_dir("claude", home=home) == home / ".claude" / "skills"


def test_install_skills_idempotent(tmp_path: Path) -> None:
    target, first = install_skills("codex", home=tmp_path, force=False)
    assert target.exists()
    assert first
    assert all(state == "installed" for state in first.values())

    _, second = install_skills("codex", home=tmp_path, force=False)
    assert all(state == "skipped" for state in second.values())

    _, third = install_skills("codex", home=tmp_path, force=True)
    assert all(state == "installed" for state in third.values())


def test_install_repo_hooks_merges_existing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    settings_path = repo / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps(
            {
                "permissions": {"allow": ["Bash(git:*)"]},
                "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": []}]},
            }
        ),
        encoding="utf-8",
    )

    installed = install_repo_hooks(repo)
    assert "repo_specs_memory.py" in installed
    assert "session_context.py" in installed

    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "hooks" in settings
    assert "PreToolUse" in settings["hooks"]
    assert "SessionStart" in settings["hooks"]
    assert (repo / ".claude" / "scripts" / "repo_specs_memory.py").exists()
    assert (repo / ".claude" / "scripts" / "session_context.py").exists()
```

- [ ] **Step 8: Run the targeted tests to verify the rename**

Run: `python -m pytest tests/test_cli.py tests/test_installer.py -q --basetemp .pytest-tmp`
Expected: `5 passed`

- [ ] **Step 9: Commit the package rename**

```bash
git add pyproject.toml repo_context_hooks tests/test_cli.py tests/test_installer.py
git commit -m "refactor: rename package to repo-context-hooks"
```

## Task 3: Protect Bundle And CLI Behavior With Focused Tests

**Files:**
- Modify: none
- Create: `tests/test_bundle_integrity.py`
- Test: `tests/test_bundle_integrity.py`, `tests/test_cli.py`

- [ ] **Step 1: Add a bundle integrity test**

Create `tests/test_bundle_integrity.py`:

```python
from __future__ import annotations

from repo_context_hooks.installer import bundle_root


def test_bundle_contains_expected_assets() -> None:
    root = bundle_root()
    assert (root / "hooks.json").exists()
    assert (root / "scripts" / "repo_specs_memory.py").exists()
    assert (root / "scripts" / "session_context.py").exists()

    skills = root / "skills"
    assert (skills / "context-handoff-hooks" / "SKILL.md").exists()
    assert (skills / "session-start-context-loader" / "SKILL.md").exists()
    assert (skills / "precompact-checkpoint" / "SKILL.md").exists()
    assert (skills / "postcompact-context-reload" / "SKILL.md").exists()
```

- [ ] **Step 2: Add a CLI skip-path test for `--skip-repo-hooks`**

Append to `tests/test_cli.py`:

```python
def test_install_respects_skip_repo_hooks(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    def fake_install_skills(platform: str, force: bool = False, home=None):
        return tmp_path, {"context-handoff-hooks": "installed"}

    monkeypatch.setattr(
        "repo_context_hooks.cli.install_skills",
        fake_install_skills,
    )

    args = Namespace(
        platform="claude",
        force=False,
        skip_repo_hooks=True,
        repo_root=str(tmp_path),
    )

    assert _install(args) == 0
    out = capsys.readouterr().out
    assert "Skipped repo hook installation" in out
```

- [ ] **Step 3: Run the focused behavior tests**

Run: `python -m pytest tests/test_cli.py tests/test_bundle_integrity.py -q --basetemp .pytest-tmp`
Expected: `4 passed`

- [ ] **Step 4: Commit the protective tests**

```bash
git add tests/test_cli.py tests/test_bundle_integrity.py
git commit -m "test: protect cli and bundle behavior"
```

## Task 4: Rewrite The Public README And Core Product Docs

**Files:**
- Modify: `README.md`, `docs/positioning.md`, `docs/competitive-analysis.md`
- Create: none
- Test: copy validation via `rg`

- [ ] **Step 1: Replace the README with a community-facing landing page**

Update `README.md`:

```markdown
# repo-context-hooks

Hook-based repo context continuity for coding agents.

`repo-context-hooks` preserves repository context across session start, compaction, and handoff using repo-local hooks, specs memory, and installable skills.

It is built for teams and solo developers who want agents to continue work from the repo's actual state instead of relying on fragile chat memory.

## Why This Exists

Agent sessions usually fail in predictable ways:

- a new session re-discovers the repo from scratch
- auto-compact drops tactical decisions
- next-work context goes stale
- issue context disappears between sessions

Claude Code's hooks model points to the right primitives. This package turns that pattern into a reusable, repo-local workflow.

## What This Is

- lifecycle hooks for session start, compact, and session end
- a dual-document contract: `README.md` for users, `specs/README.md` for engineering memory
- bundled skills for loading context and checkpointing work
- zero external database or hosted service requirement

## What This Is Not

- not a vector memory layer
- not a hosted memory service
- not a knowledge graph database
- not Claude-only, even if Claude Code inspired the first version

## Install

```bash
python -m pip install -e .
repo-context-hooks install --platform codex
```

Compatibility aliases:

```bash
repohandoff install --platform codex
graphify install --platform codex
```

## What `install` Does

1. Installs bundled skills into the target agent home directory
2. Copies helper scripts into `.claude/scripts`
3. Merges lifecycle hook entries into `.claude/settings.json`
4. Bootstraps `specs/README.md` continuity for the current repo

## Repo Contract

- `README.md`: user-facing project explanation and contribution guide
- `specs/README.md`: engineering memory, decisions, constraints, failures, and next work

## Who This Helps

- developers using Claude Code or Codex in long-running repos
- teams onboarding new agents into partially complete projects
- engineers who want deterministic continuity without extra infrastructure

## Development

```bash
python -m pytest -q --basetemp .pytest-tmp
```

## License

MIT
```

- [ ] **Step 2: Rewrite the positioning doc around the new public language**

Update `docs/positioning.md`:

```markdown
# repo-context-hooks Positioning

## One-Line Pitch

Hook-based repo context continuity for coding agents.

## Problem

Agent sessions degrade at the edges:

- startup lacks project state
- compaction drops tactical context
- handoffs lose next-work clarity

## Thesis

Repository context should be durable, reviewable, and operational.

## Product Claim

`repo-context-hooks` turns repo context into infrastructure using hooks, repo docs, and deterministic checkpoints.

## Core Value

- lifecycle hooks at the right moments
- repo-local engineering memory
- startup context loading
- no external memory backend

## Messaging Guardrails

- Do say: "repo-local continuity"
- Do say: "hook-based context handoff"
- Do not say: "solves AI memory"
- Do not say: "knowledge graph platform"
```

- [ ] **Step 3: Rewrite the competitive analysis with an honest comparison**

Update `docs/competitive-analysis.md`:

```markdown
# Competitive Analysis

## Adjacent Projects

### `thedotmack/claude-mem`

- Focus: session capture, compression, and retrieval
- Difference: stronger on memory archive behavior than repo-operating workflow

### `mem0ai/mem0` and OpenMemory

- Focus: long-term memory infrastructure
- Difference: stronger on cross-session memory systems than repo-local hook workflows

### Claude Code Hooks

- Focus: lifecycle primitives provided by the platform
- Difference: capability only, not a packaged workflow

## Honest Take

This project is not novel because hooks exist or because memory tools exist.

Its value is packaging the workflow many teams actually need:

- load project state on session start
- checkpoint tactical context before compact
- restore continuity after compact
- keep the source of truth in the repo

## Positioning Rule

Describe `repo-context-hooks` as a deterministic repo workflow, not as a universal memory solution.
```

- [ ] **Step 4: Validate the copy no longer leads with the old product name**

Run: `rg -n "RepoHandoff|^# RepoHandoff" README.md docs/positioning.md docs/competitive-analysis.md`
Expected: no matches

- [ ] **Step 5: Commit the docs rewrite**

```bash
git add README.md docs/positioning.md docs/competitive-analysis.md
git commit -m "docs: rewrite public positioning for repo-context-hooks"
```

## Task 5: Add Architecture Docs And Real Example Layouts

**Files:**
- Create: `docs/architecture.md`, `examples/minimal-repo/README.md`, `examples/minimal-repo/specs/README.md`, `examples/multi-project/README.md`
- Modify: none
- Test: content validation via `rg`

- [ ] **Step 1: Add an architecture explainer**

Create `docs/architecture.md`:

```markdown
# Architecture

## Core Flow

1. `SessionStart` loads project memory and next-work context
2. `PreCompact` checkpoints the latest tactical state into `specs/README.md`
3. `PostCompact` reloads the condensed project context
4. `SessionEnd` captures a final continuity note

## Source Of Truth

The repo owns the context:

- user-facing intent lives in `README.md`
- engineering memory lives in `specs/README.md`
- hook automation keeps those files current enough for the next agent

## Why This Works

The system avoids hidden state. A new agent can inspect the repo and understand:

- what the product is
- what constraints matter
- what changed recently
- what should happen next
```

- [ ] **Step 2: Add a minimal example repo contract**

Create `examples/minimal-repo/README.md`:

```markdown
# Example Project

This is a user-facing README.

## What It Does

This example project shows the smallest useful repo shape for `repo-context-hooks`.

## Contributing

- read `specs/README.md` before making architectural changes
- update this README when the user-facing behavior changes
```

Create `examples/minimal-repo/specs/README.md`:

```markdown
# Engineering Memory

## Constraints

- keep the project simple
- prefer repo-local automation

## Decisions

- use hooks to load and checkpoint context
- keep tactical continuity in markdown instead of hidden state

## Current State

- starter example is complete

## Next Work

- add issue sync if the team wants startup triage
```

- [ ] **Step 3: Add a multi-project example**

Create `examples/multi-project/README.md`:

```markdown
# Multi-Project Example

Use this layout when one developer or team maintains several agent-enabled repos.

## Pattern

- each repo keeps its own `README.md`
- each repo keeps its own `specs/README.md`
- a shared portfolio or wiki can index the repos, but operational context stays local

## Why

This keeps handoff quality high and prevents one giant memory file from becoming the bottleneck.
```

- [ ] **Step 4: Validate the example contract is present**

Run: `rg -n "Engineering Memory|What It Does|Multi-Project Example" docs examples`
Expected: one or more matches in the newly created files

- [ ] **Step 5: Commit the architecture and examples**

```bash
git add docs/architecture.md examples
git commit -m "docs: add architecture and example repo contracts"
```

## Task 6: Add Launch Assets For LinkedIn And Substack

**Files:**
- Create: `docs/launch/linkedin.md`, `docs/launch/substack.md`
- Modify: none
- Test: copy validation via `rg`

- [ ] **Step 1: Write the LinkedIn launch post**

Create `docs/launch/linkedin.md`:

```markdown
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
```

- [ ] **Step 2: Write the Substack launch draft**

Create `docs/launch/substack.md`:

```markdown
# Repo Context Hooks: Turning Repo Context Into Infrastructure

I have been spending a lot of time with coding agents recently, and one failure mode kept repeating: the more real the project became, the more fragile the agent's working context felt.

Claude Code made that especially obvious for me. It is easy to say "the model forgot," but that framing is incomplete. When I went back to the documentation, the more interesting takeaway was that the product already hinted at a better pattern. Claude Code exposes lifecycle hooks around session start, compaction, and session end. That means the right question is not "how do I make the model remember everything?" It is "how do I make project continuity deterministic?"

That shift led me to build `repo-context-hooks`.

It is not a memory database. It is not a hosted knowledge layer. It is not an attempt to solve agent memory in the abstract.

It is a smaller and more useful thing:

- load repo context at session start
- checkpoint tactical state before compact
- restore working continuity after compact
- keep the durable state inside the repository

The project also reflects something I think we will need more of in the broader agent ecosystem: tools that operationalize workflow patterns instead of promising magical memory.

I took inspiration from Claude Code's documentation and from adjacent projects in the memory/plugin space, but I wanted something more honest and more operational. The result is a package that treats context as repo infrastructure: hooks, docs, and clear handoff points.

If you want to try it or adapt the workflow for your own repos, the project is here:

`https://github.com/narendranathe/repo-context-hooks`
```

- [ ] **Step 3: Validate the launch copy includes the origin story and the repo URL**

Run: `rg -n "Claude Code|repo-context-hooks|github.com/narendranathe/repo-context-hooks" docs/launch`
Expected: matches in both launch files

- [ ] **Step 4: Commit the launch assets**

```bash
git add docs/launch
git commit -m "docs: add launch posts for repo-context-hooks"
```

## Task 7: Validate The Renamed Package End-To-End And Publish It

**Files:**
- Modify: git metadata and remote configuration only
- Create: none
- Test: full suite plus installed CLI smoke tests

- [ ] **Step 1: Run the full test suite**

Run: `python -m pytest -q --basetemp .pytest-tmp`
Expected: all tests pass

- [ ] **Step 2: Install the package in editable mode**

Run: `python -m pip install -e .`
Expected: pip reports `Successfully installed repo-context-hooks-0.1.0` or `Successfully installed repo-context-hooks`

- [ ] **Step 3: Smoke-test the primary and compatibility CLIs**

Run: `repo-context-hooks --help`
Expected: help text starts with `usage: repo-context-hooks`

Run: `repohandoff --help`
Expected: help text starts with `usage: repo-context-hooks`

Run: `graphify --help`
Expected: help text starts with `usage: repo-context-hooks`

- [ ] **Step 4: Rename or create the GitHub repository**

If the current remote is still `narendranathe/repohandoff`, run:

```bash
gh api -X PATCH repos/narendranathe/repohandoff -f name='repo-context-hooks'
git remote set-url origin https://github.com/narendranathe/repo-context-hooks.git
```

If the repo was never published, run instead:

```bash
gh repo create narendranathe/repo-context-hooks --public --source . --remote origin --push
```

- [ ] **Step 5: Verify the worktree is clean before publish**

Run: `git status --short`
Expected: no output

- [ ] **Step 6: Push the implementation branch**

Run: `git push -u origin feat/repo-context-hooks`
Expected: branch pushed successfully

- [ ] **Step 7: Open the pull request**

Run: `gh pr create --fill --base main --head feat/repo-context-hooks`
Expected: GitHub CLI prints the PR URL

- [ ] **Step 8: Merge the pull request once checks pass**

Run: `gh pr merge --squash --delete-branch --auto`
Expected: GitHub CLI confirms auto-merge or immediate merge

## Self-Review

### Spec Coverage

- rename and public identity: Task 2
- compatibility aliases: Task 2 and Task 7
- public GitHub-ready README/docs: Task 4 and Task 5
- honest differentiation and self-critique: Task 4
- launch assets: Task 6
- clean publish flow: Task 7

### Placeholder Scan

- no `TODO`
- no `TBD`
- all file paths are explicit
- all code-bearing steps include code blocks

### Type Consistency

- package/module name is consistently `repo_context_hooks`
- public CLI name is consistently `repo-context-hooks`
- compatibility aliases remain `repohandoff` and `graphify`
