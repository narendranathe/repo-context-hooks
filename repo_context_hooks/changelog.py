"""CHANGELOG parsing for issue #76's gate workflow and release-notes extractor.

Two responsibilities, one module:

1. `extract_section(text, version)` — pull `## [<version>]` body out of a
   Keep-a-Changelog file for the GitHub Release page. Strips HTML comments
   and `<!-- none -->`-only subheadings. Raises `LookupError` if the section
   is missing or empty after stripping. **Fails loud, never silent** — the
   release-notes failure mode where an empty section silently overwrites an
   existing release body is the core failure-mode-critic non-negotiable.

2. `find_unreleased_changed_lines(diff_text)` — read a `git diff --unified=0`
   patch and count `+` lines whose hunk falls inside the `## [Unreleased]`
   section of the destination file. The PR-side gate uses this to enforce
   that the diff actually adds to `[Unreleased]` (not a stale historical
   section, not a deletion-only edit, not a typo fix).

Stdlib only. The package's `dependencies = []` contract is non-negotiable.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Heading line for any release section in CHANGELOG.md, including [Unreleased]
# and dated releases like `## [0.6.0] - 2026-04-28`.
RCH_CHANGELOG_HEADING_RE = re.compile(
    r"^## \[(?P<ver>[^\]]+)\](?:\s*-\s*\d{4}-\d{2}-\d{2})?\s*$"
)

# Empty-body markers we drop. Subheadings that contain only `<!-- none -->`
# (or just whitespace) are noise on the release page.
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_SUBHEADING_RE = re.compile(r"^### \S", re.MULTILINE)


def _normalize(text: str) -> str:
    """CRLF -> LF. Idempotent."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _strip_empty_subsections(body: str) -> str:
    """Drop `### Foo` blocks whose body is whitespace / `<!-- none -->` only.

    Keeps ### blocks that have at least one non-whitespace, non-comment line.
    The CHANGELOG contract block in CHANGELOG.md uses `<!-- none -->` as a
    placeholder for unused subheadings during development; those should not
    appear on the public GitHub Release page.
    """
    lines = body.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.startswith("### "):
            out.append(line)
            i += 1
            continue
        # Collect the subheading and its body up to the next ### or end.
        sub_start = i
        i += 1
        sub_body_lines: list[str] = []
        while i < len(lines) and not lines[i].startswith("### "):
            sub_body_lines.append(lines[i])
            i += 1
        # Strip HTML comments + whitespace; if anything substantive remains, keep.
        sub_body_text = _HTML_COMMENT_RE.sub("", "\n".join(sub_body_lines)).strip()
        if sub_body_text:
            out.append(lines[sub_start])
            out.extend(sub_body_lines)
    return "\n".join(out)


def extract_section(text: str, version: str) -> str:
    """Return the body of `## [<version>]`, stripped of comments and noise.

    Raises:
      LookupError if the section is missing OR is empty/whitespace-only after
      stripping HTML comments and `<!-- none -->`-only subheadings.
    """
    norm = _normalize(text)
    lines = norm.split("\n")

    start_idx: int | None = None
    end_idx: int = len(lines)

    for i, line in enumerate(lines):
        m = RCH_CHANGELOG_HEADING_RE.match(line)
        if not m:
            continue
        if start_idx is None:
            if m.group("ver") == version:
                start_idx = i + 1
        else:
            # Next release header — that's the section boundary.
            end_idx = i
            break

    if start_idx is None:
        raise LookupError(f"CHANGELOG section [{version}] not found")

    body_lines = lines[start_idx:end_idx]
    body = "\n".join(body_lines)
    body = _strip_empty_subsections(body)
    body = _HTML_COMMENT_RE.sub("", body)
    body = body.strip()

    if not body:
        raise LookupError(
            f"CHANGELOG section [{version}] is empty after stripping comments"
        )
    return body + "\n"


def _find_unreleased_range(head_changelog: str) -> tuple[int, int] | None:
    """Return (first_body_line, end_exclusive) of `## [Unreleased]` in the
    post-image of CHANGELOG.md, both as 1-indexed line numbers. None if absent.

    `end_exclusive` is the line number of the next `## [Version]` heading, or
    one past the file's last line if `[Unreleased]` is the last section.
    """
    lines = _normalize(head_changelog).split("\n")
    start: int | None = None
    end: int = len(lines) + 1  # 1-indexed, past EOF
    for i, line in enumerate(lines, start=1):
        m = RCH_CHANGELOG_HEADING_RE.match(line)
        if not m:
            continue
        if start is None and m.group("ver") == "Unreleased":
            start = i + 1  # body starts AFTER the heading line
        elif start is not None:
            end = i
            break
    if start is None:
        return None
    return (start, end)


