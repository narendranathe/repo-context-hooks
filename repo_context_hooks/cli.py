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
from .telemetry import (
    experiment_finish,
    experiment_start,
    experiment_status,
    export_impact_report,
    measure_impact,
    write_public_monitoring_snapshot,
)
from . import consent as _consent_mod


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
    install.add_argument(
        "--dedup",
        action="store_true",
        help="Remove duplicate hook entries from settings.json before installing.",
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
    measure.add_argument(
        "--badge",
        action="store_true",
        help="Output an SVG badge showing the current contract score.",
    )
    measure.add_argument(
        "--badge-out",
        metavar="PATH",
        help="Write the SVG badge to this file path (implies --badge).",
    )
    measure.add_argument(
        "--open",
        action="store_true",
        help="Generate the local monitoring dashboard and open it in the browser.",
    )
    measure.add_argument(
        "--forecast",
        action="store_true",
        help="Show a 30-day activity projection based on current daily rate.",
    )
    measure.add_argument(
        "--branches",
        action="store_true",
        help="Show per-branch score and session count, sorted by last seen.",
    )
    measure.add_argument(
        "--clean-ghosts",
        action="store_true",
        help="Remove test-run ghost repos from the telemetry store (dry-run by default).",
    )
    measure.add_argument(
        "--no-dry-run",
        action="store_false",
        dest="dry_run",
        help="Actually delete ghost repos (use with --clean-ghosts).",
    )
    measure.add_argument(
        "positional_args",
        nargs="*",
        metavar="SUBCOMMAND [ARGS...]",
        help=(
            "Sub-commands: "
            "'export [--format markdown|json]' — redacted shareable impact report; "
            "'experiment [start|finish|status]' — guided before/after continuity experiment."
        ),
    )
    measure.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format for 'export' (default: markdown).",
    )
    measure.add_argument(
        "--redact",
        action="store_true",
        default=True,
        help="Redact local filesystem paths from the export (default: on; always enforced).",
    )
    measure.add_argument(
        "--output",
        "-o",
        metavar="PATH",
        help="Write export output to this file path instead of stdout.",
    )
    measure.add_argument(
        "--experiment-dir",
        metavar="PATH",
        default=None,
        help=(
            "Directory to store before.json/after.json for experiments "
            "(default: .repo-context-hooks/experiment in the repo root)."
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

    checkpoint = subparsers.add_parser(
        "checkpoint",
        help="Append a decision/handoff summary to specs/README.md Session Log.",
    )
    checkpoint.add_argument(
        "--message",
        required=True,
        help="Decision summary to record (what was built, key decisions, next step).",
    )
    checkpoint.add_argument(
        "--path",
        default=".",
        help="Repository root (default: current directory).",
    )

    telemetry = subparsers.add_parser(
        "telemetry",
        help="Manage remote telemetry consent (opt-in, local config only).",
    )
    telemetry_sub = telemetry.add_subparsers(dest="telemetry_subcommand", required=True)

    telemetry_sub.add_parser(
        "status",
        help="Show the current remote telemetry consent state.",
    )

    telemetry_enable = telemetry_sub.add_parser(
        "enable",
        help="Opt in to remote telemetry. Shows consent text and prompts for confirmation.",
    )
    telemetry_enable.add_argument(
        "--yes",
        action="store_true",
        help="Skip interactive confirmation prompt (for CI/non-interactive use).",
    )

    telemetry_sub.add_parser(
        "disable",
        help="Opt out of remote telemetry.",
    )

    telemetry_preview = telemetry_sub.add_parser(
        "preview",
        help="Preview the payload that would be sent if telemetry were enabled.",
    )
    telemetry_preview.add_argument(
        "--repo-root",
        default=None,
        help="Repository root to include continuity score in the preview (optional).",
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

    # Auto-dedup on every install (also triggered explicitly by --dedup flag)
    from .platforms.runtime import deduplicate_hooks
    dedup_result = deduplicate_hooks(Path.home())
    if dedup_result.get("removed", 0) > 0:
        print(f"Removed {dedup_result['removed']} duplicate hook entries")

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


def _resolve_experiment_dir(args: argparse.Namespace, repo_root: Path) -> Path:
    raw = getattr(args, "experiment_dir", None)
    if raw:
        p = Path(raw)
        return p if p.is_absolute() else repo_root / p
    return repo_root / ".repo-context-hooks" / "experiment"


def _measure(args: argparse.Namespace) -> int:
    if getattr(args, "clean_ghosts", False):
        from .telemetry import purge_ghost_repos
        dry_run = getattr(args, "dry_run", True)
        result = purge_ghost_repos(dry_run=dry_run)
        action = "Would remove" if dry_run else "Removed"
        freed_kb = result["bytes_freed"] // 1024
        print(f"{action} {result['removed']} ghost repo dirs ({freed_kb} KB freed)")
        if result["dirs"]:
            for d in result["dirs"]:
                print(f"  - {d}")
        if dry_run and result["removed"] > 0:
            print("Re-run with --no-dry-run to actually delete.")
        return 0

    repo_root = Path(args.repo_root).resolve()

    positional = list(getattr(args, "positional_args", None) or [])

    if positional and positional[0] == "export":
        report = measure_impact(repo_root=repo_root)
        output = export_impact_report(
            report,
            format=getattr(args, "format", "markdown"),
            redact=True,
        )
        out_path = getattr(args, "output", None)
        if out_path:
            Path(out_path).write_text(output, encoding="utf-8")
            print(f"Export written to: {out_path}")
        else:
            print(output)
        return 0

    if positional and positional[0] == "experiment":
        exp_dir = _resolve_experiment_dir(args, repo_root)
        sub = positional[1] if len(positional) > 1 else "status"
        if sub == "start":
            try:
                before_path = experiment_start(repo_root, exp_dir)
                print(f"Before snapshot: {before_path}")
            except FileExistsError as exc:
                print(f"Error: {exc}")
                return 1
        elif sub == "finish":
            try:
                experiment_finish(repo_root, exp_dir)
            except FileNotFoundError as exc:
                print(f"Error: {exc}")
                return 1
        elif sub == "status":
            status = experiment_status(exp_dir)
            print(status["message"])
        else:
            print(f"Unknown experiment subcommand: {sub!r}")
            print("Usage: repo-context-hooks measure experiment [start|finish|status]")
            return 1
        return 0

    if getattr(args, "forecast", False):
        from .telemetry import forecast_activity
        forecast = forecast_activity(repo_root)
        if getattr(args, "json", False):
            _print_json(forecast.to_dict())
        else:
            print(forecast.render())
        return 0

    if getattr(args, "branches", False):
        from .telemetry import branch_scores
        stats = branch_scores(repo_root)
        if getattr(args, "json", False):
            _print_json([s.to_dict() for s in stats])
        else:
            if not stats:
                print("No branch data found.")
            else:
                print(f"{'Branch':<30} {'Sessions':>8} {'Avg Score':>9} {'Last Seen'}")
                print("-" * 65)
                for s in stats:
                    print(f"{s.branch:<30} {s.session_count:>8} {s.avg_score:>9} {s.last_seen[:10]}")
        return 0

    report = measure_impact(repo_root=repo_root)

    badge_out = getattr(args, "badge_out", None)
    show_badge = getattr(args, "badge", False) or badge_out is not None
    if show_badge:
        from .badge import render_badge
        svg = render_badge(report.current_score, report.usability.lifecycle_coverage)
        if badge_out:
            Path(badge_out).write_text(svg, encoding="utf-8")
            print(f"Badge written to: {badge_out}")
        else:
            print(svg)
        return 0

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

    if getattr(args, "open", False):
        import webbrowser
        from .telemetry import write_monitoring_dashboard
        dash = write_monitoring_dashboard(report)
        webbrowser.open(dash.as_uri())
        print(f"Opened: {dash}")
        return 0

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


def _checkpoint(args: argparse.Namespace) -> int:
    import subprocess
    import sys

    repo_root_raw = ""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=args.path,
            check=True,
            capture_output=True,
            text=True,
        )
        repo_root_raw = result.stdout.strip()
    except Exception:
        pass

    if not repo_root_raw:
        print("error: no git repo found at the specified path")
        return 1

    specs_readme = Path(repo_root_raw) / "specs" / "README.md"
    if not specs_readme.exists():
        print("error: no workspace contract found — run `repo-context-hooks init` first")
        return 1

    bundle_script = Path(__file__).parent / "bundle" / "skills" / "context-handoff-hooks" / "scripts" / "repo_specs_memory.py"
    result = subprocess.run(
        [sys.executable, str(bundle_script), "decision", "--message", args.message],
        cwd=repo_root_raw,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr.strip())
        return result.returncode

    print(result.stdout.strip())
    return 0


def _telemetry_cmd(args: argparse.Namespace) -> int:
    sub = args.telemetry_subcommand

    if sub == "status":
        state = _consent_mod.get_consent_state()
        status = state["status"]
        config_path = state["config_path"]

        if status == "enabled":
            print(f"Remote telemetry: enabled")
            print(f"Install ID: {state['install_id']}")
            if state["enabled_at"]:
                print(f"Enabled at: {state['enabled_at']}")
            print(f"Config: {config_path}")
            print("Note: Remote collector endpoint not yet configured. No data is being sent.")
        elif status == "disabled":
            print("Remote telemetry: disabled")
            print(f"Config: {config_path}")
        else:
            print("Remote telemetry: not configured")
            print("Install ID: (will be generated on first enable)")
            print(f"Config: {config_path}")
        return 0

    if sub == "enable":
        use_yes = getattr(args, "yes", False)
        if not use_yes:
            # Interactive mode: show consent text and prompt.
            print(_consent_mod.CONSENT_TEXT)
            print()
            try:
                answer = input("Enable remote telemetry? [y/N]: ").strip().lower()
            except (EOFError, OSError):
                # Non-interactive environment without --yes flag.
                print("Non-interactive environment detected. Use --yes to skip the prompt.")
                print("Telemetry remains disabled.")
                return 0
            if answer not in ("y", "yes"):
                print("Telemetry remains disabled.")
                return 0

        state = _consent_mod.enable_consent()
        print("Remote telemetry enabled.")
        print(f"Install ID: {state['install_id']}")
        print(f"Config: {state['config_path']}")
        print("Note: Remote collector endpoint not yet configured. No data is being sent.")
        return 0

    if sub == "disable":
        state = _consent_mod.disable_consent()
        print("Remote telemetry disabled.")
        print(f"Config: {state['config_path']}")
        return 0

    if sub == "preview":
        repo_root: Path | None = None
        raw_root = getattr(args, "repo_root", None)
        if raw_root is not None:
            repo_root = Path(raw_root).resolve()
        payload = _consent_mod.preview_payload(repo_root=repo_root)
        _print_json(payload)
        return 0

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
    if args.command == "checkpoint":
        return _checkpoint(args)
    if args.command == "telemetry":
        return _telemetry_cmd(args)
    parser.error("Unknown command")
    return 2
