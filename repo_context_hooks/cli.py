from __future__ import annotations

import argparse
import json
from pathlib import Path

from .doctor import diagnose_all_platforms, diagnose_platform
from .installer import install_platform, supported_platform_ids
from .platforms import get_registry
from .recommend import recommend_setup
from .repo_contract import init_repo_contract
from .doctor import diagnose_repo_contract
from .telemetry import measure_impact, write_public_monitoring_snapshot


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
    doctor.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
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
    recommend.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )

    measure = subparsers.add_parser(
        "measure",
        help="Measure repo continuity evidence and estimated impact.",
    )
    measure.add_argument(
        "--repo-root",
        default=".",
        help="Repository root to inspect (default: current directory).",
    )
    measure.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    measure.add_argument(
        "--snapshot-dir",
        help=(
            "Write a sanitized public monitoring snapshot to this directory "
            "(for example: docs/monitoring)."
        ),
    )

    platforms = subparsers.add_parser(
        "platforms",
        help="List supported platforms and support tiers.",
    )
    platforms.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    return parser


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _platforms(args: argparse.Namespace | None = None) -> int:
    if getattr(args, "json", False):
        _print_json(
            {
                "platforms": [
                    {
                        "id": adapter.metadata.id,
                        "display_name": adapter.metadata.display_name,
                        "support_tier": adapter.metadata.support_tier.value,
                        "install_surfaces": list(adapter.metadata.install_surfaces),
                        "summary": adapter.metadata.summary,
                    }
                    for adapter in get_registry().all()
                ]
            }
        )
        return 0

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
    if getattr(args, "json", False):
        _print_json(report.to_dict())
    else:
        print(report.render())
    return 0 if report.ok else 1


def _recommend(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    report = recommend_setup(repo_root=repo_root, limit=args.limit)
    if getattr(args, "json", False):
        _print_json(report.to_dict())
    else:
        print(report.render())
    return 0


def _measure(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    report = measure_impact(repo_root=repo_root)
    snapshot = None
    snapshot_dir = getattr(args, "snapshot_dir", None)
    if snapshot_dir:
        output_dir = Path(snapshot_dir)
        if not output_dir.is_absolute():
            output_dir = repo_root / output_dir
        snapshot = write_public_monitoring_snapshot(
            report,
            output_dir.resolve(),
        )
    if getattr(args, "json", False):
        payload = report.to_dict()
        if snapshot is not None:
            payload["public_snapshot"] = snapshot
        _print_json(payload)
    else:
        print(report.render())
        if snapshot is not None:
            print(f"Wrote public monitoring snapshot: {snapshot['dashboard_path']}")
            print(f"Wrote public monitoring history: {snapshot['history_path']}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "init":
        return _init(args)
    if args.command == "install":
        return _install(args)
    if args.command == "platforms":
        return _platforms(args)
    if args.command == "doctor":
        return _doctor(args)
    if args.command == "recommend":
        return _recommend(args)
    if args.command == "measure":
        return _measure(args)
    parser.error("Unknown command")
    return 2
