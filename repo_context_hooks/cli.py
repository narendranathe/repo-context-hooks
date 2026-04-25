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
from .telemetry import (
    measure_impact,
    measure_rollup,
    record_context_window,
    render_prometheus_metrics,
    render_rollup_prometheus_metrics,
    write_public_rollup_snapshot,
    write_public_monitoring_snapshot,
)


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
    measure_output = measure.add_mutually_exclusive_group()
    measure_output.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    measure_output.add_argument(
        "--prometheus",
        action="store_true",
        help="Print Prometheus/OpenMetrics text exposition output.",
    )
    measure.add_argument(
        "--snapshot-dir",
        help=(
            "Write a sanitized public monitoring snapshot to this directory "
            "(for example: docs/monitoring)."
        ),
    )

    rollup = subparsers.add_parser(
        "rollup",
        help="Aggregate local telemetry across all repos in the telemetry store.",
    )
    rollup_output = rollup.add_mutually_exclusive_group()
    rollup_output.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    rollup_output.add_argument(
        "--prometheus",
        action="store_true",
        help="Print Prometheus/OpenMetrics text exposition output.",
    )
    rollup.add_argument(
        "--telemetry-dir",
        help="Telemetry directory to scan (default: repo-context-hooks OS cache).",
    )
    rollup.add_argument(
        "--projects-root",
        help="Also scan repo-local fallback telemetry under each child of this projects directory.",
    )
    rollup.add_argument(
        "--snapshot-dir",
        help="Write a sanitized public cross-repo rollup snapshot to this directory.",
    )

    record_context = subparsers.add_parser(
        "record-context",
        help="Record context-window fullness from an editor, wrapper, or model runner.",
    )
    record_context.add_argument(
        "--repo-root",
        default=".",
        help="Repository root to associate with the context sample.",
    )
    record_context.add_argument(
        "--used-tokens",
        type=int,
        required=True,
        help="Estimated tokens currently used in the active context window.",
    )
    record_context.add_argument(
        "--limit-tokens",
        type=int,
        required=True,
        help="Estimated model context-window token limit.",
    )
    record_context.add_argument(
        "--threshold-percent",
        type=float,
        default=99.0,
        help="Usage percent that should count as the pre-compact threshold.",
    )
    record_context.add_argument(
        "--checkpoint",
        action="store_true",
        help="Also record a pre-compact checkpoint event when the threshold is reached.",
    )
    record_context.add_argument(
        "--source",
        default="context-window",
        help="Telemetry source label, for example vscode-extension.",
    )
    record_context.add_argument(
        "--agent-platform",
        help="Agent platform label, for example codex, claude, cursor, or vscode.",
    )
    record_context.add_argument(
        "--model-name",
        help="Model label when available.",
    )
    record_context.add_argument(
        "--session-id",
        help="Agent session id when available.",
    )
    record_context.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
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
    if getattr(args, "prometheus", False):
        print(render_prometheus_metrics(report), end="")
    elif getattr(args, "json", False):
        payload = report.to_dict()
        if snapshot is not None:
            payload["public_snapshot"] = snapshot
        _print_json(payload)
    else:
        print(report.render())
        if snapshot is not None:
            print(f"Wrote public monitoring snapshot: {snapshot['dashboard_path']}")
            print(f"Wrote public monitoring history: {snapshot['history_path']}")
            if "time_series_svg_path" in snapshot:
                print(f"Wrote public monitoring chart: {snapshot['time_series_svg_path']}")
    return 0


def _rollup(args: argparse.Namespace) -> int:
    telemetry_base = (
        Path(args.telemetry_dir).resolve()
        if getattr(args, "telemetry_dir", None)
        else None
    )
    projects_root = (
        Path(args.projects_root).resolve()
        if getattr(args, "projects_root", None)
        else None
    )
    report = measure_rollup(
        telemetry_base=telemetry_base,
        projects_root=projects_root,
    )
    snapshot = None
    snapshot_dir = getattr(args, "snapshot_dir", None)
    if snapshot_dir:
        output_dir = Path(snapshot_dir)
        if not output_dir.is_absolute():
            output_dir = Path.cwd() / output_dir
        snapshot = write_public_rollup_snapshot(
            report,
            output_dir.resolve(),
        )
    if getattr(args, "prometheus", False):
        print(render_rollup_prometheus_metrics(report), end="")
    elif getattr(args, "json", False):
        payload = report.to_dict()
        if snapshot is not None:
            payload["public_snapshot"] = snapshot
        _print_json(payload)
    else:
        print(report.render())
        if snapshot is not None:
            print(f"Wrote cross-repo rollup dashboard: {snapshot['dashboard_path']}")
            print(f"Wrote cross-repo rollup data: {snapshot['history_path']}")
    return 0


def _record_context(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    usage_percent = round(args.used_tokens / args.limit_tokens * 100, 2)
    threshold_reached = usage_percent >= args.threshold_percent
    event_name = (
        "context-window-threshold"
        if threshold_reached
        else "context-window-sample"
    )
    event_path = record_context_window(
        repo_root=repo_root,
        used_tokens=args.used_tokens,
        limit_tokens=args.limit_tokens,
        threshold_percent=args.threshold_percent,
        checkpoint=args.checkpoint,
        source=args.source,
        agent_platform=args.agent_platform,
        model_name=args.model_name,
        agent_session_id=args.session_id,
    )
    payload = {
        "event_name": event_name,
        "usage_percent": usage_percent,
        "remaining_percent": round(max(0.0, 100.0 - usage_percent), 2),
        "threshold_percent": args.threshold_percent,
        "checkpoint_recorded": bool(args.checkpoint and threshold_reached),
        "event_path": str(event_path),
    }
    if getattr(args, "json", False):
        _print_json(payload)
    else:
        print(f"[OK] {event_name}")
        print(f"Context usage: {usage_percent}%")
        print(f"Threshold: {args.threshold_percent}%")
        if payload["checkpoint_recorded"]:
            print("Checkpoint event recorded: pre-compact")
        print(f"Evidence log: {event_path}")
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
    if args.command == "rollup":
        return _rollup(args)
    if args.command == "record-context":
        return _record_context(args)
    parser.error("Unknown command")
    return 2
