from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

from repo_context_hooks import __version__
from repo_context_hooks.cli import main as repo_main
from repo_context_hooks.installer import install_platform as repo_install_platform

# Project root — used to load alias packages from the local directory directly,
# bypassing any site-packages `graphify` (e.g. the graphifyy skill package).
_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_local(module_name: str) -> object:
    """Load a module from the project root, bypassing sys.modules cache."""
    parts = module_name.split(".", 1)
    pkg_dir = _PROJECT_ROOT / parts[0]
    if len(parts) == 1:
        spec_path = pkg_dir / "__init__.py"
    else:
        spec_path = pkg_dir / parts[1].replace(".", "/") / "__init__.py"
        if not spec_path.exists():
            spec_path = pkg_dir / (parts[1].replace(".", "/") + ".py")

    spec = importlib.util.spec_from_file_location(module_name, spec_path)
    assert spec and spec.loader, f"could not build spec for {module_name} at {spec_path}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_legacy_modules_expose_version_and_main() -> None:
    graphify = _load_local("graphify")
    repohandoff = _load_local("repohandoff")

    assert graphify.__version__ == __version__
    assert repohandoff.__version__ == __version__
    assert graphify.main is repo_main
    assert repohandoff.main is repo_main


def test_legacy_cli_and_installer_modules_proxy_repo_context_hooks() -> None:
    graphify_cli = _load_local("graphify.cli")
    repohandoff_cli = _load_local("repohandoff.cli")
    graphify_installer = _load_local("graphify.installer")
    repohandoff_installer = _load_local("repohandoff.installer")

    assert graphify_cli.main is repo_main
    assert repohandoff_cli.main is repo_main
    assert graphify_installer.install_platform is repo_install_platform
    assert repohandoff_installer.install_platform is repo_install_platform


def test_legacy_main_modules_expose_repo_main() -> None:
    graphify_main = _load_local("graphify.__main__")
    repohandoff_main = _load_local("repohandoff.__main__")

    assert graphify_main.main is repo_main
    assert repohandoff_main.main is repo_main
