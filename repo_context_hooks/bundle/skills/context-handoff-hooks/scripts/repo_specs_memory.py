from __future__ import annotations

import datetime as dt
import re
import subprocess
import sys
from pathlib import Path


EVENT = sys.argv[1] if len(sys.argv) > 1 else "session-start"

AUTO_BLOCK_START = "<!-- AUTO:REPO_CONTEXT_START -->"
AUTO_BLOCK_END = "<!-- AUTO:REPO_CONTEXT_END -->"
CHECKPOINTS_HEADING = "## Session Checkpoints"

SECTIONS: list[tuple[str, str]] = [
    (
        "Architecture and Design Constraints",
        "- Document hard constraints: security, latency, data boundaries, platform limits.\n"
        "- Explicitly call out non-goals so agents do not overbuild.",
    ),
    (
        "Built So Far",
        "- Summarize current shipped capabilities and important in-progress slices.\n"
        "- Prefer concrete status over aspiration.",
    ),
    (
        "Design Decisions",
        "- Record decisions with short rationale and trade-offs.\n"
        "- Keep this as the canonical ADR-lite trail for this repo.",
    ),
    (
        "What Worked",
        "- Capture patterns that produced reliable progress and quality.",
    ),
    (
        "What Failed or Was Reverted",
        "- Capture dead ends, regressions, and reversals so new agents avoid repeats.",
    ),
    (
        "Open Issues and Next Work",
        "- List open issues, next priority, and implementation order.\n"
        "- Keep this section actionable and current before compaction.",
    ),
    (
        "How To Work in This Repo",
        "- Read `README.md` first for user-facing behavior and contribution flow.\n"
        "- Read this `specs/README.md` before implementation.\n"
        "- Update this file before `compact` and at session end.",
    ),
]


def git_output(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def clean_line(line: str) -> str:
    line = re.sub(r"<[^>]+>", "", line)
    line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
    return line.strip()


def extract_repo_summary(repo_root: Path) -> str:
    readme = repo_root / "README.md"
    if not readme.exists():
        return (
            f"{repo_root.name} is an active project. Keep this repository's user-facing "
            "README and engineering memory synchronized."
        )

    lines: list[str] = []
    for raw in readme.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = clean_line(raw)
        if not line:
            continue
        if line.startswith(("#", "|", "```", ">", "!", "-", "*")):
            continue
        if len(line) < 25:
            continue
        lines.append(line)
        if len(lines) == 2:
            break

    if lines:
        return " ".join(lines)[:400].rstrip()
    return f"{repo_root.name} repository. Add a concise project summary to README.md."


def ensure_ubiquitous_language(repo_root: Path) -> Path:
    path = repo_root / "UBIQUITOUS_LANGUAGE.md"
    if path.exists():
        return path

    content = (
        "# Ubiquitous Language\n\n"
        "Keep project terms stable across code, specs, docs, and conversation.\n\n"
        "## Terms\n\n"
        "- Add domain terms as they are introduced.\n"
        "- Prefer one canonical term per concept.\n"
    )
    path.write_text(content, encoding="utf-8")
    return path


def ensure_section(content: str, title: str, body: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(title)}\s*$", re.MULTILINE)
    if pattern.search(content):
        return content

    suffix = f"\n## {title}\n\n{body}\n"
    if not content.endswith("\n"):
        content += "\n"
    return content + suffix


def build_auto_block(repo_root: Path, summary: str, ul_path: Path) -> str:
    return (
        f"{AUTO_BLOCK_START}\n"
        "### Canonical Context Sources\n\n"
        f"- User-facing overview: `README.md`\n"
        f"- Engineering memory: `specs/README.md`\n"
        f"- Glossary: `{ul_path.name}`\n"
        "- Source of truth: checked-in repo docs, not chat-only summaries\n\n"
        "### Repo Summary\n\n"
        f"- {summary}\n"
        f"{AUTO_BLOCK_END}"
    )


def ensure_specs_readme(repo_root: Path, summary: str, ul_path: Path) -> Path:
    specs_dir = repo_root / "specs"
    specs_dir.mkdir(exist_ok=True)
    path = specs_dir / "README.md"

    if not path.exists():
        path.write_text(
            "# Engineering Memory\n\n"
            "This file is the persistent project context for agents and maintainers.\n\n",
            encoding="utf-8",
        )

    content = path.read_text(encoding="utf-8", errors="ignore")

    auto_block = build_auto_block(repo_root, summary, ul_path)
    if AUTO_BLOCK_START in content and AUTO_BLOCK_END in content:
        pattern = re.compile(
            rf"{re.escape(AUTO_BLOCK_START)}.*?{re.escape(AUTO_BLOCK_END)}",
            re.DOTALL,
        )
        content = pattern.sub(auto_block, content)
    else:
        if not content.endswith("\n"):
            content += "\n"
        content += "\n## Repo Context Index\n\n" + auto_block + "\n"

    for title, body in SECTIONS:
        content = ensure_section(content, title, body)

    if CHECKPOINTS_HEADING not in content:
        if not content.endswith("\n"):
            content += "\n"
        content += f"\n{CHECKPOINTS_HEADING}\n\n"

    path.write_text(content, encoding="utf-8")
    return path


def append_checkpoint(specs_readme: Path) -> None:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    branch = git_output("branch", "--show-current") or "unknown"
    modified = git_output("status", "--short")

    changed_files: list[str] = []
    if modified:
        for line in modified.splitlines():
            cleaned = re.sub(r"^\s*[A-Z?!]{1,2}\s+", "", line).strip()
            if cleaned:
                changed_files.append(cleaned)

    file_list = ", ".join(changed_files[:10]) if changed_files else "none"
    entry = (
        f"\n### {now} - {EVENT}\n\n"
        f"- Branch: `{branch}`\n"
        f"- Working changes: {file_list}\n"
    )

    content = specs_readme.read_text(encoding="utf-8", errors="ignore")
    specs_readme.write_text(content + entry, encoding="utf-8")


def record_telemetry(repo_root: Path, specs_readme: Path, ul_path: Path) -> None:
    try:
        for parent in Path(__file__).resolve().parents:
            if (parent / "repo_context_hooks" / "telemetry.py").exists():
                sys.path.insert(0, str(parent))
                break

        from repo_context_hooks.telemetry import auto_commit_snapshot, is_sampled, record_event

        if not is_sampled(repo_root):
            return

        event_path = record_event(
            repo_root,
            EVENT,
            source="repo_specs_memory",
            details={"specs_readme": str(specs_readme), "glossary": str(ul_path)},
        )
        print(f"- Telemetry: `{event_path}`")

        if EVENT == "session-end":
            auto_commit_snapshot(repo_root)
            from repo_context_hooks.telemetry import clear_session_state
            clear_session_state(repo_root)
    except Exception:
        pass


def main() -> int:
    repo_root_raw = git_output("rev-parse", "--show-toplevel")
    if not repo_root_raw:
        return 0

    repo_root = Path(repo_root_raw)
    summary = extract_repo_summary(repo_root)
    ul_path = ensure_ubiquitous_language(repo_root)
    specs_readme = ensure_specs_readme(repo_root, summary, ul_path)

    print("### Repo Specs Memory")
    print(f"- Synced: `{specs_readme}`")
    print(f"- Glossary: `{ul_path}`")

    if EVENT in {"pre-compact", "post-compact", "session-end"}:
        append_checkpoint(specs_readme)
        print(f"- Appended checkpoint for `{EVENT}`")
    else:
        print(f"- Bootstrapped for `{EVENT}`")

    record_telemetry(repo_root, specs_readme, ul_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
