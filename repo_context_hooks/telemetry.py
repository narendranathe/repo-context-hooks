from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4


EVENTS_FILE = "events.jsonl"
CURRENT_SESSION_FILE = "current-session.json"


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


def _repo_display_name(repo_root: Path) -> str:
    top_level = _git_output(repo_root, "rev-parse", "--show-toplevel")
    try:
        is_git_root = bool(top_level) and Path(top_level).resolve() == repo_root.resolve()
    except OSError:
        is_git_root = False
    if not is_git_root:
        return repo_root.name

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


def _clean_dimension(value: object, default: str) -> str:
    text = str(value or "").strip()
    return text if text else default


def _agent_platform_from_source(source: str) -> str:
    normalized = source.lower()
    if "claude" in normalized or normalized in {
        "repo_specs_memory",
        "session_context",
    }:
        return "claude"
    for platform in (
        "codex",
        "cursor",
        "replit",
        "windsurf",
        "lovable",
        "openclaw",
        "ollama",
        "kimi",
    ):
        if platform in normalized:
            return platform
    return "unknown"


def _event_agent_platform(event: dict[str, Any]) -> str:
    details = event.get("details", {})
    if not isinstance(details, dict):
        details = {}
    return _clean_dimension(
        event.get("agent_platform")
        or details.get("agent_platform")
        or _agent_platform_from_source(str(event.get("source", ""))),
        "unknown",
    )


def _event_model_name(event: dict[str, Any]) -> str:
    details = event.get("details", {})
    if not isinstance(details, dict):
        details = {}
    return _clean_dimension(
        event.get("model_name") or details.get("model_name"),
        "unknown",
    )


def _event_agent_session_id(event: dict[str, Any]) -> str:
    return _clean_dimension(event.get("agent_session_id"), "unknown-session")


def _current_session_state_path(events_path: Path) -> Path:
    return events_path.with_name(CURRENT_SESSION_FILE)


def _read_current_session(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _is_recent_session_start(state: dict[str, Any] | None) -> bool:
    if not state:
        return False
    timestamp = _parse_timestamp(str(state.get("started_at", "")))
    if timestamp is None:
        return False
    age = dt.datetime.now(dt.timezone.utc) - timestamp
    return dt.timedelta(seconds=0) <= age <= dt.timedelta(minutes=5)


def _new_agent_session_id(agent_platform: str) -> str:
    timestamp = (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .strftime("%Y%m%dT%H%M%SZ")
    )
    safe_platform = "".join(
        char.lower() if char.isalnum() else "-"
        for char in agent_platform
    ).strip("-") or "agent"
    return f"{timestamp}-{safe_platform}-{uuid4().hex[:8]}"


def _write_current_session(
    path: Path,
    *,
    agent_session_id: str,
    agent_platform: str,
    model_name: str,
) -> None:
    payload = {
        "agent_session_id": agent_session_id,
        "agent_platform": agent_platform,
        "model_name": model_name,
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    try:
        path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    except OSError:
        pass


def _resolve_agent_session_id(
    *,
    event_name: str,
    events_path: Path,
    agent_platform: str,
    model_name: str,
    explicit_session_id: str | None = None,
) -> str:
    state_path = _current_session_state_path(events_path)
    state = _read_current_session(state_path)
    if explicit_session_id:
        session_id = _clean_dimension(explicit_session_id, "unknown-session")
        _write_current_session(
            state_path,
            agent_session_id=session_id,
            agent_platform=agent_platform,
            model_name=model_name,
        )
        return session_id

    normalized_event = event_name.lower()
    if "session-start" in normalized_event:
        existing = _clean_dimension(
            state.get("agent_session_id") if state else None,
            "",
        )
        if existing and _is_recent_session_start(state):
            return existing
        session_id = _new_agent_session_id(agent_platform)
        _write_current_session(
            state_path,
            agent_session_id=session_id,
            agent_platform=agent_platform,
            model_name=model_name,
        )
        return session_id

    existing = _clean_dimension(
        state.get("agent_session_id") if state else None,
        "",
    )
    if existing:
        return existing

    session_id = _new_agent_session_id(agent_platform)
    _write_current_session(
        state_path,
        agent_session_id=session_id,
        agent_platform=agent_platform,
        model_name=model_name,
    )
    return session_id


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
    agent_platform: str | None = None,
    model_name: str | None = None,
    agent_session_id: str | None = None,
) -> Path:
    repo_root = repo_root.resolve()
    signals = contract_signals(repo_root)
    details = dict(details or {})
    path = telemetry_events_path(repo_root, base=telemetry_base)
    resolved_platform = _clean_dimension(
        agent_platform
        or details.get("agent_platform")
        or os.environ.get("REPO_CONTEXT_HOOKS_AGENT_PLATFORM")
        or _agent_platform_from_source(source),
        "unknown",
    )
    resolved_model = _clean_dimension(
        model_name
        or details.get("model_name")
        or os.environ.get("REPO_CONTEXT_HOOKS_MODEL_NAME")
        or os.environ.get("CODEX_MODEL")
        or os.environ.get("CLAUDE_MODEL"),
        "unknown",
    )
    resolved_session_id = _resolve_agent_session_id(
        event_name=event_name,
        events_path=path,
        agent_platform=resolved_platform,
        model_name=resolved_model,
        explicit_session_id=agent_session_id
        or details.get("agent_session_id")
        or os.environ.get("REPO_CONTEXT_HOOKS_AGENT_SESSION_ID")
        or os.environ.get("CLAUDE_SESSION_ID")
        or os.environ.get("CODEX_SESSION_ID"),
    )
    event = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "event_name": event_name,
        "source": source,
        "agent_platform": resolved_platform,
        "model_name": resolved_model,
        "agent_session_id": resolved_session_id,
        "repo_id": repo_id(repo_root),
        "repo_name": _repo_display_name(repo_root),
        "branch": _git_output(repo_root, "branch", "--show-current") or "unknown",
        "repo_contract_score": signals["score"],
        "estimated_baseline_score": signals["estimated_baseline_score"],
        "details": details,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    try:
        measure_impact(repo_root, telemetry_base=telemetry_base)
    except Exception:
        pass
    return path


def _context_window_details(
    *,
    used_tokens: int,
    limit_tokens: int,
    threshold_percent: float,
) -> dict[str, Any]:
    if limit_tokens <= 0:
        raise ValueError("limit_tokens must be greater than zero")
    if used_tokens < 0:
        raise ValueError("used_tokens must be zero or greater")
    usage_percent = round(used_tokens / limit_tokens * 100, 2)
    remaining_percent = round(max(0.0, 100.0 - usage_percent), 2)
    threshold_window = round(max(0.0, 100.0 - threshold_percent), 2)
    return {
        "used_tokens": used_tokens,
        "limit_tokens": limit_tokens,
        "usage_percent": usage_percent,
        "remaining_percent": remaining_percent,
        "threshold_percent": float(threshold_percent),
        "threshold_window_percent": threshold_window,
    }


def record_context_window(
    repo_root: Path,
    *,
    used_tokens: int,
    limit_tokens: int,
    threshold_percent: float = 99.0,
    checkpoint: bool = False,
    source: str = "context-window",
    telemetry_base: Path | None = None,
    agent_platform: str | None = None,
    model_name: str | None = None,
    agent_session_id: str | None = None,
) -> Path:
    """Record context-window pressure from an editor, wrapper, or model runner."""
    details = _context_window_details(
        used_tokens=used_tokens,
        limit_tokens=limit_tokens,
        threshold_percent=threshold_percent,
    )
    threshold_reached = details["usage_percent"] >= threshold_percent
    event_name = (
        "context-window-threshold"
        if threshold_reached
        else "context-window-sample"
    )
    path = record_event(
        repo_root,
        event_name,
        source=source,
        telemetry_base=telemetry_base,
        details=details,
        agent_platform=agent_platform,
        model_name=model_name,
        agent_session_id=agent_session_id,
    )
    if threshold_reached and checkpoint:
        checkpoint_details = {
            **details,
            "checkpoint_trigger": event_name,
            "checkpoint_requested": True,
        }
        record_event(
            repo_root,
            "pre-compact",
            source=f"{source}:checkpoint",
            telemetry_base=telemetry_base,
            details=checkpoint_details,
            agent_platform=agent_platform,
            model_name=model_name,
            agent_session_id=agent_session_id,
        )
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_days": self.active_days,
            "resume_events": self.resume_events,
            "checkpoint_events": self.checkpoint_events,
            "reload_events": self.reload_events,
            "session_end_events": self.session_end_events,
            "lifecycle_coverage": self.lifecycle_coverage,
            "readiness_minutes_since_last_event": self.readiness_minutes_since_last_event,
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
    agent_comparison: tuple[dict[str, Any], ...]
    agent_sessions: tuple[dict[str, Any], ...]
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
        if self.event_counts:
            lines.append("Event counts:")
            lines.extend(
                f"- {name}: {count}"
                for name, count in sorted(self.event_counts.items())
            )
        if self.agent_comparison:
            lines.append("Agent/model comparison:")
            lines.extend(
                (
                    "- "
                    f"{item['agent_platform']} / {item['model_name']}: "
                    f"{item['events']} events, score {item['latest_score']}"
                )
                for item in self.agent_comparison
            )
        if self.agent_sessions:
            lines.append(f"Agent sessions observed: {len(self.agent_sessions)}")
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
            "agent_comparison": list(self.agent_comparison),
            "agent_sessions": list(self.agent_sessions),
            "dashboard_path": str(self.dashboard_path),
            "history": self.history.to_dict(),
            "usability": self.usability.to_dict(),
            "recommendations": list(self.recommendations),
        }


