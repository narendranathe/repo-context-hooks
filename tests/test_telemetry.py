from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from repo_context_hooks.repo_contract import init_repo_contract
from repo_context_hooks.telemetry import (
    measure_rollup,
    measure_impact,
    record_context_window,
    record_event,
    render_rollup_prometheus_metrics,
    render_prometheus_metrics,
    render_public_time_series_svg,
    telemetry_dir,
    write_public_rollup_snapshot,
    write_public_monitoring_snapshot,
)

ROOT = Path(__file__).resolve().parents[1]


def _tmp_dir() -> Path:
    base = ROOT / ".tmp-tests"
    base.mkdir(exist_ok=True)
    path = base / uuid4().hex
    path.mkdir()
    return path


def test_record_event_writes_local_jsonl_outside_repo() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo_contract(repo)
    telemetry_base = tmp_path / "telemetry"

    event_path = record_event(
        repo,
        "session-start",
        source="test-hook",
        telemetry_base=telemetry_base,
        details={"context_bytes": 123},
    )

    assert telemetry_base in event_path.parents
    assert repo not in event_path.parents

    payload = json.loads(event_path.read_text(encoding="utf-8").splitlines()[0])
    assert payload["event_name"] == "session-start"
    assert payload["source"] == "test-hook"
    assert payload["agent_platform"] == "unknown"
    assert payload["model_name"] == "unknown"
    assert payload["agent_session_id"]
    assert payload["repo_name"] == "repo"
    assert payload["repo_id"]
    assert payload["repo_contract_score"] > 0
    assert payload["details"]["context_bytes"] == 123
    assert (event_path.parent / "monitoring.html").exists()


def test_record_event_stores_agent_platform_and_model_name() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo_contract(repo)

    event_path = record_event(
        repo,
        "session-start",
        source="codex-hook",
        telemetry_base=tmp_path / "telemetry",
        agent_platform="codex",
        model_name="gpt-test",
    )

    payload = json.loads(event_path.read_text(encoding="utf-8").splitlines()[0])

    assert payload["agent_platform"] == "codex"
    assert payload["model_name"] == "gpt-test"
    assert payload["agent_session_id"]


def test_record_event_reuses_agent_session_for_one_lifecycle() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo_contract(repo)
    telemetry_base = tmp_path / "telemetry"

    first_path = record_event(
        repo,
        "session-start",
        source="repo_specs_memory",
        telemetry_base=telemetry_base,
        agent_platform="claude",
        model_name="sonnet-test",
    )
    record_event(
        repo,
        "session-context-session-start",
        source="session_context",
        telemetry_base=telemetry_base,
        agent_platform="claude",
        model_name="sonnet-test",
    )
    record_event(
        repo,
        "pre-compact",
        source="repo_specs_memory",
        telemetry_base=telemetry_base,
        agent_platform="claude",
        model_name="sonnet-test",
    )

    events = [
        json.loads(line)
        for line in first_path.read_text(encoding="utf-8").splitlines()
    ]
    session_ids = {event["agent_session_id"] for event in events}

    assert len(session_ids) == 1


def test_measure_impact_aggregates_agent_model_comparison() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo_contract(repo)
    telemetry_base = tmp_path / "telemetry"
    record_event(
        repo,
        "session-start",
        telemetry_base=telemetry_base,
        agent_platform="claude",
        model_name="sonnet-test",
    )
    record_event(
        repo,
        "pre-compact",
        telemetry_base=telemetry_base,
        agent_platform="claude",
        model_name="sonnet-test",
    )
    record_event(
        repo,
        "session-start",
        telemetry_base=telemetry_base,
        agent_platform="codex",
        model_name="gpt-test",
    )

    report = measure_impact(repo, telemetry_base=telemetry_base)
    comparison = report.to_dict()["agent_comparison"]
    sessions = report.to_dict()["agent_sessions"]

    assert comparison[0]["agent_platform"] == "claude"
    assert comparison[0]["model_name"] == "sonnet-test"
    assert comparison[0]["events"] == 2
    assert comparison[0]["sessions"] == 1
    assert comparison[0]["latest_score"] == report.current_score
    assert comparison[0]["baseline"] == report.estimated_baseline_score
    assert comparison[0]["uplift"] == report.uplift
    assert comparison[1]["agent_platform"] == "codex"
    assert comparison[1]["model_name"] == "gpt-test"
    assert comparison[1]["events"] == 1
    assert comparison[1]["sessions"] == 1
    assert sessions[0]["agent_session_id"]
    assert sessions[0]["events"] == 2
    assert sessions[0]["agent_platform"] == "claude"