def find_unreleased_changed_lines(
    diff_text: str, head_changelog: str | None = None
) -> int:
    """Count `+` lines whose post-image position falls inside `## [Unreleased]`.

    Two modes:

    1. **head_changelog supplied (preferred):** we know exactly where
       `## [Unreleased]` lives in the post-image. We walk the diff hunks and
       count any `+` line whose new-file line number lands inside the
       `[Unreleased]` body range. This is the path the gate workflow uses,
       since `actions/checkout@v4` always gives us the head-side file on disk.

    2. **head_changelog not supplied (legacy):** we try to infer the
       `[Unreleased]` post-image line from the diff itself. This only works if
       the heading was touched in the diff. Otherwise we return 0.
    """
    text = _normalize(diff_text)
    lines = text.split("\n")

    unreleased_post_line: int | None = None
    next_section_post_line: int | None = None

    if head_changelog is not None:
        rng = _find_unreleased_range(head_changelog)
        if rng is None:
            return 0
        unreleased_post_line, next_section_post_line = rng
    else:
        # Fallback: scan the diff for the heading itself.
        cursor: int | None = None
        for line in lines:
            hunk_m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if hunk_m:
                cursor = int(hunk_m.group(1))
                continue
            if cursor is None:
                continue
            if line.startswith("-"):
                continue
            if line.startswith("\\"):
                continue
            m = RCH_CHANGELOG_HEADING_RE.match(
                line[1:] if line.startswith(("+", " ")) else line
            )
            if m:
                if m.group("ver") == "Unreleased" and unreleased_post_line is None:
                    unreleased_post_line = cursor
                elif unreleased_post_line is not None and next_section_post_line is None:
                    next_section_post_line = cursor
            cursor += 1

        if unreleased_post_line is None:
            return 0

    # Second pass: count `+` lines whose post-image line number is in
    # [unreleased_post_line, next_section_post_line).
    count = 0
    cursor = None
    for line in lines:
        hunk_m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
        if hunk_m:
            cursor = int(hunk_m.group(1))
            continue
        if cursor is None:
            continue
        if line.startswith("\\"):
            continue
        if line.startswith("+") and not line.startswith("+++"):
            in_unreleased = cursor >= unreleased_post_line and (
                next_section_post_line is None or cursor < next_section_post_line
            )
            if in_unreleased:
                # Don't count the heading itself as "an entry".
                stripped = line[1:].strip()
                if not RCH_CHANGELOG_HEADING_RE.match(stripped):
                    count += 1
            cursor += 1
        elif line.startswith(" ") or line.startswith("+"):
            cursor += 1
        # `-` lines don't advance the new-file cursor.
    return count


def _cmd_extract(args: argparse.Namespace) -> int:
    path = Path(args.path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"::error::Cannot read {path}: {exc}", file=sys.stderr)
        return 1
    try:
        body = extract_section(text, args.version)
    except LookupError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    sys.stdout.write(body)
    return 0


def _cmd_gate(args: argparse.Namespace) -> int:
    """Run `git diff` between two SHAs and verify [Unreleased] saw additions."""
    try:
        result = subprocess.run(
            [
                "git",
                "diff",
                "--unified=0",
                f"{args.base}...{args.head}",
                "--",
                "CHANGELOG.md",
            ],
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError) as exc:
        print(f"::error::git diff failed: {exc}", file=sys.stderr)
        return 1
    if result.returncode != 0:
        print(f"::error::git diff returned {result.returncode}: {result.stderr.strip()}", file=sys.stderr)
        return 1

    diff_text = result.stdout
    if not diff_text.strip():
        print(
            "::error::CHANGELOG.md was not modified in this PR. Add a bullet "
            "under '## [Unreleased]' or apply one of the labels: "
            "skip-changelog, documentation, chore, dependencies.",
            file=sys.stderr,
        )
        return 1

    # Read the head-side CHANGELOG.md from the working tree (the gate workflow
    # checks out the PR head). Without this, a PR that adds bullets UNDER an
    # already-existing `## [Unreleased]` heading would fail the gate, because
    # `--unified=0` diffs don't include the heading line as context.
    head_changelog: str | None = None
    try:
        head_changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    except OSError:
        # CHANGELOG.md missing on disk — fall back to diff-only inference.
        pass

    added = find_unreleased_changed_lines(diff_text, head_changelog=head_changelog)
    if added <= 0:
        print(
            "::error::CHANGELOG.md changed but no addition under '## [Unreleased]'. "
            "Add the new bullet under [Unreleased], not under a historical release "
            "section. (Edits to historical sections do not satisfy this gate.)",
            file=sys.stderr,
        )
        return 1
    print(f"OK: {added} added line(s) under [Unreleased].")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="repo_context_hooks.changelog")
    sub = parser.add_subparsers(dest="cmd", required=True)

    extract = sub.add_parser("extract", help="Print a release section from CHANGELOG.md.")
    extract.add_argument("version", help="Version string, e.g. 0.6.0 or 1.0.0-rc1.")
    extract.add_argument("path", help="Path to CHANGELOG.md.")
    extract.set_defaults(func=_cmd_extract)

    gate = sub.add_parser("gate", help="Verify a PR diff adds to [Unreleased].")
    gate.add_argument("base", help="Base ref or SHA.")
    gate.add_argument("head", help="Head ref or SHA.")
    gate.set_defaults(func=_cmd_gate)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
