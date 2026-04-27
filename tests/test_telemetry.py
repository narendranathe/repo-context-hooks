from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from repo_context_hooks.repo_contract import init_repo_contract
from repo_context_hooks.telemetry import (
    measure_impact,
    record_event,
    telemetry_dir,
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
    assert payload["repo_name"] == "repo"
    assert payload["repo_id"]
    assert payload["repo_contract_score"] > 0
    assert payload["details"]["context_bytes"] == 123
    # monitoring.html is no longer generated inline by record_event;
    # it is only produced when the `measure` CLI is explicitly called.
    assert not (event_path.parent / "monitoring.html").exists()


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
            "https://github.com/narendranathe/repo-context-hooks.git"
            if args == ("remote", "get-url", "origin")
            else ""
        ),
    )

    report = measure_impact(repo, telemetry_base=tmp_path / "telemetry")

    assert report.repo_name == "repo-context-hooks"


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

    history = json.loads((snapshot_dir / "history.json").read_text(encoding="utf-8"))
    dashboard = (snapshot_dir / "index.html").read_text(encoding="utf-8")

    assert history["score"] == report.current_score
    assert history["observed_events"] == report.observed_events
    assert history["usability"]["active_days"] == 1
    assert "Continuity Impact Monitor" in dashboard
    assert "Public snapshot" in dashboard
    assert str(tmp_path) not in dashboard
    assert str(tmp_path) not in json.dumps(history)


# --- purge_ghost_repos tests ---

def test_purge_ghost_repos_dry_run_does_not_delete(tmp_path):
    from repo_context_hooks.telemetry import purge_ghost_repos, EVENTS_FILE
    ghost = tmp_path / "ghost-id"
    ghost.mkdir()
    (ghost / EVENTS_FILE).write_text(
        '{"event_name":"session-start","repo_name":"repo"}\n', encoding="utf-8"
    )
    result = purge_ghost_repos(telemetry_base=tmp_path, dry_run=True)
    assert result["removed"] == 1
    assert ghost.exists(), "dry_run must not delete"


def test_purge_ghost_repos_deletes_on_confirm(tmp_path):
    from repo_context_hooks.telemetry import purge_ghost_repos, EVENTS_FILE
    ghost = tmp_path / "ghost-id"
    ghost.mkdir()
    (ghost / EVENTS_FILE).write_text(
        '{"event_name":"session-start","repo_name":"repo"}\n', encoding="utf-8"
    )
    result = purge_ghost_repos(telemetry_base=tmp_path, dry_run=False)
    assert result["removed"] == 1
    assert not ghost.exists()


def test_purge_ghost_repos_keeps_two_event_repos(tmp_path):
    from repo_context_hooks.telemetry import purge_ghost_repos, EVENTS_FILE
    legit = tmp_path / "legit-id"
    legit.mkdir()
    (legit / EVENTS_FILE).write_text(
        '{"event_name":"session-start","repo_name":"repo"}\n'
        '{"event_name":"session-end","repo_name":"repo"}\n',
        encoding="utf-8",
    )
    result = purge_ghost_repos(telemetry_base=tmp_path, dry_run=False)
    assert result["removed"] == 0
    assert legit.exists()


def test_purge_ghost_repos_keeps_non_ghost_names(tmp_path):
    from repo_context_hooks.telemetry import purge_ghost_repos, EVENTS_FILE
    real_repo = tmp_path / "real-id"
    real_repo.mkdir()
    (real_repo / EVENTS_FILE).write_text(
        '{"event_name":"session-start","repo_name":"autoapply-ai"}\n', encoding="utf-8"
    )
    result = purge_ghost_repos(telemetry_base=tmp_path, dry_run=False)
    assert result["removed"] == 0
    assert real_repo.exists()


# --- forecast_activity tests ---

def test_forecast_empty_telemetry(tmp_path):
    from repo_context_hooks.telemetry import forecast_activity
    f = forecast_activity(tmp_path, telemetry_base=tmp_path / "telem")
    assert f.daily_rate == 0.0
    assert f.projected_events == 0
    assert f.confidence == "low"


def test_forecast_known_event_rate(tmp_path, monkeypatch):
    import datetime, json
    from repo_context_hooks.telemetry import forecast_activity, EVENTS_FILE, telemetry_events_path

    telem_base = tmp_path / "telem"
    events_file = telemetry_events_path(tmp_path, base=telem_base)
    # 7 events on 7 distinct days = rate of 1/day
    lines = []
    for i in range(7):
        day = (datetime.date(2026, 1, 1) + datetime.timedelta(days=i)).isoformat()
        event = {"event_name": "session-start", "timestamp": f"{day}T12:00:00+00:00"}
        lines.append(json.dumps(event))
    events_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    f = forecast_activity(tmp_path, telemetry_base=telem_base)
    assert f.confidence == "high"
    assert f.daily_rate == 1.0
    assert f.projected_events == 30


def test_forecast_to_dict_has_required_keys(tmp_path):
    from repo_context_hooks.telemetry import forecast_activity
    f = forecast_activity(tmp_path, telemetry_base=tmp_path / "telem")
    d = f.to_dict()
    assert set(d) >= {"daily_rate", "projected_events", "projected_active_days", "confidence", "week_series"}


# --- branch_scores tests ---

def test_branch_scores_groups_by_branch(tmp_path):
    import json
    from repo_context_hooks.telemetry import branch_scores, EVENTS_FILE, telemetry_events_path

    telem_base = tmp_path / "telem"
    events_file = telemetry_events_path(tmp_path, base=telem_base)
    events = [
        {"branch": "main", "session_id": "s1", "repo_contract_score": 80, "timestamp": "2026-01-01T00:00:00+00:00"},
        {"branch": "main", "session_id": "s2", "repo_contract_score": 90, "timestamp": "2026-01-02T00:00:00+00:00"},
        {"branch": "feature", "session_id": "s3", "repo_contract_score": 70, "timestamp": "2026-01-03T00:00:00+00:00"},
    ]
    events_file.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")

    stats = branch_scores(tmp_path, telemetry_base=telem_base)
    by_branch = {s.branch: s for s in stats}

    assert "main" in by_branch
    assert "feature" in by_branch
    assert by_branch["main"].session_count == 2
    assert by_branch["main"].avg_score == 85
    assert by_branch["feature"].session_count == 1
    assert by_branch["feature"].avg_score == 70


def test_branch_scores_sorted_by_last_seen(tmp_path):
    import json
    from repo_context_hooks.telemetry import branch_scores, telemetry_events_path

    telem_base = tmp_path / "telem"
    events_file = telemetry_events_path(tmp_path, base=telem_base)
    events = [
        {"branch": "older", "session_id": "s1", "repo_contract_score": 90, "timestamp": "2026-01-01T00:00:00+00:00"},
        {"branch": "newer", "session_id": "s2", "repo_contract_score": 90, "timestamp": "2026-01-10T00:00:00+00:00"},
    ]
    events_file.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")

    stats = branch_scores(tmp_path, telemetry_base=telem_base)
    assert stats[0].branch == "newer"
    assert stats[1].branch == "older"


def test_branch_scores_empty_returns_empty_list(tmp_path):
    from repo_context_hooks.telemetry import branch_scores
    stats = branch_scores(tmp_path, telemetry_base=tmp_path / "telem")
    assert stats == []
