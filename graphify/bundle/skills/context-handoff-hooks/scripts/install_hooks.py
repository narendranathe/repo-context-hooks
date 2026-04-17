from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if not text:
        return {}
    return json.loads(text)


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def install_scripts(skill_scripts_dir: Path, repo_scripts_dir: Path) -> None:
    repo_scripts_dir.mkdir(parents=True, exist_ok=True)
    for script_name in ("repo_specs_memory.py", "session_context.py"):
        src = skill_scripts_dir / script_name
        dst = repo_scripts_dir / script_name
        shutil.copy2(src, dst)


def build_hooks(repo_root: Path) -> dict:
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install context handoff hooks into a repository."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Target repository root (default: current directory)",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    claude_dir = repo_root / ".claude"
    scripts_dir = claude_dir / "scripts"
    settings_path = claude_dir / "settings.json"

    skill_scripts_dir = Path(__file__).resolve().parent
    install_scripts(skill_scripts_dir, scripts_dir)

    settings = load_json(settings_path)
    desired_hooks = build_hooks(repo_root)
    existing_hooks = settings.get("hooks", {})
    if not isinstance(existing_hooks, dict):
        existing_hooks = {}
    existing_hooks.update(desired_hooks)
    settings["hooks"] = existing_hooks
    save_json(settings_path, settings)

    print("Installed context handoff hooks.")
    print(f"- Repo: {repo_root}")
    print(f"- Settings: {settings_path}")
    print(f"- Scripts: {scripts_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