def test_measure_impact_compares_current_state_to_no_contract_baseline() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo_contract(repo)
    telemetry_base = tmp_path / "telemetry"
    record_event(repo, "session-start", telemetry_base=telemetry_base)
    record_event(repo, "pre-compact", telemetry_base=telemetry_base)

    report = measure_impact(repo, telemetry_base=telemetry_base)

    assert report.current_score > report.estimated_baseline_score
    assert report.uplift > 0
    assert report.observed_events == 2
    assert report.event_counts["session-start"] == 1
    assert report.event_counts["pre-compact"] == 1
    assert report.history.latest_score > 0
    assert report.history.score_delta >= 0
    assert report.history.daily_event_counts
    assert report.history.score_series
    assert report.usability.active_days == 1
    assert report.usability.resume_events == 1
    assert report.usability.checkpoint_events == 1
    assert report.usability.lifecycle_coverage >= 50
    assert report.dashboard_path.exists()
    assert "Continuity Impact Monitor" in report.dashboard_path.read_text(encoding="utf-8")
    assert "Usability time series" in report.dashboard_path.read_text(encoding="utf-8")
    assert "context-impact" in report.render()
    assert "Monitoring view" in report.render()
    assert "Estimated baseline" in report.render()
    assert report.to_dict()["uplift"] == report.uplift
    assert report.to_dict()["history"]["latest_score"] == report.history.latest_score
    assert report.to_dict()["usability"]["active_days"] == 1
    assert report.to_dict()["dashboard_path"] == str(report.dashboard_path)


def test_measure_impact_recommends_install_when_no_hooks_are_observed() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo_contract(repo)

    report = measure_impact(repo, telemetry_base=tmp_path / "telemetry")

    assert report.observed_events == 0
    assert any("install --platform claude" in item for item in report.recommendations)
    assert telemetry_dir(repo, base=tmp_path / "telemetry").exists()


def test_measure_impact_uses_remote_name_for_worktree_display(monkeypatch) -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "feat-evidence-monitoring"
    repo.mkdir()
    init_repo_contract(repo)

    monkeypatch.setattr(
        "repo_context_hooks.telemetry._git_output",
        lambda repo_root, *args: (
            str(repo)
            if args == ("rev-parse", "--show-toplevel")
            else "https://github.com/narendranathe/repo-context-hooks.git"
            if args == ("remote", "get-url", "origin")
            else ""
        ),
    )

    report = measure_impact(repo, telemetry_base=tmp_path / "telemetry")

    assert report.repo_name == "repo-context-hooks"


def test_record_event_uses_remote_name_for_worktree_display(monkeypatch) -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "feat-observability-proof-strip"
    repo.mkdir()
    init_repo_contract(repo)

    monkeypatch.setattr(
        "repo_context_hooks.telemetry._git_output",
        lambda repo_root, *args: (
            str(repo)
            if args == ("rev-parse", "--show-toplevel")
            else "https://github.com/narendranathe/repo-context-hooks.git"
            if args == ("remote", "get-url", "origin")
            else "feature-branch"
            if args == ("branch", "--show-current")
            else ""
        ),
    )

    event_path = record_event(
        repo,
        "session-start",
        telemetry_base=tmp_path / "telemetry",
    )
    payload = json.loads(event_path.read_text(encoding="utf-8").splitlines()[0])

    assert payload["repo_name"] == "repo-context-hooks"


