"""Local content catalog discovery and reporting."""

import re
from dataclasses import dataclass
from pathlib import Path

from .paths import Targets

BASE_SKILLS = {
    "dh-shell-env-detection",
    "dh-saving-reports",
    "dh-jira-access",
    "dh-confluence-page-access",
}
EXCLUDED_SKILLS = {
    "dh-create-skill",
    "dh-skills-validation",
    "dh-agent-skills-spec",
    "dh-create-agent",
    "dh-create-prompt",
    "dh-agents-validation",
    "dh-prompts-validation",
}


@dataclass(frozen=True)
class Catalog:
    skills: tuple[str, ...]
    agents: tuple[Path, ...]
    prompts: tuple[Path, ...]


def discover_catalog(content_dir: Path) -> Catalog:
    """Discover skills, agents, and prompts from a content checkout."""
    root = Path(content_dir)
    skills_dir = root / "skills"
    agents_dir = root / "agents"
    prompts_dir = root / "prompts"
    skills = tuple(sorted(path.name for path in skills_dir.iterdir() if path.is_dir()))
    agents = tuple(sorted(agents_dir.glob("*.agent.md")))
    prompts = tuple(sorted(prompts_dir.glob("*.prompt.md")))
    return Catalog(skills, agents, prompts)


def _frontmatter_skills(path: Path) -> tuple[str, ...]:
    """Read the inline or block `skills`/`tools` field from an artifact."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return ()
    frontmatter = text.split("---", 2)[1].splitlines()
    values: list[str] = []
    collecting = False
    for line in frontmatter:
        field = re.match(r"(?:skills|tools):\s*(.*)$", line)
        if field:
            value = field.group(1).strip()
            if value.startswith("[") and value.endswith("]"):
                values.extend(item.strip() for item in value[1:-1].split(",") if item.strip())
                collecting = False
            else:
                collecting = True
            continue
        if collecting:
            item = re.match(r"\s*-\s*(\S.*)$", line)
            if item:
                values.append(item.group(1).strip())
            else:
                collecting = False
    return tuple(values)


def list_content(
    content_dir: Path,
    targets: Targets,
    *,
    dev: bool = False,
    show_skills: bool = True,
    show_agents: bool = True,
    show_prompts: bool = True,
) -> None:
    """Print available content and installed markers."""
    catalog = discover_catalog(content_dir)
    if show_skills:
        print("Skills:")
        visible = [name for name in catalog.skills if dev or name not in EXCLUDED_SKILLS]
        for name in visible:
            marker = "*" if name in BASE_SKILLS else "[dev only]" if name in EXCLUDED_SKILLS else ""
            installed = " [installed]" if (targets.skills / name).is_dir() else ""
            suffix = f" {marker}" if marker else ""
            print(f"{name}{suffix}{installed}")
        installed_count = sum((targets.skills / name).is_dir() for name in visible)
        print(f"Installed skills: {len(visible)} available, {installed_count} installed")
    if show_agents:
        print("Agents:")
        for path in catalog.agents:
            wrapped = ", ".join(_frontmatter_skills(path))
            suffix = f" ({wrapped})" if wrapped else ""
            print(f"{path.name}{suffix}")
    if show_prompts:
        print("Prompts:")
        for path in catalog.prompts:
            print(path.name)


def status_content(
    content_dir: Path,
    targets: Targets,
    *,
    repo_targets: Targets | None = None,
    dev: bool = False,
) -> None:
    """Print available content and installation counts."""
    catalog = discover_catalog(content_dir)
    visible_skills = [name for name in catalog.skills if dev or name not in EXCLUDED_SKILLS]
    installed_skills = sum((targets.skills / name).is_dir() for name in visible_skills)
    print(f"Skills: {installed_skills}/{len(visible_skills)} installed")

    user_agents = sum((targets.agents / path.name).is_file() for path in catalog.agents)
    user_prompts = sum((targets.prompts / path.name).is_file() for path in catalog.prompts)
    print(f"Agents: {user_agents}/{len(catalog.agents)} available [user]")
    print(f"Prompts: {user_prompts}/{len(catalog.prompts)} available [user]")
    if repo_targets is not None:
        repo_agents = sum((repo_targets.agents / path.name).is_file() for path in catalog.agents)
        repo_prompts = sum((repo_targets.prompts / path.name).is_file() for path in catalog.prompts)
        print(f"Repo agents: {repo_agents} installed")
        print(f"Repo prompts: {repo_prompts} installed")