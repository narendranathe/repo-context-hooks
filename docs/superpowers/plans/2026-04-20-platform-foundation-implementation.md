# Platform Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the tuple-based installer with a real platform-adapter foundation, ship Claude/Cursor/Codex support tiers, add `platforms` and `doctor` commands, reposition public docs, and create GitHub issues for planned platforms.

**Architecture:** Introduce a narrow adapter registry that produces install and validation behavior per platform. Keep Claude as the only `native` lifecycle implementation, add useful `partial` support for Cursor and Codex, and derive CLI/docs support claims from code-owned metadata instead of hand-written promises.

**Tech Stack:** Python 3.9+, setuptools CLI package, pytest, git, GitHub issues

---

### Task 1: Introduce Platform Metadata And Registry

**Files:**
- Create: `repo_context_hooks/platforms/__init__.py`
- Create: `repo_context_hooks/platforms/base.py`
- Create: `repo_context_hooks/platforms/registry.py`
- Test: `tests/test_platform_registry.py`
- Modify: `repo_context_hooks/installer.py`

- [ ] **Step 1: Write the failing registry tests**

```python
from repo_context_hooks.platforms import get_registry


def test_registry_exposes_phase1_platform_ids() -> None:
    registry = get_registry()

    assert [adapter.id for adapter in registry.all()] == [
        "claude",
        "cursor",
        "codex",
    ]


def test_registry_support_tiers_match_phase1_contract() -> None:
    registry = get_registry()

    assert registry.get("claude").support_tier.value == "native"
    assert registry.get("cursor").support_tier.value == "partial"
    assert registry.get("codex").support_tier.value == "partial"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_platform_registry.py -q --basetemp .pytest-tmp-platform-registry-red`
Expected: FAIL with import errors for `repo_context_hooks.platforms` or missing registry objects.

- [ ] **Step 3: Add minimal platform base types and registry**

```python
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, Protocol


class SupportTier(str, Enum):
    NATIVE = "native"
    PARTIAL = "partial"
    PLANNED = "planned"


@dataclass(frozen=True)
class PlatformMetadata:
    id: str
    display_name: str
    support_tier: SupportTier
    summary: str


class PlatformAdapter(Protocol):
    metadata: PlatformMetadata


class PlatformRegistry:
    def __init__(self, adapters: Iterable[PlatformAdapter]) -> None:
        self._adapters: Dict[str, PlatformAdapter] = {
            adapter.metadata.id: adapter for adapter in adapters
        }

    def all(self) -> list[PlatformAdapter]:
        return list(self._adapters.values())

    def get(self, platform_id: str) -> PlatformAdapter:
        return self._adapters[platform_id]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_platform_registry.py -q --basetemp .pytest-tmp-platform-registry-green`
Expected: PASS

- [ ] **Step 5: Refactor installer to stop owning `PLATFORMS`**

```python
from .platforms import get_registry


def supported_platform_ids() -> tuple[str, ...]:
    return tuple(adapter.id for adapter in get_registry().all())
```

- [ ] **Step 6: Run focused tests for registry and installer**

Run: `python -m pytest tests/test_platform_registry.py tests/test_installer.py -q --basetemp .pytest-tmp-platform-registry-full`
Expected: PASS with updated installer behavior.

- [ ] **Step 7: Commit**

```bash
git add repo_context_hooks/platforms repo_context_hooks/installer.py tests/test_platform_registry.py tests/test_installer.py
git commit -m "feat: add platform registry foundation"
```

### Task 2: Add Install Plans And Phase 1 Adapters

**Files:**
- Create: `repo_context_hooks/platforms/claude.py`
- Create: `repo_context_hooks/platforms/cursor.py`
- Create: `repo_context_hooks/platforms/codex.py`
- Modify: `repo_context_hooks/platforms/base.py`
- Modify: `repo_context_hooks/platforms/__init__.py`
- Modify: `repo_context_hooks/installer.py`
- Test: `tests/test_platform_install_plans.py`

- [ ] **Step 1: Write the failing adapter-plan tests**

