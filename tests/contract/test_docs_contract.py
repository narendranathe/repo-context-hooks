"""Docs contract tests (issue #75).

These tests travel with the package — forks and contributors who run the test
suite without the docs CI job in CI still get the same drift / staleness /
CDN gates. Stdlib-only by discipline, matching `test_public_surface.py` and
`test_dependabot_policy.py`.

The three gates:

1. CLI-reference drift — every subcommand on `repo_context_hooks.cli:build_parser`
   must appear literally in the committed `docs/cli-reference.md`. The
   pre-render script (`scripts/render_cli_reference.py`) is the source of
   truth; this test re-runs the renderer in-process and diffs against the
   committed file so contributors who edit `cli.py` without re-rendering
   get an immediate test failure rather than a silently stale docs site.

2. Troubleshooting freshness — every H2 in `docs/troubleshooting.md` must
   be followed by a `Last verified: <version>` footer. v1.0 does not enforce
   the version is recent (over-engineering for this milestone), only that
   the footer is present, so future-readers can sanity-check the entry's
   age without grepping git blame.

3. CDN-free docs — no markdown file under `docs/` may reference an external
   CDN host. The site must work in air-gapped, CSP-strict, or
   corporate-proxy environments where `cdn.jsdelivr.net`, `unpkg.com`, and
   friends are unreachable.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs"
CLI_REFERENCE = DOCS_DIR / "cli-reference.md"
TROUBLESHOOTING = DOCS_DIR / "troubleshooting.md"
SCRIPTS_DIR = REPO_ROOT / "scripts"

# Hosts that signal a CDN dependency. Kept conservative — adding a new entry
# is cheap, removing one is a real conversation.
FORBIDDEN_CDN_HOSTS = (
    "cdn.jsdelivr.net",
    "unpkg.com",
    "cdnjs.cloudflare.com",
    "stackpath.bootstrapcdn.com",
)


def _import_render_module():
    """Import the render-cli-reference script as a module."""
    sys.path.insert(0, str(SCRIPTS_DIR))
    import render_cli_reference  # noqa: WPS433  -- intentional dynamic import

    return render_cli_reference


def _iter_subcommand_names(parser: argparse.ArgumentParser):
    """Yield every subcommand name registered on the parser, recursively."""
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, sub in action.choices.items():
                yield name
                yield from _iter_subcommand_names(sub)


# ---------------------------------------------------------------------------
# Gate 1: CLI-reference drift
# ---------------------------------------------------------------------------


def test_cli_reference_exists():
    assert CLI_REFERENCE.exists(), (
        f"{CLI_REFERENCE.relative_to(REPO_ROOT)} is missing. "
        "Run: python scripts/render_cli_reference.py --write"
    )


def test_cli_reference_lists_every_subcommand():
    """Every subcommand from build_parser must appear literally in the page."""
    from repo_context_hooks.cli import build_parser

    parser = build_parser()
    body = CLI_REFERENCE.read_text(encoding="utf-8")
    missing = [
        name for name in _iter_subcommand_names(parser) if f"`{name}`" not in body
    ]
    assert not missing, (
        f"Subcommands missing from {CLI_REFERENCE.relative_to(REPO_ROOT)}: "
        f"{missing}. Re-run: python scripts/render_cli_reference.py --write"
    )


def test_cli_reference_matches_renderer_output():
    """Drift gate: committed file == renderer output."""
    render = _import_render_module()
    expected = render.render(render.build_parser())
    actual = CLI_REFERENCE.read_text(encoding="utf-8")
    if actual != expected:
        pytest.fail(
            f"{CLI_REFERENCE.relative_to(REPO_ROOT)} is stale relative to "
            "repo_context_hooks.cli:build_parser. "
            "Run: python scripts/render_cli_reference.py --write"
        )


# ---------------------------------------------------------------------------
# Gate 2: troubleshooting freshness
# ---------------------------------------------------------------------------


def test_troubleshooting_exists():
    assert TROUBLESHOOTING.exists(), (
        f"{TROUBLESHOOTING.relative_to(REPO_ROOT)} is missing — issue #75 "
        "requires a troubleshooting page with at least 6 documented failure "
        "modes."
    )


def test_troubleshooting_has_at_least_six_failure_modes():
    """AC1 of issue #75: ≥6 documented failure modes."""
    body = TROUBLESHOOTING.read_text(encoding="utf-8")
    headings = [line for line in body.splitlines() if line.startswith("## ") and not line.startswith("## Related")]
    assert len(headings) >= 6, (
        f"{TROUBLESHOOTING.relative_to(REPO_ROOT)} must document ≥6 failure "
        f"modes (issue #75 AC1). Found {len(headings)} H2 sections "
        f"(excluding 'Related'): {headings}"
    )


def test_every_troubleshooting_section_has_last_verified_footer():
    """Each failure-mode H2 must end with a `Last verified` footer."""
    body = TROUBLESHOOTING.read_text(encoding="utf-8")
    sections = _split_h2_sections(body)
    missing = []
    for heading, section_body in sections.items():
        if heading == "Related":
            continue
        if "Last verified" not in section_body:
            missing.append(heading)
    assert not missing, (
        f"Troubleshooting sections missing 'Last verified' footer: {missing}. "
        "Every failure-mode entry must end with a `Last verified: <version>` "
        "line so readers can sanity-check the entry's age."
    )


def _split_h2_sections(body: str) -> dict[str, str]:
    """Return {h2_title: body_until_next_h2} for every H2 in the document."""
    sections: dict[str, str] = {}
    current_title: str | None = None
    current_lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if current_title is not None:
                sections[current_title] = "\n".join(current_lines)
            current_title = line[3:].strip()
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)
    if current_title is not None:
        sections[current_title] = "\n".join(current_lines)
    return sections


# ---------------------------------------------------------------------------
# Gate 3: no external CDN
# ---------------------------------------------------------------------------


def test_no_external_cdn_in_docs_markdown():
    """Air-gapped / CSP-strict adopters must be able to view the site offline."""
    offenders: list[tuple[Path, str]] = []
    for md_path in DOCS_DIR.rglob("*.md"):
        # Skip the gitignored internal/ scratch dir if it exists.
        if "internal" in md_path.parts:
            continue
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for host in FORBIDDEN_CDN_HOSTS:
            if host in text:
                offenders.append((md_path.relative_to(REPO_ROOT), host))
    assert not offenders, (
        "External CDN references found in docs/. The docs must work in "
        "air-gapped / CSP-strict / corporate-proxy environments. Vendor any "
        f"required assets under `docs/assets/` instead. Offenders: {offenders}"
    )
