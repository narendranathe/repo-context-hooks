"""Tests for ``repo_context_hooks.verify`` (issue #74).

Mirrors the failure-mode coverage demanded by the consensus spec:

- Happy path: synthetic event round-trips through events.jsonl, schema valid.
- Cold start: settings.json missing, verify still proves plumbing.
- Isolation: synthetic event NEVER lands under ``Path.home()``.
- Schema drift: missing canonical key surfaces in ``schema_missing_keys``.
- Settings hash: canonical (sort_keys=True), so whitespace edits are no-ops.
- 2-second SLA: assertion at the end of the happy-path test.
- ``--json`` output via the CLI dispatch (covered in ``test_cli.py``).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterator

import pytest

from repo_context_hooks import verify as verify_mod
from repo_context_hooks.telemetry import CANONICAL_EVENT_KEYS


@pytest.fixture(autouse=True)
def _isolate_logging(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Redirect the M5 logging cache so verify's get_last_error tail is isolated."""
    from repo_context_hooks import logging_setup as ls

    monkeypatch.setattr(ls, "_LOG_DIR_OVERRIDE", tmp_path / "logs")
    ls.reset_for_tests()
    yield
    ls.reset_for_tests()


def test_run_verify_round_trips_synthetic_event(tmp_path: Path) -> None:
    report = verify_mod.run_verify(
        platform="claude",
        home=tmp_path / "fake-home",
        telemetry_base_override=tmp_path / "telemetry",
    )
    assert report.event_round_tripped is True
    assert report.schema_ok is True, f"missing: {report.schema_missing_keys}"
    assert report.last_event_timestamp is not None
    assert report.ok is True
    assert report.status == "healthy"


def test_run_verify_includes_all_canonical_keys_in_schema_check(tmp_path: Path) -> None:
    report = verify_mod.run_verify(
        platform="claude",
        home=tmp_path / "fake-home",
        telemetry_base_override=tmp_path / "telemetry",
    )
    # When schema is OK, no keys can be missing — symmetry check on the
    # CANONICAL_EVENT_KEYS contract from telemetry.py.
    assert report.schema_missing_keys == ()
    # And the canonical key tuple matches the telemetry module's.
    assert set(CANONICAL_EVENT_KEYS).issubset({
        "timestamp", "event_name", "session_id", "source",
        "repo_id", "repo_name", "branch",
        "repo_contract_score", "estimated_baseline_score", "details",
    })


def test_run_verify_cold_start_settings_missing_still_proves_plumbing(
    tmp_path: Path,
) -> None:
    """Verify proves the plumbing even when no install has happened yet."""
    fake_home = tmp_path / "never-installed-home"
    report = verify_mod.run_verify(
        platform="claude",
        home=fake_home,
        telemetry_base_override=tmp_path / "telemetry",
    )
    assert report.settings_exists is False
    assert report.settings_sha256 is None
    assert report.event_round_tripped is True
    # OK because plumbing works; install state is a separate question.
    assert report.ok is True


def test_run_verify_canonical_settings_hash_ignores_whitespace(tmp_path: Path) -> None:
    """SHA-256 over canonical JSON, not raw bytes — whitespace is a no-op."""
    home_a = tmp_path / "home-a"
    home_b = tmp_path / "home-b"
    settings_a = home_a / ".claude" / "settings.json"
    settings_b = home_b / ".claude" / "settings.json"
    settings_a.parent.mkdir(parents=True)
    settings_b.parent.mkdir(parents=True)
    payload = {"hooks": {}, "permissions": {"allow": ["Read"]}}
    # Same semantic content, different formatting.
    settings_a.write_text(json.dumps(payload, indent=2))
    settings_b.write_text(json.dumps(payload, separators=(",", ":")))

    rep_a = verify_mod.run_verify(
        platform="claude",
        home=home_a,
        telemetry_base_override=tmp_path / "tel-a",
    )
    rep_b = verify_mod.run_verify(
        platform="claude",
        home=home_b,
        telemetry_base_override=tmp_path / "tel-b",
    )
    assert rep_a.settings_sha256 == rep_b.settings_sha256


