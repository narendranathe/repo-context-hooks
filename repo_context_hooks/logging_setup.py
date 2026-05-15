"""Self-observability for repo-context-hooks.

Stdlib-only logging setup. WARNING records go to stderr by default; ERROR
records are also appended to ``<cache>/errors.log`` (rotated, 5 x 1 MB).
With ``--debug``, both streams promote to DEBUG and the file handler
captures full tracebacks.

Design contract (from issue #73 consensus spec):

1. The logger MUST NEVER raise into the host CLI. Set
   ``logging.raiseExceptions = False``, override ``RotatingFileHandler.emit``
   to swallow OSError, and write a one-time stderr breadcrumb on first
   failure so the adopter sees *why* file logging is off without spam.

2. The log directory MUST NOT be created on no-op runs (``--help``,
   ``--version``, argparse errors, successful commands that emit no errors).
   We achieve this by overriding ``RotatingFileHandler._open`` to create
   the parent dir lazily on first ERROR emit. ``--help`` exits in
   ``argparse`` before ``main()`` ever calls ``configure_logging``; even
   when ``configure_logging`` is called, ``delay=True`` plus the ERROR
   level on the file handler means a successful no-error run never opens
   the file.

3. Path resolution mirrors ``telemetry._default_telemetry_base()`` exactly
   (XDG_CACHE_HOME on POSIX, LOCALAPPDATA on Windows, with safe fallbacks)
   so adopters get one mental model for "where does this tool put state".

The public surface (``configure_logging``, ``get_last_error``, ``log_path``,
``_LOG_DIR_OVERRIDE``) is what M6's ``verify`` command will import; the
underscore-prefixed helpers are internal and may change.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

# Test seam mirroring ``consent._CONFIG_PATH_OVERRIDE``. Tests assign a
# ``tmp_path`` to bypass the real XDG/LOCALAPPDATA lookup. Production code
# never writes to this.
_LOG_DIR_OVERRIDE: Optional[Path] = None


# Indirection used by tests that need to simulate a different platform
# without monkey-patching ``os.name`` (which on Windows triggers
# ``PosixPath`` instantiation and ``NotImplementedError``).
def _is_windows() -> bool:
    return os.name == "nt"


# Internal: ``configure_logging`` is idempotent. A second call in the same
# process is a no-op.
_CONFIGURED = False

_PACKAGE_LOGGER = "repo_context_hooks"
_LOG_FILE_NAME = "errors.log"
_MAX_BYTES = 1_048_576  # 1 MB
_BACKUP_COUNT = 4  # 1 active + 4 rotated = 5 files x 1 MB total (issue #73)

_FORMAT_DEFAULT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_FORMAT_STREAM = "%(levelname)s %(name)s: %(message)s"


def _default_log_dir() -> Path:
    """Resolve the cache directory for ``errors.log``.

    Order: explicit test override > ``REPO_CONTEXT_HOOKS_LOG_DIR`` env >
    ``LOCALAPPDATA`` (Windows) > ``XDG_CACHE_HOME`` (POSIX) >
    ``~/AppData/Local`` or ``~/.cache`` fallback.

    Mirrors ``telemetry._default_telemetry_base()`` byte-for-byte, swapping
    the leaf component from ``telemetry`` to ``logs``. Adopters who set
    ``XDG_CACHE_HOME`` once get both this tool's telemetry AND error log in
    a predictable spot.
    """
    if _LOG_DIR_OVERRIDE is not None:
        return _LOG_DIR_OVERRIDE

    configured = os.environ.get("REPO_CONTEXT_HOOKS_LOG_DIR")
    if configured:
        return Path(configured)

    if _is_windows():
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "repo-context-hooks" / "logs"
        return _safe_home() / "AppData" / "Local" / "repo-context-hooks" / "logs"

    cache_home = os.environ.get("XDG_CACHE_HOME")
    if cache_home:
        return Path(cache_home) / "repo-context-hooks" / "logs"
    return _safe_home() / ".cache" / "repo-context-hooks" / "logs"


def _safe_home() -> Path:
    """Return ``Path.home()``, falling back to ``tempfile.gettempdir()``.

    ``Path.home()`` raises ``RuntimeError`` (NOT ``OSError``) when neither
    ``HOME``/``USERPROFILE`` is set nor a platform-specific lookup succeeds.
    This fires on Windows SYSTEM accounts with unset ``LOCALAPPDATA``, AWS
    Lambda layers, hermetic Bazel sandboxes, and distroless containers.

    The error is not caught by ``_SafeRotatingFileHandler``'s OSError shield
    because it fires inside ``_default_log_dir()`` long before any handler
    receives a record. Without this fallback, ``configure_logging`` crashes
    the entire CLI on those platforms — including ``doctor``, the very
    command an adopter would run to diagnose a broken environment.

    ``tempfile.gettempdir()`` is the stdlib's totalised fallback: it never
    raises and is defined on every platform Python supports. The lazy
    ``mkdir`` + OSError-swallowing ``emit`` then handle the case where even
    tempdir is read-only.
    """
    try:
        return Path.home()
    except RuntimeError:
        return Path(tempfile.gettempdir())


def log_path() -> Path:
    """Return the resolved path to ``errors.log`` (does not create it)."""
    return _default_log_dir() / _LOG_FILE_NAME


class _SafeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """RotatingFileHandler with three production-grade safety properties.

    1. **Lazy parent-dir creation**: ``_open()`` runs ``mkdir(parents=True)``
       on the parent before opening the file, so the cache dir is never
       created until the first ERROR record is actually emitted. Combined
       with ``delay=True`` this means ``--help``, ``--version``, and
       successful no-error runs leave no filesystem trace.

    2. **Never raises into the host CLI**: ``emit()`` wraps the inherited
       implementation in try/except. On the FIRST failure we write a
       one-line stderr breadcrumb naming the OSError so a curious adopter
       on a read-only filesystem can diagnose without enabling debug.
       Subsequent failures latch silently — no spam.

    3. **No traceback on emit failure**: ``handleError`` is overridden to
       a no-op so we don't dump a 12-line stack to the user's terminal
       when the cache happens to be read-only.
    """

    _failure_announced: bool = False
    _disabled: bool = False

    def _open(self):  # type: ignore[override]
        Path(self.baseFilename).parent.mkdir(parents=True, exist_ok=True)
        return super()._open()

    def emit(self, record: logging.LogRecord) -> None:  # type: ignore[override]
        # Bypass ``RotatingFileHandler.emit``'s built-in ``except Exception:
        # self.handleError(...)``. That catch routes our OSError into a
        # silent traceback dump, eating the breadcrumb we want to emit on
        # the first failure. Calling ``FileHandler.emit`` directly lets us
        # observe the exception, write a one-line stderr message, and
        # latch the handler off so we don't retry-and-fail on every record.
        if _SafeRotatingFileHandler._disabled:
            return
        try:
            if self.shouldRollover(record):
                self.doRollover()
            logging.FileHandler.emit(self, record)
        except OSError as exc:
            _SafeRotatingFileHandler._disabled = True
            if not _SafeRotatingFileHandler._failure_announced:
                _SafeRotatingFileHandler._failure_announced = True
                sys.stderr.write(
                    f"repo-context-hooks: cannot open error log ({exc!s}); "
                    f"continuing without file logging\n"
                )
        except Exception:
            # Defence in depth: any non-OSError (formatter bug, stream
            # closed unexpectedly) latches off too, but silently — we have
            # no useful breadcrumb to give the user.
            _SafeRotatingFileHandler._disabled = True

    def handleError(self, record: logging.LogRecord) -> None:  # type: ignore[override]
        # Suppress the default traceback dump. ``emit()`` already announced
        # the failure exactly once.
        return None


def configure_logging(debug: bool = False) -> None:
    """Configure the package-wide logger.

    Idempotent: a second call on the same process is a no-op (preserves
    handlers from the first call). Safe to invoke from every CLI entry
    point; safe to skip entirely on no-op runs (argparse short-circuits
    before this is reached).

    Attaches a stderr ``StreamHandler`` (WARNING, or DEBUG when
    ``debug=True``) eagerly. The file handler is also attached eagerly but
    with ``delay=True`` and ERROR threshold (DEBUG when ``debug=True``); it
    does not open the file or create the parent dir until the first record
    above its threshold actually fires.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    # Library-wide kill switch: never let a logging failure raise into a
    # caller. ``logging`` defaults this to True in user code; we flip it.
    logging.raiseExceptions = False

    logger = logging.getLogger(_PACKAGE_LOGGER)
    logger.setLevel(logging.DEBUG if debug else logging.WARNING)
    # Don't bubble up to root. Adopters who configure root logging in their
    # own apps shouldn't see our records duplicated.
    logger.propagate = False

    stream = logging.StreamHandler(sys.stderr)
    stream.setLevel(logging.DEBUG if debug else logging.WARNING)
    stream.setFormatter(logging.Formatter(_FORMAT_STREAM))
    logger.addHandler(stream)

    file_handler = _SafeRotatingFileHandler(
        str(log_path()),
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
        delay=True,
    )
    file_handler.setLevel(logging.DEBUG if debug else logging.ERROR)
    file_handler.setFormatter(logging.Formatter(_FORMAT_DEFAULT))
    logger.addHandler(file_handler)

    _CONFIGURED = True


