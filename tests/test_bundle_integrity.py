from __future__ import annotations

from repo_context_hooks.installer import bundle_root


def test_bundle_contains_expected_assets() -> None:
    root = bundle_root()
    assert (root / "hooks.json").exists()
    assert (root / "scripts" / "repo_specs_memory.py").exists()
    assert (root / "scripts" / "session_context.py").exists()
    assert (root / "templates" / "replit.md").exists()

    skills = root / "skills"
    assert (skills / "context-handoff-hooks" / "SKILL.md").exists()
    assert (skills / "session-start-context-loader" / "SKILL.md").exists()
    assert (skills / "precompact-checkpoint" / "SKILL.md").exists()
    assert (skills / "postcompact-context-reload" / "SKILL.md").exists()
