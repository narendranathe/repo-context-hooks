from __future__ import annotations

from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]


def test_public_monitoring_dashboard_exists_and_shows_repo_impact() -> None:
    dashboard = ROOT / "docs" / "monitoring" / "index.html"
    text = dashboard.read_text(encoding="utf-8")

    required = [
        "Continuity Impact Monitor",
        "Contract score",
        "Continuity uplift",
        "Tokens injected",
        "Lifecycle coverage",
        "Claude native hooks",
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

    assert "assets/brand/repo-context-hooks-logo.png" in readme
    assert "assets/diagrams/context-continuity-engine.svg" in readme
    assert "docs/monitoring/index.html" in readme
    assert "docs/monitoring/history.json" in readme
    assert "Telemetry Visibility" in readme
    assert "Observable Plot" in readme
    assert "Vega-Lite" in readme
    assert "90 / 100" in readme
    assert "+70 points" in readme


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


def test_dashboard_contains_cold_start_card():
    """Dashboard HTML must show the cold start time saved metric."""
    from repo_context_hooks.telemetry import render_monitoring_dashboard, _make_test_report
    report = _make_test_report(reload_events=3)  # 3 * 5 = 15 min
    html = render_monitoring_dashboard(report)
    assert "Cold starts prevented" in html
    assert "15 min" in html


def test_dashboard_contains_week1_uplift_card():
    """Dashboard HTML must show the week-1 score uplift when data is available."""
    from repo_context_hooks.telemetry import render_monitoring_dashboard, _make_test_report
    report = _make_test_report(score_week1_uplift=25)
    html = render_monitoring_dashboard(report)
    assert "Week-1 uplift" in html
    assert "+25" in html


def test_dashboard_uplift_dash_when_none():
    """Dashboard must show — when score_week1_uplift is None."""
    from repo_context_hooks.telemetry import render_monitoring_dashboard, _make_test_report
    report = _make_test_report(score_week1_uplift=None)
    html = render_monitoring_dashboard(report)
    assert "Week-1 uplift" in html
    assert "—" in html  # em-dash rendered when uplift is None
