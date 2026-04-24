from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


EVENT = sys.argv[1] if len(sys.argv) > 1 else "session-start"


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


def section_body(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s+|\Z)",
        re.MULTILINE,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def extract_bullets(text: str, limit: int = 6) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            items.append(line[2:].strip())
        elif re.match(r"^\d+\.\s+", line):
            items.append(re.sub(r"^\d+\.\s+", "", line))
        if len(items) >= limit:
            break
    return [i for i in items if i]


def open_issues(repo_root: Path) -> list[dict[str, str]]:
    if shutil.which("gh") is None:
        return []

    remote = git_output("remote", "get-url", "origin")
    if "github.com" not in remote:
        return []

    try:
        result = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--state",
                "open",
                "--limit",
                "8",
                "--json",
                "number,title,url",
            ],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=8,
        )
        raw = json.loads(result.stdout or "[]")
        issues: list[dict[str, str]] = []
        for item in raw:
            issues.append(
                {
                    "number": str(item.get("number", "")),
                    "title": str(item.get("title", "")).strip(),
                    "url": str(item.get("url", "")).strip(),
                }
            )
        return issues
    except Exception:
        return []


def issue_refs_from_text(text: str) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(r"#(\d+)", text):
        ref = f"#{match.group(1)}"
        if ref not in seen:
            seen.add(ref)
            refs.append(ref)
    for match in re.finditer(r"https?://github\.com/[^\s)]+/issues/\d+", text):
        ref = match.group(0)
        if ref not in seen:
            seen.add(ref)
            refs.append(ref)
    return refs[:10]


def record_telemetry(
    repo_root: Path,
    next_items: list[str],
    method_items: list[str],
    issues: list[dict[str, str]],
) -> None:
    try:
        for parent in Path(__file__).resolve().parents:
            if (parent / "repo_context_hooks" / "telemetry.py").exists():
                sys.path.insert(0, str(parent))
                break

        from repo_context_hooks.telemetry import record_event

        record_event(
            repo_root,
            f"session-context-{EVENT}",
            source="session_context",
            details={
                "next_work_items": len(next_items),
                "workflow_items": len(method_items),
                "open_issues": len(issues),
            },
        )
    except Exception:
        pass


def main() -> int:
    repo_root_raw = git_output("rev-parse", "--show-toplevel")
    if not repo_root_raw:
        return 0

    repo_root = Path(repo_root_raw)
    repo_name = repo_root.name
    branch = git_output("branch", "--show-current") or "unknown"

    specs_path = repo_root / "specs" / "README.md"
    readme_path = repo_root / "README.md"
    claude_path = repo_root / "CLAUDE.md"

    specs_text = specs_path.read_text(encoding="utf-8", errors="ignore") if specs_path.exists() else ""
    next_work_section = section_body(specs_text, "Open Issues and Next Work")
    work_method_section = section_body(specs_text, "How To Work in This Repo")
    next_items = extract_bullets(next_work_section, limit=6)
    method_items = extract_bullets(work_method_section, limit=5)
    issues = open_issues(repo_root)

    print("## Project Context (auto-injected)")
    print("")
    print(f"- Event: `{EVENT}`")
    print(f"- Repo: `{repo_name}`")
    print(f"- Branch: `{branch}`")
    print("")

    print("### Canonical Docs")
    print(f"- User-facing README: `{readme_path}`" if readme_path.exists() else "- User-facing README: missing")
    print(f"- Engineering memory: `{specs_path}`" if specs_path.exists() else "- Engineering memory: missing")
    print(f"- Agent bootstrap: `{claude_path}`" if claude_path.exists() else "- Agent bootstrap: missing")
    print("")

    print("### What To Work On Next")
    if next_items:
        for item in next_items:
            print(f"- {item}")
    else:
        print("- Add actionable priorities under `## Open Issues and Next Work` in `specs/README.md`.")
    print("")

    print("### How To Work Here")
    if method_items:
        for item in method_items:
            print(f"- {item}")
    else:
        print("- Add workflow bullets under `## How To Work in This Repo` in `specs/README.md`.")
    print("")

    print("### Open GitHub Issues")
    if issues:
        for issue in issues:
            print(f"- #{issue['number']}: {issue['title']} ({issue['url']})")
    else:
        refs = issue_refs_from_text(specs_text)
        if refs:
            for ref in refs:
                print(f"- Referenced issue: {ref}")
        else:
            print("- Unable to fetch open issues (missing auth, non-GitHub remote, or no open issues).")
    print("")

    record_telemetry(repo_root, next_items, method_items, issues)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
