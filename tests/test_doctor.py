from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from repo_context_hooks.doctor import diagnose_all_platforms, diagnose_platform, diagnose_repo_contract
from repo_context_hooks.installer import install_platform
from repo_context_hooks.repo_contract import init_repo_contract

ROOT = Path(__file__).resolve().parents[1]


def _tmp_dir() -> Path:
    base = ROOT / ".tmp-tests"
    base.mkdir(exist_ok=True)
    path = base / uuid4().hex
    path.mkdir()
    return path


def _write_repo_contract(repo: Path) -> None:
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    specs_dir = repo / "specs"
    specs_dir.mkdir()
    (specs_dir / "README.md").write_text("# Specs\n", encoding="utf-8")


def test_repo_doctor_reports_missing_contract_files() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()

    report = diagnose_repo_contract(repo)

    assert report.ok is False
    assert "README.md" in report.missing
    assert "specs/README.md" in report.missing
    assert "UBIQUITOUS_LANGUAGE.md" in report.missing
    assert "MISSING" in report.render()


def test_repo_doctor_reports_initialized_contract() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo_contract(repo)

    report = diagnose_repo_contract(repo)

    assert report.ok is True
    assert "README.md" in report.present
    assert "specs/README.md" in report.present
    assert "UBIQUITOUS_LANGUAGE.md" in report.present
    assert "AGENTS.md" in report.present


def test_repo_doctor_rejects_placeholder_specs_readme() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo_contract(repo)
    (repo / "specs" / "README.md").write_text("placeholder\n", encoding="utf-8")

    report = diagnose_repo_contract(repo)

    assert report.ok is False
    assert "specs/README.md" in report.invalid
    assert "INVALID" in report.render()


def test_all_platforms_doctor_is_nonfatal_for_missing_platform_setup() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo_contract(repo)

    report = diagnose_all_platforms(repo, home=tmp_path / "home")

    assert report.ok is True
    rendered = report.render()
    assert "[OK] platform-readiness" in rendered
    assert "repo-contract\tok" in rendered
    assert "claude\tnative\tmissing" in rendered


def test_all_platforms_doctor_fails_on_invalid_platform_state() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract(repo)

    install_platform("replit", repo_root=repo, home=tmp_path / "home")
    (repo / "replit.md").write_text("placeholder\n", encoding="utf-8")

    report = diagnose_all_platforms(repo, home=tmp_path / "home")

    assert report.ok is False
    assert "replit\tpartial\tinvalid" in report.render()


def test_all_platforms_doctor_renders_compact_relative_details() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo_contract(repo)

    report = diagnose_all_platforms(repo, home=tmp_path / "home")

    rendered = report.render()
    assert "home:.claude/skills/context-handoff-hooks" in rendered
    assert "repo:.cursor/rules/repo-context-continuity.mdc" in rendered


def test_doctor_reports_missing_cursor_rule() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_repo_contract(repo)

    report = diagnose_platform("cursor", repo_root=repo, home=tmp_path / "home")

    assert report.ok is False
    assert any(
        item.endswith(".cursor/rules/repo-context-continuity.mdc")
        for item in report.missing
    )
    assert "MISSING" in report.render()


def test_doctor_reports_installed_codex_contract() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract(repo)

    home = tmp_path / "home"
    install_platform("codex", repo_root=repo, home=home)

    report = diagnose_platform("codex", repo_root=repo, home=home)

    assert report.ok is True
    assert any(item.endswith("AGENTS.md") for item in report.present)
    assert not any(".codex/skills" in item for item in report.present)


def test_doctor_rejects_placeholder_codex_agents_file() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract(repo)

    home = tmp_path / "home"
    install_platform("codex", repo_root=repo, home=home)
    (repo / "AGENTS.md").write_text("placeholder\n", encoding="utf-8")

    report = diagnose_platform("codex", repo_root=repo, home=home)

    assert report.ok is False
    assert any(item.endswith("AGENTS.md") for item in report.invalid)
    assert "INVALID" in report.render()


