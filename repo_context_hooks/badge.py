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


def render_badge(score: int, label: str = "context score") -> str:
    """Return a shields.io-style flat SVG badge as a string."""
    color = _score_color(score)
    value = str(score)
    # Approximate text widths (Verdana 11px ~= 6.5px per char)
    label_w = max(len(label) * 6 + 10, 60)
    value_w = max(len(value) * 7 + 10, 28)
    total_w = label_w + value_w
    label_x = label_w // 2
    value_x = label_w + value_w // 2

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
    <rect x="{label_w}" width="{value_w}" height="20" fill="{color}"/>
    <rect width="{total_w}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="110">
    <text x="{label_x * 10}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{(label_w - 10) * 10}" lengthAdjust="spacing">{label}</text>
    <text x="{label_x * 10}" y="140" transform="scale(.1)" textLength="{(label_w - 10) * 10}" lengthAdjust="spacing">{label}</text>
    <text x="{value_x * 10}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{(value_w - 10) * 10}" lengthAdjust="spacing">{value}</text>
    <text x="{value_x * 10}" y="140" transform="scale(.1)" textLength="{(value_w - 10) * 10}" lengthAdjust="spacing">{value}</text>
  </g>
</svg>"""
