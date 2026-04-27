"""Tests for ROI metrics: cold_start_time_saved_minutes and score_week1_uplift."""
import datetime as dt
from repo_context_hooks.telemetry import _build_usability, ImpactHistory


def _make_history(score_series=None, daily_event_counts=None):
    now = dt.datetime.now(dt.timezone.utc)
    score_series = score_series or [{"date": now.strftime("%Y-%m-%d"), "score": 60}]
    daily = daily_event_counts or [{"date": now.strftime("%Y-%m-%d"), "events": 3}]
    return ImpactHistory(
        first_seen=(now - dt.timedelta(days=10)).isoformat(),
        latest_seen=now.isoformat(),
        latest_score=score_series[-1]["score"],
        min_score=min(s["score"] for s in score_series),
        max_score=max(s["score"] for s in score_series),
        score_delta=score_series[-1]["score"] - score_series[0]["score"],
        daily_event_counts=tuple(daily),
        score_series=tuple(score_series),
        recent_events=(),
    )


def test_cold_start_time_saved_is_reload_events_times_5():
    events = [
        {"event_name": "session-start", "timestamp": "2026-04-20T10:00:00+00:00", "repo_contract_score": 60},
        {"event_name": "post-compact", "timestamp": "2026-04-20T10:30:00+00:00", "repo_contract_score": 60},
        {"event_name": "post-compact", "timestamp": "2026-04-21T09:00:00+00:00", "repo_contract_score": 65},
    ]
    history = _make_history()
    metrics = _build_usability(events, history)
    assert metrics.cold_start_time_saved_minutes == 10  # 2 reloads * 5 min


def test_cold_start_zero_when_no_reloads():
    events = [
        {"event_name": "session-start", "timestamp": "2026-04-20T10:00:00+00:00", "repo_contract_score": 60},
    ]
    history = _make_history()
    metrics = _build_usability(events, history)
    assert metrics.cold_start_time_saved_minutes == 0


def test_score_week1_uplift_computes_correctly():
    base = dt.date(2026, 4, 10)
    score_series = [
        {"date": (base + dt.timedelta(days=i)).isoformat(), "score": 40 + i * 5}
        for i in range(14)
    ]
    history = _make_history(score_series=score_series)
    events = [
        {
            "event_name": "session-start",
            "timestamp": f"{s['date']}T10:00:00+00:00",
            "repo_contract_score": s["score"],
        }
        for s in score_series
    ]
    metrics = _build_usability(events, history)
    # day 0 = score 40, day 7 = score 40 + 7*5 = 75, uplift = 35
    assert metrics.score_week1_uplift == 35


def test_score_week1_uplift_none_when_fewer_than_2_days():
    score_series = [{"date": "2026-04-20", "score": 60}]
    history = _make_history(score_series=score_series)
    events = [
        {"event_name": "session-start", "timestamp": "2026-04-20T10:00:00+00:00", "repo_contract_score": 60}
    ]
    metrics = _build_usability(events, history)
    assert metrics.score_week1_uplift is None


def test_score_week1_uplift_none_when_no_day7_data():
    """If there are only 3 days of data (all within week 1), uplift is None."""
    base = dt.date(2026, 4, 10)
    score_series = [
        {"date": (base + dt.timedelta(days=i)).isoformat(), "score": 50 + i * 3}
        for i in range(3)  # days 0, 1, 2 — no day 7
    ]
    history = _make_history(score_series=score_series)
    events = [
        {
            "event_name": "session-start",
            "timestamp": f"{s['date']}T10:00:00+00:00",
            "repo_contract_score": s["score"],
        }
        for s in score_series
    ]
    metrics = _build_usability(events, history)
    assert metrics.score_week1_uplift is None


def test_roi_metrics_in_to_dict():
    """Both new fields must appear in to_dict() output."""
    events = [
        {"event_name": "session-start", "timestamp": "2026-04-20T10:00:00+00:00", "repo_contract_score": 60},
        {"event_name": "post-compact", "timestamp": "2026-04-20T10:30:00+00:00", "repo_contract_score": 60},
    ]
    history = _make_history()
    d = _build_usability(events, history).to_dict()
    assert "cold_start_time_saved_minutes" in d
    assert "score_week1_uplift" in d
