from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def readme_text() -> str:
    return README.read_text(encoding="utf-8")


def test_readme_has_public_facing_sections_in_order() -> None:
    text = readme_text()
    expected_sections = [
        "# repo-context-hooks",
        "## Why Repo-Native Continuity",
        "## How It Works",
        "## Supported Today",
        "## Platform Support",
        "## Concrete Stories",
        "## See Also",
        "## Development",
        "## License",
    ]
    positions = []
    for section in expected_sections:
        position = text.find(section)
        assert position != -1, f"missing section: {section}"
        positions.append(position)

    assert positions == sorted(positions), "README sections are out of order"


def test_readme_mentions_current_platforms_honestly() -> None:
    text = readme_text()
    expected_snippets = [
        "currently supported",
        "Claude",
        "Cursor",
        "Codex",
        "Replit",
        "Windsurf",
        "Lovable",
        "OpenClaw",
        "Claude (`native`)",
        "Cursor (`partial`)",
        "Codex (`partial`)",
        "Replit (`partial`)",
        "Windsurf (`partial`)",
        "Lovable (`partial`)",
        "OpenClaw (`partial`)",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing README platform snippet: {snippet}"


def test_readme_points_to_platform_support_doc() -> None:
    text = readme_text()
    link_text = "docs/platforms.md"
    assert link_text in text, f"missing supporting link: {link_text}"
    assert (ROOT / "docs" / "platforms.md").exists(), "missing docs/platforms.md"


def test_readme_avoids_internal_operator_heavy_sections() -> None:
    text = readme_text()
    unexpected_snippets = [
        "## What `install` Actually Does",
        "## Honest Critique",
        "operational contract",
        "Supported agent targets today: Codex and Claude",
    ]
    for snippet in unexpected_snippets:
        assert snippet not in text, f"README still exposes internal-heavy copy: {snippet}"


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


def test_readme_links_supporting_docs_and_examples() -> None:
    text = readme_text()
    expected_links = [
        ("docs/architecture.md", ROOT / "docs" / "architecture.md"),
        ("docs/competitive-analysis.md", ROOT / "docs" / "competitive-analysis.md"),
        ("docs/demo/animation-plan.md", ROOT / "docs" / "demo" / "animation-plan.md"),
        ("docs/launch/platform-roadmap.md", ROOT / "docs" / "launch" / "platform-roadmap.md"),
        ("examples/minimal-repo/", ROOT / "examples" / "minimal-repo"),
        ("examples/multi-project/", ROOT / "examples" / "multi-project"),
    ]
    for link_text, link_path in expected_links:
        assert link_text in text, f"missing supporting link: {link_text}"
        assert link_path.exists(), f"missing supporting path: {link_path}"