def test_run_verify_telemetry_base_isolated_from_real_telemetry(
    tmp_path: Path,
) -> None:
    """The synthetic event MUST NOT land under the real telemetry directory.

    Critic C non-budge: the highest-blast-radius failure mode is corrupting
    real user telemetry. The check uses ``_default_telemetry_base()`` (which
    resolves XDG/LOCALAPPDATA), not ``Path.home()`` — on Windows the OS
    tmpdir lives under home (``%LOCALAPPDATA%\\Temp``) and would false-
    positive a home-rooted check.
    """
    from repo_context_hooks import telemetry

    real_telemetry = telemetry._default_telemetry_base()
    override = tmp_path / "verify-isolated"
    report = verify_mod.run_verify(
        platform="claude",
        home=tmp_path / "fake-home",
        telemetry_base_override=override,
    )
    assert override.exists()
    assert not verify_mod._is_subpath(override, real_telemetry), (
        f"{override} is under {real_telemetry} — verify polluted real telemetry"
    )
    # And the report came back healthy from the isolated directory.
    assert report.ok is True


def test_run_verify_refuses_to_use_real_telemetry_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If override resolves to the real telemetry dir, verify must refuse."""
    from repo_context_hooks import telemetry

    # Pretend the real telemetry dir is under tmp_path.
    fake_real = tmp_path / "real-telemetry"
    fake_real.mkdir()

    def _fake_default_telemetry_base() -> Path:
        return fake_real

    monkeypatch.setattr(telemetry, "_default_telemetry_base", _fake_default_telemetry_base)

    # And tell verify to use that exact path.
    report = verify_mod.run_verify(
        platform="claude",
        home=tmp_path / "fake-home",
        telemetry_base_override=fake_real,
    )
    assert report.ok is False
    assert report.event_round_tripped is False
    assert "refused" in (report.failure_reason or "").lower() or \
           "real telemetry" in (report.failure_reason or "").lower()


def test_run_verify_meets_two_second_sla(tmp_path: Path) -> None:
    """Acceptance criterion: verify completes in <2s on a healthy install."""
    start = time.perf_counter()
    report = verify_mod.run_verify(
        platform="claude",
        home=tmp_path / "fake-home",
        telemetry_base_override=tmp_path / "telemetry",
    )
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0, f"verify took {elapsed:.2f}s, SLA is <2s"
    assert report.elapsed_ms < 2000, f"reported elapsed {report.elapsed_ms}ms exceeds 2000ms SLA"


def test_verify_report_render_includes_required_fields(tmp_path: Path) -> None:
    report = verify_mod.run_verify(
        platform="claude",
        home=tmp_path / "fake-home",
        telemetry_base_override=tmp_path / "telemetry",
    )
    rendered = report.render()
    assert "Platform: claude" in rendered
    assert "Agent home:" in rendered
    assert "Settings path:" in rendered
    assert "Status:" in rendered


def test_verify_report_to_dict_contains_status_field(tmp_path: Path) -> None:
    report = verify_mod.run_verify(
        platform="claude",
        home=tmp_path / "fake-home",
        telemetry_base_override=tmp_path / "telemetry",
    )
    d = report.to_dict()
    assert d["status"] in ("healthy", "broken")
    assert "ok" in d
    assert isinstance(d["schema_missing_keys"], list)


def test_run_verify_uses_module_level_override_when_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``_EVENTS_DIR_OVERRIDE`` is the test seam for module-wide redirection."""
    override = tmp_path / "module-level-override"
    monkeypatch.setattr(verify_mod, "_EVENTS_DIR_OVERRIDE", override)
    report = verify_mod.run_verify(
        platform="claude",
        home=tmp_path / "fake-home",
        # No explicit override — must fall back to module-level seam.
    )
    assert override.exists()
    assert report.event_round_tripped is True


def test_verify_uses_posix_paths_in_receipt(tmp_path: Path) -> None:
    """Receipt always emits posix slashes for shell-pipeline portability."""
    report = verify_mod.run_verify(
        platform="claude",
        home=tmp_path / "fake-home",
        telemetry_base_override=tmp_path / "telemetry",
    )
    # ``Path.as_posix()`` always returns forward slashes regardless of OS.
    assert "\\" not in report.agent_home
    assert "\\" not in report.settings_path


def test_canonical_settings_sha256_is_stable() -> None:
    """Hash function is deterministic across calls."""
    payload = {"hooks": {"SessionStart": [{"matcher": ""}]}}
    h1 = verify_mod._canonical_settings_sha256(payload)
    h2 = verify_mod._canonical_settings_sha256(payload)
    assert h1 == h2
    assert len(h1) == 64  # sha256 hex


def test_canonical_settings_sha256_ignores_key_order() -> None:
    """sort_keys=True means dict insertion order doesn't change the hash."""
    a = {"hooks": {}, "permissions": {"allow": ["Read"]}}
    b = {"permissions": {"allow": ["Read"]}, "hooks": {}}
    assert verify_mod._canonical_settings_sha256(a) == verify_mod._canonical_settings_sha256(b)


