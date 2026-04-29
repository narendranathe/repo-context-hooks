# Deprecation Policy

This document explains how we remove things from the [stability contract](stability.md) without breaking downstream users.

## The rule

**A public surface symbol must be marked deprecated for at least one full MINOR release before it is removed.**

Concretely, to remove a public symbol in version `1.N`:

1. In version `1.N-1` (or earlier), land a `### Deprecated` entry in [`CHANGELOG.md`](https://github.com/narendranathe/repo-context-hooks/blob/main/CHANGELOG.md) and emit a `DeprecationWarning` from the runtime when the symbol is touched.
2. In version `1.N`, land a `### Removed` entry referencing the prior `### Deprecated` entry, drop the symbol from `repo_context_hooks/__init__.py`, the CLI parser, or the env-var reader, and update `tests/contract/public_surface.json` in the same PR.

A removal in `1.N` that was not deprecated in some earlier `1.x` is **not allowed**. The CI gate (`scripts/check_public_surface.py --verify-removals`) blocks the PR.

A MAJOR bump (`1.x → 2.0`) may remove deprecated symbols in bulk, but may not introduce *new* removals — every removal in `2.0` must trace back to a `### Deprecated` entry in some `1.x`.

## CHANGELOG flow

Every deprecation lives in `CHANGELOG.md` under the [Unreleased] / target-version block, in this shape:

```markdown
### Deprecated

- `<symbol>`: deprecated in <version>, scheduled for removal in <version>.
  Migration: <one-line action the user should take>.
  See <link to issue or doc>.
```

And later, when removed:

```markdown
### Removed

- `<symbol>`: removed in <version>; was deprecated in <version> (see CHANGELOG entry above).
```

The CI gate parses these lines, so the bullet text must contain the symbol name in backticks. Anything else is freeform.

## Per-context guidance

The mechanism for emitting a `DeprecationWarning` differs depending on what is being deprecated.

### Python imports (`__all__` removal)

Use `warnings.warn(...)` at module import time:

```python
import warnings
warnings.warn(
    "`repo_context_hooks.foo` is deprecated and will be removed in 1.4. "
    "Use `repo_context_hooks.bar` instead.",
    DeprecationWarning,
    stacklevel=2,
)
```

`stacklevel=2` attributes the warning to the caller's frame, not the warning site.

### CLI flag removal

The deprecated flag stays accepted by the parser. On invocation it emits a warning to stderr (not via Python `warnings`, because most CLI users don't enable `-W default`):

```python
parser.add_argument(
    "--old-flag",
    action="store_true",
    help="(deprecated, use --new-flag — will be removed in 1.4)",
)
# in the dispatch:
if args.old_flag:
    print(
        "warning: --old-flag is deprecated and will be removed in 1.4; use --new-flag",
        file=sys.stderr,
    )
```

The help text also marks the flag deprecated, which keeps `--help` users informed.

### CLI subcommand removal

Same shape as a flag: the subcommand stays registered, runs its old behaviour, and prints a deprecation line to stderr before doing the work. The CHANGELOG `### Deprecated` bullet names the subcommand.

### Environment variable removal

The reader continues to honour the old name for one full MINOR. If both old and new are set, prefer the new one and warn that the old one was ignored. If only the old one is set, honour it and warn that it is deprecated.

### `--platform` choice removal

`argparse`'s default `choices=` validation will hard-reject a removed value with `SystemExit(2)`, which gives the user no migration path. The deprecation must use a custom `argparse.Action` that:

1. Accepts the deprecated value.
2. Emits a `DeprecationWarning` with the replacement (or `none`).
3. Maps it to the replacement value internally so the rest of the code path is unchanged.

Once the cycle expires, the value is removed from both the custom action and `tests/contract/public_surface.json::platform_choices`.

## Migration paths are mandatory

Every `### Deprecated` bullet **must** include a one-line migration path. "Use `X` instead", or "remove the call site", or "set `Y=z` in your config". A deprecation without a migration path is a slow-rolling break and gets rejected in review.

## What is *not* covered

This policy applies only to surfaces listed under [Stability — Stable surfaces](stability.md#stable-surfaces). Internal surfaces (everything else) may change in any release, including patch. There is no obligation to deprecate an internal symbol — the warning we owe users is the [stability doc](stability.md) itself, which says these surfaces are not promised.

If you discover that you are relying on an internal surface, the right step is to open an issue requesting promotion. We will weigh the use case and either promote it (which lands as a new `### Added` entry on the public surface) or document a workaround.

## SemVer alignment

We follow [SemVer 2.0.0](https://semver.org/) starting at `1.0.0`. In short:

- **PATCH** (`1.0.x`) — backwards-compatible bug fixes only. No surface change.
- **MINOR** (`1.x.0`) — backwards-compatible additions and `### Deprecated` markers. No removals from the public surface.
- **MAJOR** (`x.0.0`) — may remove anything that was deprecated in a prior MINOR. May not introduce new, non-deprecated removals.

This is the deal. The CI gate is the enforcement. If the gate fails, the contract caught a bug — fix the contract path, don't bypass the gate.
