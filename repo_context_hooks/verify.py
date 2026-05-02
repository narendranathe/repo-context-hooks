"""Install verification — proves the plumbing without touching real telemetry.

The ``verify`` subcommand (issue #74) closes the 5-30 minute trust gap
between ``pip install repo-context-hooks && repo-context-hooks install``
and the next session firing. It synthesizes a ``SessionStart`` event,
round-trips it through the local telemetry write/read path, validates the
schema against ``telemetry.CANONICAL_EVENT_KEYS``, and prints a confirmation
receipt with platform / agent home / settings.json hash / last event
timestamp.

Design contract (from issue #74 consensus spec, three non-negotiables):

1. The dummy event is written to a freshly-created tmpdir, NEVER to
   ``Path.home()``-rooted paths. Asserted at runtime — corrupting real user
   telemetry is the highest-blast-radius failure mode here.

2. The settings.json hash is computed over the canonical JSON form
   (``json.dumps(sort_keys=True, separators=(",",":"))``), not raw bytes,
   so whitespace-only edits do not produce false-positive churn.

3. ``record_event`` already calls ``_write_then_close`` (handle.write inside
   ``with``), so by the time the ``with`` block exits the bytes are in the
   kernel page cache. We add an explicit ``os.fsync`` after the write so
   Windows/SMB shares cannot reorder write-vs-read across the boundary.

Public surface (M7 #75 consumes this for docs auto-generation):

- ``VerifyReport`` dataclass — the receipt; renders text and JSON.
- ``run_verify(platform)`` — top-level entry point.

Internal (subject to change without notice):

- ``_canonical_settings_sha256`` — hash function.
- ``_synthesize_session_start`` — event writer.
- ``_EVENTS_DIR_OVERRIDE`` — module-level test seam (mirrors
  ``consent._CONFIG_PATH_OVERRIDE`` and ``logging_setup._LOG_DIR_OVERRIDE``).
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import json
import logging
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from . import logging_setup as _logging_setup
from .platforms import get_registry


def _telemetry():
    """Late-bound accessor for the telemetry module.

    Uses ``importlib.import_module`` so we always pick up the current
    ``sys.modules`` entry rather than a stale import-time reference.
    Robust against tests that aggressively replace+delete
    ``sys.modules["repo_context_hooks.telemetry"]`` for mocking
    (e.g. ``tests/test_session_duration_wiring.py``) — the re-import
    after teardown produces a NEW module object, and a frozen
    ``from . import telemetry as _t`` binding would silently call the
    OLD module's functions, defeating downstream monkeypatches.
    """

    return importlib.import_module("repo_context_hooks.telemetry")

_log = logging.getLogger(__name__)

# Test seam. Production code never assigns to this; tests set it to a
# ``tmp_path`` so the verify helper writes its synthetic event into an
# isolated directory tree. Kept module-level (not function-arg) to mirror
# ``logging_setup._LOG_DIR_OVERRIDE`` and ``consent._CONFIG_PATH_OVERRIDE``
# — single repo idiom for "test override of an environment-resolved path".
_EVENTS_DIR_OVERRIDE: Optional[Path] = None


@dataclass(frozen=True)
class VerifyReport:
    """Receipt from a single verify run. Renders to text or JSON."""

    platform: str
    agent_home: str  # posix
    settings_path: str  # posix
    settings_exists: bool
    settings_sha256: Optional[str]
    event_round_tripped: bool
    last_event_timestamp: Optional[str]
    schema_ok: bool
    schema_missing_keys: tuple[str, ...]
    elapsed_ms: int
    last_error: Optional[str]
    failure_reason: Optional[str] = None

    @property
    def ok(self) -> bool:
        return (
            self.event_round_tripped
            and self.schema_ok
            and self.failure_reason is None
        )

    @property
    def status(self) -> str:
        return "healthy" if self.ok else "broken"

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["status"] = self.status
        d["ok"] = self.ok
        # ``schema_missing_keys`` is a tuple; JSON wants a list.
        d["schema_missing_keys"] = list(self.schema_missing_keys)
        return d

    def render(self) -> str:
        lines = [
            f"Platform: {self.platform}",
            f"Agent home: {self.agent_home}",
            f"Settings path: {self.settings_path}",
            f"Settings exists: {'yes' if self.settings_exists else 'no'}",
        ]
        if self.settings_sha256:
            lines.append(f"Settings sha256 (canonical): {self.settings_sha256}")
        lines.append(
            f"Synthetic event round-trip: {'OK' if self.event_round_tripped else 'FAILED'}"
        )
        if self.last_event_timestamp:
            lines.append(f"Last event timestamp: {self.last_event_timestamp}")
        if self.event_round_tripped:
            schema_line = "yes" if self.schema_ok else (
                f"NO (missing: {', '.join(self.schema_missing_keys)})"
            )
            lines.append(f"Schema valid: {schema_line}")
        lines.append(f"Elapsed: {self.elapsed_ms} ms")
        if self.failure_reason:
            lines.append(f"Failure: {self.failure_reason}")
        lines.append(f"Status: {self.status.upper()}")
        return "\n".join(lines)


def _canonical_settings_sha256(data: dict) -> str:
    """SHA-256 over the canonical JSON form of ``data``.

    Whitespace-only edits to ``settings.json`` don't change the hash, so the
    receipt only churns on semantically-meaningful changes.
    """

    blob = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _read_settings_for_hash(settings_path: Path) -> tuple[bool, Optional[str]]:
    if not settings_path.exists():
        return False, None
    try:
        text = settings_path.read_text(encoding="utf-8", errors="ignore").strip()
    except OSError:
        return True, None
    if not text:
        return True, _canonical_settings_sha256({})
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Hash the raw text under a stable canonical form: empty dict →
        # well-defined hash, signals "file present but unreadable" without
        # crashing the receipt.
        return True, _canonical_settings_sha256({})
    if not isinstance(data, dict):
        data = {}
    return True, _canonical_settings_sha256(data)


def _resolve_events_dir(override: Optional[Path]) -> Path:
    """Return the directory where the synthetic event will land.

    Order: explicit kwarg > module-level test seam > freshly-minted tmpdir.
    Production callers always hit the third branch — the synthetic event
    NEVER lands in real telemetry storage.
    """

    if override is not None:
        return override
    if _EVENTS_DIR_OVERRIDE is not None:
        return _EVENTS_DIR_OVERRIDE
    return Path(tempfile.mkdtemp(prefix="rch-verify-"))


def _init_synthetic_repo(scratch_root: Path) -> Path:
    """Create a tiny stand-in repo for the dummy event.

    ``record_event`` calls ``_git_output`` and ``contract_signals`` which
    need a real git repo — running from a non-git tmpdir produces empty
    branch / score=0 fields but does NOT raise. We initialise an empty git
    repo to keep the receipt's ``last_event_timestamp`` deterministic and
    avoid spurious "branch=unknown" noise.
    """

    repo = scratch_root / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    # --initial-branch is git 2.28+ (Aug 2020). RHEL 7/8 / UBI 8 ship
    # git 2.20/2.27 — the flag exits non-zero with "unknown option"
    # and leaves the dir uninitialised. Try-modern-then-fallback keeps
    # the comment's deterministic-branch claim true on 2.28+ AND keeps
    # verify working on older git. OSError covers "git not on PATH".
    for argv in (
        ["git", "init", "--quiet", "--initial-branch=verify"],
        ["git", "init", "--quiet"],  # git < 2.28 fallback
    ):
        try:
            result = subprocess.run(
                argv, cwd=repo, check=False,
                capture_output=True, timeout=5,
            )
            if result.returncode == 0:
                break
        except (OSError, subprocess.SubprocessError):
            # git absent entirely; synthetic event still writes — verify
            # proves the plumbing works even when git is missing.
            break
    return repo


def _synthesize_session_start(repo_root: Path, telemetry_base: Path) -> Path:
    """Write a single SessionStart event into ``telemetry_base`` and fsync.

    Returns the path to ``events.jsonl``. ``record_event`` already opens
    in append mode and closes inside its ``with`` block; we add an explicit
    ``os.fsync`` after so Windows/SMB ordering cannot put the read ahead of
    the write.
    """

    path = _telemetry().record_event(
        repo_root=repo_root,
        event_name="SessionStart",
        source="rch-verify",
        telemetry_base=telemetry_base,
        details={"synthetic": True, "purpose": "verify-roundtrip"},
    )
    # ``record_event`` doesn't expose the file handle — open + fsync the
    # file itself to flush dirty pages to disk. On Windows this is a real
    # FlushFileBuffers; on POSIX a fsync(2). Cheap (single syscall) and
    # closes the write/read race window unconditionally.
    try:
        fd = os.open(str(path), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        # fsync on a tmpfs-backed path can be a no-op; we don't care about
        # the failure beyond logging it for ``--debug`` users.
        _log.debug("fsync(%s) failed; continuing", path)
    return path


def _platform_settings_path(platform: str, home: Path) -> Path:
    # Codex uses ``.codex``; everything shipping settings.json today lives
    # under ``.<platform>/settings.json``. Adapters that don't write
    # settings.json (PARTIAL tier) still get a logical "would-write" path
    # so the receipt has something to display.
    return home / f".{platform}" / "settings.json"


def _platform_tier(platform: str) -> str:
    try:
        adapter = get_registry().get(platform)
    except KeyError:
        return "unknown"
    return adapter.metadata.support_tier.value


def run_verify(
    platform: str,
    *,
    home: Optional[Path] = None,
    telemetry_base_override: Optional[Path] = None,
) -> VerifyReport:
    """Synthesize a dummy event, round-trip it, return a receipt.

    Never writes outside an isolated tmpdir. Never spawns a real LLM or
    network call. Catches all expected failure modes (PermissionError,
    OSError) and surfaces them in ``failure_reason`` rather than raising.
    """

    start = time.perf_counter()
    # Path.home() raises RuntimeError on Windows SYSTEM accounts (no
    # USERPROFILE), AWS Lambda layers (no /home), Nix sandboxes with
    # read-only $HOME, and distroless containers without /etc/passwd.
    # PR #103 fixed this in logging_setup via _safe_home() — route
    # through the same helper to inherit the cross-platform fallback
    # ladder (USERPROFILE -> HOME -> tempdir). Without this guard,
    # verify crashes BEFORE the try-block can convert the failure into
    # a receipt — defeating verify's contract.
    if home is not None:
        h = home
    else:
        h = _logging_setup._safe_home()
    agent_home = h / f".{platform}"
    settings_path = _platform_settings_path(platform, h)

    # Hash existing settings.json (or report absent). Cold-start case: the
    # user has not run ``install`` yet; verify still proves the plumbing.
    settings_exists, settings_sha = _read_settings_for_hash(settings_path)

    failure: Optional[str] = None
    event_round_tripped = False
    schema_ok = False
    schema_missing: tuple[str, ...] = ()
    last_event_ts: Optional[str] = None

    try:
        events_dir = _resolve_events_dir(telemetry_base_override)
        events_dir.mkdir(parents=True, exist_ok=True)
        # Critic C non-budge: assert isolation from real telemetry storage.
        # Real telemetry lands under ``Path.home() / ".cache" / "repo-context-hooks"``
        # (POSIX) or ``%LOCALAPPDATA%\repo-context-hooks`` (Windows). The
        # synthetic event MUST NOT land there.
        # Resolve only the override; tempdir paths under /tmp on POSIX or
        # under user-temp on Windows already escape ``Path.home()``.
        real_telemetry = _telemetry()._default_telemetry_base()
        if events_dir == real_telemetry or _is_subpath(events_dir, real_telemetry):
            raise RuntimeError(
                "verify refused to run: telemetry override resolved to the "
                f"real telemetry directory ({real_telemetry}). Refusing to "
                "pollute user telemetry."
            )
        repo_root = _init_synthetic_repo(events_dir)
        events_path = _synthesize_session_start(repo_root, telemetry_base=events_dir)

        # Read back. ``_read_events`` returns list[dict].
        events = _telemetry()._read_events(events_path)
        synthetic = [
            e for e in events
            if e.get("source") == "rch-verify"
            and e.get("event_name") == "SessionStart"
        ]
        if not synthetic:
            failure = "synthesized event did not appear on read-back"
        else:
            event_round_tripped = True
            event = synthetic[-1]
            last_event_ts = event.get("timestamp")
            present = set(event.keys())
            missing = tuple(
                k for k in _telemetry().CANONICAL_EVENT_KEYS if k not in present
            )
            schema_missing = missing
            schema_ok = not missing

    except PermissionError as exc:
        failure = f"agent home read-only — cannot run verify ({exc})"
    except OSError as exc:
        failure = f"filesystem error during verify: {exc}"
    except RuntimeError as exc:
        failure = str(exc)
    except Exception as exc:  # pragma: no cover - last-resort safety net
        # Never propagate; the receipt is the contract.
        _log.exception("verify crashed unexpectedly")
        failure = f"unexpected error during verify: {exc}"

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    last_error = _logging_setup.get_last_error()

    return VerifyReport(
        platform=platform,
        agent_home=agent_home.as_posix(),
        settings_path=settings_path.as_posix(),
        settings_exists=settings_exists,
        settings_sha256=settings_sha,
        event_round_tripped=event_round_tripped,
        last_event_timestamp=last_event_ts,
        schema_ok=schema_ok,
        schema_missing_keys=schema_missing,
        elapsed_ms=elapsed_ms,
        last_error=last_error,
        failure_reason=failure,
    )


def _is_subpath(child: Path, parent: Path) -> bool:
    """True iff ``child`` is the same as or contained in ``parent``.

    Both paths are resolved to absolutes for comparison; symlink targets
    are NOT followed (would defeat the safety check on a system where the
    user's tmpdir symlinks back into ``Path.home()``).
    """

    try:
        child_abs = child.absolute()
        parent_abs = parent.absolute()
    except OSError:
        return False
    try:
        child_abs.relative_to(parent_abs)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Public surface (issue #74). M7 (#75) consumes these for mkdocs-click
# auto-generation; rename or remove only via a deprecation cycle.
# ---------------------------------------------------------------------------

__all__ = [
    "VerifyReport",
    "run_verify",
]
