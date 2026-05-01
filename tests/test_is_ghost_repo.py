"""Unit tests for the `is_ghost_repo` predicate (issue #106).

The predicate is the side-effect-free classifier extracted from
`purge_ghost_repos`. Once issue #107 lands, the rollup walker will
call it to decide whether a workspace dir should be excluded from
the cross-workspace fleet rollup.
"""

from __future__ import annotations

from repo_context_hooks.telemetry import EVENTS_FILE, is_ghost_repo


def test_ghost_name_with_single_event_is_ghost(tmp_path):
    repo_dir = tmp_path / "abc123"
    repo_dir.mkdir()
    (repo_dir / EVENTS_FILE).write_text(
        '{"event_name":"session-start","repo_name":"repo"}\n',
        encoding="utf-8",
    )
    assert is_ghost_repo(repo_dir) is True


def test_normal_repo_name_with_single_event_is_not_ghost(tmp_path):
    repo_dir = tmp_path / "def456"
    repo_dir.mkdir()
    (repo_dir / EVENTS_FILE).write_text(
        '{"event_name":"session-start","repo_name":"autoapply-ai"}\n',
        encoding="utf-8",
    )
    assert is_ghost_repo(repo_dir) is False


def test_two_or_more_events_is_never_ghost_even_if_name_matches(tmp_path):
    repo_dir = tmp_path / "ghi789"
    repo_dir.mkdir()
    (repo_dir / EVENTS_FILE).write_text(
        '{"event_name":"session-start","repo_name":"repo"}\n'
        '{"event_name":"session-end","repo_name":"repo"}\n',
        encoding="utf-8",
    )
    assert is_ghost_repo(repo_dir) is False


def test_missing_events_file_falls_back_to_dir_name_ghost(tmp_path):
    repo_dir = tmp_path / "tmp"
    repo_dir.mkdir()
    assert is_ghost_repo(repo_dir) is True


def test_missing_events_file_falls_back_to_dir_name_non_ghost(tmp_path):
    repo_dir = tmp_path / "real-project-id"
    repo_dir.mkdir()
    assert is_ghost_repo(repo_dir) is False


def test_empty_events_file_falls_back_to_dir_name_ghost(tmp_path):
    repo_dir = tmp_path / "test"
    repo_dir.mkdir()
    (repo_dir / EVENTS_FILE).write_text("", encoding="utf-8")
    assert is_ghost_repo(repo_dir) is True


def test_each_ghost_name_classified(tmp_path):
    for ghost_name in ("repo", "tmp", "temp", "test"):
        repo_dir = tmp_path / f"id-{ghost_name}"
        repo_dir.mkdir()
        (repo_dir / EVENTS_FILE).write_text(
            f'{{"event_name":"session-start","repo_name":"{ghost_name}"}}\n',
            encoding="utf-8",
        )
        assert is_ghost_repo(repo_dir) is True, f"{ghost_name} must be ghost"


def test_corrupt_jsonl_line_is_tolerated(tmp_path):
    repo_dir = tmp_path / "id-corrupt"
    repo_dir.mkdir()
    (repo_dir / EVENTS_FILE).write_text(
        '{"event_name":"session-start","repo_name":"repo"}\n'
        "this is not json\n",
        encoding="utf-8",
    )
    assert is_ghost_repo(repo_dir) is True
