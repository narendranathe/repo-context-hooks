from __future__ import annotations

from typing import Dict, Iterable, List

from .base import PlatformAdapter


class PlatformRegistry:
    def __init__(self, adapters: Iterable[PlatformAdapter]) -> None:
        self._adapters: Dict[str, PlatformAdapter] = {}
        for adapter in adapters:
            self._adapters[adapter.id] = adapter

    def all(self) -> List[PlatformAdapter]:
        return list(self._adapters.values())

    def get(self, platform_id: str) -> PlatformAdapter:
        return self._adapters[platform_id]