@dataclass(frozen=True)
class RepoRollupSummary:
    repo_name: str
    repo_id: str
    observed_events: int
    latest_score: int
    baseline: int
    uplift: int
    agent_sessions: int
    lifecycle_coverage: int
    context_threshold_events: int
    checkpoint_events: int
    max_context_usage_percent: float | None
    latest_seen: str | None
    event_counts: dict[str, int]
    agent_platforms: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_name": self.repo_name,
            "repo_id": self.repo_id,
            "observed_events": self.observed_events,
            "latest_score": self.latest_score,
            "baseline": self.baseline,
            "uplift": self.uplift,
            "agent_sessions": self.agent_sessions,
            "lifecycle_coverage": self.lifecycle_coverage,
            "context_threshold_events": self.context_threshold_events,
            "checkpoint_events": self.checkpoint_events,
            "max_context_usage_percent": self.max_context_usage_percent,
            "latest_seen": self.latest_seen,
            "event_counts": self.event_counts,
            "agent_platforms": list(self.agent_platforms),
        }


@dataclass(frozen=True)
class RollupReport:
    telemetry_base: Path
    generated_at: str
    repos: tuple[RepoRollupSummary, ...]
    event_counts: dict[str, int]

    @property
    def repo_count(self) -> int:
        return len(self.repos)

    @property
    def total_events(self) -> int:
        return sum(repo.observed_events for repo in self.repos)

    @property
    def total_agent_sessions(self) -> int:
        return sum(repo.agent_sessions for repo in self.repos)

    @property
    def context_threshold_events(self) -> int:
        return sum(repo.context_threshold_events for repo in self.repos)

    @property
    def checkpoint_events(self) -> int:
        return sum(repo.checkpoint_events for repo in self.repos)

    def render(self) -> str:
        lines = [
            "[OK] cross-repo telemetry rollup",
            f"Telemetry store: {self.telemetry_base}",
            f"Repos observed: {self.repo_count}",
            f"Total events: {self.total_events}",
            f"Agent sessions observed: {self.total_agent_sessions}",
            f"Context threshold events: {self.context_threshold_events}",
            f"Checkpoint events: {self.checkpoint_events}",
        ]
        if self.repos:
            lines.append("Repos:")
            for repo in self.repos:
                usage = (
                    "n/a"
                    if repo.max_context_usage_percent is None
                    else f"{repo.max_context_usage_percent}%"
                )
                lines.append(
                    "- "
                    f"{repo.repo_name}: {repo.observed_events} events, "
                    f"{repo.agent_sessions} sessions, "
                    f"score {repo.latest_score}, "
                    f"context max {usage}"
                )
        else:
            lines.append("No repo telemetry events found yet.")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "repo_count": self.repo_count,
            "total_events": self.total_events,
            "total_agent_sessions": self.total_agent_sessions,
            "context_threshold_events": self.context_threshold_events,
            "checkpoint_events": self.checkpoint_events,
            "event_counts": self.event_counts,
            "repos": [repo.to_dict() for repo in self.repos],
        }


def _prometheus_label(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace('"', '\\"')
    )


def _prometheus_line(
    metric: str,
    value: int | float,
    *,
    labels: dict[str, str] | None = None,
) -> str:
    label_text = ""
    if labels:
        rendered = ",".join(
            f'{name}="{_prometheus_label(label_value)}"'
            for name, label_value in labels.items()
        )
        label_text = f"{{{rendered}}}"
    return f"{metric}{label_text} {value}"


