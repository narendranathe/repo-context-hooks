"""Tests for the ``Last error`` section in ``doctor`` output (issue #73).

The plain-text rendering must include a "Last error:" line followed by
either the most recent log entry or "No errors recorded". The JSON
rendering must surface ``last_error`` and ``log_path`` keys so M6's
``verify`` command and downstream tooling can consume them
programmatically.
"""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from repo_context_hooks import logging_setup
from repo_context_hooks.cli import _doctor
from repo_context_hooks.doctor import DoctorReport


@pytest.fixture(autouse=True)
def _reset_logging_state() -> None:
    logging_setup.reset_for_tests()
    yield
    logging_setup.reset_for_tests()


@pytest.fixture
def isolate_log_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(logging_setup, "_LOG_DIR_OVERRIDE", tmp_path)
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_LOG_DIR", raising=False)
    return tmp_path


def _ok_report(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch ``diagnose_repo_contract`` to return an OK report."""
    monkeypatch.setattr(
        "repo_context_hooks.cli.diagnose_repo_contract",
        lambda repo_root: DoctorReport(
            platform_id="repo-contract",
            ok=True,
            present=("README.md",),
            missing=(),
            invalid=(),
            warnings=(),
        ),
    )


def test_doctor_text_says_no_errors_when_log_missing(
    isolate_log_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    _ok_report(monkeypatch)
    args = Namespace(
        platform=None,
        all_platforms=False,
        repo_root=str(tmp_path),
        json=False,
    )
    assert _doctor(args) == 0
    out = capsys.readouterr().out
    assert "Last error:" in out
    assert "No errors recorded" in out


def test_doctor_text_shows_last_error_line(
    isolate_log_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    _ok_report(monkeypatch)
    (isolate_log_dir / "errors.log").write_text(
        "2026-04-29 12:00:00 ERROR repo_context_hooks.cli: experiment finish failed: missing\n",
        encoding="utf-8",
    )
    args = Namespace(
        platform=None,
        all_platforms=False,
        repo_root=str(tmp_path),
        json=False,
    )
    assert _doctor(args) == 0
    out = capsys.readouterr().out
    assert "Last error:" in out
    assert "experiment finish failed: missing" in out


def test_doctor_json_payload_includes_last_error_and_log_path(
    isolate_log_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    _ok_report(monkeypatch)
    (isolate_log_dir / "errors.log").write_text(
        "2026-04-29 12:00:00 ERROR repo_context_hooks.cli: boom\n",
        encoding="utf-8",
    )
    args = Namespace(
        platform=None,
        all_platforms=False,
        repo_root=str(tmp_path),
        json=True,
    )
    assert _doctor(args) == 0
    payload = json.loads(capsys.readouterr().out)
    # Original report keys are preserved (sibling-PR contract).
    assert payload["platform_id"] == "repo-contract"
    # New self-observability keys land alongside.
    assert payload["last_error"].endswith("boom")
    assert payload["log_path"].endswith("errors.log")


def test_doctor_json_payload_emits_null_last_error_when_log_missing(
    isolate_log_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    _ok_report(monkeypatch)
    args = Namespace(
        platform=None,
        all_platforms=False,
        repo_root=str(tmp_path),
        json=True,
    )
    assert _doctor(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["last_error"] is None
    assert payload["log_path"].endswith("errors.log")
