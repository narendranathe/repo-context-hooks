from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_platform_playbooks_doc_exists_but_is_not_primary_public_path() -> None:
    playbooks = ROOT / "docs" / "platform-playbooks.md"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    platforms = (ROOT / "docs" / "platforms.md").read_text(encoding="utf-8")

    assert playbooks.exists()
    assert "docs/platform-playbooks.md" not in readme
    assert "docs/platform-playbooks.md" not in platforms


def test_platform_playbooks_cover_supported_platforms_and_boundaries() -> None:
    text = (ROOT / "docs" / "platform-playbooks.md").read_text(encoding="utf-8")

    expected_snippets = [
        "# Platform Playbooks",
        "## Replit",
        "## Windsurf",
        "## Lovable",
        "## OpenClaw",
        "## Ollama",
        "## Kimi",
        "What gets installed",
        "What remains manual",
        "What not to claim",
        "no native lifecycle hooks",
        "no compact automation",
        "https://github.com/narendranathe/repo-context-hooks/issues/2",
        "https://github.com/narendranathe/repo-context-hooks/issues/3",
        "https://github.com/narendranathe/repo-context-hooks/issues/4",
        "https://github.com/narendranathe/repo-context-hooks/issues/5",
        "https://github.com/narendranathe/repo-context-hooks/issues/6",
        "https://github.com/narendranathe/repo-context-hooks/issues/8",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing playbook snippet: {snippet}"


def test_platform_playbooks_keep_ollama_and_kimi_claims_narrow() -> None:
    text = (ROOT / "docs" / "platform-playbooks.md").read_text(encoding="utf-8")

    assert "Ollama is a model runtime" in text
    assert "does not read repo files automatically" in text
    assert "Kimi Code CLI" in text
    assert "not generic Kimi API setup" in text
