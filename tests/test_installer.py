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


# ---------------------------------------------------------------------------
# Property-based idempotency over realistic hook payloads (issue #71)
#
# `deduplicate_hooks` is called from `install_global_hooks` on every agent
# install. A regression that breaks idempotency would silently grow
# settings.json on every run. The property: regardless of the input shape,
# the on-disk JSON is byte-equal after a second call.
# ---------------------------------------------------------------------------

import pytest  # noqa: E402
from hypothesis import given, strategies as st  # noqa: E402

_HOOK_EVENT = st.sampled_from(
    ["SessionStart", "PreCompact", "PostCompact", "SessionEnd", "PreToolUse", "PostToolUse"]
)
_HOOK_COMMAND = st.sampled_from(
    [
        'python "$CLAUDE_PROJECT_DIR"/.claude/scripts/repo_specs_memory.py session-start',
        'python "$CLAUDE_PROJECT_DIR"/.claude/scripts/session_context.py session-start',
        'python "$CLAUDE_PROJECT_DIR"/.claude/scripts/repo_specs_memory.py post-compact',
        'python ./scripts/foo.py post-compact',
        'echo "noop"',
    ]
)


def _hook_entry(cmd: str) -> dict:
    return {"type": "command", "command": cmd, "timeout": 10}


def _matcher_group(cmds: list[str]) -> dict:
    return {"matcher": "", "hooks": [_hook_entry(c) for c in cmds]}


@st.composite
def _settings_with_potential_dupes(draw) -> dict:
    events = draw(st.lists(_HOOK_EVENT, min_size=1, max_size=4, unique=True))
    hooks: dict = {}
    for event in events:
        cmds = draw(st.lists(_HOOK_COMMAND, min_size=1, max_size=4))
        # Deliberately re-sample from the same list so duplicates are likely.
        injected = draw(st.lists(st.sampled_from(cmds), min_size=0, max_size=2))
        hooks[event] = [_matcher_group(cmds + injected)]
    return {"hooks": hooks}


