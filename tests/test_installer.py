from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from repo_context_hooks.installer import (
    dedup_platform,
    install_global_hooks,
    install_repo_hooks,
    install_platform,
    install_skills,
    platform_skill_dir,
    supported_platform_ids,
    uninstall_platform,
)
from repo_context_hooks.platforms.runtime import deduplicate_hooks, uninstall_global_hooks

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
    expected_scripts_dir = (
        agent_home / ".claude" / "skills" / "context-handoff-hooks" / "scripts"
    ).as_posix()
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


def test_install_platform_codex_writes_global_settings_marker() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    agent_home = tmp_path / "home"

    result = install_platform(
        "codex",
        repo_root=repo,
        home=agent_home,
        install_repo_context=False,
    )

    codex_settings = agent_home / ".codex" / "settings.json"
    assert codex_settings.exists(), "install_global_hooks must write ~/.codex/settings.json"
    import json
    data = json.loads(codex_settings.read_text(encoding="utf-8"))
    assert data.get("_repo_context_hooks_installed") is True
    assert result.home_statuses.get("settings.json") == "installed"


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


def test_install_platform_claude_also_repo_hooks_writes_repo_settings() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    result = install_platform(
        "claude",
        repo_root=repo,
        home=tmp_path / "home",
        also_repo_hooks=True,
    )

    repo_settings = repo / ".claude" / "settings.json"
    assert repo_settings.exists(), "--also-repo-hooks must write per-repo .claude/settings.json"
    assert result.repo_statuses, "repo_statuses must be non-empty when --also-repo-hooks is set"


def test_install_platform_codex_install_global_hooks_idempotent() -> None:
    tmp_path = _tmp_dir()
    agent_home = tmp_path / "home"

    from repo_context_hooks.platforms.codex import install_global_hooks as codex_global_hooks

    first = codex_global_hooks(agent_home)
    second = codex_global_hooks(agent_home)

    assert first["settings.json"] == "installed"
    assert second["settings.json"] == "skipped"

    settings_path = agent_home / ".codex" / "settings.json"
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    assert data["_repo_context_hooks_installed"] is True


def test_install_platform_codex_install_global_hooks_preserves_existing_settings() -> None:
    tmp_path = _tmp_dir()
    agent_home = tmp_path / "home"
    settings_path = agent_home / ".codex" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps({"existing_key": "existing_value"}),
        encoding="utf-8",
    )

    from repo_context_hooks.platforms.codex import install_global_hooks as codex_global_hooks

    codex_global_hooks(agent_home)

    data = json.loads(settings_path.read_text(encoding="utf-8"))
    assert data["existing_key"] == "existing_value", "existing settings must be preserved"
    assert data["_repo_context_hooks_installed"] is True


# ---------------------------------------------------------------------------
# Uninstall tests
# ---------------------------------------------------------------------------


def test_uninstall_removes_skills_dir() -> None:
    tmp_path = _tmp_dir()
    agent_home = tmp_path / "home"

    # Install first so there is something to remove.
    install_global_hooks(agent_home)
    install_skills("claude", home=agent_home, force=False)

    skills_dir = agent_home / ".claude" / "skills" / "context-handoff-hooks"
    assert skills_dir.exists(), "skills dir must exist after install"

    result = uninstall_platform("claude", home=agent_home)

    assert not skills_dir.exists(), "skills dir must be gone after uninstall"
    assert result["context-handoff-hooks"] == "removed"


def test_uninstall_cleans_settings_json() -> None:
    tmp_path = _tmp_dir()
    agent_home = tmp_path / "home"

    install_global_hooks(agent_home)

    settings_path = agent_home / ".claude" / "settings.json"
    before = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "SessionStart" in before["hooks"], "hooks must be present before uninstall"

    result = uninstall_platform("claude", home=agent_home)

    after = json.loads(settings_path.read_text(encoding="utf-8"))
    lifecycle_events = {"SessionStart", "PreCompact", "PostCompact", "SessionEnd"}
    remaining = lifecycle_events & set(after.get("hooks", {}).keys())
    assert remaining == set(), f"lifecycle hooks must be removed; still present: {remaining}"
    assert result["settings.json"] == "cleaned"


