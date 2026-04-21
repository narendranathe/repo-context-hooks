from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from repo_context_hooks.platforms import get_registry

ROOT = Path(__file__).resolve().parents[1]


def _tmp_dir() -> Path:
    base = ROOT / ".tmp-tests"
    base.mkdir(exist_ok=True)
    path = base / uuid4().hex
    path.mkdir()
    return path


def test_claude_plan_includes_repo_hooks() -> None:
    tmp_path = _tmp_dir()
    adapter = get_registry().get("claude")
    plan = adapter.build_install_plan(repo_root=tmp_path, home=tmp_path / "home")

    assert plan.installs_repo_context is True
    assert any(path.endswith(".claude/settings.json") for path in plan.repo_paths)
    assert any(
        path.endswith(".claude/scripts/repo_specs_memory.py")
        for path in plan.repo_paths
    )
    assert any(".claude/skills" in path for path in plan.home_paths)


def test_cursor_plan_targets_cursor_rules_and_agents() -> None:
    tmp_path = _tmp_dir()
    adapter = get_registry().get("cursor")
    plan = adapter.build_install_plan(repo_root=tmp_path, home=tmp_path / "home")

    assert any(
        path.endswith(".cursor/rules/repo-context-continuity.mdc")
        for path in plan.repo_paths
    )
    assert any(path.endswith("AGENTS.md") for path in plan.repo_paths)
    assert plan.installs_repo_context is True
    assert any("native lifecycle hooks" in item.lower() for item in plan.warnings)


def test_codex_plan_installs_skills_and_repo_contract() -> None:
    tmp_path = _tmp_dir()
    adapter = get_registry().get("codex")
    plan = adapter.build_install_plan(repo_root=tmp_path, home=tmp_path / "home")

    assert any(".codex/skills" in path for path in plan.home_paths)
    assert any(path.endswith("AGENTS.md") for path in plan.repo_paths)
    assert any("native lifecycle hooks" in item.lower() for item in plan.warnings)
