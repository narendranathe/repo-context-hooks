from __future__ import annotations

import datetime as dt
import hashlib
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
class ImpactReport:
    repo_name: str
    repo_id: str
    telemetry_path: Path
    current_score: int
    estimated_baseline_score: int
    observed_events: int
    event_counts: dict[str, int]
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
        ]
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


def measure_impact(repo_root: Path, telemetry_base: Path | None = None) -> ImpactReport:
    repo_root = repo_root.resolve()
    signals = contract_signals(repo_root)
    path = telemetry_events_path(repo_root, base=telemetry_base)
    events = _read_events(path)
    event_counts: dict[str, int] = {}
    for event in events:
        name = str(event.get("event_name", "unknown"))
        event_counts[name] = event_counts.get(name, 0) + 1

    return ImpactReport(
        repo_name=repo_root.name,
        repo_id=repo_id(repo_root),
        telemetry_path=path,
        current_score=int(signals["score"]),
        estimated_baseline_score=int(signals["estimated_baseline_score"]),
        observed_events=len(events),
        event_counts=event_counts,
        recommendations=_recommendations(signals, events),
    )
