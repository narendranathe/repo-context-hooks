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
    uninstall_global_hooks,
)


def supported_platform_ids() -> tuple[str, ...]:
    return tuple(adapter.id for adapter in get_registry().all())


def install_skills(
    platform: str,
    force: bool = False,
    home: Path | None = None,
) -> Tuple[Path, Dict[str, str]]:
    return install_skills_bundle(platform, force=force, home=home)


def uninstall_platform(
    platform: str,
    home: Path | None = None,
) -> dict:
    """Remove the skills bundle and global hook entries for *platform*.

    Returns a status dict such as ``{"context-handoff-hooks": "removed",
    "settings.json": "cleaned"}``.  The operation is idempotent: running it
    when nothing is installed returns ``"not found"`` / ``"no changes"``
    statuses without raising.
    """
    # Validate the platform exists in the registry (raises if unknown).
    get_registry().get(platform)
    return uninstall_global_hooks(agent_home=home or Path.home())


def install_platform(
    platform: str,
    repo_root: Path,
    force: bool = False,
    home: Path | None = None,
    install_repo_context: bool = False,
    also_repo_hooks: bool = False,
    telemetry: bool = True,
) -> InstallResult:
    adapter = get_registry().get(platform)
    # Pass telemetry only to adapters that accept it (ClaudeAdapter does;
    # partial-support adapters use a fixed signature without telemetry).
    try:
        return adapter.install(
            repo_root=repo_root.resolve(),
            force=force,
            home=home,
            install_repo_context=install_repo_context,
            also_repo_hooks=also_repo_hooks,
            telemetry=telemetry,
        )
    except TypeError:
        # Adapter does not accept telemetry kwarg — fall back without it.
        return adapter.install(
            repo_root=repo_root.resolve(),
            force=force,
            home=home,
            install_repo_context=install_repo_context,
            also_repo_hooks=also_repo_hooks,
        )
