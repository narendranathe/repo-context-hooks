from __future__ import annotations

from repo_context_hooks.installer import bundle_root


def test_bundle_contains_expected_assets() -> None:
    root = bundle_root()
    assert (root / "hooks.json").exists()
    assert (root / "scripts" / "repo_specs_memory.py").exists()
    assert (root / "scripts" / "session_context.py").exists()
    assert (root / "templates" / "replit.md").exists()
    assert (root / "templates" / "windsurf-rule.md").exists()
    assert (root / "templates" / "lovable-project-knowledge.md").exists()
    assert (root / "templates" / "lovable-workspace-knowledge.md").exists()
    assert (root / "templates" / "openclaw-soul.md").exists()
    assert (root / "templates" / "openclaw-user.md").exists()
    assert (root / "templates" / "openclaw-tools.md").exists()
    assert (root / "templates" / "ollama-modelfile").exists()

    skills = root / "skills"
    assert (skills / "context-handoff-hooks" / "SKILL.md").exists()
    assert (skills / "session-start-context-loader" / "SKILL.md").exists()
    assert (skills / "precompact-checkpoint" / "SKILL.md").exists()
    assert (skills / "postcompact-context-reload" / "SKILL.md").exists()


def test_context_handoff_skill_scripts_include_telemetry_recording() -> None:
    root = bundle_root()
    for relative_path in (
        "scripts/repo_specs_memory.py",
        "scripts/session_context.py",
        "skills/context-handoff-hooks/scripts/repo_specs_memory.py",
        "skills/context-handoff-hooks/scripts/session_context.py",
    ):
        text = (root / relative_path).read_text(encoding="utf-8")
        assert "record_event" in text
        assert "repo_context_hooks.telemetry" in text


def test_context_handoff_skill_installer_ignores_repo_local_telemetry() -> None:
    installer = (
        bundle_root()
        / "skills"
        / "context-handoff-hooks"
        / "scripts"
        / "install_hooks.py"
    )
    text = installer.read_text(encoding="utf-8")
    assert ".repo-context-hooks/" in text
    assert "ensure_gitignore" in text
