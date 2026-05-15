from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "specs" / "README.md"
GLOSSARY = ROOT / "UBIQUITOUS_LANGUAGE.md"
SCRIPT = ROOT / "repo_context_hooks" / "bundle" / "scripts" / "repo_specs_memory.py"


def _tmp_dir() -> Path:
    base = ROOT / ".tmp-tests"
    base.mkdir(exist_ok=True)
    path = base / uuid4().hex
    path.mkdir()
    return path


def test_repo_tracks_canonical_memory_files() -> None:
    assert GLOSSARY.exists(), "missing UBIQUITOUS_LANGUAGE.md"
    assert SPECS.exists(), "missing specs/README.md"

    glossary = GLOSSARY.read_text(encoding="utf-8")
    specs = SPECS.read_text(encoding="utf-8")

    expected_terms = [
        "repo contract",
        "repo-native continuity",
        "engineering memory",
        "support tier",
        "native",
        "partial",
        "planned",
    ]
    for term in expected_terms:
        assert term in glossary, f"missing glossary term: {term}"

    expected_sections = [
        "## Repo Context Index",
        "## Architecture and Design Constraints",
        "## Built So Far",
        "## Design Decisions",
        "## What Worked",
        "## What Failed or Was Reverted",
        "## Open Issues and Next Work",
        "## How To Work in This Repo",
        "## Session Log",
        "## Session Checkpoints",
    ]
    for section in expected_sections:
        assert section in specs, f"missing specs section: {section}"

    # These strings belong only in Session Checkpoints, not in the main body.
    checkpoints_marker = "## Session Checkpoints"
    body = specs.split(checkpoints_marker)[0] if checkpoints_marker in specs else specs
    assert "Branch snapshot:" not in body
    assert "Last commit:" not in body


