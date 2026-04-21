from __future__ import annotations

from pathlib import Path

from .base import InstallPlan, InstallResult, PlatformMetadata, SupportTier
from .runtime import (
    bundled_skill_names,
    install_skills_bundle,
    platform_skill_dir,
    posix_paths,
    render_template,
    write_text_file,
)


class CodexAdapter:
    metadata = PlatformMetadata(
        id="codex",
        display_name="Codex",
        support_tier=SupportTier.PARTIAL,
        summary="Installs Codex skills and repo contract guidance without native hooks.",
        install_surfaces=("skills", "repo-contract"),
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
        skill_root = platform_skill_dir("codex", home=home)
        home_paths = posix_paths(skill_root / name for name in bundled_skill_names())
        repo_paths = posix_paths((repo_root / "AGENTS.md",))
        return InstallPlan(
            platform_id=self.id,
            home_paths=home_paths,
            repo_paths=repo_paths,
            warnings=(
                "Codex does not expose native lifecycle hooks; support stays repo-contract driven.",
            ),
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
            "codex",
            force=force,
            home=home,
        )
        repo_statuses: dict[str, str] = {}
        if install_repo_context:
            repo_statuses["AGENTS.md"] = write_text_file(
                repo_root / "AGENTS.md",
                render_template("AGENTS.md"),
                force=force,
            )
        return InstallResult(
            platform_id=self.id,
            display_name=self.metadata.display_name,
            support_tier=self.metadata.support_tier,
            home_target=home_target,
            home_statuses=home_statuses,
            repo_statuses=repo_statuses,
            warnings=(
                "Codex does not expose native lifecycle hooks; support remains partial.",
            ),
        )
