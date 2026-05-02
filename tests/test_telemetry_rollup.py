"""Tests for the cross-workspace telemetry rollup core (issue #107).

The rollup walks a telemetry base directory containing one subdir per
workspace (each with an `events.jsonl`), applies the same `_build_usability`
substring-match formula already used by `measure`, and produces a stable
versioned report.

These tests cover the M1+M3+M4 slice only — the data + formula core. The
CLI surface (`measure --all-repos`) lands in #108; docs in #110.

Test fixtures construct a synthetic telemetry tree under `tmp_path` so the
real telemetry dir is never read or written.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from repo_context_hooks.telemetry import (
    EVENTS_FILE,
    RollupReport,
    redact_repo_name,
    rollup_telemetry,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _write_events(workspace_dir: Path, events: list[dict]) -> Path:
    """Write events as JSONL into <workspace_dir>/events.jsonl."""
    workspace_dir.mkdir(parents=True, exist_ok=True)
    path = workspace_dir / EVENTS_FILE
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    return path


def _ev(
    name: str, *, repo_name: str = "repo-context-hooks", session_id: str = "s1", **extra
) -> dict:
    """Construct a minimal event payload."""
    return {
        "event_name": name,
        "repo_name": repo_name,
        "session_id": session_id,
        **extra,
    }


# ---------------------------------------------------------------------------
# Empty / boundary cases
# ---------------------------------------------------------------------------


def test_empty_base_returns_empty_report(tmp_path: Path) -> None:
    base = tmp_path / "telemetry"
    base.mkdir()
    report = rollup_telemetry(base=base)
    assert isinstance(report, RollupReport)
    assert report.repos == ()
    assert report.summary.session_starts == 0
    assert report.summary.events_total == 0
    assert report.summary.workspaces_total == 0
    assert report.summary.workspaces_real == 0
    assert report.summary.workspaces_ghost == 0
    assert report.schema_version == 1


def test_nonexistent_base_returns_empty_report(tmp_path: Path) -> None:
    """Missing base path is not a crash — just zero events."""
    base = tmp_path / "does-not-exist"
    report = rollup_telemetry(base=base)
    assert report.repos == ()
    assert report.summary.events_total == 0


# ---------------------------------------------------------------------------
# Formula correctness — the load-bearing assertion
# ---------------------------------------------------------------------------


def test_single_repo_three_session_starts_yields_tokens_saved_1800(
    tmp_path: Path,
) -> None:
    """resume_events=3 → tokens_saved = round(3 * 0.30 * 2000) = 1800."""
    base = tmp_path / "telemetry"
    _write_events(
        base / "repo_aaa",
        [
            _ev("session-start", session_id="s1"),
            _ev("session-start", session_id="s2"),
            _ev("session-start", session_id="s3"),
        ],
    )
    report = rollup_telemetry(base=base)
    assert report.summary.session_starts == 3
    assert report.summary.tokens_saved == 1800
    assert report.summary.tokens_injected == 3 * 4500  # 13500
    assert report.summary.cost_saved_usd == round(1800 / 1_000_000 * 3.0, 3)


def test_session_start_substring_match_includes_compound_names(tmp_path: Path) -> None:
    """Formula substring-matches `"session-start" in name` — must catch
    `session-context-session-start` etc. (matches `_build_usability`)."""
    base = tmp_path / "telemetry"
    _write_events(
        base / "repo_xyz",
        [
            _ev("session-start"),
            _ev("session-context-session-start"),
            _ev("decision"),  # not a start, not counted
        ],
    )
    report = rollup_telemetry(base=base)
    assert report.summary.session_starts == 2


# ---------------------------------------------------------------------------
# Ghost filter
# ---------------------------------------------------------------------------


def test_multi_repo_excludes_ghost_dir_by_default(tmp_path: Path) -> None:
    base = tmp_path / "telemetry"
    # Real workspace: 3 events, real repo_name
    _write_events(
        base / "repo_real",
        [
            _ev("session-start", repo_name="my-real-repo", session_id="s1"),
            _ev("decision", repo_name="my-real-repo", session_id="s1"),
            _ev("session-end", repo_name="my-real-repo", session_id="s1"),
        ],
    )
    # Ghost: <2 events AND repo_name in {"repo","tmp","temp","test"}
    _write_events(
        base / "repo_ghost",
        [_ev("session-start", repo_name="tmp", session_id="g1")],
    )
    report = rollup_telemetry(base=base)
    assert report.summary.workspaces_total == 2
    assert report.summary.workspaces_real == 1
    assert report.summary.workspaces_ghost == 1
    assert len(report.repos) == 1
    assert report.repos[0].repo_name == "my-real-repo"


def test_include_ghosts_true_includes_ghost_dir(tmp_path: Path) -> None:
    base = tmp_path / "telemetry"
    _write_events(
        base / "repo_real",
        [
            _ev("session-start", repo_name="real", session_id="s1"),
            _ev("session-end", repo_name="real", session_id="s1"),
        ],
    )
    _write_events(
        base / "repo_ghost",
        [_ev("session-start", repo_name="tmp", session_id="g1")],
    )
    report = rollup_telemetry(base=base, include_ghosts=True)
    assert len(report.repos) == 2
    # is_ghost flag preserved on per-repo records
    ghost_records = [r for r in report.repos if r.is_ghost]
    assert len(ghost_records) == 1
    assert ghost_records[0].repo_name == "tmp"


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------


def test_repos_sorted_by_tokens_saved_descending(tmp_path: Path) -> None:
    base = tmp_path / "telemetry"
    # Repo A: 1 session-start
    _write_events(
        base / "repo_a", [_ev("session-start", repo_name="aa", session_id="s1")]
    )
    # Repo B: 5 session-starts (highest)
    _write_events(
        base / "repo_b",
        [_ev("session-start", repo_name="bb", session_id=f"s{i}") for i in range(5)],
    )
    # Repo C: 2 session-starts (middle)
    _write_events(
        base / "repo_c",
        [_ev("session-start", repo_name="cc", session_id=f"s{i}") for i in range(2)],
    )
    report = rollup_telemetry(base=base)
    assert [r.repo_name for r in report.repos] == ["bb", "cc", "aa"]


# ---------------------------------------------------------------------------
# Redaction helper
# ---------------------------------------------------------------------------


def test_redact_repo_name_returns_12_char_hex_deterministic() -> None:
    a = redact_repo_name("foo")
    b = redact_repo_name("foo")
    c = redact_repo_name("bar")
    assert a == b
    assert a != c
    assert len(a) == 12
    assert all(ch in "0123456789abcdef" for ch in a)


def test_redact_repo_name_handles_empty_string() -> None:
    assert len(redact_repo_name("")) == 12


# ---------------------------------------------------------------------------
# JSON schema (the stable downstream contract)
# ---------------------------------------------------------------------------


def test_to_dict_has_schema_version_summary_and_repos_keys(tmp_path: Path) -> None:
    base = tmp_path / "telemetry"
    _write_events(
        base / "repo_a",
        [_ev("session-start", repo_name="aa", session_id="s1")],
    )
    payload = rollup_telemetry(base=base).to_dict()
    assert payload["schema_version"] == 1
    assert "summary" in payload
    assert "repos" in payload
    summary = payload["summary"]
    for key in (
        "telemetry_base",
        "workspaces_total",
        "workspaces_real",
        "workspaces_ghost",
        "sessions_distinct",
        "events_total",
        "event_counts",
        "session_starts",
        "tokens_injected",
        "tokens_saved",
        "cost_saved_usd",
    ):
        assert key in summary, f"summary missing key: {key}"
    repo = payload["repos"][0]
    for key in (
        "repo_id",
        "repo_name",
        "sessions",
        "session_starts",
        "tokens_saved",
        "is_ghost",
    ):
        assert key in repo, f"repo record missing key: {key}"


def test_to_dict_event_counts_aggregate_across_workspaces(tmp_path: Path) -> None:
    base = tmp_path / "telemetry"
    _write_events(
        base / "repo_a",
        [
            _ev("session-start", repo_name="aa", session_id="s1"),
            _ev("decision", repo_name="aa", session_id="s1"),
        ],
    )
    _write_events(
        base / "repo_b",
        [
            _ev("session-start", repo_name="bb", session_id="s2"),
            _ev("session-start", repo_name="bb", session_id="s3"),
        ],
    )
    payload = rollup_telemetry(base=base).to_dict()
    assert payload["summary"]["event_counts"]["session-start"] == 3
    assert payload["summary"]["event_counts"]["decision"] == 1
    assert payload["summary"]["sessions_distinct"] == 3
    assert payload["summary"]["events_total"] == 4


# ---------------------------------------------------------------------------
# Robustness — corrupt JSONL must not crash
# ---------------------------------------------------------------------------


def test_corrupt_jsonl_line_is_skipped(tmp_path: Path) -> None:
    base = tmp_path / "telemetry"
    workspace = base / "repo_a"
    workspace.mkdir(parents=True)
    (workspace / EVENTS_FILE).write_text(
        json.dumps(_ev("session-start", repo_name="aa", session_id="s1"))
        + "\n"
        + "this is not json {{\n"  # malformed line
        + json.dumps(_ev("session-end", repo_name="aa", session_id="s1"))
        + "\n",
        encoding="utf-8",
    )
    report = rollup_telemetry(base=base)
    # Two valid events parsed, malformed line silently skipped.
    assert report.summary.events_total == 2
    assert report.summary.session_starts == 1


# ---------------------------------------------------------------------------
# Environment overrides
# ---------------------------------------------------------------------------


def test_env_telemetry_zero_returns_empty_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """REPO_CONTEXT_HOOKS_TELEMETRY=0 short-circuits — no filesystem read."""
    base = tmp_path / "telemetry"
    _write_events(
        base / "repo_a",
        [_ev("session-start", repo_name="aa", session_id="s1")],
    )
    monkeypatch.setenv("REPO_CONTEXT_HOOKS_TELEMETRY", "0")
    report = rollup_telemetry(base=base)
    assert report.repos == ()
    assert report.summary.events_total == 0
    # Even though the workspace exists on disk, opt-out means workspaces_total=0.
    assert report.summary.workspaces_total == 0


def test_env_telemetry_dir_override_is_honored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When base=None, REPO_CONTEXT_HOOKS_TELEMETRY_DIR drives base resolution."""
    base = tmp_path / "override-base"
    _write_events(
        base / "repo_a",
        [_ev("session-start", repo_name="aa", session_id="s1")],
    )
    monkeypatch.setenv("REPO_CONTEXT_HOOKS_TELEMETRY_DIR", str(base))
    report = rollup_telemetry()  # base=None → resolve via env
    assert report.summary.session_starts == 1
    assert report.summary.telemetry_base == str(base)


