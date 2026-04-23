from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from repo_context_hooks.installer import (
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
    assert supported_platform_ids() == ("claude", "cursor", "codex")


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
    assert "PreToolUse" in settings["hooks"]  # preserved
    assert "SessionStart" in settings["hooks"]  # added
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


def test_install_platform_routes_claude_hooks() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    result = install_platform("claude", repo_root=repo, home=tmp_path / "home")

    assert (repo / ".claude" / "settings.json").exists()
    assert result.repo_statuses["settings.json"] == "installed"


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
