from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest

from repo_context_hooks.telemetry import (
    auto_commit_snapshot,
    clear_session_state,
    is_sampled,
    record_event,
    session_id,
)

ROOT = Path(__file__).resolve().parents[1]


def _tmp_dir() -> Path:
    base = ROOT / ".tmp-tests"
    base.mkdir(exist_ok=True)
    path = base / uuid4().hex
    path.mkdir()
    return path


# ---------------------------------------------------------------------------
# Issue #36: session_id() + record_event includes session_id
# ---------------------------------------------------------------------------


def test_session_id_generates_uuid_and_persists_to_file(monkeypatch) -> None:
    tmp = _tmp_dir()
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_SESSION_ID", raising=False)

    first = session_id(tmp)
    second = session_id(tmp)

    assert first == second, "same session must return same ID"
    assert len(first) > 8, "session ID must be non-trivial"

    session_file = tmp / ".repo-context-hooks" / "current-session-id"
    assert session_file.exists(), "session ID must be persisted to file"
    assert session_file.read_text(encoding="utf-8").strip() == first


def test_session_id_respects_env_var_override(monkeypatch) -> None:
    tmp = _tmp_dir()
    monkeypatch.setenv("REPO_CONTEXT_HOOKS_SESSION_ID", "test-fixed-id-abc")

    result = session_id(tmp)

    assert result == "test-fixed-id-abc"


def test_session_id_reads_existing_file_on_subsequent_call(monkeypatch) -> None:
    tmp = _tmp_dir()
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_SESSION_ID", raising=False)

    session_dir = tmp / ".repo-context-hooks"
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "current-session-id").write_text("persisted-id-xyz\n", encoding="utf-8")

    result = session_id(tmp)

    assert result == "persisted-id-xyz"


def test_record_event_includes_session_id_field(monkeypatch) -> None:
    tmp = _tmp_dir()
    repo = tmp / "repo"
    repo.mkdir()
    telemetry_base = tmp / "telemetry"
    monkeypatch.setenv("REPO_CONTEXT_HOOKS_SESSION_ID", "test-session-123")

    event_path = record_event(
        repo,
        "session-start",
        source="test",
        telemetry_base=telemetry_base,
    )

    payload = json.loads(event_path.read_text(encoding="utf-8").splitlines()[0])
    assert "session_id" in payload, "record_event must write session_id field"
    assert payload["session_id"] == "test-session-123"


def test_record_event_session_id_is_stable_across_calls(monkeypatch) -> None:
    tmp = _tmp_dir()
    repo = tmp / "repo"
    repo.mkdir()
    telemetry_base = tmp / "telemetry"
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_SESSION_ID", raising=False)

    path1 = record_event(repo, "session-start", source="test", telemetry_base=telemetry_base)
    path2 = record_event(repo, "pre-compact", source="test", telemetry_base=telemetry_base)

    lines = path1.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    id1 = json.loads(lines[0])["session_id"]
    id2 = json.loads(lines[1])["session_id"]
    assert id1 == id2, "both events in the same session must share the same session_id"


# ---------------------------------------------------------------------------
# Issue #37: is_sampled() probabilistic gate
# ---------------------------------------------------------------------------


def test_is_sampled_rate_1_always_returns_true(monkeypatch) -> None:
    tmp = _tmp_dir()
    monkeypatch.setenv("REPO_CONTEXT_HOOKS_SAMPLE_RATE", "1.0")
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_SESSION_ID", raising=False)

    result = is_sampled(tmp)

    assert result is True


def test_is_sampled_rate_0_always_returns_false(monkeypatch) -> None:
    tmp = _tmp_dir()
    monkeypatch.setenv("REPO_CONTEXT_HOOKS_SAMPLE_RATE", "0.0")
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_SESSION_ID", raising=False)

    result = is_sampled(tmp)

    assert result is False


def test_is_sampled_persists_decision_for_session(monkeypatch) -> None:
    tmp = _tmp_dir()
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_SAMPLE_RATE", raising=False)
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_SESSION_ID", raising=False)

    first = is_sampled(tmp)
    second = is_sampled(tmp)

    assert first == second, "sampling decision must be stable within a session"

    sampled_file = tmp / ".repo-context-hooks" / "current-session-sampled"
    assert sampled_file.exists(), "sampling decision must be persisted to file"


