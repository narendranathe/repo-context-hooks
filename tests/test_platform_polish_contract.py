from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_replit_and_windsurf_templates_include_polish_guidance() -> None:
    replit = (ROOT / "repo_context_hooks" / "bundle" / "templates" / "replit.md").read_text(
        encoding="utf-8"
    )
    windsurf = (
        ROOT / "repo_context_hooks" / "bundle" / "templates" / "windsurf-rule.md"
    ).read_text(encoding="utf-8")

    assert "Resume Checklist" in replit
    assert "last completed change" in replit
    assert "next step" in replit

    assert "repo-specific continuity only" in windsurf
    assert "team-wide or personal Cascade rules" in windsurf


def test_lovable_and_openclaw_templates_include_safe_sync_guidance() -> None:
    lovable_project = (
        ROOT / "repo_context_hooks" / "bundle" / "templates" / "lovable-project-knowledge.md"
    ).read_text(encoding="utf-8")
    lovable_workspace = (
        ROOT / "repo_context_hooks" / "bundle" / "templates" / "lovable-workspace-knowledge.md"
    ).read_text(encoding="utf-8")
    openclaw_soul = (
        ROOT / "repo_context_hooks" / "bundle" / "templates" / "openclaw-soul.md"
    ).read_text(encoding="utf-8")
    openclaw_user = (
        ROOT / "repo_context_hooks" / "bundle" / "templates" / "openclaw-user.md"
    ).read_text(encoding="utf-8")
    openclaw_tools = (
        ROOT / "repo_context_hooks" / "bundle" / "templates" / "openclaw-tools.md"
    ).read_text(encoding="utf-8")

    assert "re-paste it into Lovable Project Knowledge" in lovable_project
    assert "hosted field is a mirror" in lovable_project
    assert "re-paste it into Lovable Workspace Knowledge" in lovable_workspace
    assert "repo-owned workspace export" in lovable_workspace

    assert "private workspace" in openclaw_soul
    assert "private workspace" in openclaw_user
    assert "private workspace" in openclaw_tools


def test_ollama_and_kimi_playbooks_include_examples() -> None:
    ollama = (
        ROOT / "repo_context_hooks" / "bundle" / "templates" / "ollama-modelfile"
    ).read_text(encoding="utf-8")
    playbooks = (ROOT / "docs" / "platform-playbooks.md").read_text(encoding="utf-8")

    assert "safe smoke test" in ollama.lower()
    assert "agent wrapper" in ollama.lower()

    assert "### Restart checklist" in playbooks
    assert "### Layering example" in playbooks
    assert "### Resync loop" in playbooks
    assert "### Safe split" in playbooks
    assert "### Safe smoke test" in playbooks
    assert "### `/init` merge example" in playbooks
