"""Regression tests for the 25% lifecycle coverage bug.

These three tests document and prevent re-introduction of the exact failure
modes identified by the four critic agents:
- RC1: is_sampled() reading stale file before env var
- RC4: worktree isolation
- Lifecycle chain: sampled session must produce all 3 event types
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest

from repo_context_hooks.telemetry import is_sampled, _session_state_dir

ROOT = Path(__file__).resolve().parents[1]
HOOK_SCRIPT = (
    ROOT
    / "repo_context_hooks"
    / "bundle"
    / "skills"
    / "context-handoff-hooks"
    / "scripts"
    / "repo_specs_memory.py"
)


def _make_git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=path, check=True, capture_output=True)
    (path / "specs").mkdir()
    (path / "specs" / "README.md").write_text("# Engineering Memory\n", encoding="utf-8")
    return path


def test_stale_sampled_false_file_is_overridden_by_env_var(tmp_path, monkeypatch) -> None:
    """RC1 regression: REPO_CONTEXT_HOOKS_TELEMETRY=1 must win over a stale sampled=false file.

    Before the fix, is_sampled() read the file before checking the env var.
    A previous session's sampled=false would silently suppress all subsequent
    events even with REPO_CONTEXT_HOOKS_SAMPLE_RATE=1.0 set.
    """
    repo = tmp_path / "repo"
    repo.mkdir()

    # Simulate a previous session that left sampled=false
    state_dir = _session_state_dir(repo)
    (state_dir / "current-session-sampled").write_text("false", encoding="utf-8")

    monkeypatch.setenv("REPO_CONTEXT_HOOKS_TELEMETRY", "1")
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_SAMPLE_RATE", raising=False)

    assert is_sampled(repo) is True, (
        "REPO_CONTEXT_HOOKS_TELEMETRY=1 must override a stale sampled=false file. "
        "If this fails, RC1 is still present — stale files silently suppress telemetry."
    )


def test_sampled_session_produces_all_lifecycle_events(tmp_path) -> None:
    """Lifecycle chain regression: a sampled session must record session-start,
    pre-compact, AND session-end — not just session-start.

    Before the fix, only session-start was recorded (25% lifecycle coverage).
    """
    if not HOOK_SCRIPT.exists():
        pytest.skip(f"hook script not found: {HOOK_SCRIPT}")

    repo = _make_git_repo(tmp_path / "repo")
    telemetry_dir = tmp_path / "telemetry"
    telemetry_dir.mkdir()

    env = {
        **os.environ,
        "REPO_CONTEXT_HOOKS_TELEMETRY": "1",
        "REPO_CONTEXT_HOOKS_TELEMETRY_DIR": str(telemetry_dir),
    }

    for event in ("session-start", "pre-compact", "session-end"):
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT), event],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"hook script failed on {event!r}:\n{result.stderr}"

    events_files = list(telemetry_dir.rglob("events.jsonl"))
    assert events_files, "no events.jsonl produced"

    lines = [l for l in events_files[0].read_text(encoding="utf-8").splitlines() if l.strip()]
    event_names = [json.loads(l)["event_name"] for l in lines]

    assert "session-start" in event_names, "session-start not recorded"
    assert "pre-compact" in event_names, "pre-compact not recorded — lifecycle coverage < 100%"
    assert "session-end" in event_names, "session-end not recorded — lifecycle coverage < 100%"

    session_ids = {json.loads(l)["session_id"] for l in lines}
    assert len(session_ids) == 1, f"events split across multiple session_ids: {session_ids}"


def test_worktree_isolation_independent_sampling_decisions(tmp_path, monkeypatch) -> None:
    """RC4 regression: two different repo_root paths must maintain independent state.

    If worktrees ever share a state dir accidentally, one worktree's sampled=false
    could suppress another worktree's events.
    """
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_TELEMETRY", raising=False)
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_SAMPLE_RATE", raising=False)

    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    repo_a.mkdir()
    repo_b.mkdir()

    # Force repo_a sampled=true, repo_b sampled=false via their individual state dirs
    state_a = _session_state_dir(repo_a)
    state_b = _session_state_dir(repo_b)

    # These must be different directories
    assert state_a != state_b, "two unrelated repos must not share a session state dir"

    (state_a / "current-session-sampled").write_text("true", encoding="utf-8")
    (state_b / "current-session-sampled").write_text("false", encoding="utf-8")

    assert is_sampled(repo_a) is True, "repo_a must be sampled"
    assert is_sampled(repo_b) is False, "repo_b must not be sampled"

    # repo_a's is_sampled call must not mutate repo_b's state
    assert (state_b / "current-session-sampled").read_text(encoding="utf-8").strip() == "false"
