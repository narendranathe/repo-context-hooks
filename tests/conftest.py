"""Shared pytest fixtures for repo-context-hooks.

Kept intentionally tiny so the existing 330-test suite is not perturbed.
The autouse fixture below only clears `REPO_CONTEXT_HOOKS_*` env vars
so a local dev environment cannot leak a sampling/consent decision into
the test run.
"""
from __future__ import annotations

import pytest

_ENV_VARS_TO_CLEAR = (
    "REPO_CONTEXT_HOOKS_TELEMETRY",
    "REPO_CONTEXT_HOOKS_SAMPLE_RATE",
    "REPO_CONTEXT_HOOKS_SESSION_ID",
)


@pytest.fixture(autouse=True)
def _isolate_repo_context_hooks_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in _ENV_VARS_TO_CLEAR:
        monkeypatch.delenv(var, raising=False)
