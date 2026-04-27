from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

from .platforms import InstallResult, get_registry
from .platforms.runtime import (
    bundle_root,
    install_global_hooks,
    install_repo_hooks,
    install_skills_bundle,
    platform_skill_dir,
)


def supported_platform_ids() -> tuple[str, ...]:
    return tuple(adapter.id for adapter in get_registry().all())


def install_skills(
    platform: str,
    force: bool = False,
    home: Path | None = None,
) -> Tuple[Path, Dict[str, str]]:
    return install_skills_bundle(platform, force=force, home=home)


def install_platform(
    platform: str,
    repo_root: Path,
    force: bool = False,
    home: Path | None = None,
    install_repo_context: bool = False,
    also_repo_hooks: bool = False,
) -> InstallResult:
    adapter = get_registry().get(platform)
    return adapter.install(
        repo_root=repo_root.resolve(),
        force=force,
        home=home,
        install_repo_context=install_repo_context,
        also_repo_hooks=also_repo_hooks,
    )
