# Security Policy

## Supported Versions

Security fixes are provided for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: (once shipped) |
| 0.6.x   | :white_check_mark: |
| < 0.6   | :x:                |

When 1.0.0 ships, the support window for 0.6.x will continue until the next minor release after 1.0 stabilizes.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report suspected vulnerabilities by email to:

**82136474+narendranathe@users.noreply.github.com**

Please include:

- A description of the issue and the impact you believe it has.
- Steps to reproduce, or a minimal proof-of-concept.
- The version of `repo-context-hooks` and the Python version you tested against.
- Whether you intend to disclose publicly, and on what timeline.

### What to expect

- **Acknowledgement** within 7 days of your report.
- **Initial assessment** within 14 days, including severity and a target fix window.
- **Coordinated disclosure**: we will agree on a public-disclosure date with the reporter before publishing any advisory.

Credit is given to reporters in the release notes unless anonymity is requested.

## Supply-Chain Updates

`repo-context-hooks` uses [Dependabot](https://docs.github.com/code-security/dependabot)
to monitor third-party code that ships into release artifacts and CI. The
canonical config is [`.github/dependabot.yml`](./.github/dependabot.yml).

- **Ecosystems watched.** Two ecosystems are configured by default:
  - `pip` — runtime and dev dependencies declared in `pyproject.toml`. The
    runtime surface ships zero deps (`dependencies = []`); the dev extras
    (`pytest`, `pytest-cov`, `hypothesis`) carry upper-version bounds so a
    compromised future major release cannot auto-install in CI.
  - `github-actions` — actions referenced by every workflow under
    `.github/workflows/`. Wave 1 validation PRs #80–#83 (bumping
    `actions/checkout`, `actions/setup-python`, `actions/upload-artifact`,
    `actions/download-artifact`) confirmed the loop is live.
- **Cadence.** Weekly per ecosystem, with `open-pull-requests-limit: 5` per
  block to bound the review queue. PRs are auto-labelled with `dependencies`
  plus the ecosystem name (`python` or `github-actions`).
- **SHA pinning for third-party Actions.** Third-party actions
  (e.g. `codecov/codecov-action`) are pinned to a 40-character commit SHA in
  workflow files. First-party `actions/*` continue to track major tags
  (Dependabot opens the upgrade PR; CI is the gate). See the `### Security`
  block in `CHANGELOG.md` for the most recent rationale.
- **Upper-bound dev-dep policy.** Dev extras pin upper bounds
  (`pytest<9`, `pytest-cov<8`, `hypothesis<7`); see `pyproject.toml` audit
  comment F3.4. When Dependabot opens a major-bump PR, the bound is
  intentionally bumped *with* the dependency, not removed.
- **For forks and downstream adopters.** The two ecosystems above are the
  minimum locked-in by the regression guard at
  `tests/test_dependabot_policy.py`. Adopters can append additional
  `package-ecosystem` blocks (`npm`, `gomod`, `bundler`, `cargo`, ...) —
  those additions are non-breaking and do not require a contract update.
  Removing `pip` or `github-actions` is a breaking change governed by the
  [stability contract](./docs/stability.md) and the
  [deprecation policy](./docs/deprecation-policy.md).
- **Source of truth.** `.github/dependabot.yml` is the live config;
  `tests/contract/dependabot_policy.json` is the human-reviewed frozen
  ecosystem set. Drift in either direction (silent removal *or* silent
  addition) fails CI.
