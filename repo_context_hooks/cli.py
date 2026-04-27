from __future__ import annotations

import argparse
import json
from pathlib import Path

from .doctor import diagnose_all_platforms, diagnose_platform
from .installer import install_platform, supported_platform_ids, uninstall_platform
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
        required=False,
        default=None,
        choices=supported_platform_ids(),
        help="Target platform for installation. If omitted, auto-detects installed agents.",
    )
    install.add_argument(
        "--repo-root",
        default=".",
        help="Repository root for repo context setup (default: current directory).",
    )
    install.add_argument(
        "--also-repo-hooks",
        action="store_true",
        help=(
            "Also install per-repo hooks into .claude/settings.json in the current repo. "
            "Agent-level install is the default; pass this flag to additionally write workspace artifacts."
        ),
    )
    install.add_argument(
        "--skip-repo-hooks",
        action="store_true",
        help=(
            "Agent-level install is now the default; this flag is a no-op unless "
            "--also-repo-hooks is passed."
        ),
    )
    install.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing installed artifacts.",
    )
    install.add_argument(
        "--no-telemetry",
        action="store_true",
        help="Bake REPO_CONTEXT_HOOKS_TELEMETRY=0 into hook command strings (local opt-out).",
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

    uninstall = subparsers.add_parser(
        "uninstall",
        help="Remove installed skills and hook entries for a platform.",
    )
    uninstall.add_argument(
        "--platform",
        required=True,
        choices=supported_platform_ids(),
        help="Platform to uninstall.",
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


def _detect_platforms() -> list[str]:
    """Return platform IDs whose agent home directory exists."""
    home = Path.home()
    detected = []
    for platform_id in supported_platform_ids():
        if (home / f".{platform_id}").is_dir():
            detected.append(platform_id)
    return detected


def _install(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    also_repo_hooks = getattr(args, "also_repo_hooks", False)
    telemetry = not getattr(args, "no_telemetry", False)

    if also_repo_hooks and not (repo_root / ".git").exists():
        print("Repo context skipped: target is not a git repository.")
        also_repo_hooks = False

    # Determine which platforms to install
    if args.platform:
        platforms_to_install = [args.platform]
    else:
        platforms_to_install = _detect_platforms()
        if not platforms_to_install:
            # Fall back to claude if nothing detected
            platforms_to_install = ["claude"]
            print("No agent home directories detected. Defaulting to --platform claude.")
        else:
            print(f"Auto-detected platforms: {', '.join(platforms_to_install)}")

    # Install each platform
    for platform in platforms_to_install:
        if len(platforms_to_install) > 1:
            print(f"\n=== Installing for {platform} ===")
        result = install_platform(
            platform=platform,
            repo_root=repo_root,
            force=args.force,
            install_repo_context=False,
            also_repo_hooks=also_repo_hooks,
            telemetry=telemetry,
        )
        if len(platforms_to_install) == 1:
            print("=== Agent skill install ===")
        print(result.summary)
        if result.home_target is not None:
            print(f"Installed platform skills to: {result.home_target}")
        if result.home_statuses:
            for name, status in result.home_statuses.items():
                print(f"- {name}: {status}")
        for warning in result.warnings:
            print(f"Warning: {warning}")
        for step in result.manual_steps:
            print(f"Manual: {step}")
        if also_repo_hooks:
            print("=== Workspace artifacts ===")
            if result.repo_statuses:
                for name, status in result.repo_statuses.items():
                    print(f"- {name}: {status}")
            else:
                print("No workspace artifacts installed.")

    # --- What happens next (first-run guidance) ---
    print("")
    print("=== What happens next ===")
    print("Every session will now start with workspace context from specs/README.md")
    print("Run `repo-context-hooks init` in any repo to set up a workspace contract")
    if len(platforms_to_install) == 1:
        print(f"Run `repo-context-hooks doctor --platform {platforms_to_install[0]}` to check setup health")
    else:
        print("Run `repo-context-hooks doctor --all-platforms` to check setup health")
    print("Run `repo-context-hooks measure` to see continuity evidence over time")

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


def _uninstall(args: argparse.Namespace) -> int:
    result = uninstall_platform(args.platform)
    for name, status in result.items():
        print(f"- {name}: {status}")
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
    if args.command == "uninstall":
        return _uninstall(args)
    parser.error("Unknown command")
    return 2
