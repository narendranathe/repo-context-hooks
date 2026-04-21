# Repo Context Hooks README Visual Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the public README, add static SVG explainer diagrams, and add an animation-support doc so `repo-context-hooks` reads like a credible technical product instead of a thin package landing page.

**Architecture:** Treat the README as a tested public interface. Add a README contract test first, then implement the new section order and technical-detail language, then add SVG assets and embed them inline, and finally add an animation-support doc linked from the README. Keep the visual layer static-SVG-first and GitHub-safe.

**Tech Stack:** Markdown, SVG, Python 3.9+, pytest, git

---

## File Map

### Modify

- `README.md`
  Purpose: rewrite the GitHub landing page around the approved section order, technical detail, critique, and inline SVG embeds.

### Create

- `tests/test_readme_contract.py`
  Purpose: verify the README contains the required sections, commands, technical details, critique, links, and visual references.
- `assets/diagrams/lifecycle-flow.svg`
  Purpose: explain the hook lifecycle visually.
- `assets/diagrams/repo-contract.svg`
  Purpose: explain the repo contract between `README.md`, `specs/README.md`, and the hooks/skills layer.
- `assets/diagrams/before-after-continuity.svg`
  Purpose: explain the before/after operational difference this tool creates.
- `docs/demo/animation-plan.md`
  Purpose: describe how optional social/demo animations should be derived from the SVG source assets without making the README depend on animation.

### Leave Untouched

- `UBIQUITOUS_LANGUAGE.md`
- `specs/`

These are user-owned untracked files already present in the worktree and must not be staged or edited as part of this plan.

## Notes Before Starting

- Use fresh pytest temp directories such as `.pytest-tmp-readme-contract`, `.pytest-tmp-readme-visuals`, and `.pytest-tmp-readme-full`. The worktree already has older temp directories with access restrictions on Windows.
- When checking git cleanliness during execution, prefer `git status --short --untracked-files=no` so user-owned untracked files do not block progress.

## Task 1: Lock The README Contract With A Failing Test

**Files:**
- Create: `tests/test_readme_contract.py`
- Modify: `README.md`
- Test: `tests/test_readme_contract.py`

- [ ] **Step 1: Write the failing README contract test**

Create `tests/test_readme_contract.py`:

```python
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def readme_text() -> str:
    return README.read_text(encoding="utf-8")


def test_readme_has_required_sections() -> None:
    text = readme_text()
    expected_sections = [
        "# repo-context-hooks",
        "## Why This Exists",
        "## How It Works",
        "## Repo Contract",
        "## Before / After",
        "## What `install` Actually Does",
        "## Technical Details",
        "## Honest Critique",
        "## Examples",
        "## Development",
        "## License",
    ]
    for section in expected_sections:
        assert section in text, f"missing section: {section}"


def test_readme_includes_install_and_alias_commands() -> None:
    text = readme_text()
    expected_snippets = [
        "python -m pip install -e .",
        "repo-context-hooks install --platform codex",
        "repohandoff install --platform codex",
        "graphify install --platform codex",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing command snippet: {snippet}"


def test_readme_surfaces_install_side_effects() -> None:
    text = readme_text()
    expected_snippets = [
        "~/.codex/skills",
        "~/.claude/skills",
        ".claude/scripts/repo_specs_memory.py",
        ".claude/scripts/session_context.py",
        ".claude/settings.json",
        "specs/README.md",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing install detail: {snippet}"


def test_readme_contains_honest_critique() -> None:
    text = readme_text()
    expected_snippets = [
        "not a vector memory layer",
        "not a hosted memory service",
        "does not replace repo discipline",
        "cross-repo semantic memory",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing critique snippet: {snippet}"


def test_readme_links_to_supporting_docs() -> None:
    text = readme_text()
    expected_links = [
        "docs/architecture.md",
        "examples/minimal-repo/",
        "examples/multi-project/",
    ]
    for link in expected_links:
        assert link in text, f"missing supporting link: {link}"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_readme_contract.py -q --basetemp .pytest-tmp-readme-contract`
Expected: FAIL because the current README is missing the new section headings and specific install-detail snippets.

