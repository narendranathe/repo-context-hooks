"""Rich version-string assembly for the `--version` CLI flag.

This is the implementation of issue #76's third deliverable: a `--version`
output that lets a user reporting a hook regression name the exact build
that shipped the regression. The format is:

    repo-context-hooks <semver> [(git: <sha7>, )]python: <pep440>, platform: <os>[, install: <method>])

Stdlib only. The package's `dependencies = []` contract is non-negotiable.

The git SHA segment is OMITTED unless we can prove three things:

1. `__file__` is NOT inside a `site-packages/` tree (so we are running from
   a checkout, not a wheel install).
2. `git rev-parse --show-toplevel` resolves a directory that is an ancestor
   of `__file__`.
3. That toplevel's `pyproject.toml` declares `name = "repo-context-hooks"`.

(3) is the monorepo guard. Without it, an editable install of this package
inside an unrelated parent monorepo would emit the OUTER monorepo's HEAD
SHA, which is exactly the misattribution this feature exists to prevent.

Every external operation (subprocess, file read, regex parse) is wrapped in
a fail-soft try/except. The CLI never crashes because of `--version`; at
worst we omit the optional segments and print bare `name <semver>`.
"""

from __future__ import annotations

import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from . import __version__

# Published regex for downstream consumers (issue dashboards, support bots).
# Groups: ver, sha (optional), py, plat, install (optional).
RCH_VERSION_RE = re.compile(
    r"^repo-context-hooks (?P<ver>\S+)"
    r" \("
    r"(?:git: (?P<sha>[0-9a-f]{7}), )?"
    r"python: (?P<py>[^,]+), "
    r"platform: (?P<plat>[^,)]+)"
    r"(?:, install: (?P<install>[^)]+))?"
    r"\)$"
)

# How long we tolerate `git` taking before declaring the SHA unknowable.
# Keep tight: this runs on every `--version` invocation. (Critic A: zero-config
# adopters will not appreciate a hung CLI on a slow filesystem.)
_GIT_TIMEOUT_SECONDS = 1.0


def _here() -> Path:
    return Path(__file__).resolve().parent


def _is_site_packages(path: Path) -> bool:
    """True if any path component is `site-packages`. Identifies wheel installs."""
    return "site-packages" in path.parts


def _run_git(args: list[str], cwd: Path) -> Optional[str]:
    """Run `git <args>` in `cwd` with hardened defaults; return stdout or None.

    Catches every exception that has been observed in the wild on this surface:
    `FileNotFoundError` (no git binary), `TimeoutExpired` (slow disk),
    `UnicodeError` (non-ASCII path on Windows cp1252), `OSError` (permissions,
    EBADF, etc.), and the generic `SubprocessError` umbrella.
    """
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_SECONDS,
            errors="replace",
            check=False,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return None
    if result.returncode != 0:
        return None
    out = result.stdout.strip()
    return out or None


def _toplevel_owns_us(toplevel: Path) -> bool:
    """Verify `toplevel/pyproject.toml` declares `name = "repo-context-hooks"`.

    Uses tomllib on 3.11+; falls back to a minimal regex on 3.9/3.10 because the
    package's `dependencies = []` contract forbids adding `tomli`. The regex is
    deliberately strict (anchored on a `[project]` section's `name = "..."`).
    """
    pyproject = toplevel / "pyproject.toml"
    try:
        text = pyproject.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False

    if sys.version_info >= (3, 11):
        try:
            import tomllib  # type: ignore[import-not-found]

            data = tomllib.loads(text)
        except Exception:  # noqa: BLE001 — fail-soft on any parse error
            return False
        return data.get("project", {}).get("name") == "repo-context-hooks"

    # Stdlib-only fallback for Python 3.9 / 3.10.
    in_project = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("["):
            in_project = line == "[project]"
            continue
        if not in_project:
            continue
        m = re.match(r'^name\s*=\s*"([^"]+)"\s*$', line)
        if m:
            return m.group(1) == "repo-context-hooks"
    return False


def get_git_sha() -> Optional[str]:
    """Return short git SHA of THIS package's repo, or None.

    Returns None unless all of:
      - we're not running from site-packages,
      - `git rev-parse --show-toplevel` succeeds and is an ancestor of __file__,
      - that toplevel's pyproject.toml declares `name = "repo-context-hooks"`.
    """
    here = _here()
    if _is_site_packages(here):
        return None

    toplevel_str = _run_git(["rev-parse", "--show-toplevel"], cwd=here)
    if not toplevel_str:
        return None
    try:
        toplevel = Path(toplevel_str).resolve()
    except (OSError, ValueError):
        return None

    # `here` must equal `toplevel` or be a descendant of it. (Sanity:
    # otherwise git resolved something unrelated.)
    if toplevel != here and toplevel not in here.parents:
        return None

    if not _toplevel_owns_us(toplevel):
        return None

    sha = _run_git(["rev-parse", "--short=7", "HEAD"], cwd=toplevel)
    if not sha or not re.fullmatch(r"[0-9a-f]{7}", sha):
        return None
    return sha


def get_install_method() -> Optional[str]:
    """Best-effort install-method heuristic; None if ambiguous.

    Adopters debugging a regression want to know how the binary they're running
    was installed. The detection is intentionally conservative — when in doubt,
    return None rather than guess wrong.
    """
    here = _here()
    parts = here.parts

    # pipx isolates each tool in `~/.local/pipx/venvs/<name>/...`. The path is
    # the most reliable signal across OSes.
    if any("pipx" in part for part in parts) and "venvs" in parts:
        return "pipx"

    # uv-managed venvs set this env var when active; uv-installed tools don't
    # always set it, so absence is not proof. But presence is a strong signal.
    if os.environ.get("UV_PROJECT_ENVIRONMENT"):
        return "uv"

    # uv tool installs land under `~/.local/share/uv/tools/<name>/...` on linux
    # and similar on other OSes; check for the `uv/tools` segment.
    for i, part in enumerate(parts[:-1]):
        if part == "uv" and parts[i + 1] == "tools":
            return "uv"

    # If we got here from site-packages without a more specific signal, assume
    # `pip`. From a source checkout, return None (no install happened).
    if _is_site_packages(here):
        return "pip"
    return None


def format_version() -> str:
    """Assemble the rich version string. Never raises."""
    try:
        sha = get_git_sha()
    except Exception:  # noqa: BLE001
        sha = None
    try:
        install = get_install_method()
    except Exception:  # noqa: BLE001
        install = None

    py = platform.python_version()  # full PEP 440 form (preserves alphas/betas)
    plat = platform.system().lower() or sys.platform

    segments: list[str] = []
    if sha:
        segments.append(f"git: {sha}")
    segments.append(f"python: {py}")
    segments.append(f"platform: {plat}")
    if install:
        segments.append(f"install: {install}")

    return f"repo-context-hooks {__version__} ({', '.join(segments)})"
