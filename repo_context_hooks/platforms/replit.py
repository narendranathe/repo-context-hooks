from __future__ import annotations

from pathlib import Path

from .base import InstallPlan, InstallResult, PlatformMetadata, SupportTier
from .runtime import posix_paths, render_template, write_text_file


class ReplitAdapter:
    metadata = PlatformMetadata(
        id="replit",
        display_name="Replit",
        support_tier=SupportTier.PARTIAL,
        summary="Installs repo-root Replit Agent context with repo-contract handoff guidance.",
        install_surfaces=("replit-md", "repo-contract"),
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
                repo_root / "replit.md",
                repo_root / "AGENTS.md",
            )
        )
        return InstallPlan(
            platform_id=self.id,
            home_paths=(),
            repo_paths=repo_paths,
            warnings=(
                "Replit does not expose native lifecycle hooks; support remains root-file driven.",
            ),
            manual_steps=(
                "Start a fresh Replit Agent conversation after adding or updating replit.md so the repo-root context is reloaded.",
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
            replit_path = repo_root / "replit.md"
            agents_path = repo_root / "AGENTS.md"
            repo_statuses["replit.md"] = write_text_file(
                replit_path,
                render_template("replit.md"),
                force=force,
            )
            repo_statuses["AGENTS.md"] = write_text_file(
                agents_path,
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
                "Replit does not expose native lifecycle hooks; support remains partial.",
            ),
            manual_steps=(
                "Start a fresh Replit Agent conversation after adding or updating replit.md so the repo-root context is reloaded.",
            ),
        )
