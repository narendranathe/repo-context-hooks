from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .doctor import diagnose_repo_contract
from .platforms import get_registry


@dataclass(frozen=True)
class Recommendation:
    platform_id: str
    score: int
    reasons: tuple[str, ...]
    signals: tuple[str, ...]
    next_command: str


@dataclass(frozen=True)
class RecommendationReport:
    repo_contract_ok: bool
    repo_contract_detail: str
    detected_signals: tuple[str, ...]
    recommendations: tuple[Recommendation, ...]
    preflight_commands: tuple[str, ...] = ()

    def render(self) -> str:
        lines = ["[RECOMMEND]"]
        repo_state = "ok" if self.repo_contract_ok else "attention-needed"
        lines.append(f"Repo contract: {repo_state} ({self.repo_contract_detail})")

        if self.detected_signals:
            lines.append("Detected signals:")
            lines.extend(f"- {signal}" for signal in self.detected_signals)
        else:
            lines.append("Detected signals:")
            lines.append("- none")

        if self.preflight_commands:
            lines.append("Before platform installs:")
            for index, command in enumerate(self.preflight_commands, start=1):
                lines.append(f"{index}. {command}")
            return "\n".join(lines)

        for index, recommendation in enumerate(self.recommendations, start=1):
            lines.append(f"{index}. {recommendation.platform_id}")
            for reason in recommendation.reasons:
                lines.append(f"   Why: {reason}")
            lines.append(f"   Next: {recommendation.next_command}")
        return "\n".join(lines)


_BASE_SCORES = {
    "native": 40,
    "partial": 20,
    "planned": 0,
}

_DEFAULT_BONUS = {
    "claude": 6,
    "codex": 4,
    "cursor": 3,
    "replit": 2,
    "windsurf": 2,
    "lovable": 2,
    "openclaw": 1,
    "ollama": 1,
    "kimi": 1,
}

_SIGNAL_RULES = {
    "claude": ((".claude/settings.json", "Detected repo signal: .claude/settings.json"),),
    "cursor": (
        (".cursor/rules/repo-context-continuity.mdc", "Detected repo signal: .cursor/rules/repo-context-continuity.mdc"),
        (".cursor", "Detected repo signal: .cursor/"),
    ),
    "codex": (
        (".codex", "Detected repo signal: .codex/"),
    ),
    "replit": (("replit.md", "Detected repo signal: replit.md"),),
    "windsurf": (
        (".windsurf/rules/repo-context-continuity.md", "Detected repo signal: .windsurf/rules/repo-context-continuity.md"),
        (".windsurf", "Detected repo signal: .windsurf/"),
    ),
    "lovable": (
        (".lovable/project-knowledge.md", "Detected repo signal: .lovable/project-knowledge.md"),
        (".lovable/workspace-knowledge.md", "Detected repo signal: .lovable/workspace-knowledge.md"),
        (".lovable", "Detected repo signal: .lovable/"),
    ),
    "openclaw": (
        ("SOUL.md", "Detected repo signal: SOUL.md"),
        ("USER.md", "Detected repo signal: USER.md"),
        ("TOOLS.md", "Detected repo signal: TOOLS.md"),
    ),
    "ollama": (("Modelfile.repo-context", "Detected repo signal: Modelfile.repo-context"),),
    "kimi": ((".kimi", "Detected repo signal: .kimi/"),),
}


def _path_exists(repo_root: Path, relative_path: str) -> bool:
    return (repo_root / relative_path).exists()


def _platform_signals(repo_root: Path, platform_id: str) -> tuple[str, ...]:
    signals: list[str] = []
    for relative_path, message in _SIGNAL_RULES.get(platform_id, ()):
        if _path_exists(repo_root, relative_path):
            signals.append(message)
    return tuple(signals)


def recommend_setup(repo_root: Path, limit: int = 3) -> RecommendationReport:
    repo_root = repo_root.resolve()
    repo_report = diagnose_repo_contract(repo_root)

    if not repo_report.ok:
        detail = "repo contract is missing or invalid"
        if repo_report.invalid:
            detail = f"invalid: {repo_report.invalid[0]}"
        elif repo_report.missing:
            detail = f"missing: {repo_report.missing[0]}"
        return RecommendationReport(
            repo_contract_ok=False,
            repo_contract_detail=detail,
            detected_signals=(),
            recommendations=(),
            preflight_commands=(
                "repo-context-hooks init --repo-root .",
                "repo-context-hooks doctor --repo-root .",
            ),
        )

    recommendations: list[Recommendation] = []
    all_detected_signals: list[str] = []
    for adapter in get_registry().all():
        signals = _platform_signals(repo_root, adapter.id)
        all_detected_signals.extend(signals)

        score = _BASE_SCORES[adapter.support_tier.value] + _DEFAULT_BONUS.get(adapter.id, 0)
        reasons = [f"{adapter.metadata.display_name} is {adapter.support_tier.value} support."]
        if signals:
            score += 50 + (len(signals) * 5)
            reasons.append("Detected repo signal(s) that already match this platform.")
        else:
            reasons.append("No platform-specific artifacts detected yet; using the default support ranking.")

        recommendations.append(
            Recommendation(
                platform_id=adapter.id,
                score=score,
                reasons=tuple(reasons + list(signals)),
                signals=signals,
                next_command=f"repo-context-hooks install --platform {adapter.id} --repo-root .",
            )
        )

    ranked = sorted(
        recommendations,
        key=lambda item: (-item.score, item.platform_id),
    )
    return RecommendationReport(
        repo_contract_ok=True,
        repo_contract_detail="repo contract is healthy",
        detected_signals=tuple(dict.fromkeys(all_detected_signals)),
        recommendations=tuple(ranked[:limit]),
    )
