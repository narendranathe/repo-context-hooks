from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .platforms import get_registry


@dataclass(frozen=True)
class DoctorReport:
    platform_id: str
    ok: bool
    present: tuple[str, ...]
    missing: tuple[str, ...]
    invalid: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def render(self) -> str:
        if self.ok:
            status = "OK"
        elif self.invalid:
            status = "INVALID"
        else:
            status = "MISSING"
        lines = [f"[{status}] {self.platform_id}"]
        lines.extend(f"present: {item}" for item in self.present)
        lines.extend(f"missing: {item}" for item in self.missing)
        lines.extend(f"invalid: {item}" for item in self.invalid)
        lines.extend(f"warning: {item}" for item in self.warnings)
        return "\n".join(lines)


def _required_markers(path: Path) -> tuple[str, ...]:
    if path.name == "AGENTS.md":
        return (
            "README.md",
            "specs/README.md",
            "repo as the continuity source of truth",
        )
    if path.name == "repo-context-continuity.mdc":
        return (
            "README.md",
            "specs/README.md",
            "AGENTS.md",
        )
    if path.name == "replit.md":
        return (
            "README.md",
            "specs/README.md",
            "AGENTS.md",
        )
    if path.name == "repo-context-continuity.md":
        return (
            "README.md",
            "specs/README.md",
            "AGENTS.md",
        )
    if path.name == "project-knowledge.md":
        return (
            "README.md",
            "specs/README.md",
            "AGENTS.md",
        )
    if path.name == "workspace-knowledge.md":
        return (
            "AGENTS.md",
            "default branch",
        )
    if path.name in ("SOUL.md", "USER.md", "TOOLS.md"):
        return (
            "repo as the continuity source of truth",
            "README.md",
            "specs/README.md",
            "AGENTS.md",
        )
    if path.name == "Modelfile.repo-context":
        return (
            "FROM",
            "SYSTEM",
            "repo as the continuity source of truth",
            "README.md",
            "specs/README.md",
            "AGENTS.md",
        )
    if path.name == "settings.json":
        return (
            "SessionStart",
            "PreCompact",
            "PostCompact",
            "SessionEnd",
        )
    return ()


def _matches_expected_markers(path: Path) -> bool:
    markers = _required_markers(path)
    if not markers or not path.is_file():
        return True
    text = path.read_text(encoding="utf-8", errors="ignore")
    return all(marker in text for marker in markers)


def diagnose_platform(
    platform: str,
    repo_root: Path,
    home: Path | None = None,
) -> DoctorReport:
    adapter = get_registry().get(platform)
    plan = adapter.build_install_plan(repo_root=repo_root, home=home)

    present: list[str] = []
    missing: list[str] = []
    invalid: list[str] = []
    for item in (*plan.home_paths, *plan.repo_paths):
        path = Path(item)
        if not path.exists():
            missing.append(item)
            continue
        if _matches_expected_markers(path):
            present.append(item)
        else:
            invalid.append(item)

    return DoctorReport(
        platform_id=platform,
        ok=not missing and not invalid,
        present=tuple(present),
        missing=tuple(missing),
        invalid=tuple(invalid),
        warnings=plan.warnings,
    )