- [ ] **Step 3: Rewrite `README.md` to satisfy the public contract**

Replace `README.md` with:

````markdown
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

## How It Works

`repo-context-hooks` treats repository context as an operational contract instead of a prompt artifact.

At session start, the hooks load project memory and current priorities. Before compaction, the hooks checkpoint tactical state into the repo. After compaction, the condensed context is reloaded so the next turn has continuity instead of drift. At session end, the repo gets one more continuity note for the next agent or session.

## Repo Contract

The repo stays the source of truth:

- `README.md` explains the project to users and contributors
- `specs/README.md` carries engineering memory, constraints, decisions, failures, and next work
- hooks and skills keep those layers synchronized enough to survive handoffs

## Before / After

Before this workflow, new agent sessions often re-discover the repo, repeat old decisions, and lose the next useful action after compaction.

After this workflow, sessions start with more structure, compaction preserves tactical state, and handoffs become more deterministic.

## What `install` Actually Does

1. Installs bundled skills into:
   - `~/.codex/skills`
   - `~/.claude/skills`
2. Copies helper scripts into:
   - `.claude/scripts/repo_specs_memory.py`
   - `.claude/scripts/session_context.py`
3. Merges lifecycle hook entries into:
   - `.claude/settings.json`
4. Assumes the repo maintains:
   - `README.md`
   - `specs/README.md`

## Technical Details

- Primary CLI: `repo-context-hooks`
- Compatibility aliases: `repohandoff`, `graphify`
- Supported agent targets today: Codex and Claude
- Expected repo contract: `README.md` plus `specs/README.md`
- Architecture notes: [docs/architecture.md](docs/architecture.md)
- Minimal example: [examples/minimal-repo/](examples/minimal-repo/)
- Multi-project example: [examples/multi-project/](examples/multi-project/)

## Honest Critique

- This is not a vector memory layer.
- This is not a hosted memory service.
- This does not replace repo discipline.
- Poor `specs/README.md` hygiene reduces the value quickly.
- Teams that need cross-repo semantic memory may still want another tool alongside this one.

## Examples

- [Minimal repo example](examples/minimal-repo/)
- [Multi-project example](examples/multi-project/)
- [Architecture notes](docs/architecture.md)

## Development

```bash
python -m pip install -e .
python -m pytest -q --basetemp .pytest-tmp-readme-full
```

Pull requests are welcome when they improve reliability, clarity, or the repo contract without turning the project into a vague memory platform.

## License

MIT
````

- [ ] **Step 4: Run the test again to verify it passes**

Run: `python -m pytest tests/test_readme_contract.py -q --basetemp .pytest-tmp-readme-contract`
Expected: PASS

- [ ] **Step 5: Commit the README contract pass**

```bash
git add README.md tests/test_readme_contract.py
git commit -m "docs: strengthen README contract"
```

## Task 2: Add SVG Explainer Assets And Inline Them Into The README

**Files:**
- Create: `assets/diagrams/lifecycle-flow.svg`, `assets/diagrams/repo-contract.svg`, `assets/diagrams/before-after-continuity.svg`
- Modify: `README.md`, `tests/test_readme_contract.py`
- Test: `tests/test_readme_contract.py`

- [ ] **Step 1: Extend the README contract test to require inline diagram embeds**

Append to `tests/test_readme_contract.py`:

```python
def test_readme_embeds_required_diagrams() -> None:
    text = readme_text()
    expected_assets = [
        "assets/diagrams/lifecycle-flow.svg",
        "assets/diagrams/repo-contract.svg",
        "assets/diagrams/before-after-continuity.svg",
    ]
    for asset in expected_assets:
        assert asset in text, f"missing diagram embed: {asset}"
        assert (ROOT / asset).exists(), f"missing diagram file: {asset}"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_readme_contract.py -q --basetemp .pytest-tmp-readme-visuals`
Expected: FAIL because the SVG files do not exist yet and the README does not embed them.

- [ ] **Step 3: Create `assets/diagrams/lifecycle-flow.svg`**