# ---------------------------------------------------------------------------
# Rendering (text)
# ---------------------------------------------------------------------------


def test_render_includes_summary_block_and_top_table(tmp_path: Path) -> None:
    base = tmp_path / "telemetry"
    _write_events(
        base / "repo_a",
        [
            _ev("session-start", repo_name="aa", session_id="s1"),
            _ev("session-start", repo_name="aa", session_id="s2"),
        ],
    )
    text = rollup_telemetry(base=base).render()
    assert "Fleet Rollup" in text
    assert "Tokens" in text
    assert "aa" in text


def test_render_top_n_truncation_default_15(tmp_path: Path) -> None:
    base = tmp_path / "telemetry"
    # 20 workspaces, each with one session-start
    for i in range(20):
        _write_events(
            base / f"repo_{i:02d}",
            [_ev("session-start", repo_name=f"r{i:02d}", session_id=f"s{i}")],
        )
    text = rollup_telemetry(base=base).render()  # default top_n=15
    # Count "r00".."r19" appearances in the body
    visible = sum(1 for i in range(20) if f"r{i:02d}" in text)
    assert visible == 15


def test_render_top_n_zero_shows_all(tmp_path: Path) -> None:
    base = tmp_path / "telemetry"
    for i in range(20):
        _write_events(
            base / f"repo_{i:02d}",
            [_ev("session-start", repo_name=f"r{i:02d}", session_id=f"s{i}")],
        )
    text = rollup_telemetry(base=base).render(top_n=0)
    visible = sum(1 for i in range(20) if f"r{i:02d}" in text)
    assert visible == 20
