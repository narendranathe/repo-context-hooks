from __future__ import annotations


_COLORS = {
    "green": "#4c1",
    "yellow": "#db1",
    "red": "#e05",
}


def _score_color(score: int) -> str:
    if score >= 80:
        return _COLORS["green"]
    if score >= 60:
        return _COLORS["yellow"]
    return _COLORS["red"]


def _coverage_color(coverage: int) -> str:
    if coverage >= 75:
        return _COLORS["green"]
    if coverage >= 25:
        return _COLORS["yellow"]
    return _COLORS["red"]


def render_badge(score: int, coverage: int, label: str = "context score") -> str:
    """Return a shields.io-style flat SVG badge as a string (three sections)."""
    score_color = _score_color(score)
    cov_color = _coverage_color(coverage)
    score_val = str(score)
    cov_label = f"{coverage}%"

    # Approximate text widths (Verdana 11px ~= 6.5px per char)
    label_w = max(len(label) * 6 + 10, 80)
    score_w = max(len(score_val) * 7 + 10, 28)
    cov_w = max(len(cov_label) * 7 + 10, 32)
    total_w = label_w + score_w + cov_w

    label_x = label_w // 2
    score_x = label_w + score_w // 2
    cov_x = label_w + score_w + cov_w // 2

    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{total_w}" height="20">
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{total_w}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_w}" height="20" fill="#555"/>
    <rect x="{label_w}" width="{score_w}" height="20" fill="{score_color}"/>
    <rect x="{label_w + score_w}" width="{cov_w}" height="20" fill="{cov_color}"/>
    <rect width="{total_w}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="110">
    <text x="{label_x * 10}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{(label_w - 10) * 10}" lengthAdjust="spacing">{label}</text>
    <text x="{label_x * 10}" y="140" transform="scale(.1)" textLength="{(label_w - 10) * 10}" lengthAdjust="spacing">{label}</text>
    <text x="{score_x * 10}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{(score_w - 10) * 10}" lengthAdjust="spacing">{score_val}</text>
    <text x="{score_x * 10}" y="140" transform="scale(.1)" textLength="{(score_w - 10) * 10}" lengthAdjust="spacing">{score_val}</text>
    <text x="{cov_x * 10}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{(cov_w - 10) * 10}" lengthAdjust="spacing">{cov_label}</text>
    <text x="{cov_x * 10}" y="140" transform="scale(.1)" textLength="{(cov_w - 10) * 10}" lengthAdjust="spacing">{cov_label}</text>
  </g>
</svg>"""