def test_telemetry_falls_back_to_repo_local_directory_when_cache_is_unavailable(monkeypatch) -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    blocked_cache = tmp_path / "blocked-cache"
    blocked_cache.write_text("not a directory", encoding="utf-8")

    monkeypatch.setattr(
        "repo_context_hooks.telemetry._default_telemetry_base",
        lambda: blocked_cache,
    )

    path = telemetry_dir(repo)

    assert repo in path.parents
    assert ".repo-context-hooks" in path.as_posix()


def test_write_public_monitoring_snapshot_sanitizes_local_paths() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo_contract(repo)
    telemetry_base = tmp_path / "telemetry"
    record_event(repo, "session-start", telemetry_base=telemetry_base)
    record_event(repo, "pre-compact", telemetry_base=telemetry_base)

    report = measure_impact(repo, telemetry_base=telemetry_base)
    snapshot_dir = tmp_path / "public" / "monitoring"

    result = write_public_monitoring_snapshot(report, snapshot_dir)

    assert result["dashboard_path"] == str(snapshot_dir / "index.html")
    assert result["history_path"] == str(snapshot_dir / "history.json")
    assert result["time_series_svg_path"] == str(snapshot_dir / "timeseries.svg")

    history = json.loads((snapshot_dir / "history.json").read_text(encoding="utf-8"))
    dashboard = (snapshot_dir / "index.html").read_text(encoding="utf-8")
    chart = (snapshot_dir / "timeseries.svg").read_text(encoding="utf-8")

    assert history["score"] == report.current_score
    assert history["observed_events"] == report.observed_events
    assert history["agent_comparison"][0]["agent_platform"]
    assert history["agent_comparison"][0]["sessions"] >= 1
    assert history["agent_sessions"][0]["agent_session_id"]
    assert history["usability"]["active_days"] == 1
    assert "Continuity Impact Monitor" in dashboard
    assert "Public snapshot" in dashboard
    assert "Telemetry time series" in chart
    assert "Generated from docs/monitoring/history.json" in chart
    assert "session-start" in chart
    assert "pre-compact" in chart
    assert "MODEL/SESSION ONLY" in chart
    assert "REPO CONTINUITY" in chart
    assert "Metric sources" in chart
    assert "Agent/model comparison" in chart
    assert "Agent sessions" in chart
    assert "agent_comparison" in chart
    assert str(tmp_path) not in dashboard
    assert str(tmp_path) not in json.dumps(history)
    assert str(tmp_path) not in chart


def test_render_public_time_series_svg_uses_snapshot_data_not_manual_claims() -> None:
    snapshot = {
        "repo": "demo",
        "score": 90,
        "baseline": 20,
        "uplift": 70,
        "observed_events": 32,
        "time_series": [
            {"date": "2026-04-24", "events": 30, "score": 90},
            {"date": "2026-04-25", "events": 2, "score": 90},
        ],
        "event_counts": {
            "session-start": 28,
            "pre-compact": 1,
            "post-compact": 1,
            "session-end": 1,
        },
        "agent_comparison": [
            {
                "agent_platform": "claude",
                "model_name": "sonnet-test",
                "events": 30,
                "sessions": 2,
                "latest_score": 90,
                "baseline": 20,
                "uplift": 70,
                "lifecycle_coverage": 100,
            },
            {
                "agent_platform": "codex",
                "model_name": "gpt-test",
                "events": 2,
                "sessions": 1,
                "latest_score": 90,
                "baseline": 20,
                "uplift": 70,
                "lifecycle_coverage": 25,
            },
        ],
        "agent_sessions": [
            {
                "agent_session_id": "claude-session",
                "agent_platform": "claude",
                "model_name": "sonnet-test",
                "events": 30,
                "latest_score": 90,
                "lifecycle_coverage": 100,
            },
            {
                "agent_session_id": "codex-session",
                "agent_platform": "codex",
                "model_name": "gpt-test",
                "events": 2,
                "latest_score": 90,
                "lifecycle_coverage": 25,
            },
        ],
        "usability": {
            "active_days": 2,
            "lifecycle_coverage": 100,
            "resume_events": 28,
            "checkpoint_events": 2,
            "reload_events": 1,
            "session_end_events": 1,
        },
    }

    chart = render_public_time_series_svg(snapshot)

    assert "Telemetry time series" in chart
    assert "Generated from docs/monitoring/history.json" in chart
    assert "2026-04-24" in chart
    assert "30 events" in chart
    assert "2026-04-25" in chart
    assert "2 events" in chart
    assert "Previous: 2026-04-24" in chart
    assert "Latest: 2026-04-25" in chart
    assert "Model/session only" in chart
    assert "Measured repo: demo" in chart
    assert "Per-repo snapshot" in chart
    assert "Repo continuity" in chart
    assert "Metric sources" in chart
    assert "Readiness(score/baseline/uplift)" in chart
    assert "Trend(time_series/event_counts)" in chart
    assert "Agent/model comparison" in chart
    assert "Agent sessions" in chart
    assert "claude / sonnet-test" in chart
    assert "codex / gpt-test" in chart
    assert "agent_comparison" in chart
    assert "2 sessions" in chart
    assert "session-start" in chart
    assert "28" in chart
    assert "manual proof card" not in chart.lower()


