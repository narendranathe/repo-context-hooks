# README Install Flow and JSON Output Implementation Plan

**Goal:** Improve the public README adoption path and add machine-readable output for the commands agents and scripts are most likely to consume.

## Task 1: Lock README and JSON expectations with tests

- Update README contract tests so the README requires separate platform install snippets.
- Add tests that keep internal-heavy docs out of the README primary link path.
- Add CLI/parser tests for `--json`.
- Add model tests for report `to_dict()` methods.

## Task 2: Add JSON serialization

- Add `to_dict()` methods to doctor reports.
- Add `to_dict()` methods to recommendation reports.
- Add JSON rendering support in the CLI.
- Add `--json` to `platforms`, `doctor`, and `recommend`.

## Task 3: Rewrite README and supporting docs

- Split install/setup into smaller copyable blocks.
- Add a `Pick Your Platform` section.
- Remove platform playbook links from the public README path.
- Keep support matrix docs focused on claims and readiness.

## Task 4: Verify and publish

- Run focused tests.
- Run the full test suite.
- Smoke-test representative JSON commands.
- Commit, push, and open a PR.
