from __future__ import annotations

import argparse
from pathlib import Path

from .installer import PLATFORMS, install_repo_hooks, install_skills


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-context-hooks",
        description="Install repo context continuity skills and lifecycle hooks.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    install = subparsers.add_parser(
        "install",
        help="Install skills for a platform and optionally configure repo hooks.",
    )
    install.add_argument(
        "--platform",
        required=True,
        choices=PLATFORMS,
        help="Target platform for skill installation.",
    )
    install.add_argument(
        "--repo-root",
        default=".",
        help="Repository root for hook setup (default: current directory).",
    )
    install.add_argument(
        "--skip-repo-hooks",
        action="store_true",
        help="Install platform skills only.",
    )
    install.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing installed skills.",
    )
    return parser


def _install(args: argparse.Namespace) -> int:
    target, statuses = install_skills(platform=args.platform, force=args.force)
    print(f"Installed platform skills to: {target}")
    for skill, state in statuses.items():
        print(f"- {skill}: {state}")

    if args.skip_repo_hooks:
        print("Skipped repo hook installation (--skip-repo-hooks).")
        return 0

    repo_root = Path(args.repo_root).resolve()
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        print(
            "Repo hooks skipped: target is not a git repository. "
            "Use --repo-root on a repo or omit --skip-repo-hooks in a repo directory."
        )
        return 0

    installed = install_repo_hooks(repo_root)
    print("Installed repo hooks:")
    for name, path in installed.items():
        print(f"- {name}: {path}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "install":
        return _install(args)
    parser.error("Unknown command")
    return 2
