"""Public-API stability gate for `repo-context-hooks`.

Two modes:

1. **Drift check** (default): assert the introspected public surface of the
   currently-installed `repo_context_hooks` matches the committed snapshot at
   `tests/contract/public_surface.json`. Catches unannounced surface changes
   inside a single PR and runs as a `pytest` test so it travels with the
   package -- forks, monorepo vendors, and contributors without GitHub Actions
   are still protected.

2. **Removal check** (`--verify-removals`): in addition to drift, compare the
   current snapshot against the snapshot at the previous release tag. Any
   removal must be excused by a matching `### Deprecated` bullet in the prior
   `CHANGELOG.md` *and* a `### Removed` bullet in the current `[Unreleased]`
   block. This mode runs in CI with `fetch-depth: 0` + `fetch-tags: true` and
   self-verifies it can resolve the prior tag -- a shallow clone hard-fails
   rather than passing silently.

The script is pure stdlib (zero new runtime deps).

See `docs/stability.md` and `docs/deprecation-policy.md` for the contract this
gate enforces.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = REPO_ROOT / "tests" / "contract" / "public_surface.json"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"

ENV_VAR_PATTERN = re.compile(
    r'os\.(?:environ\.get|getenv)\(\s*["\'](REPO_CONTEXT_HOOKS_[A-Z0-9_]+)["\']'
)


# ---------------------------------------------------------------------------
# Introspection
# ---------------------------------------------------------------------------


def introspect_surface() -> dict[str, Any]:
    """Compute the package's current public surface."""
    import repo_context_hooks  # noqa: WPS433
    from repo_context_hooks import cli  # noqa: WPS433

    parser = cli.build_parser()
    sub_action = _find_subparsers_action(parser)
    cli_commands = []
    platform_choices: list[str] = []
    for name in sorted(sub_action.choices):
        sp = sub_action.choices[name]
        flags = _extract_flags(sp)
        sub_subparsers = _extract_subcommands(sp)
        cmd: dict[str, Any] = {"name": name, "flags": flags}
        if sub_subparsers:
            cmd["subcommands"] = sub_subparsers
        cli_commands.append(cmd)
        if name == "install":
            platform_choices = _extract_platform_choices(sp)

    env_vars = sorted(_grep_env_vars(REPO_ROOT / "repo_context_hooks"))

    return {
        "all": sorted(repo_context_hooks.__all__),
        "console_scripts": _read_console_scripts(),
        "cli_commands": cli_commands,
        "platform_choices": platform_choices,
        "env_vars": env_vars,
        "top_level_flags": _extract_top_level_flags(parser),
    }


def _find_subparsers_action(parser: argparse.ArgumentParser) -> argparse._SubParsersAction:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action
    raise RuntimeError("CLI parser exposes no subparsers; cannot introspect public surface.")


def _extract_flags(parser: argparse.ArgumentParser) -> list[str]:
    flags: set[str] = set()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            continue
        if action.option_strings:
            for opt in action.option_strings:
                if opt in ("-h", "--help"):
                    continue
                flags.add(opt)
    return sorted(flags)


def _extract_top_level_flags(parser: argparse.ArgumentParser) -> list[str]:
    """Return the root parser's public option strings.

    Mirrors ``_extract_flags`` but applied to the root parser so we pin
    flags like ``--version`` and ``--debug`` that live above the
    subcommand dispatch. Issue #97 — sibling PR #76 added ``--version``
    at the root and the gate did not pin it; this closes that hole.
    The same private-attribute walk over ``parser._actions`` is used so
    drift in argparse internals surfaces here in one place rather than
    in every subparser walker.
    """
    return _extract_flags(parser)


def _extract_subcommands(parser: argparse.ArgumentParser) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for sub_name in sorted(action.choices):
                sub_parser = action.choices[sub_name]
                out.append({"name": sub_name, "flags": _extract_flags(sub_parser)})
    return out


def _extract_platform_choices(install_parser: argparse.ArgumentParser) -> list[str]:
    for action in install_parser._actions:
        if "--platform" in action.option_strings and action.choices:
            return sorted(action.choices)
    return []


