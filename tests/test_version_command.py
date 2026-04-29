"""Tests for the rich `--version` output (issue #76).

Coverage targets every failure mode flagged by the failure-modes critic:
- subprocess errors (FileNotFoundError, TimeoutExpired, UnicodeDecodeError)
- monorepo SHA leak (toplevel pyproject.toml owns a different package)
- site-packages skip
- empty / non-hex git output
- best-effort install-method detection
- the published RCH_VERSION_RE regex round-trips its own output
"""
from __future__ import annotations

import re
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

import pytest
from hypothesis import given, strategies as st

from repo_context_hooks import version_info
from repo_context_hooks.cli import build_parser, main
from repo_context_hooks.version_info import (
    RCH_VERSION_RE,
    format_version,
    get_git_sha,
    get_install_method,
)


# ---------------------------------------------------------------------------
# Parser surface
# ---------------------------------------------------------------------------


def test_parser_accepts_version_flag() -> None:
    parser = build_parser()
    args = parser.parse_args(["--version"])
    assert args.version is True
    assert args.command is None


def test_parser_command_is_optional_when_version_set() -> None:
    """Adding --version must not require a subcommand."""
    parser = build_parser()
    # No SystemExit raised:
    parser.parse_args(["--version"])


def test_main_prints_version_and_exits_zero(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["repo-context-hooks", "--version"])
    rc = main()
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out.startswith("repo-context-hooks ")
    assert RCH_VERSION_RE.match(out), f"output does not match published regex: {out}"


def test_main_without_command_or_version_errors(monkeypatch) -> None:
    """Calling with no subcommand AND no --version is still an error."""
    monkeypatch.setattr(sys, "argv", ["repo-context-hooks"])
    with pytest.raises(SystemExit):
        main()


# ---------------------------------------------------------------------------
# format_version output shape
# ---------------------------------------------------------------------------


def test_format_version_includes_python_full_version(monkeypatch) -> None:
    monkeypatch.setattr(version_info, "get_git_sha", lambda: None)
    monkeypatch.setattr(version_info, "get_install_method", lambda: None)
    out = format_version()
    # platform.python_version() preserves alpha/beta/rc tags; we assert the
    # exact string is in the output. (Critic A non-negotiable.)
    import platform as _p
    assert f"python: {_p.python_version()}" in out


def test_format_version_omits_git_segment_when_none(monkeypatch) -> None:
    monkeypatch.setattr(version_info, "get_git_sha", lambda: None)
    monkeypatch.setattr(version_info, "get_install_method", lambda: None)
    out = format_version()
    assert "git:" not in out


def test_format_version_includes_git_segment_when_present(monkeypatch) -> None:
    monkeypatch.setattr(version_info, "get_git_sha", lambda: "1a2b3c4")
    monkeypatch.setattr(version_info, "get_install_method", lambda: None)
    out = format_version()
    assert "git: 1a2b3c4" in out


def test_format_version_includes_install_method_when_detected(monkeypatch) -> None:
    monkeypatch.setattr(version_info, "get_git_sha", lambda: None)
    monkeypatch.setattr(version_info, "get_install_method", lambda: "pipx")
    out = format_version()
    assert "install: pipx" in out


def test_format_version_swallows_get_git_sha_exceptions(monkeypatch) -> None:
    def boom() -> str | None:
        raise RuntimeError("simulated explosion")

    monkeypatch.setattr(version_info, "get_git_sha", boom)
    monkeypatch.setattr(version_info, "get_install_method", lambda: None)
    out = format_version()
    assert out.startswith("repo-context-hooks ")
    assert "git:" not in out


# ---------------------------------------------------------------------------
# get_git_sha() — failure-mode coverage
# ---------------------------------------------------------------------------


def test_get_git_sha_returns_none_in_site_packages(monkeypatch, tmp_path) -> None:
    fake = tmp_path / "site-packages" / "repo_context_hooks"
    fake.mkdir(parents=True)
    monkeypatch.setattr(version_info, "_here", lambda: fake)
    assert get_git_sha() is None


