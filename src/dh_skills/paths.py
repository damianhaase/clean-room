"""Deployment target resolution for the dh-skills CLI."""

import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Targets:
    skills: Path
    agents: Path
    prompts: Path


def resolve_targets(
    *,
    platform: str | None = None,
    home: Path | None = None,
    environ: Mapping[str, str] | None = None,
    skills: Path | None = None,
    agents: Path | None = None,
    prompts: Path | None = None,
    repo: Path | None = None,
) -> Targets:
    """Resolve deployment directories from platform defaults and overrides."""
    current_platform = sys.platform if platform is None else platform
    user_home = Path.home() if home is None else Path(home)
    environment = os.environ if environ is None else environ

    resolved_skills = user_home / ".agents" / "skills" if skills is None else Path(skills)
    resolved_agents = user_home / ".copilot" / "agents" if agents is None else Path(agents)

    if current_platform.startswith("win"):
        appdata = Path(environment.get("APPDATA", user_home / "AppData" / "Roaming"))
        default_prompts = appdata / "Code" / "User" / "prompts"
    elif current_platform == "darwin":
        default_prompts = user_home / "Library" / "Application Support" / "Code" / "User" / "prompts"
    else:
        config_home = Path(environment.get("XDG_CONFIG_HOME", user_home / ".config"))
        default_prompts = config_home / "Code" / "User" / "prompts"

    resolved_prompts = default_prompts if prompts is None else Path(prompts)
    if repo is not None:
        repo_path = Path(repo)
        if agents is None:
            resolved_agents = repo_path / ".github" / "agents"
        if prompts is None:
            resolved_prompts = repo_path / ".github" / "prompts"

    return Targets(resolved_skills, resolved_agents, resolved_prompts)