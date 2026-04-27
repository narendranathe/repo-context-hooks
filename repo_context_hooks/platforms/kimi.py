from __future__ import annotations

from pathlib import Path

from .base import InstallPlan, InstallResult, PlatformMetadata, SupportTier
from .runtime import posix_paths, render_template, write_text_file


class KimiAdapter:
    metadata = PlatformMetadata(
        id="kimi",
        display_name="Kimi",
        support_tier=SupportTier.PARTIAL,
        summary="Installs AGENTS guidance for Kimi Code CLI project context.",
        install_surfaces=("agents-md",),
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
                "Kimi support targets Kimi Code CLI project context, not the generic Kimi API.",
            ),
            manual_steps=(
                "Run or review Kimi Code CLI /init output, then merge any generated guidance with this AGENTS.md contract.",
                "Keep Kimi-specific rules out of public claims until a stable Kimi rules path is documented.",
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
                "Kimi support targets Kimi Code CLI project context, not the generic Kimi API.",
            ),
            manual_steps=(
                "Run or review Kimi Code CLI /init output, then merge any generated guidance with this AGENTS.md contract.",
                "Keep Kimi-specific rules out of public claims until a stable Kimi rules path is documented.",
            ),
        )