def test_uninstall_preserves_user_hooks() -> None:
    """Only hooks added by this tool are removed; adjacent user hooks survive."""
    tmp_path = _tmp_dir()
    agent_home = tmp_path / "home"
    settings_path = agent_home / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True)

    # Pre-populate with a user hook on SessionStart alongside our future hooks.
    settings_path.write_text(
        json.dumps({
            "permissions": {"allow": ["Bash(git:*)"]},
            "hooks": {
                "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo user-pretool"}]}],
                "SessionStart": [{"matcher": "", "hooks": [{"type": "command", "command": "echo user-session"}]}],
            },
        }),
        encoding="utf-8",
    )

    install_global_hooks(agent_home)

    # Confirm our hooks were merged in.
    mid = json.loads(settings_path.read_text(encoding="utf-8"))
    assert len(mid["hooks"]["SessionStart"]) == 2, "user group + our group must both be present"

    uninstall_platform("claude", home=agent_home)

    after = json.loads(settings_path.read_text(encoding="utf-8"))
    # User hooks must survive.
    assert after["permissions"]["allow"] == ["Bash(git:*)"], "permissions must be preserved"
    assert "PreToolUse" in after["hooks"], "PreToolUse user hook must survive"
    # The user's SessionStart group must survive; our group must be gone.
    session_start_groups = after["hooks"].get("SessionStart", [])
    assert len(session_start_groups) == 1, "only the user's SessionStart group must remain"
    user_cmds = [h["command"] for h in session_start_groups[0]["hooks"]]
    assert user_cmds == ["echo user-session"], "user hook command must be intact"


def test_uninstall_idempotent() -> None:
    tmp_path = _tmp_dir()
    agent_home = tmp_path / "home"

    install_global_hooks(agent_home)
    install_skills("claude", home=agent_home, force=False)

    first = uninstall_platform("claude", home=agent_home)
    second = uninstall_platform("claude", home=agent_home)

    assert first["context-handoff-hooks"] == "removed"
    assert second["context-handoff-hooks"] == "not found", "second run must be a no-op"
    assert second["settings.json"] in ("no changes", "not found"), (
        f"second run settings.json status must indicate no-op, got: {second['settings.json']}"
    )


def test_uninstall_no_op_when_nothing_installed() -> None:
    """Uninstall on a fresh home directory must not raise and must return graceful statuses."""
    tmp_path = _tmp_dir()
    agent_home = tmp_path / "home"

    # Nothing was ever installed — no .claude directory at all.
    result = uninstall_global_hooks(agent_home)

    assert result["context-handoff-hooks"] == "not found"
    assert result["settings.json"] == "not found"


# ---------------------------------------------------------------------------
# --no-telemetry / telemetry=False tests
# ---------------------------------------------------------------------------


def test_global_hook_payload_no_telemetry_prefixes_all_commands() -> None:
    """global_hook_payload(telemetry=False) must prefix every command with REPO_CONTEXT_HOOKS_TELEMETRY=0."""
    from repo_context_hooks.platforms.runtime import global_hook_payload

    scripts_dir = Path("/fake/skills/context-handoff-hooks/scripts")
    payload = global_hook_payload(scripts_dir, telemetry=False)

    all_commands = [
        hook["command"]
        for event_hooks in payload.values()
        for group in event_hooks
        for hook in group["hooks"]
    ]
    assert all_commands, "payload must contain at least one command"
    for cmd in all_commands:
        assert cmd.startswith("REPO_CONTEXT_HOOKS_TELEMETRY=0 "), (
            f"Expected telemetry opt-out prefix on: {cmd}"
        )


def test_global_hook_payload_default_has_no_prefix() -> None:
    """global_hook_payload() with default telemetry=True must NOT prefix commands."""
    from repo_context_hooks.platforms.runtime import global_hook_payload

    scripts_dir = Path("/fake/skills/context-handoff-hooks/scripts")
    payload = global_hook_payload(scripts_dir)

    all_commands = [
        hook["command"]
        for event_hooks in payload.values()
        for group in event_hooks
        for hook in group["hooks"]
    ]
    for cmd in all_commands:
        assert not cmd.startswith("REPO_CONTEXT_HOOKS_TELEMETRY=0 "), (
            f"Default payload must not have opt-out prefix: {cmd}"
        )


def test_install_global_hooks_no_telemetry_writes_prefix_to_settings() -> None:
    """install_global_hooks(telemetry=False) must write prefixed command strings to settings.json."""
    tmp_path = _tmp_dir()
    agent_home = tmp_path / "home"

    install_global_hooks(agent_home, telemetry=False)

    settings_path = agent_home / ".claude" / "settings.json"
    assert settings_path.exists()
    settings = json.loads(settings_path.read_text(encoding="utf-8"))

    all_commands = [
        hook["command"]
        for event_hooks in settings["hooks"].values()
        for group in event_hooks
        for hook in group["hooks"]
    ]
    assert all_commands, "settings.json must contain hook commands"
    for cmd in all_commands:
        assert cmd.startswith("REPO_CONTEXT_HOOKS_TELEMETRY=0 "), (
            f"Hook command must carry opt-out prefix when telemetry=False: {cmd}"
        )


