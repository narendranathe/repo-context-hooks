# Stability Contract

`repo-context-hooks` follows [Semantic Versioning 2.0.0](https://semver.org/) starting at the `1.0.0` release. This page is the canonical answer to **"what can I rely on across a 1.x → 1.y bump?"**.

If a behaviour is listed under [Stable surfaces](#stable-surfaces), we will not break it without first going through the [deprecation policy](deprecation-policy.md). If a behaviour is listed under [Internal surfaces](#internal-surfaces), we may change it at any time, including in a patch release.

The contract is enforced in CI by `scripts/check_public_surface.py`, which compares the running package against the snapshot in `tests/contract/public_surface.json`. A removal that does not follow the deprecation policy fails the build.

---

## Stable surfaces

These will not break before the next MAJOR release without first being deprecated for at least one full MINOR cycle.

### Console scripts

The package installs three console scripts. All three resolve to the same CLI; the additional names exist for muscle-memory compatibility:

- `repo-context-hooks`
- `repohandoff`
- `graphify`

Removing any of these names is a breaking change.

### CLI subcommands

Every documented subcommand of the CLI:

- `install`
- `init`
- `doctor`
- `recommend`
- `measure` (including `measure export`, `measure experiment {start,finish,status}`)
- `platforms`
- `uninstall`
- `checkpoint`
- `telemetry` (including `telemetry status`, `telemetry preview`, `telemetry enable`, `telemetry disable`)

The full list of subcommand names and their flags is enumerated in `tests/contract/public_surface.json::cli_commands`.

### CLI flags

Every documented flag on the subcommands above is part of the contract. Renaming, removing, or changing the type of a flag requires a deprecation cycle.

Adding a new flag is non-breaking. Adding a new subcommand is non-breaking.

### Top-level flags

Flags declared on the root parser — above the subcommand dispatch — are part of the contract too. Today this includes:

- `--version` — print version + git sha + python + platform + install method and exit.
- `--debug` — promote stderr logging to DEBUG and write full tracebacks to the error log.

These are pinned in `tests/contract/public_surface.json::top_level_flags` and enforced by `scripts/check_public_surface.py`. Renaming or removing one requires a deprecation cycle on the same terms as a subcommand flag.

### `--platform` choices

The accepted values for `--platform` (`claude`, `cursor`, `codex`, `replit`, `windsurf`, `lovable`, `openclaw`, `ollama`, `kimi`) are part of the contract. Removing a platform from this list is a breaking change and follows the deprecation policy: the value continues to be accepted for one MINOR cycle, emits a `DeprecationWarning`, and points the user to the replacement (or `none`).

Adding a new platform is non-breaking.

### Environment variables

The `REPO_CONTEXT_HOOKS_*` namespace, as documented in [TELEMETRY.md](https://github.com/narendranathe/repo-context-hooks/blob/main/TELEMETRY.md). Today this includes:

- `REPO_CONTEXT_HOOKS_TELEMETRY` — `0`/`1` toggle, hard opt-out
- `REPO_CONTEXT_HOOKS_TELEMETRY_DIR` — directory override for the telemetry log
- `REPO_CONTEXT_HOOKS_SAMPLE_RATE` — float in `[0.0, 1.0]`, defaults to `1.0`
- `REPO_CONTEXT_HOOKS_SESSION_ID` — UUID override for deterministic test runs
- `REPO_CONTEXT_HOOKS_LOG_DIR` — directory override for the self-observability error log (`errors.log`). Defaults to `$XDG_CACHE_HOME/repo-context-hooks/logs/` on POSIX or `%LOCALAPPDATA%\repo-context-hooks\logs\` on Windows. The directory is created lazily on first error — successful runs leave no filesystem trace.

The full list lives in `tests/contract/public_surface.json::env_vars`. Removing or renaming any of these requires a deprecation cycle. Both names continue to be read for one full MINOR.

### File locations

- `~/.cache/repo-context-hooks/events.jsonl` (Linux, macOS) — telemetry evidence log
- `%LOCALAPPDATA%\repo-context-hooks\events.jsonl` (Windows) — telemetry evidence log
- `~/.cache/repo-context-hooks/logs/errors.log` (Linux, macOS) — self-observability error log (rotated, 5 × 1 MB)
- `%LOCALAPPDATA%\repo-context-hooks\logs\errors.log` (Windows) — self-observability error log (rotated, 5 × 1 MB)
- `~/.claude/settings.json` — agent-level hook installation target (we own only the hook entries we wrote; the rest is the user's)
- `<repo>/.claude/settings.json` — workspace-level hook installation target (same ownership rule)
- `<repo>/specs/README.md` `## Session Log` heading — checkpoint append target

These locations and the partial-ownership rule will not change before MAJOR.

### Configuration contracts

The supply-chain policy file `.github/dependabot.yml` is part of the stability contract. Removing the `pip` or `github-actions` ecosystem is a breaking change that follows the [deprecation policy](deprecation-policy.md): the regression guard at `tests/test_dependabot_policy.py`, frozen against `tests/contract/dependabot_policy.json`, blocks accidental drops. Adopters forking the project may add additional ecosystems (`npm`, `gomod`, `bundler`, etc.) — those additions are non-breaking and do not require a contract update. The full policy, cadence, and rationale are documented in [SECURITY.md § Supply-Chain Updates](https://github.com/narendranathe/repo-context-hooks/blob/main/SECURITY.md#supply-chain-updates).

### Python API

```python
from repo_context_hooks import __version__
```

That is the entire stable Python surface. `__all__` in `repo_context_hooks/__init__.py` is the source of truth.

If you are importing anything else, you are using an internal surface and you should expect it to change.

---

## Internal surfaces

These may change in any release, including patch.

- Every submodule of `repo_context_hooks` not re-exported via `__all__`: `cli`, `installer`, `doctor`, `recommend`, `repo_contract`, `consent`, `telemetry`, `badge`, every module under `platforms/`.
- Internal helpers and private functions (anything prefixed with `_`).
- The shape of records written to `events.jsonl` beyond the documented core schema (see [TELEMETRY.md](https://github.com/narendranathe/repo-context-hooks/blob/main/TELEMETRY.md) for the documented core).
- Exit-code values beyond the binary "zero on success, non-zero on failure" guarantee. Specific non-zero exit codes are not stable and should not be branched on by scripts.
- The exact text of log lines, error messages, and console output. Tests should not regex against these.
- Bundle scripts under `repo_context_hooks/bundle/scripts/` — these are subprocess-invoked by hooks and their internal layout is an implementation detail.
- The HTML and SVG output of `measure --badge`, `measure export --format markdown`, and the dashboard at `docs/monitoring/`.

---

## Why a public surface this small

`repo-context-hooks` is a tool you install, not a library you import. The CLI is the primary product. Keeping the Python `__all__` minimal lets us refactor the internals freely without breaking anyone in the wild.

If you need a function from an internal submodule for a real use case, open an issue describing the use case and we will consider promoting it. Promotion is its own change and lands in the `### Added` section of the next release.

---

## Related

- [Deprecation policy](deprecation-policy.md) — how we remove things from the surface above
- [Telemetry policy](telemetry-policy.md) — what we collect and where it goes
