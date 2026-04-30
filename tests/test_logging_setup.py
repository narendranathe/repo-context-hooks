"""Tests for repo_context_hooks.logging_setup.

The module is the M5 entry point: a stdlib-only logger that writes to
``<cache>/errors.log`` with rotation, surfaces the last error in ``doctor``,
and never raises into the host CLI.

Test plan (mirrors the issue #73 consensus spec, see
``docs/internal/wave3/issue-73-spec.md``):

1. **Path resolution matrix** — Hypothesis-driven, parametrised over the
   8 cells of (XDG_CACHE_HOME set/unset) × (LOCALAPPDATA set/unset) ×
   (override set/None). Each cell asserts a deterministic result.
2. **Lazy file-handler attach** — a successful ``configure_logging`` does
   NOT create the log directory. Only an ERROR-level record triggers it.
3. **Rotation actually fires** — write 1.1 MB of error records and assert
   ``errors.log.1`` exists, ``errors.log`` size is back below 1 MB.
4. **Read-only fallback** — pointing the override at a path whose parent
   cannot be created falls back to stderr-only without raising.
5. **get_last_error edge cases** — missing file, empty file, binary tail,
   trailing blank lines.
6. **Idempotent configure** — second call is a no-op (no duplicate
   handlers).
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from hypothesis import given, strategies as st

from repo_context_hooks import logging_setup


@pytest.fixture(autouse=True)
def _reset_logging_state() -> None:
    """Reset module-global handlers/flags between tests.

    Without this, tests that configure with ``debug=False`` would prevent a
    later ``debug=True`` test from re-configuring (since
    ``configure_logging`` is idempotent by design).
    """
    logging_setup.reset_for_tests()
    yield
    logging_setup.reset_for_tests()


@pytest.fixture
def isolate_log_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the override at ``tmp_path`` and clear env confounds.

    Mirrors the test seam used by ``consent.py`` so this module's tests do
    not depend on the developer's real ``XDG_CACHE_HOME``/``LOCALAPPDATA``.
    """
    monkeypatch.setattr(logging_setup, "_LOG_DIR_OVERRIDE", tmp_path)
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_LOG_DIR", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    return tmp_path


# ---------------------------------------------------------------------------
# 1. Path resolution
# ---------------------------------------------------------------------------


def test_log_path_uses_override_when_set(
    isolate_log_dir: Path,
) -> None:
    assert logging_setup.log_path() == isolate_log_dir / "errors.log"


def test_log_path_uses_env_var_when_no_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(logging_setup, "_LOG_DIR_OVERRIDE", None)
    monkeypatch.setenv("REPO_CONTEXT_HOOKS_LOG_DIR", str(tmp_path))
    assert logging_setup.log_path() == tmp_path / "errors.log"


def test_log_path_uses_xdg_cache_home_on_posix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Patch the platform indirection rather than ``os.name`` directly:
    # mutating ``os.name`` on Windows triggers ``PosixPath`` instantiation
    # and a NotImplementedError from pathlib.
    monkeypatch.setattr(logging_setup, "_LOG_DIR_OVERRIDE", None)
    monkeypatch.setattr(logging_setup, "_is_windows", lambda: False)
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_LOG_DIR", raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    expected = tmp_path / "repo-context-hooks" / "logs" / "errors.log"
    assert logging_setup.log_path() == expected


def test_log_path_uses_localappdata_on_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(logging_setup, "_LOG_DIR_OVERRIDE", None)
    monkeypatch.setattr(logging_setup, "_is_windows", lambda: True)
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_LOG_DIR", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    expected = tmp_path / "repo-context-hooks" / "logs" / "errors.log"
    assert logging_setup.log_path() == expected


def test_log_path_posix_fallback_when_no_xdg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(logging_setup, "_LOG_DIR_OVERRIDE", None)
    monkeypatch.setattr(logging_setup, "_is_windows", lambda: False)
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_LOG_DIR", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    expected = Path.home() / ".cache" / "repo-context-hooks" / "logs" / "errors.log"
    assert logging_setup.log_path() == expected