# ---------------------------------------------------------------------------
# Coverage backfill for verify.py error paths (Codecov patch-coverage gate).
# Each test below targets a specific except/branch that the happy-path tests
# above did not exercise.
# ---------------------------------------------------------------------------


def test_read_settings_for_hash_returns_false_when_missing(tmp_path: Path) -> None:
    """Non-existent path returns ``(False, None)`` cleanly."""
    exists, sha = verify_mod._read_settings_for_hash(tmp_path / "absent.json")
    assert exists is False
    assert sha is None


def test_read_settings_for_hash_handles_corrupt_json(tmp_path: Path) -> None:
    """Malformed JSON returns ``(True, hash-of-empty-dict)`` rather than raising."""
    p = tmp_path / "settings.json"
    p.write_text("{not valid json <<<<<", encoding="utf-8")
    exists, sha = verify_mod._read_settings_for_hash(p)
    assert exists is True
    assert sha == verify_mod._canonical_settings_sha256({})


def test_read_settings_for_hash_handles_non_dict_json(tmp_path: Path) -> None:
    """Top-level array (or scalar) coerces to empty dict for hashing."""
    p = tmp_path / "settings.json"
    p.write_text('["not", "a", "dict"]', encoding="utf-8")
    exists, sha = verify_mod._read_settings_for_hash(p)
    assert exists is True
    assert sha == verify_mod._canonical_settings_sha256({})


def test_read_settings_for_hash_handles_empty_file(tmp_path: Path) -> None:
    """Zero-byte settings.json hashes to the empty-dict canonical form."""
    p = tmp_path / "settings.json"
    p.write_text("", encoding="utf-8")
    exists, sha = verify_mod._read_settings_for_hash(p)
    assert exists is True
    assert sha == verify_mod._canonical_settings_sha256({})


def test_init_synthetic_repo_survives_git_not_installed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If ``git`` binary is missing (Nix sandbox / distroless), falls through
    cleanly — the synthetic event still gets written downstream."""
    import subprocess as _sp

    def _raise_filenotfound(*_a, **_kw):
        raise FileNotFoundError("git not on PATH")

    monkeypatch.setattr("repo_context_hooks.verify.subprocess.run", _raise_filenotfound)
    repo = verify_mod._init_synthetic_repo(tmp_path)
    assert repo == tmp_path / "repo"
    assert repo.exists()


def test_platform_tier_returns_unknown_for_unregistered_platform() -> None:
    """``_platform_tier`` swallows ``KeyError`` and returns ``"unknown"``."""
    assert verify_mod._platform_tier("not-a-real-platform") == "unknown"


def test_platform_tier_returns_native_for_claude() -> None:
    assert verify_mod._platform_tier("claude") == "native"


def test_render_includes_failure_line_when_set() -> None:
    """When ``failure_reason`` is populated the render emits a `Failure:` line."""
    report = verify_mod.VerifyReport(
        platform="claude",
        agent_home="/home/x/.claude",
        settings_path="/home/x/.claude/settings.json",
        settings_exists=True,
        settings_sha256="abc",
        event_round_tripped=False,
        last_event_timestamp=None,
        schema_ok=False,
        schema_missing_keys=(),
        elapsed_ms=10,
        last_error=None,
        failure_reason="agent home read-only — cannot run verify",
    )
    rendered = report.render()
    assert "Failure: agent home read-only" in rendered
    assert "Status: BROKEN" in rendered


def test_render_omits_settings_sha_line_when_none() -> None:
    """``settings_sha256=None`` (cold start) suppresses the sha line."""
    report = verify_mod.VerifyReport(
        platform="claude",
        agent_home="/home/x/.claude",
        settings_path="/home/x/.claude/settings.json",
        settings_exists=False,
        settings_sha256=None,
        event_round_tripped=True,
        last_event_timestamp="2026-04-30T12:00:00Z",
        schema_ok=True,
        schema_missing_keys=(),
        elapsed_ms=42,
        last_error=None,
    )
    rendered = report.render()
    assert "Settings sha256" not in rendered
    assert "Settings exists: no" in rendered


def test_render_includes_schema_missing_keys_list_when_drifted() -> None:
    """When schema_ok=False, the missing keys are enumerated in the receipt."""
    report = verify_mod.VerifyReport(
        platform="claude",
        agent_home="/home/x/.claude",
        settings_path="/home/x/.claude/settings.json",
        settings_exists=True,
        settings_sha256="abc",
        event_round_tripped=True,
        last_event_timestamp="2026-04-30T12:00:00Z",
        schema_ok=False,
        schema_missing_keys=("event_name", "session_id"),
        elapsed_ms=10,
        last_error=None,
    )
    rendered = report.render()
    assert "Schema valid: NO" in rendered
    assert "event_name" in rendered
    assert "session_id" in rendered


def test_run_verify_surfaces_permission_error_as_failure_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A ``PermissionError`` during synthetic-event write is surfaced as a
    receipt failure_reason rather than propagated as an exception."""

    def _raise_perm(*_a, **_kw):
        raise PermissionError("read-only filesystem")

    monkeypatch.setattr(verify_mod, "_synthesize_session_start", _raise_perm)
    report = verify_mod.run_verify(
        platform="claude",
        home=tmp_path / "fake-home",
        telemetry_base_override=tmp_path / "ev",
    )
    assert report.ok is False
    assert "agent home read-only" in (report.failure_reason or "").lower()


