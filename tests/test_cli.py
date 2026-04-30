from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from repo_context_hooks.cli import (
    _checkpoint,
    _detect_platforms,
    _doctor,
    _init,
    _install,
    _measure,
    _platforms,
    _recommend,
    _resolve_experiment_dir,
    _telemetry_cmd,
    build_parser,
    main,
)
from repo_context_hooks.doctor import DoctorReport

ROOT = Path(__file__).resolve().parents[1]


def _tmp_dir() -> Path:
    base = ROOT / ".tmp-tests"
    base.mkdir(exist_ok=True)
    path = base / uuid4().hex
    path.mkdir()
    return path


def test_build_parser_uses_public_name() -> None:
    parser = build_parser()
    assert parser.prog == "repo-context-hooks"
    assert "repo context continuity" in parser.description.lower()


def test_parser_accepts_global_debug_flag() -> None:
    """``--debug`` is a top-level flag (issue #73) and propagates via
    ``args.debug`` to every subcommand without needing per-subparser
    duplication. Mirrors the ``--version`` convention."""
    parser = build_parser()
    assert parser.parse_args(["--debug", "platforms"]).debug is True
    assert parser.parse_args(["platforms"]).debug is False
    assert parser.parse_args(["--debug", "doctor", "--platform", "claude"]).debug is True


def test_parser_supports_platforms_and_doctor_commands() -> None:
    parser = build_parser()

    assert parser.parse_args(["platforms"]).command == "platforms"
    assert parser.parse_args(["platforms", "--json"]).json is True
    assert parser.parse_args(["doctor", "--platform", "claude"]).command == "doctor"
    assert parser.parse_args(["doctor", "--platform", "claude", "--json"]).json is True
    assert parser.parse_args(["doctor", "--all-platforms"]).command == "doctor"
    assert parser.parse_args(["doctor"]).command == "doctor"
    assert parser.parse_args(["init"]).command == "init"
    assert parser.parse_args(["recommend"]).command == "recommend"
    assert parser.parse_args(["recommend", "--json"]).json is True
    assert parser.parse_args(["measure"]).command == "measure"
    assert parser.parse_args(["measure", "--json"]).json is True
    assert (
        parser.parse_args(
            ["measure", "--snapshot-dir", "docs/monitoring"]
        ).snapshot_dir
        == "docs/monitoring"
    )


def test_platforms_print_support_tiers(capsys) -> None:
    assert _platforms(Namespace(json=False)) == 0

    out = capsys.readouterr().out
    assert "claude" in out
    assert "cursor" in out
    assert "codex" in out
    assert "replit" in out
    assert "windsurf" in out
    assert "lovable" in out
    assert "openclaw" in out
    assert "ollama" in out
    assert "kimi" in out
    assert "native" in out
    assert "partial" in out


def test_platforms_prints_json(capsys) -> None:
    assert _platforms(Namespace(json=True)) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["platforms"][0]["id"] == "claude"
    assert payload["platforms"][0]["support_tier"] == "native"