```python
from pathlib import Path

from repo_context_hooks.platforms import get_registry


def test_claude_plan_includes_repo_hooks(tmp_path: Path) -> None:
    adapter = get_registry().get("claude")
    plan = adapter.build_install_plan(repo_root=tmp_path, home=tmp_path / "home")

    assert plan.installs_repo_context is True
    assert ".claude/settings.json" in "\n".join(plan.repo_paths)


def test_cursor_plan_targets_cursor_rules_and_agents(tmp_path: Path) -> None:
    adapter = get_registry().get("cursor")
    plan = adapter.build_install_plan(repo_root=tmp_path, home=tmp_path / "home")

    assert any(path.endswith(".cursor/rules/repo-context-continuity.mdc") for path in plan.repo_paths)
    assert any(path.endswith("AGENTS.md") for path in plan.repo_paths)
    assert plan.installs_repo_context is True


def test_codex_plan_installs_skills_and_repo_contract(tmp_path: Path) -> None:
    adapter = get_registry().get("codex")
    plan = adapter.build_install_plan(repo_root=tmp_path, home=tmp_path / "home")

    assert any(".codex/skills" in path for path in plan.home_paths)
    assert any(path.endswith("AGENTS.md") for path in plan.repo_paths)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_platform_install_plans.py -q --basetemp .pytest-tmp-install-plans-red`
Expected: FAIL because adapters do not expose `build_install_plan`.

- [ ] **Step 3: Add `InstallPlan` and implement Claude/Cursor/Codex adapters**

```python
@dataclass(frozen=True)
class InstallPlan:
    platform_id: str
    home_paths: tuple[str, ...]
    repo_paths: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    manual_steps: tuple[str, ...] = ()
    installs_repo_context: bool = False
```

```python
class CursorAdapter:
    metadata = PlatformMetadata(
        id="cursor",
        display_name="Cursor",
        support_tier=SupportTier.PARTIAL,
        summary="Installs repo continuity rules and agent instructions for Cursor.",
    )

    def build_install_plan(self, repo_root: Path, home: Path | None = None) -> InstallPlan:
        return InstallPlan(
            platform_id="cursor",
            home_paths=(),
            repo_paths=(
                str(repo_root / ".cursor" / "rules" / "repo-context-continuity.mdc"),
                str(repo_root / "AGENTS.md"),
            ),
            installs_repo_context=True,
        )
```

- [ ] **Step 4: Update installer to delegate to adapters**

```python
def install_platform(platform: str, repo_root: Path, force: bool = False, home: Path | None = None) -> InstallResult:
    adapter = get_registry().get(platform)
    plan = adapter.build_install_plan(repo_root=repo_root, home=home)
    return adapter.install(repo_root=repo_root, home=home, force=force, plan=plan)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_platform_install_plans.py tests/test_installer.py -q --basetemp .pytest-tmp-install-plans-green`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add repo_context_hooks/platforms repo_context_hooks/installer.py tests/test_platform_install_plans.py tests/test_installer.py
git commit -m "feat: add phase1 platform adapters"
```

### Task 3: Add CLI `platforms` And `doctor`

**Files:**
- Modify: `repo_context_hooks/cli.py`
- Create: `repo_context_hooks/doctor.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_doctor.py`

- [ ] **Step 1: Write the failing CLI and doctor tests**

```python
from pathlib import Path

from repo_context_hooks.cli import build_parser
from repo_context_hooks.doctor import diagnose_platform


def test_parser_supports_platforms_and_doctor_commands() -> None:
    parser = build_parser()

    assert parser.parse_args(["platforms"]).command == "platforms"
    assert parser.parse_args(["doctor", "--platform", "claude"]).command == "doctor"


def test_doctor_reports_missing_cursor_rule(tmp_path: Path) -> None:
    report = diagnose_platform("cursor", repo_root=tmp_path, home=tmp_path / "home")

    assert report.ok is False
    assert any(".cursor/rules/repo-context-continuity.mdc" in item for item in report.missing)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py tests/test_doctor.py -q --basetemp .pytest-tmp-doctor-red`
Expected: FAIL with missing command and module errors.

- [ ] **Step 3: Implement `platforms` output and doctor validation**

```python
def _platforms() -> int:
    for adapter in get_registry().all():
        meta = adapter.metadata
        print(f"{meta.id}\t{meta.support_tier.value}\t{meta.summary}")
    return 0


def _doctor(args: argparse.Namespace) -> int:
    report = diagnose_platform(args.platform, repo_root=Path(args.repo_root).resolve())
    print(report.render())
    return 0 if report.ok else 1
