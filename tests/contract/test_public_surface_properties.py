"""Property-based tests for the public-surface introspection walker (issue #97).

The walker in ``scripts/check_public_surface.py`` reads private ``argparse``
attributes (``parser._actions``, ``_SubParsersAction.choices``). That's
tolerated because the alternative — re-implementing argparse — is worse,
but it makes the walker fragile in two specific ways:

1. argparse internals can shift across Python 3.9-3.13.
2. The walker is not stress-tested against synthetic graphs — it has only
   ever been exercised against the one real parser in ``cli.build_parser``.

This module Hypothesis-fuzzes random argparse trees (depth 0-2, with
top-level flags coexisting with subparsers, and the regex flag-name
generator from issue #97's acceptance criteria) and asserts the walker
output is deterministic, sort-stable, duplicate-free, and JSON-round-trips
byte-for-byte. A regression here means the walker silently dropped a flag
or returned non-deterministic output — both of which would let a public-
surface change slip through the gate.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hypothesis import given, strategies as st

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import check_public_surface as gate  # noqa: E402


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Acceptance-criteria regex: ``^--[a-z][a-z0-9-]{1,15}$``. Hypothesis'
# ``from_regex`` honours it and produces flag names like ``--frob``,
# ``--a-b-c``, ``--mode2``.
_FLAG_STRATEGY = st.from_regex(r"\A--[a-z][a-z0-9-]{1,15}\Z", fullmatch=True)

# Subcommand names: short, lower-case, no dashes (matches the real CLI
# conventions in `repo_context_hooks/cli.py`).
_SUBCOMMAND_NAME_STRATEGY = st.from_regex(r"\A[a-z][a-z0-9]{0,8}\Z", fullmatch=True)


def _flag_set_strategy(min_size: int = 0, max_size: int = 5) -> st.SearchStrategy:
    """Unique sets of flag names, excluding ``--help`` (reserved by argparse)."""
    return st.sets(
        _FLAG_STRATEGY.filter(lambda f: f != "--help"),
        min_size=min_size,
        max_size=max_size,
    )


def _name_set_strategy(min_size: int, max_size: int) -> st.SearchStrategy:
    """Unique sets of subcommand names."""
    return st.sets(
        _SUBCOMMAND_NAME_STRATEGY,
        min_size=min_size,
        max_size=max_size,
    )


def _build_parser(
    top_flags: list[str],
    subcommands: dict[str, dict[str, object]],
) -> argparse.ArgumentParser:
    """Build a synthetic argparse tree from a spec.

    ``subcommands`` maps ``name`` → ``{"flags": [...], "subs": {name: {...}}}``
    where the nested ``subs`` is at most one level deep (issue #97 caps
    depth at 0-2 — root + 2 levels of subparsers).
    """
    p = argparse.ArgumentParser(prog="synthetic", add_help=False)
    for f in top_flags:
        p.add_argument(f, action="store_true")
    if subcommands:
        subs = p.add_subparsers(dest="cmd")
        for name, spec in subcommands.items():
            sp = subs.add_parser(name, add_help=False)
            for f in spec.get("flags", []):  # type: ignore[arg-type]
                sp.add_argument(f, action="store_true")
            nested = spec.get("subs") or {}
            if nested:
                nsubs = sp.add_subparsers(dest=f"{name}_cmd")
                for nname, nspec in nested.items():  # type: ignore[union-attr]
                    nsp = nsubs.add_parser(nname, add_help=False)
                    for f in nspec.get("flags", []):
                        nsp.add_argument(f, action="store_true")
    return p


# Composite strategy: a parser spec at depth 0-2.
@st.composite
def _parser_spec(draw):
    top_flags = sorted(draw(_flag_set_strategy(min_size=0, max_size=4)))
    sub_names = draw(_name_set_strategy(min_size=0, max_size=4))
    subcommands: dict[str, dict[str, object]] = {}
    for name in sub_names:
        sub_flags = sorted(draw(_flag_set_strategy(min_size=0, max_size=4)))
        nested_names = draw(_name_set_strategy(min_size=0, max_size=2))
        nested: dict[str, dict[str, object]] = {}
        for nname in nested_names:
            nested[nname] = {
                "flags": sorted(draw(_flag_set_strategy(min_size=0, max_size=3))),
            }
        subcommands[name] = {"flags": sub_flags, "subs": nested}
    return {"top_flags": top_flags, "subcommands": subcommands}


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


@given(spec=_parser_spec())
def test_top_level_flag_extraction_is_deterministic(spec):
    """Two introspection passes over the same parser must return the same
    list — sort-stable, no duplicates, no missing flags.
    """
    parser = _build_parser(spec["top_flags"], spec["subcommands"])
    first = gate._extract_top_level_flags(parser)
    second = gate._extract_top_level_flags(parser)
    assert first == second
    assert first == sorted(first)
    assert len(first) == len(set(first))
    assert set(first) == set(spec["top_flags"])


@given(spec=_parser_spec())
def test_subcommand_walker_dedupes_and_sorts(spec):
    """``_extract_subcommands`` must return sorted-by-name, no duplicates,
    with each subcommand's flags also sorted and de-duplicated.
    """
    parser = _build_parser(spec["top_flags"], spec["subcommands"])
    subs = gate._extract_subcommands(parser)
    names = [s["name"] for s in subs]
    assert names == sorted(names)
    assert len(names) == len(set(names))
    for entry in subs:
        flags = entry["flags"]
        assert flags == sorted(flags)
        assert len(flags) == len(set(flags))


@given(spec=_parser_spec())
def test_introspection_json_round_trips(spec):
    """Serialising the walker output and parsing it back must produce the
    same object — i.e. every value is JSON-native and order is stable.

    Without this, a future refactor that snuck a ``set`` or ``frozenset``
    into the output would silently break ``json.dumps(sort_keys=True)``
    reproducibility and the freeze-baseline workflow in issue #96.
    """
    parser = _build_parser(spec["top_flags"], spec["subcommands"])
    payload = {
        "top_level_flags": gate._extract_top_level_flags(parser),
        "subcommands": gate._extract_subcommands(parser),
    }
    raw = json.dumps(payload, sort_keys=True)
    assert json.loads(raw) == payload
    # A second serialisation must be byte-identical (stable key order).
    assert json.dumps(json.loads(raw), sort_keys=True) == raw


@given(
    top_flags=_flag_set_strategy(min_size=1, max_size=4),
    sub_names=_name_set_strategy(min_size=1, max_size=3),
)
def test_top_level_and_subcommand_flags_are_disjoint_under_walker(
    top_flags, sub_names
):
    """``--frob`` declared on the root must show up under ``top_level_flags``
    and MUST NOT bleed into any subparser's flag list (and vice-versa).

    This is the exact bug class issue #97 calls out: a future walker
    refactor that confuses ``parser._actions`` for ``subparser._actions``
    would silently merge the two and the regression would only surface
    in a release that drops a flag.
    """
    subcommands = {
        name: {"flags": ["--inner-only"], "subs": {}} for name in sub_names
    }
    parser = _build_parser(sorted(top_flags), subcommands)
    extracted_top = set(gate._extract_top_level_flags(parser))
    extracted_subs = gate._extract_subcommands(parser)
    for entry in extracted_subs:
        sub_flags = set(entry["flags"])
        assert sub_flags & extracted_top == set(), (
            f"Subparser '{entry['name']}' leaks top-level flag(s): "
            f"{sorted(sub_flags & extracted_top)}"
        )
        assert "--inner-only" in sub_flags
    assert extracted_top == set(top_flags)
