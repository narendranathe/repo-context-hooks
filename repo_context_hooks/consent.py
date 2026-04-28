"""Consent management for remote telemetry.

Manages the local consent config file. No data is sent remotely until a real
collector endpoint exists, a published privacy policy is in place, and this
module is wired to an actual upload path.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any


CONSENT_TEXT = """\
repo-context-hooks can optionally send privacy-preserving usage metrics to the \
maintainer so the community can see adoption and continuity impact.

Collected: anonymous install id, package version, platform adapter, lifecycle \
event counts, continuity score, estimated baseline score, and coarse OS/runtime \
information.

Never collected: source code, prompts, compact summaries, issue bodies, secrets, \
environment values, resumes, or personal files.

Remote telemetry is optional and can be disabled at any time.\
"""

# Allow tests to override the config path via this module-level variable.
_CONFIG_PATH_OVERRIDE: Path | None = None


def consent_config_path() -> Path:
    """Return the platform-appropriate path to the consent config file."""
    if _CONFIG_PATH_OVERRIDE is not None:
        return _CONFIG_PATH_OVERRIDE

    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            base = Path(local_app_data) / "repo-context-hooks"
        else:
            base = Path.home() / "AppData" / "Local" / "repo-context-hooks"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            base = Path(xdg) / "repo-context-hooks"
        else:
            base = Path.home() / ".config" / "repo-context-hooks"

    return base / "consent.json"


def _read_config() -> dict[str, Any]:
    path = consent_config_path()
    if not path.exists():
        return {}
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _write_config(data: dict[str, Any]) -> None:
    path = consent_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def get_consent_state() -> dict[str, Any]:
    """Return the current consent state.

    Returns a dict with keys:
      - status: "enabled" | "disabled" | "not_set"
      - enabled_at: ISO timestamp string or None
      - install_id: UUID string or None
      - config_path: path to the config file (as string)
    """
    cfg = _read_config()
    consented = cfg.get("consented")
    if consented is True:
        status = "enabled"
    elif consented is False:
        status = "disabled"
    else:
        status = "not_set"

    return {
        "status": status,
        "enabled_at": cfg.get("enabled_at"),
        "install_id": cfg.get("install_id"),
        "config_path": str(consent_config_path()),
    }


def enable_consent() -> dict[str, Any]:
    """Write consent=True to the config. Generate install_id if not present.

    Returns the new consent state dict.
    """
    cfg = _read_config()
    if not cfg.get("install_id"):
        cfg["install_id"] = str(uuid.uuid4())
    cfg["consented"] = True
    cfg["enabled_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    _write_config(cfg)
    return get_consent_state()


def disable_consent() -> dict[str, Any]:
    """Write consent=False to the config.

    Returns the new consent state dict.
    """
    cfg = _read_config()
    cfg["consented"] = False
    _write_config(cfg)
    return get_consent_state()


def is_consented() -> bool:
    """Return True only if consent status is explicitly 'enabled'."""
    return get_consent_state()["status"] == "enabled"


def preview_payload(repo_root: Path | None = None) -> dict[str, Any]:
    """Return the payload that WOULD be sent if consent is given.

    No local paths are included. This is safe to display to users.
    """
    state = get_consent_state()
    install_id = state["install_id"] or "not-yet-generated"

    # Resolve package version without leaking local paths.
    package_version = _get_package_version()

    continuity_score = None
    estimated_baseline_score = None
    lifecycle_event_counts: dict[str, int] = {}

    if repo_root is not None:
        try:
            from .telemetry import measure_impact
            report = measure_impact(repo_root=repo_root)
            continuity_score = report.current_score
            estimated_baseline_score = report.estimated_baseline_score
            lifecycle_event_counts = dict(report.event_counts)
        except Exception:
            pass

    return {
        "install_id": install_id,
        "package_version": package_version,
        "platform_adapter": "unknown",
        "os_family": sys.platform,
        "python_minor": f"{sys.version_info.major}.{sys.version_info.minor}",
        "continuity_score": continuity_score,
        "estimated_baseline_score": estimated_baseline_score,
        "lifecycle_event_counts": lifecycle_event_counts,
        "collector_endpoint": "not yet configured",
        "disclaimer": "This is a preview of data that WOULD be sent. No data has been sent.",
    }


def _get_package_version() -> str:
    """Return the installed package version, with a pyproject.toml fallback."""
    try:
        from importlib.metadata import version as _meta_version
        return _meta_version("repo-context-hooks")
    except Exception:
        pass

    # Fallback: read from pyproject.toml next to the package root.
    try:
        import re
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        if pyproject.exists():
            text = pyproject.read_text(encoding="utf-8")
            match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
            if match:
                return match.group(1)
    except Exception:
        pass

    return "unknown"
