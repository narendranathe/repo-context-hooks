"""Tests for measure experiment start / finish / status commands."""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from uuid import uuid4

import pytest

from repo_context_hooks.cli import _measure
from repo_context_hooks.repo_contract import init_repo_contract
from repo_context_hooks.telemetry import (
    experiment_finish,
    experiment_start,
    experiment_status,
    measure_impact,
)

ROOT = Path(__file__).resolve().parents[1]


def _tmp_dir() -> Path:
    base = ROOT / ".tmp-tests"
    base.mkdir(exist_ok=True)
    path = base / uuid4().hex
    path.mkdir()
    return path


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo_contract(repo)
    return repo


# ---------------------------------------------------------------------------
# experiment_start
# ---------------------------------------------------------------------------


def test_experiment_start_creates_before_json(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "experiment"

    before_path = experiment_start(repo, exp_dir)

    assert before_path == exp_dir / "before.json"
    assert before_path.exists()
    data = json.loads(before_path.read_text(encoding="utf-8"))
    for key in ("timestamp", "score", "baseline", "uplift", "observed_events",
                "event_counts", "lifecycle_coverage", "contract_files_present"):
        assert key in data, f"Missing key: {key}"


def test_experiment_start_creates_experiment_dir(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "nonexistent" / "subdir"

    experiment_start(repo, exp_dir)

    assert exp_dir.exists()


def test_experiment_start_contract_files_present_is_dict_of_bools(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "experiment"

    experiment_start(repo, exp_dir)

    data = json.loads((exp_dir / "before.json").read_text(encoding="utf-8"))
    cfp = data["contract_files_present"]
    assert isinstance(cfp, dict)
    assert all(isinstance(v, bool) for v in cfp.values())


def test_experiment_start_fails_if_before_json_already_exists(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "experiment"

    experiment_start(repo, exp_dir)

    with pytest.raises(FileExistsError, match="experiment is already in progress"):
        experiment_start(repo, exp_dir)


def test_experiment_start_prints_guidance(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "experiment"

    experiment_start(repo, exp_dir)

    out = capsys.readouterr().out
    assert "experiment finish" in out


# ---------------------------------------------------------------------------
# experiment_finish
# ---------------------------------------------------------------------------


def test_experiment_finish_creates_after_json(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "experiment"

    experiment_start(repo, exp_dir)
    result = experiment_finish(repo, exp_dir)

    after_path = exp_dir / "after.json"
    assert after_path.exists()
    data = json.loads(after_path.read_text(encoding="utf-8"))
    for key in ("timestamp", "score", "baseline", "uplift", "observed_events",
                "event_counts", "lifecycle_coverage", "contract_files_present"):
        assert key in data, f"Missing key: {key}"


def test_experiment_finish_returns_comparison_dict(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "experiment"

    experiment_start(repo, exp_dir)
    result = experiment_finish(repo, exp_dir)

    for key in ("before", "after", "score_delta", "uplift_delta", "events_delta", "new_files", "summary"):
        assert key in result, f"Missing key: {key}"
    assert isinstance(result["score_delta"], int)
    assert isinstance(result["new_files"], list)
    assert isinstance(result["summary"], str)


def test_experiment_finish_fails_if_before_json_missing(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "experiment"
    exp_dir.mkdir()

    with pytest.raises(FileNotFoundError, match="experiment start"):
        experiment_finish(repo, exp_dir)


def test_experiment_finish_score_delta_is_correct(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "experiment"

    experiment_start(repo, exp_dir)
    result = experiment_finish(repo, exp_dir)

    before_score = result["before"]["score"]
    after_score = result["after"]["score"]
    assert result["score_delta"] == after_score - before_score


def test_experiment_finish_new_files_detects_additions(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "experiment"

    # Start before any extra files
    experiment_start(repo, exp_dir)

    # CLAUDE.md is tracked by contract_signals but not created by init_repo_contract
    claude_file = repo / "CLAUDE.md"
    claude_file.write_text("# Project instructions\n", encoding="utf-8")

    result = experiment_finish(repo, exp_dir)

    assert "CLAUDE.md" in result["new_files"]


def test_experiment_finish_summary_never_says_productivity(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "experiment"

    experiment_start(repo, exp_dir)
    result = experiment_finish(repo, exp_dir)

    assert "productivity" not in result["summary"].lower(), (
        "Claim boundary violation: summary must not mention 'productivity'"
    )


def test_experiment_finish_summary_mentions_continuity_or_contract(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "experiment"

    experiment_start(repo, exp_dir)
    result = experiment_finish(repo, exp_dir)

    summary_lower = result["summary"].lower()
    assert "continuity" in summary_lower or "contract" in summary_lower, (
        "Summary should use 'continuity' or 'contract' terminology"
    )


# ---------------------------------------------------------------------------
# experiment_status
# ---------------------------------------------------------------------------


def test_experiment_status_not_started(tmp_path: Path) -> None:
    exp_dir = tmp_path / "experiment"
    exp_dir.mkdir()

    status = experiment_status(exp_dir)

    assert status["state"] == "not_started"
    assert "experiment start" in status["message"]


def test_experiment_status_in_progress(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "experiment"

    experiment_start(repo, exp_dir)
    status = experiment_status(exp_dir)

    assert status["state"] == "in_progress"
    assert "in progress" in status["message"].lower()


def test_experiment_status_finished(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "experiment"

    experiment_start(repo, exp_dir)
    experiment_finish(repo, exp_dir)
    status = experiment_status(exp_dir)

    assert status["state"] == "finished"
    assert "complete" in status["message"].lower()


def test_experiment_status_nonexistent_dir(tmp_path: Path) -> None:
    exp_dir = tmp_path / "does-not-exist"

    status = experiment_status(exp_dir)

    assert status["state"] == "not_started"


# ---------------------------------------------------------------------------
# CLI integration: _measure() dispatch
# ---------------------------------------------------------------------------


def test_cli_measure_experiment_start(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "exp"

    args = Namespace(
        repo_root=str(repo),
        positional_args=["experiment", "start"],
        experiment_dir=str(exp_dir),
        clean_ghosts=False,
        forecast=False,
        branches=False,
        json=False,
        badge=False,
        badge_out=None,
        snapshot_dir=None,
        open=False,
        dry_run=True,
    )
    rc = _measure(args)

    assert rc == 0
    assert (exp_dir / "before.json").exists()
    out = capsys.readouterr().out
    assert "before.json" in out.lower() or "experiment" in out.lower()


def test_cli_measure_experiment_finish(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "exp"

    # start first
    start_args = Namespace(
        repo_root=str(repo),
        positional_args=["experiment", "start"],
        experiment_dir=str(exp_dir),
        clean_ghosts=False,
        forecast=False,
        branches=False,
        json=False,
        badge=False,
        badge_out=None,
        snapshot_dir=None,
        open=False,
        dry_run=True,
    )
    assert _measure(start_args) == 0
    capsys.readouterr()

    finish_args = Namespace(
        repo_root=str(repo),
        positional_args=["experiment", "finish"],
        experiment_dir=str(exp_dir),
        clean_ghosts=False,
        forecast=False,
        branches=False,
        json=False,
        badge=False,
        badge_out=None,
        snapshot_dir=None,
        open=False,
        dry_run=True,
    )
    rc = _measure(finish_args)

    assert rc == 0
    assert (exp_dir / "after.json").exists()
    out = capsys.readouterr().out
    assert "complete" in out.lower() or "after" in out.lower()


def test_cli_measure_experiment_status(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "exp"

    args = Namespace(
        repo_root=str(repo),
        positional_args=["experiment", "status"],
        experiment_dir=str(exp_dir),
        clean_ghosts=False,
        forecast=False,
        branches=False,
        json=False,
        badge=False,
        badge_out=None,
        snapshot_dir=None,
        open=False,
        dry_run=True,
    )
    rc = _measure(args)

    assert rc == 0
    out = capsys.readouterr().out
    assert "experiment start" in out


def test_cli_measure_experiment_start_fails_gracefully_when_already_exists(
    tmp_path: Path, capsys
) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "exp"

    args = Namespace(
        repo_root=str(repo),
        positional_args=["experiment", "start"],
        experiment_dir=str(exp_dir),
        clean_ghosts=False,
        forecast=False,
        branches=False,
        json=False,
        badge=False,
        badge_out=None,
        snapshot_dir=None,
        open=False,
        dry_run=True,
    )
    assert _measure(args) == 0
    capsys.readouterr()

    rc = _measure(args)
    assert rc == 1
    out = capsys.readouterr().out
    assert "Error" in out or "already" in out.lower()


def test_cli_measure_experiment_finish_fails_gracefully_with_no_start(
    tmp_path: Path, capsys
) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "exp"

    args = Namespace(
        repo_root=str(repo),
        positional_args=["experiment", "finish"],
        experiment_dir=str(exp_dir),
        clean_ghosts=False,
        forecast=False,
        branches=False,
        json=False,
        badge=False,
        badge_out=None,
        snapshot_dir=None,
        open=False,
        dry_run=True,
    )
    rc = _measure(args)

    assert rc == 1
    out = capsys.readouterr().out
    assert "Error" in out or "experiment start" in out


def test_cli_measure_experiment_unknown_subcommand(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    exp_dir = tmp_path / "exp"

    args = Namespace(
        repo_root=str(repo),
        positional_args=["experiment", "banana"],
        experiment_dir=str(exp_dir),
        clean_ghosts=False,
        forecast=False,
        branches=False,
        json=False,
        badge=False,
        badge_out=None,
        snapshot_dir=None,
        open=False,
        dry_run=True,
    )
    rc = _measure(args)

    assert rc == 1
    out = capsys.readouterr().out
    assert "Unknown" in out or "banana" in out


def test_cli_measure_experiment_default_dir_uses_repo_root(tmp_path: Path, capsys) -> None:
    """When --experiment-dir is not given, default should be <repo_root>/.repo-context-hooks/experiment."""
    repo = _make_repo(tmp_path)

    args = Namespace(
        repo_root=str(repo),
        positional_args=["experiment", "start"],
        experiment_dir=None,
        clean_ghosts=False,
        forecast=False,
        branches=False,
        json=False,
        badge=False,
        badge_out=None,
        snapshot_dir=None,
        open=False,
        dry_run=True,
    )
    rc = _measure(args)

    assert rc == 0
    assert (repo / ".repo-context-hooks" / "experiment" / "before.json").exists()
    capsys.readouterr()