def test_render_prometheus_metrics_exports_safe_aggregate_evidence() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo_contract(repo)
    telemetry_base = tmp_path / "telemetry"
    record_event(repo, "session-start", telemetry_base=telemetry_base)
    record_event(repo, "pre-compact", telemetry_base=telemetry_base)

    report = measure_impact(repo, telemetry_base=telemetry_base)
    metrics = render_prometheus_metrics(report)

    assert "# HELP repo_context_hooks_continuity_score" in metrics
    assert "# TYPE repo_context_hooks_continuity_score gauge" in metrics
    assert f'repo_context_hooks_continuity_score{{repo="{report.repo_name}"}}' in metrics
    assert f'repo_context_hooks_uplift{{repo="{report.repo_name}"}}' in metrics
    assert f'repo_context_hooks_observed_events_total{{repo="{report.repo_name}"}} 2' in metrics
    assert f'repo_context_hooks_lifecycle_coverage_percent{{repo="{report.repo_name}"}}' in metrics
    assert "repo_context_hooks_agent_events_total" in metrics
    assert "repo_context_hooks_agent_sessions_total" in metrics
    assert (
        f'repo_context_hooks_event_count{{repo="{report.repo_name}",event_name="session-start"}} 1'
        in metrics
    )
    assert (
        f'repo_context_hooks_event_count{{repo="{report.repo_name}",event_name="pre-compact"}} 1'
        in metrics
    )
    assert str(tmp_path) not in metrics
    assert "telemetry_path" not in metrics


def test_record_context_window_records_threshold_and_checkpoint_event() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo_contract(repo)
    telemetry_base = tmp_path / "telemetry"

    event_path = record_context_window(
        repo,
        used_tokens=99_000,
        limit_tokens=100_000,
        threshold_percent=99,
        checkpoint=True,
        telemetry_base=telemetry_base,
        source="vscode-extension",
        agent_platform="codex",
        model_name="gpt-test",
    )

    events = [
        json.loads(line)
        for line in event_path.read_text(encoding="utf-8").splitlines()
    ]
    names = [event["event_name"] for event in events]
    threshold_event = events[0]
    checkpoint_event = events[1]

    assert names == ["context-window-threshold", "pre-compact"]
    assert threshold_event["agent_platform"] == "codex"
    assert threshold_event["model_name"] == "gpt-test"
    assert threshold_event["details"]["used_tokens"] == 99_000
    assert threshold_event["details"]["limit_tokens"] == 100_000
    assert threshold_event["details"]["usage_percent"] == 99.0
    assert threshold_event["details"]["remaining_percent"] == 1.0
    assert threshold_event["details"]["threshold_percent"] == 99.0
    assert threshold_event["details"]["threshold_window_percent"] == 1.0
    assert checkpoint_event["details"]["checkpoint_trigger"] == "context-window-threshold"


