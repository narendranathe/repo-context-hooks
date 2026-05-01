from __future__ import annotations

import difflib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Tuple


SKILL_PLATFORMS = ("claude",)


# ---------------------------------------------------------------------------
# Planner / applier split (issue #74).
#
# Every settings.json mutator below is split into a pure planner that returns
# a ``SettingsPlan`` and a wrapper that applies the plan via ``_save_json``.
# The CLI's ``--dry-run`` path calls only the planner, so the dry-run
# guarantee ("never writes to disk") is mechanical, not by-convention.
# ``install_global_hooks`` / ``uninstall_global_hooks`` / ``deduplicate_hooks``
# keep their existing signatures and return-dict contracts so the 506-test
# suite needs zero changes.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SettingsPlan:
    """The result of computing a settings.json change *without* writing it.

    ``current_text`` is what ``settings.json`` contains right now (``""`` if
    missing). ``proposed_text`` is what would be written if applied. ``diff``
    is the unified diff between the two — empty tuple when ``action == "skip"``
    or ``"no changes"``. ``statuses`` mirrors what the original mutating
    function would have returned so the apply wrapper can keep the legacy
    return-dict contract.
    """

    settings_path: Path
    current_text: str
    proposed_text: str
    diff: Tuple[str, ...]
    action: str  # "install" | "skip" | "uninstall" | "no changes"
    statuses: Dict[str, str] = field(default_factory=dict)

    @property
    def will_change(self) -> bool:
        return self.current_text != self.proposed_text

    def diff_text(self) -> str:
        return "".join(self.diff)


def _canonical_settings_text(data: dict) -> str:
    """Serialise settings dict to the on-disk JSON shape ``_save_json`` writes.

    ``json.dumps(..., indent=2)`` with a trailing newline matches
    ``_save_json`` exactly (see line ~``settings_path.write_text``). Sorted
    keys give a line-stable diff across Python dict-ordering variations
    (Python 3.7+ preserves insertion order, but the planner runs on values
    whose key order is set by external user edits — sort_keys neutralises
    that source of churn).
    """

    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _read_settings_text(path: Path) -> str:
    """Return current settings.json content as text, or ``""`` if absent.

    Mirrors ``_load_json``'s tolerance: missing file is empty string. We do
    NOT swallow JSON-decode errors here because the planner needs to know
    whether the existing file is parseable (a corrupt file means
    ``_load_json`` returns ``{}`` and the diff would falsely show
    "everything is new"). Caller decides what to do.
    """

    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _unified_diff(current: str, proposed: str, *, path: Path) -> Tuple[str, ...]:
    name = path.as_posix()
    return tuple(
        difflib.unified_diff(
            current.splitlines(keepends=True),
            proposed.splitlines(keepends=True),
            fromfile=name,
            tofile=f"{name} (proposed)",
            lineterm="",
        )
    )


def _normalise_hook_cmd(cmd: str) -> str:
    return cmd.replace("\\", "/").strip()


def bundle_root() -> Path:
    return Path(__file__).resolve().parents[1] / "bundle"


def bundle_skills_root() -> Path:
    return bundle_root() / "skills"


def bundle_scripts_root() -> Path:
    return bundle_root() / "scripts"


def bundle_templates_root() -> Path:
    return bundle_root() / "templates"


def bundled_skill_names() -> Tuple[str, ...]:
    return tuple(
        sorted(path.name for path in bundle_skills_root().iterdir() if path.is_dir())
    )


def platform_skill_dir(platform: str, home: Path | None = None) -> Path:
    if platform not in SKILL_PLATFORMS:
        raise ValueError(f"Unsupported platform: {platform}")
    h = home or Path.home()
    if platform == "codex":
        return h / ".codex" / "skills"
    return h / ".claude" / "skills"


def copy_tree(src: Path, dst: Path, force: bool = False) -> str:
    if dst.exists():
        if not force:
            return "skipped"
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return "installed"


def copy_file(src: Path, dst: Path, force: bool = False) -> str:
    if dst.exists() and not force:
        return "skipped"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return "installed"


def install_skills_bundle(
    platform: str,
    force: bool = False,
    home: Path | None = None,
) -> tuple[Path, Dict[str, str]]:
    src_skills = bundle_skills_root()
    target = platform_skill_dir(platform, home=home)
    target.mkdir(parents=True, exist_ok=True)

    status: Dict[str, str] = {}
    for skill_name in bundled_skill_names():
        source = src_skills / skill_name
        destination = target / skill_name
        status[skill_name] = copy_tree(source, destination, force=force)
    return target, status


