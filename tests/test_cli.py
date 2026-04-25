from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from repo_context_hooks.cli import (
    _doctor,
    _init,
    _install,
    _measure,
    _platforms,
    _recommend,
    build_parser,
)
from repo_context_hooks.doctor import DoctorReport

ROOT = Path(__file__).resolve().parents[1]


def _tmp_dir() -> Path:
    base = ROOT / ".tmp-tests"
    base.mkdir(exist_ok=True)
    path = base / uuid4().hex
    path.mkdir()
    return path


def test_build_parser_uses_public_name() -> None:
    parser = build_parser()
    assert parser.prog == "repo-context-hooks"
    assert "repo context continuity" in parser.description.lower()


def test_parser_supports_platforms_and_doctor_commands() -> None:
    parser = build_parser()

    assert parser.parse_args(["platforms"]).command == "platforms"
    assert parser.parse_args(["platforms", "--json"]).json is True
    assert parser.parse_args(["doctor", "--platform", "claude"]).command == "doctor"
    assert parser.parse_args(["doctor", "--platform", "claude", "--json"]).json is True
    assert parser.parse_args(["doctor", "--all-platforms"]).command == "doctor"
    assert parser.parse_args(["doctor"]).command == "doctor"
    assert parser.parse_args(["init"]).command == "init"
    assert parser.parse_args(["recommend"]).command == "recommend"
    assert parser.parse_args(["recommend", "--json"]).json is True
    assert parser.parse_args(["measure"]).command == "measure"
    assert parser.parse_args(["measure", "--json"]).json is True
    assert parser.parse_args(["measure", "--prometheus"]).prometheus is True
    assert (
        parser.parse_args(
            ["measure", "--snapshot-dir", "docs/monitoring"]
        ).snapshot_dir
        == "docs/monitoring"
    )


def test_platforms_print_support_tiers(capsys) -> None:
    assert _platforms(Namespace(json=False)) == 0

    out = capsys.readouterr().out
    assert "claude" in out
    assert "cursor" in out
    assert "codex" in out
    assert "replit" in out
    assert "windsurf" in out
    assert "lovable" in out
    assert "openclaw" in out
    assert "ollama" in out
    assert "kimi" in out
    assert "native" in out
    assert "partial" in out


def test_platforms_prints_json(capsys) -> None:
    assert _platforms(Namespace(json=True)) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["platforms"][0]["id"] == "claude"
    assert payload["platforms"][0]["support_tier"] == "native"


