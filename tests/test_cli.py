from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from repo_context_hooks.cli import _doctor, _install, _platforms, build_parser
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


def test_parser_supports_platforms_and_doctor_commands() -> None:
    parser = build_parser()

    assert parser.parse_args(["platforms"]).command == "platforms"
    assert parser.parse_args(["doctor", "--platform", "claude"]).command == "doctor"


def test_platforms_print_support_tiers(capsys) -> None:
    assert _platforms() == 0

    out = capsys.readouterr().out
    assert "claude" in out
    assert "cursor" in out
    assert "codex" in out
    assert "native" in out
    assert "partial" in out


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
        install_repo_context: bool = True,
    ):
        calls.append(install_repo_context)
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
        install_repo_context: bool = True,
    ):
        calls.append(install_repo_context)
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
        repo_root=str(tmp_path),
    )

    assert _install(args) == 0
    out = capsys.readouterr().out
    assert "Skipped repo context installation" in out
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