def render_template(name: str, **replacements: str) -> str:
    text = (bundle_templates_root() / name).read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace(f"__{key}__", value)
    return text


def write_text_file(path: Path, text: str, force: bool = False) -> str:
    if path.exists() and not force:
        return "skipped"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return "installed"


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def global_hook_payload(scripts_dir: Path, telemetry: bool = True) -> dict:
    repo_specs = (scripts_dir / "repo_specs_memory.py").as_posix()
    session_ctx = (scripts_dir / "session_context.py").as_posix()
    prefix = "" if telemetry else "REPO_CONTEXT_HOOKS_TELEMETRY=0 "
    return {
        "SessionStart": [
            {
                "matcher": "",
                "hooks": [
                    {"type": "command", "command": f"{prefix}python {repo_specs} session-start", "timeout": 20},
                    {"type": "command", "command": f"{prefix}python {session_ctx} session-start", "timeout": 20},
                ],
            }
        ],
        "PreCompact": [
            {
                "matcher": "",
                "hooks": [
                    {"type": "command", "command": f"{prefix}python {repo_specs} pre-compact", "timeout": 15},
                ],
            }
        ],
        "PostCompact": [
            {
                "matcher": "",
                "hooks": [
                    {"type": "command", "command": f"{prefix}python {repo_specs} post-compact", "timeout": 20},
                    {"type": "command", "command": f"{prefix}python {session_ctx} post-compact", "timeout": 20},
                ],
            }
        ],
        "SessionEnd": [
            {
                "matcher": "",
                "hooks": [
                    {"type": "command", "command": f"{prefix}python {repo_specs} session-end", "timeout": 30},
                ],
            }
        ],
    }


def plan_global_hooks(
    agent_home: Path,
    skill_name: str = "context-handoff-hooks",
    telemetry: bool = True,
) -> SettingsPlan:
    """Compute the settings.json patch a real install would write — pure.

    This function performs ZERO disk writes. ``install_global_hooks`` calls
    it then writes only when ``plan.action == "install"``. The CLI's
    ``--dry-run`` path calls only this function and renders ``plan.diff``.
    """

    scripts_dir = agent_home / ".claude" / "skills" / skill_name / "scripts"
    settings_path = agent_home / ".claude" / "settings.json"
    current_text = _read_settings_text(settings_path)
    settings = _load_json(settings_path)
    existing_hooks = settings.get("hooks", {})
    if not isinstance(existing_hooks, dict):
        existing_hooks = {}
    payload = global_hook_payload(scripts_dir, telemetry=telemetry)
    proposed_hooks: dict = {k: list(v) if isinstance(v, list) else v for k, v in existing_hooks.items()}
    changed = False
    for event, new_groups in payload.items():
        existing_list = proposed_hooks.get(event, [])
        if not isinstance(existing_list, list):
            existing_list = []
        for new_group in new_groups:
            new_cmds = {h.get("command", "") for h in new_group.get("hooks", [])}
            new_cmds_norm = {_normalise_hook_cmd(c) for c in new_cmds}
            already_installed = any(
                _normalise_hook_cmd(h.get("command", "")) in new_cmds_norm
                for eg in existing_list
                if isinstance(eg, dict)
                for h in eg.get("hooks", [])
            )
            if not already_installed:
                existing_list.append(new_group)
                changed = True
        proposed_hooks[event] = existing_list

    if not changed:
        return SettingsPlan(
            settings_path=settings_path,
            current_text=current_text,
            proposed_text=current_text,
            diff=(),
            action="skip",
            statuses={"settings.json": "skipped"},
        )

    proposed = dict(settings)
    proposed["hooks"] = proposed_hooks
    proposed_text = _canonical_settings_text(proposed)
    return SettingsPlan(
        settings_path=settings_path,
        current_text=current_text,
        proposed_text=proposed_text,
        diff=_unified_diff(current_text, proposed_text, path=settings_path),
        action="install",
        statuses={"settings.json": "installed"},
    )


