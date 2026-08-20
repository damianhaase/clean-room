from pathlib import Path

from dh_skills.installer import install_content
from dh_skills.paths import Targets


def make_fixture(tmp_path: Path) -> tuple[Path, Targets]:
    content = tmp_path / "content"
    skills = content / "skills"
    agents = content / "agents"
    prompts = content / "prompts"
    for directory in (skills, agents, prompts):
        directory.mkdir(parents=True)
    for name in (
        "dh-shell-env-detection",
        "dh-saving-reports",
        "dh-jira-access",
        "dh-confluence-page-access",
    ):
        (skills / name).mkdir()
        (skills / name / "SKILL.md").write_text(name, encoding="utf-8")
    (agents / "planner.agent.md").write_text("bundle agent", encoding="utf-8")
    (prompts / "ship.prompt.md").write_text("bundle prompt", encoding="utf-8")
    targets = Targets(tmp_path / "skills", tmp_path / "agents", tmp_path / "prompts")
    return content, targets


def test_identical_agents_and_prompts_count_unchanged(tmp_path):
    content, targets = make_fixture(tmp_path)
    install_content(content, targets, ref="main", commit="abc")

    result = install_content(content, targets, ref="main", commit="def")

    assert result.unchanged == 6
    assert result.preserved == 0


def test_modified_agents_and_prompts_are_preserved_and_warn(tmp_path, capsys):
    content, targets = make_fixture(tmp_path)
    install_content(content, targets, ref="main", commit="abc")
    (targets.agents / "planner.agent.md").write_text("user agent", encoding="utf-8")
    (targets.prompts / "ship.prompt.md").write_text("user prompt", encoding="utf-8")

    result = install_content(content, targets, ref="main", commit="def")

    assert result.preserved == 2
    assert result.unchanged == 4
    assert (targets.agents / "planner.agent.md").read_text(encoding="utf-8") == "user agent"
    assert (targets.prompts / "ship.prompt.md").read_text(encoding="utf-8") == "user prompt"
    warning = capsys.readouterr().err
    assert "preserve" in warning


def test_force_overwrites_modified_agents_and_prompts(tmp_path):
    content, targets = make_fixture(tmp_path)
    install_content(content, targets, ref="main", commit="abc")
    (targets.agents / "planner.agent.md").write_text("user agent", encoding="utf-8")
    (targets.prompts / "ship.prompt.md").write_text("user prompt", encoding="utf-8")

    result = install_content(content, targets, force=True, ref="main", commit="def")

    assert result.overwritten == 2
    assert result.unchanged == 4
    assert (targets.agents / "planner.agent.md").read_text(encoding="utf-8") == "bundle agent"
    assert (targets.prompts / "ship.prompt.md").read_text(encoding="utf-8") == "bundle prompt"


def test_dry_run_does_not_copy_new_artifacts(tmp_path):
    content, targets = make_fixture(tmp_path)

    result = install_content(content, targets, dry_run=True, ref="main", commit="abc")

    assert result.dry_run is True
    assert result.installed == 6
    assert not targets.agents.exists()
    assert not targets.prompts.exists()
