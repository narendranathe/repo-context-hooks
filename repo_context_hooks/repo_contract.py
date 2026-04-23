from __future__ import annotations

import re
from pathlib import Path

from .platforms.runtime import render_template


AUTO_BLOCK_START = "<!-- AUTO:REPO_CONTEXT_START -->"
AUTO_BLOCK_END = "<!-- AUTO:REPO_CONTEXT_END -->"
CHECKPOINTS_HEADING = "## Session Checkpoints"

README_TEMPLATE = """# Project Overview

Describe what this project does for users, how they can use it, and how they can contribute.
"""

GLOSSARY_TEMPLATE = """# Ubiquitous Language

Keep project terms stable across code, specs, docs, and conversation.

## Terms

- Add domain terms as they are introduced.
- Prefer one canonical term per concept.
"""

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


def ensure_section(content: str, title: str, body: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(title)}\s*$", re.MULTILINE)
    if pattern.search(content):
        return content

    suffix = f"\n## {title}\n\n{body}\n"
    if not content.endswith("\n"):
        content += "\n"
    return content + suffix


def build_auto_block(summary: str) -> str:
    return (
        f"{AUTO_BLOCK_START}\n"
        "### Canonical Context Sources\n\n"
        "- User-facing overview: `README.md`\n"
        "- Engineering memory: `specs/README.md`\n"
        "- Glossary: `UBIQUITOUS_LANGUAGE.md`\n"
        "- Source of truth: checked-in repo docs, not chat-only summaries\n\n"
        "### Repo Summary\n\n"
        f"- {summary}\n"
        f"{AUTO_BLOCK_END}"
    )


def ensure_readme(repo_root: Path, force: bool = False) -> str:
    path = repo_root / "README.md"
    if path.exists() and not force:
        return "skipped"
    path.write_text(README_TEMPLATE, encoding="utf-8")
    return "installed"


def ensure_ubiquitous_language(repo_root: Path, force: bool = False) -> str:
    path = repo_root / "UBIQUITOUS_LANGUAGE.md"
    if path.exists() and not force:
        return "skipped"
    path.write_text(GLOSSARY_TEMPLATE, encoding="utf-8")
    return "installed"


def ensure_agents(repo_root: Path, force: bool = False) -> str:
    path = repo_root / "AGENTS.md"
    if path.exists() and not force:
        return "skipped"
    path.write_text(render_template("AGENTS.md"), encoding="utf-8")
    return "installed"


def ensure_specs_readme(repo_root: Path, force: bool = False) -> str:
    specs_dir = repo_root / "specs"
    specs_dir.mkdir(exist_ok=True)
    path = specs_dir / "README.md"

    if force and path.exists():
        path.unlink()

    if not path.exists():
        path.write_text(
            "# Engineering Memory\n\n"
            "This file is the persistent project context for agents and maintainers.\n\n",
            encoding="utf-8",
        )
        created = True
    else:
        created = False

    summary = extract_repo_summary(repo_root)
    content = path.read_text(encoding="utf-8", errors="ignore")
    auto_block = build_auto_block(summary)

    if AUTO_BLOCK_START in content and AUTO_BLOCK_END in content:
        pattern = re.compile(
            rf"{re.escape(AUTO_BLOCK_START)}.*?{re.escape(AUTO_BLOCK_END)}",
            re.DOTALL,
        )
        updated = pattern.sub(auto_block, content)
    else:
        updated = content
        if not updated.endswith("\n"):
            updated += "\n"
        updated += "\n## Repo Context Index\n\n" + auto_block + "\n"

    for title, body in SECTIONS:
        updated = ensure_section(updated, title, body)

    if CHECKPOINTS_HEADING not in updated:
        if not updated.endswith("\n"):
            updated += "\n"
        updated += f"\n{CHECKPOINTS_HEADING}\n\n"

    if updated != content:
        path.write_text(updated, encoding="utf-8")
        if created:
            return "installed"
        return "updated"
    return "installed" if created else "skipped"


def init_repo_contract(repo_root: Path, force: bool = False) -> dict[str, str]:
    repo_root = repo_root.resolve()
    repo_root.mkdir(parents=True, exist_ok=True)

    return {
        "README.md": ensure_readme(repo_root, force=force),
        "specs/README.md": ensure_specs_readme(repo_root, force=force),
        "UBIQUITOUS_LANGUAGE.md": ensure_ubiquitous_language(repo_root, force=force),
        "AGENTS.md": ensure_agents(repo_root, force=force),
    }