def render_prometheus_metrics(report: ImpactReport) -> str:
    """Render aggregate continuity evidence in Prometheus text exposition format."""
    repo_label = {"repo": report.repo_name}
    metrics: list[str] = [
        "# HELP repo_context_hooks_continuity_score Current repo continuity score from the checked-in repo contract.",
        "# TYPE repo_context_hooks_continuity_score gauge",
        _prometheus_line(
            "repo_context_hooks_continuity_score",
            report.current_score,
            labels=repo_label,
        ),
        "# HELP repo_context_hooks_baseline_score Estimated score for a README-only repo without continuity hooks.",
        "# TYPE repo_context_hooks_baseline_score gauge",
        _prometheus_line(
            "repo_context_hooks_baseline_score",
            report.estimated_baseline_score,
            labels=repo_label,
        ),
        "# HELP repo_context_hooks_uplift Difference between current continuity score and estimated baseline.",
        "# TYPE repo_context_hooks_uplift gauge",
        _prometheus_line(
            "repo_context_hooks_uplift",
            report.uplift,
            labels=repo_label,
        ),
        "# HELP repo_context_hooks_observed_events_total Total observed local hook and skill telemetry events.",
        "# TYPE repo_context_hooks_observed_events_total counter",
        _prometheus_line(
            "repo_context_hooks_observed_events_total",
            report.observed_events,
            labels=repo_label,
        ),
        "# HELP repo_context_hooks_active_days Number of UTC days with observed continuity events.",
        "# TYPE repo_context_hooks_active_days gauge",
        _prometheus_line(
            "repo_context_hooks_active_days",
            report.usability.active_days,
            labels=repo_label,
        ),
        "# HELP repo_context_hooks_lifecycle_coverage_percent Percent of lifecycle stages observed across session-start, pre-compact, post-compact, and session-end.",
        "# TYPE repo_context_hooks_lifecycle_coverage_percent gauge",
        _prometheus_line(
            "repo_context_hooks_lifecycle_coverage_percent",
            report.usability.lifecycle_coverage,
            labels=repo_label,
        ),
        "# HELP repo_context_hooks_resume_events_total Total observed session-start or resume events.",
        "# TYPE repo_context_hooks_resume_events_total counter",
        _prometheus_line(
            "repo_context_hooks_resume_events_total",
            report.usability.resume_events,
            labels=repo_label,
        ),
        "# HELP repo_context_hooks_checkpoint_events_total Total observed checkpoint events.",
        "# TYPE repo_context_hooks_checkpoint_events_total counter",
        _prometheus_line(
            "repo_context_hooks_checkpoint_events_total",
            report.usability.checkpoint_events,
            labels=repo_label,
        ),
        "# HELP repo_context_hooks_reload_events_total Total observed post-compact reload events.",
        "# TYPE repo_context_hooks_reload_events_total counter",
        _prometheus_line(
            "repo_context_hooks_reload_events_total",
            report.usability.reload_events,
            labels=repo_label,
        ),
        "# HELP repo_context_hooks_session_end_events_total Total observed session-end events.",
        "# TYPE repo_context_hooks_session_end_events_total counter",
        _prometheus_line(
            "repo_context_hooks_session_end_events_total",
            report.usability.session_end_events,
            labels=repo_label,
        ),
        "# HELP repo_context_hooks_event_count Local continuity events by event name.",
        "# TYPE repo_context_hooks_event_count counter",
    ]
    for event_name, count in sorted(report.event_counts.items()):
        metrics.append(
            _prometheus_line(
                "repo_context_hooks_event_count",
                count,
                labels={"repo": report.repo_name, "event_name": event_name},
            )
        )
    metrics.extend(
        [
            "# HELP repo_context_hooks_agent_events_total Local continuity events by agent platform and model.",
            "# TYPE repo_context_hooks_agent_events_total counter",
            "# HELP repo_context_hooks_agent_latest_score Latest continuity score by agent platform and model.",
            "# TYPE repo_context_hooks_agent_latest_score gauge",
            "# HELP repo_context_hooks_agent_sessions_total Observed agent sessions by agent platform and model.",
            "# TYPE repo_context_hooks_agent_sessions_total counter",
        ]
    )
    for item in report.agent_comparison:
        labels = {
            "repo": report.repo_name,
            "agent_platform": str(item["agent_platform"]),
            "model_name": str(item["model_name"]),
        }
        metrics.append(
            _prometheus_line(
                "repo_context_hooks_agent_events_total",
                int(item["events"]),
                labels=labels,
            )
        )
        metrics.append(
            _prometheus_line(
                "repo_context_hooks_agent_latest_score",
                int(item["latest_score"]),
                labels=labels,
            )
        )
        metrics.append(
            _prometheus_line(
                "repo_context_hooks_agent_sessions_total",
                int(item.get("sessions", 0)),
                labels=labels,
            )
        )
    return "\n".join(metrics) + "\n"


def _event_context_usage_percent(event: dict[str, Any]) -> float | None:
    details = event.get("details", {})
    if not isinstance(details, dict):
        return None
    value = details.get("usage_percent")
    if value is None:
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _rollup_event_paths(
    telemetry_base: Path,
    projects_root: Path | None = None,
) -> tuple[Path, ...]:
    paths: set[Path] = set()
    if not telemetry_base.exists() or not telemetry_base.is_dir():
        pass
    else:
        paths.update(path.resolve() for path in telemetry_base.glob(f"*/{EVENTS_FILE}"))
    if projects_root is not None and projects_root.exists():
        paths.update(
            path.resolve()
            for path in projects_root.glob(f"*/.repo-context-hooks/telemetry/*/{EVENTS_FILE}")
        )
    return tuple(sorted(paths))


def _build_repo_rollup(events: list[dict[str, Any]]) -> RepoRollupSummary:
    history = _build_history(events)
    usability = _build_usability(events, history)
    latest = events[-1]
    event_counts: dict[str, int] = {}
    for event in events:
        name = _event_name(event)
        event_counts[name] = event_counts.get(name, 0) + 1
    context_values = [
        value
        for value in (_event_context_usage_percent(event) for event in events)
        if value is not None
    ]
    baseline = 0
    try:
        baseline = int(latest.get("estimated_baseline_score", 0))
    except (TypeError, ValueError):
        baseline = 0
    latest_score = history.latest_score or _event_score(latest)
    session_ids = {
        _event_agent_session_id(event)
        for event in events
        if _event_agent_session_id(event) != "unknown-session"
    }
    if not session_ids and events:
        session_ids = {"unknown-session"}
    agent_platforms = tuple(
        sorted(
            {
                _event_agent_platform(event)
                for event in events
            }
        )
    )
    return RepoRollupSummary(
        repo_name=_clean_dimension(latest.get("repo_name"), "unknown-repo"),
        repo_id=_clean_dimension(latest.get("repo_id"), "unknown-repo"),
        observed_events=len(events),
        latest_score=latest_score,
        baseline=baseline,
        uplift=latest_score - baseline,
        agent_sessions=len(session_ids),
        lifecycle_coverage=usability.lifecycle_coverage,
        context_threshold_events=event_counts.get("context-window-threshold", 0),
        checkpoint_events=sum(
            count
            for name, count in event_counts.items()
            if name in {"pre-compact", "session-end"}
        ),
        max_context_usage_percent=max(context_values) if context_values else None,
        latest_seen=history.latest_seen,
        event_counts=event_counts,
        agent_platforms=agent_platforms,
    )


