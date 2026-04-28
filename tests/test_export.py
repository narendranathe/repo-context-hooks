"""Tests for export_impact_report() and the 'measure export' CLI subcommand."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

from repo_context_hooks.telemetry import _make_test_report, export_impact_report

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tmp_dir() -> Path:
    base = ROOT / ".tmp-tests"
    base.mkdir(exist_ok=True)
    path = base / uuid4().hex
    path.mkdir()
    return path


def _report_with_events():
    """Return a test report that has non-empty event_counts and history."""
    from repo_context_hooks.repo_contract import init_repo_contract
    from repo_context_hooks.telemetry import measure_impact, record_event

    tmp = _tmp_dir()
    repo = tmp / "myproject"
    repo.mkdir()
    init_repo_contract(repo)
    tbase = tmp / "telem"
    record_event(repo, "session-start", telemetry_base=tbase)
    record_event(repo, "post-compact", telemetry_base=tbase)
    return measure_impact(repo, telemetry_base=tbase)


# ---------------------------------------------------------------------------
# JSON format tests
# ---------------------------------------------------------------------------


def test_export_json_is_valid_json():
    report = _make_test_report()
    output = export_impact_report(report, format="json")
    parsed = json.loads(output)  # must not raise
    assert isinstance(parsed, dict)


def test_export_json_has_required_keys():
    report = _make_test_report(current_score=90)
    parsed = json.loads(export_impact_report(report, format="json"))
    assert "repo" in parsed
    assert "score" in parsed
    assert "uplift" in parsed
    assert "disclaimer" in parsed
    assert "generated_at" in parsed
    assert "baseline" in parsed
    assert "observed_events" in parsed


def test_export_json_values_are_correct():
    report = _make_test_report(current_score=90)
    parsed = json.loads(export_impact_report(report, format="json"))
    assert parsed["repo"] == "test-repo"
    assert parsed["score"] == 90
    assert parsed["baseline"] == 20
    assert parsed["uplift"] == 70


def test_export_json_has_no_local_filesystem_paths():
    """The JSON output must not contain the telemetry_path or dashboard_path."""
    report = _make_test_report()
    output = export_impact_report(report, format="json")
    # Verify local paths are absent - check for path separators typical of absolute paths
    assert str(report.telemetry_path) not in output
    assert str(report.dashboard_path) not in output
    # No Windows-style absolute path fragments (e.g. "C:\\", "C:/")
    assert "C:\\" not in output
    assert "C:/" not in output
    assert "/tmp/test-telemetry" not in output
    assert "/tmp/test-dashboard" not in output


def test_export_json_no_repo_id():
    """repo_id (the hash) should not appear in the JSON output."""
    report = _make_test_report()
    parsed = json.loads(export_impact_report(report, format="json"))
    assert "repo_id" not in parsed


def test_export_json_usability_metrics_present():
    report = _make_test_report(current_score=80, reload_events=3, resume_events=7)
    parsed = json.loads(export_impact_report(report, format="json"))
    assert parsed["resume_events"] == 7
    assert parsed["reload_events"] == 3
    assert parsed["cold_start_time_saved_minutes"] == 15  # 3 * 5
    assert parsed["active_days"] == 1
    assert parsed["lifecycle_coverage_pct"] == 25


def test_export_json_date_only_timestamps():
    """first_seen and latest_seen must be dates (10 chars), not full ISO strings."""
    report = _make_test_report()
    parsed = json.loads(export_impact_report(report, format="json"))
    first = parsed.get("first_seen")
    latest = parsed.get("latest_seen")
    if first is not None:
        assert len(first) == 10, f"Expected date-only, got: {first!r}"
    if latest is not None:
        assert len(latest) == 10, f"Expected date-only, got: {latest!r}"


def test_export_json_with_real_events_no_paths():
    """Integration: export from a real measure_impact call must have no local paths."""
    report = _report_with_events()
    output = export_impact_report(report, format="json")
    parsed = json.loads(output)
    # No absolute path strings in keys or values
    serialised = json.dumps(parsed)
    assert str(report.telemetry_path) not in serialised
    assert str(report.dashboard_path) not in serialised


# ---------------------------------------------------------------------------
# Markdown format tests
# ---------------------------------------------------------------------------


def test_export_markdown_has_h2_heading():
    report = _make_test_report()
    output = export_impact_report(report, format="markdown")
    assert output.startswith("## ")


def test_export_markdown_has_table():
    report = _make_test_report()
    output = export_impact_report(report, format="markdown")
    assert "| Metric | Value |" in output
    assert "|---|---|" in output


def test_export_markdown_shows_score_and_uplift():
    report = _make_test_report(current_score=85)
    output = export_impact_report(report, format="markdown")
    assert "85" in output
    assert "+65" in output  # uplift = 85 - 20


def test_export_markdown_has_disclaimer():
    report = _make_test_report()
    output = export_impact_report(report, format="markdown")
    assert "local operational telemetry" in output
    assert "no source code" in output


def test_export_markdown_has_no_local_filesystem_paths():
    report = _make_test_report()
    output = export_impact_report(report, format="markdown")
    assert str(report.telemetry_path) not in output
    assert str(report.dashboard_path) not in output
    assert "/tmp/test-telemetry" not in output
    assert "/tmp/test-dashboard" not in output


def test_export_markdown_includes_event_breakdown_when_nonempty():
    report = _report_with_events()
    output = export_impact_report(report, format="markdown")
    assert "Event breakdown" in output
    assert "session-start" in output


def test_export_markdown_no_event_breakdown_when_empty():
    report = _make_test_report()  # event_counts={}
    output = export_impact_report(report, format="markdown")
    assert "Event breakdown" not in output


# ---------------------------------------------------------------------------
# Redact flag behaviour
# ---------------------------------------------------------------------------


def test_export_redact_default_is_true():
    """Calling export without redact= should still produce clean output."""
    report = _make_test_report()
    output = export_impact_report(report)
    assert str(report.telemetry_path) not in output


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------


def _run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "repo_context_hooks", *args],
        capture_output=True,
        text=True,
        cwd=str(cwd or ROOT),
    )


def test_cli_measure_export_markdown_exits_zero():
    result = _run_cli("measure", "export", "--format", "markdown")
    assert result.returncode == 0, result.stderr


def test_cli_measure_export_json_exits_zero():
    result = _run_cli("measure", "export", "--format", "json")
    assert result.returncode == 0, result.stderr


def test_cli_measure_export_json_is_valid_json():
    result = _run_cli("measure", "export", "--format", "json")
    assert result.returncode == 0
    parsed = json.loads(result.stdout)
    assert "score" in parsed
    assert "uplift" in parsed
    assert "disclaimer" in parsed


def test_cli_measure_export_markdown_has_heading():
    result = _run_cli("measure", "export", "--format", "markdown")
    assert result.returncode == 0
    assert "## " in result.stdout


def test_cli_measure_export_to_file(tmp_path):
    out_file = tmp_path / "report.md"
    result = _run_cli("measure", "export", "--format", "markdown", "--output", str(out_file))
    assert result.returncode == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "## " in content
    assert "Export written to:" in result.stdout


def test_cli_measure_export_json_no_local_paths():
    """The CLI JSON export must contain no local user path fragments."""
    result = _run_cli("measure", "export", "--format", "json")
    assert result.returncode == 0
    # Should not contain typical absolute path markers
    assert "C:\\" not in result.stdout
    assert "\\Users\\" not in result.stdout
    assert "/home/" not in result.stdout


def test_cli_measure_existing_flags_still_work():
    """Ensure existing measure flags are not broken by the new subcommand."""
    result = _run_cli("measure", "--json")
    assert result.returncode == 0
    parsed = json.loads(result.stdout)
    assert "current_score" in parsed
