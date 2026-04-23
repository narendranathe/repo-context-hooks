# Platform Playbooks

These playbooks explain what to do after `repo-context-hooks install --platform <name>` for each partial platform.

Use them as the operating guide for platforms that do not expose Claude-style lifecycle hooks. The core rule is simple: keep `README.md`, `specs/README.md`, and `AGENTS.md` as the repo contract, then map that contract into the strongest real surface each platform exposes.

Every partial platform has the same claim boundary:

- no native lifecycle hooks
- no compact automation
- no Claude-style hook parity
- no claim that hosted or runtime state is verified unless `doctor` can check it locally

## Replit

Follow-up issue: https://github.com/narendranathe/repo-context-hooks/issues/2

### What gets installed

- `AGENTS.md`
- `replit.md`

### What remains manual

- Start or resume the Replit Agent from the repo root.
- Tell the agent to read `replit.md`, `AGENTS.md`, `README.md`, and `specs/README.md` before making changes.
- Write durable decisions or next work back into repo docs before ending the session.

### What `doctor` verifies

- `AGENTS.md` exists and points to the repo contract.
- `replit.md` exists and references `README.md`, `specs/README.md`, and `AGENTS.md`.

### What not to claim

- Do not claim native lifecycle hooks.
- Do not claim compact automation.
- Do not claim that Replit interruption or resume behavior is controlled by this package.

## Windsurf

Follow-up issue: https://github.com/narendranathe/repo-context-hooks/issues/8

### What gets installed

- `AGENTS.md`
- `.windsurf/rules/repo-context-continuity.md`

### What remains manual

- Keep root `AGENTS.md` as the short repo operating contract.
- Use `.windsurf/rules/repo-context-continuity.md` as the always-on Cascade rule that points back to the repo contract.
- Add project-specific Windsurf rules separately if the repo needs them, but do not duplicate the whole contract.

### What `doctor` verifies

- `AGENTS.md` exists and points to the repo contract.
- `.windsurf/rules/repo-context-continuity.md` exists and references `README.md`, `specs/README.md`, and `AGENTS.md`.

### What not to claim

- Do not claim native lifecycle hooks.
- Do not claim compact automation.
- Do not claim that Windsurf rules are equivalent to Claude hooks.

## Lovable

Follow-up issue: https://github.com/narendranathe/repo-context-hooks/issues/3

### What gets installed

- `AGENTS.md`
- `.lovable/project-knowledge.md`
- `.lovable/workspace-knowledge.md`

### What remains manual

- Connect Lovable to the synced GitHub repository.
- Paste `.lovable/project-knowledge.md` into Lovable Project Knowledge.
- Paste `.lovable/workspace-knowledge.md` into Lovable Workspace Knowledge if shared rules are useful.
- Re-paste the hosted knowledge fields whenever the repo-owned exports change.

### What `doctor` verifies

- The local repo-owned export files exist.
- The export files reference the repo contract.

### What not to claim

- Do not claim native lifecycle hooks.
- Do not claim compact automation.
- Do not claim local verification of Lovable's hosted Project Knowledge or Workspace Knowledge state.

## OpenClaw

Follow-up issue: https://github.com/narendranathe/repo-context-hooks/issues/5

### What gets installed

- `AGENTS.md`
- `SOUL.md`
- `USER.md`
- `TOOLS.md`

### What remains manual

- Point OpenClaw `agents.defaults.workspace` to the repo root, or copy the generated files into the active OpenClaw workspace.
- Keep secrets and private memory out of public repos.
- Run OpenClaw setup or doctor after changing workspace configuration.

### What `doctor` verifies

- The generated workspace files exist locally.
- The workspace files reference `README.md`, `specs/README.md`, `AGENTS.md`, and the repo as the continuity source of truth.

### What not to claim

- Do not claim native lifecycle hooks.
- Do not claim compact automation.
- Do not claim that local `doctor` verifies the active OpenClaw workspace path.

## Ollama

Follow-up issue: https://github.com/narendranathe/repo-context-hooks/issues/4

### What gets installed

- `AGENTS.md`
- `Modelfile.repo-context`

### What remains manual

- Edit the `FROM` line in `Modelfile.repo-context` if you prefer a different local model.
- Run `ollama create repo-context-helper -f Modelfile.repo-context`.
- Use the created model through an agent wrapper that can read repo files, or paste `README.md`, `specs/README.md`, and `AGENTS.md` when using direct `ollama run`.

### What `doctor` verifies

- `Modelfile.repo-context` exists.
- The Modelfile includes `FROM`, `SYSTEM`, `README.md`, `specs/README.md`, `AGENTS.md`, and the repo continuity instruction.

### What not to claim

- Do not claim native lifecycle hooks.
- Do not claim compact automation.
- Do not claim Ollama reads repo files automatically.

Ollama is a model runtime. It does not read repo files automatically. `repo-context-hooks` gives it a repeatable repo-context prompt, but an agent wrapper or user prompt must still provide the actual file contents.

## Kimi

Follow-up issue: https://github.com/narendranathe/repo-context-hooks/issues/6

### What gets installed

- `AGENTS.md`

### What remains manual

- Run or review Kimi Code CLI `/init` output.
- Merge any generated Kimi guidance with the repo-owned `AGENTS.md` contract.
- Keep Kimi-specific rules out of public claims until a stable Kimi rules path is documented.

### What `doctor` verifies

- `AGENTS.md` exists and points to `README.md`, `specs/README.md`, and the repo as the continuity source of truth.

### What not to claim

- Do not claim native lifecycle hooks.
- Do not claim compact automation.
- Do not claim generic Kimi API setup.

This support is for Kimi Code CLI project context, not generic Kimi API setup.