def _read_console_scripts() -> list[str]:
    pyproject = REPO_ROOT / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8-sig")
    in_scripts = False
    scripts: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "[project.scripts]":
            in_scripts = True
            continue
        if in_scripts:
            if stripped.startswith("[") and stripped.endswith("]"):
                break
            if "=" in stripped and not stripped.startswith("#"):
                name = stripped.split("=", 1)[0].strip()
                if name:
                    scripts.append(name)
    return sorted(scripts)


def _grep_env_vars(root: Path) -> set[str]:
    """Walk python sources under `root` and collect every `REPO_CONTEXT_HOOKS_*`
    name read via `os.environ.get(...)` or `os.getenv(...)`.
    """
    found: set[str] = set()
    for path in root.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (UnicodeDecodeError, OSError):
            continue
        for match in ENV_VAR_PATTERN.finditer(text):
            found.add(match.group(1))
    return found


# ---------------------------------------------------------------------------
# Snapshot I/O
# ---------------------------------------------------------------------------


def load_snapshot(path: Path = SNAPSHOT_PATH) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8-sig")
    snap = json.loads(text)
    return _normalize(snap)


def _normalize(snap: dict[str, Any]) -> dict[str, Any]:
    """Drop schema-only metadata so the comparison is over surface keys only."""
    return {k: v for k, v in snap.items() if not k.startswith("_") and k != "schema_version"}


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------


def diff_surface(snapshot: dict[str, Any], current: dict[str, Any]) -> list[str]:
    """Return a list of human-readable drift messages. Empty list = no drift."""
    msgs: list[str] = []
    snap_norm = _normalize(snapshot)
    for pillar in (
        "all",
        "console_scripts",
        "platform_choices",
        "env_vars",
        "top_level_flags",
    ):
        s = set(snap_norm.get(pillar) or [])
        c = set(current.get(pillar) or [])
        for added in sorted(c - s):
            msgs.append(f"[{pillar}] added '{added}' to source but missing from snapshot.")
        for removed in sorted(s - c):
            msgs.append(f"[{pillar}] removed '{removed}' from source but still in snapshot.")

    msgs.extend(
        _diff_cli_commands(
            snap_norm.get("cli_commands") or [],
            current.get("cli_commands") or [],
        )
    )
    return msgs


