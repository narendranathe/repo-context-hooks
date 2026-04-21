from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_lifecycle_diagram_mentions_real_interrupted_workflow() -> None:
    text = (ROOT / "assets" / "diagrams" / "lifecycle-flow.svg").read_text(encoding="utf-8").lower()

    expected_snippets = [
        "bugfix interrupted by compact",
        "checkpoint written to specs/readme.md",
        "next session resumes from repo state",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing lifecycle story detail: {snippet}"


def test_repo_contract_diagram_mentions_handoff_story() -> None:
    text = (ROOT / "assets" / "diagrams" / "repo-contract.svg").read_text(encoding="utf-8").lower()

    expected_snippets = [
        "open pr story stays in readme.md",
        "handoff notes land in specs/readme.md",
        "agents.md guides the re-entry",
        "cursor or codex can re-enter with repo context",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing repo contract story detail: {snippet}"


def test_before_after_diagram_mentions_repeated_work_and_clean_handoff() -> None:
    text = (ROOT / "assets" / "diagrams" / "before-after-continuity.svg").read_text(encoding="utf-8").lower()

    expected_snippets = [
        "same bug explained again",
        "re-read the repo and resume review comments",
        "resume from checked-in continuity",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing before/after story detail: {snippet}"


def test_platform_roadmap_doc_links_planned_platforms() -> None:
    text = (ROOT / "docs" / "launch" / "platform-roadmap.md").read_text(encoding="utf-8")

    expected_snippets = [
        "# Planned Platform Roadmap",
        "Replit",
        "Lovable",
        "Ollama",
        "OpenClaw",
        "Kimi",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing roadmap snippet: {snippet}"
    assert "Likely tier:" not in text


def test_animation_plan_stays_static_first_but_story_driven() -> None:
    text = (ROOT / "docs" / "demo" / "animation-plan.md").read_text(encoding="utf-8").lower()

    expected_snippets = [
        "static svg remains the source of truth",
        "interrupted task",
        "handoff story",
        "do not imply automation the tool does not provide",
    ]
    for snippet in expected_snippets:
        assert snippet in text, f"missing animation plan guidance: {snippet}"