def test_install_skips_repo_context_outside_git_repo(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()
    calls: list[bool] = []

    def fake_install_platform(
        platform: str,
        repo_root,
        force: bool = False,
        home=None,
        install_repo_context: bool = False,
        also_repo_hooks: bool = False,
        telemetry: bool = True,
    ):
        calls.append(also_repo_hooks)
        return SimpleNamespace(
            summary="Codex partial support installed.",
            home_target=None,
            home_statuses={"context-handoff-hooks": "installed"},
            repo_statuses={},
            warnings=(),
            manual_steps=(),
        )

    monkeypatch.setattr(
        "repo_context_hooks.cli.install_platform",
        fake_install_platform,
    )

    args = Namespace(
        platform="codex",
        force=False,
        skip_repo_hooks=False,
        also_repo_hooks=True,
        no_telemetry=False,
        repo_root=str(tmp_path),
    )

    assert _install(args) == 0
    out = capsys.readouterr().out
    assert "Repo context skipped: target is not a git repository." in out
    assert "Codex partial support installed." in out
    assert calls == [False]


def test_install_respects_skip_repo_hooks(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()
    calls: list[bool] = []

    def fake_install_platform(
        platform: str,
        repo_root,
        force: bool = False,
        home=None,
        install_repo_context: bool = False,
        also_repo_hooks: bool = False,
        telemetry: bool = True,
    ):
        calls.append(also_repo_hooks)
        return SimpleNamespace(
            summary="Claude native support installed.",
            home_target=None,
            home_statuses={"context-handoff-hooks": "installed"},
            repo_statuses={},
            warnings=(),
            manual_steps=(),
        )

    monkeypatch.setattr(
        "repo_context_hooks.cli.install_platform",
        fake_install_platform,
    )

    args = Namespace(
        platform="claude",
        force=False,
        skip_repo_hooks=True,
        also_repo_hooks=False,
        no_telemetry=False,
        repo_root=str(tmp_path),
    )

    assert _install(args) == 0
    out = capsys.readouterr().out
    # --skip-repo-hooks is now a no-op; agent-level section always shown
    assert "=== Agent skill install ===" in out
    assert calls == [False]


def test_doctor_returns_nonzero_for_missing_state(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()

    def fake_diagnose_platform(platform: str, repo_root, home=None) -> DoctorReport:
        return DoctorReport(
            platform_id=platform,
            ok=False,
            present=(),
            missing=(".cursor/rules/repo-context-continuity.mdc",),
            warnings=("Cursor is partial support only.",),
        )

    monkeypatch.setattr(
        "repo_context_hooks.cli.diagnose_platform",
        fake_diagnose_platform,
    )

    args = Namespace(
        platform="cursor",
        repo_root=str(tmp_path),
    )

    assert _doctor(args) == 1
    out = capsys.readouterr().out
    assert "repo-context-continuity.mdc" in out


def test_doctor_all_platforms_prints_matrix_summary(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()

    class FakeReport:
        ok = True

        def render(self) -> str:
            return "[OK] platform-readiness\nclaude\tnative\tmissing\tsettings.json"

        def to_dict(self):
            return {"ok": True, "platforms": [{"platform_id": "claude"}]}

    monkeypatch.setattr(
        "repo_context_hooks.cli.diagnose_all_platforms",
        lambda repo_root: FakeReport(),
    )

    args = Namespace(
        platform=None,
        all_platforms=True,
        repo_root=str(tmp_path),
        json=False,
    )

    assert _doctor(args) == 0
    out = capsys.readouterr().out
    assert "platform-readiness" in out
    assert "claude" in out


def test_doctor_prints_json(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()

    class FakeReport:
        ok = True

        def render(self) -> str:
            return "[OK] repo-contract"

        def to_dict(self):
            return {"platform_id": "repo-contract", "ok": True}

    monkeypatch.setattr(
        "repo_context_hooks.cli.diagnose_repo_contract",
        lambda repo_root: FakeReport(),
    )

    args = Namespace(
        platform=None,
        all_platforms=False,
        repo_root=str(tmp_path),
        json=True,
    )

    assert _doctor(args) == 0
    assert json.loads(capsys.readouterr().out)["platform_id"] == "repo-contract"


def test_measure_prints_json(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()

    class FakeReport:
        def render(self) -> str:
            return "[OK] context-impact"

        def to_dict(self):
            return {
                "repo_name": "demo",
                "current_score": 84,
                "estimated_baseline_score": 35,
                "uplift": 49,
            }

    monkeypatch.setattr(
        "repo_context_hooks.cli.measure_impact",
        lambda repo_root: FakeReport(),
    )

    args = Namespace(
        repo_root=str(tmp_path),
        json=True,
    )

    assert _measure(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["repo_name"] == "demo"
    assert payload["uplift"] == 49


def test_measure_writes_public_snapshot(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()
    calls: list[tuple[str, Path]] = []

    class FakeReport:
        def render(self) -> str:
            return "[OK] context-impact"

        def to_dict(self):
            return {
                "repo_name": "demo",
                "current_score": 84,
                "estimated_baseline_score": 35,
                "uplift": 49,
            }

    def fake_snapshot(report, output_dir):
        calls.append((report.to_dict()["repo_name"], output_dir))
        return {
            "dashboard_path": str(output_dir / "index.html"),
            "history_path": str(output_dir / "history.json"),
        }

    monkeypatch.setattr(
        "repo_context_hooks.cli.measure_impact",
        lambda repo_root: FakeReport(),
    )
    monkeypatch.setattr(
        "repo_context_hooks.cli.write_public_monitoring_snapshot",
        fake_snapshot,
    )

    args = Namespace(
        repo_root=str(tmp_path),
        json=False,
        snapshot_dir="docs/monitoring",
    )

    assert _measure(args) == 0
    out = capsys.readouterr().out
    assert "Wrote public monitoring snapshot" in out
    assert calls == [("demo", tmp_path / "docs" / "monitoring")]


def test_init_prints_repo_contract_statuses(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()

    def fake_init_repo_contract(repo_root, force: bool = False):
        return {
            "README.md": "installed",
            "specs/README.md": "installed",
            "UBIQUITOUS_LANGUAGE.md": "installed",
            "AGENTS.md": "skipped",
        }

    monkeypatch.setattr(
        "repo_context_hooks.cli.init_repo_contract",
        fake_init_repo_contract,
    )

    args = Namespace(
        repo_root=str(tmp_path),
        force=False,
    )

    assert _init(args) == 0
    out = capsys.readouterr().out
    assert "Initialized repo contract" in out
    assert "README.md: installed" in out
    assert "AGENTS.md: skipped" in out


def test_recommend_prints_ranked_output(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()

    class FakeRecommendations:
        def render(self) -> str:
            return "[RECOMMEND]\n1. claude\nNext: repo-context-hooks install --platform claude"

        def to_dict(self):
            return {"recommendations": [{"platform_id": "claude"}]}

    monkeypatch.setattr(
        "repo_context_hooks.cli.recommend_setup",
        lambda repo_root, limit=3: FakeRecommendations(),
    )

    args = Namespace(
        repo_root=str(tmp_path),
        limit=3,
        json=False,
    )

    assert _recommend(args) == 0
    out = capsys.readouterr().out
    assert "[RECOMMEND]" in out
    assert "repo-context-hooks install --platform claude" in out


def test_recommend_prints_json(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()

    class FakeRecommendations:
        def render(self) -> str:
            return "[RECOMMEND]"

        def to_dict(self):
            return {"recommendations": [{"platform_id": "claude"}]}

    monkeypatch.setattr(
        "repo_context_hooks.cli.recommend_setup",
        lambda repo_root, limit=3: FakeRecommendations(),
    )

    args = Namespace(
        repo_root=str(tmp_path),
        limit=3,
        json=True,
    )

    assert _recommend(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["recommendations"][0]["platform_id"] == "claude"


def test_parser_install_accepts_also_repo_hooks_flag() -> None:
    parser = build_parser()
    args = parser.parse_args(["install", "--platform", "claude", "--also-repo-hooks"])
    assert args.also_repo_hooks is True
    assert args.skip_repo_hooks is False


def test_parser_install_also_repo_hooks_defaults_false() -> None:
    parser = build_parser()
    args = parser.parse_args(["install", "--platform", "claude"])
    assert args.also_repo_hooks is False


def test_install_prints_two_section_output_with_also_repo_hooks(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()
    (tmp_path / ".git").mkdir()

    def fake_install_platform(
        platform: str,
        repo_root,
        force: bool = False,
        home=None,
        install_repo_context: bool = False,
        also_repo_hooks: bool = False,
        telemetry: bool = True,
    ):
        return SimpleNamespace(
            summary="Claude native support installed.",
            home_target=tmp_path / "home" / ".claude" / "skills",
            home_statuses={"context-handoff-hooks": "installed", "settings.json": "installed"},
            repo_statuses={"repo_specs_memory.py": "installed", "session_context.py": "installed"},
            warnings=(),
            manual_steps=(),
        )

    monkeypatch.setattr(
        "repo_context_hooks.cli.install_platform",
        fake_install_platform,
    )

    args = Namespace(
        platform="claude",
        force=False,
        skip_repo_hooks=False,
        also_repo_hooks=True,
        no_telemetry=False,
        repo_root=str(tmp_path),
    )

    assert _install(args) == 0
    out = capsys.readouterr().out
    assert "=== Agent skill install ===" in out
    assert "=== Workspace artifacts ===" in out
    assert "Claude native support installed." in out
    assert "repo_specs_memory.py: installed" in out


def test_parser_install_no_telemetry_flag() -> None:
    parser = build_parser()
    args = parser.parse_args(["install", "--platform", "claude", "--no-telemetry"])
    assert args.no_telemetry is True


def test_parser_install_no_telemetry_defaults_false() -> None:
    parser = build_parser()
    args = parser.parse_args(["install", "--platform", "claude"])
    assert args.no_telemetry is False


def test_install_passes_telemetry_false_when_no_telemetry_flag(
    monkeypatch,
    capsys,
) -> None:
    """_install() must pass telemetry=False to install_platform when --no-telemetry is set."""
    tmp_path = _tmp_dir()
    captured_telemetry: list[bool] = []

    def fake_install_platform(
        platform: str,
        repo_root,
        force: bool = False,
        home=None,
        install_repo_context: bool = False,
        also_repo_hooks: bool = False,
        telemetry: bool = True,
    ):
        captured_telemetry.append(telemetry)
        return SimpleNamespace(
            summary="Claude native support installed.",
            home_target=None,
            home_statuses={"settings.json": "installed"},
            repo_statuses={},
            warnings=(),
            manual_steps=(),
        )

    monkeypatch.setattr(
        "repo_context_hooks.cli.install_platform",
        fake_install_platform,
    )

    args = Namespace(
        platform="claude",
        force=False,
        skip_repo_hooks=False,
        also_repo_hooks=False,
        no_telemetry=True,
        repo_root=str(tmp_path),
    )

    assert _install(args) == 0
    assert captured_telemetry == [False], "install_platform must receive telemetry=False"


def test_install_passes_telemetry_true_by_default(
    monkeypatch,
    capsys,
) -> None:
    """_install() must pass telemetry=True when --no-telemetry is absent."""
    tmp_path = _tmp_dir()
    captured_telemetry: list[bool] = []

    def fake_install_platform(
        platform: str,
        repo_root,
        force: bool = False,
        home=None,
        install_repo_context: bool = False,
        also_repo_hooks: bool = False,
        telemetry: bool = True,
    ):
        captured_telemetry.append(telemetry)
        return SimpleNamespace(
            summary="Claude native support installed.",
            home_target=None,
            home_statuses={"settings.json": "installed"},
            repo_statuses={},
            warnings=(),
            manual_steps=(),
        )

    monkeypatch.setattr(
        "repo_context_hooks.cli.install_platform",
        fake_install_platform,
    )

    args = Namespace(
        platform="claude",
        force=False,
        skip_repo_hooks=False,
        also_repo_hooks=False,
        no_telemetry=False,
        repo_root=str(tmp_path),
    )

    assert _install(args) == 0
    assert captured_telemetry == [True], "install_platform must receive telemetry=True by default"


def test_install_omits_workspace_section_without_also_repo_hooks(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()

    def fake_install_platform(
        platform: str,
        repo_root,
        force: bool = False,
        home=None,
        install_repo_context: bool = False,
        also_repo_hooks: bool = False,
        telemetry: bool = True,
    ):
        return SimpleNamespace(
            summary="Claude native support installed.",
            home_target=tmp_path / "home" / ".claude" / "skills",
            home_statuses={"settings.json": "installed"},
            repo_statuses={},
            warnings=(),
            manual_steps=(),
        )

    monkeypatch.setattr(
        "repo_context_hooks.cli.install_platform",
        fake_install_platform,
    )

    args = Namespace(
        platform="claude",
        force=False,
        skip_repo_hooks=False,
        also_repo_hooks=False,
        no_telemetry=False,
        repo_root=str(tmp_path),
    )

    assert _install(args) == 0
    out = capsys.readouterr().out
    assert "=== Agent skill install ===" in out
    assert "=== Workspace artifacts ===" not in out


# ---------------------------------------------------------------------------
# _detect_platforms() tests
# ---------------------------------------------------------------------------


def test_detect_platforms_finds_claude_if_dot_claude_exists(
    monkeypatch,
    tmp_path,
) -> None:
    """_detect_platforms returns 'claude' when ~/.claude/ exists."""
    dot_claude = tmp_path / ".claude"
    dot_claude.mkdir()
    monkeypatch.setattr("repo_context_hooks.cli.Path.home", lambda: tmp_path)
    detected = _detect_platforms()
    assert "claude" in detected


def test_detect_platforms_empty_if_nothing_exists(
    monkeypatch,
    tmp_path,
) -> None:
    """_detect_platforms returns empty list when no agent home dirs exist."""
    monkeypatch.setattr("repo_context_hooks.cli.Path.home", lambda: tmp_path)
    detected = _detect_platforms()
    assert detected == []


def test_detect_platforms_finds_multiple(
    monkeypatch,
    tmp_path,
) -> None:
    """_detect_platforms returns all platforms whose home dirs exist."""
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".cursor").mkdir()
    monkeypatch.setattr("repo_context_hooks.cli.Path.home", lambda: tmp_path)
    detected = _detect_platforms()
    assert "claude" in detected
    assert "cursor" in detected


# ---------------------------------------------------------------------------
# _install() auto-detection tests
# ---------------------------------------------------------------------------


def test_install_auto_detects_when_no_platform_arg(
    monkeypatch,
    capsys,
) -> None:
    """When args.platform is None, _install() auto-detects and installs detected platforms."""
    tmp_path = _tmp_dir()
    captured_platforms: list[str] = []

    monkeypatch.setattr(
        "repo_context_hooks.cli._detect_platforms",
        lambda: ["claude"],
    )

    def fake_install_platform(
        platform: str,
        repo_root,
        force: bool = False,
        home=None,
        install_repo_context: bool = False,
        also_repo_hooks: bool = False,
        telemetry: bool = True,
    ):
        captured_platforms.append(platform)
        return SimpleNamespace(
            summary="Claude native support installed.",
            home_target=None,
            home_statuses={"context-handoff-hooks": "installed"},
            repo_statuses={},
            warnings=(),
            manual_steps=(),
        )

    monkeypatch.setattr(
        "repo_context_hooks.cli.install_platform",
        fake_install_platform,
    )

    args = Namespace(
        platform=None,
        force=False,
        skip_repo_hooks=False,
        also_repo_hooks=False,
        no_telemetry=False,
        repo_root=str(tmp_path),
    )

    assert _install(args) == 0
    assert captured_platforms == ["claude"]
    out = capsys.readouterr().out
    assert "Auto-detected platforms: claude" in out


def test_install_falls_back_to_claude_when_nothing_detected(
    monkeypatch,
    capsys,
) -> None:
    """When _detect_platforms returns [], _install() defaults to claude."""
    tmp_path = _tmp_dir()
    captured_platforms: list[str] = []

    monkeypatch.setattr(
        "repo_context_hooks.cli._detect_platforms",
        lambda: [],
    )

    def fake_install_platform(
        platform: str,
        repo_root,
        force: bool = False,
        home=None,
        install_repo_context: bool = False,
        also_repo_hooks: bool = False,
        telemetry: bool = True,
    ):
        captured_platforms.append(platform)
        return SimpleNamespace(
            summary="Claude native support installed.",
            home_target=None,
            home_statuses={"context-handoff-hooks": "installed"},
            repo_statuses={},
            warnings=(),
            manual_steps=(),
        )

    monkeypatch.setattr(
        "repo_context_hooks.cli.install_platform",
        fake_install_platform,
    )

    args = Namespace(
        platform=None,
        force=False,
        skip_repo_hooks=False,
        also_repo_hooks=False,
        no_telemetry=False,
        repo_root=str(tmp_path),
    )

    assert _install(args) == 0
    assert captured_platforms == ["claude"]
    out = capsys.readouterr().out
    assert "No agent home directories detected. Defaulting to --platform claude." in out


def test_parser_install_platform_is_optional() -> None:
    """install subcommand must accept no --platform flag."""
    parser = build_parser()
    args = parser.parse_args(["install"])
    assert args.platform is None


def test_parser_install_platform_still_works_with_flag() -> None:
    """Backward compat: --platform claude must still parse correctly."""
    parser = build_parser()
    args = parser.parse_args(["install", "--platform", "claude"])
    assert args.platform == "claude"


def test_install_multi_platform_prints_section_headers(
    monkeypatch,
    capsys,
) -> None:
    """When multiple platforms detected, section headers use platform names."""
    tmp_path = _tmp_dir()

    monkeypatch.setattr(
        "repo_context_hooks.cli._detect_platforms",
        lambda: ["claude", "cursor"],
    )

    def fake_install_platform(
        platform: str,
        repo_root,
        force: bool = False,
        home=None,
        install_repo_context: bool = False,
        also_repo_hooks: bool = False,
        telemetry: bool = True,
    ):
        return SimpleNamespace(
            summary=f"{platform} installed.",
            home_target=None,
            home_statuses={},
            repo_statuses={},
            warnings=(),
            manual_steps=(),
        )

    monkeypatch.setattr(
        "repo_context_hooks.cli.install_platform",
        fake_install_platform,
    )

    args = Namespace(
        platform=None,
        force=False,
        skip_repo_hooks=False,
        also_repo_hooks=False,
        no_telemetry=False,
        repo_root=str(tmp_path),
    )

    assert _install(args) == 0
    out = capsys.readouterr().out
    assert "=== Installing for claude ===" in out
    assert "=== Installing for cursor ===" in out
    assert "Auto-detected platforms: claude, cursor" in out
    # Multi-platform: no "=== Agent skill install ===" header
    assert "=== Agent skill install ===" not in out
    # doctor hint uses --all-platforms
    assert "doctor --all-platforms" in out


def test_parser_supports_checkpoint_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["checkpoint", "--message", "Built X. Decided Y. Next: Z."])
    assert args.command == "checkpoint"
    assert args.message == "Built X. Decided Y. Next: Z."
    assert args.path == "."


def test_parser_checkpoint_requires_message() -> None:
    import pytest
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["checkpoint"])


# ===========================================================================
# Issue #92 — backfill cli.py to >=85% line+branch coverage.
# Tests appended (not split into a new file) per the repo's grep-locality
# convention: every cli dispatch test lives in this file. All tests follow
# the existing pattern (Namespace + monkeypatch + capsys); none invoke the
# CLI as a subprocess.
# ===========================================================================

import subprocess

import pytest

import repo_context_hooks.cli as cli_mod
import repo_context_hooks.consent as consent_mod
import repo_context_hooks.telemetry as telemetry_mod


# ---------------------------------------------------------------------------
# Section 1 — _measure --clean-ghosts (cli.py ~489-502)
# ---------------------------------------------------------------------------
# `purge_ghost_repos` is imported lazily *inside* `_measure` via
# `from .telemetry import purge_ghost_repos`, so patches must target the
# source module `telemetry.purge_ghost_repos` — `cli.purge_ghost_repos` is
# not bound at module level and patching it is a no-op.

def test_measure_clean_ghosts_dry_run_lists_dirs_and_hint(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(
        telemetry_mod,
        "purge_ghost_repos",
        lambda dry_run=True: {"removed": 2, "bytes_freed": 4096, "dirs": ["a", "b"]},
    )

    args = Namespace(clean_ghosts=True, dry_run=True, repo_root=str(_tmp_dir()))

    assert _measure(args) == 0
    out = capsys.readouterr().out
    assert "Would remove 2 ghost repo dirs (4 KB freed)" in out
    assert "  - a" in out
    assert "  - b" in out
    assert "Re-run with --no-dry-run" in out


def test_measure_clean_ghosts_no_dry_run_says_removed(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(
        telemetry_mod,
        "purge_ghost_repos",
        lambda dry_run=True: {"removed": 1, "bytes_freed": 1024, "dirs": ["x"]},
    )

    args = Namespace(clean_ghosts=True, dry_run=False, repo_root=str(_tmp_dir()))

    assert _measure(args) == 0
    out = capsys.readouterr().out
    assert "Removed 1 ghost repo dirs (1 KB freed)" in out
    assert "Re-run with --no-dry-run" not in out


def test_measure_clean_ghosts_zero_removed_omits_hint(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(
        telemetry_mod,
        "purge_ghost_repos",
        lambda dry_run=True: {"removed": 0, "bytes_freed": 0, "dirs": []},
    )

    args = Namespace(clean_ghosts=True, dry_run=True, repo_root=str(_tmp_dir()))

    assert _measure(args) == 0
    out = capsys.readouterr().out
    assert "Would remove 0 ghost repo dirs" in out
    assert "Re-run with --no-dry-run" not in out


def test_measure_clean_ghosts_default_dry_run_true_when_attr_missing(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """Pin `getattr(args, 'dry_run', True)` — flipping the default to False
    would silently make `--clean-ghosts` destructive on first invocation."""
    captured: dict = {}

    def fake_purge(dry_run: bool = True) -> dict:
        captured["dry_run"] = dry_run
        return {"removed": 0, "bytes_freed": 0, "dirs": []}

    monkeypatch.setattr(telemetry_mod, "purge_ghost_repos", fake_purge)

    args = Namespace(clean_ghosts=True, repo_root=str(_tmp_dir()))

    assert _measure(args) == 0
    assert captured["dry_run"] is True
    out = capsys.readouterr().out
    assert "Would remove" in out
    assert "Removed " not in out


# ---------------------------------------------------------------------------
# Section 2 — _measure export (cli.py ~508-521)
# ---------------------------------------------------------------------------

def _fake_measure_impact(repo_root, telemetry_base=None):
    return SimpleNamespace(current_score=0.5)


def test_measure_export_markdown_to_stdout(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(cli_mod, "measure_impact", _fake_measure_impact)
    monkeypatch.setattr(
        cli_mod,
        "export_impact_report",
        lambda report, format="markdown", redact=True: f"# Impact ({format})\nbody",
    )

    args = Namespace(
        positional_args=["export"],
        format="markdown",
        output=None,
        repo_root=str(_tmp_dir()),
    )

    assert _measure(args) == 0
    out = capsys.readouterr().out
    assert "# Impact (markdown)" in out
    assert "Export written to:" not in out


def test_measure_export_writes_to_file_and_announces_path(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(cli_mod, "measure_impact", _fake_measure_impact)
    monkeypatch.setattr(
        cli_mod,
        "export_impact_report",
        lambda report, format="markdown", redact=True: f"## json export\n{format}",
    )

    tmp = _tmp_dir()
    out_path = tmp / "out.md"
    args = Namespace(
        positional_args=["export"],
        format="json",
        output=str(out_path),
        repo_root=str(tmp),
    )

    assert _measure(args) == 0
    assert out_path.exists()
    assert "json" in out_path.read_text(encoding="utf-8")
    out = capsys.readouterr().out
    assert "Export written to:" in out
    assert str(out_path) in out


def test_measure_export_default_format_is_markdown_when_attr_missing(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pin `getattr(args, "format", "markdown")` — flipping the default to
    "json" would silently change export output for callers that omit the
    flag."""
    captured: dict = {}

    def fake_export(report, format="markdown", redact=True):
        captured["format"] = format
        captured["redact"] = redact
        return "EXPORTED"

    monkeypatch.setattr(cli_mod, "measure_impact", _fake_measure_impact)
    monkeypatch.setattr(cli_mod, "export_impact_report", fake_export)

    args = Namespace(
        positional_args=["export"], output=None, repo_root=str(_tmp_dir())
    )

    assert _measure(args) == 0
    assert captured["format"] == "markdown"
    assert captured["redact"] is True


# ---------------------------------------------------------------------------
# Section 3 — _measure experiment {start, finish, status}
# (cli.py ~523-546) and _resolve_experiment_dir (cli.py ~481-486)
# ---------------------------------------------------------------------------

def test_measure_experiment_start_prints_before_path(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    tmp = _tmp_dir()
    before = tmp / "before.json"
    monkeypatch.setattr(cli_mod, "experiment_start", lambda root, exp_dir: before)

    args = Namespace(
        positional_args=["experiment", "start"],
        experiment_dir=str(tmp / "exp"),
        repo_root=str(tmp),
    )

    assert _measure(args) == 0
    out = capsys.readouterr().out
    assert "Before snapshot:" in out
    assert str(before) in out


def test_measure_experiment_start_existing_returns_one(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    def raise_exists(root, exp_dir):
        raise FileExistsError("already started")

    monkeypatch.setattr(cli_mod, "experiment_start", raise_exists)

    args = Namespace(
        positional_args=["experiment", "start"],
        experiment_dir=None,
        repo_root=str(_tmp_dir()),
    )

    assert _measure(args) == 1
    assert "Error: already started" in capsys.readouterr().out


def test_measure_experiment_finish_missing_returns_one(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    def raise_missing(root, exp_dir):
        raise FileNotFoundError("no before snapshot")

    monkeypatch.setattr(cli_mod, "experiment_finish", raise_missing)

    args = Namespace(
        positional_args=["experiment", "finish"],
        experiment_dir=None,
        repo_root=str(_tmp_dir()),
    )

    assert _measure(args) == 1
    out = capsys.readouterr().out
    assert "Error:" in out
    assert "no before snapshot" in out


def test_measure_experiment_status_prints_message(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(
        cli_mod,
        "experiment_status",
        lambda exp_dir: {"message": "no experiment in progress"},
    )

    args = Namespace(
        positional_args=["experiment", "status"],
        experiment_dir=None,
        repo_root=str(_tmp_dir()),
    )

    assert _measure(args) == 0
    assert "no experiment in progress" in capsys.readouterr().out


def test_measure_experiment_unknown_subcommand_returns_one(capsys) -> None:
    args = Namespace(
        positional_args=["experiment", "bogus"],
        experiment_dir=None,
        repo_root=str(_tmp_dir()),
    )

    assert _measure(args) == 1
    out = capsys.readouterr().out
    assert "Unknown experiment subcommand: 'bogus'" in out
    assert "Usage: repo-context-hooks measure experiment" in out


def test_measure_experiment_no_subcommand_defaults_to_status(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """Pin the `positional[1] if len(positional) > 1 else "status"` default
    so a refactor to "start" or "finish" can't sneak in."""
    captured: dict = {"called": False}

    def fake_status(exp_dir):
        captured["called"] = True
        return {"message": "default-status-routed"}

    monkeypatch.setattr(cli_mod, "experiment_status", fake_status)

    args = Namespace(
        positional_args=["experiment"],
        experiment_dir=None,
        repo_root=str(_tmp_dir()),
    )

    assert _measure(args) == 0
    assert captured["called"] is True
    assert "default-status-routed" in capsys.readouterr().out


@pytest.mark.parametrize("raw", [None, "", "custom/exp", "nested/relative/dir"])
def test_resolve_experiment_dir_relative_or_default(raw) -> None:
    """Pin `getattr(args, "experiment_dir", None)` default + relative-path
    branch on Windows + POSIX."""
    repo_root = Path(_tmp_dir())
    args = Namespace(experiment_dir=raw)

    resolved = _resolve_experiment_dir(args, repo_root)

    assert resolved.is_absolute()
    if not raw:
        assert resolved == repo_root / ".repo-context-hooks" / "experiment"
    else:
        assert resolved == repo_root / raw


def test_resolve_experiment_dir_absolute_returned_verbatim() -> None:
    repo_root = Path(_tmp_dir())
    abs_path = (repo_root.parent / "absolute_exp").resolve()
    args = Namespace(experiment_dir=str(abs_path))

    resolved = _resolve_experiment_dir(args, repo_root)
    assert resolved == abs_path


def test_resolve_experiment_dir_attr_missing_uses_default() -> None:
    """Pin `getattr(args, "experiment_dir", None)` — Namespace without attr."""
    repo_root = Path(_tmp_dir())
    args = Namespace()
    resolved = _resolve_experiment_dir(args, repo_root)
    assert resolved == repo_root / ".repo-context-hooks" / "experiment"


# ---------------------------------------------------------------------------
# Section 4 — _checkpoint (cli.py ~618-656)
# ---------------------------------------------------------------------------
# All tests stub `subprocess.run`. We never invoke real git or the bundled
# script — that's a smoke-test concern, out of scope for #92's unit-coverage
# ratchet.

def _git_rev_parse_path(p: Path) -> str:
    """Mimic `git rev-parse --show-toplevel` actual output: forward-slash
    path with trailing newline. Real git emits forward slashes on Windows
    too — using `str(p)` would test a path shape git never produces."""
    return str(p).replace("\\", "/") + "\n"


def test_checkpoint_no_git_repo_returns_one(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "git")

    monkeypatch.setattr("subprocess.run", fake_run)

    args = Namespace(message="msg", path=str(_tmp_dir()))

    assert _checkpoint(args) == 1
    assert "no git repo found" in capsys.readouterr().out


def test_checkpoint_git_binary_missing_returns_one(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """Pin user-visible behaviour when `git` is not on PATH (broken-install
    territory)."""

    def fake_run(*args, **kwargs):
        raise FileNotFoundError("git not found")

    monkeypatch.setattr("subprocess.run", fake_run)

    args = Namespace(message="msg", path=str(_tmp_dir()))

    assert _checkpoint(args) == 1
    assert "no git repo found" in capsys.readouterr().out


def test_checkpoint_no_specs_readme_returns_one(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    tmp = _tmp_dir()  # Do NOT create tmp/specs/README.md.

    def fake_run(*args, **kwargs):
        return SimpleNamespace(
            stdout=_git_rev_parse_path(tmp), returncode=0, stderr=""
        )

    monkeypatch.setattr("subprocess.run", fake_run)

    args = Namespace(message="m", path=str(tmp))

    assert _checkpoint(args) == 1
    out = capsys.readouterr().out
    assert "no workspace contract found" in out
    assert "repo-context-hooks init" in out


def test_checkpoint_calls_repo_specs_memory_with_message(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    tmp = _tmp_dir()
    (tmp / "specs").mkdir(parents=True, exist_ok=True)
    (tmp / "specs" / "README.md").write_text("# specs\n", encoding="utf-8")

    captured: list = []

    def fake_run(args_list, **kwargs):
        captured.append(list(args_list))
        if len(captured) == 1:
            assert "rev-parse" in args_list
            return SimpleNamespace(
                stdout=_git_rev_parse_path(tmp), returncode=0, stderr=""
            )
        return SimpleNamespace(returncode=0, stdout="Decision recorded\n", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)

    args = Namespace(message="Built X. Decided Y. Next: Z.", path=str(tmp))

    assert _checkpoint(args) == 0
    assert "Decision recorded" in capsys.readouterr().out

    assert len(captured) == 2
    second = captured[1]
    assert "decision" in second
    assert "--message" in second
    assert "Built X. Decided Y. Next: Z." in second


def test_checkpoint_propagates_subprocess_failure(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    tmp = _tmp_dir()
    (tmp / "specs").mkdir(parents=True, exist_ok=True)
    (tmp / "specs" / "README.md").write_text("# specs\n", encoding="utf-8")

    call_idx = {"i": 0}

    def fake_run(args_list, **kwargs):
        call_idx["i"] += 1
        if call_idx["i"] == 1:
            return SimpleNamespace(
                stdout=_git_rev_parse_path(tmp), returncode=0, stderr=""
            )
        return SimpleNamespace(returncode=2, stdout="", stderr="boom\n")

    monkeypatch.setattr("subprocess.run", fake_run)

    args = Namespace(message="m", path=str(tmp))

    assert _checkpoint(args) == 2
    assert "boom" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Section 5 — _telemetry_cmd (cli.py ~659-722)
# ---------------------------------------------------------------------------
# CRITICAL global-adoption requirement: every test in this class redirects
# `consent._CONFIG_PATH_OVERRIDE` to a tmp path via class-scoped autouse
# fixture. Without it, `_telemetry_cmd enable --yes` would silently write
# to the developer's real `%LOCALAPPDATA%\repo-context-hooks\consent.json`
# (or `~/.config/repo-context-hooks/consent.json`), corrupting their actual
# telemetry consent state and accumulating fake install_ids in their user
# profile every time they run `pytest`. The class boundary makes it
# impossible to forget — every method inherits the override.

class TestTelemetryCli:
    """All `_telemetry_cmd` tests live here. The autouse fixture below is
    the safety boundary — do not move tests outside the class without
    setting `_CONFIG_PATH_OVERRIDE` manually."""

    @pytest.fixture(autouse=True)
    def _redirect_consent_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            consent_mod, "_CONFIG_PATH_OVERRIDE", tmp_path / "consent.json"
        )

    # ---- status -----------------------------------------------------------

    def test_status_not_set_prints_three_lines(self, capsys) -> None:
        args = Namespace(telemetry_subcommand="status")
        assert _telemetry_cmd(args) == 0
        out = capsys.readouterr().out
        assert "Remote telemetry: not configured" in out
        assert "Install ID: (will be generated" in out
        assert "Config:" in out

    def test_status_enabled_prints_install_id(self, capsys) -> None:
        consent_mod.enable_consent()
        args = Namespace(telemetry_subcommand="status")

        assert _telemetry_cmd(args) == 0
        out = capsys.readouterr().out
        assert "Remote telemetry: enabled" in out
        assert "Install ID:" in out
        assert "Enabled at:" in out
        assert "collector endpoint not yet configured" in out

    def test_status_disabled_prints_config(self, capsys) -> None:
        consent_mod.enable_consent()
        consent_mod.disable_consent()
        args = Namespace(telemetry_subcommand="status")

        assert _telemetry_cmd(args) == 0
        out = capsys.readouterr().out
        assert "Remote telemetry: disabled" in out
        assert "Config:" in out

    # ---- enable -----------------------------------------------------------

    def test_enable_yes_writes_consent_and_install_id(
        self, capsys, tmp_path: Path
    ) -> None:
        args = Namespace(telemetry_subcommand="enable", yes=True)

        assert _telemetry_cmd(args) == 0
        out = capsys.readouterr().out
        assert "Remote telemetry enabled." in out
        assert "Install ID:" in out

        cfg_path = tmp_path / "consent.json"
        assert cfg_path.exists()
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        assert cfg["consented"] is True
        from uuid import UUID
        UUID(cfg["install_id"])

    def test_enable_attr_missing_enters_interactive(
        self, monkeypatch: pytest.MonkeyPatch, capsys, tmp_path: Path
    ) -> None:
        """Pin `getattr(args, 'yes', False)` — flipping to True would
        auto-enable telemetry without consent."""
        monkeypatch.setattr("builtins.input", lambda _prompt="": "n")
        args = Namespace(telemetry_subcommand="enable")

        assert _telemetry_cmd(args) == 0
        out = capsys.readouterr().out
        assert "Telemetry remains disabled." in out
        assert not (tmp_path / "consent.json").exists()

    @pytest.mark.parametrize(
        "user_input,enabled",
        [
            ("y", True),
            ("Y", True),
            ("yes", True),
            ("YES", True),
            ("  yes  ", True),
            ("n", False),
            ("N", False),
            ("", False),
            ("no", False),
            ("maybe", False),
        ],
    )
    def test_enable_interactive_input_table(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        user_input: str,
        enabled: bool,
    ) -> None:
        """Single parametrize over the four contracts of
        `input().strip().lower()`: whitespace strip, case fold,
        set-membership (`y`/`yes`), and the [y/N] capital-N convention
        (empty → no)."""
        monkeypatch.setattr("builtins.input", lambda _prompt="": user_input)
        args = Namespace(telemetry_subcommand="enable", yes=False)

        assert _telemetry_cmd(args) == 0

        cfg_path = tmp_path / "consent.json"
        if enabled:
            assert cfg_path.exists()
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            assert cfg["consented"] is True
        else:
            assert not cfg_path.exists()

    def test_enable_eof_returns_zero_disabled(
        self, monkeypatch: pytest.MonkeyPatch, capsys, tmp_path: Path
    ) -> None:
        def raise_eof(_prompt=""):
            raise EOFError

        monkeypatch.setattr("builtins.input", raise_eof)
        args = Namespace(telemetry_subcommand="enable", yes=False)

        assert _telemetry_cmd(args) == 0
        out = capsys.readouterr().out
        assert "Non-interactive environment detected." in out
        assert not (tmp_path / "consent.json").exists()

    def test_enable_os_error_treated_as_eof(
        self, monkeypatch: pytest.MonkeyPatch, capsys, tmp_path: Path
    ) -> None:
        def raise_oserror(_prompt=""):
            raise OSError

        monkeypatch.setattr("builtins.input", raise_oserror)
        args = Namespace(telemetry_subcommand="enable", yes=False)

        assert _telemetry_cmd(args) == 0
        out = capsys.readouterr().out
        assert "Non-interactive environment detected." in out
        assert not (tmp_path / "consent.json").exists()

    # ---- disable ----------------------------------------------------------

    def test_disable_writes_false_and_preserves_install_id(
        self, capsys, tmp_path: Path
    ) -> None:
        consent_mod.enable_consent()
        cfg_path = tmp_path / "consent.json"
        original_id = json.loads(cfg_path.read_text(encoding="utf-8"))["install_id"]

        args = Namespace(telemetry_subcommand="disable")
        assert _telemetry_cmd(args) == 0
        assert "Remote telemetry disabled." in capsys.readouterr().out

        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        assert cfg["consented"] is False
        # install_id MUST be preserved across disable — privacy-relevant.
        assert cfg["install_id"] == original_id

    # ---- preview ----------------------------------------------------------

    def test_preview_no_repo_root_returns_payload(self, capsys) -> None:
        args = Namespace(telemetry_subcommand="preview", repo_root=None)
        assert _telemetry_cmd(args) == 0

        payload = json.loads(capsys.readouterr().out)
        assert payload["install_id"] == "not-yet-generated"
        assert "package_version" in payload
        assert "disclaimer" in payload
        assert payload["continuity_score"] is None

    def test_preview_attr_missing_returns_payload(self, capsys) -> None:
        """Pin `getattr(args, 'repo_root', None)` — Namespace without attr."""
        args = Namespace(telemetry_subcommand="preview")
        assert _telemetry_cmd(args) == 0

        payload = json.loads(capsys.readouterr().out)
        assert payload["continuity_score"] is None
        assert payload["disclaimer"].startswith("This is a preview")


# ---------------------------------------------------------------------------
# Section 6 — main() dispatch routing for new subcommands
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "argv,private_attr",
    [
        (["repo-context-hooks", "checkpoint", "--message", "x"], "_checkpoint"),
        (["repo-context-hooks", "telemetry", "status"], "_telemetry_cmd"),
    ],
)
def test_main_dispatches_new_subcommands(
    monkeypatch: pytest.MonkeyPatch,
    argv: list,
    private_attr: str,
) -> None:
    """If the parser→dispatch wiring for `checkpoint` or `telemetry` ever
    breaks, every unit test still passes and the CLI is broken for users.
    This integration test pins the wiring."""
    sentinel = {"called": False}

    def fake_dispatch(args):
        sentinel["called"] = True
        return 7

    monkeypatch.setattr(cli_mod, private_attr, fake_dispatch)
    monkeypatch.setattr("sys.argv", argv)

    assert main() == 7
    assert sentinel["called"] is True
