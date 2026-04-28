"""Tests for repo_context_hooks.consent module."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

import repo_context_hooks.consent as consent_mod


@pytest.fixture(autouse=True)
def _redirect_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect consent config to a temp path for every test."""
    override_path = tmp_path / "consent.json"
    monkeypatch.setattr(consent_mod, "_CONFIG_PATH_OVERRIDE", override_path)


# ---------------------------------------------------------------------------
# consent_config_path()
# ---------------------------------------------------------------------------

def test_consent_config_path_returns_path_under_platform_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without the override, path should end with consent.json inside a known dir."""
    monkeypatch.setattr(consent_mod, "_CONFIG_PATH_OVERRIDE", None)

    path = consent_mod.consent_config_path()
    assert path.name == "consent.json"
    assert "repo-context-hooks" in str(path)
    # Must not be a raw home dir root - should be inside a config subdir
    assert path != Path.home() / "consent.json"


def test_consent_config_path_respects_override(tmp_path: Path) -> None:
    """The _CONFIG_PATH_OVERRIDE fixture should redirect correctly."""
    path = consent_mod.consent_config_path()
    assert path == tmp_path / "consent.json"


# ---------------------------------------------------------------------------
# get_consent_state()
# ---------------------------------------------------------------------------

def test_get_consent_state_returns_not_set_when_no_config(tmp_path: Path) -> None:
    state = consent_mod.get_consent_state()
    assert state["status"] == "not_set"
    assert state["enabled_at"] is None
    assert state["install_id"] is None
    assert "consent.json" in state["config_path"]


def test_get_consent_state_reflects_enabled(tmp_path: Path) -> None:
    consent_mod.enable_consent()
    state = consent_mod.get_consent_state()
    assert state["status"] == "enabled"
    assert state["install_id"] is not None
    assert state["enabled_at"] is not None


def test_get_consent_state_reflects_disabled(tmp_path: Path) -> None:
    consent_mod.enable_consent()
    consent_mod.disable_consent()
    state = consent_mod.get_consent_state()
    assert state["status"] == "disabled"


# ---------------------------------------------------------------------------
# enable_consent()
# ---------------------------------------------------------------------------

def test_enable_consent_writes_config_and_returns_enabled_state(tmp_path: Path) -> None:
    state = consent_mod.enable_consent()
    assert state["status"] == "enabled"
    assert state["install_id"] is not None
    # install_id should be a valid UUID
    uuid.UUID(state["install_id"])  # raises if invalid


def test_enable_consent_creates_config_file(tmp_path: Path) -> None:
    consent_mod.enable_consent()
    config_path = consent_mod.consent_config_path()
    assert config_path.exists()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert data["consented"] is True
    assert "install_id" in data
    assert "enabled_at" in data


def test_enable_consent_preserves_existing_install_id(tmp_path: Path) -> None:
    state1 = consent_mod.enable_consent()
    id1 = state1["install_id"]
    consent_mod.disable_consent()
    state2 = consent_mod.enable_consent()
    assert state2["install_id"] == id1


# ---------------------------------------------------------------------------
# disable_consent()
# ---------------------------------------------------------------------------

def test_disable_consent_returns_disabled_state(tmp_path: Path) -> None:
    consent_mod.enable_consent()
    state = consent_mod.disable_consent()
    assert state["status"] == "disabled"


def test_disable_consent_creates_config_even_without_prior_enable(tmp_path: Path) -> None:
    state = consent_mod.disable_consent()
    assert state["status"] == "disabled"
    assert consent_mod.consent_config_path().exists()


def test_disable_consent_overwrites_enabled(tmp_path: Path) -> None:
    consent_mod.enable_consent()
    consent_mod.disable_consent()
    data = json.loads(consent_mod.consent_config_path().read_text(encoding="utf-8"))
    assert data["consented"] is False


# ---------------------------------------------------------------------------
# is_consented()
# ---------------------------------------------------------------------------

def test_is_consented_false_when_not_set(tmp_path: Path) -> None:
    assert consent_mod.is_consented() is False


def test_is_consented_true_when_enabled(tmp_path: Path) -> None:
    consent_mod.enable_consent()
    assert consent_mod.is_consented() is True


def test_is_consented_false_when_disabled(tmp_path: Path) -> None:
    consent_mod.enable_consent()
    consent_mod.disable_consent()
    assert consent_mod.is_consented() is False


# ---------------------------------------------------------------------------
# preview_payload()
# ---------------------------------------------------------------------------

def test_preview_payload_returns_dict_with_required_keys(tmp_path: Path) -> None:
    payload = consent_mod.preview_payload()
    required = {
        "install_id",
        "package_version",
        "platform_adapter",
        "os_family",
        "python_minor",
        "continuity_score",
        "estimated_baseline_score",
        "lifecycle_event_counts",
        "collector_endpoint",
        "disclaimer",
    }
    assert required <= payload.keys()


def test_preview_payload_contains_disclaimer(tmp_path: Path) -> None:
    payload = consent_mod.preview_payload()
    assert "No data has been sent" in payload["disclaimer"]


def test_preview_payload_no_local_paths(tmp_path: Path) -> None:
    """Payload must not contain any string that looks like an absolute local path."""
    payload = consent_mod.preview_payload()
    payload_str = json.dumps(payload)
    # Should not contain Windows drive letters or Unix-style absolute paths
    # beyond the known safe fields.
    for key in ("install_id", "package_version", "platform_adapter", "os_family",
                "python_minor", "collector_endpoint", "disclaimer"):
        val = str(payload.get(key, ""))
        # These fields should not contain path separators that imply local paths
        assert "Users" not in val, f"Field {key!r} may contain a local path: {val!r}"
        assert "home" not in val.lower() or key in ("os_family",), (
            f"Field {key!r} may contain a local path reference: {val!r}"
        )


def test_preview_payload_install_id_placeholder_when_not_consented(tmp_path: Path) -> None:
    payload = consent_mod.preview_payload()
    assert payload["install_id"] == "not-yet-generated"


def test_preview_payload_install_id_populated_after_enable(tmp_path: Path) -> None:
    consent_mod.enable_consent()
    payload = consent_mod.preview_payload()
    assert payload["install_id"] != "not-yet-generated"
    uuid.UUID(payload["install_id"])  # should be valid UUID


def test_preview_payload_collector_endpoint_not_configured(tmp_path: Path) -> None:
    payload = consent_mod.preview_payload()
    assert payload["collector_endpoint"] == "not yet configured"


def test_preview_payload_null_scores_without_repo_root(tmp_path: Path) -> None:
    payload = consent_mod.preview_payload(repo_root=None)
    assert payload["continuity_score"] is None
    assert payload["estimated_baseline_score"] is None
    assert payload["lifecycle_event_counts"] == {}


def test_preview_payload_python_minor_format(tmp_path: Path) -> None:
    import sys
    payload = consent_mod.preview_payload()
    expected = f"{sys.version_info.major}.{sys.version_info.minor}"
    assert payload["python_minor"] == expected


# ---------------------------------------------------------------------------
# CLI integration - telemetry subcommand
# ---------------------------------------------------------------------------

def test_cli_telemetry_status_parseable(tmp_path: Path) -> None:
    """build_parser() must accept 'telemetry status'."""
    from repo_context_hooks.cli import build_parser
    parser = build_parser()
    args = parser.parse_args(["telemetry", "status"])
    assert args.command == "telemetry"
    assert args.telemetry_subcommand == "status"


def test_cli_telemetry_enable_parseable(tmp_path: Path) -> None:
    from repo_context_hooks.cli import build_parser
    parser = build_parser()
    args = parser.parse_args(["telemetry", "enable", "--yes"])
    assert args.command == "telemetry"
    assert args.telemetry_subcommand == "enable"
    assert args.yes is True


def test_cli_telemetry_disable_parseable(tmp_path: Path) -> None:
    from repo_context_hooks.cli import build_parser
    parser = build_parser()
    args = parser.parse_args(["telemetry", "disable"])
    assert args.command == "telemetry"
    assert args.telemetry_subcommand == "disable"


def test_cli_telemetry_preview_parseable(tmp_path: Path) -> None:
    from repo_context_hooks.cli import build_parser
    parser = build_parser()
    args = parser.parse_args(["telemetry", "preview"])
    assert args.command == "telemetry"
    assert args.telemetry_subcommand == "preview"


def test_cli_telemetry_status_not_configured_output(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    from repo_context_hooks.cli import _telemetry_cmd
    from argparse import Namespace
    args = Namespace(command="telemetry", telemetry_subcommand="status")
    ret = _telemetry_cmd(args)
    assert ret == 0
    out = capsys.readouterr().out
    assert "not configured" in out
    assert "will be generated on first enable" in out


def test_cli_telemetry_enable_yes_flag(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    from repo_context_hooks.cli import _telemetry_cmd
    from argparse import Namespace
    args = Namespace(command="telemetry", telemetry_subcommand="enable", yes=True)
    ret = _telemetry_cmd(args)
    assert ret == 0
    out = capsys.readouterr().out
    assert "enabled" in out
    assert "No data is being sent" in out


def test_cli_telemetry_enable_noninteractive_without_yes(
    tmp_path: Path, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """In a non-interactive environment (EOF on stdin), should print graceful message."""
    from repo_context_hooks.cli import _telemetry_cmd
    from argparse import Namespace

    def _raise_eof(_prompt: str) -> str:
        raise EOFError

    # Simulate EOF on stdin
    monkeypatch.setattr("builtins.input", _raise_eof)
    args = Namespace(command="telemetry", telemetry_subcommand="enable", yes=False)
    ret = _telemetry_cmd(args)
    assert ret == 0
    out = capsys.readouterr().out
    assert "Telemetry remains disabled" in out


def test_cli_telemetry_disable_output(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    from repo_context_hooks.cli import _telemetry_cmd
    from argparse import Namespace
    args = Namespace(command="telemetry", telemetry_subcommand="disable")
    ret = _telemetry_cmd(args)
    assert ret == 0
    out = capsys.readouterr().out
    assert "disabled" in out


def test_cli_telemetry_preview_output(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    from repo_context_hooks.cli import _telemetry_cmd
    from argparse import Namespace
    args = Namespace(command="telemetry", telemetry_subcommand="preview", repo_root=None)
    ret = _telemetry_cmd(args)
    assert ret == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "disclaimer" in data
    assert "No data has been sent" in data["disclaimer"]
    assert data["collector_endpoint"] == "not yet configured"
