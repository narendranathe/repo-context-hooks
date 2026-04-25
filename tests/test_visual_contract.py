from __future__ import annotations

from pathlib import Path
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS = ROOT / "assets" / "diagrams"
BRAND = ROOT / "assets" / "brand"
MONITORING = ROOT / "docs" / "monitoring"


def _svg_root(path: Path) -> ET.Element:
    return ET.fromstring(path.read_text(encoding="utf-8"))


def _viewbox(root: ET.Element) -> tuple[float, float, float, float]:
    raw = root.attrib["viewBox"]
    values = tuple(float(part) for part in raw.split())
    assert len(values) == 4
    return values


def _numbers(value: str) -> list[float]:
    return [float(item) for item in re.findall(r"-?\d+(?:\.\d+)?", value)]


def _svg_text_value(element: ET.Element) -> str:
    return "".join(element.itertext()).strip()


def _svg_font_size(element: ET.Element) -> float:
    return float(element.attrib.get("font-size", "16"))


def _estimated_text_width(text: str, font_size: float) -> float:
    # Segoe UI/Georgia vary by glyph, so this intentionally leans conservative.
    return len(text) * font_size * 0.64


def _walk_visible(root: ET.Element):
    ignored = {"defs", "title", "desc", "marker", "pattern", "filter", "linearGradient", "radialGradient", "style"}

    def visit(element: ET.Element, hidden: bool = False):
        tag = element.tag.rsplit("}", 1)[-1]
        hidden = hidden or tag in ignored
        if not hidden:
            yield element
        for child in element:
            yield from visit(child, hidden)

    yield from visit(root)


def test_diagram_assets_keep_content_inside_safe_margins() -> None:
    for path in sorted(DIAGRAMS.glob("*.svg")):
        root = _svg_root(path)
        _, _, width, height = _viewbox(root)
        for element in _walk_visible(root):
            tag = element.tag.rsplit("}", 1)[-1]
            if tag in {"rect", "text", "circle"}:
                for attr in ("x", "y", "cx", "cy"):
                    if attr in element.attrib:
                        value = float(element.attrib[attr])
                        assert 32 <= value <= width - 32, f"{path.name} {tag}.{attr}={value} is too close to edge"
                if tag == "rect":
                    x = float(element.attrib.get("x", "0"))
                    y = float(element.attrib.get("y", "0"))
                    rect_width = float(element.attrib.get("width", "0"))
                    rect_height = float(element.attrib.get("height", "0"))
                    if x > 0 and y > 0:
                        assert x + rect_width <= width - 32, f"{path.name} rect overflows right edge"
                        assert y + rect_height <= height - 32, f"{path.name} rect overflows bottom edge"


def test_diagram_paths_do_not_draw_outside_viewbox() -> None:
    for path in sorted(DIAGRAMS.glob("*.svg")):
        root = _svg_root(path)
        _, _, width, height = _viewbox(root)
        for element in _walk_visible(root):
            if element.tag.rsplit("}", 1)[-1] != "path":
                continue
            values = _numbers(element.attrib.get("d", ""))
            for index in range(0, len(values) - 1, 2):
                x = values[index]
                y = values[index + 1]
                assert 24 <= x <= width - 24, f"{path.name} path x={x} is outside safe viewBox"
                assert 24 <= y <= height - 24, f"{path.name} path y={y} is outside safe viewBox"


def test_diagram_lines_and_polylines_stay_inside_safe_margins() -> None:
    for path in sorted(DIAGRAMS.glob("*.svg")):
        root = _svg_root(path)
        _, _, width, height = _viewbox(root)
        for element in _walk_visible(root):
            tag = element.tag.rsplit("}", 1)[-1]
            if tag == "line":
                for attr in ("x1", "x2"):
                    value = float(element.attrib[attr])
                    assert 24 <= value <= width - 24, f"{path.name} line {attr}={value} is outside safe viewBox"
                for attr in ("y1", "y2"):
                    value = float(element.attrib[attr])
                    assert 24 <= value <= height - 24, f"{path.name} line {attr}={value} is outside safe viewBox"
            if tag == "polyline":
                values = _numbers(element.attrib.get("points", ""))
                for index in range(0, len(values) - 1, 2):
                    x = values[index]
                    y = values[index + 1]
                    assert 24 <= x <= width - 24, f"{path.name} polyline x={x} is outside safe viewBox"
                    assert 24 <= y <= height - 24, f"{path.name} polyline y={y} is outside safe viewBox"


def test_visual_assets_avoid_transform_based_edge_positioning() -> None:
    for path in [
        *sorted(DIAGRAMS.glob("*.svg")),
        MONITORING / "timeseries.svg",
        BRAND / "repo-context-hooks-logo.svg",
    ]:
        text = path.read_text(encoding="utf-8")
        assert "transform=" not in text, f"{path.name} should use direct coordinates for easier edge safety"


