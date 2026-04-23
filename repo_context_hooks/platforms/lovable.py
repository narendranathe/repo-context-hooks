from __future__ import annotations

from pathlib import Path

from .base import InstallPlan, InstallResult, PlatformMetadata, SupportTier
from .runtime import posix_paths, render_template, write_text_file


class LovableAdapter:
    metadata = PlatformMetadata(
        id="lovable",
        display_name="Lovable",
        support_tier=SupportTier.PARTIAL,
        summary="Installs repo-owned Lovable knowledge exports plus AGENTS guidance.",
        install_surfaces=("agents-md", "lovable-knowledge-export"),
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
                repo_root / ".lovable" / "project-knowledge.md",
                repo_root / ".lovable" / "workspace-knowledge.md",
            )
        )
        return InstallPlan(
            platform_id=self.id,
            home_paths=(),
            repo_paths=repo_paths,
            warnings=(
                "Lovable project and workspace knowledge live in the Lovable UI and cannot be verified locally.",
            ),
            manual_steps=(
                "Connect Lovable to the synced GitHub repository on the default branch.",
                "Paste .lovable/project-knowledge.md into Lovable Project Knowledge.",
                "Paste .lovable/workspace-knowledge.md into Lovable Workspace Knowledge if you want shared rules.",
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
            agents_path = repo_root / "AGENTS.md"
            project_knowledge = repo_root / ".lovable" / "project-knowledge.md"
            workspace_knowledge = repo_root / ".lovable" / "workspace-knowledge.md"
            repo_statuses["AGENTS.md"] = write_text_file(
                agents_path,
                render_template("AGENTS.md"),
                force=force,
            )
            repo_statuses["project-knowledge.md"] = write_text_file(
                project_knowledge,
                render_template("lovable-project-knowledge.md"),
                force=force,
            )
            repo_statuses["workspace-knowledge.md"] = write_text_file(
                workspace_knowledge,
                render_template("lovable-workspace-knowledge.md"),
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
                "Lovable project and workspace knowledge live in the Lovable UI and cannot be verified locally.",
            ),
            manual_steps=(
                "Connect Lovable to the synced GitHub repository on the default branch.",
                "Paste .lovable/project-knowledge.md into Lovable Project Knowledge.",
                "Paste .lovable/workspace-knowledge.md into Lovable Workspace Knowledge if you want shared rules.",
            ),
        )
