from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Protocol, Tuple


class SupportTier(str, Enum):
    NATIVE = "native"
    PARTIAL = "partial"
    PLANNED = "planned"


@dataclass(frozen=True)
class PlatformMetadata:
    id: str
    display_name: str
    support_tier: SupportTier
    summary: str
    install_surfaces: Tuple[str, ...]


@dataclass(frozen=True)
class InstallPlan:
    platform_id: str
    home_paths: Tuple[str, ...]
    repo_paths: Tuple[str, ...]
    warnings: Tuple[str, ...] = ()
    manual_steps: Tuple[str, ...] = ()
    installs_repo_context: bool = False


@dataclass(frozen=True)
class InstallResult:
    platform_id: str
    display_name: str
    support_tier: SupportTier
    home_target: Path | None
    home_statuses: Dict[str, str]
    repo_statuses: Dict[str, str]
    warnings: Tuple[str, ...] = ()
    manual_steps: Tuple[str, ...] = ()

    @property
    def summary(self) -> str:
        installed_home = any(status == "installed" for status in self.home_statuses.values())
        installed_repo = any(status == "installed" for status in self.repo_statuses.values())

        if installed_home and installed_repo:
            return f"{self.display_name} {self.support_tier.value} support installed."
        if installed_home and not self.repo_statuses:
            return (
                f"{self.display_name} {self.support_tier.value} skills installed; "
                "repo context skipped."
            )
        if installed_repo and not self.home_statuses:
            return (
                f"{self.display_name} {self.support_tier.value} repo context installed."
            )
        return f"{self.display_name} {self.support_tier.value} support checked."


class PlatformAdapter(Protocol):
    metadata: PlatformMetadata

    @property
    def id(self) -> str:
        ...

    @property
    def support_tier(self) -> SupportTier:
        ...

    def build_install_plan(
        self,
        repo_root: Path,
        home: Path | None = None,
    ) -> InstallPlan:
        ...

    def install(
        self,
        repo_root: Path,
        force: bool = False,
        home: Path | None = None,
        install_repo_context: bool = True,
    ) -> InstallResult:
        ...