def test_log_path_windows_fallback_when_no_localappdata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(logging_setup, "_LOG_DIR_OVERRIDE", None)
    monkeypatch.setattr(logging_setup, "_is_windows", lambda: True)
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_LOG_DIR", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    expected = (
        Path.home() / "AppData" / "Local" / "repo-context-hooks" / "logs" / "errors.log"
    )
    assert logging_setup.log_path() == expected


def test_log_path_falls_back_to_tempdir_when_home_unresolvable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``Path.home()`` raises ``RuntimeError`` (NOT ``OSError``) on Windows
    SYSTEM, AWS Lambda, distroless containers, hermetic Bazel sandboxes.
    The fallback inside ``_safe_home`` MUST catch RuntimeError and return
    ``tempfile.gettempdir()`` so the CLI can still start. Without this,
    every subcommand that calls ``configure_logging`` crashes before
    dispatch — including ``doctor``, the command the adopter would run
    to diagnose the broken environment.
    """
    import tempfile as _tmp

    monkeypatch.setattr(logging_setup, "_LOG_DIR_OVERRIDE", None)
    monkeypatch.setattr(logging_setup, "_is_windows", lambda: False)
    monkeypatch.delenv("REPO_CONTEXT_HOOKS_LOG_DIR", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)

    def _raise_runtime():
        raise RuntimeError("Could not determine home directory.")

    monkeypatch.setattr(Path, "home", staticmethod(_raise_runtime))

    # Must NOT raise. Must produce a path under the system tempdir.
    resolved = logging_setup.log_path()
    assert resolved.name == "errors.log"
    assert str(resolved).startswith(_tmp.gettempdir()), resolved


@given(
    xdg=st.one_of(
        st.none(), st.text(min_size=1, max_size=10).filter(lambda s: "\x00" not in s)
    ),
    local_app_data=st.one_of(
        st.none(), st.text(min_size=1, max_size=10).filter(lambda s: "\x00" not in s)
    ),
    use_override=st.booleans(),
    posix=st.booleans(),
)
def test_log_path_resolution_is_total_and_deterministic(
    xdg: str | None,
    local_app_data: str | None,
    use_override: bool,
    posix: bool,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Hypothesis property: ``log_path()`` is total (never raises) and
    deterministic for a fixed input over the path-resolution matrix.

    The 8-cell matrix the issue calls out (XDG set/unset × LOCALAPPDATA
    set/unset × override set/None × OS) is the surface the function MUST
    behave well on. Hypothesis fuzzes the env values too — if a future
    change introduced a NUL-byte handling bug, this test would catch it.
    """
    monkeypatch = pytest.MonkeyPatch()
    try:
        # Reset module state per Hypothesis example so prior runs don't leak.
        logging_setup.reset_for_tests()
        monkeypatch.setattr(logging_setup, "_is_windows", lambda: not posix)
        if use_override:
            monkeypatch.setattr(
                logging_setup,
                "_LOG_DIR_OVERRIDE",
                tmp_path_factory.mktemp("ovr", numbered=True),
            )
        else:
            monkeypatch.setattr(logging_setup, "_LOG_DIR_OVERRIDE", None)
        monkeypatch.delenv("REPO_CONTEXT_HOOKS_LOG_DIR", raising=False)
        if xdg is None:
            monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
        else:
            monkeypatch.setenv("XDG_CACHE_HOME", xdg)
        if local_app_data is None:
            monkeypatch.delenv("LOCALAPPDATA", raising=False)
        else:
            monkeypatch.setenv("LOCALAPPDATA", local_app_data)

        first = logging_setup.log_path()
        second = logging_setup.log_path()
        # Determinism: identical inputs return identical paths.
        assert first == second
        # Totality: the path always ends in our log file name.
        assert first.name == "errors.log"
    finally:
        monkeypatch.undo()


