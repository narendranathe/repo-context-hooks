"""Smoke test: every bundled hook script must be syntactically valid Python.

``repo_context_hooks/bundle/scripts/*`` is shipped INTO end-user agent_home
directories and executed as Claude/Codex hook subprocesses on session events
(SessionStart, PreCompact, PostCompact, SessionEnd). The coverage gate
deliberately omits this path (see ``[tool.coverage.run].omit`` in
``pyproject.toml``) because it's exercised by the install-smoke-test CI job,
not by unit tests. But "exercised in CI" only catches runtime errors on the
specific code paths the smoke job hits — a typo in an import block on a
seldom-triggered hook would ship green and only fail on a user's machine.

This test compiles every bundled script with ``py_compile`` so a bad
``from __future__`` placement, a stray syntax error, or an invalid encoding
fails CI before merge. (audit F2.1)
"""
from __future__ import annotations

import py_compile
from pathlib import Path

import repo_context_hooks


def test_all_bundled_hook_scripts_compile() -> None:
    bundle_root = Path(repo_context_hooks.__file__).resolve().parent / "bundle"
    scripts_root = bundle_root / "scripts"
    if not scripts_root.exists():
        return  # Bundle layout may evolve; skip cleanly if scripts/ moves.

    py_files = sorted(scripts_root.rglob("*.py"))
    assert py_files, f"no bundled scripts found under {scripts_root}"

    for path in py_files:
        # ``doraise=True`` makes a syntax error raise PyCompileError instead of
        # just printing to stderr. The default cache file goes alongside the
        # source — that's fine for a CI smoke test.
        py_compile.compile(str(path), doraise=True)


def test_all_bundled_skill_scripts_compile() -> None:
    """Same contract for any .py shipped under bundle/skills/*/scripts/."""
    bundle_root = Path(repo_context_hooks.__file__).resolve().parent / "bundle"
    skills_root = bundle_root / "skills"
    if not skills_root.exists():
        return

    py_files = sorted(skills_root.rglob("*.py"))
    if not py_files:
        return  # Some skills are markdown-only; that's fine.

    for path in py_files:
        py_compile.compile(str(path), doraise=True)
