"""Tests that bundle/scripts/repo_specs_memory.py wires session duration tracking."""
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock


def _load_dev_script_record_telemetry():
    """Return the record_telemetry function from bundle/scripts/repo_specs_memory.py."""
    script = (
        Path(__file__).parent.parent
        / "repo_context_hooks"
        / "bundle"
        / "scripts"
        / "repo_specs_memory.py"
    )
    spec = importlib.util.spec_from_file_location("rsmdev", script)
    mod = importlib.util.module_from_spec(spec)
    # The script reads a module-level EVENT variable — patch it before exec
    return mod, spec


def test_dev_script_calls_record_session_start_time(tmp_path, monkeypatch):
    """record_telemetry must call record_session_start_time when EVENT='session-start'."""
    monkeypatch.setenv("EVENT", "session-start")
    called = []

    mock_telemetry = MagicMock()
    mock_telemetry.record_session_start_time.side_effect = lambda r: called.append(r)
    mock_telemetry.record_event.return_value = tmp_path / "events.jsonl"

    mod, spec = _load_dev_script_record_telemetry()
    sys.modules["repo_context_hooks.telemetry"] = mock_telemetry
    try:
        spec.loader.exec_module(mod)
        mod.record_telemetry(tmp_path, tmp_path / "specs/README.md", tmp_path / "UL.md")
    finally:
        del sys.modules["repo_context_hooks.telemetry"]

    assert len(called) == 1, "record_session_start_time must be called once on session-start"


def test_dev_script_passes_duration_on_session_end(tmp_path, monkeypatch):
    """record_telemetry must pass duration_minutes to record_event when EVENT='session-end'."""
    monkeypatch.setenv("EVENT", "session-end")
    captured_kwargs = []

    mock_telemetry = MagicMock()
    mock_telemetry.read_session_duration_minutes.return_value = 42
    mock_telemetry.record_event.side_effect = lambda *a, **kw: captured_kwargs.append(kw) or (tmp_path / "events.jsonl")

    mod, spec = _load_dev_script_record_telemetry()
    sys.modules["repo_context_hooks.telemetry"] = mock_telemetry
    try:
        spec.loader.exec_module(mod)
        mod.record_telemetry(tmp_path, tmp_path / "specs/README.md", tmp_path / "UL.md")
    finally:
        del sys.modules["repo_context_hooks.telemetry"]

    assert any(kw.get("duration_minutes") == 42 for kw in captured_kwargs), (
        f"record_event must receive duration_minutes=42, got: {captured_kwargs}"
    )


def test_dev_script_no_duration_on_session_start(tmp_path, monkeypatch):
    """record_event must NOT receive duration_minutes on session-start."""
    monkeypatch.setenv("EVENT", "session-start")
    captured_kwargs = []

    mock_telemetry = MagicMock()
    mock_telemetry.record_event.side_effect = lambda *a, **kw: captured_kwargs.append(kw) or (tmp_path / "events.jsonl")
    mock_telemetry.record_session_start_time.return_value = None

    mod, spec = _load_dev_script_record_telemetry()
    sys.modules["repo_context_hooks.telemetry"] = mock_telemetry
    try:
        spec.loader.exec_module(mod)
        mod.record_telemetry(tmp_path, tmp_path / "specs/README.md", tmp_path / "UL.md")
    finally:
        del sys.modules["repo_context_hooks.telemetry"]

    for kw in captured_kwargs:
        assert kw.get("duration_minutes") is None, "duration_minutes must be None on session-start"