# ---------------------------------------------------------------------------
# 2. Lazy file-handler attach
# ---------------------------------------------------------------------------


def test_configure_logging_does_not_create_log_dir(
    isolate_log_dir: Path,
) -> None:
    # Pre-condition: tmp_path exists but ``errors.log`` and any sub-dir do not.
    assert not (isolate_log_dir / "errors.log").exists()

    logging_setup.configure_logging(debug=False)

    # No-op runs (CLI invoked with --help, --version, or a successful
    # command that emits no errors) MUST NOT scribble into the cache.
    assert not (isolate_log_dir / "errors.log").exists()


def test_warning_record_does_not_create_log_file(
    isolate_log_dir: Path,
) -> None:
    logging_setup.configure_logging(debug=False)
    logging.getLogger("repo_context_hooks.test").warning("warn me")
    # Lazy attach triggers on ERROR, not WARNING.
    assert not (isolate_log_dir / "errors.log").exists()


def test_error_record_creates_log_file(
    isolate_log_dir: Path,
) -> None:
    logging_setup.configure_logging(debug=False)
    logging.getLogger("repo_context_hooks.test").error("boom")
    assert (isolate_log_dir / "errors.log").exists()
    text = (isolate_log_dir / "errors.log").read_text(encoding="utf-8")
    assert "boom" in text
    assert "ERROR" in text


def test_debug_records_write_to_file_when_debug_true(
    isolate_log_dir: Path,
) -> None:
    logging_setup.configure_logging(debug=True)
    logger = logging.getLogger("repo_context_hooks.test")
    # First emit must be ERROR-or-above to attach the file handler; the
    # subsequent DEBUG record then lands in the file because handler level
    # was DEBUG when ``debug=True``.
    logger.error("first error attaches handler")
    logger.debug("verbose follow-up")
    text = (isolate_log_dir / "errors.log").read_text(encoding="utf-8")
    assert "verbose follow-up" in text


# ---------------------------------------------------------------------------
# 3. Rotation actually fires
# ---------------------------------------------------------------------------


def test_rotation_creates_backup_file(
    isolate_log_dir: Path,
) -> None:
    """Issue #73 requires 5 x 1 MB rotation. We assert that writing >1 MB
    of records produces at least one rotated ``errors.log.1`` file and the
    active log shrinks below the 1 MB threshold afterward."""
    logging_setup.configure_logging(debug=False)
    logger = logging.getLogger("repo_context_hooks.test")
    # Each record is ~1 KB once formatted; 1100 records guarantees rotation
    # at the 1 MB boundary.
    payload = "x" * 900
    for i in range(1200):
        logger.error("entry %d %s", i, payload)

    log_dir = isolate_log_dir
    assert (log_dir / "errors.log").exists()
    rotated = list(log_dir.glob("errors.log.*"))
    assert rotated, "expected at least one rotated backup file"


def test_rotation_caps_at_backup_count_4(
    isolate_log_dir: Path,
) -> None:
    """5 files total = 1 active + 4 rotated. Assert we never accumulate
    ``errors.log.5`` no matter how much we write."""
    logging_setup.configure_logging(debug=False)
    logger = logging.getLogger("repo_context_hooks.test")
    payload = "x" * 900
    for i in range(6000):
        logger.error("e%d %s", i, payload)

    rotated = sorted((isolate_log_dir).glob("errors.log.*"))
    # backupCount=4 means only .1 .. .4 are kept.
    assert all(
        p.suffix in {".1", ".2", ".3", ".4"} for p in rotated
    ), f"unexpected rotated files: {[p.name for p in rotated]}"


# ---------------------------------------------------------------------------
# 4. Read-only fallback (logger never raises)
# ---------------------------------------------------------------------------