def reset_for_tests() -> None:
    """Clear handlers and the configured flag.

    Tests that exercise multiple debug-on/debug-off configurations need to
    reset module-global state. Production code never calls this.
    """
    global _CONFIGURED
    logger = logging.getLogger(_PACKAGE_LOGGER)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass
    _CONFIGURED = False
    _SafeRotatingFileHandler._failure_announced = False
    _SafeRotatingFileHandler._disabled = False


def get_last_error() -> Optional[str]:
    """Return the last non-blank line of ``errors.log``, or None.

    Reads from end-of-file in 4 KB chunks so the function stays O(1) on
    arbitrarily large logs (we cap at 64 KB scanned in case the entire file
    is one record). Decodes with ``errors="replace"`` so a corrupt tail
    cannot crash ``doctor``. Returns None when:
      - the log file does not exist (no errors logged yet)
      - the log file is empty (rotated immediately)
      - no non-blank line is found within the scan budget

    Public helper — M6's ``verify`` command imports this to surface the
    same line.
    """
    path = log_path()
    try:
        if not path.exists():
            return None
        size = path.stat().st_size
        if size == 0:
            return None
        scan = min(size, 65_536)
        with path.open("rb") as fh:
            fh.seek(size - scan)
            tail = fh.read(scan)
    except OSError:
        return None

    # Decode permissively. errors="replace" turns invalid UTF-8 into U+FFFD
    # rather than raising — important if a hook subprocess wrote raw bytes.
    text = tail.decode("utf-8", errors="replace")
    for line in reversed(text.splitlines()):
        stripped = line.strip()
        if stripped:
            return stripped
    return None