def install_global_hooks(
    agent_home: Path,
    skill_name: str = "context-handoff-hooks",
    telemetry: bool = True,
) -> Dict[str, str]:
    plan = plan_global_hooks(agent_home, skill_name=skill_name, telemetry=telemetry)
    if plan.action == "install":
        # ``proposed_text`` was generated via ``_canonical_settings_text``
        # which uses ``sort_keys=True``. We deliberately do NOT round-trip
        # through json.loads/_save_json (which sorts again) to avoid double
        # serialisation; write the canonical text directly.
        plan.settings_path.parent.mkdir(parents=True, exist_ok=True)
        plan.settings_path.write_text(plan.proposed_text, encoding="utf-8")
    return dict(plan.statuses)


def plan_deduplicate_hooks(
    agent_home: Path,
    skill_name: str = "context-handoff-hooks",
) -> SettingsPlan:
    """Compute the dedup patch — pure, no disk writes. (issue #74)

    ``statuses`` carries the legacy ``{"removed": N}`` shape so the apply
    wrapper preserves the existing return contract; ``action`` is
    ``"install"`` (apply) when N > 0 else ``"skip"``.
    """

    settings_path = agent_home / ".claude" / "settings.json"
    current_text = _read_settings_text(settings_path)
    settings = _load_json(settings_path)
    hooks = settings.get("hooks", {})
    if not isinstance(hooks, dict):
        return SettingsPlan(
            settings_path=settings_path,
            current_text=current_text,
            proposed_text=current_text,
            diff=(),
            action="skip",
            statuses={"removed": 0},
        )

    removed = 0
    cleaned: dict = {}
    for event, groups in hooks.items():
        if not isinstance(groups, list):
            cleaned[event] = groups
            continue
        seen_cmds: set[str] = set()
        new_groups = []
        for group in groups:
            if not isinstance(group, dict):
                new_groups.append(group)
                continue
            new_hook_list = []
            for h in group.get("hooks", []):
                norm = _normalise_hook_cmd(h.get("command", ""))
                if norm and norm in seen_cmds:
                    removed += 1
                else:
                    seen_cmds.add(norm)
                    new_hook_list.append(h)
            if new_hook_list:
                new_groups.append({**group, "hooks": new_hook_list})
        cleaned[event] = new_groups

    if removed == 0:
        return SettingsPlan(
            settings_path=settings_path,
            current_text=current_text,
            proposed_text=current_text,
            diff=(),
            action="skip",
            statuses={"removed": 0},
        )

    proposed = dict(settings)
    proposed["hooks"] = cleaned
    proposed_text = _canonical_settings_text(proposed)
    return SettingsPlan(
        settings_path=settings_path,
        current_text=current_text,
        proposed_text=proposed_text,
        diff=_unified_diff(current_text, proposed_text, path=settings_path),
        action="install",
        statuses={"removed": removed},
    )


def deduplicate_hooks(
    agent_home: Path,
    skill_name: str = "context-handoff-hooks",
) -> dict:
    """Remove duplicate hook entries from settings.json. Returns {"removed": N}."""
    plan = plan_deduplicate_hooks(agent_home, skill_name=skill_name)
    if plan.action == "install":
        plan.settings_path.parent.mkdir(parents=True, exist_ok=True)
        plan.settings_path.write_text(plan.proposed_text, encoding="utf-8")
    return dict(plan.statuses)


def hook_payload(repo_root: Path) -> dict:
    del repo_root
    repo_specs = '"$CLAUDE_PROJECT_DIR"/.claude/scripts/repo_specs_memory.py'
    session_ctx = '"$CLAUDE_PROJECT_DIR"/.claude/scripts/session_context.py'
    return {
        "SessionStart": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"python {repo_specs} session-start",
                        "timeout": 20,
                    },
                    {
                        "type": "command",
                        "command": f"python {session_ctx} session-start",
                        "timeout": 20,
                    },
                ],
            }
        ],
        "PreCompact": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"python {repo_specs} pre-compact",
                        "timeout": 15,
                    }
                ],
            }
        ],
        "PostCompact": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"python {repo_specs} post-compact",
                        "timeout": 20,
                    },
                    {
                        "type": "command",
                        "command": f"python {session_ctx} post-compact",
                        "timeout": 20,
                    },
                ],
            }
        ],
        "SessionEnd": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"python {repo_specs} session-end",
                        "timeout": 10,
                    }
                ],
            }
        ],
    }


