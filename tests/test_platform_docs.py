from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_platform_doc_has_support_matrix_with_tiers() -> None:
    text = (ROOT / "docs" / "platforms.md").read_text(encoding="utf-8")

    expected_snippets = [
        "# Platform Support",
        "| Platform | Tier |",
        "native",
        "partial",
        "planned",
        "Claude",
        "Cursor",
        "Codex",
        "Replit",
        "Windsurf",
        "Lovable",
        "OpenClaw",
        "Kimi",
        "replit.md",
        ".windsurf/rules",
        ".lovable/project-knowledge.md",
        "SOUL.md",
        "Modelfile.repo-context",
        "Kimi Code CLI",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing platform doc snippet: {snippet}"


def test_platform_doc_explains_no_hook_parity_claims() -> None:
    text = (ROOT / "docs" / "platforms.md").read_text(encoding="utf-8")

    expected_snippets = [
        "no Claude-style hook parity",
        "no native lifecycle hooks or compact automation",
        "do not claim universal agent support",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing support-tier caveat: {snippet}"


def test_architecture_and_competitive_docs_match_repo_native_positioning() -> None:
    architecture = (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
    competitive = (ROOT / "docs" / "competitive-analysis.md").read_text(encoding="utf-8")
    positioning = (ROOT / "docs" / "positioning.md").read_text(encoding="utf-8")

    assert "repo-native continuity layer" in architecture
    assert "platform adapters expose different continuity surfaces" in architecture
    assert "repo-native continuity" in competitive
    assert "not a universal memory layer" in competitive
    assert "native support on Claude" in positioning
    assert "partial support on Cursor, Codex, Replit, Windsurf, Lovable, OpenClaw, Ollama, and Kimi" in positioning
    assert "replit.md" in architecture
    assert ".windsurf/rules" in architecture
    assert ".lovable/project-knowledge.md" in architecture
    assert "Current support is intentionally built around nine platforms" in architecture
