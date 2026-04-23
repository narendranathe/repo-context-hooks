from __future__ import annotations

from repo_context_hooks.platforms import get_registry


def test_registry_exposes_supported_platform_ids() -> None:
    registry = get_registry()

    assert [adapter.id for adapter in registry.all()] == [
        "claude",
        "cursor",
        "codex",
        "replit",
        "windsurf",
        "lovable",
    ]


def test_registry_support_tiers_match_current_contract() -> None:
    registry = get_registry()

    assert registry.get("claude").support_tier.value == "native"
    assert registry.get("cursor").support_tier.value == "partial"
    assert registry.get("codex").support_tier.value == "partial"
    assert registry.get("replit").support_tier.value == "partial"
    assert registry.get("windsurf").support_tier.value == "partial"
    assert registry.get("lovable").support_tier.value == "partial"


def test_registry_metadata_describes_install_surfaces() -> None:
    registry = get_registry()

    assert registry.get("claude").metadata.install_surfaces == (
        "skills",
        "repo-hooks",
    )
    assert registry.get("cursor").metadata.install_surfaces == (
        "cursor-rules",
        "repo-contract",
    )
    assert registry.get("codex").metadata.install_surfaces == (
        "repo-contract",
    )
    assert registry.get("replit").metadata.install_surfaces == (
        "replit-md",
        "repo-contract",
    )
    assert registry.get("windsurf").metadata.install_surfaces == (
        "agents-md",
        "windsurf-rules",
    )
    assert registry.get("lovable").metadata.install_surfaces == (
        "agents-md",
        "lovable-knowledge-export",
    )
