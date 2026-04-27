from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, Tuple


SKILL_PLATFORMS = ("claude",)


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
                    {"type": "command", "command": f"{prefix}python {repo_specs} session-end", "timeout": 10},
                ],
            }
        ],
    }


def install_global_hooks(
    agent_home: Path,
    skill_name: str = "context-handoff-hooks",
    telemetry: bool = True,
) -> Dict[str, str]:
    scripts_dir = agent_home / ".claude" / "skills" / skill_name / "scripts"
    settings_path = agent_home / ".claude" / "settings.json"
    settings = _load_json(settings_path)
    existing_hooks = settings.get("hooks", {})
    if not isinstance(existing_hooks, dict):
        existing_hooks = {}
    payload = global_hook_payload(scripts_dir, telemetry=telemetry)
    changed = False
    for event, new_groups in payload.items():
        existing_list = existing_hooks.get(event, [])
        if not isinstance(existing_list, list):
            existing_list = []
        for new_group in new_groups:
            new_cmds = {h.get("command", "") for h in new_group.get("hooks", [])}
            already_installed = any(
                h.get("command", "") in new_cmds
                for eg in existing_list
                if isinstance(eg, dict)
                for h in eg.get("hooks", [])
            )
            if not already_installed:
                existing_list.append(new_group)
                changed = True
        existing_hooks[event] = existing_list
    if not changed:
        return {"settings.json": "skipped"}
    settings["hooks"] = existing_hooks
    _save_json(settings_path, settings)
    return {"settings.json": "installed"}


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

    # --- Clean matching hook entries from settings.json ---
    settings_path = agent_home / ".claude" / "settings.json"
    settings = _load_json(settings_path)
    existing_hooks = settings.get("hooks", {})
    if not isinstance(existing_hooks, dict) or not existing_hooks:
        result["settings.json"] = "not found"
        return result

    # The marker string present in every command we installed.
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
                # Nothing removed from this group — keep it as-is.
                new_groups.append(group)
            elif filtered:
                # Some hooks removed, but the group still has entries.
                changed = True
                new_groups.append({**group, "hooks": filtered})
            else:
                # All hooks in this group were ours — drop the whole group.
                changed = True

        if new_groups:
            cleaned_hooks[event] = new_groups
        else:
            # The entire event list is now empty — drop the key.
            changed = True

    if changed:
        settings["hooks"] = cleaned_hooks
        _save_json(settings_path, settings)
        result["settings.json"] = "cleaned"
    else:
        result["settings.json"] = "no changes"

    return result


def posix_paths(paths: Iterable[Path]) -> Tuple[str, ...]:
    return tuple(path.as_posix() for path in paths)
