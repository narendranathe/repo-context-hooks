"""Tests for `repo_context_hooks.changelog` (issue #76).

Failure-mode-critic table:
- missing version section
- empty / `<!-- none -->`-only section
- CRLF input
- prerelease tags
- diff hunks: addition under [Unreleased] vs historical vs deletion-only
- CLI exit codes (extract / gate)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from repo_context_hooks import changelog
from repo_context_hooks.changelog import (
    RCH_CHANGELOG_HEADING_RE,
    extract_section,
    find_unreleased_changed_lines,
)


# ---------------------------------------------------------------------------
# extract_section
# ---------------------------------------------------------------------------


_SAMPLE = """\
# Changelog

<!-- contract block -->

## [Unreleased]

### Added
- Rich --version flag (#76)

### Changed
<!-- none -->

## [0.6.0] - 2026-04-28

### Added
- measure export
- experiment start/finish/status

### Fixed
- is_sampled bypass

## [0.5.0] - 2026-04-27

### Added
- shields.io badge
"""


def test_extract_existing_release_returns_body_with_subheadings() -> None:
    body = extract_section(_SAMPLE, "0.6.0")
    assert "### Added" in body
    assert "measure export" in body
    assert "is_sampled bypass" in body
    # Must NOT include the next release section.
    assert "## [0.5.0]" not in body
    # Must NOT include HTML comments from the contract block.
    assert "<!--" not in body


def test_extract_drops_subheadings_with_only_html_comment() -> None:
    body = extract_section(_SAMPLE, "Unreleased")
    assert "### Added" in body
    # `### Changed` has only `<!-- none -->` -> dropped.
    assert "### Changed" not in body


def test_extract_handles_crlf_input() -> None:
    crlf = _SAMPLE.replace("\n", "\r\n")
    body = extract_section(crlf, "0.6.0")
    assert "\r" not in body
    assert "measure export" in body


def test_extract_missing_version_raises_lookup_error() -> None:
    with pytest.raises(LookupError, match=r"\[9\.9\.9\] not found"):
        extract_section(_SAMPLE, "9.9.9")


def test_extract_empty_section_raises_lookup_error() -> None:
    text = """\
# Changelog

## [Unreleased]
<!-- none -->

## [0.1.0] - 2026-01-01

### Added
- initial release
"""
    with pytest.raises(LookupError, match=r"\[Unreleased\] is empty"):
        extract_section(text, "Unreleased")


def test_extract_prerelease_tag() -> None:
    text = """\
## [1.0.0-rc1] - 2026-05-01

### Added
- release candidate cut
"""
    body = extract_section(text, "1.0.0-rc1")
    assert "release candidate cut" in body


def test_extract_section_without_date_header() -> None:
    """`## [Unreleased]` has no date suffix; `## [0.6.0] - 2026-04-28` does."""
    text = """\
## [Unreleased]

### Added
- foo

## [0.6.0] - 2026-04-28

### Added
- bar
"""
    assert "foo" in extract_section(text, "Unreleased")
    assert "bar" in extract_section(text, "0.6.0")


def test_heading_regex_recognises_canonical_forms() -> None:
    assert RCH_CHANGELOG_HEADING_RE.match("## [Unreleased]")
    assert RCH_CHANGELOG_HEADING_RE.match("## [0.6.0] - 2026-04-28")
    assert RCH_CHANGELOG_HEADING_RE.match("## [1.0.0-rc1] - 2026-05-01")
    assert not RCH_CHANGELOG_HEADING_RE.match("# [0.6.0]")
    assert not RCH_CHANGELOG_HEADING_RE.match("## 0.6.0")


# ---------------------------------------------------------------------------
# find_unreleased_changed_lines
# ---------------------------------------------------------------------------


_DIFF_UNRELEASED_ADD = """\
diff --git a/CHANGELOG.md b/CHANGELOG.md
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -10,0 +11,2 @@
+## [Unreleased]
+- new bullet for #76
@@ -25,0 +28,1 @@
+- another unreleased line
"""


_DIFF_HISTORICAL_ONLY = """\
diff --git a/CHANGELOG.md b/CHANGELOG.md
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -20,0 +21,2 @@
+## [0.5.0] - 2026-04-27
+- typo fix in historical section
"""


_DIFF_DELETION_ONLY = """\
diff --git a/CHANGELOG.md b/CHANGELOG.md
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -10,2 +10,0 @@
-## [Unreleased]
-- old bullet removed
"""


def test_find_unreleased_change_count_with_addition() -> None:
    n = find_unreleased_changed_lines(_DIFF_UNRELEASED_ADD)
    # Two `+` content lines under [Unreleased]; the heading itself is not counted.
    assert n == 2


def test_find_unreleased_change_count_historical_only() -> None:
    """Edits to a historical release section must NOT satisfy the gate."""
    n = find_unreleased_changed_lines(_DIFF_HISTORICAL_ONLY)
    # No [Unreleased] heading was seen first in the diff -> 0.
    assert n == 0


def test_find_unreleased_change_count_deletion_only() -> None:
    """A deletion-only diff under [Unreleased] does not count."""
    n = find_unreleased_changed_lines(_DIFF_DELETION_ONLY)
    assert n == 0


def test_find_unreleased_change_count_empty_diff() -> None:
    assert find_unreleased_changed_lines("") == 0


# ---------------------------------------------------------------------------
# head_changelog mode — the realistic case where a PR adds bullets BELOW an
# already-existing `## [Unreleased]` heading. With `--unified=0`, the heading
# is not in the diff context, so we must use the post-image to know its line.
# This is the bug surfaced by the gate failing on its own PR (issue #76).
# ---------------------------------------------------------------------------


def test_find_unreleased_change_count_with_head_post_image() -> None:
    """Bullets added under an existing [Unreleased] heading are detected when
    the head-side CHANGELOG.md is supplied as the post-image."""
    head = """\
# Changelog

## [Unreleased]

### Added
- bullet one (existing)
- bullet two (newly added)
- bullet three (newly added)

## [0.6.0] - 2026-04-28

### Added
- old release entry
"""
    # Diff: two `+` lines at post-image lines 7 and 8 (under [Unreleased]
    # which is at line 3, body starts line 4, next section [0.6.0] is at line 10).
    diff = """\
diff --git a/CHANGELOG.md b/CHANGELOG.md
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -7,0 +7,2 @@
+- bullet two (newly added)
+- bullet three (newly added)
"""
    assert find_unreleased_changed_lines(diff, head_changelog=head) == 2


def test_find_unreleased_change_count_with_head_rejects_historical_addition() -> None:
    """Even with the post-image, additions OUTSIDE [Unreleased] must not count."""
    head = """\
# Changelog

## [Unreleased]

- (no entries yet)

## [0.6.0] - 2026-04-28

### Added
- bullet one
- bullet two (newly added to historical)
"""
    diff = """\
diff --git a/CHANGELOG.md b/CHANGELOG.md
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -10,0 +11,1 @@
+- bullet two (newly added to historical)
"""
    assert find_unreleased_changed_lines(diff, head_changelog=head) == 0


def test_find_unreleased_change_count_with_head_no_unreleased_section() -> None:
    """If [Unreleased] is missing from the post-image, return 0."""
    head = "# Changelog\n\n## [0.6.0] - 2026-04-28\n\n- only release\n"
    diff = """\
@@ -3,0 +4,1 @@
+- some new line
"""
    assert find_unreleased_changed_lines(diff, head_changelog=head) == 0


def test_find_unreleased_change_count_with_head_unreleased_at_eof() -> None:
    """[Unreleased] as the last section in the file (no following heading)."""
    head = """\
# Changelog

## [0.6.0] - 2026-04-28

- old release

## [Unreleased]

- new bullet
"""
    diff = """\
@@ -7,0 +9,1 @@
+- new bullet
"""
    assert find_unreleased_changed_lines(diff, head_changelog=head) == 1


# ---------------------------------------------------------------------------
# CLI: `python -m repo_context_hooks.changelog extract ...`
# ---------------------------------------------------------------------------


def test_extract_cli_success(tmp_path, capsys) -> None:
    f = tmp_path / "CHANGELOG.md"
    f.write_text(_SAMPLE, encoding="utf-8")
    rc = changelog.main(["extract", "0.6.0", str(f)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "measure export" in out


def test_extract_cli_missing_version_returns_one(tmp_path, capsys) -> None:
    f = tmp_path / "CHANGELOG.md"
    f.write_text(_SAMPLE, encoding="utf-8")
    rc = changelog.main(["extract", "9.9.9", str(f)])
    err = capsys.readouterr().err
    assert rc == 1
    assert "::error::" in err


def test_extract_cli_missing_file_returns_one(tmp_path, capsys) -> None:
    rc = changelog.main(["extract", "0.6.0", str(tmp_path / "nope.md")])
    err = capsys.readouterr().err
    assert rc == 1
    assert "Cannot read" in err


def test_extract_cli_empty_section_returns_one(tmp_path, capsys) -> None:
    f = tmp_path / "CHANGELOG.md"
    f.write_text(
        "## [Unreleased]\n<!-- none -->\n\n## [0.1.0] - 2026-01-01\n- bullet\n",
        encoding="utf-8",
    )
    rc = changelog.main(["extract", "Unreleased", str(f)])
    err = capsys.readouterr().err
    assert rc == 1
    assert "is empty" in err


# ---------------------------------------------------------------------------
# CLI: `python -m repo_context_hooks.changelog gate ...`
#
# We mock subprocess.run so we don't depend on the test runner being inside a
# real git repo.
# ---------------------------------------------------------------------------


def _write_changelog_with_unreleased_through_line_30(tmp_path: Path) -> Path:
    """Synthetic CHANGELOG where [Unreleased] body covers lines 4..30 and
    [0.6.0] starts at line 31. Makes diff hunks at +11..+28 land safely
    inside [Unreleased] for the `_DIFF_UNRELEASED_ADD` fixture.
    """
    lines = ["# Changelog", "", "## [Unreleased]"]
    lines.extend([f"- placeholder bullet {i}" for i in range(27)])  # lines 4-30
    lines.append("## [0.6.0] - 2026-04-28")  # line 31
    lines.append("- old release")
    cl = tmp_path / "CHANGELOG.md"
    cl.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return cl


def _write_changelog_where_line_21_is_new_historical(tmp_path: Path) -> Path:
    """Synthetic CHANGELOG where line 21 is a NEW `## [0.5.0]` heading and
    lines 21+ are OUTSIDE the [Unreleased] body. Mirrors the post-image of a
    PR that only adds a historical section. Used with `_DIFF_HISTORICAL_ONLY`.
    """
    lines = ["# Changelog", "", "## [Unreleased]"]  # heading at line 3
    lines.extend([f"- pre-existing bullet {i}" for i in range(17)])  # lines 4-20
    lines.append("## [0.5.0] - 2026-04-27")  # line 21 (the newly-added heading)
    lines.append("- typo fix in historical section")  # line 22 (newly added)
    cl = tmp_path / "CHANGELOG.md"
    cl.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return cl


def test_gate_cli_passes_when_unreleased_added_lines(monkeypatch, capsys, tmp_path) -> None:
    _write_changelog_with_unreleased_through_line_30(tmp_path)
    monkeypatch.chdir(tmp_path)

    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(
            args=args, returncode=0, stdout=_DIFF_UNRELEASED_ADD, stderr=""
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    rc = changelog.main(["gate", "BASE", "HEAD"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK" in out


def test_gate_cli_fails_when_only_historical_edits(monkeypatch, capsys, tmp_path) -> None:
    _write_changelog_where_line_21_is_new_historical(tmp_path)
    monkeypatch.chdir(tmp_path)

    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(
            args=args, returncode=0, stdout=_DIFF_HISTORICAL_ONLY, stderr=""
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    rc = changelog.main(["gate", "BASE", "HEAD"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "[Unreleased]" in err


def test_gate_cli_fails_when_changelog_unchanged(monkeypatch, capsys) -> None:
    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(
            args=args, returncode=0, stdout="", stderr=""
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    rc = changelog.main(["gate", "BASE", "HEAD"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "not modified" in err


def test_gate_cli_fails_when_git_diff_errors(monkeypatch, capsys) -> None:
    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(
            args=args, returncode=128, stdout="", stderr="fatal: bad object"
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    rc = changelog.main(["gate", "BASE", "HEAD"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "git diff returned" in err


def test_gate_cli_handles_subprocess_exception(monkeypatch, capsys) -> None:
    def fake_run(args, **kwargs):
        raise OSError("git binary missing")

    monkeypatch.setattr(subprocess, "run", fake_run)
    rc = changelog.main(["gate", "BASE", "HEAD"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "git diff failed" in err


def test_gate_cli_passes_when_bullets_added_below_existing_unreleased_heading(
    monkeypatch, capsys, tmp_path
) -> None:
    """Regression test for the bug discovered when this gate failed on its own
    PR: with `--unified=0`, a diff that ONLY adds bullets below an existing
    `## [Unreleased]` heading does not include the heading line. The gate must
    still pass by reading the head-side CHANGELOG.md from the working tree.
    """
    cl = tmp_path / "CHANGELOG.md"
    cl.write_text(
        "\n".join(
            [
                "# Changelog",
                "",
                "## [Unreleased]",  # line 3
                "",  # line 4
                "### Added",  # line 5
                "- existing bullet",  # line 6
                "- new bullet 1",  # line 7
                "- new bullet 2",  # line 8
                "",  # line 9
                "## [0.6.0] - 2026-04-28",  # line 10
                "",
                "- old release",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    # The diff a real PR like #94 produces: `--unified=0`, no [Unreleased]
    # heading shown, only the new bullets at post-image lines 7 and 8.
    diff_text = (
        "diff --git a/CHANGELOG.md b/CHANGELOG.md\n"
        "--- a/CHANGELOG.md\n"
        "+++ b/CHANGELOG.md\n"
        "@@ -6,0 +7,2 @@\n"
        "+- new bullet 1\n"
        "+- new bullet 2\n"
    )

    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(args=args, returncode=0, stdout=diff_text, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    rc = changelog.main(["gate", "BASE", "HEAD"])
    out = capsys.readouterr().out
    assert rc == 0, "gate must pass when bullets are added below an existing [Unreleased] heading"
    assert "OK" in out
