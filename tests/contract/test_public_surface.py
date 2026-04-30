"""Public-API stability contract tests for `repo-context-hooks` (issue #72).

These tests are the primary enforcement of the contract documented in
`docs/stability.md` and `docs/deprecation-policy.md`. They run on every
`pytest` invocation, so the contract travels with the package -- forks,
monorepo vendors, and contributors without GitHub Actions are still
protected. The CI gate (`scripts/check_public_surface.py --verify-removals`)
adds removal-vs-prior-tag enforcement on top.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import check_public_surface as gate  # noqa: E402


# ---------------------------------------------------------------------------
# Drift check -- the primary gate
# ---------------------------------------------------------------------------


def test_snapshot_matches_introspected_surface():
    """The committed snapshot must match the running package, exactly.

    If this fails, edit `tests/contract/public_surface.json` in the same PR
    as the source change, or revert the source change. See docs/stability.md.
    """
    snapshot = gate.load_snapshot()
    current = gate.introspect_surface()
    drift = gate.diff_surface(snapshot, current)
    assert drift == [], "Public-surface drift:\n" + "\n".join(f"  {m}" for m in drift)


def test_every_name_in_dunder_all_is_importable():
    import repo_context_hooks

    for name in repo_context_hooks.__all__:
        assert hasattr(repo_context_hooks, name), (
            f"`__all__` lists `{name}` but `repo_context_hooks` does not expose it. "
            "Either add the attribute or remove the entry from `__all__`."
        )


def test_module_surface_pins_logging_setup_helpers():
    """Cross-PR composability gate (issue #73 -> #74).

    M6's `verify` command imports `configure_logging`, `get_last_error`, and
    `log_path` from `repo_context_hooks.logging_setup`. Pin them so a rename
    is a contract event, not a silent break.
    """
    import importlib

    snapshot = gate.load_snapshot()
    pinned = snapshot.get("module_surface") or {}
    for module_name, names in pinned.items():
        if module_name.startswith("_"):
            continue
        mod = importlib.import_module(module_name)
        for name in names:
            assert hasattr(mod, name) and callable(getattr(mod, name)), (
                f"`{module_name}.{name}` is pinned in public_surface.json::module_surface "
                f"but is missing or not callable. Sibling PRs (e.g. M6 verify) import this."
            )


def test_doctor_json_emits_pinned_keys(tmp_path):
    """`doctor --json` keys are a sibling-PR contract — M6 verify reads them."""
    import contextlib
    import io
    import json as _json
    from argparse import Namespace

    from repo_context_hooks import cli as _cli

    snapshot = gate.load_snapshot()
    pinned_keys = set((snapshot.get("json_output_keys") or {}).get("doctor") or [])
    args = Namespace(
        platform=None,
        all_platforms=False,
        repo_root=str(tmp_path),
        json=True,
    )
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _cli._doctor(args)
    payload = _json.loads(buf.getvalue())
    missing = pinned_keys - set(payload.keys())
    assert not missing, f"doctor --json missing pinned keys: {sorted(missing)}"


def test_no_undocumented_env_var():
    """Every `REPO_CONTEXT_HOOKS_*` env var read by the package must be in
    the snapshot. Catches the 'added a new env var, forgot to document it'
    failure mode at PR time, not in the wild.
    """
    snapshot = gate.load_snapshot()
    documented = set(snapshot.get("env_vars") or [])
    found = gate._grep_env_vars(REPO_ROOT / "repo_context_hooks")
    undocumented = found - documented
    assert not undocumented, (
        f"Undocumented public env vars referenced in source: {sorted(undocumented)}. "
        "Add them to tests/contract/public_surface.json::env_vars and document them in "
        "docs/stability.md and TELEMETRY.md."
    )


# ---------------------------------------------------------------------------
# Drift check edge cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "snapshot,current,expected_drift",
    [
        pytest.param(
            {
                "all": ["a"],
                "console_scripts": [],
                "platform_choices": [],
                "env_vars": [],
                "cli_commands": [],
            },
            {
                "all": ["a"],
                "console_scripts": [],
                "platform_choices": [],
                "env_vars": [],
                "cli_commands": [],
            },
            [],
            id="empty-diff",
        ),
        pytest.param(
            {
                "all": ["a"],
                "console_scripts": [],
                "platform_choices": [],
                "env_vars": [],
                "cli_commands": [],
            },
            {
                "all": ["a", "b"],
                "console_scripts": [],
                "platform_choices": [],
                "env_vars": [],
                "cli_commands": [],
            },
            ["[all] added 'b' to source but missing from snapshot."],
            id="pure-addition-fails-drift",
        ),
        pytest.param(
            {
                "all": ["a", "b"],
                "console_scripts": [],
                "platform_choices": [],
                "env_vars": [],
                "cli_commands": [],
            },
            {
                "all": ["a"],
                "console_scripts": [],
                "platform_choices": [],
                "env_vars": [],
                "cli_commands": [],
            },
            ["[all] removed 'b' from source but still in snapshot."],
            id="silent-removal-fails-drift",
        ),
        pytest.param(
            {
                "all": [],
                "console_scripts": [],
                "platform_choices": ["x", "y"],
                "env_vars": [],
                "cli_commands": [],
            },
            {
                "all": [],
                "console_scripts": [],
                "platform_choices": ["x"],
                "env_vars": [],
                "cli_commands": [],
            },
            ["[platform_choices] removed 'y' from source but still in snapshot."],
            id="platform-choice-removal-detected",
        ),
        pytest.param(
            {
                "all": [],
                "console_scripts": [],
                "platform_choices": [],
                "env_vars": [],
                "cli_commands": [{"name": "install", "flags": ["--platform"]}],
            },
            {
                "all": [],
                "console_scripts": [],
                "platform_choices": [],
                "env_vars": [],
                "cli_commands": [{"name": "install", "flags": []}],
            },
            ["[cli_commands] 'install': removed flag '--platform' still in snapshot."],
            id="cli-flag-removal-detected",
        ),
    ],
)
def test_diff_surface_table(snapshot, current, expected_drift):
    assert gate.diff_surface(snapshot, current) == expected_drift


# ---------------------------------------------------------------------------
# Removal-vs-baseline excuse logic
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "baseline,current,changelog,expected_violations",
    [
        pytest.param(
            {"all": ["a"], "cli_commands": []},
            {"all": ["a"], "cli_commands": []},
            "## [Unreleased]\n",
            0,
            id="no-removal-no-violation",
        ),
        pytest.param(
            {"all": ["a", "b"], "cli_commands": []},
            {"all": ["a"], "cli_commands": []},
            "## [Unreleased]\n",
            1,
            id="removal-with-no-deprecation-and-no-removed-entry-fails",
        ),
        pytest.param(
            {"all": ["a", "b"], "cli_commands": []},
            {"all": ["a"], "cli_commands": []},
            "## [Unreleased]\n### Removed\n- `b` removed; was deprecated in 1.1.\n## [1.1.0] - 2026-05-01\n### Deprecated\n- `b` deprecated, use `a` instead.\n",
            0,
            id="removal-with-prior-deprecation-and-current-removed-passes",
        ),
        pytest.param(
            {"all": ["a", "b"], "cli_commands": []},
            {"all": ["a"], "cli_commands": []},
            "## [Unreleased]\n## [1.1.0] - 2026-05-01\n### Deprecated\n- `b` deprecated.\n",
            1,
            id="prior-deprecation-but-no-current-removed-bullet-fails",
        ),
        pytest.param(
            {"all": ["a", "b"], "cli_commands": []},
            {"all": ["a"], "cli_commands": []},
            "## [Unreleased]\n### Removed\n- `b` removed.\n",
            1,
            id="current-removed-but-no-prior-deprecation-fails",
        ),
        pytest.param(
            {
                "cli_commands": [
                    {"name": "install", "flags": ["--platform", "--legacy"]}
                ]
            },
            {"cli_commands": [{"name": "install", "flags": ["--platform"]}]},
            "## [Unreleased]\n",
            1,
            id="cli-flag-removal-without-excuse-fails",
        ),
        pytest.param(
            {
                "cli_commands": [
                    {"name": "install", "flags": ["--platform", "--legacy"]}
                ]
            },
            {"cli_commands": [{"name": "install", "flags": ["--platform"]}]},
            "## [Unreleased]\n### Removed\n- `--legacy` flag removed; deprecated in 1.1.\n## [1.1.0] - 2026-05-01\n### Deprecated\n- `--legacy` flag deprecated.\n",
            0,
            id="cli-flag-removal-with-deprecation-passes",
        ),
    ],
)
def test_removal_excuse_logic(baseline, current, changelog, expected_violations):
    baseline_full = {
        "all": baseline.get("all", []),
        "console_scripts": [],
        "platform_choices": [],
        "env_vars": [],
        "cli_commands": baseline.get("cli_commands", []),
    }
    current_full = {
        "all": current.get("all", []),
        "console_scripts": [],
        "platform_choices": [],
        "env_vars": [],
        "cli_commands": current.get("cli_commands", []),
    }
    removals = gate.removed_symbols_vs_baseline(baseline_full, current_full)
    deprecations = gate.parse_changelog_deprecations(changelog)
    removed_bullets = gate.parse_changelog_removed_unreleased(changelog)
    violations = [
        gate.explain_removal_violation(r, deprecations, removed_bullets)
        for r in removals
    ]
    actual = sum(1 for v in violations if v is not None)
    assert actual == expected_violations, f"violations={violations}"


def test_removed_then_readded_in_same_pr_is_not_flagged():
    """The gate compares baseline-tag vs HEAD only. If a symbol is removed in
    commit N and re-added in commit N+1 of the same branch, the net diff is
    empty and the gate stays green.
    """
    baseline = {
        "all": ["a", "b"],
        "console_scripts": [],
        "platform_choices": [],
        "env_vars": [],
        "cli_commands": [],
    }
    current = {
        "all": ["a", "b"],
        "console_scripts": [],
        "platform_choices": [],
        "env_vars": [],
        "cli_commands": [],
    }
    removals = gate.removed_symbols_vs_baseline(baseline, current)
    assert removals == []


# ---------------------------------------------------------------------------
# CHANGELOG parser tolerance (Critic C: utf-8-sig + CRLF + mixed case)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    [
        pytest.param(
            "﻿## [1.1.0]\n### Deprecated\n- `foo` deprecated.\n", id="utf-8-sig-bom"
        ),
        pytest.param(
            "## [1.1.0]\r\n### Deprecated\r\n- `foo` deprecated.\r\n",
            id="crlf-line-endings",
        ),
        pytest.param(
            "## [1.1.0]\n### deprecated\n- `foo` deprecated.\n", id="lowercase-heading"
        ),
        pytest.param(
            "## [1.1.0]\n### DEPRECATED\n- `foo` deprecated.\n", id="uppercase-heading"
        ),
    ],
)
def test_changelog_parser_handles_quirky_input(raw):
    deprecations = gate.parse_changelog_deprecations(raw)
    flat = [b for bs in deprecations.values() for b in bs]
    assert any(
        "foo" in b for b in flat
    ), f"Expected `foo` in parsed bullets; got {deprecations}"


def test_unreleased_removed_section_isolated_from_release_versions():
    """A `### Removed` block under a tagged version must not be confused with
    one under `[Unreleased]`. Only `[Unreleased]`'s `### Removed` excuses a
    removal in *this* PR.
    """
    changelog = textwrap.dedent(
        """\
        ## [Unreleased]
        ## [1.0.0]
        ### Removed
        - `historic_thing` removed in 1.0.
        """
    )
    bullets = gate.parse_changelog_removed_unreleased(changelog)
    assert bullets == [], (
        "parse_changelog_removed_unreleased must only return bullets under [Unreleased]; "
        f"got {bullets}"
    )


# ---------------------------------------------------------------------------
# DeprecationWarning surfaces to end users (Critic C2)
# ---------------------------------------------------------------------------


def test_deprecation_warning_surfaces_with_default_filters():
    """If `pyproject.toml` ever globally silences DeprecationWarning, our entire
    deprecation contract becomes a lie. Run a fresh subprocess with default
    warning filters and confirm a DeprecationWarning hits stderr.
    """
    code = (
        "import warnings; "
        "warnings.warn('repo-context-hooks-deprecation-test', DeprecationWarning, stacklevel=1)"
    )
    result = subprocess.run(
        [sys.executable, "-W", "default", "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert "repo-context-hooks-deprecation-test" in result.stderr, (
        "DeprecationWarning did not surface with default warning filters. "
        f"stderr={result.stderr!r}"
    )


def test_pyproject_does_not_globally_silence_deprecation_warnings():
    """Hard-fail if a future `[tool.pytest.ini_options] filterwarnings` ever
    silences DeprecationWarning unconditionally. Ignore-with-a-pattern is OK.
    """
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8-sig")
    bad_lines = [
        ln
        for ln in pyproject_text.splitlines()
        if "ignore::DeprecationWarning" in ln.replace(" ", "")
        and not ln.strip().startswith("#")
    ]
    assert not bad_lines, (
        "Found unconditional `ignore::DeprecationWarning` in pyproject.toml. "
        "This breaks the deprecation contract -- our DeprecationWarnings would never surface to users. "
        f"Offending lines: {bad_lines}"
    )


# ---------------------------------------------------------------------------
# Bootstrap / shallow-clone safety (Critic C1, C5)
# ---------------------------------------------------------------------------


def test_can_resolve_prior_tag_self_reports():
    """The helper must return an actionable diagnostic (not silently True) when
    no tags are reachable.
    """
    ok, tag, diag = gate.can_resolve_prior_tag()
    if not ok:
        assert "fetch-depth" in diag.lower() or "git" in diag.lower(), diag
    else:
        assert tag, "ok=True but tag is empty"


def test_load_snapshot_at_missing_ref_returns_none():
    assert gate.load_snapshot_at_ref("definitely-not-a-real-ref-12345") is None
