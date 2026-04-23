from __future__ import annotations

from .base import InstallPlan, InstallResult, PlatformMetadata, SupportTier
from .claude import ClaudeAdapter
from .codex import CodexAdapter
from .cursor import CursorAdapter
from .lovable import LovableAdapter
from .replit import ReplitAdapter
from .registry import PlatformRegistry
from .windsurf import WindsurfAdapter

_REGISTRY = PlatformRegistry(
    (
        ClaudeAdapter(),
        CursorAdapter(),
        CodexAdapter(),
        ReplitAdapter(),
        WindsurfAdapter(),
        LovableAdapter(),
    )
)


def get_registry() -> PlatformRegistry:
    return _REGISTRY


__all__ = [
    "InstallPlan",
    "InstallResult",
    "PlatformMetadata",
    "PlatformRegistry",
    "SupportTier",
    "get_registry",
]
