import json
from pathlib import Path

import pytest

from dh_skills.catalog import BASE_SKILLS, EXCLUDED_SKILLS
from dh_skills.installer import DEPLOY_STATE_FILENAME, install_content
from dh_skills.cli import main
from dh_skills.paths import Targets


def make_fixture(tmp_path: Path) -> tuple[Path, Targets]:
    content = tmp_path / "content"
    skills = content / "skills"
    agents = content / "agents"
    prompts = content / "prompts"
    for directory in (skills, agents, prompts):
        directory.mkdir(parents=True)
    for name in (*BASE_SKILLS, "dh-extra", next(iter(EXCLUDED_SKILLS))):
        skill = skills / name
        skill.mkdir()
        (skill / "SKILL.md").write_text(name, encoding="utf-8")
    (agents / "planner.agent.md").write_text("planner", encoding="utf-8")
    (prompts / "ship.prompt.md").write_text("ship", encoding="utf-8")

    targets = Targets(
        skills=tmp_path / "installed-skills",
        agents=tmp_path / "installed-agents",
        prompts=tmp_path / "installed-prompts",
    )
    return content, targets


def test_subset_install_always_includes_base_skills_and_writes_cache(tmp_path):
    content, targets = make_fixture(tmp_path)

    result = install_content(content, targets, names=["dh-extra"], ref="main", commit="abc123")

    assert result.installed == len(BASE_SKILLS) + 1
    assert all((targets.skills / name).is_dir() for name in (*BASE_SKILLS, "dh-extra"))
    state = json.loads((targets.skills / DEPLOY_STATE_FILENAME).read_text(encoding="utf-8"))
    assert state["ref"] == "main"
    assert state["commit"] == "abc123"
    assert state["deployed_at"]


def test_unknown_skill_fails_without_writing(tmp_path, capsys):
    content, targets = make_fixture(tmp_path)

    result = install_content(content, targets, names=["dh-missing"], ref="main", commit="abc")

    assert result.exit_code == 1
    assert "unknown skill" in capsys.readouterr().err
    assert not targets.skills.exists()


def test_excluded_skill_requires_dev_mode(tmp_path, capsys):
    content, targets = make_fixture(tmp_path)
    excluded = next(iter(EXCLUDED_SKILLS))

    result = install_content(content, targets, names=[excluded], ref="main", commit="abc")

    assert result.exit_code == 1
    assert "dev" in capsys.readouterr().err
    assert not targets.skills.exists()

    result = install_content(content, targets, names=[excluded], dev=True, ref="main", commit="abc")

    assert result.exit_code == 0
    assert (targets.skills / excluded).is_dir()


def test_existing_skill_is_skipped_without_force_and_overwritten_with_force(tmp_path):
    content, targets = make_fixture(tmp_path)
    destination = targets.skills / "dh-extra"
    destination.mkdir(parents=True)
    (destination / "SKILL.md").write_text("local", encoding="utf-8")

    result = install_content(content, targets, names=["dh-extra"], ref="main", commit="abc")
    assert result.skipped == 1
    assert (destination / "SKILL.md").read_text(encoding="utf-8") == "local"

    result = install_content(content, targets, names=["dh-extra"], force=True, ref="main", commit="abc")
    assert result.overwritten == 1
    assert (destination / "SKILL.md").read_text(encoding="utf-8") == "dh-extra"


def test_identical_skill_is_unchanged_and_dry_run_writes_nothing(tmp_path):
    content, targets = make_fixture(tmp_path)
    install_content(content, targets, names=["dh-extra"], ref="main", commit="abc")
    cache = targets.skills / DEPLOY_STATE_FILENAME
    cache.unlink()

    result = install_content(content, targets, names=["dh-extra"], ref="main", commit="abc")
    assert result.unchanged == len(BASE_SKILLS) + 1
    assert cache.exists()
    cache.unlink()

    result = install_content(content, targets, dry_run=True, dev=True, ref="main", commit="def")
    assert result.dry_run is True
    assert not cache.exists()


def test_install_without_names_deploys_agents_and_prompts(tmp_path):
    content, targets = make_fixture(tmp_path)

    result = install_content(content, targets, dev=True, ref="main", commit="abc")

    assert result.exit_code == 0
    assert (targets.agents / "planner.agent.md").read_text(encoding="utf-8") == "planner"
    assert (targets.prompts / "ship.prompt.md").read_text(encoding="utf-8") == "ship"


def test_cli_install_dispatches_to_local_installer(tmp_path):
    content, targets = make_fixture(tmp_path)

    exit_code = main(["install", "dh-extra"], content_dir=content, targets=targets)

    assert exit_code == 0
    assert (targets.skills / "dh-extra").is_dir()