Create `assets/diagrams/lifecycle-flow.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 240" role="img" aria-labelledby="title desc">
  <title id="title">repo-context-hooks lifecycle flow</title>
  <desc id="desc">SessionStart, PreCompact, PostCompact, and SessionEnd shown as a left-to-right continuity lifecycle.</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#334155" />
    </marker>
    <style>
      .label { font: 700 18px Arial, sans-serif; fill: #0f172a; }
      .caption { font: 13px Arial, sans-serif; fill: #475569; }
    </style>
  </defs>

  <rect width="920" height="240" rx="24" fill="#f8fafc" />

  <rect x="40" y="72" width="180" height="68" rx="16" fill="#e0f2fe" stroke="#0284c7" stroke-width="2" />
  <rect x="260" y="72" width="180" height="68" rx="16" fill="#fef3c7" stroke="#d97706" stroke-width="2" />
  <rect x="480" y="72" width="180" height="68" rx="16" fill="#ede9fe" stroke="#7c3aed" stroke-width="2" />
  <rect x="700" y="72" width="180" height="68" rx="16" fill="#dcfce7" stroke="#16a34a" stroke-width="2" />

  <text class="label" x="130" y="112" text-anchor="middle">SessionStart</text>
  <text class="label" x="350" y="112" text-anchor="middle">PreCompact</text>
  <text class="label" x="570" y="112" text-anchor="middle">PostCompact</text>
  <text class="label" x="790" y="112" text-anchor="middle">SessionEnd</text>

  <path d="M220 106 H260" fill="none" stroke="#334155" stroke-width="3" marker-end="url(#arrow)" />
  <path d="M440 106 H480" fill="none" stroke="#334155" stroke-width="3" marker-end="url(#arrow)" />
  <path d="M660 106 H700" fill="none" stroke="#334155" stroke-width="3" marker-end="url(#arrow)" />

  <text class="caption" x="130" y="176" text-anchor="middle">load repo state</text>
  <text class="caption" x="350" y="176" text-anchor="middle">checkpoint tactical work</text>
  <text class="caption" x="570" y="176" text-anchor="middle">reload condensed context</text>
  <text class="caption" x="790" y="176" text-anchor="middle">capture final handoff</text>
</svg>
```

- [ ] **Step 4: Create `assets/diagrams/repo-contract.svg`**

Create `assets/diagrams/repo-contract.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 280" role="img" aria-labelledby="title desc">
  <title id="title">repo-context-hooks repo contract</title>
  <desc id="desc">README.md and specs/README.md are connected to hooks and skills that keep continuity operational.</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#334155" />
    </marker>
    <style>
      .title { font: 700 18px Arial, sans-serif; fill: #0f172a; }
      .body { font: 13px Arial, sans-serif; fill: #475569; }
    </style>
  </defs>

  <rect width="920" height="280" rx="24" fill="#f8fafc" />

  <rect x="60" y="52" width="250" height="74" rx="16" fill="#ffffff" stroke="#334155" stroke-width="2" />
  <rect x="60" y="156" width="250" height="74" rx="16" fill="#fff7ed" stroke="#c2410c" stroke-width="2" />
  <rect x="560" y="104" width="280" height="74" rx="16" fill="#eff6ff" stroke="#2563eb" stroke-width="2" />

  <text class="title" x="185" y="92" text-anchor="middle">README.md</text>
  <text class="body" x="185" y="112" text-anchor="middle">user-facing project intent</text>

  <text class="title" x="185" y="196" text-anchor="middle">specs/README.md</text>
  <text class="body" x="185" y="216" text-anchor="middle">engineering memory and next work</text>

  <text class="title" x="700" y="142" text-anchor="middle">Hooks + Skills</text>
  <text class="body" x="700" y="162" text-anchor="middle">sync and reload continuity</text>

  <path d="M310 92 C420 92, 450 110, 560 128" fill="none" stroke="#334155" stroke-width="3" marker-end="url(#arrow)" />
  <path d="M310 194 C420 194, 450 176, 560 154" fill="none" stroke="#334155" stroke-width="3" marker-end="url(#arrow)" />
</svg>
```

- [ ] **Step 5: Create `assets/diagrams/before-after-continuity.svg`**