def test_install_skips_repo_context_outside_git_repo(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()
    calls: list[bool] = []

    def fake_install_platform(
        platform: str,
        repo_root,
        force: bool = False,
        home=None,
        install_repo_context: bool = True,
    ):
        calls.append(install_repo_context)
        return SimpleNamespace(
            summary="Codex partial support installed.",
            home_target=None,
            home_statuses={"context-handoff-hooks": "installed"},
            repo_statuses={},
            warnings=(),
            manual_steps=(),
        )

    monkeypatch.setattr(
        "repo_context_hooks.cli.install_platform",
        fake_install_platform,
    )

    args = Namespace(
        platform="codex",
        force=False,
        skip_repo_hooks=False,
        repo_root=str(tmp_path),
    )

    assert _install(args) == 0
    out = capsys.readouterr().out
    assert "Repo context skipped: target is not a git repository." in out
    assert "Codex partial support installed." in out
    assert calls == [False]


def test_install_respects_skip_repo_hooks(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()
    calls: list[bool] = []

    def fake_install_platform(
        platform: str,
        repo_root,
        force: bool = False,
        home=None,
        install_repo_context: bool = True,
    ):
        calls.append(install_repo_context)
        return SimpleNamespace(
            summary="Claude native support installed.",
            home_target=None,
            home_statuses={"context-handoff-hooks": "installed"},
            repo_statuses={},
            warnings=(),
            manual_steps=(),
        )

    monkeypatch.setattr(
        "repo_context_hooks.cli.install_platform",
        fake_install_platform,
    )

    args = Namespace(
        platform="claude",
        force=False,
        skip_repo_hooks=True,
        repo_root=str(tmp_path),
    )

    assert _install(args) == 0
    out = capsys.readouterr().out
    assert "Skipped repo context installation" in out
    assert calls == [False]


def test_doctor_returns_nonzero_for_missing_state(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()

    def fake_diagnose_platform(platform: str, repo_root, home=None) -> DoctorReport:
        return DoctorReport(
            platform_id=platform,
            ok=False,
            present=(),
            missing=(".cursor/rules/repo-context-continuity.mdc",),
            warnings=("Cursor is partial support only.",),
        )

    monkeypatch.setattr(
        "repo_context_hooks.cli.diagnose_platform",
        fake_diagnose_platform,
    )

    args = Namespace(
        platform="cursor",
        repo_root=str(tmp_path),
    )

    assert _doctor(args) == 1
    out = capsys.readouterr().out
    assert "repo-context-continuity.mdc" in out


def test_doctor_all_platforms_prints_matrix_summary(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()

    class FakeReport:
        ok = True

        def render(self) -> str:
            return "[OK] platform-readiness\nclaude\tnative\tmissing\tsettings.json"

        def to_dict(self):
            return {"ok": True, "platforms": [{"platform_id": "claude"}]}

    monkeypatch.setattr(
        "repo_context_hooks.cli.diagnose_all_platforms",
        lambda repo_root: FakeReport(),
    )

    args = Namespace(
        platform=None,
        all_platforms=True,
        repo_root=str(tmp_path),
        json=False,
    )

    assert _doctor(args) == 0
    out = capsys.readouterr().out
    assert "platform-readiness" in out
    assert "claude" in out


def test_doctor_prints_json(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()

    class FakeReport:
        ok = True

        def render(self) -> str:
            return "[OK] repo-contract"

        def to_dict(self):
            return {"platform_id": "repo-contract", "ok": True}

    monkeypatch.setattr(
        "repo_context_hooks.cli.diagnose_repo_contract",
        lambda repo_root: FakeReport(),
    )

    args = Namespace(
        platform=None,
        all_platforms=False,
        repo_root=str(tmp_path),
        json=True,
    )

    assert _doctor(args) == 0
    assert json.loads(capsys.readouterr().out)["platform_id"] == "repo-contract"


def test_measure_prints_json(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()

    class FakeReport:
        def render(self) -> str:
            return "[OK] context-impact"

        def to_dict(self):
            return {
                "repo_name": "demo",
                "current_score": 84,
                "estimated_baseline_score": 35,
                "uplift": 49,
            }

    monkeypatch.setattr(
        "repo_context_hooks.cli.measure_impact",
        lambda repo_root: FakeReport(),
    )

    args = Namespace(
        repo_root=str(tmp_path),
        json=True,
        prometheus=False,
    )

    assert _measure(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["repo_name"] == "demo"
    assert payload["uplift"] == 49


def test_measure_prints_prometheus_metrics(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()

    class FakeReport:
        pass

    monkeypatch.setattr(
        "repo_context_hooks.cli.measure_impact",
        lambda repo_root: FakeReport(),
    )
    monkeypatch.setattr(
        "repo_context_hooks.cli.render_prometheus_metrics",
        lambda report: "repo_context_hooks_continuity_score 90\n",
    )

    args = Namespace(
        repo_root=str(tmp_path),
        json=False,
        prometheus=True,
        snapshot_dir=None,
    )

    assert _measure(args) == 0
    assert capsys.readouterr().out == "repo_context_hooks_continuity_score 90\n"


def test_measure_writes_public_snapshot(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()
    calls: list[tuple[str, Path]] = []

    class FakeReport:
        def render(self) -> str:
            return "[OK] context-impact"

        def to_dict(self):
            return {
                "repo_name": "demo",
                "current_score": 84,
                "estimated_baseline_score": 35,
                "uplift": 49,
            }

    def fake_snapshot(report, output_dir):
        calls.append((report.to_dict()["repo_name"], output_dir))
        return {
            "dashboard_path": str(output_dir / "index.html"),
            "history_path": str(output_dir / "history.json"),
        }

    monkeypatch.setattr(
        "repo_context_hooks.cli.measure_impact",
        lambda repo_root: FakeReport(),
    )
    monkeypatch.setattr(
        "repo_context_hooks.cli.write_public_monitoring_snapshot",
        fake_snapshot,
    )

    args = Namespace(
        repo_root=str(tmp_path),
        json=False,
        prometheus=False,
        snapshot_dir="docs/monitoring",
    )

    assert _measure(args) == 0
    out = capsys.readouterr().out
    assert "Wrote public monitoring snapshot" in out
    assert calls == [("demo", tmp_path / "docs" / "monitoring")]


def test_init_prints_repo_contract_statuses(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()

    def fake_init_repo_contract(repo_root, force: bool = False):
        return {
            "README.md": "installed",
            "specs/README.md": "installed",
            "UBIQUITOUS_LANGUAGE.md": "installed",
            "AGENTS.md": "skipped",
        }

    monkeypatch.setattr(
        "repo_context_hooks.cli.init_repo_contract",
        fake_init_repo_contract,
    )

    args = Namespace(
        repo_root=str(tmp_path),
        force=False,
    )

    assert _init(args) == 0
    out = capsys.readouterr().out
    assert "Initialized repo contract" in out
    assert "README.md: installed" in out
    assert "AGENTS.md: skipped" in out


def test_recommend_prints_ranked_output(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()

    class FakeRecommendations:
        def render(self) -> str:
            return "[RECOMMEND]\n1. claude\nNext: repo-context-hooks install --platform claude"

        def to_dict(self):
            return {"recommendations": [{"platform_id": "claude"}]}

    monkeypatch.setattr(
        "repo_context_hooks.cli.recommend_setup",
        lambda repo_root, limit=3: FakeRecommendations(),
    )

    args = Namespace(
        repo_root=str(tmp_path),
        limit=3,
        json=False,
    )

    assert _recommend(args) == 0
    out = capsys.readouterr().out
    assert "[RECOMMEND]" in out
    assert "repo-context-hooks install --platform claude" in out


def test_recommend_prints_json(
    monkeypatch,
    capsys,
) -> None:
    tmp_path = _tmp_dir()

    class FakeRecommendations:
        def render(self) -> str:
            return "[RECOMMEND]"

        def to_dict(self):
            return {"recommendations": [{"platform_id": "claude"}]}

    monkeypatch.setattr(
        "repo_context_hooks.cli.recommend_setup",
        lambda repo_root, limit=3: FakeRecommendations(),
    )

    args = Namespace(
        repo_root=str(tmp_path),
        limit=3,
        json=True,
    )

    assert _recommend(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["recommendations"][0]["platform_id"] == "claude"
