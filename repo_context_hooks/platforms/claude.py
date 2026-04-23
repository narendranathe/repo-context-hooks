from __future__ import annotations

from pathlib import Path

from .base import InstallPlan, InstallResult, PlatformMetadata, SupportTier
from .runtime import (
    bundled_skill_names,
    install_repo_hooks,
    install_skills_bundle,
    platform_skill_dir,
    posix_paths,
)


class ClaudeAdapter:
    metadata = PlatformMetadata(
        id="claude",
        display_name="Claude",
        support_tier=SupportTier.NATIVE,
        summary="Installs skills and Claude lifecycle hooks for repo continuity.",
        install_surfaces=("skills", "repo-hooks"),
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
        skill_root = platform_skill_dir("claude", home=home)
        home_paths = posix_paths(skill_root / name for name in bundled_skill_names())
        repo_paths = posix_paths(
            (
                repo_root / ".claude" / "scripts" / "repo_specs_memory.py",
                repo_root / ".claude" / "scripts" / "session_context.py",
                repo_root / ".claude" / "settings.json",
            )
        )
        return InstallPlan(
            platform_id=self.id,
            home_paths=home_paths,
            repo_paths=repo_paths,
            installs_repo_context=True,
        )

    def install(
        self,
        repo_root: Path,
        force: bool = False,
        home: Path | None = None,
        install_repo_context: bool = True,
    ) -> InstallResult:
        home_target, home_statuses = install_skills_bundle(
            "claude",
            force=force,
            home=home,
        )
        repo_statuses: dict[str, str] = {}
        if install_repo_context:
            repo_statuses = install_repo_hooks(repo_root, force=force)
        return InstallResult(
            platform_id=self.id,
            display_name=self.metadata.display_name,
            support_tier=self.metadata.support_tier,
            home_target=home_target,
            home_statuses=home_statuses,
            repo_statuses=repo_statuses,
        )
