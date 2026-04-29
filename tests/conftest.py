"""Shared pytest fixtures for repo-context-hooks.

Three concerns live here, in this order:

1. **Hypothesis storage isolation** — pin the example database to a process-local
   tmpdir BEFORE any hypothesis import so the test suite stays green on
   read-only HOME directories (Nix sandbox, distroless containers, some
   Jenkins agents). (audit F2.4)
2. **Hypothesis profile** — register a single ``"rch"`` profile so every
   property test in the suite shares the same `derandomize`/`deadline`/
   `max_examples` values. Without this, settings drift across files within a
   week. (audit F4.4)
3. **Env-var isolation** — strip every ``REPO_CONTEXT_HOOKS_*`` env var so a
   local dev opt-out (or a CI runner that exports one for unrelated reasons)
   cannot poison telemetry / sampling tests. The previous fixed-tuple
   approach silently missed ``REPO_CONTEXT_HOOKS_TELEMETRY_DIR`` and would
   have missed every future env var added by Wave 2/3 PRs. (audit F4.1)
"""
from __future__ import annotations

import os
import tempfile

# ---------------------------------------------------------------------------
# (1) Hypothesis storage MUST be set before importing hypothesis.
# ---------------------------------------------------------------------------
os.environ.setdefault(
    "HYPOTHESIS_STORAGE_DIRECTORY",
    tempfile.mkdtemp(prefix="rch-hyp-"),
)

import pytest  # noqa: E402

from hypothesis import HealthCheck, settings as hyp_settings  # noqa: E402

# ---------------------------------------------------------------------------
# (2) Single shared Hypothesis profile.
# ---------------------------------------------------------------------------
hyp_settings.register_profile(
    "rch",
    derandomize=True,
    deadline=None,
    max_examples=50,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
hyp_settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "rch"))


# ---------------------------------------------------------------------------
# (3) Env-var isolation. Glob-clear every REPO_CONTEXT_HOOKS_* var.
# ---------------------------------------------------------------------------
_ENV_PREFIX = "REPO_CONTEXT_HOOKS_"


@pytest.fixture(autouse=True)
def _isolate_repo_context_hooks_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in [k for k in os.environ if k.startswith(_ENV_PREFIX)]:
        monkeypatch.delenv(var, raising=False)
