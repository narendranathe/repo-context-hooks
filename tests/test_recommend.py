from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from repo_context_hooks.recommend import recommend_setup
from repo_context_hooks.repo_contract import init_repo_contract


ROOT = Path(__file__).resolve().parents[1]


def _tmp_dir() -> Path:
    base = ROOT / ".tmp-tests"
    base.mkdir(exist_ok=True)
    path = base / uuid4().hex
    path.mkdir()
    return path


def test_recommend_prefers_init_when_repo_contract_is_missing() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()

    report = recommend_setup(repo)

    rendered = report.render()
    assert "repo-context-hooks init" in rendered
    assert "repo-context-hooks doctor" in rendered


def test_recommend_defaults_to_claude_for_repo_contract_only_repo() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo_contract(repo)

    report = recommend_setup(repo)

    rendered = report.render()
    assert "1. claude" in rendered.lower()
    assert "repo-context-hooks install --platform claude" in rendered


def test_recommend_exposes_json_contract() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo_contract(repo)

    payload = recommend_setup(repo).to_dict()

    assert payload["repo_contract_ok"] is True
    assert payload["recommendations"][0]["platform_id"] == "claude"
    assert payload["recommendations"][0]["next_command"] == (
        "repo-context-hooks install --platform claude --repo-root ."
    )


def test_recommend_prefers_explicit_platform_signal() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo_contract(repo)
    (repo / "replit.md").write_text("# Replit\n", encoding="utf-8")

    report = recommend_setup(repo)

    rendered = report.render().lower()
    assert "1. replit" in rendered
    assert "detected repo signal" in rendered
