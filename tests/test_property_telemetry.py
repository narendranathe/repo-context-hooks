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

from hypothesis import HealthCheck, given, settings, strategies as st

from repo_context_hooks.telemetry import is_sampled, repo_id

# derandomize=True makes any failure deterministic so a CI flake is reproducible
# locally instead of being a merge-blocking ghost. deadline=None protects the
# Windows runners (which can be 5x slower than the Linux ones) from spurious
# timeouts when the JSON-on-disk state writes happen. The function_scoped_fixture
# suppression is intentional: every test below either nonces its own subdir under
# tmp_path or uses the Hypothesis-generated `name` to disambiguate, so sharing the
# parent tmp_path across examples is safe.
_PROPERTY_SETTINGS = settings(
    derandomize=True,
    deadline=None,
    max_examples=50,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

# Path components must be safe on every CI OS. Restrict to ASCII letters,
# digits, hyphen, underscore, and dot — broad enough to exercise the codepath,
# narrow enough to never hit a Windows path-syntax error mid-test.
_PATH_NAME = st.text(
    min_size=1,
    max_size=40,
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.",
).filter(lambda s: s.strip(". ") != "")


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


@_PROPERTY_SETTINGS
@given(rate=st.floats(min_value=1.0, max_value=1e6, allow_nan=False, allow_infinity=False))
def test_is_sampled_true_when_rate_ge_one(tmp_path: Path, rate: float) -> None:
    repo_root = _fresh_repo_root(tmp_path)
    assert is_sampled(repo_root, rate) is True


@_PROPERTY_SETTINGS
@given(rate=st.floats(min_value=-1e6, max_value=0.0, allow_nan=False, allow_infinity=False))
def test_is_sampled_false_when_rate_le_zero(tmp_path: Path, rate: float) -> None:
    repo_root = _fresh_repo_root(tmp_path)
    assert is_sampled(repo_root, rate) is False


@_PROPERTY_SETTINGS
@given(rate=st.floats(min_value=0.001, max_value=0.999, allow_nan=False, allow_infinity=False))
def test_is_sampled_cached_decision_is_stable(tmp_path: Path, rate: float) -> None:
    """Two consecutive calls inside the same session return the same decision.

    The first call may roll a random number; the second must read the persisted
    decision file and return identically. This is the determinism the issue
    asks for — `session_id` is not an argument of `is_sampled`, so determinism
    actually flows from the cached `_SESSION_SAMPLED_FILE`.
    """
    repo_root = _fresh_repo_root(tmp_path)
    first = is_sampled(repo_root, rate)
    second = is_sampled(repo_root, rate)
    assert first == second


# ---------------------------------------------------------------------------
# repo_id
# ---------------------------------------------------------------------------


_HEX = frozenset("0123456789abcdef")


@_PROPERTY_SETTINGS
@given(name=_PATH_NAME)
def test_repo_id_is_16_lowercase_hex_chars(tmp_path: Path, name: str) -> None:
    repo_root = tmp_path / name
    repo_root.mkdir(exist_ok=True)
    rid = repo_id(repo_root)
    assert len(rid) == 16
    assert set(rid).issubset(_HEX)


@_PROPERTY_SETTINGS
@given(name=_PATH_NAME)
def test_repo_id_stable_across_calls(tmp_path: Path, name: str) -> None:
    repo_root = tmp_path / name
    repo_root.mkdir(exist_ok=True)
    assert repo_id(repo_root) == repo_id(repo_root)
