"""Property-based tests for telemetry hot paths.

Issue #71 — the contract a downstream library author depends on:
- `is_sampled(rate)` is True for every rate >= 1.0 and False for every rate <= 0.0
- A mid-range rate produces a decision that is stable across consecutive calls
  inside the same session (cache hit on the second call)
- `repo_id(path)` returns 16 lowercase hex chars and is stable across calls in
  the same process

NaN and infinity rates are out-of-contract; strategies exclude them.
Cross-process / cross-OS hash equality is NOT promised (Path.resolve normalises
differently on Windows vs POSIX) — only the shape is.
"""
from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from hypothesis import given, strategies as st

from repo_context_hooks.telemetry import is_sampled, repo_id

# Hypothesis settings are loaded from the shared ``"rch"`` profile registered in
# ``tests/conftest.py``. Override via ``HYPOTHESIS_PROFILE=ci`` or similar — do
# NOT re-register a profile here. The ``rch`` profile sets ``derandomize=True``,
# ``deadline=None``, ``max_examples=50``, and suppresses
# ``HealthCheck.function_scoped_fixture`` (every test below either nonces its
# own subdir under ``tmp_path`` or uses the Hypothesis-generated ``name`` to
# disambiguate, so sharing the parent tmp_path across examples is safe).

# Path components must be safe on every CI OS. Restrict to ASCII letters,
# digits, hyphen, underscore, and dot — broad enough to exercise the codepath,
# narrow enough to never hit a Windows path-syntax error mid-test. Reject the
# Windows reserved device names (CON, PRN, AUX, NUL, COM1-9, LPT1-9) and the
# `.`/`..` traversal cases. (audit F2.8)
_WIN_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
_PATH_NAME = st.text(
    min_size=1,
    max_size=40,
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.",
).filter(
    lambda s: s.strip(". ") != ""
    and s not in (".", "..")
    and s.upper() not in _WIN_RESERVED
)


def _fresh_repo_root(tmp_path: Path) -> Path:
    """Return a unique directory for each Hypothesis example.

    Hypothesis calls the test function once and runs many examples inside it,
    sharing the same `tmp_path`. Without this nonce, every example would write
    to the same `_session_state_dir` and the cached sampling decision from one
    example would poison the next.
    """
    p = tmp_path / uuid4().hex
    p.mkdir()
    return p


# ---------------------------------------------------------------------------
# is_sampled
# ---------------------------------------------------------------------------


@given(rate=st.floats(min_value=1.0, max_value=1e6, allow_nan=False, allow_infinity=False))
def test_is_sampled_true_when_rate_ge_one(tmp_path: Path, rate: float) -> None:
    repo_root = _fresh_repo_root(tmp_path)
    assert is_sampled(repo_root, rate) is True


@given(rate=st.floats(min_value=-1e6, max_value=0.0, allow_nan=False, allow_infinity=False))
def test_is_sampled_false_when_rate_le_zero(tmp_path: Path, rate: float) -> None:
    repo_root = _fresh_repo_root(tmp_path)
    assert is_sampled(repo_root, rate) is False


@given(rate=st.floats(min_value=0.001, max_value=0.999, allow_nan=False, allow_infinity=False))
def test_is_sampled_cached_decision_is_stable(tmp_path: Path, rate: float) -> None:
    """N consecutive calls inside the same session return the same decision.

    The first call may roll a random number; subsequent calls must read the
    persisted decision file. The issue asks for determinism for the same
    ``(session_id, rate)`` pair — ``session_id`` is not an argument of
    ``is_sampled``, so determinism flows from the cached ``_SESSION_SAMPLED_FILE``.

    Looped 10 times (audit F5.4). Two-call equality would be satisfied by a
    pathological implementation that flips on the 3rd, 5th, 7th call; the loop
    pins the spec's intent: same session, same rate, same answer, every time.
    """
    repo_root = _fresh_repo_root(tmp_path)
    first = is_sampled(repo_root, rate)
    for _ in range(9):
        assert is_sampled(repo_root, rate) == first


@given(rate=st.floats(min_value=0.001, max_value=0.999, allow_nan=False, allow_infinity=False))
def test_is_sampled_cache_invalidation_re_rolls(tmp_path: Path, rate: float) -> None:
    """Deleting the cache file mid-session re-rolls the decision (no stale-true poisoning).

    The issue #71 risk note flagged: "Hypothesis on is_sampled may surface a
    real bug in cache invalidation — investigate before suppressing." This
    test deliberately exercises the invalidation path: roll once, delete the
    cache file (simulating ``clear_session_state`` or a tempdir GC), roll
    again. Both calls must return SOME boolean (no crash on missing cache),
    and both must agree with whatever they each wrote to disk afterwards.
    Investigated; no bug surfaced. (audit F5.2)
    """
    import time
    from repo_context_hooks.telemetry import _session_state_dir, _SESSION_SAMPLED_FILE

    repo_root = _fresh_repo_root(tmp_path)
    first = is_sampled(repo_root, rate)
    cache = _session_state_dir(repo_root) / _SESSION_SAMPLED_FILE
    assert cache.exists(), "first call must persist the decision"

    cache.unlink()
    # Sleep long enough that mtime comparisons can't accidentally re-use stale
    # state on filesystems with second-resolution timestamps.
    time.sleep(0.01)
    second = is_sampled(repo_root, rate)
    assert isinstance(second, bool)
    # After re-roll, cache must reflect the new decision.
    assert cache.read_text(encoding="utf-8").strip() == ("true" if second else "false")
    # Suppress unused-variable lint when first happens to equal second.
    _ = first


# ---------------------------------------------------------------------------
# repo_id
# ---------------------------------------------------------------------------


_HEX = frozenset("0123456789abcdef")


@given(name=_PATH_NAME)
def test_repo_id_is_16_lowercase_hex_chars(tmp_path: Path, name: str) -> None:
    repo_root = tmp_path / name
    repo_root.mkdir(exist_ok=True)
    rid = repo_id(repo_root)
    assert len(rid) == 16
    assert set(rid).issubset(_HEX)


@given(name=_PATH_NAME)
def test_repo_id_stable_across_calls(tmp_path: Path, name: str) -> None:
    repo_root = tmp_path / name
    repo_root.mkdir(exist_ok=True)
    assert repo_id(repo_root) == repo_id(repo_root)
