"""CLI surface for cross-workspace rollup (issue #108).

Wires `rollup_telemetry()` (#107) into `repo-context-hooks measure
--all-repos`. Tests cover (a) the CLI plumbing — argparse → flags →
early-return branch in `_measure()`, (b) format selection via `--json`,
(c) `--top N` truncation, (d) `--include-ghosts` propagation, (e)
`--redact` rewriting `repo_name` in both renderings, and (f) the
`REPO_CONTEXT_HOOKS_TELEMETRY=0` opt-out short-circuit (no FS reads).

Tests use `Namespace` + `monkeypatch.setattr(telemetry_mod,
"rollup_telemetry", ...)` to inject deterministic reports — focuses
the assertions on CLI plumbing, not on rollup math (covered in
tests/test_telemetry_rollup.py).
"""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from uuid import uuid4

import pytest

from repo_context_hooks import telemetry as telemetry_mod
from repo_context_hooks.cli import (
    _measure,
    build_parser,
    main,
)  # noqa: F401  -- main reachable via sys.argv patch
from repo_context_hooks.telemetry import (
    EVENTS_FILE,
    RollupRepo,
    RollupReport,
    RollupSummary,
)

ROOT = Path(__file__).resolve().parents[1]


def _tmp_dir() -> Path:
    base = ROOT / ".tmp-tests"
    base.mkdir(exist_ok=True)
    path = base / uuid4().hex
    path.mkdir()
    return path


def _fake_report(*, repo_names: list[str] | None = None) -> RollupReport:
    """Build a deterministic RollupReport for CLI plumbing assertions."""
    if repo_names is None:
        repo_names = ["alpha", "beta"]
    repos = tuple(
        RollupRepo(
            repo_id=f"id_{i:02d}",
            repo_name=name,
            sessions=2 + i,
            session_starts=3 + i,
            tokens_saved=(3 + i) * 600,
            is_ghost=False,
        )
        for i, name in enumerate(repo_names)
    )
    summary = RollupSummary(
        telemetry_base="/fake/base",
        workspaces_total=len(repos),
        workspaces_real=len(repos),
        workspaces_ghost=0,
        sessions_distinct=sum(r.sessions for r in repos),
        events_total=10,
        event_counts={"session-start": sum(r.session_starts for r in repos)},
        session_starts=sum(r.session_starts for r in repos),
        tokens_injected=sum(r.session_starts for r in repos) * 4500,
        tokens_saved=round(sum(r.session_starts for r in repos) * 0.30 * 2000),
        cost_saved_usd=0.123,
    )
    return RollupReport(summary=summary, repos=repos)


def _measure_args(**overrides) -> Namespace:
    """Construct a Namespace matching the measure subparser defaults."""
    defaults = {
        "all_repos": False,
        "include_ghosts": False,
        "top": 15,
        "redact": False,
        "json": False,
        "repo_root": str(_tmp_dir()),
        # Other measure flags default to falsy so the early-return branches
        # don't fire ahead of --all-repos.
        "clean_ghosts": False,
        "dry_run": True,
        "branches": False,
        "forecast": False,
        "badge": False,
        "badge_out": None,
        "open": False,
        "snapshot_dir": None,
        "positional_args": [],
        "format": "markdown",
        "output": None,
        "experiment_dir": None,
    }
    defaults.update(overrides)
    return Namespace(**defaults)


# ---------------------------------------------------------------------------
# Argparse wiring (Tracer Bullet — first end-to-end CLI reach)
# ---------------------------------------------------------------------------


def test_parser_accepts_all_repos_include_ghosts_top() -> None:
    """build_parser() must register the three new flags on the measure subparser."""
    parser = build_parser()
    args = parser.parse_args(
        ["measure", "--all-repos", "--include-ghosts", "--top", "7"]
    )
    assert args.all_repos is True
    assert args.include_ghosts is True
    assert args.top == 7


def test_parser_top_default_is_15() -> None:
    parser = build_parser()
    args = parser.parse_args(["measure", "--all-repos"])
    assert args.top == 15


def test_parser_all_repos_default_false() -> None:
    """measure without --all-repos must leave the flag falsy so the legacy
    measure_impact path is unaffected."""
    parser = build_parser()
    args = parser.parse_args(["measure"])
    assert args.all_repos is False


# ---------------------------------------------------------------------------
# _measure() early-return branch (CLI plumbing)
# ---------------------------------------------------------------------------


