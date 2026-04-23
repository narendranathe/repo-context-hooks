from __future__ import annotations

from pathlib import Path

from .base import InstallPlan, InstallResult, PlatformMetadata, SupportTier
from .runtime import (
    posix_paths,
    render_template,
    write_text_file,
)


class CodexAdapter:
    metadata = PlatformMetadata(
        id="codex",
        display_name="Codex",
        support_tier=SupportTier.PARTIAL,
        summary="Installs repo-contract guidance for Codex without native hooks.",
        install_surfaces=("repo-contract",),
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
        repo_paths = posix_paths((repo_root / "AGENTS.md",))
        return InstallPlan(
            platform_id=self.id,
            home_paths=(),
            repo_paths=repo_paths,
            warnings=(
                "Codex does not expose native lifecycle hooks; support stays repo-contract driven.",
                "Codex does not yet install bundled lifecycle skills; continuity is anchored in checked-in repo docs.",
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
        del home
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
            home_target=None,
            home_statuses={},
            repo_statuses=repo_statuses,
            warnings=(
                "Codex does not expose native lifecycle hooks; support remains partial.",
                "Codex continuity currently relies on checked-in repo docs and AGENTS.md rather than bundled lifecycle skills.",
            ),
        )