def test_monitoring_timeseries_svg_keeps_readme_graph_inside_safe_margins() -> None:
    path = MONITORING / "timeseries.svg"
    root = _svg_root(path)
    _, _, width, height = _viewbox(root)
    for element in _walk_visible(root):
        tag = element.tag.rsplit("}", 1)[-1]
        if tag in {"rect", "text", "circle"}:
            for attr in ("x", "y", "cx", "cy"):
                if attr in element.attrib:
                    value = float(element.attrib[attr])
                    assert 32 <= value <= width - 32, f"{path.name} {tag}.{attr}={value} is too close to edge"
            if tag == "rect":
                x = float(element.attrib.get("x", "0"))
                y = float(element.attrib.get("y", "0"))
                rect_width = float(element.attrib.get("width", "0"))
                rect_height = float(element.attrib.get("height", "0"))
                if x > 0 and y > 0:
                    assert x + rect_width <= width - 32, f"{path.name} rect overflows right edge"
                    assert y + rect_height <= height - 32, f"{path.name} rect overflows bottom edge"


def test_monitoring_timeseries_svg_text_estimates_stay_inside_viewbox() -> None:
    path = MONITORING / "timeseries.svg"
    root = _svg_root(path)
    _, _, width, _ = _viewbox(root)
    for element in _walk_visible(root):
        if element.tag.rsplit("}", 1)[-1] != "text":
            continue
        text = _svg_text_value(element)
        if not text:
            continue
        x = float(element.attrib.get("x", "0"))
        font_size = _svg_font_size(element)
        estimated_right_edge = x + _estimated_text_width(text, font_size)

        assert estimated_right_edge <= width - 32, (
            f"{path.name} text may overflow right edge: {text!r} "
            f"estimated at {estimated_right_edge:.1f}px"
        )


def test_brand_svg_keeps_visible_artwork_inside_logo_tile() -> None:
    root = _svg_root(BRAND / "repo-context-hooks-logo.svg")
    _, _, width, height = _viewbox(root)
    for element in _walk_visible(root):
        tag = element.tag.rsplit("}", 1)[-1]
        if tag in {"rect", "circle", "path", "text"}:
            for attr in ("x", "y", "cx", "cy"):
                if attr in element.attrib:
                    value = float(element.attrib[attr])
                    assert 40 <= value <= width - 40, f"brand {tag}.{attr}={value} is too close to edge"


def test_lifecycle_diagram_mentions_real_interrupted_workflow() -> None:
    text = (ROOT / "assets" / "diagrams" / "lifecycle-flow.svg").read_text(encoding="utf-8").lower()

    expected_snippets = [
        "bugfix interrupted by compact",
        "checkpoint written to specs/readme.md",
        "next session resumes from repo state",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing lifecycle story detail: {snippet}"


def test_repo_contract_diagram_mentions_handoff_story() -> None:
    text = (ROOT / "assets" / "diagrams" / "repo-contract.svg").read_text(encoding="utf-8").lower()

    expected_snippets = [
        "open pr story stays in readme.md",
        "handoff notes land in specs/readme.md",
        "agents.md guides the re-entry",
        "cursor or codex can re-enter with repo context",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing repo contract story detail: {snippet}"


def test_before_after_diagram_mentions_repeated_work_and_clean_handoff() -> None:
    text = (ROOT / "assets" / "diagrams" / "before-after-continuity.svg").read_text(encoding="utf-8").lower()

    expected_snippets = [
        "same bug explained again",
        "re-read the repo and resume review comments",
        "resume from checked-in continuity",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing before/after story detail: {snippet}"


def test_context_engine_hero_mentions_continuous_monitoring() -> None:
    text = (ROOT / "assets" / "diagrams" / "context-continuity-engine.svg").read_text(encoding="utf-8").lower()

    expected_snippets = [
        "context continuity engine",
        "hook events",
        "impact monitor",
        "score 90",
        "+70 uplift",
        "next agent resumes warm",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing context engine hero detail: {snippet}"


def test_platform_roadmap_doc_links_planned_platforms() -> None:
    text = (ROOT / "docs" / "launch" / "platform-roadmap.md").read_text(encoding="utf-8")

    expected_snippets = [
        "# Planned Platform Roadmap",
        "current partial support via `replit.md`",
        "Windsurf",
        "Replit",
        "Lovable",
        "Ollama",
        "OpenClaw",
        "Kimi",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing roadmap snippet: {snippet}"
    assert "Likely tier:" not in text
    assert "no native lifecycle hooks" in text
    assert "project knowledge" in text.lower()


def test_animation_plan_stays_static_first_but_story_driven() -> None:
    text = (ROOT / "docs" / "demo" / "animation-plan.md").read_text(encoding="utf-8").lower()

    expected_snippets = [
        "static svg remains the source of truth",
        "interrupted task",
        "handoff story",
        "do not imply automation the tool does not provide",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing animation plan guidance: {snippet}"