def test_measure_all_repos_text_output(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    captured: dict = {}

    def fake_rollup(**kwargs):
        captured.update(kwargs)
        return _fake_report(repo_names=["alpha-svc", "beta-svc"])

    monkeypatch.setattr(telemetry_mod, "rollup_telemetry", fake_rollup)

    args = _measure_args(all_repos=True)
    assert _measure(args) == 0

    out = capsys.readouterr().out
    assert "Fleet Rollup" in out
    assert "alpha-svc" in out
    assert "beta-svc" in out
    # Defaults propagated: include_ghosts=False
    assert captured.get("include_ghosts") is False


def test_measure_all_repos_json_output_has_schema_version(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(telemetry_mod, "rollup_telemetry", lambda **kw: _fake_report())

    args = _measure_args(all_repos=True, json=True)
    assert _measure(args) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == 1
    assert "summary" in payload
    assert "repos" in payload
    assert {r["repo_name"] for r in payload["repos"]} == {"alpha", "beta"}


def test_measure_all_repos_top_truncates_table(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(
        telemetry_mod,
        "rollup_telemetry",
        lambda **kw: _fake_report(repo_names=[f"r{i:02d}" for i in range(20)]),
    )

    args = _measure_args(all_repos=True, top=5)
    assert _measure(args) == 0

    out = capsys.readouterr().out
    visible = sum(1 for i in range(20) if f"r{i:02d}" in out)
    assert visible == 5


def test_measure_all_repos_top_zero_shows_all(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(
        telemetry_mod,
        "rollup_telemetry",
        lambda **kw: _fake_report(repo_names=[f"r{i:02d}" for i in range(20)]),
    )

    args = _measure_args(all_repos=True, top=0)
    assert _measure(args) == 0

    out = capsys.readouterr().out
    visible = sum(1 for i in range(20) if f"r{i:02d}" in out)
    assert visible == 20


def test_measure_all_repos_include_ghosts_propagates(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    captured: dict = {}

    def fake_rollup(**kwargs):
        captured.update(kwargs)
        return _fake_report()

    monkeypatch.setattr(telemetry_mod, "rollup_telemetry", fake_rollup)

    args = _measure_args(all_repos=True, include_ghosts=True)
    assert _measure(args) == 0

    assert captured.get("include_ghosts") is True


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------


def test_measure_all_repos_redact_replaces_repo_name_in_text(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(
        telemetry_mod,
        "rollup_telemetry",
        lambda **kw: _fake_report(repo_names=["super-secret-repo"]),
    )

    args = _measure_args(all_repos=True, redact=True)
    assert _measure(args) == 0

    out = capsys.readouterr().out
    assert "super-secret-repo" not in out
    # The redacted form is sha256(name)[:12] — check at least one 12-char
    # lowercase hex token appears in the table body.
    import re

    assert re.search(
        r"\b[0-9a-f]{12}\b", out
    ), "no 12-char hex token in redacted output"


def test_measure_all_repos_redact_replaces_repo_name_in_json(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(
        telemetry_mod,
        "rollup_telemetry",
        lambda **kw: _fake_report(repo_names=["secret-a", "secret-b"]),
    )

    args = _measure_args(all_repos=True, redact=True, json=True)
    assert _measure(args) == 0

    payload = json.loads(capsys.readouterr().out)
    repo_names = {r["repo_name"] for r in payload["repos"]}
    assert "secret-a" not in repo_names
    assert "secret-b" not in repo_names
    # Each redacted name is 12 lowercase hex chars
    for name in repo_names:
        assert len(name) == 12
        assert all(ch in "0123456789abcdef" for ch in name)


# ---------------------------------------------------------------------------
# Env opt-out short-circuit
# ---------------------------------------------------------------------------


def test_measure_all_repos_env_opt_out_prints_message_and_does_not_walk(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """REPO_CONTEXT_HOOKS_TELEMETRY=0 must short-circuit at the CLI: print
    a friendly opt-out message and exit 0 WITHOUT calling rollup_telemetry
    (which would touch the filesystem)."""

    def boom(**kwargs):
        pytest.fail("rollup_telemetry must not be called when telemetry is off")

    monkeypatch.setattr(telemetry_mod, "rollup_telemetry", boom)
    monkeypatch.setenv("REPO_CONTEXT_HOOKS_TELEMETRY", "0")

    args = _measure_args(all_repos=True)
    assert _measure(args) == 0

    out = capsys.readouterr().out
    assert "Telemetry disabled" in out
    assert "rollup is opt-out" in out


# ---------------------------------------------------------------------------
# End-to-end through main() — confirms full argparse → dispatch → output
# ---------------------------------------------------------------------------


def test_measure_all_repos_end_to_end_through_main(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys
) -> None:
    """Build a synthetic telemetry tree, point REPO_CONTEXT_HOOKS_TELEMETRY_DIR
    at it, and confirm `main(["measure", "--all-repos", "--json"])` produces
    the expected schema. This is the real tracer bullet — no mocks."""
    base = tmp_path / "telemetry"
    workspace = base / "ws_real"
    workspace.mkdir(parents=True)
    (workspace / EVENTS_FILE).write_text(
        "\n".join(
            json.dumps(
                {
                    "event_name": "session-start",
                    "repo_name": "real-svc",
                    "session_id": f"s{i}",
                }
            )
            for i in range(3)
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("REPO_CONTEXT_HOOKS_TELEMETRY_DIR", str(base))
    # `main()` reads sys.argv; patch it instead of passing args directly.
    monkeypatch.setattr(
        "sys.argv", ["repo-context-hooks", "measure", "--all-repos", "--json"]
    )

    rc = main()
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == 1
    assert payload["summary"]["session_starts"] == 3
    assert payload["summary"]["tokens_saved"] == 1800  # round(3 * 0.30 * 2000)
    assert any(r["repo_name"] == "real-svc" for r in payload["repos"])


# ---------------------------------------------------------------------------
# Public-surface contract — drift gate covers this, but pin it explicitly
# ---------------------------------------------------------------------------


def test_public_surface_includes_all_repos_include_ghosts_and_top() -> None:
    """The committed snapshot must list the three new flags so the
    public-surface drift gate (`scripts/check_public_surface.py`) stays
    green after this PR lands."""
    snapshot = json.loads(
        (ROOT / "tests" / "contract" / "public_surface.json").read_text(
            encoding="utf-8"
        )
    )
    measure = next(c for c in snapshot["cli_commands"] if c["name"] == "measure")
    for flag in ("--all-repos", "--include-ghosts", "--top"):
        assert (
            flag in measure["flags"]
        ), f"public_surface.json::measure.flags is missing {flag!r}"
