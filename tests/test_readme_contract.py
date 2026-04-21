from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def readme_text() -> str:
    return README.read_text(encoding="utf-8")


def test_readme_has_required_sections() -> None:
    text = readme_text()
    expected_sections = [
        "# repo-context-hooks",
        "## Why This Exists",
        "## How It Works",
        "## Repo Contract",
        "## Before / After",
        "## What `install` Actually Does",
        "## Technical Details",
        "## Honest Critique",
        "## Examples",
        "## Development",
        "## License",
    ]
    positions = []
    for section in expected_sections:
        position = text.find(section)
        assert position != -1, f"missing section: {section}"
        positions.append(position)

    assert positions == sorted(positions), "README sections are out of order"


def test_readme_includes_install_and_alias_commands() -> None:
    text = readme_text()
    expected_snippets = [
        "python -m pip install -e .",
        "repo-context-hooks install --platform codex",
        "repohandoff install --platform codex",
        "graphify install --platform codex",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing command snippet: {snippet}"


def test_readme_surfaces_install_side_effects() -> None:
    text = readme_text()
    expected_snippets = [
        "~/.codex/skills",
        "~/.claude/skills",
        ".claude/scripts/repo_specs_memory.py",
        ".claude/scripts/session_context.py",
        ".claude/settings.json",
        "specs/README.md",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing install detail: {snippet}"


def test_readme_contains_honest_critique() -> None:
    text = readme_text()
    expected_snippets = [
        "not a vector memory layer",
        "not a hosted memory service",
        "does not replace repo discipline",
        "cross-repo semantic memory",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing critique snippet: {snippet}"


def test_readme_links_to_supporting_docs() -> None:
    text = readme_text()
    expected_links = [
        ("docs/architecture.md", ROOT / "docs" / "architecture.md"),
        ("examples/minimal-repo/", ROOT / "examples" / "minimal-repo"),
        ("examples/multi-project/", ROOT / "examples" / "multi-project"),
    ]
    for link_text, link_path in expected_links:
        assert link_text in text, f"missing supporting link: {link_text}"
        assert link_path.exists(), f"missing supporting path: {link_path}"


def test_readme_embeds_required_diagrams() -> None:
    text = readme_text()
    expected_assets = [
        "assets/diagrams/lifecycle-flow.svg",
        "assets/diagrams/repo-contract.svg",
        "assets/diagrams/before-after-continuity.svg",
    ]
    for asset in expected_assets:
        assert asset in text, f"missing diagram embed: {asset}"
        assert (ROOT / asset).exists(), f"missing diagram file: {asset}"
