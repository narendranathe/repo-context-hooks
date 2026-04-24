from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "docs" / "telemetry-policy.md"
REMOTE_SPEC = (
    ROOT
    / "docs"
    / "superpowers"
    / "specs"
    / "2026-04-24-consented-community-telemetry-design.md"
)


def test_public_telemetry_policy_requires_explicit_opt_in() -> None:
    text = POLICY.read_text(encoding="utf-8")

    required = [
        "Remote telemetry is off by default",
        "explicit opt-in",
        "revoked",
        "No source code",
        "No prompts",
        "No secrets",
        "No cookies are used by the CLI",
    ]
    for snippet in required:
        assert snippet in text


def test_remote_telemetry_spec_keeps_mvp_local_first() -> None:
    text = REMOTE_SPEC.read_text(encoding="utf-8")

    assert "MVP Decision" in text
    assert "Do not implement remote upload until there is a real endpoint" in text
    assert "MCP server" in text
    assert "consent token" in text