@given(payload=_settings_with_potential_dupes())
def test_deduplicate_hooks_idempotent_on_disk(
    payload: dict, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """Running `deduplicate_hooks` twice on the same input leaves settings.json byte-equal.

    The function's RETURN value legitimately differs between calls (first
    reports `{"removed": N>0}`, second reports `{"removed": 0}`). Idempotency
    is a property of the on-disk state, not the return dict.

    Uses ``tmp_path_factory`` (not the local ``_tmp_dir()`` helper) so each
    Hypothesis example writes to pytest's TTL-managed tmp tree instead of
    accumulating dirs under the repo root. Settings/profile come from
    ``tests/conftest.py`` via the ``"rch"`` Hypothesis profile.
    """
    agent_home = tmp_path_factory.mktemp("home")
    (agent_home / ".claude").mkdir(parents=True)
    settings_path = agent_home / ".claude" / "settings.json"
    settings_path.write_text(json.dumps(payload), encoding="utf-8")

    deduplicate_hooks(agent_home)
    after_first = settings_path.read_text(encoding="utf-8")
    deduplicate_hooks(agent_home)
    after_second = settings_path.read_text(encoding="utf-8")

    assert after_first == after_second


# ---------------------------------------------------------------------------
# deduplicate_hooks — defensive contracts (audit F1.2)
#
# `_load_json` already tolerates missing files, malformed JSON, and zero-byte
# files (returns ``{}``), so `deduplicate_hooks` cannot crash the install flow
# on these inputs. These tests lock that contract so a future refactor of
# `_load_json` cannot silently break the agent install path.
# ---------------------------------------------------------------------------


def test_deduplicate_hooks_missing_settings_file_returns_zero() -> None:
    """Fresh-install case: no settings.json yet."""
    agent_home = _tmp_dir() / "home"
    (agent_home / ".claude").mkdir(parents=True)
    # Deliberately do NOT create settings.json.
    assert deduplicate_hooks(agent_home) == {"removed": 0}


def test_deduplicate_hooks_zero_byte_settings_returns_zero() -> None:
    """Power-loss / partial-write produces a zero-byte settings.json."""
    agent_home = _tmp_dir() / "home"
    (agent_home / ".claude").mkdir(parents=True)
    (agent_home / ".claude" / "settings.json").write_text("", encoding="utf-8")
    assert deduplicate_hooks(agent_home) == {"removed": 0}


def test_deduplicate_hooks_malformed_json_returns_zero() -> None:
    """Merge-conflict markers / hand-edited typos produce malformed JSON.

    Contract: must return cleanly so ``install_global_hooks`` can recover
    instead of raising ``json.JSONDecodeError`` up to the agent install flow.
    """
    agent_home = _tmp_dir() / "home"
    (agent_home / ".claude").mkdir(parents=True)
    (agent_home / ".claude" / "settings.json").write_text(
        "{not valid json <<<<<", encoding="utf-8"
    )
    assert deduplicate_hooks(agent_home) == {"removed": 0}


# ===========================================================================
# Settings.json migration tests (issue #74).
#
# Real fixture files under ``tests/fixtures/migrations/`` represent
# settings.json shapes from earlier rch versions. The contract tested here
# is "upgrade preserves user customisations": after running the current
# install on top of an old settings.json, every user-authored hook must
# still appear in the result. Lives in test_installer.py (not a separate
# test_migration.py) per grep-locality reasoning — migration is a property
# OF install, not a separate concern.
# ===========================================================================


import json as _json_for_migration  # local alias to avoid colliding with module-top imports
from typing import Iterable as _Iterable

import pytest as _pytest_for_migration

try:
    from hypothesis import given as _hyp_given
    from hypothesis import strategies as _st
    from hypothesis import settings as _hyp_settings
    _HYPOTHESIS_AVAILABLE = True
except ImportError:  # pragma: no cover - hypothesis is in dev deps
    _HYPOTHESIS_AVAILABLE = False


_FIXTURES_DIR = ROOT / "tests" / "fixtures" / "migrations"


def _all_user_hook_commands(settings: dict) -> set[str]:
    """Return the set of every hook command string present in ``settings``.

    User commands are anything NOT containing the rch skill scripts marker —
    the install/uninstall logic uses the same marker rule, so the set we
    extract here is exactly what 'must survive upgrade' means.
    """
    commands: set[str] = set()
    for groups in (settings.get("hooks", {}) or {}).values():
        if not isinstance(groups, list):
            continue
        for group in groups:
            if not isinstance(group, dict):
                continue
            for h in group.get("hooks", []) or []:
                if isinstance(h, dict):
                    cmd = h.get("command", "")
                    if cmd:
                        commands.add(cmd)
    return commands


def _user_only_hooks(settings: dict, marker: str = "/skills/context-handoff-hooks/scripts/") -> set[str]:
    return {c for c in _all_user_hook_commands(settings) if marker not in c}


@_pytest_for_migration.mark.parametrize(
    "fixture_name",
    ["v0_5_settings.json", "v0_6_settings.json"],
)
def test_migration_install_preserves_user_hooks(fixture_name: str) -> None:
    """Re-installing on top of an older settings.json keeps user hooks intact."""
    agent_home = _tmp_dir() / "home"
    (agent_home / ".claude").mkdir(parents=True)
    settings_path = agent_home / ".claude" / "settings.json"
    fixture_data = _json_for_migration.loads(
        (_FIXTURES_DIR / fixture_name).read_text(encoding="utf-8")
    )
    settings_path.write_text(
        _json_for_migration.dumps(fixture_data, indent=2),
        encoding="utf-8",
    )
    user_hooks_before = _user_only_hooks(fixture_data)

    install_global_hooks(agent_home)

    after = _json_for_migration.loads(settings_path.read_text(encoding="utf-8"))
    user_hooks_after = _user_only_hooks(after)
    assert user_hooks_before.issubset(user_hooks_after), (
        f"User hooks dropped during {fixture_name} migration: "
        f"{user_hooks_before - user_hooks_after}"
    )
    # And install is idempotent — second install adds nothing.
    install_global_hooks(agent_home)
    after_2 = _json_for_migration.loads(settings_path.read_text(encoding="utf-8"))
    assert after == after_2, "Second install changed settings.json (not idempotent)"


def test_migration_install_preserves_top_level_keys() -> None:
    """Non-hooks keys (e.g. ``permissions``) survive the install merge."""
    agent_home = _tmp_dir() / "home"
    (agent_home / ".claude").mkdir(parents=True)
    settings_path = agent_home / ".claude" / "settings.json"
    fixture_data = _json_for_migration.loads(
        (_FIXTURES_DIR / "v0_5_settings.json").read_text(encoding="utf-8")
    )
    settings_path.write_text(
        _json_for_migration.dumps(fixture_data, indent=2),
        encoding="utf-8",
    )

    install_global_hooks(agent_home)

    after = _json_for_migration.loads(settings_path.read_text(encoding="utf-8"))
    assert "permissions" in after
    assert after["permissions"] == fixture_data["permissions"]


def test_migration_empty_settings_file_handled() -> None:
    """Empty bytes ≠ malformed JSON — install must initialise cleanly."""
    agent_home = _tmp_dir() / "home"
    (agent_home / ".claude").mkdir(parents=True)
    (agent_home / ".claude" / "settings.json").write_text("", encoding="utf-8")
    result = install_global_hooks(agent_home)
    assert result == {"settings.json": "installed"}
    after = _json_for_migration.loads(
        (agent_home / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    assert "hooks" in after


# ---------------------------------------------------------------------------
# Hypothesis property: arbitrary 0.5-shaped settings always preserve user hooks.
# Uses the "rch" profile from tests/conftest.py (max_examples=50, derandomized).
# ---------------------------------------------------------------------------

if _HYPOTHESIS_AVAILABLE:
    _hook_command = _st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz_-/. ",
        min_size=4,
        max_size=60,
    ).filter(lambda s: "/skills/context-handoff-hooks/scripts/" not in s)
    _hook_event = _st.dictionaries(
        keys=_st.sampled_from(["matcher"]),
        values=_st.text(min_size=0, max_size=12),
        min_size=0,
        max_size=1,
    )

    @_st.composite
    def _arbitrary_v05_settings(draw):
        # A 0.5-shaped settings.json with a list of user-authored hooks
        # under various event keys. We deliberately use only canonical
        # event names because install merges by key — surfacing
        # arbitrary keys here would be testing a different invariant.
        event_names = draw(_st.lists(
            _st.sampled_from([
                "SessionStart", "PreCompact", "PostCompact", "SessionEnd",
                "UserPromptSubmit",
            ]),
            min_size=1,
            max_size=5,
            unique=True,
        ))
        cmds_per_event = draw(_st.lists(
            _st.lists(_hook_command, min_size=1, max_size=4),
            min_size=len(event_names),
            max_size=len(event_names),
        ))
        hooks: dict = {}
        for name, cmds in zip(event_names, cmds_per_event):
            hooks[name] = [
                {
                    "matcher": "",
                    "hooks": [{"type": "command", "command": cmd, "timeout": 10} for cmd in cmds],
                }
            ]
        return {"hooks": hooks, "permissions": {"allow": ["Read"]}}

    @_hyp_given(settings=_arbitrary_v05_settings())
    @_hyp_settings(max_examples=50)
    def test_property_install_preserves_arbitrary_user_hooks(settings: dict) -> None:
        """Property: every user hook in arbitrary 0.5-shape survives install."""
        agent_home = _tmp_dir() / "home"
        (agent_home / ".claude").mkdir(parents=True)
        settings_path = agent_home / ".claude" / "settings.json"
        settings_path.write_text(
            _json_for_migration.dumps(settings, indent=2),
            encoding="utf-8",
        )
        before = _user_only_hooks(settings)

        install_global_hooks(agent_home)

        after = _json_for_migration.loads(settings_path.read_text(encoding="utf-8"))
        assert before.issubset(_user_only_hooks(after))


# ===========================================================================
# Planner / dry-run sanity tests (issue #74 Critic B non-budge).
#
# The dry-run guarantee ("never writes to disk") is verified MECHANICALLY
# by monkeypatching the underlying write to raise. If any planning function
# silently writes, the test crashes loud.
# ===========================================================================


from repo_context_hooks.platforms import runtime as _runtime
from repo_context_hooks.platforms.runtime import (
    plan_deduplicate_hooks,
    plan_global_hooks,
    plan_uninstall_global_hooks,
    SettingsPlan,
)


def test_plan_global_hooks_returns_diff_without_writing(
    tmp_path: Path, monkeypatch: _pytest_for_migration.MonkeyPatch
) -> None:
    """plan_global_hooks must NEVER call _save_json — verified by monkeypatch."""
    agent_home = tmp_path / "home"
    (agent_home / ".claude").mkdir(parents=True)
    monkeypatch.setattr(
        _runtime,
        "_save_json",
        lambda *a, **k: pytest.fail("plan_global_hooks called _save_json"),
    )

    plan = plan_global_hooks(agent_home)
    assert isinstance(plan, SettingsPlan)
    assert plan.action == "install"
    assert plan.diff
    # And no settings.json was written.
    assert not (agent_home / ".claude" / "settings.json").exists()


def test_plan_uninstall_global_hooks_returns_diff_without_writing(
    tmp_path: Path, monkeypatch: _pytest_for_migration.MonkeyPatch
) -> None:
    agent_home = tmp_path / "home"
    (agent_home / ".claude").mkdir(parents=True)
    # Seed a settings.json with rch hooks so uninstall has something to remove.
    install_global_hooks(agent_home)
    snapshot = (agent_home / ".claude" / "settings.json").read_text(encoding="utf-8")
    monkeypatch.setattr(
        _runtime,
        "_save_json",
        lambda *a, **k: pytest.fail("plan_uninstall called _save_json"),
    )

    plan = plan_uninstall_global_hooks(agent_home)
    assert plan.action == "uninstall"
    assert plan.diff
    # File contents unchanged.
    assert (agent_home / ".claude" / "settings.json").read_text(encoding="utf-8") == snapshot


def test_plan_deduplicate_hooks_returns_diff_without_writing(
    tmp_path: Path, monkeypatch: _pytest_for_migration.MonkeyPatch
) -> None:
    agent_home = tmp_path / "home"
    (agent_home / ".claude").mkdir(parents=True)
    # Build a settings.json with deliberate duplicates.
    install_global_hooks(agent_home)
    settings_path = agent_home / ".claude" / "settings.json"
    data = _json_for_migration.loads(settings_path.read_text(encoding="utf-8"))
    # Duplicate the SessionStart group.
    data["hooks"]["SessionStart"].append(data["hooks"]["SessionStart"][0])
    settings_path.write_text(_json_for_migration.dumps(data, indent=2), encoding="utf-8")
    snapshot = settings_path.read_text(encoding="utf-8")
    monkeypatch.setattr(
        _runtime,
        "_save_json",
        lambda *a, **k: pytest.fail("plan_deduplicate called _save_json"),
    )

    plan = plan_deduplicate_hooks(agent_home)
    assert plan.action == "install"
    assert plan.statuses["removed"] > 0
    assert settings_path.read_text(encoding="utf-8") == snapshot


def test_plan_global_hooks_skip_when_already_installed(tmp_path: Path) -> None:
    agent_home = tmp_path / "home"
    (agent_home / ".claude").mkdir(parents=True)
    install_global_hooks(agent_home)
    plan = plan_global_hooks(agent_home)
    assert plan.action == "skip"
    assert plan.diff == ()
    assert plan.statuses == {"settings.json": "skipped"}
