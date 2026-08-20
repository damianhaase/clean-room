import json
from pathlib import Path

from dh_skills.catalog import BASE_SKILLS
from dh_skills.installer import DEPLOY_STATE_FILENAME, install_content
from dh_skills.lifecycle import clean_content, load_deploy_state, uninstall_content, update_check, update_content
from dh_skills.paths import Targets


def make_fixture(tmp_path: Path) -> tuple[Path, Targets]:
    content = tmp_path / "content"
    skills = content / "skills"
    agents = content / "agents"
    prompts = content / "prompts"
    for directory in (skills, agents, prompts):
        directory.mkdir(parents=True)
    for name in (*BASE_SKILLS, "dh-extra"):
        (skills / name).mkdir()
        (skills / name / "SKILL.md").write_text(name, encoding="utf-8")
    (agents / "dh-planner.agent.md").write_text("planner", encoding="utf-8")
    (prompts / "dh-ship.prompt.md").write_text("ship", encoding="utf-8")
    targets = Targets(tmp_path / "skills", tmp_path / "agents", tmp_path / "prompts")
    return content, targets


def test_update_forces_overwrite_and_refreshes_cache(tmp_path):
    content, targets = make_fixture(tmp_path)
    install_content(content, targets, names=["dh-extra"], ref="main", commit="old")
    (targets.skills / "dh-extra" / "SKILL.md").write_text("changed", encoding="utf-8")

    result = update_content(content, targets, names=["dh-extra"], ref="main", commit="new")

    assert result.overwritten == 1
    assert (targets.skills / "dh-extra" / "SKILL.md").read_text(encoding="utf-8") == "dh-extra"
    assert load_deploy_state(targets.skills)["commit"] == "new"


def test_update_check_is_read_only_and_reports_cache_state(tmp_path, capsys):
    content, targets = make_fixture(tmp_path)
    install_content(content, targets, names=["dh-extra"], ref="main", commit="same")
    cache_before = (targets.skills / DEPLOY_STATE_FILENAME).read_text(encoding="utf-8")

    assert update_check(targets, remote_commit="same") == 0
    assert "up to date" in capsys.readouterr().out
    assert (targets.skills / DEPLOY_STATE_FILENAME).read_text(encoding="utf-8") == cache_before

    assert update_check(targets, remote_commit="new") == 0
    assert "update available" in capsys.readouterr().out
    assert update_check(targets, remote_commit=None) == 0
    assert "offline" in capsys.readouterr().out


def test_uninstall_named_skill_rejects_base_and_removes_regular_skill(tmp_path, capsys):
    content, targets = make_fixture(tmp_path)
    install_content(content, targets, names=["dh-extra"], ref="main", commit="abc")

    assert uninstall_content(targets, names=[next(iter(BASE_SKILLS))]).exit_code == 1
    assert "base" in capsys.readouterr().err
    result = uninstall_content(targets, names=["dh-extra"])

    assert result.exit_code == 0
    assert not (targets.skills / "dh-extra").exists()


def test_uninstall_all_requires_confirmation_and_dry_run_writes_nothing(tmp_path, monkeypatch):
    content, targets = make_fixture(tmp_path)
    install_content(content, targets, ref="main", commit="abc")
    monkeypatch.setattr("builtins.input", lambda _: "y")

    result = uninstall_content(targets, dry_run=True)
    assert result.exit_code == 0
    assert (targets.skills / "dh-extra").exists()
    assert (targets.agents / "dh-planner.agent.md").exists()

    result = uninstall_content(targets)
    assert result.exit_code == 0
    assert not (targets.skills / "dh-extra").exists()
    assert not targets.agents.exists()
    assert not targets.prompts.exists()


def test_clean_removes_managed_and_legacy_orphans_after_confirmation(tmp_path, monkeypatch):
    content, targets = make_fixture(tmp_path)
    install_content(content, targets, ref="main", commit="abc")
    (targets.skills / "dh-orphan").mkdir()
    (targets.skills / "clean-old").mkdir()
    (targets.agents / "dh-old.agent.md").write_text("old", encoding="utf-8")
    (targets.prompts / "clean-old.prompt.md").write_text("old", encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _: "y")

    result = clean_content(content, targets)

    assert result.exit_code == 0
    assert not (targets.skills / "dh-orphan").exists()
    assert not (targets.skills / "clean-old").exists()
    assert not (targets.agents / "dh-old.agent.md").exists()
    assert not (targets.prompts / "clean-old.prompt.md").exists()
