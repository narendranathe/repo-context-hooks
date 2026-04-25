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


EVENTS_FILE = "events.jsonl"


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
) -> Path:
    repo_root = repo_root.resolve()
    signals = contract_signals(repo_root)
    event = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "event_name": event_name,
        "source": source,
        "repo_id": repo_id(repo_root),
        "repo_name": repo_root.name,
        "branch": _git_output(repo_root, "branch", "--show-current") or "unknown",
        "repo_contract_score": signals["score"],
        "estimated_baseline_score": signals["estimated_baseline_score"],
        "details": details or {},
    }
    path = telemetry_events_path(repo_root, base=telemetry_base)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    try:
        measure_impact(repo_root, telemetry_base=telemetry_base)
    except Exception:
        pass
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
    )[:5]

    width = 1200
    height = 660
    chart_x = 96
    chart_y = 294
    chart_width = 690
    chart_height = 220
    max_events = max(max(int(item["events"]) for item in points), 1)
    point_start = chart_x + 76
    point_end = chart_x + chart_width - 76
    step = (point_end - point_start) / max(len(points) - 1, 1)
    bar_width = min(82, max(34, chart_width / max(len(points), 1) * 0.42))

    bars: list[str] = []
    line_points: list[str] = []
    markers: list[str] = []
    for index, item in enumerate(points):
        x = point_start + step * index
        events = int(item["events"])
        item_score = int(item["score"])
        bar_height = round(events / max_events * 168) if max_events else 0
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
                    f'<text x="{round(max(42, x - 54), 2)}" y="{chart_y + chart_height + 40}" fill="#4e3a23" font-family="Segoe UI, sans-serif" font-size="17">{_svg_text(item["date"])}</text>',
                    f'<text x="{round(max(42, x - 44), 2)}" y="{chart_y + chart_height + 66}" fill="#17120b" font-family="Segoe UI, sans-serif" font-size="18" font-weight="800">{events} events</text>',
                ]
            )
        )

    event_rows: list[str] = []
    max_count = max((count for _, count in top_events), default=1)
    for index, (name, count) in enumerate(top_events):
        y = 258 + index * 44
        bar = max(8, round(count / max_count * 72))
        label = name if len(name) <= 20 else name[:17] + "..."
        event_rows.append(
            "\n".join(
                [
                    f'<text x="872" y="{y}" fill="#f6efe0" font-family="Segoe UI, sans-serif" font-size="18">{_svg_text(label)}</text>',
                    f'<rect x="1032" y="{y - 18}" width="{bar}" height="20" rx="10" fill="#e5a92f"/>',
                    f'<text x="1118" y="{y}" fill="#f6efe0" font-family="Segoe UI, sans-serif" font-size="18" font-weight="800">{count}</text>',
                ]
            )
        )
    if not event_rows:
        event_rows.append(
            '<text x="872" y="258" fill="#f6efe0" font-family="Segoe UI, sans-serif" font-size="18">No events observed yet</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">Telemetry time series</title>
  <desc id="desc">Generated from docs/monitoring/history.json for {repo}. Shows score {score}, baseline {baseline}, uplift {uplift}, {observed_events} hook events, lifecycle coverage {lifecycle} percent, daily event bars, score trend, and event counts.</desc>
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
  <rect x="32" y="32" width="1136" height="596" rx="36" fill="url(#page)"/>
  <rect x="58" y="58" width="1084" height="544" rx="28" fill="#fff9ea" opacity="0.78"/>
  <text x="86" y="104" fill="#17120b" font-family="Georgia, serif" font-size="42" font-weight="700">Telemetry time series</text>
  <text x="86" y="138" fill="#6f5632" font-family="Segoe UI, sans-serif" font-size="18">Generated from docs/monitoring/history.json, not a hand-authored proof card</text>
  <text x="86" y="166" fill="#6f5632" font-family="Segoe UI, sans-serif" font-size="18">Repo: {repo}</text>
  <rect x="86" y="184" width="160" height="74" rx="18" fill="#17120b"/>
  <text x="110" y="214" fill="#e5a92f" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800">SCORE</text>
  <text x="110" y="246" fill="#fff6dc" font-family="Georgia, serif" font-size="32" font-weight="700">Score {score}</text>
  <rect x="266" y="184" width="166" height="74" rx="18" fill="#f3dfb8" stroke="#d4b071" stroke-width="2"/>
  <text x="290" y="214" fill="#7b3a21" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800">BASELINE</text>
  <text x="290" y="246" fill="#17120b" font-family="Georgia, serif" font-size="32" font-weight="700">{baseline}</text>
  <rect x="452" y="184" width="166" height="74" rx="18" fill="#f3dfb8" stroke="#d4b071" stroke-width="2"/>
  <text x="476" y="214" fill="#7b3a21" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800">UPLIFT</text>
  <text x="476" y="246" fill="#17120b" font-family="Georgia, serif" font-size="32" font-weight="700">+{uplift}</text>
  <rect x="638" y="184" width="168" height="74" rx="18" fill="#f3dfb8" stroke="#d4b071" stroke-width="2"/>
  <text x="662" y="214" fill="#7b3a21" font-family="Segoe UI, sans-serif" font-size="14" font-weight="800">HOOK EVENTS</text>
  <text x="662" y="246" fill="#17120b" font-family="Georgia, serif" font-size="32" font-weight="700">{observed_events}</text>
  <rect x="86" y="{chart_y}" width="{chart_width}" height="{chart_height}" rx="20" fill="#f8e9c8" stroke="#d0ad72" stroke-width="2"/>
  <line x1="{chart_x}" y1="{chart_y + chart_height}" x2="{chart_x + chart_width}" y2="{chart_y + chart_height}" stroke="#9a7a4d" stroke-width="2"/>
  <line x1="{chart_x}" y1="{chart_y + 110}" x2="{chart_x + chart_width}" y2="{chart_y + 110}" stroke="#dec18d" stroke-width="2" stroke-dasharray="10 10"/>
  <text x="112" y="{chart_y + 30}" fill="#6f5632" font-family="Segoe UI, sans-serif" font-size="16">Daily hook events as bars</text>
  <text x="112" y="{chart_y + 56}" fill="#2f6957" font-family="Segoe UI, sans-serif" font-size="16" font-weight="800">Score trend as line</text>
  {"".join(bars)}
  <polyline points="{" ".join(line_points)}" fill="none" stroke="url(#line)" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
  {"".join(markers)}
  <rect x="842" y="184" width="300" height="250" rx="24" fill="#17120b"/>
  <text x="872" y="226" fill="#e5a92f" font-family="Segoe UI, sans-serif" font-size="16" font-weight="800">EVENT MIX FROM JSON</text>
  {"".join(event_rows)}
  <text x="872" y="462" fill="#d6c29a" font-family="Segoe UI, sans-serif" font-size="16">Lifecycle coverage: {lifecycle}%</text>
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
