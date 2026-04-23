from __future__ import annotations

import importlib

from repo_context_hooks import __version__
from repo_context_hooks.cli import main as repo_main
from repo_context_hooks.installer import install_platform as repo_install_platform


def test_legacy_modules_expose_version_and_main() -> None:
    graphify = importlib.import_module("graphify")
    repohandoff = importlib.import_module("repohandoff")

    assert graphify.__version__ == __version__
    assert repohandoff.__version__ == __version__
    assert graphify.main is repo_main
    assert repohandoff.main is repo_main


def test_legacy_cli_and_installer_modules_proxy_repo_context_hooks() -> None:
    graphify_cli = importlib.import_module("graphify.cli")
    repohandoff_cli = importlib.import_module("repohandoff.cli")
    graphify_installer = importlib.import_module("graphify.installer")
    repohandoff_installer = importlib.import_module("repohandoff.installer")

    assert graphify_cli.main is repo_main
    assert repohandoff_cli.main is repo_main
    assert graphify_installer.install_platform is repo_install_platform
    assert repohandoff_installer.install_platform is repo_install_platform


def test_legacy_main_modules_expose_repo_main() -> None:
    graphify_main = importlib.import_module("graphify.__main__")
    repohandoff_main = importlib.import_module("repohandoff.__main__")

    assert graphify_main.main is repo_main
    assert repohandoff_main.main is repo_main
