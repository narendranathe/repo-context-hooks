from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from repo_context_hooks.doctor import diagnose_platform
from repo_context_hooks.installer import install_platform

ROOT = Path(__file__).resolve().parents[1]


def _tmp_dir() -> Path:
    base = ROOT / ".tmp-tests"
    base.mkdir(exist_ok=True)
    path = base / uuid4().hex
    path.mkdir()
    return path


def _write_repo_contract(repo: Path) -> None:
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    specs_dir = repo / "specs"
    specs_dir.mkdir()
    (specs_dir / "README.md").write_text("# Specs\n", encoding="utf-8")


def test_doctor_reports_missing_cursor_rule() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_repo_contract(repo)

    report = diagnose_platform("cursor", repo_root=repo, home=tmp_path / "home")

    assert report.ok is False
    assert any(
        item.endswith(".cursor/rules/repo-context-continuity.mdc")
        for item in report.missing
    )
    assert "MISSING" in report.render()


def test_doctor_reports_installed_codex_contract() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract(repo)

    home = tmp_path / "home"
    install_platform("codex", repo_root=repo, home=home)

    report = diagnose_platform("codex", repo_root=repo, home=home)

    assert report.ok is True
    assert any(item.endswith("AGENTS.md") for item in report.present)
    assert any(".codex/skills" in item for item in report.present)


def test_doctor_rejects_placeholder_codex_agents_file() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract(repo)

    home = tmp_path / "home"
    install_platform("codex", repo_root=repo, home=home)
    (repo / "AGENTS.md").write_text("placeholder\n", encoding="utf-8")

    report = diagnose_platform("codex", repo_root=repo, home=home)

    assert report.ok is False
    assert any(item.endswith("AGENTS.md") for item in report.invalid)
    assert "INVALID" in report.render()
