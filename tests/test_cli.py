from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from repo_context_hooks.cli import _install, build_parser


def test_build_parser_uses_public_name() -> None:
    parser = build_parser()
    assert parser.prog == "repo-context-hooks"
    assert "repo context continuity" in parser.description.lower()


def test_install_skips_repo_hooks_outside_git_repo(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    def fake_install_skills(platform: str, force: bool = False, home=None):
        return tmp_path, {"context-handoff-hooks": "installed"}

    monkeypatch.setattr(
        "repo_context_hooks.cli.install_skills",
        fake_install_skills,
    )

    args = Namespace(
        platform="codex",
        force=False,
        skip_repo_hooks=False,
        repo_root=str(tmp_path),
    )

    assert _install(args) == 0
    out = capsys.readouterr().out
    assert "Installed platform skills to:" in out
    assert "Repo hooks skipped: target is not a git repository." in out


def test_install_respects_skip_repo_hooks(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    def fake_install_skills(platform: str, force: bool = False, home=None):
        return tmp_path, {"context-handoff-hooks": "installed"}

    monkeypatch.setattr(
        "repo_context_hooks.cli.install_skills",
        fake_install_skills,
    )

    args = Namespace(
        platform="claude",
        force=False,
        skip_repo_hooks=True,
        repo_root=str(tmp_path),
    )

    assert _install(args) == 0
    out = capsys.readouterr().out
    assert "Skipped repo hook installation" in out