def test_is_sampled_reads_existing_decision_file(monkeypatch) -> None:
    tmp = _tmp_dir()
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_SAMPLE_RATE", raising=False)
    session_dir = tmp / ".repo-context-hooks"
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "current-session-sampled").write_text("true", encoding="utf-8")

    result = is_sampled(tmp)

    assert result is True


def test_is_sampled_false_decision_file_returns_false(monkeypatch) -> None:
    tmp = _tmp_dir()
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_SAMPLE_RATE", raising=False)
    session_dir = tmp / ".repo-context-hooks"
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "current-session-sampled").write_text("false", encoding="utf-8")

    result = is_sampled(tmp)

    assert result is False


# ---------------------------------------------------------------------------
# Issue #37: hook script sampling gate via subprocess
# ---------------------------------------------------------------------------


def _make_git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=path, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=path, check=True, capture_output=True,
    )
    return path


HOOK_SCRIPT = (
    ROOT
    / "repo_context_hooks"
    / "bundle"
    / "skills"
    / "context-handoff-hooks"
    / "scripts"
    / "repo_specs_memory.py"
)


def test_hook_script_skips_telemetry_when_not_sampled() -> None:
    tmp = _tmp_dir()
    repo = _make_git_repo(tmp / "repo")
    telemetry_dir = tmp / "telemetry"

    env = {
        **os.environ,
        "REPO_CONTEXT_HOOKS_SAMPLE_RATE": "0.0",
        "REPO_CONTEXT_HOOKS_TELEMETRY_DIR": str(telemetry_dir),
    }
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT), "session-start"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"hook script failed: {result.stderr}"
    events_files = list(telemetry_dir.rglob("events.jsonl"))
    assert len(events_files) == 0, "no telemetry should be written when not sampled"


def test_hook_script_writes_telemetry_when_sampled() -> None:
    tmp = _tmp_dir()
    repo = _make_git_repo(tmp / "repo")
    telemetry_dir = tmp / "telemetry"

    env = {
        **os.environ,
        "REPO_CONTEXT_HOOKS_SAMPLE_RATE": "1.0",
        "REPO_CONTEXT_HOOKS_TELEMETRY_DIR": str(telemetry_dir),
    }
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT), "session-start"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"hook script failed: {result.stderr}"
    events_files = list(telemetry_dir.rglob("events.jsonl"))
    assert len(events_files) == 1, "telemetry must be written when sampled"
    payload = json.loads(events_files[0].read_text(encoding="utf-8").splitlines()[0])
    assert payload["event_name"] == "session-start"
    assert "session_id" in payload


# ---------------------------------------------------------------------------
# Issue #38: session state cleanup and auto_commit_snapshot
# ---------------------------------------------------------------------------


def test_clear_session_state_removes_session_files() -> None:
    tmp = _tmp_dir()
    session_dir = tmp / ".repo-context-hooks"
    session_dir.mkdir(parents=True)
    (session_dir / "current-session-id").write_text("abc", encoding="utf-8")
    (session_dir / "current-session-sampled").write_text("true", encoding="utf-8")

    clear_session_state(tmp)

    assert not (session_dir / "current-session-id").exists()
    assert not (session_dir / "current-session-sampled").exists()


def test_auto_commit_snapshot_skips_when_no_git_dir() -> None:
    tmp = _tmp_dir()
    repo = tmp / "not-a-git-repo"
    repo.mkdir()

    result = auto_commit_snapshot(repo)

    assert result is False


def test_auto_commit_snapshot_skips_when_docs_monitoring_missing() -> None:
    tmp = _tmp_dir()
    repo = _make_git_repo(tmp / "repo")

    result = auto_commit_snapshot(repo)

    assert result is False


def test_auto_commit_snapshot_commits_when_history_changes() -> None:
    tmp = _tmp_dir()
    repo = _make_git_repo(tmp / "repo")
    telemetry_dir = tmp / "telemetry"

    # Bootstrap with at least one event so measure_impact has data
    record_event(repo, "session-start", source="test", telemetry_base=telemetry_dir)

    # Create docs/monitoring/ with an initial history.json
    monitoring = repo / "docs" / "monitoring"
    monitoring.mkdir(parents=True)
    (monitoring / "history.json").write_text('{"score": 0}\n', encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=repo, check=True, capture_output=True,
    )

    committed = auto_commit_snapshot(repo, telemetry_base=telemetry_dir)

    assert committed is True
    log = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        cwd=repo, check=True, capture_output=True, text=True,
    ).stdout
    assert "monitoring snapshot" in log