Create `assets/diagrams/before-after-continuity.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 260" role="img" aria-labelledby="title desc">
  <title id="title">repo-context-hooks before and after continuity</title>
  <desc id="desc">A comparison between context drift before the tool and deterministic handoff after the tool.</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#334155" />
    </marker>
    <style>
      .heading { font: 700 20px Arial, sans-serif; }
      .item { font: 14px Arial, sans-serif; }
    </style>
  </defs>

  <rect width="920" height="260" rx="24" fill="#f8fafc" />

  <rect x="36" y="34" width="360" height="192" rx="18" fill="#fef2f2" stroke="#dc2626" stroke-width="2" />
  <rect x="524" y="34" width="360" height="192" rx="18" fill="#f0fdf4" stroke="#16a34a" stroke-width="2" />

  <text class="heading" x="216" y="72" text-anchor="middle" fill="#7f1d1d">Before</text>
  <text class="heading" x="704" y="72" text-anchor="middle" fill="#14532d">After</text>

  <text class="item" x="216" y="112" text-anchor="middle" fill="#7f1d1d">re-discovery on every session</text>
  <text class="item" x="216" y="142" text-anchor="middle" fill="#7f1d1d">lost next-work context</text>
  <text class="item" x="216" y="172" text-anchor="middle" fill="#7f1d1d">compaction drift</text>

  <text class="item" x="704" y="112" text-anchor="middle" fill="#14532d">startup context loaded</text>
  <text class="item" x="704" y="142" text-anchor="middle" fill="#14532d">tactical checkpoints preserved</text>
  <text class="item" x="704" y="172" text-anchor="middle" fill="#14532d">deterministic handoff</text>

  <path d="M396 130 H524" fill="none" stroke="#334155" stroke-width="4" marker-end="url(#arrow)" />
</svg>
```

- [ ] **Step 6: Update `README.md` to embed the diagrams inline**

Update `README.md` by replacing the `How It Works`, `Repo Contract`, and `Before / After` sections with:

```markdown
## How It Works

`repo-context-hooks` treats repository context as an operational contract instead of a prompt artifact.

At session start, the hooks load project memory and current priorities. Before compaction, the hooks checkpoint tactical state into the repo. After compaction, the condensed context is reloaded so the next turn has continuity instead of drift. At session end, the repo gets one more continuity note for the next agent or session.

![Lifecycle flow diagram showing SessionStart, PreCompact, PostCompact, and SessionEnd](assets/diagrams/lifecycle-flow.svg)

## Repo Contract

The repo stays the source of truth:

- `README.md` explains the project to users and contributors
- `specs/README.md` carries engineering memory, constraints, decisions, failures, and next work
- hooks and skills keep those layers synchronized enough to survive handoffs

![Repo contract diagram showing README.md, specs/README.md, and hooks plus skills](assets/diagrams/repo-contract.svg)

## Before / After

Before this workflow, new agent sessions often re-discover the repo, repeat old decisions, and lose the next useful action after compaction.

After this workflow, sessions start with more structure, compaction preserves tactical state, and handoffs become more deterministic.

![Before and after continuity comparison showing context drift versus deterministic handoff](assets/diagrams/before-after-continuity.svg)
```

- [ ] **Step 7: Run the test again to verify it passes**

Run: `python -m pytest tests/test_readme_contract.py -q --basetemp .pytest-tmp-readme-visuals`
Expected: PASS

- [ ] **Step 8: Commit the visual asset pass**

```bash
git add README.md assets/diagrams tests/test_readme_contract.py
git commit -m "docs: add README explainer diagrams"
```

## Task 3: Add Animation Support Documentation Without Making README Depend On Motion

**Files:**
- Create: `docs/demo/animation-plan.md`
- Modify: `README.md`, `tests/test_readme_contract.py`
- Test: `tests/test_readme_contract.py`

- [ ] **Step 1: Extend the README contract test to require the animation-support link**

Append to `tests/test_readme_contract.py`:

```python
def test_readme_links_animation_support_doc() -> None:
    text = readme_text()
    assert "docs/demo/animation-plan.md" in text
    assert "static-SVG-first" in text
    assert (ROOT / "docs" / "demo" / "animation-plan.md").exists()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_readme_contract.py -q --basetemp .pytest-tmp-readme-animation`