def test_repo_specs_memory_bootstrap_avoids_branch_and_commit_noise() -> None:
    temp_root = _tmp_dir()
    repo = temp_root / "repo"
    repo.mkdir()

    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True, text=True)
    (repo / "README.md").write_text(
        "# Demo Repo\n\nDemo repo for testing the repo memory bootstrap behavior.\n",
        encoding="utf-8",
    )

    subprocess.run(
        [sys.executable, str(SCRIPT), "session-start"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    specs = (repo / "specs" / "README.md").read_text(encoding="utf-8")
    glossary = (repo / "UBIQUITOUS_LANGUAGE.md").read_text(encoding="utf-8")

    assert "### Canonical Context Sources" in specs
    assert "Source of truth: checked-in repo docs, not chat-only summaries" in specs
    assert "Branch snapshot:" not in specs
    assert "Last commit:" not in specs
    assert "Keep project terms stable across code, specs, docs, and conversation." in glossary


def test_repo_specs_memory_emits_local_telemetry_event() -> None:
    temp_root = _tmp_dir()
    repo = temp_root / "repo"
    repo.mkdir()
    telemetry_base = temp_root / "telemetry"

    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True, text=True)
    (repo / "README.md").write_text(
        "# Demo Repo\n\nDemo repo for testing telemetry evidence.\n",
        encoding="utf-8",
    )

    subprocess.run(
        [sys.executable, str(SCRIPT), "pre-compact"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env={
            **dict(__import__("os").environ),
            "REPO_CONTEXT_HOOKS_TELEMETRY_DIR": str(telemetry_base),
        },
    )

    events = list(telemetry_base.rglob("events.jsonl"))
    assert len(events) == 1
    payload = events[0].read_text(encoding="utf-8")
    assert '"event_name": "pre-compact"' in payload


SKILLS_SCRIPT = ROOT / "repo_context_hooks" / "bundle" / "skills" / "context-handoff-hooks" / "scripts" / "repo_specs_memory.py"


def test_decision_entry_written_to_session_log() -> None:
    temp_root = _tmp_dir()
    repo = temp_root / "repo"
    repo.mkdir()

    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True, text=True)
    (repo / "README.md").write_text(
        "# Demo Repo\n\nDecision entry test.\n",
        encoding="utf-8",
    )

    # Bootstrap specs/README.md (normally done via repo-context-hooks init)
    (repo / "specs").mkdir()
    (repo / "specs" / "README.md").write_text("# Engineering Memory", encoding="utf-8")

    # Write a decision entry
    message = "Built: auth endpoint. Decided: JWT over sessions for stateless scaling. Next: wire middleware."
    result = subprocess.run(
        [sys.executable, str(SKILLS_SCRIPT), "decision", "--message", message],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    specs = (repo / "specs" / "README.md").read_text(encoding="utf-8")
    assert "## Session Log" in specs
    assert "Built: auth endpoint" in specs
    assert "decision (" in specs


def test_extract_repo_summary_skips_multi_line_html_comments() -> None:
    """Regression for #124. The README often opens with a `<!-- BADGES:START -->`
    block followed by a multi-line HTML comment whose body is plain prose
    (badge ordering convention, etc.). The pre-fix parser's `clean_line`
    only stripped single-line HTML tags, so the comment body survived the
    prose filters and got concatenated into the AUTO:REPO_CONTEXT_END block
    summary on every SessionStart fire — overwriting the real summary.

    This test synthesises a README with the same shape as `repo-context-hooks`
    own README and asserts the AUTO summary captures the prose paragraph that
    follows the comment block, not the comment body itself.
    """
    temp_root = _tmp_dir()
    repo = temp_root / "repo"
    repo.mkdir()

    subprocess.run(
        ["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True
    )

    # Note line 3 is short enough to contribute the first prose line, then a
    # multi-line HTML comment whose body LOOKS like prose (>25 chars, no
    # markdown-list prefix). The actual prose paragraph that should be
    # picked up follows below.
    (repo / "README.md").write_text(
        "# Demo Repo\n"
        "\n"
        "Tagline-style description of demo repo.\n"
        "\n"
        "<!-- BADGES:START -->\n"
        "<!--\n"
        "  Badge row convention. Add new badges INSIDE this anchor, one per line, in\n"
        "  this order: build/quality / coverage / version. Each badge uses the linked\n"
        "  form `[![alt](svg-url)](click-url)`.\n"
        "-->\n"
        "![demo badge](docs/badge.svg)\n"
        "<!-- BADGES:END -->\n"
        "\n"
        "This demo repo exists purely so the AUTO summary can be exercised against a "
        "realistic README shape. It is the canonical second prose paragraph the "
        "parser should pick up.\n",
        encoding="utf-8",
    )

    subprocess.run(
        [sys.executable, str(SCRIPT), "session-start"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    specs = (repo / "specs" / "README.md").read_text(encoding="utf-8")

    auto_start = "<!-- AUTO:REPO_CONTEXT_START -->"
    auto_end = "<!-- AUTO:REPO_CONTEXT_END -->"
    assert auto_start in specs and auto_end in specs
    auto_block = specs.split(auto_start, 1)[1].split(auto_end, 1)[0]

    # The bug: comment body leaks into the AUTO summary.
    assert "Badge row convention" not in auto_block, (
        "AUTO:REPO_CONTEXT block was clobbered by HTML-comment body — "
        "extract_repo_summary did not skip multi-line HTML comments. "
        "Regression for #124."
    )

    # Positive shape: the actual prose paragraph below the badge block lands in
    # the summary. The "tagline" line on its own is acceptable as line 1; the
    # second line of summary should be the real prose paragraph, not the
    # comment body.
    assert "Tagline-style description" in auto_block
    assert "canonical second prose paragraph" in auto_block


def test_checkpoint_appends_recent_commits() -> None:
    temp_root = _tmp_dir()
    repo = temp_root / "repo"
    repo.mkdir()

    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)
    (repo / "README.md").write_text("# Demo\n\nRecent commits test.\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial commit"], cwd=repo, check=True, capture_output=True)

    # Bootstrap specs/README.md (normally done via repo-context-hooks init)
    (repo / "specs").mkdir()
    (repo / "specs" / "README.md").write_text("# Engineering Memory", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(SKILLS_SCRIPT), "pre-compact"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    specs = (repo / "specs" / "README.md").read_text(encoding="utf-8")
    assert "pre-compact" in specs
    assert "initial commit" in specs
