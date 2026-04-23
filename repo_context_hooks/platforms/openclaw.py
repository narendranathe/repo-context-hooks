from __future__ import annotations

from pathlib import Path

from .base import InstallPlan, InstallResult, PlatformMetadata, SupportTier
from .runtime import posix_paths, render_template, write_text_file


class OpenClawAdapter:
    metadata = PlatformMetadata(
        id="openclaw",
        display_name="OpenClaw",
        support_tier=SupportTier.PARTIAL,
        summary="Installs repo-safe OpenClaw workspace files plus AGENTS guidance.",
        install_surfaces=("agents-md", "openclaw-workspace-files"),
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
                repo_root / "SOUL.md",
                repo_root / "USER.md",
                repo_root / "TOOLS.md",
            )
        )
        return InstallPlan(
            platform_id=self.id,
            home_paths=(),
            repo_paths=repo_paths,
            warnings=(
                "Local checks cannot verify the active OpenClaw workspace configuration.",
            ),
            manual_steps=(
                "Set OpenClaw agents.defaults.workspace to this repo root, or copy AGENTS.md, SOUL.md, USER.md, and TOOLS.md into the active OpenClaw workspace.",
                "Keep secrets and private memory out of public repos; generated OpenClaw files are sanitized repo guidance only.",
                "Run OpenClaw setup or doctor after changing the active workspace configuration.",
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
            repo_statuses["SOUL.md"] = write_text_file(
                repo_root / "SOUL.md",
                render_template("openclaw-soul.md"),
                force=force,
            )
            repo_statuses["USER.md"] = write_text_file(
                repo_root / "USER.md",
                render_template("openclaw-user.md"),
                force=force,
            )
            repo_statuses["TOOLS.md"] = write_text_file(
                repo_root / "TOOLS.md",
                render_template("openclaw-tools.md"),
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
                "Local checks cannot verify the active OpenClaw workspace configuration.",
            ),
            manual_steps=(
                "Set OpenClaw agents.defaults.workspace to this repo root, or copy AGENTS.md, SOUL.md, USER.md, and TOOLS.md into the active OpenClaw workspace.",
                "Keep secrets and private memory out of public repos; generated OpenClaw files are sanitized repo guidance only.",
                "Run OpenClaw setup or doctor after changing the active workspace configuration.",
            ),
        )