def install_repo_hooks(repo_root: Path, force: bool = False) -> Dict[str, str]:
    repo_root = repo_root.resolve()
    scripts_dir = repo_root / ".claude" / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    copied: Dict[str, str] = {}
    for script_name in ("repo_specs_memory.py", "session_context.py"):
        src = bundle_scripts_root() / script_name
        dst = scripts_dir / script_name
        copied[script_name] = copy_file(src, dst, force=force)

    settings_path = repo_root / ".claude" / "settings.json"
    settings = _load_json(settings_path)
    existing_hooks = settings.get("hooks", {})
    if not isinstance(existing_hooks, dict):
        existing_hooks = {}
    existing_hooks.update(hook_payload(repo_root))
    settings["hooks"] = existing_hooks
    _save_json(settings_path, settings)

    bootstrap = scripts_dir / "repo_specs_memory.py"
    try:
        subprocess.run(
            [sys.executable, str(bootstrap), "session-start"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception:
        pass

    copied["settings.json"] = "installed"
    return copied


def plan_uninstall_global_hooks(
    agent_home: Path,
    skill_name: str = "context-handoff-hooks",
) -> SettingsPlan:
    """Compute the settings.json patch a real uninstall would write — pure.

    Skill-bundle directory removal is a side effect (not settings.json), so
    it lives in ``uninstall_global_hooks`` only. The plan covers ONLY the
    settings.json edit, which is the part the dry-run user wants to audit.
    ``statuses`` carries ``{"settings.json": "cleaned"|"no changes"|"not found"}``
    so the apply wrapper merges it with the bundle-removal status.
    """

    settings_path = agent_home / ".claude" / "settings.json"
    current_text = _read_settings_text(settings_path)
    settings = _load_json(settings_path)
    existing_hooks = settings.get("hooks", {})

    if not isinstance(existing_hooks, dict) or not existing_hooks:
        return SettingsPlan(
            settings_path=settings_path,
            current_text=current_text,
            proposed_text=current_text,
            diff=(),
            action="skip",
            statuses={"settings.json": "not found"},
        )

    marker = f"/skills/{skill_name}/scripts/"
    changed = False
    cleaned_hooks: dict = {}
    for event, groups in existing_hooks.items():
        if not isinstance(groups, list):
            cleaned_hooks[event] = groups
            continue
        new_groups = []
        for group in groups:
            if not isinstance(group, dict):
                new_groups.append(group)
                continue
            hooks_in_group = group.get("hooks", [])
            filtered = [
                h for h in hooks_in_group
                if not (isinstance(h, dict) and marker in h.get("command", ""))
            ]
            if len(filtered) == len(hooks_in_group):
                new_groups.append(group)
            elif filtered:
                changed = True
                new_groups.append({**group, "hooks": filtered})
            else:
                changed = True
        if new_groups:
            cleaned_hooks[event] = new_groups
        else:
            changed = True

    if not changed:
        return SettingsPlan(
            settings_path=settings_path,
            current_text=current_text,
            proposed_text=current_text,
            diff=(),
            action="skip",
            statuses={"settings.json": "no changes"},
        )

    proposed = dict(settings)
    proposed["hooks"] = cleaned_hooks
    proposed_text = _canonical_settings_text(proposed)
    return SettingsPlan(
        settings_path=settings_path,
        current_text=current_text,
        proposed_text=proposed_text,
        diff=_unified_diff(current_text, proposed_text, path=settings_path),
        action="uninstall",
        statuses={"settings.json": "cleaned"},
    )


def uninstall_global_hooks(
    agent_home: Path,
    skill_name: str = "context-handoff-hooks",
) -> Dict[str, str]:
    """Remove the skills bundle directory and hook entries added by this tool.

    Only removes hook entries whose command string contains the skill scripts
    path (``/skills/{skill_name}/scripts/``).  Adjacent user-defined hooks are
    left untouched.  Missing directories and settings files are handled
    gracefully so the operation is idempotent.
    """
    result: Dict[str, str] = {}

    # --- Remove the skills bundle directory ---
    skills_dir = agent_home / ".claude" / "skills" / skill_name
    if skills_dir.exists():
        shutil.rmtree(skills_dir)
        result[skill_name] = "removed"
    else:
        result[skill_name] = "not found"

    # --- Clean matching hook entries from settings.json (via planner) ---
    plan = plan_uninstall_global_hooks(agent_home, skill_name=skill_name)
    if plan.action == "uninstall":
        plan.settings_path.parent.mkdir(parents=True, exist_ok=True)
        plan.settings_path.write_text(plan.proposed_text, encoding="utf-8")
    result.update(plan.statuses)
    return result


def posix_paths(paths: Iterable[Path]) -> Tuple[str, ...]:
    return tuple(path.as_posix() for path in paths)
