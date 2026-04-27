from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]

REPO_SPECS = (
    ROOT / "repo_context_hooks" / "bundle" / "skills"
    / "context-handoff-hooks" / "scripts" / "repo_specs_memory.py"
)
SESSION_CTX = (
    ROOT / "repo_context_hooks" / "bundle" / "skills"
    / "context-handoff-hooks" / "scripts" / "session_context.py"
)


def _tmp_dir() -> Path:
    base = ROOT / ".tmp-tests"
    base.mkdir(exist_ok=True)
    path = base / uuid4().hex
    path.mkdir()
    return path


def _non_git_dir() -> Path:
    """Return a temp dir that is guaranteed to be outside any git repo."""
    path = Path(tempfile.mkdtemp(prefix="rch-test-"))
    return path


def _git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "t@t.com"],
        cwd=path, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "T"],
        cwd=path, check=True, capture_output=True,
    )
    return path


def _run(script: Path, event: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), event],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# repo_specs_memory.py — non-git directory
# ---------------------------------------------------------------------------

def test_repo_specs_non_git_prints_message_and_exits_0() -> None:
    tmp = _non_git_dir()
    result = _run(REPO_SPECS, "session-start", tmp)

    assert result.returncode == 0
    assert "no git repo detected" in result.stdout


def test_repo_specs_non_git_all_events_exit_0() -> None:
    tmp = _non_git_dir()
    for event in ("session-start", "pre-compact", "post-compact", "session-end"):
        result = _run(REPO_SPECS, event, tmp)
        assert result.returncode == 0, f"failed on event {event}: {result.stderr}"
        assert "no git repo detected" in result.stdout


# ---------------------------------------------------------------------------
# repo_specs_memory.py — git repo but no workspace contract
# ---------------------------------------------------------------------------

def test_repo_specs_session_start_no_contract_prints_init_hint() -> None:
    tmp = _tmp_dir()
    repo = _git_repo(tmp / "repo")

    result = _run(REPO_SPECS, "session-start", repo)

    assert result.returncode == 0
    assert "no workspace contract" in result.stdout
    assert "repo-context-hooks init" in result.stdout


def test_repo_specs_session_start_no_contract_does_not_scaffold() -> None:
    tmp = _tmp_dir()
    repo = _git_repo(tmp / "repo")

    _run(REPO_SPECS, "session-start", repo)

    assert not (repo / "specs" / "README.md").exists(), (
        "SessionStart must NOT auto-scaffold specs/README.md"
    )


def test_repo_specs_compact_no_contract_prints_nothing_to_checkpoint() -> None:
    tmp = _tmp_dir()
    repo = _git_repo(tmp / "repo")

    for event in ("pre-compact", "post-compact", "session-end"):
        result = _run(REPO_SPECS, event, repo)
        assert result.returncode == 0
        assert "nothing to checkpoint" in result.stdout, (
            f"expected checkpoint message for {event}, got: {result.stdout!r}"
        )


# ---------------------------------------------------------------------------
# session_context.py — non-git directory
# ---------------------------------------------------------------------------

def test_session_ctx_non_git_prints_message_and_exits_0() -> None:
    tmp = _non_git_dir()
    result = _run(SESSION_CTX, "session-start", tmp)

    assert result.returncode == 0
    assert "no git repo detected" in result.stdout


# ---------------------------------------------------------------------------
# session_context.py — git repo but no workspace contract
# ---------------------------------------------------------------------------

def test_session_ctx_no_contract_prints_init_hint() -> None:
    tmp = _tmp_dir()
    repo = _git_repo(tmp / "repo")

    result = _run(SESSION_CTX, "session-start", repo)

    assert result.returncode == 0
    assert "no workspace contract" in result.stdout
    assert "repo-context-hooks init" in result.stdout


# ---------------------------------------------------------------------------
# No regression — existing behavior preserved when contract IS present
# ---------------------------------------------------------------------------

def test_repo_specs_with_contract_still_works() -> None:
    tmp = _tmp_dir()
    repo = _git_repo(tmp / "repo")
    (repo / "README.md").write_text("# Test\n", encoding="utf-8")
    specs = repo / "specs"
    specs.mkdir()
    (specs / "README.md").write_text("# Engineering Memory\n", encoding="utf-8")

    result = _run(REPO_SPECS, "session-start", repo)

    assert result.returncode == 0
    assert "Repo Specs Memory" in result.stdout
    assert "Synced" in result.stdout


def test_session_ctx_with_contract_still_works() -> None:
    tmp = _tmp_dir()
    repo = _git_repo(tmp / "repo")
    (repo / "README.md").write_text("# Test\n", encoding="utf-8")
    specs = repo / "specs"
    specs.mkdir()
    (specs / "README.md").write_text("# Engineering Memory\n", encoding="utf-8")

    result = _run(SESSION_CTX, "session-start", repo)

    assert result.returncode == 0
    assert "Project Context" in result.stdout
