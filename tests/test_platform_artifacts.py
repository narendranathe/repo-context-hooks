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
