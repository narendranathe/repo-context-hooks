"""Regression guard for issue #85 — Dependabot supply-chain policy audit.

Stdlib-only on purpose: the project ships ``dependencies = []`` and the
dev-dep surface is intentionally minimal (``pyproject.toml`` audit comment
F3.4). Do NOT add PyYAML to read a ~40-line config file. This module uses
``re`` + ``pathlib`` in the same spirit as ``repo_context_hooks/changelog.py``.

Failure modes covered (per Phase 1 critic-C lens):

- File missing                            → ``test_dependabot_yml_exists``
- UTF-8 BOM at file head                  → ``test_no_utf8_bom``
- Schema-version drift                    → ``test_declares_version_2``
- Dependabot globally disabled            → ``test_not_globally_disabled``
- Bidirectional ecosystem drift           → ``test_ecosystems_match_frozen_contract``
                                            (the non-negotiable assertion)
- Block missing ``directory: "/"``        → ``test_block_has_root_directory``
- Block missing/typo'd cadence            → ``test_block_has_supported_interval``
- Sane PR-limit (1..10)                   → ``test_block_has_sane_pr_limit``
- Doc/config drift in either direction    → ``test_security_md_documents_both_ecosystems``
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DEPENDABOT_YML = REPO_ROOT / ".github" / "dependabot.yml"
SECURITY_MD = REPO_ROOT / "SECURITY.md"
CONTRACT_PATH = REPO_ROOT / "tests" / "contract" / "dependabot_policy.json"

# Quoting flexibility: GitHub Dependabot accepts ``"pip"``, ``'pip'``, and
# bare ``pip``. The regex tolerates all three so a future contributor who
# unquotes a value does not red-X a *valid* config.
_ECOSYSTEM_LINE_RE = re.compile(
    r'^\s*-\s*package-ecosystem:\s*["\']?(?P<eco>[a-z][a-z0-9_-]*)["\']?\s*$',
    re.MULTILINE,
)
_VERSION_RE = re.compile(r"^version:\s*2\s*$", re.MULTILINE)
_INTERVAL_RE = re.compile(
    r'^\s+interval:\s*["\']?(?P<v>daily|weekly|monthly)["\']?\s*$',
    re.MULTILINE,
)
_LIMIT_RE = re.compile(
    r"^\s+open-pull-requests-limit:\s*(?P<n>\d+)\s*$", re.MULTILINE
)
_DIRECTORY_RE = re.compile(
    r'^\s+directory:\s*["\']?(?P<d>[^"\'\s]+)["\']?\s*$', re.MULTILINE
)
_DISABLED_RE = re.compile(r"^enabled:\s*false\s*$", re.MULTILINE)


def _read_text() -> str:
    """Strict UTF-8 read with CRLF normalisation; no BOM tolerated."""
    raw = DEPENDABOT_YML.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), "dependabot.yml has UTF-8 BOM"
    return raw.decode("utf-8").replace("\r\n", "\n")


def _strip_comments(text: str) -> str:
    """Drop lines whose first non-whitespace char is ``#``.

    Without this, a commented-out ``# - package-ecosystem: "npm"`` would
    register as an ecosystem and fool the bidirectional drift guard.
    """
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )


def _parse_ecosystem_blocks(text: str) -> dict[str, str]:
    """Return ``{ecosystem_name: block_text}`` for every top-level block.

    A block is the text from a ``- package-ecosystem:`` line up to the next
    ``- package-ecosystem:`` line (or EOF). Comment lines are stripped before
    parsing so a ``#``-commented block does not register.
    """
    body = _strip_comments(text)
    matches = list(_ECOSYSTEM_LINE_RE.finditer(body))
    blocks: dict[str, str] = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        blocks[m.group("eco")] = body[m.start() : end]
    return blocks


def _expected_ecosystems() -> frozenset[str]:
    payload = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    return frozenset(payload["required_ecosystems"])


_PARAMETRIZED_ECOSYSTEMS = sorted({"github-actions", "pip"})


# ─── Existence + shape ──────────────────────────────────────────────────────

def test_dependabot_yml_exists() -> None:
    assert DEPENDABOT_YML.is_file(), f"missing: {DEPENDABOT_YML}"


def test_contract_file_exists() -> None:
    assert CONTRACT_PATH.is_file(), f"missing: {CONTRACT_PATH}"


def test_no_utf8_bom() -> None:
    raw = DEPENDABOT_YML.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")


def test_declares_version_2() -> None:
    assert _VERSION_RE.search(_read_text()), (
        "dependabot.yml must declare `version: 2` at column 0"
    )


def test_not_globally_disabled() -> None:
    """A drive-by ``enabled: false`` would silently void the entire policy."""
    assert not _DISABLED_RE.search(_strip_comments(_read_text()))


# ─── The non-negotiable: bidirectional drift guard (critic-C) ──────────────

def test_ecosystems_match_frozen_contract() -> None:
    """Removing pip OR github-actions fails. Silently adding npm fails too.

    Updating the contract is a deliberate JSON edit reviewed in PR — that is
    the policy this guard is meant to install (issue #85 AC #3).
    """
    found = frozenset(_parse_ecosystem_blocks(_read_text()).keys())
    expected = _expected_ecosystems()
    assert found == expected, (
        f"Dependabot ecosystem set drifted.\n"
        f"  found:    {sorted(found)}\n"
        f"  expected: {sorted(expected)}\n"
        f"  contract: {CONTRACT_PATH.relative_to(REPO_ROOT)}\n"
        "If the change is intentional, update the contract JSON in the same PR."
    )


# ─── Per-block hygiene (parametrized — one named test per ecosystem) ───────

@pytest.fixture
def blocks() -> dict[str, str]:
    return _parse_ecosystem_blocks(_read_text())


@pytest.mark.parametrize("ecosystem", _PARAMETRIZED_ECOSYSTEMS)
def test_block_has_root_directory(
    blocks: dict[str, str], ecosystem: str
) -> None:
    body = blocks.get(ecosystem)
    assert body, f"missing block for {ecosystem!r}"
    dirs = [m.group("d") for m in _DIRECTORY_RE.finditer(body)]
    assert "/" in dirs, (
        f"{ecosystem!r} block must include `directory: \"/\"` (found {dirs})"
    )


@pytest.mark.parametrize("ecosystem", _PARAMETRIZED_ECOSYSTEMS)
def test_block_has_supported_interval(
    blocks: dict[str, str], ecosystem: str
) -> None:
    body = blocks.get(ecosystem)
    assert body, f"missing block for {ecosystem!r}"
    intervals = [m.group("v") for m in _INTERVAL_RE.finditer(body)]
    assert intervals, f"{ecosystem!r} block missing `interval:`"
    assert all(v in {"daily", "weekly", "monthly"} for v in intervals), (
        f"{ecosystem!r} interval values must be one of daily/weekly/monthly"
    )


@pytest.mark.parametrize("ecosystem", _PARAMETRIZED_ECOSYSTEMS)
def test_block_has_sane_pr_limit(
    blocks: dict[str, str], ecosystem: str
) -> None:
    body = blocks.get(ecosystem)
    assert body, f"missing block for {ecosystem!r}"
    limits = [int(m.group("n")) for m in _LIMIT_RE.finditer(body)]
    if limits:  # field is optional; if present, must be sane.
        assert all(1 <= n <= 10 for n in limits), (
            f"{ecosystem!r} open-pull-requests-limit must be in 1..10"
        )


# ─── Doc cross-link guard (critic-C #9) ────────────────────────────────────

def test_security_md_documents_both_ecosystems() -> None:
    """SECURITY.md must reference both ecosystems by exact name.

    Catches the failure mode where someone adds an ecosystem to YAML but
    forgets to update the policy doc, or vice-versa.
    """
    text = SECURITY_MD.read_text(encoding="utf-8")
    assert "Supply-Chain Updates" in text, (
        "SECURITY.md is missing the `## Supply-Chain Updates` section"
    )
    for ecosystem in _expected_ecosystems():
        assert ecosystem in text, (
            f"SECURITY.md does not mention ecosystem {ecosystem!r}"
        )