def test_measure_rollup_aggregates_multiple_repo_event_logs() -> None:
    tmp_path = _tmp_dir()
    telemetry_base = tmp_path / "telemetry"
    repo_a = tmp_path / "portfolio"
    repo_b = tmp_path / "tailor-resume"
    repo_a.mkdir()
    repo_b.mkdir()
    init_repo_contract(repo_a)
    init_repo_contract(repo_b)

    record_event(
        repo_a,
        "session-start",
        telemetry_base=telemetry_base,
        agent_platform="claude",
        model_name="sonnet-test",
    )
    record_context_window(
        repo_a,
        used_tokens=99_500,
        limit_tokens=100_000,
        threshold_percent=99,
        checkpoint=True,
        telemetry_base=telemetry_base,
        agent_platform="claude",
        model_name="sonnet-test",
    )
    record_event(
        repo_b,
        "session-start",
        telemetry_base=telemetry_base,
        agent_platform="codex",
        model_name="gpt-test",
    )

    report = measure_rollup(telemetry_base=telemetry_base)
    payload = report.to_dict()

    assert payload["repo_count"] == 2
    assert payload["total_events"] == 4
    assert payload["total_agent_sessions"] == 2
    assert payload["context_threshold_events"] == 1
    assert payload["checkpoint_events"] == 1
    assert payload["repos"][0]["repo_name"] == "portfolio"
    assert payload["repos"][0]["context_threshold_events"] == 1
    assert payload["repos"][0]["max_context_usage_percent"] == 99.5
    assert {item["repo_name"] for item in payload["repos"]} == {
        "portfolio",
        "tailor-resume",
    }
    assert "portfolio" in report.render()
    assert "cross-repo telemetry rollup" in report.render()

    metrics = render_rollup_prometheus_metrics(report)
    assert "repo_context_hooks_rollup_repos_total 2" in metrics
    assert "repo_context_hooks_rollup_context_threshold_events_total 1" in metrics
    assert 'repo_context_hooks_repo_events_total{repo="portfolio"} 3' in metrics


def test_measure_rollup_scans_projects_root_fallback_telemetry() -> None:
    tmp_path = _tmp_dir()
    projects_root = tmp_path / "projects"
    repo_a = projects_root / "portfolio"
    repo_b = projects_root / "tailor-resume"
    repo_a.mkdir(parents=True)
    repo_b.mkdir(parents=True)
    init_repo_contract(repo_a)
    init_repo_contract(repo_b)

    record_event(
        repo_a,
        "session-start",
        telemetry_base=repo_a / ".repo-context-hooks" / "telemetry",
        agent_platform="claude",
    )
    record_event(
        repo_b,
        "session-start",
        telemetry_base=repo_b / ".repo-context-hooks" / "telemetry",
        agent_platform="codex",
    )

    report = measure_rollup(
        telemetry_base=tmp_path / "empty-shared-telemetry",
        projects_root=projects_root,
    )
    payload = report.to_dict()

    assert payload["repo_count"] == 2
    assert payload["total_events"] == 2
    assert {item["repo_name"] for item in payload["repos"]} == {
        "portfolio",
        "tailor-resume",
    }


def test_write_public_rollup_snapshot_sanitizes_paths() -> None:
    tmp_path = _tmp_dir()
    telemetry_base = tmp_path / "telemetry"
    repo = tmp_path / "portfolio"
    repo.mkdir()
    init_repo_contract(repo)
    record_event(repo, "session-start", telemetry_base=telemetry_base)

    report = measure_rollup(telemetry_base=telemetry_base)
    output_dir = tmp_path / "public" / "rollup"

    result = write_public_rollup_snapshot(report, output_dir)

    assert result["dashboard_path"] == str(output_dir / "index.html")
    assert result["history_path"] == str(output_dir / "rollup.json")
    dashboard = (output_dir / "index.html").read_text(encoding="utf-8")
    history = json.loads((output_dir / "rollup.json").read_text(encoding="utf-8"))

    assert "Cross-Repo Telemetry Rollup" in dashboard
    assert history["repo_count"] == 1
    assert history["repos"][0]["repo_name"] == "portfolio"
    assert str(tmp_path) not in dashboard
    assert str(tmp_path) not in json.dumps(history)
