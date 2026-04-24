from __future__ import annotations

import argparse
from pathlib import Path

from .doctor import diagnose_all_platforms, diagnose_platform
from .installer import install_platform, supported_platform_ids
from .platforms import get_registry
from .recommend import recommend_setup
from .repo_contract import init_repo_contract
from .doctor import diagnose_repo_contract


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

    init = subparsers.add_parser(
        "init",
        help="Bootstrap the canonical repo contract files.",
    )
    init.add_argument(
        "--repo-root",
        default=".",
        help="Repository root to initialize (default: current directory).",
    )
    init.add_argument(
        "--force",
        action="store_true",
        help="Overwrite bootstrapped files when supported.",
    )

    doctor = subparsers.add_parser(
        "doctor",
        help="Validate repo context setup for a platform.",
    )
    doctor_scope = doctor.add_mutually_exclusive_group()
    doctor_scope.add_argument(
        "--platform",
        choices=supported_platform_ids(),
        help="Target platform to validate.",
    )
    doctor_scope.add_argument(
        "--all-platforms",
        action="store_true",
        help="Validate repo contract health plus readiness across all supported platforms.",
    )
    doctor.add_argument(
        "--repo-root",
        default=".",
        help="Repository root to inspect (default: current directory).",
    )

    recommend = subparsers.add_parser(
        "recommend",
        help="Recommend the next best platform setup path for this repo.",
    )
    recommend.add_argument(
        "--repo-root",
        default=".",
        help="Repository root to inspect (default: current directory).",
    )
    recommend.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Maximum number of platform recommendations to print (default: 3).",
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


def _init(args: argparse.Namespace) -> int:
    statuses = init_repo_contract(
        Path(args.repo_root).resolve(),
        force=args.force,
    )
    print("Initialized repo contract:")
    for name, status in statuses.items():
        print(f"- {name}: {status}")
    return 0


def _doctor(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    if getattr(args, "all_platforms", False):
        report = diagnose_all_platforms(repo_root=repo_root)
    elif getattr(args, "platform", None):
        report = diagnose_platform(
            args.platform,
            repo_root=repo_root,
        )
    else:
        report = diagnose_repo_contract(repo_root)
    print(report.render())
    return 0 if report.ok else 1


def _recommend(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    report = recommend_setup(repo_root=repo_root, limit=args.limit)
    print(report.render())
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "init":
        return _init(args)
    if args.command == "install":
        return _install(args)
    if args.command == "platforms":
        return _platforms()
    if args.command == "doctor":
        return _doctor(args)
    if args.command == "recommend":
        return _recommend(args)
    parser.error("Unknown command")
    return 2