def test_doctor_does_not_require_codex_skill_directories() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract(repo)

    install_platform("codex", repo_root=repo, home=tmp_path / "home")

    report = diagnose_platform("codex", repo_root=repo, home=tmp_path / "home")

    assert report.ok is True
    assert not any(".codex/skills" in item for item in (*report.present, *report.missing, *report.invalid))


def test_doctor_reports_missing_replit_md() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_repo_contract(repo)

    report = diagnose_platform("replit", repo_root=repo, home=tmp_path / "home")

    assert report.ok is False
    assert any(item.endswith("replit.md") for item in report.missing)
    assert "MISSING" in report.render()


def test_doctor_reports_installed_replit_contract() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract(repo)

    install_platform("replit", repo_root=repo, home=tmp_path / "home")
    report = diagnose_platform("replit", repo_root=repo, home=tmp_path / "home")

    assert report.ok is True
    assert any(item.endswith("replit.md") for item in report.present)
    assert any(item.endswith("AGENTS.md") for item in report.present)


def test_doctor_rejects_placeholder_replit_md() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract(repo)

    install_platform("replit", repo_root=repo, home=tmp_path / "home")
    (repo / "replit.md").write_text("placeholder\n", encoding="utf-8")

    report = diagnose_platform("replit", repo_root=repo, home=tmp_path / "home")

    assert report.ok is False
    assert any(item.endswith("replit.md") for item in report.invalid)
    assert "INVALID" in report.render()


def test_doctor_reports_missing_windsurf_rule() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_repo_contract(repo)

    report = diagnose_platform("windsurf", repo_root=repo, home=tmp_path / "home")

    assert report.ok is False
    assert any(
        item.endswith(".windsurf/rules/repo-context-continuity.md")
        for item in report.missing
    )
    assert "MISSING" in report.render()


def test_doctor_reports_installed_windsurf_contract() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract(repo)

    install_platform("windsurf", repo_root=repo, home=tmp_path / "home")
    report = diagnose_platform("windsurf", repo_root=repo, home=tmp_path / "home")

    assert report.ok is True
    assert any(
        item.endswith(".windsurf/rules/repo-context-continuity.md")
        for item in report.present
    )
    assert any(item.endswith("AGENTS.md") for item in report.present)


def test_doctor_rejects_placeholder_windsurf_rule() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract(repo)

    install_platform("windsurf", repo_root=repo, home=tmp_path / "home")
    (repo / ".windsurf" / "rules" / "repo-context-continuity.md").write_text(
        "placeholder\n",
        encoding="utf-8",
    )

    report = diagnose_platform("windsurf", repo_root=repo, home=tmp_path / "home")

    assert report.ok is False
    assert any(
        item.endswith(".windsurf/rules/repo-context-continuity.md")
        for item in report.invalid
    )
    assert "INVALID" in report.render()


def test_doctor_reports_missing_lovable_exports() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_repo_contract(repo)

    report = diagnose_platform("lovable", repo_root=repo, home=tmp_path / "home")

    assert report.ok is False
    assert any(item.endswith(".lovable/project-knowledge.md") for item in report.missing)
    assert any(item.endswith(".lovable/workspace-knowledge.md") for item in report.missing)
    assert any("cannot be verified locally" in item.lower() for item in report.warnings)


def test_doctor_reports_installed_lovable_exports() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract(repo)

    install_platform("lovable", repo_root=repo, home=tmp_path / "home")
    report = diagnose_platform("lovable", repo_root=repo, home=tmp_path / "home")

    assert report.ok is True
    assert any(item.endswith(".lovable/project-knowledge.md") for item in report.present)
    assert any(item.endswith(".lovable/workspace-knowledge.md") for item in report.present)
    assert any(item.endswith("AGENTS.md") for item in report.present)


def test_doctor_rejects_placeholder_lovable_project_knowledge() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract(repo)

    install_platform("lovable", repo_root=repo, home=tmp_path / "home")
    (repo / ".lovable" / "project-knowledge.md").write_text(
        "placeholder\n",
        encoding="utf-8",
    )

    report = diagnose_platform("lovable", repo_root=repo, home=tmp_path / "home")

    assert report.ok is False
    assert any(item.endswith(".lovable/project-knowledge.md") for item in report.invalid)
    assert "INVALID" in report.render()


