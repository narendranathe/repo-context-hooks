# Troubleshooting

Common failure modes encountered while installing, running, or auditing
`repo-context-hooks`. Each entry is sourced from a closed issue — the
reproduction and fix below are self-contained, the issue link is for
forensics. The `Last verified` line records the version on which the
reproduction was last confirmed; if you hit one of these on a newer release,
please [open a new issue](https://github.com/narendranathe/repo-context-hooks/issues/new)
so we can refresh the page.

If your symptom does not match anything below, run `repo-context-hooks doctor`
first and then `repo-context-hooks --debug <subcommand>` to surface a
traceback in `<cache>/errors.log`. The "Last error" section in `doctor` output
prints the path so you do not have to guess where it landed.

---

## Hooks do not fire after install

### Symptom

`repo-context-hooks install --platform claude` exits 0, `doctor` reports the
platform as ready, but `~/.cache/repo-context-hooks/events.jsonl` is empty
after starting a Claude Code session in a workspace that has `specs/README.md`.
No `SessionStart`, `PreCompact`, or `SessionEnd` records ever appear.

### Reproduce

1. POSIX: `pip install --user repo-context-hooks && repo-context-hooks install --platform claude`.
2. Open a fresh Claude Code session in a directory that contains `specs/README.md` and `.git/`.
3. Run `cat ~/.cache/repo-context-hooks/events.jsonl` (POSIX) or
   `Get-Content "$env:LOCALAPPDATA\repo-context-hooks\events.jsonl"` (Windows).

### Fix

The most common root cause is that `~/.claude/settings.json` was not actually
updated — Claude Code only loads hooks from the file Python's `Path.home()`
resolves to at install time. Re-install with `--force` after confirming
`echo $HOME` (POSIX) or `echo $env:USERPROFILE` (Windows) matches the
`Agent home` line printed by `repo-context-hooks doctor`. If the agent home
matches but events still do not fire, run `repo-context-hooks verify --platform claude`
to round-trip a synthetic event end-to-end — verify writes to an isolated
tmpdir and tells you within two seconds whether the hook plumbing is wired
to the same `settings.json` Claude is reading. See the
[`verify` reference](cli-reference.md) and the
[Verify section of the home page](index.md).

### Last verified

`0.6.0` — provenance: closed issue
[#41](https://github.com/narendranathe/repo-context-hooks/issues/41)
(end-to-end smoke test pip install → install → doctor → hook fires).

---

## `events.jsonl` is empty after a complete session

### Symptom

`repo-context-hooks install` succeeded, the `SessionStart` record appears in
`events.jsonl`, but no `SessionEnd` or `PreCompact` records ever land — even
after closing the session normally. `repo-context-hooks measure` reports
`0% lifecycle coverage` on a workspace where you have actually been working.

### Reproduce

1. Install the agent skill and open a session.
2. Work for at least a minute, then close the session via the platform's
   normal "end" or "exit" flow.
3. Run `repo-context-hooks measure --json` and inspect `lifecycle_coverage`.

### Fix

Two failure paths converge on this symptom:

1. The session-end subprocess timed out before the bundle script could finish
   writing. The default timeout was raised to 30 seconds in 0.6.0; if you are
   on an older release, upgrade.
2. A previous version inlined `measure_impact` inside `record_event`, which
   could fail under filesystem pressure and silently swallow the write. The
   fix decoupled the two; if you are on 0.6.0 or later you should not see
   this anymore.

To recover lifecycle coverage on an existing repo, run
`repo-context-hooks measure --clean-ghosts` to remove any test-run "ghost"
repos that pollute the count, then `repo-context-hooks measure` again.

### Last verified

`0.6.0` — provenance: closed issue
[#57](https://github.com/narendranathe/repo-context-hooks/issues/57)
(remove inline `measure_impact` from `record_event`, raise session-end
timeout to 30s).

---

## `settings.json` got clobbered or has duplicate hook entries

### Symptom

After running `install` more than once (e.g. on a release upgrade), your
agent's `settings.json` either lost a user-authored hook entry or now contains
the same `repo-context-hooks` command three or four times. Claude prints a
warning about hook ordering, or you see duplicate events in `events.jsonl`
for the same session.

### Reproduce

1. Manually add a custom `SessionStart` hook to `~/.claude/settings.json`.
2. Run `repo-context-hooks install --platform claude` twice.
3. Open `~/.claude/settings.json` and look for repeated entries with the same
   `command` field, or a missing user-authored hook.

### Fix

`install` is idempotent against its own writes, but path normalization differs
between Windows and POSIX (mixed `/` and `\\` resolved to distinct strings),
which used to defeat the deduplication check. Re-run with the `--dedup` flag:

```bash
repo-context-hooks install --platform claude --dedup
```

This collapses entries whose `command` strings are equal under canonical
path normalization. Before letting `install` write, you can audit what would
change with:

```bash
repo-context-hooks install --platform claude --dry-run
```

The `--dry-run` flag prints the unified diff that would be applied and exits
without writing. Pair with `--json` for a machine-parseable diff suitable for
change-control review.

### Last verified

`0.6.0` — provenance: closed issue
[#58](https://github.com/narendranathe/repo-context-hooks/issues/58)
(hook deduplication, normalise paths in `install_global_hooks`, `--dedup`
flag).

---

## Windows path issues — backslashes, mixed separators, agent-home mismatch

### Symptom

On Windows, `install` succeeded but `doctor` exits non-zero with a path
mismatch error. Or `~/.claude/settings.json` shows hook commands containing
backslashes (`C:\\Users\\you\\AppData\\…`) and Claude Code refuses to load
them. Or you ran `install` from Git Bash (`/c/Users/you/...`) and the saved
paths do not match what Claude reads.

### Reproduce

1. Windows: open Git Bash and run `repo-context-hooks install --platform claude`.
2. Open `%USERPROFILE%\.claude\settings.json` in Notepad and look for the
   hook entries. Mixed `/c/Users/you/` and native `C:\Users\you\` paths
   indicate the bug.
3. Run `repo-context-hooks doctor --platform claude` from `cmd.exe`.

### Fix

`install` now writes POSIX-style forward-slash paths regardless of which shell
invoked it, and the smoke-test job in CI specifically asserts no backslash
paths leak into `settings.json` on Windows. Upgrade to 0.6.0 or later. If
you have a polluted `settings.json` from an older release, the safest
recovery is:

```bash
# Windows (PowerShell)
repo-context-hooks uninstall --platform claude --dry-run
repo-context-hooks uninstall --platform claude
repo-context-hooks install --platform claude
```

`uninstall` only removes the hook entries it owns — your custom hooks are
preserved.

### Last verified

`0.6.0` — provenance: closed issue
[#46](https://github.com/narendranathe/repo-context-hooks/issues/46)
(audit and fix Windows path handling across install, doctor, and hook
commands).

---

## Multiple Python environments — agent runs the wrong `repo-context-hooks`

### Symptom

`pip install repo-context-hooks` lands in your project venv, but Claude Code
runs in your system shell where `which repo-context-hooks` (POSIX) or
`Get-Command repo-context-hooks` (Windows) resolves to an older copy in a
different env — so hooks fire, but they execute pre-0.6.0 logic and your
new flags are unrecognized. Symptom variants: `--debug` is rejected,
`verify` exits "command not found", or `events.jsonl` records have a stale
schema.

### Reproduce

1. POSIX: `python -m venv .venv && .venv/bin/pip install repo-context-hooks`.
2. In a different shell (without the venv activated): `pip install --user repo-context-hooks==0.5.0`.
3. From the venv shell: `repo-context-hooks --version` (shows 0.6.0).
4. Open Claude Code from the OS shell with no venv: hooks run the 0.5.0 copy.

### Fix

Hooks execute via the agent's parent process, which usually does not inherit
your venv. The bundle scripts shipped under `repo_context_hooks/bundle/`
were hardened in 0.6.0 to gracefully degrade when imported from agent-home
(read-only fallbacks instead of raising). You have three options, in
preference order:

1. Install the package via `pipx` so it lives in an isolated env that is
   always on `$PATH`:

    ```bash
    pipx install repo-context-hooks
    repo-context-hooks install --platform claude
    ```

2. POSIX: install with `pip install --user` and ensure
   `$HOME/.local/bin` is on `PATH` for every shell that will launch the
   agent (`echo $PATH` in your `~/.bashrc` / `~/.zshrc`).
3. Windows: install with `pip install --user` and ensure
   `%APPDATA%\Python\Python<major><minor>\Scripts` is on `PATH` system-wide
   (System Properties → Environment Variables).

After whichever option you pick, re-run `repo-context-hooks install --platform claude --force`
so the hook command strings in `settings.json` point at the new binary path,
then `repo-context-hooks --version` from a fresh shell to confirm.

### Last verified

`0.6.0` — provenance: closed issue
[#32](https://github.com/narendranathe/repo-context-hooks/issues/32)
(script hardening: graceful degradation for agent-home execution).

---

## `verify` exits 1 — how to read the error log

### Symptom

`repo-context-hooks verify --platform claude` prints `Status: BROKEN` and
exits 1. The receipt names a `failure_reason`, but the user-facing message
is short — you want the full traceback.

### Reproduce

1. Install on a deliberately broken setup (e.g. delete `~/.claude/settings.json`
   after `install`).
2. Run `repo-context-hooks verify --platform claude` and observe
   `Status: BROKEN`, exit code 1.

### Fix

Re-run with `--debug` to write the full traceback to the rotating error log,
then read it:

```bash
repo-context-hooks --debug verify --platform claude

# POSIX
cat ~/.cache/repo-context-hooks/logs/errors.log

# Windows (PowerShell)
Get-Content "$env:LOCALAPPDATA\repo-context-hooks\logs\errors.log"
```

`doctor` also prints the active log path and the last error in its output:

```bash
repo-context-hooks doctor --platform claude
# ...
# Log path: /home/you/.cache/repo-context-hooks/logs/errors.log
# Last error: 2026-04-30T22:14:03 - verify - settings.json missing at /home/you/.claude/settings.json
```

The log directory is created lazily on the first ERROR record — a clean
install with no errors leaves zero filesystem trace. The log rotates at
1 MB with 5 backups, so even a chatty failure mode will not fill the disk.
On Linux distributions that confine `~/.cache` (SELinux, AppArmor, sandboxed
CI), set `REPO_CONTEXT_HOOKS_LOG_DIR` to a writable path; `doctor --json`
exposes `log_path` so you can confirm where it landed.

### Last verified

`0.6.0` — provenance: closed issues
[#74](https://github.com/narendranathe/repo-context-hooks/issues/74)
(`verify` command, `--dry-run`, version-migration tests) and
[#73](https://github.com/narendranathe/repo-context-hooks/issues/73)
(self-observability — error log, `--debug` flag, `doctor` surface).

---

## Related

- [Verify the install in under two seconds](index.md) — happy-path receipt
- [CLI Reference](cli-reference.md) — every flag and subcommand
- [Stability contract](stability.md) — what this page is allowed to break across releases
