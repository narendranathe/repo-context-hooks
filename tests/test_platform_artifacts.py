from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from repo_context_hooks.installer import install_platform

ROOT = Path(__file__).resolve().parents[1]


def _tmp_dir() -> Path:
    base = ROOT / ".tmp-tests"
    base.mkdir(exist_ok=True)
    path = base / uuid4().hex
    path.mkdir()
    return path


def _write_repo_contract_basics(repo: Path) -> None:
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    specs_dir = repo / "specs"
    specs_dir.mkdir()
    (specs_dir / "README.md").write_text("# Specs\n", encoding="utf-8")


def test_install_cursor_writes_rule_and_agents() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract_basics(repo)

    result = install_platform("cursor", repo_root=repo, home=tmp_path / "home")

    rule_path = repo / ".cursor" / "rules" / "repo-context-continuity.mdc"
    agents_path = repo / "AGENTS.md"

    assert rule_path.exists()
    assert agents_path.exists()
    assert "AGENTS.md" in rule_path.read_text(encoding="utf-8")
    assert "README.md" in agents_path.read_text(encoding="utf-8")
    assert "specs/README.md" in agents_path.read_text(encoding="utf-8")
    assert "Cursor" in result.summary
    assert "partial" in result.summary.lower()


def test_install_codex_preserves_agents_without_installing_skills() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract_basics(repo)
    agents_path = repo / "AGENTS.md"
    agents_path.write_text("keep me\n", encoding="utf-8")

    install_platform("codex", repo_root=repo, home=tmp_path / "home")

    assert agents_path.read_text(encoding="utf-8") == "keep me\n"
    assert not (tmp_path / "home" / ".codex" / "skills").exists()


def test_install_replit_writes_replit_md_and_agents() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract_basics(repo)

    result = install_platform("replit", repo_root=repo, home=tmp_path / "home")

    replit_path = repo / "replit.md"
    agents_path = repo / "AGENTS.md"

    assert replit_path.exists()
    assert agents_path.exists()
    replit_text = replit_path.read_text(encoding="utf-8")
    assert "README.md" in replit_text
    assert "specs/README.md" in replit_text
    assert "AGENTS.md" in replit_text
    assert "Replit" in result.summary
    assert "partial" in result.summary.lower()
    assert result.manual_steps


def test_install_windsurf_writes_rule_and_agents() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract_basics(repo)

    result = install_platform("windsurf", repo_root=repo, home=tmp_path / "home")

    rule_path = repo / ".windsurf" / "rules" / "repo-context-continuity.md"
    agents_path = repo / "AGENTS.md"

    assert rule_path.exists()
    assert agents_path.exists()
    rule_text = rule_path.read_text(encoding="utf-8")
    assert "README.md" in rule_text
    assert "specs/README.md" in rule_text
    assert "AGENTS.md" in rule_text
    assert "Windsurf" in result.summary
    assert "partial" in result.summary.lower()


def test_install_lovable_writes_knowledge_exports_and_agents() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract_basics(repo)

    result = install_platform("lovable", repo_root=repo, home=tmp_path / "home")

    project_knowledge = repo / ".lovable" / "project-knowledge.md"
    workspace_knowledge = repo / ".lovable" / "workspace-knowledge.md"
    agents_path = repo / "AGENTS.md"

    assert project_knowledge.exists()
    assert workspace_knowledge.exists()
    assert agents_path.exists()
    assert "README.md" in project_knowledge.read_text(encoding="utf-8")
    assert "specs/README.md" in project_knowledge.read_text(encoding="utf-8")
    assert "AGENTS.md" in workspace_knowledge.read_text(encoding="utf-8")
    assert "Lovable" in result.summary
    assert any("project knowledge" in step.lower() for step in result.manual_steps)


def test_install_openclaw_writes_workspace_files_and_agents() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract_basics(repo)

    result = install_platform("openclaw", repo_root=repo, home=tmp_path / "home")

    agents_path = repo / "AGENTS.md"
    soul_path = repo / "SOUL.md"
    user_path = repo / "USER.md"
    tools_path = repo / "TOOLS.md"

    assert agents_path.exists()
    assert soul_path.exists()
    assert user_path.exists()
    assert tools_path.exists()
    assert "README.md" in soul_path.read_text(encoding="utf-8")
    assert "specs/README.md" in user_path.read_text(encoding="utf-8")
    assert "AGENTS.md" in tools_path.read_text(encoding="utf-8")
    assert "OpenClaw" in result.summary
    assert any("workspace" in step.lower() for step in result.manual_steps)


def test_install_ollama_writes_modelfile_and_agents() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract_basics(repo)

    result = install_platform("ollama", repo_root=repo, home=tmp_path / "home")

    agents_path = repo / "AGENTS.md"
    modelfile_path = repo / "Modelfile.repo-context"

    assert agents_path.exists()
    assert modelfile_path.exists()
    modelfile = modelfile_path.read_text(encoding="utf-8")
    assert "FROM" in modelfile
    assert "SYSTEM" in modelfile
    assert "README.md" in modelfile
    assert "specs/README.md" in modelfile
    assert "AGENTS.md" in modelfile
    assert "Ollama" in result.summary
    assert any("ollama create" in step.lower() for step in result.manual_steps)


def test_install_kimi_writes_agents_only() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract_basics(repo)

    result = install_platform("kimi", repo_root=repo, home=tmp_path / "home")

    agents_path = repo / "AGENTS.md"

    assert agents_path.exists()
    agents_text = agents_path.read_text(encoding="utf-8")
    assert "README.md" in agents_text
    assert "specs/README.md" in agents_text
    assert "Kimi" in result.summary
    assert any("/init" in step for step in result.manual_steps)
