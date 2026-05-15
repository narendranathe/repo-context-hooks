"""Render docs/cli-reference.md from repo_context_hooks.cli:build_parser.

The CLI is argparse-based, so the standard mkdocs-click plugin does not apply.
Instead we introspect the parser, emit a deterministic Markdown rendering, and
gate drift in CI via tests/contract/test_docs_contract.py — same "no drift"
guarantee as mkdocs-click without the plugin or the runtime dep.

Usage:
    python scripts/render_cli_reference.py --check   # exit 1 if file is stale
    python scripts/render_cli_reference.py --write   # regenerate the file

Stdlib-only by design — same discipline as scripts/check_public_surface.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET = REPO_ROOT / "docs" / "cli-reference.md"

# Import path: the script may run from a fresh checkout where the package is
# not yet installed. Ensure the repo root is on sys.path so `import
# repo_context_hooks.cli` succeeds without a `pip install -e .`.
sys.path.insert(0, str(REPO_ROOT))

from repo_context_hooks.cli import build_parser  # noqa: E402

HEADER = """# CLI Reference

This page is auto-generated from `repo_context_hooks.cli:build_parser`. Do not
edit by hand — your changes will be overwritten the next time the CI drift gate
regenerates it.

To regenerate after editing the parser:

```bash
python scripts/render_cli_reference.py --write
```

The drift check that runs in CI is:

```bash
python scripts/render_cli_reference.py --check
```

The full list of stable subcommands and flags is also pinned in
[`docs/stability.md`](stability.md) — every name on this page is part of the
v1.0 public contract and follows the
[deprecation policy](deprecation-policy.md) before removal.

"""


def _format_flag(action: argparse.Action) -> str:
    """Render a single argparse Action as a Markdown bullet body."""
    names = ", ".join(f"`{s}`" for s in action.option_strings) or f"`{action.dest}`"
    metavar = ""
    if action.option_strings and action.metavar:
        metavar = f" {action.metavar}"
    elif action.option_strings and action.choices:
        metavar = " {" + ",".join(str(c) for c in action.choices) + "}"
    elif action.option_strings and action.nargs is None and not isinstance(
        action,
        (argparse._StoreTrueAction, argparse._StoreFalseAction, argparse._CountAction, argparse._HelpAction),
    ):
        metavar = f" {action.dest.upper()}"
    help_text = (action.help or "").strip()
    if help_text and not help_text.endswith("."):
        help_text += "."
    return f"- {names}{metavar} — {help_text}"


def _iter_subparsers(parser: argparse.ArgumentParser):
    """Yield (name, subparser) pairs for every subcommand registered."""
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, sub in action.choices.items():
                yield name, sub


def _render_subparser(name: str, sub: argparse.ArgumentParser, level: int) -> str:
    """Render a subparser as a Markdown section."""
    heading = "#" * level
    lines: list[str] = []
    lines.append(f"{heading} `{name}`")
    lines.append("")
    description = (sub.description or "").strip()
    if description:
        lines.append(description)
        lines.append("")
    flags = [
        a
        for a in sub._actions
        if a.option_strings and not isinstance(a, argparse._HelpAction)
    ]
    if flags:
        lines.append("Flags:")
        lines.append("")
        for action in flags:
            lines.append(_format_flag(action))
        lines.append("")
    nested = list(_iter_subparsers(sub))
    if nested:
        lines.append("Sub-commands:")
        lines.append("")
        for nested_name, nested_sub in nested:
            lines.append(_render_subparser(nested_name, nested_sub, level + 1))
    return "\n".join(lines).rstrip() + "\n\n"


def render(parser: argparse.ArgumentParser) -> str:
    """Render the full parser into a Markdown document."""
    lines: list[str] = [HEADER.rstrip(), ""]
    lines.append("## `repo-context-hooks`")
    lines.append("")
    description = (parser.description or "").strip()
    if description:
        lines.append(description)
        lines.append("")
    top_level = [
        a
        for a in parser._actions
        if a.option_strings and not isinstance(a, argparse._HelpAction)
    ]
    if top_level:
        lines.append("Top-level flags:")
        lines.append("")
        for action in top_level:
            lines.append(_format_flag(action))
        lines.append("")
    lines.append("## Subcommands")
    lines.append("")
    for name, sub in _iter_subparsers(parser):
        lines.append(_render_subparser(name, sub, 3))
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Exit 1 if file is stale.")
    mode.add_argument("--write", action="store_true", help="Regenerate the file.")
    args = parser.parse_args(argv)

    rendered = render(build_parser())
    if args.write:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        TARGET.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"Wrote {TARGET.relative_to(REPO_ROOT)} ({len(rendered)} bytes)")
        return 0

    if not TARGET.exists():
        print(f"FAIL: {TARGET.relative_to(REPO_ROOT)} does not exist", file=sys.stderr)
        print("Run: python scripts/render_cli_reference.py --write", file=sys.stderr)
        return 1
    current = TARGET.read_text(encoding="utf-8")
    if current != rendered:
        print(
            f"FAIL: {TARGET.relative_to(REPO_ROOT)} is stale relative to "
            f"repo_context_hooks.cli:build_parser",
            file=sys.stderr,
        )
        print("Run: python scripts/render_cli_reference.py --write", file=sys.stderr)
        return 1
    print(f"OK: {TARGET.relative_to(REPO_ROOT)} is up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
