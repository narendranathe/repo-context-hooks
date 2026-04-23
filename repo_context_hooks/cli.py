from __future__ import annotations

import argparse
from pathlib import Path

from .doctor import diagnose_platform
from .installer import install_platform, supported_platform_ids
from .platforms import get_registry


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
        choices=supported_platform_ids(),
        help="Target platform for installation.",
    )
    install.add_argument(
        "--repo-root",
        default=".",
        help="Repository root for repo context setup (default: current directory).",
    )
    install.add_argument(
        "--skip-repo-hooks",
        action="store_true",
        help="Install platform skills only.",
    )
    install.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing installed artifacts.",
    )

    doctor = subparsers.add_parser(
        "doctor",
        help="Validate repo context setup for a platform.",
    )
    doctor.add_argument(
        "--platform",
        required=True,
        choices=supported_platform_ids(),
        help="Target platform to validate.",
    )
    doctor.add_argument(
        "--repo-root",
        default=".",
        help="Repository root to inspect (default: current directory).",
    )

    subparsers.add_parser(
        "platforms",
        help="List supported platforms and support tiers.",
    )
    return parser


def _platforms() -> int:
    for adapter in get_registry().all():
        meta = adapter.metadata
        surfaces = ", ".join(meta.install_surfaces)
        print(
            f"{meta.id}\t{meta.support_tier.value}\t{surfaces}\t{meta.summary}"
        )
    return 0


def _install(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    install_repo_context = not args.skip_repo_hooks

    if install_repo_context and not (repo_root / ".git").exists():
        print("Repo context skipped: target is not a git repository.")
        install_repo_context = False

    result = install_platform(
        platform=args.platform,
        repo_root=repo_root,
        force=args.force,
        install_repo_context=install_repo_context,
    )
    print(result.summary)
    if result.home_target is not None:
        print(f"Installed platform skills to: {result.home_target}")
    if result.home_statuses:
        for name, status in result.home_statuses.items():
            print(f"- {name}: {status}")
    if result.repo_statuses:
        print("Installed repo artifacts:")
        for name, status in result.repo_statuses.items():
            print(f"- {name}: {status}")
    elif args.skip_repo_hooks:
        print("Skipped repo context installation (--skip-repo-hooks).")
    for warning in result.warnings:
        print(f"Warning: {warning}")
    for step in result.manual_steps:
        print(f"Manual: {step}")
    return 0


def _doctor(args: argparse.Namespace) -> int:
    report = diagnose_platform(
        args.platform,
        repo_root=Path(args.repo_root).resolve(),
    )
    print(report.render())
    return 0 if report.ok else 1


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "install":
        return _install(args)
    if args.command == "platforms":
        return _platforms()
    if args.command == "doctor":
        return _doctor(args)
    parser.error("Unknown command")
    return 2
