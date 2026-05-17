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
- Section-scoped ecosystem mention drift  → ``test_security_md_ecosystem_bullet_per_required``
                                            (issue #101 tightening)
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

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


# ─── Doc cross-link guard (critic-C #9, issue #101 tightening) ─────────────

_SUPPLY_CHAIN_HEADING_RE = re.compile(
    r"^##\s+Supply-Chain Updates\s*$", re.MULTILINE
)
_NEXT_H2_RE = re.compile(r"^##\s+\S", re.MULTILINE)


def _supply_chain_section(text: str) -> str:
    """Return the body of the ``## Supply-Chain Updates`` H2 section.

    Sliced between its own heading and the next H2 (or EOF). Returns the
    empty string if the section is missing. The slice is the unit the
    bullet-count guard operates on — without it, ``"npm"`` appearing in
    an unrelated section would mask a missing entry in this one.
    """
    match = _SUPPLY_CHAIN_HEADING_RE.search(text)
    if not match:
        return ""
    rest = text[match.end():]
    next_h2 = _NEXT_H2_RE.search(rest)
    return rest[: next_h2.start()] if next_h2 else rest


def _missing_ecosystem_bullets(
    section_text: str, ecosystems: Iterable[str]
) -> list[str]:
    """Return ecosystems lacking a standalone bullet mention in ``section_text``.

    A standalone mention is a bullet line whose first non-whitespace tokens
    are ``- `` followed by an inline-code-wrapped ecosystem name (``- `pip` …``).
    Plain prose containing the word, or a fenced-code occurrence, does not
    count — that is the leakage path #101 was filed to close.
    """
    missing: list[str] = []
    for eco in ecosystems:
        pattern = re.compile(
            rf"^\s*-\s+`{re.escape(eco)}`(?:\s|$)", re.MULTILINE
        )
        if not pattern.search(section_text):
            missing.append(eco)
    return sorted(missing)


def test_security_md_documents_both_ecosystems() -> None:
    """SECURITY.md must reference every required ecosystem by exact name
    somewhere in the file.

    Catches the failure mode where someone adds an ecosystem to YAML but
    forgets to update the policy doc, or vice-versa. The
    ``test_security_md_ecosystem_bullet_per_required`` guard below tightens
    this to a section-scoped, bullet-shaped mention.
    """
    text = SECURITY_MD.read_text(encoding="utf-8")
    assert "Supply-Chain Updates" in text, (
        "SECURITY.md is missing the `## Supply-Chain Updates` section"
    )
    for ecosystem in _expected_ecosystems():
        assert ecosystem in text, (
            f"SECURITY.md does not mention ecosystem {ecosystem!r}"
        )


def test_security_md_ecosystem_bullet_per_required() -> None:
    """Each required ecosystem must appear as a standalone bullet inside
    ``## Supply-Chain Updates`` — not just anywhere in the file (issue #101).

    Closes the leakage path flagged in PR #98's phase-2 review: a future PR
    that adds ``npm`` to ``dependabot.yml`` + the contract JSON but forgets
    to add ``- `npm` —`` under the section would slip past the looser guard
    above as long as the literal token ``npm`` appeared *anywhere* (an
    unrelated example, a code fence, a sentence). The bullet-shape check
    here is the smaller of the two options in #101 and matches the existing
    ``- `pip` — …`` / ``- `github-actions` — …`` doc layout.
    """
    text = SECURITY_MD.read_text(encoding="utf-8")
    section = _supply_chain_section(text)
    assert section, (
        "SECURITY.md is missing the `## Supply-Chain Updates` section heading"
    )
    missing = _missing_ecosystem_bullets(section, _expected_ecosystems())
    assert not missing, (
        "SECURITY.md `## Supply-Chain Updates` is missing a standalone "
        f"bullet (``- `<name>` …``) for: {missing}. Each ecosystem listed in "
        f"{CONTRACT_PATH.relative_to(REPO_ROOT)} must appear as its own "
        "bullet inside that section so an adopter scanning the policy doc "
        "sees every ecosystem at a glance — not just incidental prose."
    )


# ─── Meta-test: the bullet-count guard can actually fail ────────────────────

def test_supply_chain_section_slice_isolates_h2_block() -> None:
    """The slicer must return only the ``## Supply-Chain Updates`` body —
    if it leaked into the previous or next H2 section, an incidental
    mention there would silently satisfy the guard.
    """
    fake = (
        "# Title\n"
        "## Supported Versions\n"
        "- `pip` mentioned incidentally here.\n"
        "## Supply-Chain Updates\n"
        "- `pip` — bullet present.\n"
        "## Reporting\n"
        "- `github-actions` — present but outside the watched section.\n"
    )
    section = _supply_chain_section(fake)
    assert "- `pip` — bullet present." in section
    assert "Supported Versions" not in section
    assert "Reporting" not in section
    assert "github-actions" not in section


@pytest.mark.parametrize(
    "section_text,ecosystems,expected_missing",
    [
        pytest.param(
            "- `pip` — runtime deps.\n- `github-actions` — workflow actions.\n",
            ["pip", "github-actions"],
            [],
            id="both-bullets-present-pass",
        ),
        pytest.param(
            "- `pip` — runtime deps. github-actions is also watched.\n",
            ["pip", "github-actions"],
            ["github-actions"],
            id="prose-only-mention-fails-just-like-the-leakage-path",
        ),
        pytest.param(
            "```\nnpm install pip\n```\n",
            ["pip"],
            ["pip"],
            id="code-fence-occurrence-does-not-count",
        ),
        pytest.param(
            "- adds pip support somewhere\n",
            ["pip"],
            ["pip"],
            id="unwrapped-name-in-bullet-does-not-count",
        ),
        pytest.param(
            "",
            ["pip"],
            ["pip"],
            id="empty-section-reports-every-missing",
        ),
    ],
)
def test_missing_ecosystem_bullets_detects_each_failure_mode(
    section_text: str,
    ecosystems: list[str],
    expected_missing: list[str],
) -> None:
    """Drives the helper through every shape #101 flagged as a leakage
    path — proves the new assertion would red-X with the right diagnostic
    rather than silently passing.
    """
    assert (
        _missing_ecosystem_bullets(section_text, ecosystems) == expected_missing
    )