Expected: FAIL because the animation-support doc and README link do not exist yet.

- [ ] **Step 3: Create `docs/demo/animation-plan.md`**

Create `docs/demo/animation-plan.md`:

````markdown
# Animation Plan

`repo-context-hooks` keeps the README static-SVG-first so the core GitHub experience stays lightweight, sharp, and maintainable.

## Goal

Use the SVG diagrams in `assets/diagrams/` as the source of truth for optional launch and demo animations.

## Allowed Animation Outputs

- short GIFs for launch posts
- short MP4 clips for social sharing
- frame sequences for blog posts or presentations

## Rules

- derive motion from the SVG source assets instead of inventing separate visual systems
- use motion to clarify lifecycle flow, not to decorate the README
- do not imply automation the tool does not actually provide
- do not make the GitHub landing page depend on animation support

## Recommended Sequence

1. `lifecycle-flow.svg`
   - reveal each phase in order
   - pause on the continuity captions
2. `repo-contract.svg`
   - emphasize `README.md`
   - then `specs/README.md`
   - then the hooks/skills bridge
3. `before-after-continuity.svg`
   - transition from drift to deterministic handoff

## Example Tooling

Example export pipeline:

```bash
inkscape assets/diagrams/lifecycle-flow.svg --export-filename=docs/demo/lifecycle-flow.png
ffmpeg -loop 1 -i docs/demo/lifecycle-flow.png -t 3 -vf "fps=12,scale=1600:-1:flags=lanczos" docs/demo/lifecycle-flow.mp4
```

The exact tooling can change, but the source assets should stay stable.
````

- [ ] **Step 4: Add the animation-support link to `README.md`**

Update the `Technical Details` section in `README.md` so it becomes:

```markdown
## Technical Details

- Primary CLI: `repo-context-hooks`
- Compatibility aliases: `repohandoff`, `graphify`
- Supported agent targets today: Codex and Claude
- Expected repo contract: `README.md` plus `specs/README.md`
- Architecture notes: [docs/architecture.md](docs/architecture.md)
- Minimal example: [examples/minimal-repo/](examples/minimal-repo/)
- Multi-project example: [examples/multi-project/](examples/multi-project/)
- Animation support plan: [docs/demo/animation-plan.md](docs/demo/animation-plan.md)

The README remains static-SVG-first so GitHub rendering stays reliable while animation assets can still be derived from the same diagram sources for launch posts and demos.
```

- [ ] **Step 5: Run the test again to verify it passes**

Run: `python -m pytest tests/test_readme_contract.py -q --basetemp .pytest-tmp-readme-animation`
Expected: PASS

- [ ] **Step 6: Commit the animation-support doc**

```bash
git add README.md docs/demo/animation-plan.md tests/test_readme_contract.py
git commit -m "docs: add animation support plan"
```

## Task 4: Verify The Full Docs/Test Surface Stays Green

**Files:**
- Modify: none
- Create: none
- Test: entire `tests/` directory

- [ ] **Step 1: Run the full test suite**

Run: `python -m pytest -q --basetemp .pytest-tmp-readme-full`
Expected: all tests pass

- [ ] **Step 2: Verify tracked changes are clean**

Run: `git status --short --untracked-files=no`
Expected: no output

- [ ] **Step 3: Verify the README references all final public assets**

Run: `rg -n "assets/diagrams|docs/demo/animation-plan.md|## Honest Critique" README.md`
Expected: matches for the three diagram paths, the animation-support doc link, and the critique section heading

## Self-Review

### Spec Coverage

- balanced README approach: Task 1
- exact README section order: Task 1
- inline technical detail: Task 1
- three static SVG assets: Task 2
- SVG embeds in README: Task 2
- animation policy / support doc: Task 3
- GitHub-safe final verification: Task 4

### Placeholder Scan

- no `TODO`
- no `TBD`
- all files are explicit
- all code/document edits include full content or precise replacement blocks

### Type Consistency

- asset paths consistently use `assets/diagrams/...`
- README doc link consistently uses `docs/demo/animation-plan.md`
- the repo contract consistently uses `README.md` and `specs/README.md`
