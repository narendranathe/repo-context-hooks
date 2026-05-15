# Contributing to repo-context-hooks

Thank you for taking the time to contribute. This document covers the full contribution workflow.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Reporting Issues](#reporting-issues)
- [Development Setup](#development-setup)
- [Branch and PR Flow](#branch-and-pr-flow)
- [Coding Standards](#coding-standards)
- [Commit Sign-off](#commit-sign-off)

## Code of Conduct

This project follows the [Contributor Covenant 2.1](CODE_OF_CONDUCT.md). By participating you agree to uphold it.

## Reporting Issues

- **Bugs**: open a [Bug report](https://github.com/narendranathe/repo-context-hooks/issues/new?template=bug.yml).
- **Features**: open a [Feature request](https://github.com/narendranathe/repo-context-hooks/issues/new?template=feature.yml).
- **Questions**: open a [Question](https://github.com/narendranathe/repo-context-hooks/issues/new?template=question.yml) or start a [Discussion](https://github.com/narendranathe/repo-context-hooks/discussions).
- **Security vulnerabilities**: do **not** open a public issue - see [SECURITY.md](SECURITY.md).

## Development Setup

```bash
git clone https://github.com/narendranathe/repo-context-hooks.git
cd repo-context-hooks
pip install -e ".[dev]"
python -m pytest -q
```

All tests must pass before submitting a PR.

## Branch and PR Flow

1. Fork the repository and create a branch from `main`:
   ```bash
   git checkout -b feat/your-feature
   ```
2. Make your changes - one concern per PR.
3. Add or update tests that cover your change.
4. Update `CHANGELOG.md` under the `[Unreleased]` section.
5. Push to your fork and open a pull request against `main`.

Keep PRs focused. A PR that mixes a bug fix with a refactor will be asked to split.

## Coding Standards

- Python 3.9+ compatible syntax.
- Follow the style of the surrounding code - no reformatting unrelated lines.
- No new runtime dependencies without prior discussion in an issue.
- Public functions and CLI commands must have a docstring.

## Commit Sign-off

All commits require a Developer Certificate of Origin sign-off:

```bash
git commit -s -m "feat: your message"
```

This adds a `Signed-off-by` trailer confirming you have the right to submit the work under the project license. See <https://developercertificate.org> for the full text.
