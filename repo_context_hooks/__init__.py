from __future__ import annotations

__all__ = ["__version__"]

try:
    from importlib.metadata import version as _pkg_version

    __version__ = _pkg_version("repo-context-hooks")
except Exception:
    __version__ = "0.6.0"
