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
        "## Why Agent-Level, Not Repo-Level",
        "## How It Works",
        "## Supported Platforms",
        "## Prove Impact",
        "## Telemetry Visibility",
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
        "| Claude | `native`",
        "| Cursor | `partial`",
        "| Codex | `partial`",
        "| Replit | `partial`",
        "| Windsurf | `partial`",
        "| Lovable | `partial`",
        "| OpenClaw | `partial`",
        "| Ollama | `partial`",
        "| Kimi | `partial`",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing README platform snippet: {snippet}"


def test_readme_points_to_platform_support_doc() -> None:
    text = readme_text()
    link_text = "docs/platforms.md"
    assert link_text in text, f"missing supporting link: {link_text}"
    assert (ROOT / "docs" / "platforms.md").exists(), "missing docs/platforms.md"


def test_readme_points_to_repo_contract_files() -> None:
    text = readme_text()
    expected_links = [
        ("specs/README.md", ROOT / "specs" / "README.md"),
        ("UBIQUITOUS_LANGUAGE.md", ROOT / "UBIQUITOUS_LANGUAGE.md"),
    ]
    for link_text, link_path in expected_links:
        assert link_text in text, f"missing repo contract link: {link_text}"
        assert link_path.exists(), f"missing repo contract file: {link_path}"


def test_readme_promotes_agent_first_onboarding_sequence() -> None:
    text = readme_text()
    # agent skill install comes first; workspace contract setup (init/doctor) is second
    install_pos = text.find("repo-context-hooks install --platform claude")
    init_pos = text.find("repo-context-hooks init")
    doctor_pos = text.find("repo-context-hooks doctor")

    assert install_pos != -1, "missing agent-level install command"
    assert init_pos != -1, "missing repo-context-hooks init command"
    assert doctor_pos != -1, "missing repo-context-hooks doctor command"
    assert install_pos < init_pos, "agent skill install must appear before workspace init"
    assert init_pos < doctor_pos, "workspace init must appear before doctor"


def test_readme_separates_platform_install_commands() -> None:
    text = readme_text()
    assert "## Other Platforms" in text
    for platform in (
        "claude",
        "cursor",
        "codex",
        "replit",
        "windsurf",
        "lovable",
        "openclaw",
        "ollama",
        "kimi",
    ):
        assert f"repo-context-hooks install --platform {platform}" in text


def test_readme_documents_impact_measurement() -> None:
    text = readme_text()
    assert "## Prove Impact" in text
    assert "repo-context-hooks measure" in text
    assert "repo-context-hooks measure --json" in text
    assert "repo-context-hooks measure --snapshot-dir docs/monitoring" in text
    assert "docs/monitoring.md" in text
    assert "docs/monitoring/history.json" in text
    assert "Observable Plot" in text
    assert "Vega-Lite" in text
    assert (ROOT / "docs" / "monitoring.md").exists()


def test_readme_keeps_internal_docs_out_of_primary_links() -> None:
    text = readme_text()
    assert "docs/platform-playbooks.md" not in text
    assert "docs/positioning.md" not in text


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
        "assets/brand/repo-context-hooks-logo.png",
        "assets/diagrams/context-continuity-engine.svg",
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
        ("examples/minimal-repo/", ROOT / "examples" / "minimal-repo"),
        ("examples/multi-project/", ROOT / "examples" / "multi-project"),
    ]
    for link_text, link_path in expected_links:
        assert link_text in text, f"missing supporting link: {link_text}"
        assert link_path.exists(), f"missing supporting path: {link_path}"
