from __future__ import annotations

from pathlib import Path

from .base import InstallPlan, InstallResult, PlatformMetadata, SupportTier
from .runtime import posix_paths, render_template, write_text_file


class OllamaAdapter:
    metadata = PlatformMetadata(
        id="ollama",
        display_name="Ollama",
        support_tier=SupportTier.PARTIAL,
        summary="Installs a repo-context Modelfile for local-model workflows.",
        install_surfaces=("agents-md", "ollama-modelfile"),
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
                repo_root / "Modelfile.repo-context",
            )
        )
        return InstallPlan(
            platform_id=self.id,
            home_paths=(),
            repo_paths=repo_paths,
            warnings=(
                "Ollama is a model runtime, not a repo-aware lifecycle platform.",
            ),
            manual_steps=(
                "Edit the FROM line in Modelfile.repo-context if you prefer a different local model.",
                "Run: ollama create repo-context-helper -f Modelfile.repo-context",
                "Use the created model through an agent wrapper that can read repo files, or paste README.md, specs/README.md, and AGENTS.md when using direct ollama run.",
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
            repo_statuses["Modelfile.repo-context"] = write_text_file(
                repo_root / "Modelfile.repo-context",
                render_template("ollama-modelfile"),
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
                "Ollama is a model runtime, not a repo-aware lifecycle platform.",
            ),
            manual_steps=(
                "Edit the FROM line in Modelfile.repo-context if you prefer a different local model.",
                "Run: ollama create repo-context-helper -f Modelfile.repo-context",
                "Use the created model through an agent wrapper that can read repo files, or paste README.md, specs/README.md, and AGENTS.md when using direct ollama run.",
            ),
        )