```

- [ ] **Step 4: Implement minimal report object**

```python
@dataclass(frozen=True)
class DoctorReport:
    platform_id: str
    ok: bool
    present: tuple[str, ...]
    missing: tuple[str, ...]

    def render(self) -> str:
        status = "OK" if self.ok else "MISSING"
        return "\n".join([f"[{status}] {self.platform_id}", *self.present, *self.missing])
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_cli.py tests/test_doctor.py -q --basetemp .pytest-tmp-doctor-green`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add repo_context_hooks/cli.py repo_context_hooks/doctor.py tests/test_cli.py tests/test_doctor.py
git commit -m "feat: add platform listing and doctor commands"
```

### Task 4: Install Real Repo Artifacts For Cursor And Codex

**Files:**
- Create: `repo_context_hooks/bundle/templates/AGENTS.md`
- Create: `repo_context_hooks/bundle/templates/cursor-rule.mdc`
- Modify: `repo_context_hooks/platforms/cursor.py`
- Modify: `repo_context_hooks/platforms/codex.py`
- Modify: `repo_context_hooks/platforms/claude.py`
- Test: `tests/test_platform_artifacts.py`

- [ ] **Step 1: Write the failing artifact-install tests**

```python
from pathlib import Path

from repo_context_hooks.installer import install_platform


def test_install_cursor_writes_rule_and_agents(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    result = install_platform("cursor", repo_root=repo, home=tmp_path / "home")

    assert (repo / ".cursor" / "rules" / "repo-context-continuity.mdc").exists()
    assert (repo / "AGENTS.md").exists()
    assert "Cursor" in result.summary


def test_install_codex_preserves_agents_and_installs_skills(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    install_platform("codex", repo_root=repo, home=tmp_path / "home")

    assert (repo / "AGENTS.md").exists()
    assert (tmp_path / "home" / ".codex" / "skills").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_platform_artifacts.py -q --basetemp .pytest-tmp-artifacts-red`
Expected: FAIL because Cursor/Codex repo artifacts are not yet installed.

- [ ] **Step 3: Add reusable templates and wire adapters to them**

```text
---
description: Repo context continuity
alwaysApply: true
---

- Treat README.md as the user-facing source of truth.
- Treat specs/README.md as engineering continuity memory.
- Read AGENTS.md before making major changes.
- Preserve next-work state when handing off or switching sessions.
```

```markdown
# AGENTS.md

Start by reading:

- README.md
- specs/README.md

Use the repo as the continuity source of truth. Preserve decisions, next work, and constraints in repo files rather than chat-only state.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_platform_artifacts.py tests/test_platform_install_plans.py -q --basetemp .pytest-tmp-artifacts-green`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add repo_context_hooks/bundle/templates repo_context_hooks/platforms tests/test_platform_artifacts.py tests/test_platform_install_plans.py
git commit -m "feat: install cursor and codex repo artifacts"
```

### Task 5: Reposition Public Docs And Support Matrix

**Files:**
- Modify: `README.md`
- Create: `docs/platforms.md`
- Modify: `docs/architecture.md`
- Modify: `docs/competitive-analysis.md`
- Modify: `tests/test_readme_contract.py`
- Create: `tests/test_platform_docs.py`

- [ ] **Step 1: Write the failing docs contract tests**

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_mentions_tested_phase1_platforms() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Claude" in text
    assert "Cursor" in text
    assert "Codex" in text
    assert "tested in Phase 1" in text


def test_platform_docs_include_support_tiers() -> None:
    text = (ROOT / "docs" / "platforms.md").read_text(encoding="utf-8")

    assert "native" in text
    assert "partial" in text
    assert "planned" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_readme_contract.py tests/test_platform_docs.py -q --basetemp .pytest-tmp-docs-red`
Expected: FAIL because the current README still exposes outdated sections and no `docs/platforms.md` file exists.

- [ ] **Step 3: Rewrite README around product outcomes and tested support**

```markdown
## Tested In Phase 1

- Claude (`native`)
- Cursor (`partial`)
- Codex (`partial`)

## Planned Next

See [docs/platforms.md](docs/platforms.md) for the roadmap and support tiers.
```

- [ ] **Step 4: Add platform matrix doc**

```markdown
# Platform Support

| Platform | Tier | What works | What does not |
| --- | --- | --- | --- |
| Claude | native | skills, repo hooks, lifecycle continuity | n/a |
| Cursor | partial | rules, AGENTS.md, repo contract | no Claude-style hook parity |
| Codex | partial | skills, AGENTS.md, repo contract | no native lifecycle hooks |
| Replit | planned | issue only | not implemented |
```

- [ ] **Step 5: Update README contract tests to remove internal-only sections**

