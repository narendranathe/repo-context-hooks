from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from repo_context_hooks.installer import (
    install_global_hooks,
    install_repo_hooks,
    install_platform,
    install_skills,
    platform_skill_dir,
    supported_platform_ids,
)

ROOT = Path(__file__).resolve().parents[1]


def _tmp_dir() -> Path:
    base = ROOT / ".tmp-tests"
    base.mkdir(exist_ok=True)
    path = base / uuid4().hex
    path.mkdir()
    return path


def test_platform_skill_dir() -> None:
    home = Path("/tmp/demo-home")
    assert platform_skill_dir("claude", home=home) == home / ".claude" / "skills"


def test_supported_platform_ids() -> None:
    assert supported_platform_ids() == (
        "claude",
        "cursor",
        "codex",
        "replit",
        "windsurf",
        "lovable",
        "openclaw",
        "ollama",
        "kimi",
    )


def test_install_skills_idempotent() -> None:
    tmp_path = _tmp_dir()
    target, first = install_skills("claude", home=tmp_path, force=False)
    assert target.exists()
    assert first
    assert all(state == "installed" for state in first.values())

    _, second = install_skills("claude", home=tmp_path, force=False)
    assert all(state == "skipped" for state in second.values())

    _, third = install_skills("claude", home=tmp_path, force=True)
    assert all(state == "installed" for state in third.values())


def test_install_repo_hooks_merges_existing() -> None:
    tmp_path = _tmp_dir()
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
    commands = [
        hook["command"]
        for group in settings["hooks"]["SessionStart"]
        for hook in group["hooks"]
    ]
    assert all("$CLAUDE_PROJECT_DIR" in command for command in commands)
    assert all(str(repo) not in command for command in commands)
    assert (repo / ".claude" / "scripts" / "repo_specs_memory.py").exists()
    assert (repo / ".claude" / "scripts" / "session_context.py").exists()


def test_install_repo_hooks_does_not_clobber_scripts_without_force() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    scripts_dir = repo / ".claude" / "scripts"
    scripts_dir.mkdir(parents=True)
    repo_specs = scripts_dir / "repo_specs_memory.py"
    session_ctx = scripts_dir / "session_context.py"
    repo_specs.write_text("custom repo specs\n", encoding="utf-8")
    session_ctx.write_text("custom session ctx\n", encoding="utf-8")

    installed = install_repo_hooks(repo, force=False)

    assert installed["repo_specs_memory.py"] == "skipped"
    assert installed["session_context.py"] == "skipped"
    assert repo_specs.read_text(encoding="utf-8") == "custom repo specs\n"
    assert session_ctx.read_text(encoding="utf-8") == "custom session ctx\n"


def test_install_global_hooks_writes_to_agent_home_settings() -> None:
    tmp_path = _tmp_dir()
    agent_home = tmp_path / "home"

    result = install_global_hooks(agent_home)

    settings_path = agent_home / ".claude" / "settings.json"
    assert settings_path.exists(), "settings.json must be written to agent home"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    hooks = settings.get("hooks", {})
    assert "SessionStart" in hooks
    assert "PreCompact" in hooks
    assert "PostCompact" in hooks
    assert "SessionEnd" in hooks
    assert result["settings.json"] == "installed"


def test_install_global_hooks_uses_absolute_script_paths() -> None:
    tmp_path = _tmp_dir()
    agent_home = tmp_path / "home"

    install_global_hooks(agent_home)

    settings = json.loads(
        (agent_home / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    all_commands = [
        hook["command"]
        for event_hooks in settings["hooks"].values()
        for group in event_hooks
        for hook in group["hooks"]
    ]
    expected_scripts_dir = str(
        agent_home / ".claude" / "skills" / "context-handoff-hooks" / "scripts"
    )
    for command in all_commands:
        assert "$CLAUDE_PROJECT_DIR" not in command, (
            f"Global hooks must not use $CLAUDE_PROJECT_DIR: {command}"
        )
        assert expected_scripts_dir in command, (
            f"Global hook must reference agent-home script path: {command}"
        )


def test_install_global_hooks_preserves_existing_settings() -> None:
    tmp_path = _tmp_dir()
    agent_home = tmp_path / "home"
    settings_path = agent_home / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps({
            "permissions": {"allow": ["Bash(git:*)"]},
            "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": []}]},
        }),
        encoding="utf-8",
    )

    install_global_hooks(agent_home)

    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert settings["permissions"]["allow"] == ["Bash(git:*)"], "permissions must be preserved"
    assert "PreToolUse" in settings["hooks"], "existing hooks must be preserved"
    assert "SessionStart" in settings["hooks"], "new lifecycle hooks must be added"