def _diff_cli_commands(snap_cmds: list[dict[str, Any]], cur_cmds: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    snap_by_name = {c["name"]: c for c in snap_cmds}
    cur_by_name = {c["name"]: c for c in cur_cmds}
    for added in sorted(set(cur_by_name) - set(snap_by_name)):
        out.append(f"[cli_commands] added subcommand '{added}' not in snapshot.")
    for removed in sorted(set(snap_by_name) - set(cur_by_name)):
        out.append(f"[cli_commands] removed subcommand '{removed}' still in snapshot.")
    for name in sorted(set(snap_by_name) & set(cur_by_name)):
        s_flags = set(snap_by_name[name].get("flags") or [])
        c_flags = set(cur_by_name[name].get("flags") or [])
        for added in sorted(c_flags - s_flags):
            out.append(f"[cli_commands] '{name}': added flag '{added}' not in snapshot.")
        for removed in sorted(s_flags - c_flags):
            out.append(f"[cli_commands] '{name}': removed flag '{removed}' still in snapshot.")
        s_subs = {x["name"]: x for x in snap_by_name[name].get("subcommands") or []}
        c_subs = {x["name"]: x for x in cur_by_name[name].get("subcommands") or []}
        for added in sorted(set(c_subs) - set(s_subs)):
            out.append(f"[cli_commands] '{name} {added}': added subcommand not in snapshot.")
        for removed in sorted(set(s_subs) - set(c_subs)):
            out.append(f"[cli_commands] '{name} {removed}': removed subcommand still in snapshot.")
        for sub_name in sorted(set(s_subs) & set(c_subs)):
            s_sub_flags = set(s_subs[sub_name].get("flags") or [])
            c_sub_flags = set(c_subs[sub_name].get("flags") or [])
            for added in sorted(c_sub_flags - s_sub_flags):
                out.append(f"[cli_commands] '{name} {sub_name}': added flag '{added}' not in snapshot.")
            for removed in sorted(s_sub_flags - c_sub_flags):
                out.append(f"[cli_commands] '{name} {sub_name}': removed flag '{removed}' still in snapshot.")
    return out


# ---------------------------------------------------------------------------
# Removal-vs-prior-tag mode
# ---------------------------------------------------------------------------


def removed_symbols_vs_baseline(baseline_snap: dict[str, Any], current_snap: dict[str, Any]) -> list[str]:
    """Symbols present in baseline_snap but absent from current_snap."""
    removed: list[str] = []
    snap_a = _normalize(baseline_snap)
    snap_b = _normalize(current_snap)
    for pillar in (
        "all",
        "console_scripts",
        "platform_choices",
        "env_vars",
        "top_level_flags",
    ):
        a = set(snap_a.get(pillar) or [])
        b = set(snap_b.get(pillar) or [])
        for sym in sorted(a - b):
            removed.append(f"{pillar}:{sym}")
    a_cmds = {c["name"]: c for c in snap_a.get("cli_commands") or []}
    b_cmds = {c["name"]: c for c in snap_b.get("cli_commands") or []}
    for name in sorted(set(a_cmds) - set(b_cmds)):
        removed.append(f"cli_commands:{name}")
    for name in sorted(set(a_cmds) & set(b_cmds)):
        a_flags = set(a_cmds[name].get("flags") or [])
        b_flags = set(b_cmds[name].get("flags") or [])
        for f in sorted(a_flags - b_flags):
            removed.append(f"cli_commands:{name}:{f}")
    return removed


def parse_changelog_deprecations(changelog_text: str) -> dict[str, list[str]]:
    """Return `{version_header: [bullet_text, ...]}` for every `### Deprecated`
    block. Tolerant of utf-8-sig BOM, CRLF endings, and mixed-case headings.
    """
    text = changelog_text.replace("\r\n", "\n").replace("\r", "\n")
    if text.startswith("﻿"):
        text = text[1:]
    out: dict[str, list[str]] = {}
    current_version: str | None = None
    in_deprecated = False
    bullets: list[str] = []
    for line in text.split("\n"):
        m = re.match(r"^##\s+\[([^\]]+)\]", line.strip())
        if m:
            if current_version is not None and bullets:
                out.setdefault(current_version, []).extend(bullets)
            current_version = m.group(1)
            in_deprecated = False
            bullets = []
            continue
        h3 = re.match(r"^###\s+(\w+)", line.strip())
        if h3:
            if in_deprecated and bullets and current_version is not None:
                out.setdefault(current_version, []).extend(bullets)
                bullets = []
            in_deprecated = h3.group(1).lower() == "deprecated"
            continue
        if in_deprecated and line.strip().startswith("-"):
            bullets.append(line.strip())
    if in_deprecated and bullets and current_version is not None:
        out.setdefault(current_version, []).extend(bullets)
    return out


def parse_changelog_removed_unreleased(changelog_text: str) -> list[str]:
    """Bullets under `[Unreleased] ### Removed`. Same tolerance as above."""
    text = changelog_text.replace("\r\n", "\n").replace("\r", "\n")
    if text.startswith("﻿"):
        text = text[1:]
    in_unreleased = False
    in_removed = False
    bullets: list[str] = []
    for line in text.split("\n"):
        m = re.match(r"^##\s+\[([^\]]+)\]", line.strip())
        if m:
            in_unreleased = m.group(1).lower() == "unreleased"
            in_removed = False
            continue
        h3 = re.match(r"^###\s+(\w+)", line.strip())
        if h3 and in_unreleased:
            in_removed = h3.group(1).lower() == "removed"
            continue
        if in_unreleased and in_removed and line.strip().startswith("-"):
            bullets.append(line.strip())
    return bullets


def _bullet_mentions(bullets: Iterable[str], symbol: str) -> bool:
    return any(symbol in b for b in bullets)


def explain_removal_violation(
    removed_key: str,
    deprecations: dict[str, list[str]],
    removed_bullets: list[str],
) -> str | None:
    """Return None if the removal is excused, else a human-readable error."""
    pillar, _, rest = removed_key.partition(":")
    symbol = rest.split(":")[-1] if ":" in rest else rest
    deprecated_anywhere = any(_bullet_mentions(bs, symbol) for bs in deprecations.values())
    removed_now = _bullet_mentions(removed_bullets, symbol)
    if deprecated_anywhere and removed_now:
        return None
    parts = [f"public-surface removal '{removed_key}' is not excused."]
    if not deprecated_anywhere:
        parts.append(
            f"  No prior `### Deprecated` CHANGELOG entry mentions `{symbol}`. "
            "See docs/deprecation-policy.md -- a removal must be deprecated for one full MINOR cycle first."
        )
    if not removed_now:
        parts.append(
            f"  No `### Removed` entry under `[Unreleased]` mentions `{symbol}`. "
            "Add one citing the prior `### Deprecated` entry."
        )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Git baseline access
# ---------------------------------------------------------------------------


def can_resolve_prior_tag(repo: Path = REPO_ROOT) -> tuple[bool, str | None, str]:
    """Return (ok, tag_name, diagnostic). When ok is False, the diagnostic is an
    actionable message for the operator.
    """
    try:
        result = subprocess.run(
            ["git", "tag", "--sort=-v:refname"],
            cwd=str(repo),
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False, None, "git is not on PATH; cannot resolve prior tag for removal check."
    if result.returncode != 0:
        return False, None, f"git tag failed: {result.stderr.strip()}"
    tags = [t for t in result.stdout.splitlines() if t.strip()]
    if not tags:
        return False, None, (
            "No tags reachable. If running in CI, set `fetch-depth: 0` and `fetch-tags: true` on actions/checkout. "
            "If this is the first release before any tag exists, the removal check is a no-op and you may skip "
            "`--verify-removals` for this run only."
        )
    return True, tags[0], ""


def load_snapshot_at_ref(ref: str, repo: Path = REPO_ROOT) -> dict[str, Any] | None:
    """Read `tests/contract/public_surface.json` as it existed at `ref`. Returns
    None if the file did not exist there.
    """
    rel = "tests/contract/public_surface.json"
    result = subprocess.run(
        ["git", "show", f"{ref}:{rel}"],
        cwd=str(repo),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return _normalize(json.loads(result.stdout))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="check_public_surface",
        description="Public-API stability gate for repo-context-hooks.",
    )
    p.add_argument(
        "--verify-removals",
        action="store_true",
        help="Also diff against the snapshot at the previous release tag and require deprecation excuses.",
    )
    p.add_argument(
        "--snapshot",
        default=str(SNAPSHOT_PATH),
        help="Path to the committed snapshot file.",
    )
    args = p.parse_args(argv)

    snap_path = Path(args.snapshot)
    snapshot = load_snapshot(snap_path)
    current = introspect_surface()

    drift = diff_surface(snapshot, current)
    if drift:
        print("PUBLIC SURFACE DRIFT -- snapshot does not match introspected package state.")
        print("Edit `tests/contract/public_surface.json` in the same PR as the source change,")
        print("or revert the source change. See docs/stability.md for the contract.\n")
        for msg in drift:
            print(f"  {msg}")
        return 1

    if not args.verify_removals:
        return 0

    ok, tag, diag = can_resolve_prior_tag()
    if not ok:
        print(f"PUBLIC SURFACE GATE: cannot run --verify-removals.\n  {diag}")
        return 2

    baseline = load_snapshot_at_ref(tag)
    if baseline is None:
        print(
            f"No baseline `tests/contract/public_surface.json` at tag {tag}; "
            "this is the first release of the gate. Treating as bootstrap (exit 0)."
        )
        return 0

    removals = removed_symbols_vs_baseline(baseline, snapshot)
    if not removals:
        return 0

    changelog_text = CHANGELOG_PATH.read_text(encoding="utf-8-sig")
    deprecations = parse_changelog_deprecations(changelog_text)
    removed_bullets = parse_changelog_removed_unreleased(changelog_text)

    violations = []
    for r in removals:
        msg = explain_removal_violation(r, deprecations, removed_bullets)
        if msg:
            violations.append(msg)

    if not violations:
        return 0

    print("PUBLIC SURFACE REMOVAL violates the deprecation contract.\n")
    for v in violations:
        print(v)
        print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
