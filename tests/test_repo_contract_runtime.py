from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from repo_context_hooks.repo_contract import init_repo_contract


ROOT = Path(__file__).resolve().parents[1]


def _tmp_dir() -> Path:
    base = ROOT / ".tmp-tests"
    base.mkdir(exist_ok=True)
    path = base / uuid4().hex
    path.mkdir()
    return path


def test_init_repo_contract_creates_missing_files() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()

    statuses = init_repo_contract(repo)

    assert statuses["README.md"] == "installed"
    assert statuses["specs/README.md"] == "installed"
    assert statuses["UBIQUITOUS_LANGUAGE.md"] == "installed"
    assert statuses["AGENTS.md"] == "installed"

    assert (repo / "README.md").exists()
    assert (repo / "specs" / "README.md").exists()
    assert (repo / "UBIQUITOUS_LANGUAGE.md").exists()
    assert (repo / "AGENTS.md").exists()


def test_init_repo_contract_preserves_existing_readme_without_force() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    readme = repo / "README.md"
    readme.write_text("# Custom\n\nKeep me.\n", encoding="utf-8")

    statuses = init_repo_contract(repo, force=False)

    assert statuses["README.md"] == "skipped"
    assert readme.read_text(encoding="utf-8") == "# Custom\n\nKeep me.\n"