def test_install_global_hooks_is_idempotent() -> None:
    tmp_path = _tmp_dir()
    agent_home = tmp_path / "home"

    install_global_hooks(agent_home)
    install_global_hooks(agent_home)

    settings = json.loads(
        (agent_home / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    for event, groups in settings["hooks"].items():
        if event in ("SessionStart", "PreCompact", "PostCompact", "SessionEnd"):
            assert len(groups) == 1, (
                f"Idempotent install must not duplicate hook groups for {event}"
            )


def test_install_platform_claude_writes_to_agent_home_not_repo() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    result = install_platform("claude", repo_root=repo, home=tmp_path / "home")

    agent_settings = tmp_path / "home" / ".claude" / "settings.json"
    repo_settings = repo / ".claude" / "settings.json"
    assert agent_settings.exists(), "global hooks must be written to agent home settings"
    assert not repo_settings.exists(), "default install must NOT write to per-repo settings"
    assert result.home_statuses.get("settings.json") == "installed"


def test_install_platform_codex_summary_mentions_skills_only_when_repo_context_skipped() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()

    result = install_platform(
        "codex",
        repo_root=repo,
        home=tmp_path / "home",
        install_repo_context=False,
    )

    assert "support checked" in result.summary.lower()


def test_install_skills_rejects_codex_platform() -> None:
    tmp_path = _tmp_dir()

    try:
        install_skills("codex", home=tmp_path, force=False)
    except ValueError as exc:
        assert "Unsupported platform: codex" in str(exc)
    else:
        raise AssertionError("Expected install_skills to reject codex")


def test_install_platform_replit_reports_manual_step() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    specs_dir = repo / "specs"
    specs_dir.mkdir()
    (specs_dir / "README.md").write_text("# Specs\n", encoding="utf-8")

    result = install_platform("replit", repo_root=repo, home=tmp_path / "home")

    assert result.home_target is None
    assert any("fresh replit agent conversation" in step.lower() for step in result.manual_steps)


def test_install_platform_windsurf_reports_repo_rule_install() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    specs_dir = repo / "specs"
    specs_dir.mkdir()
    (specs_dir / "README.md").write_text("# Specs\n", encoding="utf-8")

    result = install_platform("windsurf", repo_root=repo, home=tmp_path / "home", install_repo_context=True)

    assert result.home_target is None
    assert "repo context installed" in result.summary.lower()


def test_install_platform_lovable_reports_manual_ui_steps() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    specs_dir = repo / "specs"
    specs_dir.mkdir()
    (specs_dir / "README.md").write_text("# Specs\n", encoding="utf-8")

    result = install_platform("lovable", repo_root=repo, home=tmp_path / "home")

    assert result.home_target is None
    assert any("project knowledge" in step.lower() for step in result.manual_steps)
    assert any("workspace knowledge" in step.lower() for step in result.manual_steps)


def test_install_platform_openclaw_reports_manual_workspace_steps() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    specs_dir = repo / "specs"
    specs_dir.mkdir()
    (specs_dir / "README.md").write_text("# Specs\n", encoding="utf-8")

    result = install_platform("openclaw", repo_root=repo, home=tmp_path / "home")

    assert result.home_target is None
    assert any("agents.defaults.workspace" in step for step in result.manual_steps)
    assert any("secrets" in step.lower() for step in result.manual_steps)


def test_install_platform_ollama_reports_manual_model_steps() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    specs_dir = repo / "specs"
    specs_dir.mkdir()
    (specs_dir / "README.md").write_text("# Specs\n", encoding="utf-8")

    result = install_platform("ollama", repo_root=repo, home=tmp_path / "home")

    assert result.home_target is None
    assert any("ollama create" in step.lower() for step in result.manual_steps)
    assert any("FROM" in step for step in result.manual_steps)


def test_install_platform_kimi_reports_manual_init_steps() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    specs_dir = repo / "specs"
    specs_dir.mkdir()
    (specs_dir / "README.md").write_text("# Specs\n", encoding="utf-8")

    result = install_platform("kimi", repo_root=repo, home=tmp_path / "home")

    assert result.home_target is None
    assert any("/init" in step for step in result.manual_steps)
    assert any("Kimi Code CLI" in warning for warning in result.warnings)
