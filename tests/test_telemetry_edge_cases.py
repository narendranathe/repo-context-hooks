"""Edge-case regression tests for telemetry primitives.

Covers contracts that the issue #71 property tests deliberately scoped out as
"out-of-contract": NaN, +/- infinity sample rates. After the audit (F1.1) we
made NaN behaviour intentional rather than accidental — this module locks that
contract so a future refactor cannot silently re-introduce the silent opt-out.
"""
from __future__ import annotations

import math
from pathlib import Path

from repo_context_hooks.telemetry import is_sampled


def test_is_sampled_nan_rate_is_treated_as_zero(tmp_path: Path) -> None:
    """NaN must be coerced to opt-out, not pass through to ``random.random() < NaN``.

    Pre-fix behaviour: every NaN call returned False because ``random.random() <
    NaN`` is always False — silent permanent opt-out, no diagnostic. Post-fix:
    the function explicitly coerces NaN to rate=0.0 (safe default).
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    assert is_sampled(repo_root, float("nan")) is False


def test_is_sampled_positive_infinity_always_samples(tmp_path: Path) -> None:
    """``inf >= 1.0`` is True so the deterministic-rate shortcut returns True."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    assert is_sampled(repo_root, math.inf) is True


def test_is_sampled_negative_infinity_never_samples(tmp_path: Path) -> None:
    """``-inf <= 0.0`` is True so the deterministic-rate shortcut returns False."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    assert is_sampled(repo_root, -math.inf) is False