def test_get_git_sha_returns_none_when_git_not_installed(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(version_info, "_here", lambda: tmp_path)

    def fake_run(args, **kwargs):
        raise FileNotFoundError("git: not found")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert get_git_sha() is None


def test_get_git_sha_returns_none_on_timeout(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(version_info, "_here", lambda: tmp_path)

    def fake_run(args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="git", timeout=1.0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert get_git_sha() is None


def test_get_git_sha_returns_none_on_unicode_error(monkeypatch, tmp_path) -> None:
    """Critic C non-negotiable: UnicodeDecodeError must not crash."""
    monkeypatch.setattr(version_info, "_here", lambda: tmp_path)

    def fake_run(args, **kwargs):
        raise UnicodeDecodeError("utf-8", b"\xff\xfe", 0, 1, "bogus")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert get_git_sha() is None


def test_get_git_sha_returns_none_when_git_returns_nonzero(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(version_info, "_here", lambda: tmp_path)

    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(
            args=args, returncode=128, stdout="", stderr="not a git repo"
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert get_git_sha() is None


def test_get_git_sha_returns_none_when_pyproject_owns_different_package(
    monkeypatch, tmp_path
) -> None:
    """Critic A non-negotiable: monorepo guard.

    If `git rev-parse --show-toplevel` resolves a directory whose
    `pyproject.toml` declares a *different* package name, we MUST NOT emit
    the SHA — that would stamp the outer monorepo's HEAD onto our version
    string and misattribute the build.
    """
    here = tmp_path / "vendor" / "rch" / "repo_context_hooks"
    here.mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "outer-monorepo"\n', encoding="utf-8"
    )
    monkeypatch.setattr(version_info, "_here", lambda: here)

    def fake_run(args, **kwargs):
        if "rev-parse" in args and "--show-toplevel" in args:
            return subprocess.CompletedProcess(
                args=args, returncode=0, stdout=str(tmp_path) + "\n", stderr=""
            )
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="aaaaaaa\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert get_git_sha() is None


def test_get_git_sha_returns_sha_when_pyproject_owns_us(monkeypatch, tmp_path) -> None:
    here = tmp_path / "repo_context_hooks"
    here.mkdir()
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "repo-context-hooks"\nversion = "0.6.0"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(version_info, "_here", lambda: here)

    def fake_run(args, **kwargs):
        if "--show-toplevel" in args:
            return subprocess.CompletedProcess(
                args=args, returncode=0, stdout=str(tmp_path) + "\n", stderr=""
            )
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="abcdef0\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert get_git_sha() == "abcdef0"


def test_get_git_sha_rejects_non_hex_output(monkeypatch, tmp_path) -> None:
    """A garbage stdout from git must not propagate as a 'sha'."""
    here = tmp_path / "repo_context_hooks"
    here.mkdir()
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "repo-context-hooks"\n', encoding="utf-8"
    )
    monkeypatch.setattr(version_info, "_here", lambda: here)

    def fake_run(args, **kwargs):
        if "--show-toplevel" in args:
            return subprocess.CompletedProcess(args=args, returncode=0, stdout=str(tmp_path) + "\n", stderr="")
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="not-a-sha\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert get_git_sha() is None


def test_toplevel_owns_us_handles_unreadable_pyproject(monkeypatch, tmp_path) -> None:
    # No pyproject.toml at all -> read fails -> returns False.
    assert version_info._toplevel_owns_us(tmp_path) is False


def test_toplevel_owns_us_regex_fallback_for_old_python(monkeypatch, tmp_path) -> None:
    """The 3.9/3.10 regex fallback path still works."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "repo-context-hooks"\nversion = "0.6.0"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(version_info.sys, "version_info", (3, 10, 0, "final", 0))
    assert version_info._toplevel_owns_us(tmp_path) is True

    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "something-else"\n', encoding="utf-8"
    )
    assert version_info._toplevel_owns_us(tmp_path) is False


# ---------------------------------------------------------------------------
# get_install_method() — best-effort heuristic
# ---------------------------------------------------------------------------


def test_get_install_method_detects_pipx(monkeypatch, tmp_path) -> None:
    fake = tmp_path / "pipx" / "venvs" / "repo-context-hooks" / "lib" / "site-packages" / "repo_context_hooks"
    fake.mkdir(parents=True)
    monkeypatch.setattr(version_info, "_here", lambda: fake)
    assert get_install_method() == "pipx"


def test_get_install_method_detects_uv_via_env(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(version_info, "_here", lambda: tmp_path)
    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", str(tmp_path))
    assert get_install_method() == "uv"


def test_get_install_method_returns_none_for_source_checkout(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(version_info, "_here", lambda: tmp_path)
    monkeypatch.delenv("UV_PROJECT_ENVIRONMENT", raising=False)
    assert get_install_method() is None


def test_get_install_method_falls_back_to_pip_in_site_packages(monkeypatch, tmp_path) -> None:
    fake = tmp_path / "site-packages" / "repo_context_hooks"
    fake.mkdir(parents=True)
    monkeypatch.setattr(version_info, "_here", lambda: fake)
    monkeypatch.delenv("UV_PROJECT_ENVIRONMENT", raising=False)
    assert get_install_method() == "pip"


# ---------------------------------------------------------------------------
# Published regex round-trips its own output
# ---------------------------------------------------------------------------


@given(
    ver=st.from_regex(r"\A\d+\.\d+\.\d+(?:[ab]\d+|rc\d+)?\Z"),
    sha=st.one_of(st.none(), st.from_regex(r"\A[0-9a-f]{7}\Z")),
    py=st.from_regex(r"\A\d+\.\d+\.\d+(?:[ab]\d+|rc\d+)?\Z"),
    plat=st.sampled_from(["linux", "darwin", "windows"]),
    install=st.one_of(st.none(), st.sampled_from(["pip", "pipx", "uv"])),
)
def test_rch_version_regex_round_trips_synthetic_output(ver, sha, py, plat, install) -> None:
    parts: list[str] = []
    if sha:
        parts.append(f"git: {sha}")
    parts.append(f"python: {py}")
    parts.append(f"platform: {plat}")
    if install:
        parts.append(f"install: {install}")
    rendered = f"repo-context-hooks {ver} ({', '.join(parts)})"
    m = RCH_VERSION_RE.match(rendered)
    assert m is not None, f"regex failed to parse its own output: {rendered}"
    assert m.group("ver") == ver
    assert m.group("py") == py
    assert m.group("plat") == plat
    if sha:
        assert m.group("sha") == sha
    else:
        assert m.group("sha") is None
    if install:
        assert m.group("install") == install
    else:
        assert m.group("install") is None
