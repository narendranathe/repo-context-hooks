from __future__ import annotations

from pathlib import Path
import struct


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


def test_readme_timeseries_visual_exists_and_uses_snapshot_data() -> None:
    asset = ROOT / "docs" / "monitoring" / "timeseries.svg"
    text = asset.read_text(encoding="utf-8").lower()

    required = [
        "telemetry time series",
        "generated from docs/monitoring/history.json",
        "2026-04-24",
        "2026-04-25",
        "score 90",
        "32 hook events",
        "session-start",
    ]
    for snippet in required:
        assert snippet in text


def test_readme_embeds_monitoring_brand_assets() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "assets/brand/repo-context-hooks-logo.png" in readme
    assert "assets/diagrams/telemetry-proof-strip.svg" not in readme
    assert "docs/monitoring/timeseries.svg" in readme
    assert "assets/diagrams/context-continuity-engine.svg" in readme
    assert "docs/monitoring/index.html" in readme
    assert "docs/monitoring/history.json" in readme
    assert "generated from the same `docs/monitoring/history.json`" in readme
    assert "repo-context-hooks measure --prometheus" in readme
    assert "Grafana" in readme
    assert "Datadog" in readme
    assert "Telemetry Visibility" in readme
    assert "Observable Plot" in readme
    assert "Vega-Lite" in readme
    assert "Score `90`" in readme
    assert "Uplift `+70`" in readme


def test_png_brand_logo_exists_and_has_expected_dimensions() -> None:
    logo = ROOT / "assets" / "brand" / "repo-context-hooks-logo.png"
    data = logo.read_bytes()

    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(data) > 4096
    width, height = struct.unpack(">II", data[16:24])
    assert (width, height) == (512, 512)


def test_svg_brand_logo_source_carries_product_language() -> None:
    logo = ROOT / "assets" / "brand" / "repo-context-hooks-logo.svg"
    text = logo.read_text(encoding="utf-8")

    required = [
        "repo-context-hooks",
        "context continuity",
        "hook events",
        "impact monitor",
    ]
    for snippet in required:
        assert snippet in text