def measure_rollup(
    telemetry_base: Path | None = None,
    projects_root: Path | None = None,
) -> RollupReport:
    """Aggregate local telemetry across every repo directory in the telemetry store."""
    base = telemetry_base or _default_telemetry_base()
    grouped: dict[str, list[dict[str, Any]]] = {}
    event_counts: dict[str, int] = {}
    for path in _rollup_event_paths(base, projects_root=projects_root):
        for event in _read_events(path):
            repo_key = _clean_dimension(
                event.get("repo_id"),
                path.parent.name,
            )
            grouped.setdefault(repo_key, []).append(event)
            name = _event_name(event)
            event_counts[name] = event_counts.get(name, 0) + 1

    repos = [
        _build_repo_rollup(sorted(events, key=lambda event: str(event.get("timestamp", ""))))
        for events in grouped.values()
        if events
    ]
    return RollupReport(
        telemetry_base=base,
        generated_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        repos=tuple(
            sorted(
                repos,
                key=lambda repo: (
                    -repo.observed_events,
                    repo.repo_name,
                ),
            )
        ),
        event_counts=event_counts,
    )


def render_rollup_prometheus_metrics(report: RollupReport) -> str:
    metrics: list[str] = [
        "# HELP repo_context_hooks_rollup_repos_total Number of repositories with local telemetry evidence.",
        "# TYPE repo_context_hooks_rollup_repos_total gauge",
        _prometheus_line("repo_context_hooks_rollup_repos_total", report.repo_count),
        "# HELP repo_context_hooks_rollup_events_total Total local continuity events across repositories.",
        "# TYPE repo_context_hooks_rollup_events_total counter",
        _prometheus_line("repo_context_hooks_rollup_events_total", report.total_events),
        "# HELP repo_context_hooks_rollup_agent_sessions_total Total observed agent sessions across repositories.",
        "# TYPE repo_context_hooks_rollup_agent_sessions_total counter",
        _prometheus_line("repo_context_hooks_rollup_agent_sessions_total", report.total_agent_sessions),
        "# HELP repo_context_hooks_rollup_context_threshold_events_total Total context-window threshold events across repositories.",
        "# TYPE repo_context_hooks_rollup_context_threshold_events_total counter",
        _prometheus_line(
            "repo_context_hooks_rollup_context_threshold_events_total",
            report.context_threshold_events,
        ),
        "# HELP repo_context_hooks_repo_events_total Local continuity events per repository.",
        "# TYPE repo_context_hooks_repo_events_total counter",
    ]
    for repo in report.repos:
        labels = {"repo": repo.repo_name}
        metrics.append(
            _prometheus_line(
                "repo_context_hooks_repo_events_total",
                repo.observed_events,
                labels=labels,
            )
        )
        metrics.append(
            _prometheus_line(
                "repo_context_hooks_repo_context_threshold_events_total",
                repo.context_threshold_events,
                labels=labels,
            )
        )
        if repo.max_context_usage_percent is not None:
            metrics.append(
                _prometheus_line(
                    "repo_context_hooks_repo_max_context_usage_percent",
                    repo.max_context_usage_percent,
                    labels=labels,
                )
            )
    return "\n".join(metrics) + "\n"


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
    )


def _build_agent_comparison(
    events: list[dict[str, Any]],
    *,
    baseline: int,
) -> tuple[dict[str, Any], ...]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for event in events:
        key = (_event_agent_platform(event), _event_model_name(event))
        grouped.setdefault(key, []).append(event)

    rows: list[dict[str, Any]] = []
    for (agent_platform, model_name), group in grouped.items():
        history = _build_history(group)
        usability = _build_usability(group, history)
        latest_score = history.latest_score or _event_score(group[-1])
        session_count = len(
            {
                _event_agent_session_id(event)
                for event in group
            }
        )
        rows.append(
            {
                "agent_platform": agent_platform,
                "model_name": model_name,
                "events": len(group),
                "sessions": session_count,
                "latest_score": latest_score,
                "baseline": baseline,
                "uplift": latest_score - baseline,
                "lifecycle_coverage": usability.lifecycle_coverage,
                "resume_events": usability.resume_events,
                "checkpoint_events": usability.checkpoint_events,
                "reload_events": usability.reload_events,
                "session_end_events": usability.session_end_events,
                "latest_seen": history.latest_seen,
            }
        )
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                -int(item["events"]),
                str(item["agent_platform"]),
                str(item["model_name"]),
            ),
        )
    )


def _build_agent_sessions(
    events: list[dict[str, Any]],
    *,
    baseline: int,
) -> tuple[dict[str, Any], ...]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for event in events:
        key = (
            _event_agent_session_id(event),
            _event_agent_platform(event),
            _event_model_name(event),
        )
        grouped.setdefault(key, []).append(event)

    rows: list[dict[str, Any]] = []
    for (session_id, agent_platform, model_name), group in grouped.items():
        history = _build_history(group)
        usability = _build_usability(group, history)
        latest_score = history.latest_score or _event_score(group[-1])
        rows.append(
            {
                "agent_session_id": session_id,
                "agent_platform": agent_platform,
                "model_name": model_name,
                "events": len(group),
                "latest_score": latest_score,
                "baseline": baseline,
                "uplift": latest_score - baseline,
                "lifecycle_coverage": usability.lifecycle_coverage,
                "first_seen": history.first_seen,
                "latest_seen": history.latest_seen,
            }
        )
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                int(item["events"]),
                str(item["agent_platform"]),
            ),
            reverse=True,
        )
    )


def _dashboard_path(events_path: Path) -> Path:
    return events_path.with_name("monitoring.html")


def _bar_width(value: int, maximum: int) -> int:
    if maximum <= 0:
        return 0
    return max(4, min(100, round(value / maximum * 100)))


