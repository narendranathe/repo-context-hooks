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

    def to_dict(self) -> dict[str, object]:
        if self.ok:
            status = "ok"
        elif self.invalid:
            status = "invalid"
        else:
            status = "missing"
        return {
            "platform_id": self.platform_id,
            "ok": self.ok,
            "status": status,
            "present": list(self.present),
            "missing": list(self.missing),
            "invalid": list(self.invalid),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class PlatformReadinessRow:
    platform_id: str
    support_tier: str
    state: str
    detail: str = "-"
    warnings: tuple[str, ...] = ()

    @classmethod
    def from_report(
        cls,
        platform_id: str,
        support_tier: str,
        report: DoctorReport,
        repo_root: Path,
        home: Path | None = None,
    ) -> "PlatformReadinessRow":
        if report.invalid:
            state = "invalid"
            detail = _compact_detail(report.invalid[0], repo_root=repo_root, home=home)
        elif report.missing:
            state = "missing"
            detail = _compact_detail(report.missing[0], repo_root=repo_root, home=home)
        else:
            state = "ready"
            detail = (
                _compact_detail(report.present[0], repo_root=repo_root, home=home)
                if report.present
                else "-"
            )
        return cls(
            platform_id=platform_id,
            support_tier=support_tier,
            state=state,
            detail=detail,
            warnings=report.warnings,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "platform_id": self.platform_id,
            "support_tier": self.support_tier,
            "state": self.state,
            "detail": self.detail,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class AllPlatformsReport:
    ok: bool
    repo_contract: DoctorReport
    rows: tuple[PlatformReadinessRow, ...]

    def render(self) -> str:
        status = "OK" if self.ok else "INVALID"
        repo_state = "ok"
        if self.repo_contract.invalid:
            repo_state = "invalid"
        elif self.repo_contract.missing:
            repo_state = "missing"

        repo_detail = "-"
        if self.repo_contract.invalid:
            repo_detail = self.repo_contract.invalid[0]
        elif self.repo_contract.missing:
            repo_detail = self.repo_contract.missing[0]

        lines = [f"[{status}] platform-readiness", f"repo-contract\t{repo_state}\t{repo_detail}"]
        lines.extend(
            f"{row.platform_id}\t{row.support_tier}\t{row.state}\t{row.detail}"
            for row in self.rows
        )
        lines.extend(
            f"warning[{row.platform_id}]: {warning}"
            for row in self.rows
            for warning in row.warnings
        )
        return "\n".join(lines)

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "repo_contract": self.repo_contract.to_dict(),
            "platforms": [row.to_dict() for row in self.rows],
        }


def _compact_detail(item: str, repo_root: Path, home: Path | None = None) -> str:
    path = Path(item)
    if not path.is_absolute():
        return item.replace("\\", "/")

    if home is not None:
        try:
            return f"home:{path.relative_to(home.resolve()).as_posix()}"
        except ValueError:
            pass

    try:
        return f"repo:{path.relative_to(repo_root.resolve()).as_posix()}"
    except ValueError:
        return path.as_posix()


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


def _repo_contract_markers(path: Path) -> tuple[str, ...]:
    path_text = path.as_posix()
    if path_text.endswith("specs/README.md"):
        return (
            "## Repo Context Index",
            "## Architecture and Design Constraints",
            "## Open Issues and Next Work",
            "## How To Work in This Repo",
            "## Session Checkpoints",
        )
    if path.name == "README.md":
        return ()
    if path.name == "UBIQUITOUS_LANGUAGE.md":
        return (
            "# Ubiquitous Language",
            "## Terms",
        )
    return ()


def _matches_repo_contract_markers(path: Path) -> bool:
    if path.name == "README.md" and path.parent.name != "specs":
        return bool(path.read_text(encoding="utf-8", errors="ignore").strip())

    markers = _repo_contract_markers(path)
    if not markers or not path.is_file():
        return True
    text = path.read_text(encoding="utf-8", errors="ignore")
    return all(marker in text for marker in markers)


def diagnose_repo_contract(repo_root: Path) -> DoctorReport:
    repo_root = repo_root.resolve()
    required = (
        repo_root / "README.md",
        repo_root / "specs" / "README.md",
        repo_root / "UBIQUITOUS_LANGUAGE.md",
    )

    present: list[str] = []
    missing: list[str] = []
    invalid: list[str] = []
    warnings: list[str] = []

    for path in required:
        rel = path.relative_to(repo_root).as_posix()
        if not path.exists():
            missing.append(rel)
            continue
        if _matches_repo_contract_markers(path):
            present.append(rel)
        else:
            invalid.append(rel)

    agents = repo_root / "AGENTS.md"
    if agents.exists():
        if _matches_expected_markers(agents):
            present.append("AGENTS.md")
        else:
            warnings.append("AGENTS.md exists but does not clearly reference the repo contract.")
    else:
        warnings.append("AGENTS.md is recommended but currently missing.")

    return DoctorReport(
        platform_id="repo-contract",
        ok=not missing and not invalid,
        present=tuple(present),
        missing=tuple(missing),
        invalid=tuple(invalid),
        warnings=tuple(warnings),
    )


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


def diagnose_all_platforms(
    repo_root: Path,
    home: Path | None = None,
) -> AllPlatformsReport:
    repo_root = repo_root.resolve()
    repo_report = diagnose_repo_contract(repo_root)

    rows: list[PlatformReadinessRow] = []
    has_invalid_platform = False
    for adapter in get_registry().all():
        report = diagnose_platform(adapter.id, repo_root=repo_root, home=home)
        row = PlatformReadinessRow.from_report(
            platform_id=adapter.id,
            support_tier=adapter.support_tier.value,
            report=report,
            repo_root=repo_root,
            home=home,
        )
        if row.state == "invalid":
            has_invalid_platform = True
        rows.append(row)

    return AllPlatformsReport(
        ok=repo_report.ok and not has_invalid_platform,
        repo_contract=repo_report,
        rows=tuple(rows),
    )
