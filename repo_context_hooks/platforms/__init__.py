from __future__ import annotations

from .base import InstallPlan, InstallResult, PlatformMetadata, SupportTier
from .claude import ClaudeAdapter
from .codex import CodexAdapter
from .cursor import CursorAdapter
from .kimi import KimiAdapter
from .lovable import LovableAdapter
from .ollama import OllamaAdapter
from .openclaw import OpenClawAdapter
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
        OpenClawAdapter(),
        OllamaAdapter(),
        KimiAdapter(),
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