def test_run_verify_surfaces_oserror_as_failure_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A generic ``OSError`` is captured in ``failure_reason``."""

    def _raise_os(*_a, **_kw):
        raise OSError("disk quota exceeded")

    monkeypatch.setattr(verify_mod, "_synthesize_session_start", _raise_os)
    report = verify_mod.run_verify(
        platform="claude",
        home=tmp_path / "fake-home",
        telemetry_base_override=tmp_path / "ev",
    )
    assert report.ok is False
    assert "filesystem error" in (report.failure_reason or "").lower()


def test_run_verify_handles_no_events_round_tripped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the read-back returns no matching synthetic events, surface that
    explicitly as the failure reason."""
    # Patch _read_events to return an empty list — simulates a write that
    # vanished (e.g. an antivirus quarantine on Windows).
    monkeypatch.setattr(
        "repo_context_hooks.telemetry._read_events",
        lambda _path: [],
    )
    report = verify_mod.run_verify(
        platform="claude",
        home=tmp_path / "fake-home",
        telemetry_base_override=tmp_path / "ev",
    )
    assert report.ok is False
    assert report.event_round_tripped is False
    assert "did not appear" in (report.failure_reason or "")


def test_is_subpath_handles_value_error() -> None:
    """``relative_to`` raises ``ValueError`` for non-related paths → returns False."""
    assert verify_mod._is_subpath(Path("/tmp/a"), Path("/var/b")) is False


def test_is_subpath_returns_true_for_self() -> None:
    """A path is its own subpath."""
    p = Path("/tmp/somewhere")
    assert verify_mod._is_subpath(p, p) is True


def test_is_subpath_returns_true_for_descendant() -> None:
    parent = Path("/tmp/parent")
    child = Path("/tmp/parent/child/leaf")
    assert verify_mod._is_subpath(child, parent) is True


class TestVerifyPortability:
    """Portability-axis regressions: Path.home() crash, old-git fallback."""

    def test_run_verify_survives_path_home_runtimeerror(
        self, monkeypatch, tmp_path
    ):
        """SYSTEM-account Windows / Lambda / Nix-sandbox: ``Path.home()``
        raises ``RuntimeError``. Verify must NOT propagate it — the receipt
        is the contract. Regression for the M5/PR #103 bug repeating in
        verify.py.
        """
        from repo_context_hooks import verify

        def boom():
            raise RuntimeError("Could not determine home directory")

        monkeypatch.setattr("pathlib.Path.home", staticmethod(boom))
        # No `home=` kwarg — exercises the fallback path through
        # _logging_setup._safe_home().
        report = verify.run_verify(
            "claude",
            telemetry_base_override=tmp_path / "ev",
        )
        # Either succeeded via tempdir fallback, or returned a receipt
        # with a failure_reason — but did NOT raise.
        assert isinstance(report, verify.VerifyReport)

    def test_init_synthetic_repo_falls_back_on_old_git(
        self, monkeypatch, tmp_path
    ):
        """RHEL 7/8 ship git 2.20/2.27 — ``--initial-branch`` exits non-zero.
        Verify falls back to plain ``git init`` so the synthetic repo still
        gets created.
        """
        import subprocess
        from repo_context_hooks import verify

        calls = []
        real_run = subprocess.run

        def fake_run(argv, **kw):
            calls.append(argv)
            if "--initial-branch=verify" in argv:
                return subprocess.CompletedProcess(argv, 129, b"", b"unknown option")
            return real_run(argv, **kw)

        monkeypatch.setattr("repo_context_hooks.verify.subprocess.run", fake_run)
        verify._init_synthetic_repo(tmp_path)
        assert len(calls) == 2  # tried modern, fell back to plain
        assert "--initial-branch=verify" not in calls[1]