```python
expected_sections = [
    "# repo-context-hooks",
    "## Why This Exists",
    "## How It Works",
    "## Tested In Phase 1",
    "## Platform Support",
    "## Examples",
    "## Development",
]
```

- [ ] **Step 6: Run test to verify it passes**

Run: `python -m pytest tests/test_readme_contract.py tests/test_platform_docs.py -q --basetemp .pytest-tmp-docs-green`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add README.md docs/platforms.md docs/architecture.md docs/competitive-analysis.md tests/test_readme_contract.py tests/test_platform_docs.py
git commit -m "docs: reposition platform support story"
```

### Task 6: Upgrade Diagrams And Create Planned-Platform Issues

**Files:**
- Modify: `assets/diagrams/lifecycle-flow.svg`
- Modify: `assets/diagrams/repo-contract.svg`
- Modify: `assets/diagrams/before-after-continuity.svg`
- Create: `docs/launch/platform-roadmap.md`
- Modify: `docs/demo/animation-plan.md`
- Create: `tests/test_visual_contract.py`

- [ ] **Step 1: Write the failing visual/docs tests**

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_lifecycle_diagram_mentions_real_interrupted_workflow() -> None:
    text = (ROOT / "assets" / "diagrams" / "lifecycle-flow.svg").read_text(encoding="utf-8")

    assert "bugfix interrupted by compact" in text.lower()


def test_platform_roadmap_doc_links_planned_platforms() -> None:
    text = (ROOT / "docs" / "launch" / "platform-roadmap.md").read_text(encoding="utf-8")

    assert "Replit" in text
    assert "Lovable" in text
    assert "Ollama" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_visual_contract.py -q --basetemp .pytest-tmp-visual-red`
Expected: FAIL because diagrams are still abstract and the roadmap doc does not exist.

- [ ] **Step 3: Replace abstract diagram copy with concrete task-story language**

```svg
<text>Bugfix interrupted by compact</text>
<text>Checkpoint written to specs/README.md</text>
<text>Next session resumes from repo state</text>
```

- [ ] **Step 4: Create roadmap issue brief doc for GitHub issues**

```markdown
# Planned Platform Roadmap

- Replit: workspace agent integration and repo-contract injection
- Lovable: GitHub-sync adapter strategy and repo instruction export
- Ollama: local runtime strategy, likely partial/manual
- OpenClaw: orchestration adapter investigation
- Kimi: integration surface investigation
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_visual_contract.py tests/test_readme_contract.py tests/test_platform_docs.py -q --basetemp .pytest-tmp-visual-green`
Expected: PASS after diagrams and roadmap docs match the new contract.

- [ ] **Step 6: Create GitHub issues from the roadmap**

Run: `gh issue create --title "Platform: Replit adapter"` and repeat for Lovable, Ollama, OpenClaw, and Kimi using the roadmap doc for the issue body.
Expected: five new GitHub issues linked from `docs/launch/platform-roadmap.md`

- [ ] **Step 7: Commit**

```bash
git add assets/diagrams docs/demo/animation-plan.md docs/launch/platform-roadmap.md tests/test_visual_contract.py
git commit -m "docs: add platform roadmap and concrete diagrams"
```

### Task 7: Full Verification And PR Update

**Files:**
- Modify: `README.md`
- Modify: `docs/platforms.md`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_installer.py`
- Modify: `tests/test_readme_contract.py`

- [ ] **Step 1: Run the full test suite**

Run: `python -m pytest -q --basetemp .pytest-tmp-platform-foundation-full`
Expected: PASS with zero failures.

- [ ] **Step 2: Run editable install and CLI smoke checks**

Run: `python -m pip install -e .`
Expected: editable install succeeds.

Run: `repo-context-hooks platforms`
Expected: lists `claude`, `cursor`, and `codex` with tiers.

Run: `repo-context-hooks doctor --platform claude --repo-root .`
Expected: prints a validation report.

- [ ] **Step 3: Review git status and confirm no user-owned untracked files were modified**

Run: `git status --short`
Expected: only intended tracked changes plus pre-existing `UBIQUITOUS_LANGUAGE.md` and `specs/` remain untouched.

- [ ] **Step 4: Commit final integration pass**

```bash
git add README.md docs repo_context_hooks tests assets
git commit -m "feat: ship phase1 platform foundation"
```

- [ ] **Step 5: Push branch and update the existing PR**

Run: `git push -u origin feat/repo-context-hooks`
Expected: branch updates the existing pull request with the new platform foundation work.