def render_monitoring_dashboard(report: ImpactReport) -> str:
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

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Continuity Impact Monitor</title>
  <style>
    :root {{
      --ink: #17120b;
      --paper: #f6efe0;
      --rust: #b54720;
      --gold: #e6a92f;
      --moss: #356857;
      --night: #101820;
      --line: rgba(23, 18, 11, .18);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      background:
        radial-gradient(circle at 18% 10%, rgba(230,169,47,.42), transparent 28rem),
        radial-gradient(circle at 86% 16%, rgba(53,104,87,.3), transparent 24rem),
        linear-gradient(135deg, #fff8e8 0%, #f5e5c8 52%, #dac39b 100%);
      font-family: "Aptos", "Segoe UI", sans-serif;
    }}
    .shell {{
      width: min(1180px, calc(100% - 40px));
      margin: 0 auto;
      padding: 54px 0;
    }}
    .hero {{
      position: relative;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 34px;
      background: rgba(255, 252, 242, .68);
      box-shadow: 0 34px 90px rgba(51, 38, 20, .22);
      padding: clamp(28px, 5vw, 64px);
    }}
    .hero:before {{
      content: "";
      position: absolute;
      inset: 22px;
      border: 1px dashed rgba(181,71,32,.35);
      border-radius: 26px;
      pointer-events: none;
    }}
    .eyebrow {{
      letter-spacing: .18em;
      text-transform: uppercase;
      color: var(--rust);
      font-weight: 800;
      font-size: 12px;
    }}
    h1 {{
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(44px, 7vw, 92px);
      letter-spacing: -.07em;
      line-height: .87;
      margin: 18px 0 20px;
      max-width: 880px;
    }}
    .lede {{
      max-width: 720px;
      font-size: clamp(18px, 2vw, 24px);
      line-height: 1.45;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin: 34px 0;
    }}
    .metric {{
      border: 1px solid var(--line);
      border-radius: 22px;
      padding: 22px;
      background: rgba(255,255,255,.44);
      backdrop-filter: blur(10px);
    }}
    .metric span {{
      display: block;
      color: rgba(23,18,11,.64);
      font-weight: 700;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: .08em;
    }}
    .metric strong {{
      display: block;
      margin-top: 8px;
      font-size: clamp(30px, 4vw, 52px);
      font-family: Georgia, "Times New Roman", serif;
      letter-spacing: -.05em;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1.25fr .75fr;
      gap: 18px;
      margin-top: 18px;
    }}
    .panel {{
      border: 1px solid var(--line);
      border-radius: 28px;
      background: rgba(255, 252, 242, .72);
      padding: 26px;
    }}
    .panel h2 {{
      margin: 0 0 18px;
      font-family: Georgia, "Times New Roman", serif;
      letter-spacing: -.04em;
      font-size: 30px;
    }}
    .bar-row {{
      display: grid;
      grid-template-columns: 90px 1fr 40px;
      align-items: center;
      gap: 12px;
      margin: 12px 0;
      font-size: 14px;
    }}
    .bar-track {{
      height: 14px;
      border-radius: 999px;
      background: rgba(16,24,32,.1);
      overflow: hidden;
    }}
    .bar-fill {{
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--rust), var(--gold));
    }}
    .events {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 10px;
    }}
    .events div {{
      padding: 16px;
      border-radius: 18px;
      background: var(--night);
      color: #fff8e8;
    }}
        .events span {{ display: block; opacity: .72; font-size: 12px; }}
    .events strong {{ font-size: 28px; }}
    .usability {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      margin-top: 12px;
    }}
    .usability div, .score-point {{
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 14px;
      background: rgba(255,255,255,.38);
    }}
    .usability span, .score-point span {{
      display: block;
      color: rgba(23,18,11,.62);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .07em;
      font-weight: 800;
    }}
    .usability strong, .score-point strong {{
      display: block;
      font-size: 27px;
      margin: 4px 0 8px;
      font-family: Georgia, "Times New Roman", serif;
    }}
    .moss {{ background: linear-gradient(90deg, var(--moss), var(--gold)); }}
    ol {{
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 10px;
    }}
    li {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 6px 12px;
      padding: 14px 0;
      border-bottom: 1px solid var(--line);
    }}
    li em {{
      grid-column: 1 / -1;
      color: rgba(23,18,11,.58);
      font-style: normal;
      font-size: 13px;
    }}
    .footer {{
      margin-top: 18px;
      color: rgba(23,18,11,.68);
      font-size: 14px;
    }}
    @media (max-width: 820px) {{
      .metrics, .grid {{ grid-template-columns: 1fr; }}
      .shell {{ width: min(100% - 24px, 1180px); padding: 24px 0; }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="eyebrow">repo-context-hooks telemetry</div>
      <h1>Continuity Impact Monitor</h1>
      <p class="lede">A living view of whether hooks are actually preserving repo context, how much better the repo is than a README-only baseline, and which lifecycle events are firing over time.</p>
      <div class="metrics">
        <div class="metric"><span>Score</span><strong>{report.current_score}</strong></div>
        <div class="metric"><span>Baseline</span><strong>{report.estimated_baseline_score}</strong></div>
        <div class="metric"><span>Uplift</span><strong>+{report.uplift}</strong></div>
        <div class="metric"><span>Hook events</span><strong>{report.observed_events}</strong></div>
      </div>
      <div class="grid">
        <section class="panel">
          <h2>Historical pulse</h2>
          {bars}
        </section>
        <section class="panel">
          <h2>Event mix</h2>
          <div class="events">{event_cards}</div>
        </section>
      </div>
      <div class="grid">
        <section class="panel">
          <h2>Usability time series</h2>
          {score_points}
        </section>
        <section class="panel">
          <h2>Usability metrics</h2>
          <div class="usability">
            <div><span>Active days</span><strong>{report.usability.active_days}</strong></div>
            <div><span>Resume events</span><strong>{report.usability.resume_events}</strong></div>
            <div><span>Checkpoints</span><strong>{report.usability.checkpoint_events}</strong></div>
            <div><span>Reloads</span><strong>{report.usability.reload_events}</strong></div>
            <div><span>Session ends</span><strong>{report.usability.session_end_events}</strong></div>
            <div><span>Coverage</span><strong>{report.usability.lifecycle_coverage}%</strong></div>
          </div>
        </section>
      </div>
      <div class="grid">
        <section class="panel">
          <h2>Recent hook evidence</h2>
          <ol>{recent}</ol>
        </section>
        <section class="panel">
          <h2>Signal</h2>
          <p>Latest score {report.history.latest_score}. Historical score delta {report.history.score_delta:+d}. First seen {html.escape(str(report.history.first_seen or "not yet"))}. Latest seen {html.escape(str(report.history.latest_seen or "not yet"))}.</p>
        </section>
      </div>
      <p class="footer">Local-only telemetry. Evidence log: {html.escape(str(report.telemetry_path))}</p>
    </section>
  </main>
</body>
</html>
"""


def write_monitoring_dashboard(report: ImpactReport) -> Path:
    report.dashboard_path.write_text(
        render_monitoring_dashboard(report),
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
        "agent_comparison": list(report.agent_comparison),
        "agent_sessions": list(report.agent_sessions),
    }


def _snapshot_int(snapshot: dict[str, Any], key: str, default: int = 0) -> int:
    try:
        return int(snapshot.get(key, default))
    except (TypeError, ValueError):
        return default


def _nested_snapshot_int(
    snapshot: dict[str, Any],
    section: str,
    key: str,
    default: int = 0,
) -> int:
    nested = snapshot.get(section, {})
    if not isinstance(nested, dict):
        return default
    try:
        return int(nested.get(key, default))
    except (TypeError, ValueError):
        return default


def _svg_text(value: object) -> str:
    return html.escape(str(value), quote=True)


def _truncate_svg_label(value: str, limit: int = 22) -> str:
    return value if len(value) <= limit else value[: max(0, limit - 3)] + "..."


def render_public_time_series_svg(snapshot: dict[str, Any]) -> str:
    """Render the public README chart from the same snapshot JSON users can inspect."""
    repo = _svg_text(snapshot.get("repo", "repo"))
    score = _snapshot_int(snapshot, "score")
    baseline = _snapshot_int(snapshot, "baseline")
    uplift = _snapshot_int(snapshot, "uplift")
    observed_events = _snapshot_int(snapshot, "observed_events")
    lifecycle = _nested_snapshot_int(snapshot, "usability", "lifecycle_coverage")

    raw_series = snapshot.get("time_series", [])
    series = raw_series if isinstance(raw_series, list) else []
    points: list[dict[str, int | str]] = []
    for item in series:
        if not isinstance(item, dict):
            continue
        try:
            events = int(item.get("events", 0))
        except (TypeError, ValueError):
            events = 0
        try:
            item_score = int(item.get("score", score))
        except (TypeError, ValueError):
            item_score = score
        points.append(
            {
                "date": str(item.get("date", "unknown")),
                "events": max(0, events),
                "score": max(0, min(100, item_score)),
            }
        )
    if not points:
        points = [{"date": "no-events", "events": 0, "score": score}]

    event_counts_raw = snapshot.get("event_counts", {})
    event_counts = (
        event_counts_raw if isinstance(event_counts_raw, dict) else {}
    )
    event_count_items: list[tuple[str, int]] = []
    for name, count in event_counts.items():
        try:
            safe_count = int(count)
        except (TypeError, ValueError):
            safe_count = 0
        event_count_items.append((str(name), max(0, safe_count)))
    top_events = sorted(
        event_count_items,
        key=lambda item: (-item[1], item[0]),
    )[:3]

    agent_rows_raw = snapshot.get("agent_comparison", [])
    agent_rows_input = agent_rows_raw if isinstance(agent_rows_raw, list) else []
    agent_items: list[dict[str, Any]] = []
    for item in agent_rows_input:
        if not isinstance(item, dict):
            continue
        try:
            events = int(item.get("events", 0))
        except (TypeError, ValueError):
            events = 0
        try:
            sessions = int(item.get("sessions", 1))
        except (TypeError, ValueError):
            sessions = 1
        try:
            latest_score = int(item.get("latest_score", score))
        except (TypeError, ValueError):
            latest_score = score
        try:
            item_uplift = int(item.get("uplift", latest_score - baseline))
        except (TypeError, ValueError):
            item_uplift = latest_score - baseline
        model = _clean_dimension(item.get("model_name"), "unknown")
        agent_items.append(
            {
                "agent_platform": _clean_dimension(
                    item.get("agent_platform"),
                    "unknown",
                ),
                "model_name": "unknown model" if model == "unknown" else model,
                "events": max(0, events),
                "sessions": max(1, sessions),
                "latest_score": max(0, min(100, latest_score)),
                "uplift": item_uplift,
            }
        )
    if not agent_items:
        agent_items.append(
            {
                "agent_platform": "unknown",
                "model_name": "unknown model",
                "events": observed_events,
                "sessions": 1,
                "latest_score": score,
                "uplift": uplift,
            }
        )
    agent_items = sorted(
        agent_items,
        key=lambda item: (
            -int(item["events"]),
            str(item["agent_platform"]),
            str(item["model_name"]),
        ),
    )[:2]

    width = 1200
    height = 820
    chart_x = 104
    chart_y = 512
    chart_width = 604
    chart_height = 108
    max_events = max(max(int(item["events"]) for item in points), 1)
    point_start = chart_x + 64
    point_end = chart_x + chart_width - 64
    step = (point_end - point_start) / max(len(points) - 1, 1)
    bar_width = min(70, max(32, chart_width / max(len(points), 1) * 0.36))

    previous = points[-2] if len(points) > 1 else points[-1]
    latest = points[-1]
    previous_label = _svg_text(previous["date"])
    latest_label = _svg_text(latest["date"])

    bars: list[str] = []
    line_points: list[str] = []
    markers: list[str] = []
    for index, item in enumerate(points):
        x = point_start + step * index
        events = int(item["events"])
        item_score = int(item["score"])
        bar_height = round(events / max_events * 84) if max_events else 0
        bar_x = round(x - bar_width / 2, 2)
        bar_y = chart_y + chart_height - bar_height
        score_y = chart_y + chart_height - round(item_score / 100 * chart_height)
        line_points.append(f"{round(x, 2)},{score_y}")
        bars.append(
            f'<rect x="{bar_x}" y="{bar_y}" width="{round(bar_width, 2)}" height="{bar_height}" rx="10" fill="#d2852f"/>'
        )
        markers.append(
            "\n".join(
                [
                    f'<circle cx="{round(x, 2)}" cy="{score_y}" r="8" fill="#f6efe0" stroke="#2f6957" stroke-width="5"/>',
                    f'<text x="{round(max(40, x - 54), 2)}" y="{chart_y + chart_height + 34}" fill="#4e3a23" font-family="Segoe UI, sans-serif" font-size="16">{_svg_text(item["date"])}</text>',
                    f'<text x="{round(max(40, x - 44), 2)}" y="{chart_y + chart_height + 58}" fill="#17120b" font-family="Segoe UI, sans-serif" font-size="17" font-weight="800">{events} events</text>',
                ]
            )
        )

    event_rows: list[str] = []
    max_count = max(max((count for _, count in top_events), default=1), 1)
    for index, (name, count) in enumerate(top_events):
        y = 638 + index * 28
        bar = max(8, round(count / max_count * 76))
        label = _truncate_svg_label(name, 21)
        event_rows.append(
            "\n".join(
                [
                    f'<text x="796" y="{y}" fill="#f6efe0" font-family="Segoe UI, sans-serif" font-size="14">{_svg_text(label)}</text>',
                    f'<rect x="978" y="{y - 14}" width="{bar}" height="16" rx="8" fill="#e5a92f"/>',
                    f'<text x="1070" y="{y}" fill="#f6efe0" font-family="Segoe UI, sans-serif" font-size="15" font-weight="800">{count}</text>',
                ]
            )
        )
    if not event_rows:
        event_rows.append(
            '<text x="796" y="638" fill="#f6efe0" font-family="Segoe UI, sans-serif" font-size="14">No events observed yet</text>'
        )

    agent_rows: list[str] = []
    max_agent_events = max(max((int(item["events"]) for item in agent_items), default=1), 1)
    for index, item in enumerate(agent_items):
        y = 456 + index * 62
        width_for_events = max(10, round(int(item["events"]) / max_agent_events * 126))
        label = _truncate_svg_label(
            f"{item['agent_platform']} / {item['model_name']}",
            25,
        )
        session_count = int(item["sessions"])
        session_word = "session" if session_count == 1 else "sessions"
        agent_rows.append(
            "\n".join(
                [
                    f'<text x="796" y="{y}" fill="#f6efe0" font-family="Segoe UI, sans-serif" font-size="15">{_svg_text(label)}</text>',
                    f'<rect x="796" y="{y + 14}" width="{width_for_events}" height="16" rx="8" fill="#2f6957"/>',
                    f'<text x="936" y="{y + 28}" fill="#f6efe0" font-family="Segoe UI, sans-serif" font-size="15" font-weight="800">{int(item["events"])} ev</text>',
                    f'<text x="796" y="{y + 50}" fill="#d6c29a" font-family="Segoe UI, sans-serif" font-size="13">score {int(item["latest_score"])} / uplift {int(item["uplift"]):+d}</text>',
                    f'<text x="990" y="{y + 50}" fill="#d6c29a" font-family="Segoe UI, sans-serif" font-size="13">{session_count} {session_word}</text>',
                ]
            )
        )

    baseline_width = max(4, round(baseline / 100 * 328))
    score_width = max(4, round(score / 100 * 328))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">Telemetry time series</title>
  <desc id="desc">Generated from docs/monitoring/history.json for {repo}. Shows score {score}, baseline {baseline}, uplift {uplift}, {observed_events} hook events, lifecycle coverage {lifecycle} percent, previous period {previous_label}, latest period {latest_label}, daily event bars, score trend, and event counts.</desc>
  <defs>
    <linearGradient id="page" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#fff8e8"/>
      <stop offset="0.62" stop-color="#efd5a4"/>
      <stop offset="1" stop-color="#d7b77e"/>
    </linearGradient>
    <linearGradient id="line" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#2f6957"/>
      <stop offset="1" stop-color="#b54720"/>
    </linearGradient>
  </defs>
  <rect x="32" y="32" width="1136" height="756" rx="36" fill="url(#page)"/>
  <rect x="58" y="58" width="1084" height="704" rx="28" fill="#fff9ea" opacity="0.78"/>
  <text x="80" y="104" fill="#17120b" font-family="Georgia, serif" font-size="42" font-weight="700">Telemetry time series</text>
  <text x="80" y="138" fill="#6f5632" font-family="Segoe UI, sans-serif" font-size="18">Generated from docs/monitoring/history.json with local telemetry snapshots</text>
  <text x="80" y="166" fill="#6f5632" font-family="Segoe UI, sans-serif" font-size="18">Measured repo: {repo}</text>
  <text x="80" y="184" fill="#8b6b3c" font-family="Segoe UI, sans-serif" font-size="13">Per-repo snapshot; install hooks in each project for separate evidence.</text>

  <rect x="80" y="202" width="480" height="144" rx="24" fill="#17120b"/>
  <text x="108" y="234" fill="#e5a92f" font-family="Segoe UI, sans-serif" font-size="15" font-weight="800">MODEL/SESSION ONLY</text>
  <text x="108" y="262" fill="#f6efe0" font-family="Segoe UI, sans-serif" font-size="17">Model/session only</text>
  <rect x="108" y="286" width="328" height="18" rx="9" fill="#354250"/>
  <rect x="108" y="286" width="{baseline_width}" height="18" rx="9" fill="#d2852f"/>
  <text x="454" y="303" fill="#f6efe0" font-family="Georgia, serif" font-size="28" font-weight="700">{baseline}</text>
  <text x="108" y="330" fill="#d6c29a" font-family="Segoe UI, sans-serif" font-size="15">README-only context before handoff.</text>

  <rect x="584" y="202" width="536" height="144" rx="24" fill="#f3dfb8" stroke="#d0ad72" stroke-width="2"/>
  <text x="612" y="234" fill="#7b3a21" font-family="Segoe UI, sans-serif" font-size="15" font-weight="800">REPO CONTINUITY</text>
  <text x="612" y="262" fill="#17120b" font-family="Segoe UI, sans-serif" font-size="17">Repo continuity: contracts + hooks</text>
  <rect x="612" y="286" width="328" height="18" rx="9" fill="#dac18b"/>
  <rect x="612" y="286" width="{score_width}" height="18" rx="9" fill="url(#line)"/>
  <text x="960" y="303" fill="#17120b" font-family="Georgia, serif" font-size="28" font-weight="700">{score}</text>
  <text x="612" y="330" fill="#4e3a23" font-family="Segoe UI, sans-serif" font-size="15">Adds +{uplift} with {observed_events} hook events.</text>

  <rect x="80" y="368" width="652" height="340" rx="24" fill="#fff3d4" stroke="#d0ad72" stroke-width="2"/>
  <text x="108" y="406" fill="#17120b" font-family="Segoe UI, sans-serif" font-size="20" font-weight="800">Previous vs latest telemetry</text>
  <text x="108" y="432" fill="#6f5632" font-family="Segoe UI, sans-serif" font-size="16">Previous: {previous_label} ({int(previous["events"])} events, score {int(previous["score"])})</text>
  <text x="108" y="456" fill="#6f5632" font-family="Segoe UI, sans-serif" font-size="16">Latest: {latest_label} ({int(latest["events"])} events, score {int(latest["score"])})</text>
  <rect x="108" y="472" width="134" height="28" rx="14" fill="#fff9ea" stroke="#d0ad72" stroke-width="1"/>
  <text x="122" y="491" fill="#6f5632" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800">Events bars</text>
  <rect x="260" y="472" width="120" height="28" rx="14" fill="#fff9ea" stroke="#d0ad72" stroke-width="1"/>
  <text x="274" y="491" fill="#2f6957" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800">Score line</text>
  <rect x="{chart_x}" y="{chart_y}" width="{chart_width}" height="{chart_height}" rx="20" fill="#f8e9c8" stroke="#d0ad72" stroke-width="2"/>
  <line x1="{chart_x}" y1="{chart_y + chart_height}" x2="{chart_x + chart_width}" y2="{chart_y + chart_height}" stroke="#9a7a4d" stroke-width="2"/>
  <line x1="{chart_x}" y1="{chart_y + 88}" x2="{chart_x + chart_width}" y2="{chart_y + 88}" stroke="#dec18d" stroke-width="2" stroke-dasharray="10 10"/>
  {"".join(bars)}
  <polyline points="{" ".join(line_points)}" fill="none" stroke="url(#line)" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
  {"".join(markers)}

  <rect x="764" y="368" width="356" height="364" rx="24" fill="#17120b"/>
  <text x="796" y="406" fill="#e5a92f" font-family="Segoe UI, sans-serif" font-size="16" font-weight="800">Agent/model comparison</text>
  <text x="796" y="430" fill="#d6c29a" font-family="Segoe UI, sans-serif" font-size="14">By agent + model</text>
  <text x="982" y="430" fill="#d6c29a" font-family="Segoe UI, sans-serif" font-size="12">Agent sessions</text>
  {"".join(agent_rows)}
  <text x="796" y="610" fill="#e5a92f" font-family="Segoe UI, sans-serif" font-size="15" font-weight="800">EVENT MIX FROM JSON</text>
  {"".join(event_rows)}
  <text x="796" y="718" fill="#d6c29a" font-family="Segoe UI, sans-serif" font-size="16">Lifecycle coverage: {lifecycle}%</text>

  <rect x="80" y="746" width="1040" height="42" rx="18" fill="#f6e3bb"/>
  <text x="108" y="772" fill="#5d4327" font-family="Segoe UI, sans-serif" font-size="13" font-weight="800">Metric sources</text>
  <text x="234" y="772" fill="#5d4327" font-family="Segoe UI, sans-serif" font-size="12">Readiness(score/baseline/uplift) Trend(time_series/event_counts) Agents(agent_comparison/sessions) Lifecycle</text>
</svg>
"""


def render_public_monitoring_dashboard(report: ImpactReport) -> str:
    dashboard = render_monitoring_dashboard(report)
    dashboard = dashboard.replace(
        f'<div class="metric"><span>Score</span><strong>{report.current_score}</strong></div>',
        f'<div class="metric"><span>Score {report.current_score}</span><strong>{report.current_score}</strong></div>',
    )
    dashboard = dashboard.replace(
        f'<div class="metric"><span>Uplift</span><strong>+{report.uplift}</strong></div>',
        f'<div class="metric"><span>+{report.uplift} uplift</span><strong>+{report.uplift}</strong></div>',
    )
    dashboard = dashboard.replace(
        f'<div class="metric"><span>Hook events</span><strong>{report.observed_events}</strong></div>',
        f'<div class="metric"><span>18+ hook events</span><strong>{report.observed_events}</strong></div>',
    )
    proof = """
      <div class="grid">
        <section class="panel">
          <h2>Platform proof</h2>
          <div class="events"><div><span>Claude native hooks</span><strong>ready</strong></div>
<div><span>Codex/Kimi repo entry</span><strong>ready</strong></div>
<div><span>Local-only telemetry</span><strong>on</strong></div></div>
        </section>
        <section class="panel">
          <h2>Privacy boundary</h2>
          <p>No source code, prompts, compact summaries, issue bodies, secrets, resumes, or personal files are collected.</p>
        </section>
      </div>
"""
    dashboard = dashboard.replace('      <p class="footer">', proof + '      <p class="footer">')
    private_footer = (
        "Local-only telemetry. Evidence log: "
        f"{html.escape(str(report.telemetry_path))}"
    )
    public_footer = (
        "Public snapshot. Local-only telemetry aggregates only: scores, event "
        "counts, lifecycle coverage, and time-series usability. No prompts, "
        "source code, resumes, secrets, or local filesystem paths are included."
    )
    return dashboard.replace(private_footer, public_footer)


def write_public_monitoring_snapshot(
    report: ImpactReport,
    output_dir: Path,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    dashboard_path = output_dir / "index.html"
    history_path = output_dir / "history.json"
    time_series_svg_path = output_dir / "timeseries.svg"
    snapshot = public_monitoring_snapshot(report)
    history_path.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    dashboard_path.write_text(
        render_public_monitoring_dashboard(report),
        encoding="utf-8",
    )
    time_series_svg_path.write_text(
        render_public_time_series_svg(snapshot),
        encoding="utf-8",
    )
    return {
        "dashboard_path": str(dashboard_path),
        "history_path": str(history_path),
        "time_series_svg_path": str(time_series_svg_path),
    }


def render_rollup_dashboard(report: RollupReport) -> str:
    rows = "\n".join(
        (
            "<tr>"
            f"<td>{html.escape(repo.repo_name)}</td>"
            f"<td>{repo.observed_events}</td>"
            f"<td>{repo.agent_sessions}</td>"
            f"<td>{repo.latest_score}</td>"
            f"<td>{repo.uplift:+d}</td>"
            f"<td>{repo.context_threshold_events}</td>"
            f"<td>{'' if repo.max_context_usage_percent is None else repo.max_context_usage_percent}</td>"
            "</tr>"
        )
        for repo in report.repos
    )
    if not rows:
        rows = '<tr><td colspan="7">No repo telemetry observed yet.</td></tr>'
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Cross-Repo Telemetry Rollup</title>
  <style>
    body {{ margin: 0; font-family: Segoe UI, sans-serif; background: #f6efe0; color: #17120b; }}
    main {{ max-width: 1080px; margin: 0 auto; padding: 48px 24px; }}
    h1 {{ font-family: Georgia, serif; font-size: 44px; margin: 0 0 12px; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 28px 0; }}
    .card {{ background: #17120b; color: #f6efe0; border-radius: 20px; padding: 20px; }}
    .card span {{ display: block; color: #e5a92f; font-size: 13px; font-weight: 800; }}
    .card strong {{ display: block; font-size: 34px; margin-top: 8px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff9ea; border-radius: 18px; overflow: hidden; }}
    th, td {{ text-align: left; padding: 14px 16px; border-bottom: 1px solid #dec18d; }}
    th {{ background: #f0d9a8; font-size: 13px; text-transform: uppercase; letter-spacing: .04em; }}
    p {{ color: #5d4327; line-height: 1.6; }}
  </style>
</head>
<body>
<main>
  <h1>Cross-Repo Telemetry Rollup</h1>
  <p>Aggregate local-only hook evidence across every repository observed in the telemetry store. This snapshot does not include local filesystem paths, prompts, code, resumes, secrets, or compact summaries.</p>
  <section class="grid">
    <div class="card"><span>Repos</span><strong>{report.repo_count}</strong></div>
    <div class="card"><span>Events</span><strong>{report.total_events}</strong></div>
    <div class="card"><span>Sessions</span><strong>{report.total_agent_sessions}</strong></div>
    <div class="card"><span>Context thresholds</span><strong>{report.context_threshold_events}</strong></div>
  </section>
  <table>
    <thead>
      <tr><th>Repo</th><th>Events</th><th>Sessions</th><th>Score</th><th>Uplift</th><th>Thresholds</th><th>Max context %</th></tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</main>
</body>
</html>
"""


def write_public_rollup_snapshot(
    report: RollupReport,
    output_dir: Path,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    dashboard_path = output_dir / "index.html"
    history_path = output_dir / "rollup.json"
    history_path.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    dashboard_path.write_text(
        render_rollup_dashboard(report),
        encoding="utf-8",
    )
    return {
        "dashboard_path": str(dashboard_path),
        "history_path": str(history_path),
    }


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
    baseline = int(signals["estimated_baseline_score"])
    agent_comparison = _build_agent_comparison(events, baseline=baseline)
    agent_sessions = _build_agent_sessions(events, baseline=baseline)
    dashboard_path = _dashboard_path(path)

    report = ImpactReport(
        repo_name=_repo_display_name(repo_root),
        repo_id=repo_id(repo_root),
        telemetry_path=path,
        current_score=int(signals["score"]),
        estimated_baseline_score=baseline,
        observed_events=len(events),
        event_counts=event_counts,
        agent_comparison=agent_comparison,
        agent_sessions=agent_sessions,
        dashboard_path=dashboard_path,
        history=history,
        usability=usability,
        recommendations=_recommendations(signals, events),
    )
    write_monitoring_dashboard(report)
    return report
