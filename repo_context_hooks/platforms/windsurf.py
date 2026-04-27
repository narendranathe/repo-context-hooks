from __future__ import annotations

from pathlib import Path

from .base import InstallPlan, InstallResult, PlatformMetadata, SupportTier
from .runtime import posix_paths, render_template, write_text_file


class WindsurfAdapter:
    metadata = PlatformMetadata(
        id="windsurf",
        display_name="Windsurf",
        support_tier=SupportTier.PARTIAL,
        summary="Installs repo-native Windsurf rules and AGENTS guidance for Cascade.",
        install_surfaces=("agents-md", "windsurf-rules"),
    )

    @property
    def id(self) -> str:
        return self.metadata.id

    @property
    def support_tier(self) -> SupportTier:
        return self.metadata.support_tier

    def build_install_plan(
        self,
        repo_root: Path,
        home: Path | None = None,
    ) -> InstallPlan:
        del home
        repo_paths = posix_paths(
            (
                repo_root / "AGENTS.md",
                repo_root / ".windsurf" / "rules" / "repo-context-continuity.md",
            )
        )
        return InstallPlan(
            platform_id=self.id,
            home_paths=(),
            repo_paths=repo_paths,
            warnings=(
                "Windsurf does not expose native lifecycle hooks; support remains rules-driven.",
            ),
            installs_repo_context=True,
        )

    def install(
        self,
        repo_root: Path,
        force: bool = False,
        home: Path | None = None,
        install_repo_context: bool = True,
        also_repo_hooks: bool = False,
    ) -> InstallResult:
        del home
        repo_statuses: dict[str, str] = {}
        if install_repo_context:
            agents_path = repo_root / "AGENTS.md"
            rule_path = repo_root / ".windsurf" / "rules" / "repo-context-continuity.md"
            repo_statuses["AGENTS.md"] = write_text_file(
                agents_path,
                render_template("AGENTS.md"),
                force=force,
            )
            repo_statuses["repo-context-continuity.md"] = write_text_file(
                rule_path,
                render_template("windsurf-rule.md"),
                force=force,
            )
        return InstallResult(
            platform_id=self.id,
            display_name=self.metadata.display_name,
            support_tier=self.metadata.support_tier,
            home_target=None,
            home_statuses={},
            repo_statuses=repo_statuses,
            warnings=(
                "Windsurf does not expose native lifecycle hooks; support remains partial.",
            ),
        )