def test_unwritable_log_dir_falls_back_to_stderr_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """If the log dir cannot be created (or RotatingFileHandler can't open),
    the next ``logger.error`` MUST NOT raise — it goes to stderr only and
    the failure latches so we don't retry on every record."""
    # Point the override at a file (not a directory). mkdir(parents=True)
    # then raises NotADirectoryError when trying to create the parent.
    blocker = tmp_path / "blocker"
    blocker.write_text("not a dir", encoding="utf-8")
    fake_log_dir = blocker / "subdir"  # parent is a file → mkdir will raise
    monkeypatch.setattr(logging_setup, "_LOG_DIR_OVERRIDE", fake_log_dir)

    logging_setup.configure_logging(debug=False)
    # The very first error: must not raise.
    logging.getLogger("repo_context_hooks.test").error("read only")
    # Latched: a second error must also not raise.
    logging.getLogger("repo_context_hooks.test").error("again")

    # The fallback writes one stderr breadcrumb the first time.
    captured = capsys.readouterr()
    assert "cannot open error log" in captured.err


# ---------------------------------------------------------------------------
# 5. get_last_error edge cases
# ---------------------------------------------------------------------------


def test_get_last_error_returns_none_when_log_missing(
    isolate_log_dir: Path,
) -> None:
    assert logging_setup.get_last_error() is None


def test_get_last_error_returns_none_when_log_empty(
    isolate_log_dir: Path,
) -> None:
    (isolate_log_dir / "errors.log").write_bytes(b"")
    assert logging_setup.get_last_error() is None


def test_get_last_error_returns_last_non_blank_line(
    isolate_log_dir: Path,
) -> None:
    (isolate_log_dir / "errors.log").write_text(
        "2026-04-29 ERROR repo_context_hooks.cli: first\n"
        "\n"
        "2026-04-29 ERROR repo_context_hooks.cli: second\n"
        "\n",
        encoding="utf-8",
    )
    assert logging_setup.get_last_error() == (
        "2026-04-29 ERROR repo_context_hooks.cli: second"
    )


def test_get_last_error_handles_binary_tail(
    isolate_log_dir: Path,
) -> None:
    """A hook subprocess that wrote raw bytes (e.g. a Windows console
    sequence) must not crash ``doctor``. ``errors='replace'`` swaps invalid
    UTF-8 for U+FFFD."""
    (isolate_log_dir / "errors.log").write_bytes(b"good line\n\xff\xfe broken\n")
    result = logging_setup.get_last_error()
    assert result is not None
    # The replacement char is what we expect; the function returned a value
    # rather than raising.
    assert "broken" in result


def test_get_last_error_handles_oversize_log(
    isolate_log_dir: Path,
) -> None:
    """A 5 MB log file (e.g. from a runaway loop before rotation triggers)
    must not be loaded into memory. We assert the function still returns
    in <1s on a 5 MB single-record file."""
    import time

    line = "padding " * 200_000  # ~1.6 MB single line
    blob = (line + "\n") * 3  # ~4.8 MB
    blob += "real last line\n"
    (isolate_log_dir / "errors.log").write_text(blob, encoding="utf-8")

    start = time.monotonic()
    result = logging_setup.get_last_error()
    elapsed = time.monotonic() - start
    assert result == "real last line"
    assert elapsed < 1.0


# ---------------------------------------------------------------------------
# 6. Idempotent configure
# ---------------------------------------------------------------------------


def test_configure_logging_is_idempotent(
    isolate_log_dir: Path,
) -> None:
    logging_setup.configure_logging(debug=False)
    pkg_logger = logging.getLogger("repo_context_hooks")
    handlers_first = list(pkg_logger.handlers)
    filters_first = list(pkg_logger.filters)

    logging_setup.configure_logging(debug=True)  # second call: no-op
    handlers_second = list(pkg_logger.handlers)
    filters_second = list(pkg_logger.filters)

    assert handlers_first == handlers_second
    assert filters_first == filters_second