def test_install_platform_claude_no_telemetry_writes_prefix() -> None:
    """install_platform(..., telemetry=False) must bake opt-out prefix into hook commands."""
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    result = install_platform(
        "claude",
        repo_root=repo,
        home=tmp_path / "home",
        telemetry=False,
    )

    agent_settings = tmp_path / "home" / ".claude" / "settings.json"
    assert agent_settings.exists()
    settings = json.loads(agent_settings.read_text(encoding="utf-8"))

    all_commands = [
        hook["command"]
        for event_hooks in settings["hooks"].values()
        for group in event_hooks
        for hook in group["hooks"]
    ]
    assert all_commands
    for cmd in all_commands:
        assert cmd.startswith("REPO_CONTEXT_HOOKS_TELEMETRY=0 "), (
            f"Installed command must carry opt-out prefix: {cmd}"
        )
    assert result.home_statuses.get("settings.json") == "installed"


def test_install_platform_claude_default_telemetry_has_no_prefix() -> None:
    """Default install (telemetry=True) must not add any env-var prefix to hook commands."""
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    install_platform("claude", repo_root=repo, home=tmp_path / "home")

    settings = json.loads(
        (tmp_path / "home" / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    all_commands = [
        hook["command"]
        for event_hooks in settings["hooks"].values()
        for group in event_hooks
        for hook in group["hooks"]
    ]
    for cmd in all_commands:
        assert "REPO_CONTEXT_HOOKS_TELEMETRY=0" not in cmd, (
            f"Default install must not embed opt-out prefix: {cmd}"
        )


# ---------------------------------------------------------------------------
# Deduplication tests
# ---------------------------------------------------------------------------


def test_install_twice_no_duplicates() -> None:
    """Running install twice must not add duplicate hook groups per event."""
    tmp_path = _tmp_dir()
    agent_home = tmp_path / "home"

    install_global_hooks(agent_home)
    install_global_hooks(agent_home)

    settings = json.loads(
        (agent_home / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    lifecycle_events = ("SessionStart", "PreCompact", "PostCompact", "SessionEnd")
    for event in lifecycle_events:
        groups = settings["hooks"].get(event, [])
        total_hooks = sum(len(g.get("hooks", [])) for g in groups)
        # Expected counts: SessionStart=2, PreCompact=1, PostCompact=2, SessionEnd=1
        # After two installs, counts must not double.
        assert total_hooks <= 2, (
            f"Event {event} must not have duplicated hooks after two installs; "
            f"found {total_hooks} hook entries"
        )


def test_deduplicate_hooks_removes_backslash_dupes() -> None:
    """deduplicate_hooks must treat backslash and forward-slash paths as the same command."""
    tmp_path = _tmp_dir()
    agent_home = tmp_path / "home"
    settings_path = agent_home / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True)

    # Write two variants of the same command — one with backslashes, one with forward slashes.
    forward_cmd = "python /home/user/.claude/skills/context-handoff-hooks/scripts/repo_specs_memory.py session-start"
    backward_cmd = forward_cmd.replace("/", "\\")
    settings_path.write_text(
        json.dumps({
            "hooks": {
                "SessionStart": [
                    {
                        "matcher": "",
                        "hooks": [
                            {"type": "command", "command": backward_cmd, "timeout": 20},
                            {"type": "command", "command": forward_cmd, "timeout": 20},
                        ],
                    }
                ]
            }
        }),
        encoding="utf-8",
    )

    result = deduplicate_hooks(agent_home)

    assert result["removed"] == 1, f"Expected 1 duplicate removed, got {result['removed']}"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    session_start_hooks = [
        h
        for group in settings["hooks"]["SessionStart"]
        for h in group.get("hooks", [])
    ]
    assert len(session_start_hooks) == 1, (
        f"Expected 1 hook after dedup, found {len(session_start_hooks)}"
    )


def test_deduplicate_hooks_idempotent() -> None:
    """Calling deduplicate_hooks twice on clean settings returns removed=0 on the second call."""
    tmp_path = _tmp_dir()
    agent_home = tmp_path / "home"

    install_global_hooks(agent_home)

    first = deduplicate_hooks(agent_home)
    second = deduplicate_hooks(agent_home)

    assert second["removed"] == 0, (
        f"Second dedup call must be a no-op; reported removed={second['removed']}"
    )
    _ = first  # first call result is not asserted — state may or may not have dupes