def test_doctor_reports_missing_openclaw_workspace_files() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_repo_contract(repo)

    report = diagnose_platform("openclaw", repo_root=repo, home=tmp_path / "home")

    assert report.ok is False
    assert any(item.endswith("SOUL.md") for item in report.missing)
    assert any(item.endswith("USER.md") for item in report.missing)
    assert any(item.endswith("TOOLS.md") for item in report.missing)
    assert any("active OpenClaw workspace" in item for item in report.warnings)


def test_doctor_reports_installed_openclaw_workspace_files() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract(repo)

    install_platform("openclaw", repo_root=repo, home=tmp_path / "home")
    report = diagnose_platform("openclaw", repo_root=repo, home=tmp_path / "home")

    assert report.ok is True
    assert any(item.endswith("SOUL.md") for item in report.present)
    assert any(item.endswith("USER.md") for item in report.present)
    assert any(item.endswith("TOOLS.md") for item in report.present)
    assert any(item.endswith("AGENTS.md") for item in report.present)


def test_doctor_rejects_placeholder_openclaw_soul_file() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract(repo)

    install_platform("openclaw", repo_root=repo, home=tmp_path / "home")
    (repo / "SOUL.md").write_text("placeholder\n", encoding="utf-8")

    report = diagnose_platform("openclaw", repo_root=repo, home=tmp_path / "home")

    assert report.ok is False
    assert any(item.endswith("SOUL.md") for item in report.invalid)
    assert "INVALID" in report.render()


def test_doctor_reports_missing_ollama_modelfile() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_repo_contract(repo)

    report = diagnose_platform("ollama", repo_root=repo, home=tmp_path / "home")

    assert report.ok is False
    assert any(item.endswith("Modelfile.repo-context") for item in report.missing)
    assert any("model runtime" in item.lower() for item in report.warnings)


def test_doctor_reports_installed_ollama_modelfile() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract(repo)

    install_platform("ollama", repo_root=repo, home=tmp_path / "home")
    report = diagnose_platform("ollama", repo_root=repo, home=tmp_path / "home")

    assert report.ok is True
    assert any(item.endswith("Modelfile.repo-context") for item in report.present)
    assert any(item.endswith("AGENTS.md") for item in report.present)


def test_doctor_rejects_placeholder_ollama_modelfile() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract(repo)

    install_platform("ollama", repo_root=repo, home=tmp_path / "home")
    (repo / "Modelfile.repo-context").write_text("placeholder\n", encoding="utf-8")

    report = diagnose_platform("ollama", repo_root=repo, home=tmp_path / "home")

    assert report.ok is False
    assert any(item.endswith("Modelfile.repo-context") for item in report.invalid)
    assert "INVALID" in report.render()


def test_doctor_reports_missing_kimi_agents_file() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_repo_contract(repo)

    report = diagnose_platform("kimi", repo_root=repo, home=tmp_path / "home")

    assert report.ok is False
    assert any(item.endswith("AGENTS.md") for item in report.missing)
    assert any("Kimi Code CLI" in item for item in report.warnings)


def test_doctor_reports_installed_kimi_agents_file() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract(repo)

    install_platform("kimi", repo_root=repo, home=tmp_path / "home")
    report = diagnose_platform("kimi", repo_root=repo, home=tmp_path / "home")

    assert report.ok is True
    assert any(item.endswith("AGENTS.md") for item in report.present)


def test_doctor_rejects_placeholder_kimi_agents_file() -> None:
    tmp_path = _tmp_dir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    _write_repo_contract(repo)

    install_platform("kimi", repo_root=repo, home=tmp_path / "home")
    (repo / "AGENTS.md").write_text("placeholder\n", encoding="utf-8")

    report = diagnose_platform("kimi", repo_root=repo, home=tmp_path / "home")

    assert report.ok is False
    assert any(item.endswith("AGENTS.md") for item in report.invalid)
    assert "INVALID" in report.render()
