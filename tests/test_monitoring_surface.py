from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_public_monitoring_dashboard_exists_and_shows_repo_impact() -> None:
    dashboard = ROOT / "docs" / "monitoring" / "index.html"
    text = dashboard.read_text(encoding="utf-8")

    required = [
        "Continuity Impact Monitor",
        "Score 90",
        "+70 uplift",
        "18+ hook events",
        "Claude native hooks",
        "Codex/Kimi repo entry",
        "Local-only telemetry",
    ]
    for snippet in required:
        assert snippet in text


def test_readme_hero_visual_exists_and_carries_core_story() -> None:
    asset = ROOT / "assets" / "diagrams" / "context-continuity-engine.svg"
    text = asset.read_text(encoding="utf-8").lower()

    required = [
        "context continuity engine",
        "readme.md",
        "specs/readme.md",
        "agents.md",
        "hook events",
        "score 90",
        "+70 uplift",
    ]
    for snippet in required:
        assert snippet in text


def test_readme_embeds_monitoring_brand_assets() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "assets/diagrams/context-continuity-engine.svg" in readme
    assert "docs/monitoring/index.html" in readme
    assert "Score `90`" in readme
    assert "Uplift `+70`" in readme
