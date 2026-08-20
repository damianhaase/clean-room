from pathlib import Path

import pytest

from dh_skills.paths import resolve_targets


def test_macos_defaults_use_home_directories(tmp_path):
    targets = resolve_targets(platform="darwin", home=tmp_path)

    assert targets.skills == tmp_path / ".agents" / "skills"
    assert targets.agents == tmp_path / ".copilot" / "agents"
    assert targets.prompts == tmp_path / "Library" / "Application Support" / "Code" / "User" / "prompts"


def test_linux_defaults_honor_xdg_config_home(tmp_path):
    config_home = tmp_path / "config"

    targets = resolve_targets(platform="linux", home=tmp_path, environ={"XDG_CONFIG_HOME": str(config_home)})

    assert targets.skills == tmp_path / ".agents" / "skills"
    assert targets.agents == tmp_path / ".copilot" / "agents"
    assert targets.prompts == config_home / "Code" / "User" / "prompts"


def test_linux_defaults_fall_back_to_dot_config(tmp_path):
    targets = resolve_targets(platform="linux", home=tmp_path, environ={})

    assert targets.prompts == tmp_path / ".config" / "Code" / "User" / "prompts"


def test_windows_defaults_use_appdata_when_available(tmp_path):
    appdata = tmp_path / "AppData" / "Roaming"

    targets = resolve_targets(platform="win32", home=tmp_path, environ={"APPDATA": str(appdata)})

    assert targets.skills == tmp_path / ".agents" / "skills"
    assert targets.agents == tmp_path / ".copilot" / "agents"
    assert targets.prompts == appdata / "Code" / "User" / "prompts"


def test_windows_defaults_fall_back_to_home_appdata(tmp_path):
    targets = resolve_targets(platform="win32", home=tmp_path, environ={})

    assert targets.prompts == tmp_path / "AppData" / "Roaming" / "Code" / "User" / "prompts"


def test_explicit_targets_override_platform_defaults(tmp_path):
    skills = tmp_path / "skills"
    agents = tmp_path / "agents"
    prompts = tmp_path / "prompts"

    targets = resolve_targets(
        platform="darwin",
        home=tmp_path,
        skills=skills,
        agents=agents,
        prompts=prompts,
    )

    assert targets.skills == skills
    assert targets.agents == agents
    assert targets.prompts == prompts


def test_repo_mode_redirects_only_agents_and_prompts(tmp_path):
    repo = tmp_path / "repo"

    targets = resolve_targets(platform="darwin", home=tmp_path, repo=repo)

    assert targets.skills == tmp_path / ".agents" / "skills"
    assert targets.agents == repo / ".github" / "agents"
    assert targets.prompts == repo / ".github" / "prompts"


def test_explicit_agent_and_prompt_targets_win_over_repo_mode(tmp_path):
    repo = tmp_path / "repo"
    agents = tmp_path / "custom-agents"
    prompts = tmp_path / "custom-prompts"

    targets = resolve_targets(
        platform="darwin",
        home=tmp_path,
        repo=repo,
        agents=agents,
        prompts=prompts,
    )

    assert targets.agents == agents
    assert targets.prompts == prompts
