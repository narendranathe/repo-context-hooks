from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import os
import random
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EVENTS_FILE = "events.jsonl"
_SESSION_ID_FILE = "current-session-id"
_SESSION_SAMPLED_FILE = "current-session-sampled"
_SESSION_START_TS_FILE = "current-session-start-ts"
_SESSION_STATE_DIR = ".repo-context-hooks"


def _git_output(repo_root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _default_telemetry_base() -> Path:
    configured = os.environ.get("REPO_CONTEXT_HOOKS_TELEMETRY_DIR")
    if configured:
        return Path(configured)

    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "repo-context-hooks" / "telemetry"
        return Path.home() / "AppData" / "Local" / "repo-context-hooks" / "telemetry"

    cache_home = os.environ.get("XDG_CACHE_HOME")
    if cache_home:
        return Path(cache_home) / "repo-context-hooks" / "telemetry"
    return Path.home() / ".cache" / "repo-context-hooks" / "telemetry"


def repo_id(repo_root: Path) -> str:
    resolved = str(repo_root.resolve())
    return hashlib.sha256(resolved.encode("utf-8")).hexdigest()[:16]


def _repo_local_telemetry_base(repo_root: Path) -> Path:
    return repo_root / ".repo-context-hooks" / "telemetry"


def telemetry_dir(repo_root: Path, base: Path | None = None) -> Path:
    repo_root = repo_root.resolve()
    candidates = [base] if base is not None else [
        _default_telemetry_base(),
        _repo_local_telemetry_base(repo_root),
    ]

    last_error: OSError | None = None
    for root in candidates:
        if root is None:
            continue
        path = root / repo_id(repo_root)
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path
        except OSError as exc:
            last_error = exc

    if last_error is not None:
        raise last_error
    raise OSError("Unable to create telemetry directory")


def telemetry_events_path(repo_root: Path, base: Path | None = None) -> Path:
    return telemetry_dir(repo_root, base=base) / EVENTS_FILE


def _canonical_repo_root(repo_root: Path) -> str:
    """Return the main worktree root so all worktrees share one session state dir."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--git-common-dir"],
            capture_output=True, text=True, check=True,
        )
        common = Path(result.stdout.strip())
        if common.name == ".git":
            return str(common.parent.resolve())
    except Exception:
        pass
    return str(repo_root.resolve())


def _session_state_dir(repo_root: Path) -> Path:
    """Session state in OS temp dir, keyed by canonical repo root — survives git clean."""
    canonical = _canonical_repo_root(repo_root)
    key = hashlib.sha1(canonical.encode()).hexdigest()[:12]
    path = Path(tempfile.gettempdir()) / f"rch-session-{key}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def session_id(repo_root: Path) -> str:
    override = os.environ.get("REPO_CONTEXT_HOOKS_SESSION_ID")
    if override:
        return override

    state_dir = _session_state_dir(repo_root)
    id_file = state_dir / _SESSION_ID_FILE

    if id_file.exists():
        stored = id_file.read_text(encoding="utf-8").strip()
        if stored:
            return stored

    new_id = str(uuid.uuid4())
    id_file.write_text(new_id, encoding="utf-8")
    return new_id


def is_sampled(repo_root: Path, rate: float = 1.0) -> bool:
    # Hard override: env var bypasses all file state and random logic
    explicit = os.environ.get("REPO_CONTEXT_HOOKS_TELEMETRY")
    if explicit is not None:
        return explicit.lower() in ("1", "true", "yes")

    # Apply REPO_CONTEXT_HOOKS_SAMPLE_RATE env var before deterministic shortcuts so
    # the env-var rate is honoured even when no explicit rate= argument is passed.
    rate_str = os.environ.get("REPO_CONTEXT_HOOKS_SAMPLE_RATE")
    if rate_str is not None:
        try:
            rate = float(rate_str)
        except ValueError:
            pass

    # Deterministic rates bypass the file cache to avoid stale-false poisoning the
    # session.  We still write the canonical value so clear_session_state() and
    # duration tracking keep working, but we never *read* an old cached value.
    state_dir = _session_state_dir(repo_root)
    sampled_file = state_dir / _SESSION_SAMPLED_FILE

    if rate >= 1.0:
        sampled_file.write_text("true", encoding="utf-8")
        return True
    if rate <= 0.0:
        sampled_file.write_text("false", encoding="utf-8")
        return False

    if sampled_file.exists():
        age = time.time() - sampled_file.stat().st_mtime
        if age <= 8 * 3600:
            return sampled_file.read_text(encoding="utf-8").strip() == "true"
        # Stale state from a killed session — re-roll
        try:
            sampled_file.unlink()
        except OSError:
            pass

    decision = random.random() < rate
    sampled_file.write_text("true" if decision else "false", encoding="utf-8")
    return decision


def record_session_start_time(repo_root: Path) -> None:
    """Write an ISO timestamp to state dir so session-end can compute duration."""
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    (_session_state_dir(repo_root) / _SESSION_START_TS_FILE).write_text(ts, encoding="utf-8")


def read_session_duration_minutes(repo_root: Path) -> int | None:
    """Return elapsed minutes since session-start, or None if no start timestamp found."""
    ts_file = _session_state_dir(repo_root) / _SESSION_START_TS_FILE
    if not ts_file.exists():
        return None
    try:
        raw = ts_file.read_text(encoding="utf-8").strip()
        start = dt.datetime.fromisoformat(raw)
        if start.tzinfo is None:
            start = start.replace(tzinfo=dt.timezone.utc)
        delta = dt.datetime.now(dt.timezone.utc) - start
        return max(0, round(delta.total_seconds() / 60))
    except Exception:
        return None


def clear_session_state(repo_root: Path) -> None:
    state_dir = _session_state_dir(repo_root)
    for name in (_SESSION_ID_FILE, _SESSION_SAMPLED_FILE, _SESSION_START_TS_FILE):
        f = state_dir / name
        if f.exists():
            try:
                f.unlink()
            except OSError:
                pass


def _repo_display_name(repo_root: Path) -> str:
    remote = _git_output(repo_root, "remote", "get-url", "origin")
    if remote:
        name = remote.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        if name:
            return name
    return repo_root.name


def _file_size(path: Path) -> int:
    if not path.exists() or not path.is_file():
        return 0
    try:
        return path.stat().st_size
    except OSError:
        return 0


def contract_signals(repo_root: Path) -> dict[str, Any]:
    docs = {
        "README.md": repo_root / "README.md",
        "specs/README.md": repo_root / "specs" / "README.md",
        "UBIQUITOUS_LANGUAGE.md": repo_root / "UBIQUITOUS_LANGUAGE.md",
        "AGENTS.md": repo_root / "AGENTS.md",
        "CLAUDE.md": repo_root / "CLAUDE.md",
        ".claude/settings.json": repo_root / ".claude" / "settings.json",
    }
    present = {name: path.exists() for name, path in docs.items()}
    sizes = {name: _file_size(path) for name, path in docs.items()}

    specs_text = ""
    specs_path = docs["specs/README.md"]
    if specs_path.exists():
        specs_text = specs_path.read_text(encoding="utf-8", errors="ignore")

    required_sections = (
        "## Repo Context Index",
        "## Architecture and Design Constraints",
        "## Open Issues and Next Work",
        "## How To Work in This Repo",
        "## Session Checkpoints",
    )
    specs_sections = {
        section: section in specs_text for section in required_sections
    }

    hook_text = ""
    settings_path = docs[".claude/settings.json"]
    if settings_path.exists():
        hook_text = settings_path.read_text(encoding="utf-8", errors="ignore")
    hook_events = {
        event: event in hook_text
        for event in ("SessionStart", "PreCompact", "PostCompact", "SessionEnd")
    }

    score = 0
    score += 20 if present["README.md"] else 0
    score += 20 if present["specs/README.md"] else 0
    score += 20 if all(specs_sections.values()) else 0
    score += 10 if present["UBIQUITOUS_LANGUAGE.md"] else 0
    score += 10 if present["AGENTS.md"] else 0
    score += 10 if present["CLAUDE.md"] else 0
    score += 10 if all(hook_events.values()) else 0

    baseline = 20 if present["README.md"] else 0

    return {
        "present": present,
        "sizes": sizes,
        "specs_sections": specs_sections,
        "hook_events": hook_events,
        "score": score,
        "estimated_baseline_score": baseline,
    }


def record_event(
    repo_root: Path,
    event_name: str,
    *,
    source: str = "repo-context-hooks",
    telemetry_base: Path | None = None,
    details: dict[str, Any] | None = None,
    skip_dashboard: bool = False,
    duration_minutes: int | None = None,
) -> Path:
    repo_root = repo_root.resolve()
    signals = contract_signals(repo_root)
    sid = session_id(repo_root)
    event: dict[str, Any] = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "event_name": event_name,
        "session_id": sid,
        "source": source,
        "repo_id": repo_id(repo_root),
        "repo_name": repo_root.name,
        "branch": _git_output(repo_root, "branch", "--show-current") or "unknown",
        "repo_contract_score": signals["score"],
        "estimated_baseline_score": signals["estimated_baseline_score"],
        "details": details or {},
    }
    if duration_minutes is not None:
        event["duration_minutes"] = duration_minutes
    path = telemetry_events_path(repo_root, base=telemetry_base)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return path


def _read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


@dataclass(frozen=True)
class ImpactHistory:
    first_seen: str | None
    latest_seen: str | None
    latest_score: int
    min_score: int
    max_score: int
    score_delta: int
    daily_event_counts: tuple[dict[str, Any], ...]
    score_series: tuple[dict[str, Any], ...]
    recent_events: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "first_seen": self.first_seen,
            "latest_seen": self.latest_seen,
            "latest_score": self.latest_score,
            "min_score": self.min_score,
            "max_score": self.max_score,
            "score_delta": self.score_delta,
            "daily_event_counts": list(self.daily_event_counts),
            "score_series": list(self.score_series),
            "recent_events": list(self.recent_events),
        }


@dataclass(frozen=True)
class UsabilityMetrics:
    active_days: int
    resume_events: int
    checkpoint_events: int
    reload_events: int
    session_end_events: int
    lifecycle_coverage: int
    readiness_minutes_since_last_event: int | None
    avg_session_duration_minutes: int | None
    max_session_duration_minutes: int | None
    cold_start_time_saved_minutes: int
    score_week1_uplift: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_days": self.active_days,
            "resume_events": self.resume_events,
            "checkpoint_events": self.checkpoint_events,
            "reload_events": self.reload_events,
            "session_end_events": self.session_end_events,
            "lifecycle_coverage": self.lifecycle_coverage,
            "readiness_minutes_since_last_event": self.readiness_minutes_since_last_event,
            "avg_session_duration_minutes": self.avg_session_duration_minutes,
            "max_session_duration_minutes": self.max_session_duration_minutes,
            "cold_start_time_saved_minutes": self.cold_start_time_saved_minutes,
            "score_week1_uplift": self.score_week1_uplift,
        }


@dataclass(frozen=True)
class ImpactReport:
    repo_name: str
    repo_id: str
    telemetry_path: Path
    current_score: int
    estimated_baseline_score: int
    observed_events: int
    event_counts: dict[str, int]
    dashboard_path: Path
    history: ImpactHistory
    usability: UsabilityMetrics
    recommendations: tuple[str, ...]

    @property
    def uplift(self) -> int:
        return self.current_score - self.estimated_baseline_score

    def render(self) -> str:
        lines = [
            "[OK] context-impact",
            f"repo: {self.repo_name}",
            f"Current continuity score: {self.current_score}",
            f"Estimated baseline without repo continuity: {self.estimated_baseline_score}",
            f"Estimated uplift: +{self.uplift}",
            f"Observed hook/skill events: {self.observed_events}",
            f"Evidence log: {self.telemetry_path}",
            f"Monitoring view: {self.dashboard_path}",
        ]
        if self.history.latest_seen:
            lines.append(f"Latest observed score: {self.history.latest_score}")
            lines.append(f"Historical score delta: {self.history.score_delta:+d}")
            lines.append(f"Lifecycle coverage: {self.usability.lifecycle_coverage}%")
            lines.append(f"Active days: {self.usability.active_days}")
            if self.usability.avg_session_duration_minutes is not None:
                lines.append(f"Avg session duration: {self.usability.avg_session_duration_minutes} min")
            if self.usability.max_session_duration_minutes is not None:
                lines.append(f"Max session duration: {self.usability.max_session_duration_minutes} min")
        if self.event_counts:
            lines.append("Event counts:")
            lines.extend(
                f"- {name}: {count}"
                for name, count in sorted(self.event_counts.items())
            )
        if self.recommendations:
            lines.append("Recommendations:")
            lines.extend(f"- {item}" for item in self.recommendations)
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_name": self.repo_name,
            "repo_id": self.repo_id,
            "telemetry_path": str(self.telemetry_path),
            "current_score": self.current_score,
            "estimated_baseline_score": self.estimated_baseline_score,
            "uplift": self.uplift,
            "observed_events": self.observed_events,
            "event_counts": self.event_counts,
            "dashboard_path": str(self.dashboard_path),
            "history": self.history.to_dict(),
            "usability": self.usability.to_dict(),
            "recommendations": list(self.recommendations),
        }


def _recommendations(signals: dict[str, Any], events: list[dict[str, Any]]) -> tuple[str, ...]:
    items: list[str] = []
    present = signals["present"]
    hook_events = signals["hook_events"]

    if signals["score"] < 70:
        items.append("Run `repo-context-hooks init` and `repo-context-hooks doctor` to strengthen the repo contract.")
    if not present.get("AGENTS.md", False):
        items.append("Add `AGENTS.md` so Codex, Windsurf, Lovable, Kimi, and other repo-instruction agents can enter through the same contract.")
    if not all(hook_events.values()):
        items.append("Run `repo-context-hooks install --platform claude --repo-root .` to install native lifecycle hook evidence collection.")
    if not events:
        items.append("Run one new agent session after install, then rerun `repo-context-hooks measure` to compare observed evidence.")
    return tuple(items)


def _event_score(event: dict[str, Any]) -> int:
    try:
        return int(event.get("repo_contract_score", 0))
    except (TypeError, ValueError):
        return 0


def _build_history(events: list[dict[str, Any]]) -> ImpactHistory:
    if not events:
        return ImpactHistory(
            first_seen=None,
            latest_seen=None,
            latest_score=0,
            min_score=0,
            max_score=0,
            score_delta=0,
            daily_event_counts=(),
            score_series=(),
            recent_events=(),
        )

    scores = [_event_score(event) for event in events]
    first_score = scores[0]
    latest_score = scores[-1]

    daily: dict[str, int] = {}
    score_by_day: dict[str, int] = {}
    for event in events:
        timestamp = str(event.get("timestamp", "unknown"))
        day = timestamp[:10] if len(timestamp) >= 10 else "unknown"
        daily[day] = daily.get(day, 0) + 1
        score_by_day[day] = _event_score(event)

    recent = tuple(
        {
            "timestamp": str(event.get("timestamp", "")),
            "event_name": str(event.get("event_name", "unknown")),
            "source": str(event.get("source", "unknown")),
            "score": _event_score(event),
        }
        for event in events[-8:]
    )

    return ImpactHistory(
        first_seen=str(events[0].get("timestamp", "")),
        latest_seen=str(events[-1].get("timestamp", "")),
        latest_score=latest_score,
        min_score=min(scores),
        max_score=max(scores),
        score_delta=latest_score - first_score,
        daily_event_counts=tuple(
            {"date": day, "events": count}
            for day, count in sorted(daily.items())
        ),
        score_series=tuple(
            {"date": day, "score": score}
            for day, score in sorted(score_by_day.items())
        ),
        recent_events=recent,
    )


def _event_name(event: dict[str, Any]) -> str:
    return str(event.get("event_name", "unknown"))


def _parse_timestamp(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


def _build_usability(events: list[dict[str, Any]], history: ImpactHistory) -> UsabilityMetrics:
    names = [_event_name(event) for event in events]
    unique_lifecycle = {
        name
        for name in names
        if name in {"session-start", "pre-compact", "post-compact", "session-end"}
    }
    latest = _parse_timestamp(history.latest_seen)
    minutes_since_last = None
    if latest is not None:
        minutes_since_last = max(
            0,
            round(
                (dt.datetime.now(dt.timezone.utc) - latest).total_seconds() / 60
            ),
        )

    durations = [
        int(e["duration_minutes"])
        for e in events
        if _event_name(e) == "session-end" and isinstance(e.get("duration_minutes"), (int, float))
    ]
    avg_dur = round(sum(durations) / len(durations)) if durations else None
    max_dur = max(durations) if durations else None

    # cold start time saved: each post-compact reload prevents ~5 min cold re-orientation
    cold_start_saved = sum(1 for name in names if "post-compact" in name) * 5

    # week-1 score uplift: score at day 7 minus score at day 0 (None if no day-7 data)
    score_week1_uplift: int | None = None
    if len(history.score_series) >= 2:
        sorted_scores = sorted(history.score_series, key=lambda x: x["date"])
        day0_date = sorted_scores[0]["date"]
        day0_score = sorted_scores[0]["score"]
        try:
            day0 = dt.date.fromisoformat(day0_date)
            target = (day0 + dt.timedelta(days=7)).isoformat()
            candidates = [s for s in sorted_scores if s["date"] >= target]
            if candidates:
                score_week1_uplift = candidates[0]["score"] - day0_score
        except (ValueError, KeyError):
            pass

    return UsabilityMetrics(
        active_days=len(history.daily_event_counts),
        resume_events=sum(1 for name in names if "session-start" in name),
        checkpoint_events=sum(
            1 for name in names if name in {"pre-compact", "session-end"}
        ),
        reload_events=sum(1 for name in names if "post-compact" in name),
        session_end_events=sum(1 for name in names if name == "session-end"),
        lifecycle_coverage=round(len(unique_lifecycle) / 4 * 100),
        readiness_minutes_since_last_event=minutes_since_last,
        avg_session_duration_minutes=avg_dur,
        max_session_duration_minutes=max_dur,
        cold_start_time_saved_minutes=cold_start_saved,
        score_week1_uplift=score_week1_uplift,
    )


def _dashboard_path(events_path: Path) -> Path:
    return events_path.with_name("monitoring.html")


def _bar_width(value: int, maximum: int) -> int:
    if maximum <= 0:
        return 0
    return max(4, min(100, round(value / maximum * 100)))


def _contract_token_estimate(repo_root: Path) -> dict[str, Any]:
    """Estimate tokens from contract files; returns counts and per-session injection figure."""
    contract_files = ["specs/README.md", "UBIQUITOUS_LANGUAGE.md", "AGENTS.md", "README.md"]
    total_bytes = 0
    sections = 0
    files_present = []
    for name in contract_files:
        p = repo_root / name
        if p.exists():
            b = len(p.read_bytes())
            total_bytes += b
            files_present.append(name)
            if name == "specs/README.md":
                sections = sum(1 for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines() if ln.startswith("## "))
    tokens_per_session = total_bytes // 4  # ~4 chars per token
    return {
        "files": len(files_present),
        "sections": sections,
        "bytes": total_bytes,
        "tokens_per_session": tokens_per_session,
    }


def _lifecycle_donut_svg(coverage: int, r: int = 44) -> str:
    """SVG ring chart for lifecycle coverage (0-100%)."""
    cx = cy = 60
    stroke = 12
    circumference = round(2 * 3.14159 * r, 1)
    filled = round(circumference * coverage / 100, 1)
    gap = round(circumference - filled, 1)
    color = "#356857" if coverage >= 75 else "#e6a92f" if coverage >= 25 else "#b54720"
    return (
        f'<svg viewBox="0 0 120 120" width="120" height="120" style="display:block;margin:auto">'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(16,24,32,.1)" stroke-width="{stroke}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{stroke}"'
        f' stroke-dasharray="{filled} {gap}" stroke-linecap="round"'
        f' transform="rotate(-90 {cx} {cy})"/>'
        f'<text x="{cx}" y="{cy}" text-anchor="middle" dy=".35em"'
        f' font-family="Georgia,serif" font-size="22" fill="#17120b">{coverage}%</text>'
        f'</svg>'
    )


def _make_test_report(
    *,
    current_score: int = 60,
    reload_events: int = 0,
    resume_events: int = 5,
    score_week1_uplift: int | None = None,
) -> "ImpactReport":
    """Build a minimal ImpactReport for tests and dashboard snapshots."""
    now = dt.datetime.now(dt.timezone.utc)
    history = ImpactHistory(
        first_seen=now.isoformat(),
        latest_seen=now.isoformat(),
        latest_score=current_score,
        min_score=current_score,
        max_score=current_score,
        score_delta=0,
        daily_event_counts=(),
        score_series=(),
        recent_events=(),
    )
    usability = UsabilityMetrics(
        active_days=1,
        resume_events=resume_events,
        checkpoint_events=0,
        reload_events=reload_events,
        session_end_events=0,
        lifecycle_coverage=25,
        readiness_minutes_since_last_event=0,
        avg_session_duration_minutes=None,
        max_session_duration_minutes=None,
        cold_start_time_saved_minutes=reload_events * 5,
        score_week1_uplift=score_week1_uplift,
    )
    return ImpactReport(
        repo_name="test-repo",
        repo_id="test-repo",
        telemetry_path=Path("/tmp/test-telemetry.jsonl"),
        current_score=current_score,
        estimated_baseline_score=20,
        observed_events=resume_events + reload_events,
        event_counts={},
        dashboard_path=Path("/tmp/test-dashboard.html"),
        history=history,
        usability=usability,
        recommendations=(),
    )


def render_monitoring_dashboard(
    report: ImpactReport,
    branch_stats: list[Any] | None = None,
    forecast: Any | None = None,
    public: bool = False,
) -> str:
    daily = report.history.daily_event_counts or ({"date": "today", "events": 0},)
    score_series = report.history.score_series or ({"date": "today", "score": report.current_score},)
    max_events = max(int(item["events"]) for item in daily) if daily else 1

    bars = "\n".join(
        (
            '<div class="bar-row">'
            f'<span>{html.escape(str(item["date"]))}</span>'
            '<div class="bar-track">'
            f'<div class="bar-fill" style="width:{_bar_width(int(item["events"]), max_events)}%"></div>'
            "</div>"
            f'<strong>{int(item["events"])}</strong>'
            "</div>"
        )
        for item in daily[-14:]
    )
    recent = "\n".join(
        (
            '<li>'
            f'<span>{html.escape(str(item["event_name"]))}</span>'
            f'<strong>score {int(item["score"])}</strong>'
            f'<em>{html.escape(str(item["source"]))}</em>'
            "</li>"
        )
        for item in report.history.recent_events
    )
    if not recent:
        recent = "<li><span>No hook events yet</span><strong>score 0</strong><em>waiting</em></li>"

    event_cards = "\n".join(
        f"<div><span>{html.escape(name)}</span><strong>{count}</strong></div>"
        for name, count in sorted(report.event_counts.items())
    )
    if not event_cards:
        event_cards = "<div><span>waiting for hooks</span><strong>0</strong></div>"

    score_points = "\n".join(
        (
            '<div class="score-point">'
            f'<span>{html.escape(str(item["date"]))}</span>'
            f'<strong>{int(item["score"])}</strong>'
            '<div class="bar-track">'
            f'<div class="bar-fill moss" style="width:{_bar_width(int(item["score"]), 100)}%"></div>'
            "</div>"
            "</div>"
        )
        for item in score_series[-14:]
    )

    # token / cost estimates
    tok_per_s = report.usability.resume_events  # proxy: each resume = one injection
    # contract files ~5000 tokens typical; use conservative 4500
    tokens_injected = report.usability.resume_events * 4500
    # saved: ~30% of sessions would have needed 2000-token re-orientation
    tokens_saved = round(report.usability.resume_events * 0.30 * 2000)
    cost_saved_usd = round((tokens_saved / 1_000_000) * 3.0, 3)
    tokens_injected_str = f"{tokens_injected:,}"
    tokens_saved_str = f"{tokens_saved:,}"
    cost_saved_str = f"${cost_saved_usd:.2f}"

    # cold-start time saved
    cold_start_min = report.usability.cold_start_time_saved_minutes
    cold_start_str = f"{cold_start_min} min" if cold_start_min > 0 else "—"

    # week-1 score uplift
    uplift = report.usability.score_week1_uplift
    if uplift is None:
        uplift_str = "—"
    elif uplift >= 0:
        uplift_str = f"+{uplift}"
    else:
        uplift_str = str(uplift)

    # lifecycle donut
    donut = _lifecycle_donut_svg(report.usability.lifecycle_coverage)

    # lifecycle breakdown pills
    lifecycle_events = [
        ("session-start", report.usability.resume_events),
        ("pre-compact", report.usability.checkpoint_events - report.usability.session_end_events),
        ("post-compact", report.usability.reload_events),
        ("session-end", report.usability.session_end_events),
    ]
    lifecycle_pills = "".join(
        f'<div class="lc-pill {"lc-active" if count > 0 else "lc-empty"}">'
        f'<span>{html.escape(name)}</span><strong>{count}</strong></div>'
        for name, count in lifecycle_events
    )

    # branch table
    if branch_stats:
        branch_rows = "".join(
            f'<tr><td>{html.escape(s.branch)}</td><td>{s.session_count}</td>'
            f'<td><div class="bar-track" style="width:80px;display:inline-block">'
            f'<div class="bar-fill moss" style="width:{s.avg_score}%"></div></div> {s.avg_score}</td>'
            f'<td>{s.last_seen[:10]}</td></tr>'
            for s in branch_stats[:8]
        )
        branch_panel = f"""
      <div class="grid g3">
        <section class="panel" style="grid-column:1/-1">
          <h2>Branch health</h2>
          <table class="btable">
            <thead><tr><th>Branch</th><th>Sessions</th><th>Avg score</th><th>Last seen</th></tr></thead>
            <tbody>{branch_rows}</tbody>
          </table>
        </section>
      </div>"""
    else:
        branch_panel = ""

    # forecast panel
    if forecast:
        fc_rows = "".join(
            f'<div class="fc-week"><span>Week {i+1}</span><strong>{c}</strong>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{min(100,c*2)}%"></div></div></div>'
            for i, c in enumerate(forecast.week_series)
        )
        forecast_panel = f"""
      <div class="grid">
        <section class="panel">
          <h2>30-day forecast <small style="font-size:14px;font-weight:400;opacity:.6">confidence: {html.escape(forecast.confidence)}</small></h2>
          <div class="metrics4">
            <div class="metric"><span>Daily rate</span><strong>{forecast.daily_rate:.1f}</strong></div>
            <div class="metric"><span>Projected events</span><strong>{forecast.projected_events:,}</strong></div>
            <div class="metric"><span>Active days (30d)</span><strong>{forecast.projected_active_days}</strong></div>
          </div>
          <div class="fc-grid">{fc_rows}</div>
        </section>
        <section class="panel">
          <h2>Platform proof</h2>
          <div class="events">
            <div><span>Claude native hooks</span><strong>ready</strong></div>
            <div><span>Repo contract score</span><strong>{report.current_score}</strong></div>
            <div><span>Local-only telemetry</span><strong>on</strong></div>
          </div>
        </section>
      </div>"""
    else:
        forecast_panel = ""

    footer_text = (
        "Public snapshot — local-only telemetry aggregates only: scores, event counts, lifecycle coverage, time-series usability. No prompts, source code, secrets, or local paths included."
        if public else
        f"Local-only telemetry. Evidence log: {html.escape(str(report.telemetry_path))}"
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>repo-context-hooks — Continuity Impact Monitor</title>
  <style>
    :root {{
      --ink: #17120b; --paper: #f6efe0; --rust: #b54720;
      --gold: #e6a92f; --moss: #356857; --night: #101820;
      --line: rgba(23,18,11,.18);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; min-height: 100vh; color: var(--ink);
      background:
        radial-gradient(circle at 18% 10%, rgba(230,169,47,.42), transparent 28rem),
        radial-gradient(circle at 86% 16%, rgba(53,104,87,.3), transparent 24rem),
        linear-gradient(135deg, #fff8e8 0%, #f5e5c8 52%, #dac39b 100%);
      font-family: "Aptos","Segoe UI",sans-serif;
    }}
    .shell {{ width: min(1220px, calc(100% - 40px)); margin: 0 auto; padding: 54px 0; }}
    .hero {{
      position: relative; overflow: hidden; border: 1px solid var(--line);
      border-radius: 34px; background: rgba(255,252,242,.68);
      box-shadow: 0 34px 90px rgba(51,38,20,.22);
      padding: clamp(28px, 5vw, 64px);
    }}
    .hero:before {{
      content: ""; position: absolute; inset: 22px;
      border: 1px dashed rgba(181,71,32,.35); border-radius: 26px; pointer-events: none;
    }}
    .eyebrow {{ letter-spacing: .18em; text-transform: uppercase; color: var(--rust); font-weight: 800; font-size: 12px; }}
    h1 {{
      font-family: Georgia,"Times New Roman",serif;
      font-size: clamp(40px, 6vw, 80px); letter-spacing: -.07em;
      line-height: .87; margin: 14px 0 16px; max-width: 880px;
    }}
    .lede {{ max-width: 720px; font-size: clamp(16px, 1.8vw, 22px); line-height: 1.45; }}
    .metrics {{
      display: grid; grid-template-columns: repeat(4, minmax(0,1fr));
      gap: 14px; margin: 28px 0;
    }}
    .metrics4 {{
      display: grid; grid-template-columns: repeat(3, minmax(0,1fr));
      gap: 12px; margin: 18px 0;
    }}
    .metric {{
      border: 1px solid var(--line); border-radius: 22px; padding: 20px;
      background: rgba(255,255,255,.44); backdrop-filter: blur(10px);
    }}
    .metric span {{
      display: block; color: rgba(23,18,11,.64); font-weight: 700;
      font-size: 12px; text-transform: uppercase; letter-spacing: .08em;
    }}
    .metric strong {{
      display: block; margin-top: 6px;
      font-size: clamp(26px, 3.5vw, 46px);
      font-family: Georgia,"Times New Roman",serif; letter-spacing: -.05em;
    }}
    .metric sub {{ font-size: 14px; opacity: .6; }}
    .savings-row {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 14px; margin: 14px 0;
    }}
    .savings-card {{
      border: 1px solid var(--line); border-radius: 22px; padding: 20px;
      background: rgba(53,104,87,.08);
    }}
    .savings-card span {{
      display: block; font-size: 12px; font-weight: 700;
      text-transform: uppercase; letter-spacing: .08em; opacity: .7;
    }}
    .savings-card strong {{
      display: block; margin-top: 6px;
      font-size: clamp(22px, 3vw, 40px);
      font-family: Georgia,"Times New Roman",serif; color: var(--moss);
    }}
    .savings-card em {{ font-style: normal; font-size: 12px; opacity: .6; }}
    .grid {{ display: grid; grid-template-columns: 1.3fr .7fr; gap: 18px; margin-top: 18px; }}
    .g3 {{ grid-template-columns: 1fr; }}
    .panel {{
      border: 1px solid var(--line); border-radius: 28px;
      background: rgba(255,252,242,.72); padding: 26px;
    }}
    .panel h2 {{
      margin: 0 0 16px; font-family: Georgia,"Times New Roman",serif;
      letter-spacing: -.04em; font-size: 28px;
    }}
    .bar-row {{
      display: grid; grid-template-columns: 100px 1fr 44px;
      align-items: center; gap: 12px; margin: 10px 0; font-size: 14px;
    }}
    .bar-track {{
      height: 12px; border-radius: 999px;
      background: rgba(16,24,32,.1); overflow: hidden;
    }}
    .bar-fill {{
      height: 100%; border-radius: inherit;
      background: linear-gradient(90deg, var(--rust), var(--gold));
    }}
    .events {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 10px;
    }}
    .events div {{
      padding: 16px; border-radius: 18px;
      background: var(--night); color: #fff8e8;
    }}
    .events span {{ display: block; opacity: .72; font-size: 11px; margin-bottom: 4px; }}
    .events strong {{ font-size: 26px; font-family: Georgia,serif; }}
    .lc-grid {{
      display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 16px;
    }}
    .lc-pill {{
      border-radius: 14px; padding: 12px 10px; text-align: center; border: 1px solid var(--line);
    }}
    .lc-active {{ background: rgba(53,104,87,.12); border-color: var(--moss); }}
    .lc-empty {{ background: rgba(181,71,32,.06); border-color: rgba(181,71,32,.3); }}
    .lc-pill span {{ display: block; font-size: 10px; text-transform: uppercase; letter-spacing: .06em; opacity: .7; margin-bottom: 4px; }}
    .lc-pill strong {{ font-size: 22px; font-family: Georgia,serif; }}
    .usability {{
      display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 12px;
    }}
    .usability div, .score-point {{
      border: 1px solid var(--line); border-radius: 18px;
      padding: 14px; background: rgba(255,255,255,.38);
    }}
    .usability span, .score-point span {{
      display: block; color: rgba(23,18,11,.62); font-size: 11px;
      text-transform: uppercase; letter-spacing: .07em; font-weight: 800;
    }}
    .usability strong, .score-point strong {{
      display: block; font-size: 24px; margin: 4px 0 6px;
      font-family: Georgia,"Times New Roman",serif;
    }}
    .moss {{ background: linear-gradient(90deg, var(--moss), var(--gold)); }}
    ol {{ list-style: none; padding: 0; margin: 0; display: grid; gap: 8px; }}
    li {{
      display: grid; grid-template-columns: 1fr auto;
      gap: 4px 12px; padding: 12px 0; border-bottom: 1px solid var(--line);
    }}
    li em {{ grid-column: 1/-1; color: rgba(23,18,11,.58); font-style: normal; font-size: 12px; }}
    .btable {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    .btable th {{ text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: .07em; opacity: .6; padding: 6px 8px; border-bottom: 1px solid var(--line); }}
    .btable td {{ padding: 10px 8px; border-bottom: 1px solid rgba(23,18,11,.07); }}
    .btable tr:last-child td {{ border-bottom: none; }}
    .fc-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-top: 14px; }}
    .fc-week {{ border: 1px solid var(--line); border-radius: 14px; padding: 14px; }}
    .fc-week span {{ display: block; font-size: 11px; text-transform: uppercase; letter-spacing: .07em; opacity: .6; }}
    .fc-week strong {{ display: block; font-size: 24px; font-family: Georgia,serif; margin: 4px 0 8px; }}
    .footer {{ margin-top: 22px; color: rgba(23,18,11,.58); font-size: 13px; line-height: 1.6; }}
    @media (max-width: 840px) {{
      .metrics, .savings-row, .lc-grid, .grid, .metrics4 {{ grid-template-columns: 1fr; }}
      .shell {{ width: min(100% - 24px, 1220px); padding: 24px 0; }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="eyebrow">repo-context-hooks · continuity telemetry</div>
      <h1>Continuity Impact Monitor</h1>
      <p class="lede">Live evidence that AI sessions are preserving repo context — score, lifecycle coverage, token savings, branch health, and 30-day trajectory in one view.</p>

      <!-- Primary metrics row -->
      <div class="metrics">
        <div class="metric"><span>Contract score</span><strong>{report.current_score}</strong></div>
        <div class="metric"><span>Baseline (no hooks)</span><strong>{report.estimated_baseline_score}</strong></div>
        <div class="metric"><span>Continuity uplift</span><strong>+{report.uplift}</strong></div>
        <div class="metric"><span>Hook events total</span><strong>{report.observed_events}</strong></div>
      </div>

      <!-- Context savings row -->
      <div class="savings-row">
        <div class="savings-card">
          <span>Tokens injected</span>
          <strong>{tokens_injected_str}</strong>
          <em>~4,500 tok/session × {report.usability.resume_events} sessions</em>
        </div>
        <div class="savings-card">
          <span>Tokens saved (est.)</span>
          <strong>{tokens_saved_str}</strong>
          <em>30% of sessions avoid 2,000-tok re-orientation</em>
        </div>
        <div class="savings-card">
          <span>Est. cost saved</span>
          <strong>{cost_saved_str}</strong>
          <em>Claude Sonnet $3/M input tokens</em>
        </div>
        <div class="savings-card">
          <span>Cold starts prevented (est.)</span>
          <strong>{cold_start_str}</strong>
          <em>Each context reload saves ~5 min re-orientation</em>
        </div>
        <div class="savings-card">
          <span>Week-1 uplift</span>
          <strong>{uplift_str}</strong>
          <em>Score gain from day 0 to day 7</em>
        </div>
      </div>

      <!-- Activity + event mix -->
      <div class="grid">
        <section class="panel">
          <h2>Daily activity</h2>
          {bars}
        </section>
        <section class="panel">
          <h2>Event mix</h2>
          <div class="events">{event_cards}</div>
        </section>
      </div>

      <!-- Lifecycle coverage -->
      <div class="grid">
        <section class="panel">
          <h2>Lifecycle coverage</h2>
          <div style="display:grid;grid-template-columns:auto 1fr;gap:28px;align-items:center">
            {donut}
            <div>
              <p style="margin:0 0 12px;opacity:.7;font-size:14px">
                {report.usability.lifecycle_coverage}% of the 4-event lifecycle is instrumented.
                {'All four hooks are firing.' if report.usability.lifecycle_coverage == 100
                 else 'session-start is active. session-end, pre-compact, and post-compact will populate after longer sessions.' if report.usability.lifecycle_coverage == 25
                 else 'Some lifecycle events are missing.'}
              </p>
              <div class="lc-grid">{lifecycle_pills}</div>
            </div>
          </div>
        </section>
        <section class="panel">
          <h2>Score history</h2>
          {score_points}
        </section>
      </div>

      <!-- Usability metrics + recent evidence -->
      <div class="grid">
        <section class="panel">
          <h2>Recent hook evidence</h2>
          <ol>{recent}</ol>
        </section>
        <section class="panel">
          <h2>Usability metrics</h2>
          <div class="usability">
            <div><span>Active days</span><strong>{report.usability.active_days}</strong></div>
            <div><span>Sessions</span><strong>{report.usability.resume_events}</strong></div>
            <div><span>Checkpoints</span><strong>{report.usability.checkpoint_events}</strong></div>
            <div><span>Reloads</span><strong>{report.usability.reload_events}</strong></div>
            <div><span>Session ends</span><strong>{report.usability.session_end_events}</strong></div>
            <div><span>Avg duration</span><strong>{"—" if report.usability.avg_session_duration_minutes is None else f"{report.usability.avg_session_duration_minutes}m"}</strong></div>
          </div>
        </section>
      </div>

      {branch_panel}
      {forecast_panel}

      <p class="footer">{html.escape(footer_text)}</p>
    </section>
  </main>
</body>
</html>
"""


def write_monitoring_dashboard(report: ImpactReport) -> Path:
    try:
        b_stats = branch_scores(
            Path("."),
            telemetry_base=report.telemetry_path.parent.parent,
        )
    except Exception:
        b_stats = None
    try:
        fc = forecast_activity(
            Path("."),
            telemetry_base=report.telemetry_path.parent.parent,
        )
    except Exception:
        fc = None
    report.dashboard_path.write_text(
        render_monitoring_dashboard(report, branch_stats=b_stats, forecast=fc),
        encoding="utf-8",
    )
    return report.dashboard_path


def _public_time_series(report: ImpactReport) -> list[dict[str, Any]]:
    events_by_day = {
        str(item["date"]): int(item["events"])
        for item in report.history.daily_event_counts
    }
    if not report.history.score_series:
        return [
            {
                "date": "current",
                "score": report.current_score,
                "events": report.observed_events,
            }
        ]

    return [
        {
            "date": str(item["date"]),
            "score": int(item["score"]),
            "events": events_by_day.get(str(item["date"]), 0),
        }
        for item in report.history.score_series
    ]


def public_monitoring_snapshot(report: ImpactReport) -> dict[str, Any]:
    return {
        "repo": report.repo_name,
        "snapshot_at": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "score": report.current_score,
        "baseline": report.estimated_baseline_score,
        "uplift": report.uplift,
        "observed_events": report.observed_events,
        "first_seen": report.history.first_seen,
        "latest_seen": report.history.latest_seen,
        "time_series": _public_time_series(report),
        "usability": report.usability.to_dict(),
        "event_counts": dict(sorted(report.event_counts.items())),
    }


def render_public_monitoring_dashboard(
    report: ImpactReport,
    branch_stats: list[Any] | None = None,
    forecast: Any | None = None,
) -> str:
    return render_monitoring_dashboard(report, branch_stats=branch_stats, forecast=forecast, public=True)


def write_public_monitoring_snapshot(
    report: ImpactReport,
    output_dir: Path,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    dashboard_path = output_dir / "index.html"
    history_path = output_dir / "history.json"

    # Enrich snapshot with branch + forecast data
    try:
        b_stats = branch_scores(report.telemetry_path.parent.parent / ".." / ".." / report.repo_id)
    except Exception:
        b_stats = None
    try:
        fc = forecast_activity(
            Path("."),
            telemetry_base=report.telemetry_path.parent.parent,
        )
    except Exception:
        fc = None

    snap = public_monitoring_snapshot(report)
    if b_stats:
        snap["branches"] = [s.to_dict() for s in b_stats]
    if fc:
        snap["forecast"] = fc.to_dict()

    history_path.write_text(
        json.dumps(snap, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    dashboard_path.write_text(
        render_public_monitoring_dashboard(report, branch_stats=b_stats, forecast=fc),
        encoding="utf-8",
    )
    return {
        "dashboard_path": str(dashboard_path),
        "history_path": str(history_path),
    }


@dataclass(frozen=True)
class ForecastReport:
    daily_rate: float
    projected_events: int
    projected_active_days: int
    confidence: str  # "high" | "medium" | "low"
    week_series: tuple[int, ...]

    def render(self) -> str:
        lines = [
            f"30-day forecast (confidence: {self.confidence})",
            f"  Daily rate: {self.daily_rate:.1f} events/day",
            f"  Projected events (30d): {self.projected_events}",
            f"  Projected active days (30d): {self.projected_active_days}",
            "  Week breakdown:",
        ]
        for i, count in enumerate(self.week_series, 1):
            lines.append(f"    Week {i}: {count} events")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "daily_rate": self.daily_rate,
            "projected_events": self.projected_events,
            "projected_active_days": self.projected_active_days,
            "confidence": self.confidence,
            "week_series": list(self.week_series),
        }


def forecast_activity(
    repo_root: Path,
    days: int = 30,
    telemetry_base: Path | None = None,
) -> ForecastReport:
    """Project future activity from the rolling 7-day average event rate."""
    path = telemetry_events_path(repo_root, base=telemetry_base)
    events = _read_events(path)

    if not events:
        return ForecastReport(
            daily_rate=0.0,
            projected_events=0,
            projected_active_days=0,
            confidence="low",
            week_series=tuple(0 for _ in range(days // 7 + (1 if days % 7 else 0))),
        )

    daily_counts: dict[str, int] = {}
    for event in events:
        ts = _parse_timestamp(event.get("timestamp"))
        if ts is None:
            continue
        day_key = ts.date().isoformat()
        daily_counts[day_key] = daily_counts.get(day_key, 0) + 1

    num_days = len(daily_counts)
    sorted_days = sorted(daily_counts.keys(), reverse=True)
    window_days = sorted_days[:7]
    window_total = sum(daily_counts[d] for d in window_days)
    window_len = len(window_days)
    daily_rate = window_total / window_len if window_len > 0 else 0.0

    if num_days >= 7:
        confidence = "high"
    elif num_days >= 3:
        confidence = "medium"
    else:
        confidence = "low"

    week_count = days // 7 + (1 if days % 7 else 0)
    week_size = 7
    week_series = tuple(round(daily_rate * min(week_size, days - i * week_size)) for i in range(week_count))

    projected_events = round(daily_rate * days)
    projected_active_days = round(num_days / max(1, len(sorted_days)) * days) if sorted_days else 0

    return ForecastReport(
        daily_rate=round(daily_rate, 2),
        projected_events=projected_events,
        projected_active_days=projected_active_days,
        confidence=confidence,
        week_series=week_series,
    )


@dataclass(frozen=True)
class BranchStat:
    branch: str
    session_count: int
    avg_score: int
    last_seen: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch": self.branch,
            "session_count": self.session_count,
            "avg_score": self.avg_score,
            "last_seen": self.last_seen,
        }


def branch_scores(
    repo_root: Path,
    telemetry_base: Path | None = None,
) -> list[BranchStat]:
    """Return per-branch stats sorted by last_seen descending."""
    path = telemetry_events_path(repo_root, base=telemetry_base)
    events = _read_events(path)

    branch_data: dict[str, dict[str, Any]] = {}
    for event in events:
        branch = str(event.get("branch") or "unknown")
        score = event.get("repo_contract_score")
        ts = event.get("timestamp", "")
        sid = event.get("session_id", "")

        if branch not in branch_data:
            branch_data[branch] = {"scores": [], "sessions": set(), "last_seen": ""}
        if isinstance(score, (int, float)):
            branch_data[branch]["scores"].append(int(score))
        if sid:
            branch_data[branch]["sessions"].add(sid)
        if ts > branch_data[branch]["last_seen"]:
            branch_data[branch]["last_seen"] = ts

    stats = []
    for branch, data in branch_data.items():
        scores = data["scores"]
        avg = round(sum(scores) / len(scores)) if scores else 0
        stats.append(BranchStat(
            branch=branch,
            session_count=len(data["sessions"]),
            avg_score=avg,
            last_seen=data["last_seen"],
        ))

    stats.sort(key=lambda s: s.last_seen, reverse=True)
    return stats


_GHOST_REPO_NAMES: frozenset[str] = frozenset({"repo", "tmp", "temp", "test"})


def purge_ghost_repos(
    telemetry_base: Path | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Remove telemetry dirs with <2 events and a ghost repo name.

    Returns {"removed": N, "bytes_freed": M, "dirs": [...paths...]}.
    Pass dry_run=False to actually delete.
    """
    import shutil

    base = telemetry_base or _default_telemetry_base()
    if not base.exists():
        return {"removed": 0, "bytes_freed": 0, "dirs": []}

    removed = 0
    bytes_freed = 0
    removed_dirs: list[str] = []

    for entry in base.iterdir():
        if not entry.is_dir():
            continue
        events_file = entry / EVENTS_FILE
        events = _read_events(events_file)
        if len(events) >= 2:
            continue
        repo_name = events[0].get("repo_name", "") if events else entry.name
        if repo_name not in _GHOST_REPO_NAMES:
            continue
        dir_size = sum(f.stat().st_size for f in entry.rglob("*") if f.is_file())
        removed_dirs.append(str(entry))
        bytes_freed += dir_size
        removed += 1
        if not dry_run:
            shutil.rmtree(entry, ignore_errors=True)

    return {"removed": removed, "bytes_freed": bytes_freed, "dirs": removed_dirs}


def measure_impact(repo_root: Path, telemetry_base: Path | None = None) -> ImpactReport:
    repo_root = repo_root.resolve()
    signals = contract_signals(repo_root)
    path = telemetry_events_path(repo_root, base=telemetry_base)
    events = _read_events(path)
    event_counts: dict[str, int] = {}
    for event in events:
        name = str(event.get("event_name", "unknown"))
        event_counts[name] = event_counts.get(name, 0) + 1
    history = _build_history(events)
    usability = _build_usability(events, history)
    dashboard_path = _dashboard_path(path)

    report = ImpactReport(
        repo_name=_repo_display_name(repo_root),
        repo_id=repo_id(repo_root),
        telemetry_path=path,
        current_score=int(signals["score"]),
        estimated_baseline_score=int(signals["estimated_baseline_score"]),
        observed_events=len(events),
        event_counts=event_counts,
        dashboard_path=dashboard_path,
        history=history,
        usability=usability,
        recommendations=_recommendations(signals, events),
    )
    write_monitoring_dashboard(report)
    return report


def auto_commit_snapshot(
    repo_root: Path,
    telemetry_base: Path | None = None,
) -> bool:
    repo_root = repo_root.resolve()
    if not (repo_root / ".git").exists():
        return False

    monitoring_dir = repo_root / "docs" / "monitoring"
    if not monitoring_dir.exists():
        return False

    try:
        report = measure_impact(repo_root, telemetry_base=telemetry_base)
        write_public_monitoring_snapshot(report, monitoring_dir)

        subprocess.run(
            ["git", "add", str(monitoring_dir)],
            cwd=repo_root,
            check=True,
            capture_output=True,
            timeout=10,
        )
        diff = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=repo_root,
            capture_output=True,
            timeout=5,
        )
        if diff.returncode == 0:
            return False

        subprocess.run(
            ["git", "commit", "-m", "chore: update monitoring snapshot [skip ci]"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            timeout=15,
        )
        return True
    except Exception:
        return False
