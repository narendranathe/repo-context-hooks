from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Tuple


PLATFORMS = ("codex", "claude")


def bundle_root() -> Path:
    return Path(__file__).resolve().parent / "bundle"


def platform_skill_dir(platform: str, home: Path | None = None) -> Path:
    if platform not in PLATFORMS:
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


def install_skills(
    platform: str,
    force: bool = False,
    home: Path | None = None,
) -> Tuple[Path, Dict[str, str]]:
    src_skills = bundle_root() / "skills"
    target = platform_skill_dir(platform, home=home)
    target.mkdir(parents=True, exist_ok=True)

    status: Dict[str, str] = {}
    for skill in sorted([p for p in src_skills.iterdir() if p.is_dir()]):
        destination = target / skill.name
        status[skill.name] = copy_tree(skill, destination, force=force)
    return target, status


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


def hook_payload(repo_root: Path) -> dict:
    scripts = repo_root / ".claude" / "scripts"
    repo_specs = scripts / "repo_specs_memory.py"
    session_ctx = scripts / "session_context.py"
    return {
        "SessionStart": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": f'python "{repo_specs}" session-start',
                        "timeout": 20,
                    },
                    {
                        "type": "command",
                        "command": f'python "{session_ctx}" session-start',
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
                        "command": f'python "{repo_specs}" pre-compact',
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
                        "command": f'python "{repo_specs}" post-compact',
                        "timeout": 20,
                    },
                    {
                        "type": "command",
                        "command": f'python "{session_ctx}" post-compact',
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
                        "command": f'python "{repo_specs}" session-end',
                        "timeout": 10,
                    }
                ],
            }
        ],
    }


def install_repo_hooks(repo_root: Path) -> Dict[str, str]:
    repo_root = repo_root.resolve()
    scripts_dir = repo_root / ".claude" / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    src_scripts = bundle_root() / "scripts"
    copied: Dict[str, str] = {}
    for script_name in ("repo_specs_memory.py", "session_context.py"):
        src = src_scripts / script_name
        dst = scripts_dir / script_name
        shutil.copy2(src, dst)
        copied[script_name] = str(dst)

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

    copied["settings.json"] = str(settings_path)
    return copied
