from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from uuid import uuid4

from repo_context_hooks.badge import render_badge
from repo_context_hooks.cli import _measure

ROOT = Path(__file__).resolve().parents[1]


def _tmp_dir() -> Path:
    base = ROOT / ".tmp-tests"
    base.mkdir(exist_ok=True)
    path = base / uuid4().hex
    path.mkdir()
    return path


def test_render_badge_green() -> None:
    svg = render_badge(90)
    assert "4c1" in svg
    assert "90" in svg
    assert "<svg" in svg


def test_render_badge_yellow() -> None:
    svg = render_badge(70)
    assert "db1" in svg
    assert "70" in svg
    assert "<svg" in svg


def test_render_badge_red() -> None:
    svg = render_badge(40)
    assert "e05" in svg
    assert "40" in svg
    assert "<svg" in svg


def test_render_badge_boundary_green_at_80() -> None:
    svg = render_badge(80)
    assert "4c1" in svg


def test_render_badge_boundary_yellow_at_60() -> None:
    svg = render_badge(60)
    assert "db1" in svg


def test_render_badge_boundary_red_at_59() -> None:
    svg = render_badge(59)
    assert "e05" in svg


def test_render_badge_custom_label() -> None:
    svg = render_badge(85, label="my score")
    assert "my score" in svg
    assert "85" in svg


def test_render_badge_is_valid_svg() -> None:
    svg = render_badge(90)
    assert svg.strip().startswith("<svg")
    assert "</svg>" in svg
    # No unescaped < or > in text content (they appear in tags, but label is plain text)
    # Confirm the label text itself doesn't break SVG
    assert "context score" in svg


def test_measure_badge_flag_outputs_svg(monkeypatch, capsys) -> None:
    tmp_path = _tmp_dir()

    class FakeReport:
        current_score = 90

        def render(self) -> str:
            return "[OK] context-impact"

        def to_dict(self):
            return {"current_score": 90}

    monkeypatch.setattr(
        "repo_context_hooks.cli.measure_impact",
        lambda repo_root: FakeReport(),
    )

    args = Namespace(
        repo_root=str(tmp_path),
        badge=True,
        badge_out=None,
        json=False,
        snapshot_dir=None,
    )

    assert _measure(args) == 0
    out = capsys.readouterr().out
    assert "<svg" in out
    assert "4c1" in out  # score 90 -> green
    assert "90" in out


def test_measure_badge_out_writes_file(monkeypatch, capsys) -> None:
    tmp_path = _tmp_dir()
    badge_path = tmp_path / "badge.svg"

    class FakeReport:
        current_score = 70

        def render(self) -> str:
            return "[OK] context-impact"

        def to_dict(self):
            return {"current_score": 70}

    monkeypatch.setattr(
        "repo_context_hooks.cli.measure_impact",
        lambda repo_root: FakeReport(),
    )

    args = Namespace(
        repo_root=str(tmp_path),
        badge=False,
        badge_out=str(badge_path),
        json=False,
        snapshot_dir=None,
    )

    assert _measure(args) == 0
    out = capsys.readouterr().out
    assert f"Badge written to: {badge_path}" in out
    assert badge_path.exists()
    content = badge_path.read_text(encoding="utf-8")
    assert "<svg" in content
    assert "db1" in content  # score 70 -> yellow
    assert "70" in content


def test_measure_normal_output_unaffected(monkeypatch, capsys) -> None:
    """Normal measure output still works when neither --badge nor --badge-out is passed."""
    tmp_path = _tmp_dir()

    class FakeReport:
        current_score = 90

        def render(self) -> str:
            return "[OK] context-impact score=90"

        def to_dict(self):
            return {"current_score": 90}

    monkeypatch.setattr(
        "repo_context_hooks.cli.measure_impact",
        lambda repo_root: FakeReport(),
    )

    args = Namespace(
        repo_root=str(tmp_path),
        badge=False,
        badge_out=None,
        json=False,
        snapshot_dir=None,
    )

    assert _measure(args) == 0
    out = capsys.readouterr().out
    assert "[OK] context-impact score=90" in out
    assert "<svg" not in out
