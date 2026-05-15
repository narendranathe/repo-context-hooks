"""Regression-grade integration test for the cross-workspace rollup (#109).

Builds a single synthetic 3-workspace telemetry tree and exercises every
rollup invariant against by-hand math:

  Workspace 1 (real, 5 session-starts) — tokens_saved = round(5*0.30*2000) = 3000
  Workspace 2 (ghost: <2 events + repo_name=tmp) — excluded by default
  Workspace 3 (real, 2 valid events + 1 corrupt JSONL line) — corrupt skipped

This test exists to lock down the headline numbers across the entire
M1-M6 chain (#106 → #107 → #108) so a future formula tweak, ghost-classifier
change, or render() refactor cannot silently break the cross-workspace
output. If you change anything in the rollup pipeline, this test should
fail loudly with a by-hand expected number, not a vague schema mismatch.

The synthetic-base builder is intentionally kept local to this file rather
than lifted into `tests/conftest.py`. Promoting it would expand conftest.py's
surface (currently scoped to isolation concerns); a second test file can
import the helper directly when one materializes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from repo_context_hooks.cli import main
from repo_context_hooks.telemetry import (
    EVENTS_FILE,
    rollup_telemetry,
)


# ---------------------------------------------------------------------------
# Synthetic 3-workspace fixture (the source of truth for the math below)
# ---------------------------------------------------------------------------

# By-hand math for the asserts below — keep these constants in sync with the
# event counts in `_build_three_workspace_tree`. Editing the counts without
# updating these numbers should make the test fail with a clear delta.
WS1_SESSION_STARTS = 5
WS3_SESSION_STARTS = 1  # 2 valid events; only one is `session-start`
GHOST_SESSION_STARTS = 1  # ghost has 1 session-start; excluded by default
TOTAL_REAL_SESSION_STARTS = WS1_SESSION_STARTS + WS3_SESSION_STARTS  # 6
TOTAL_REAL_TOKENS_SAVED = round(TOTAL_REAL_SESSION_STARTS * 0.30 * 2000)  # 3600
TOTAL_REAL_TOKENS_INJECTED = TOTAL_REAL_SESSION_STARTS * 4500  # 27000
WS1_TOKENS_SAVED = round(WS1_SESSION_STARTS * 0.30 * 2000)  # 3000
WS3_TOKENS_SAVED = round(WS3_SESSION_STARTS * 0.30 * 2000)  # 600


def _ev(name: str, *, repo_name: str, session_id: str) -> dict:
    return {
        "event_name": name,
        "repo_name": repo_name,
        "session_id": session_id,
    }


def _write_jsonl(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_three_workspace_tree(base: Path) -> Path:
    """Construct the canonical 3-workspace telemetry tree under `base`.

    Returns `base` for chaining. Layout:

        <base>/
          ws_alpha/events.jsonl       — 5 session-starts (real)
          ws_ghost/events.jsonl       — 1 session-start with repo_name="tmp"
                                        (qualifies as ghost: <2 events AND
                                         repo_name in {"repo","tmp","temp","test"})
          ws_corrupt/events.jsonl     — 1 valid session-start + 1 malformed
                                        line + 1 valid session-end
                                        (real workspace; corrupt line skipped)
    """
    # Workspace 1: real, 5 session-starts. repo_name=service-alpha.
    _write_jsonl(
        base / "ws_alpha" / EVENTS_FILE,
        [
            json.dumps(
                _ev("session-start", repo_name="service-alpha", session_id=f"a{i}")
            )
            for i in range(WS1_SESSION_STARTS)
        ],
    )

    # Workspace 2: ghost — exactly 1 event AND repo_name="tmp".
    _write_jsonl(
        base / "ws_ghost" / EVENTS_FILE,
        [json.dumps(_ev("session-start", repo_name="tmp", session_id="g1"))],
    )

    # Workspace 3: 2 valid events + 1 corrupt JSONL line. Both valid events
    # have repo_name="service-gamma"; only one is a session-start so this
    # workspace contributes WS3_SESSION_STARTS = 1 to the total.
    _write_jsonl(
        base / "ws_corrupt" / EVENTS_FILE,
        [
            json.dumps(
                _ev("session-start", repo_name="service-gamma", session_id="c1")
            ),
            "this line is not json {{",  # malformed — must be silently skipped
            json.dumps(_ev("session-end", repo_name="service-gamma", session_id="c1")),
        ],
    )
    return base


# ---------------------------------------------------------------------------
# Default rollup — ghost excluded
# ---------------------------------------------------------------------------


def test_default_rollup_excludes_ghost_and_matches_by_hand_math(tmp_path: Path) -> None:
    base = _build_three_workspace_tree(tmp_path / "telemetry")
    report = rollup_telemetry(base=base)

    s = report.summary
    assert s.workspaces_total == 3
    assert s.workspaces_ghost == 1
    assert s.workspaces_real == 2

    # By-hand: ws_alpha contributes 5, ws_corrupt contributes 1.
    assert s.session_starts == TOTAL_REAL_SESSION_STARTS
    assert s.tokens_saved == TOTAL_REAL_TOKENS_SAVED  # 3600
    assert s.tokens_injected == TOTAL_REAL_TOKENS_INJECTED  # 27000
    # cost_saved_usd = round(3600 / 1_000_000 * 3.0, 3) = round(0.0108, 3) = 0.011
    assert s.cost_saved_usd == round(TOTAL_REAL_TOKENS_SAVED / 1_000_000 * 3.0, 3)

    # ws_alpha + ws_corrupt = 2 real records; ws_ghost is skipped.
    assert len(report.repos) == 2
    repo_names = {r.repo_name for r in report.repos}
    assert "service-alpha" in repo_names
    assert "service-gamma" in repo_names
    assert "tmp" not in repo_names


def test_default_rollup_corrupt_jsonl_is_silently_skipped(tmp_path: Path) -> None:
    """ws_corrupt has 3 lines but only 2 parseable — corrupt line must not crash."""
    base = _build_three_workspace_tree(tmp_path / "telemetry")
    report = rollup_telemetry(base=base)

    # ws_alpha = 5 events; ws_corrupt = 2 valid events; ghost excluded → 7 total.
    assert report.summary.events_total == 7

    # ws_corrupt's record carries exactly 2 events worth of state.
    gamma = next(r for r in report.repos if r.repo_name == "service-gamma")
    assert gamma.session_starts == WS3_SESSION_STARTS  # 1
    assert gamma.tokens_saved == WS3_TOKENS_SAVED  # 600


# ---------------------------------------------------------------------------
# include_ghosts=True
# ---------------------------------------------------------------------------


def test_include_ghosts_brings_ghost_dir_back_into_repos(tmp_path: Path) -> None:
    base = _build_three_workspace_tree(tmp_path / "telemetry")
    report = rollup_telemetry(base=base, include_ghosts=True)

    assert len(report.repos) == 3
    ghost_records = [r for r in report.repos if r.is_ghost]
    assert len(ghost_records) == 1
    assert ghost_records[0].repo_name == "tmp"

    # Now the ghost's session-start is counted in the global total.
    s = report.summary
    assert s.session_starts == TOTAL_REAL_SESSION_STARTS + GHOST_SESSION_STARTS  # 7


# ---------------------------------------------------------------------------
# Sort order — tokens_saved desc
# ---------------------------------------------------------------------------


def test_repos_sorted_by_tokens_saved_descending(tmp_path: Path) -> None:
    base = _build_three_workspace_tree(tmp_path / "telemetry")
    report = rollup_telemetry(base=base, include_ghosts=True)

    # ws_alpha: 5 starts → 3000 tokens
    # ws_ghost: 1 start  →  600 tokens
    # ws_corrupt: 1 start →  600 tokens
    # The two 600-token entries can tie; the head must be ws_alpha.
    assert report.repos[0].repo_name == "service-alpha"
    assert report.repos[0].tokens_saved == WS1_TOKENS_SAVED  # 3000
    # Tail entries are both 600.
    tail_saves = [r.tokens_saved for r in report.repos[1:]]
    assert all(t == 600 for t in tail_saves)


# ---------------------------------------------------------------------------
# JSON contract — schema_version: 1
# ---------------------------------------------------------------------------


def test_json_payload_has_schema_version_one(tmp_path: Path) -> None:
    base = _build_three_workspace_tree(tmp_path / "telemetry")
    payload = rollup_telemetry(base=base).to_dict()

    assert payload["schema_version"] == 1
    assert payload["summary"]["session_starts"] == TOTAL_REAL_SESSION_STARTS
    assert payload["summary"]["tokens_saved"] == TOTAL_REAL_TOKENS_SAVED
    assert {r["repo_name"] for r in payload["repos"]} == {
        "service-alpha",
        "service-gamma",
    }


# ---------------------------------------------------------------------------
# CLI tracer — full main() → JSON output → asserts on the parsed payload
# ---------------------------------------------------------------------------


def test_measure_all_repos_end_to_end_through_main_matches_by_hand_math(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """The same fixture, but reached through `main()` → argparse → _measure
    → rollup_telemetry → JSON. Locks down the full M1-M6 chain."""
    base = _build_three_workspace_tree(tmp_path / "telemetry")
    monkeypatch.setenv("REPO_CONTEXT_HOOKS_TELEMETRY_DIR", str(base))
    monkeypatch.setattr(
        "sys.argv", ["repo-context-hooks", "measure", "--all-repos", "--json"]
    )

    rc = main()
    assert rc == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == 1
    assert payload["summary"]["session_starts"] == TOTAL_REAL_SESSION_STARTS
    assert payload["summary"]["tokens_saved"] == TOTAL_REAL_TOKENS_SAVED
    assert payload["summary"]["workspaces_real"] == 2
    assert payload["summary"]["workspaces_ghost"] == 1
    # Real-only by default — ghost excluded from per-repo block.
    assert {r["repo_name"] for r in payload["repos"]} == {
        "service-alpha",
        "service-gamma",
    }


def test_measure_all_repos_redact_round_trip_through_main(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """`measure --all-repos --redact --json` end-to-end: real repo names
    must NOT appear in the JSON; redacted forms (12-char lowercase hex) must."""
    base = _build_three_workspace_tree(tmp_path / "telemetry")
    monkeypatch.setenv("REPO_CONTEXT_HOOKS_TELEMETRY_DIR", str(base))
    monkeypatch.setattr(
        "sys.argv",
        ["repo-context-hooks", "measure", "--all-repos", "--redact", "--json"],
    )

    rc = main()
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)

    repo_names = {r["repo_name"] for r in payload["repos"]}
    assert "service-alpha" not in repo_names
    assert "service-gamma" not in repo_names
    for name in repo_names:
        assert len(name) == 12
        assert all(ch in "0123456789abcdef" for ch in name)
    # Headline math is invariant under redaction.
    assert payload["summary"]["tokens_saved"] == TOTAL_REAL_TOKENS_SAVED
