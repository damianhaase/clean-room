from pathlib import Path

from dh_skills.catalog import BASE_SKILLS, EXCLUDED_SKILLS
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
        (skills / name).mkdir()
    (agents / "planner.agent.md").write_text("---\nskills: [dh-extra, dh-saving-reports]\n---\n", encoding="utf-8")
    (prompts / "ship.prompt.md").write_text("ship", encoding="utf-8")

    user_targets = Targets(
        skills=tmp_path / "user-skills",
        agents=tmp_path / "user-agents",
        prompts=tmp_path / "user-prompts",
    )
    user_targets.skills.mkdir()
    (user_targets.skills / "dh-extra").mkdir()
    user_targets.agents.mkdir()
    (user_targets.agents / "planner.agent.md").write_text("user planner", encoding="utf-8")
    user_targets.prompts.mkdir()
    (user_targets.prompts / "ship.prompt.md").write_text("user ship", encoding="utf-8")
    return content, user_targets


def test_list_hides_excluded_skills_and_marks_installed_and_base(tmp_path, capsys):
    content, targets = make_fixture(tmp_path)

    exit_code = main(["list"], content_dir=content, targets=targets)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "dh-extra [installed]" in output
    assert "dh-shell-env-detection *" in output
    assert next(iter(EXCLUDED_SKILLS)) not in output
    assert "Installed skills: 5 available, 1 installed" in output


def test_list_dev_includes_excluded_and_lists_agents_and_prompts(tmp_path, capsys):
    content, targets = make_fixture(tmp_path)

    exit_code = main(["list", "--dev"], content_dir=content, targets=targets)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert f"{next(iter(EXCLUDED_SKILLS))} [dev only]" in output
    assert "planner.agent.md" in output
    assert "ship.prompt.md" in output
    assert "dh-extra, dh-saving-reports" in output


def test_status_reports_available_and_installed_counts_by_location(tmp_path, capsys):
    content, targets = make_fixture(tmp_path)
    repo_targets = Targets(
        skills=targets.skills,
        agents=tmp_path / "repo" / ".github" / "agents",
        prompts=tmp_path / "repo" / ".github" / "prompts",
    )
    repo_targets.agents.mkdir(parents=True)
    (repo_targets.agents / "planner.agent.md").write_text("repo planner", encoding="utf-8")

    exit_code = main(["status"], content_dir=content, targets=targets, repo_targets=repo_targets)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Skills: 1/5 installed" in output
    assert "Agents: 1/1 available [user]" in output
    assert "Prompts: 1/1 available [user]" in output
    assert "Repo agents: 1 installed" in output
