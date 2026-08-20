"""Local update, uninstall, and cleanup lifecycle operations."""

import json
import shutil
from pathlib import Path

from .catalog import BASE_SKILLS, discover_catalog
from .installer import DEPLOY_STATE_FILENAME, InstallResult, install_content
from .paths import Targets

MANAGED_PREFIXES = ("dh-",)
LEGACY_PREFIXES = ("clean-",)


def load_deploy_state(skills_target: Path) -> dict[str, str]:
    """Load the deployment cache, returning an empty mapping when absent."""
    try:
        value = json.loads((Path(skills_target) / DEPLOY_STATE_FILENAME).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def update_content(
    content_dir: Path,
    targets: Targets,
    *,
    names: list[str] | None = None,
    dev: bool = False,
    dry_run: bool = False,
    ref: str = "main",
    commit: str = "",
) -> InstallResult:
    """Force-install content for an update operation."""
    return install_content(
        content_dir,
        targets,
        names=names,
        force=True,
        dev=dev,
        dry_run=dry_run,
        ref=ref,
        commit=commit,
    )


def update_check(targets: Targets, *, remote_commit: str | None) -> int:
    """Report whether cached content differs from an injected remote commit."""
    state = load_deploy_state(targets.skills)
    if not state:
        print("no deploy recorded")
    elif remote_commit is None:
        print("offline: unable to check for updates")
    elif state.get("commit") == remote_commit:
        print("up to date")
    else:
        print("update available: run update")
    return 0


def _confirm(action: str, *, dry_run: bool) -> bool:
    if dry_run:
        return True
    return input(f"{action} [y/N] ").strip().lower() == "y"


def _remove(path: Path, *, dry_run: bool) -> None:
    if dry_run:
        return
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def uninstall_content(
    targets: Targets,
    *,
    names: list[str] | None = None,
    skills_only: bool = False,
    agents_only: bool = False,
    prompts_only: bool = False,
    dry_run: bool = False,
) -> InstallResult:
    """Remove named or all managed installed content."""
    result = InstallResult(dry_run=dry_run)
    requested = list(names or [])
    if requested and (skills_only or agents_only or prompts_only):
        print("dh-skills: scope flags require no names", file=__import__("sys").stderr)
        return InstallResult(exit_code=2, dry_run=dry_run)
    if requested:
        for name in requested:
            if name in BASE_SKILLS:
                print(f"dh-skills: cannot uninstall base skill {name}", file=__import__("sys").stderr)
                return InstallResult(exit_code=1, dry_run=dry_run)
            candidates = []
            if not agents_only and not prompts_only:
                candidates.append(targets.skills / name)
            if not skills_only and not prompts_only:
                candidates.append(targets.agents / f"{name}.agent.md")
            if not skills_only and not agents_only:
                candidates.append(targets.prompts / f"{name}.prompt.md")
            for candidate in candidates:
                if candidate.exists():
                    _remove(candidate, dry_run=dry_run)
                    result.overwritten += 1
                    break
        _prune_base_skills(targets, dry_run=dry_run)
        return result

    if not _confirm("Remove all managed content?", dry_run=dry_run):
        return result
    if not agents_only:
        _remove_managed_skills(targets.skills, result, dry_run=dry_run)
    if not skills_only:
        _remove_managed_files(targets.agents, ".agent.md", result, dry_run=dry_run)
    if not prompts_only:
        _remove_managed_files(targets.prompts, ".prompt.md", result, dry_run=dry_run)
    return result


def _remove_managed_skills(target: Path, result: InstallResult, *, dry_run: bool) -> None:
    if not target.exists():
        return
    for path in target.iterdir():
        if path.is_dir() and path.name.startswith(MANAGED_PREFIXES + LEGACY_PREFIXES):
            _remove(path, dry_run=dry_run)
            result.overwritten += 1


def _remove_managed_files(target: Path, suffix: str, result: InstallResult, *, dry_run: bool) -> None:
    if not target.exists():
        return
    for path in target.glob(f"*{suffix}"):
        if path.stem.removesuffix(suffix).startswith(MANAGED_PREFIXES + LEGACY_PREFIXES):
            _remove(path, dry_run=dry_run)
            result.overwritten += 1
    if not dry_run and target.exists() and not any(target.iterdir()):
        target.rmdir()


def _prune_base_skills(targets: Targets, *, dry_run: bool) -> None:
    managed = [path for path in targets.skills.glob("dh-*") if path.is_dir() and path.name not in BASE_SKILLS]
    if managed:
        return
    for name in BASE_SKILLS:
        _remove(targets.skills / name, dry_run=dry_run)


def clean_content(content_dir: Path, targets: Targets, *, dry_run: bool = False) -> InstallResult:
    """Remove managed and legacy target items absent from canonical content."""
    catalog = discover_catalog(Path(content_dir))
    canonical_skills = set(catalog.skills)
    canonical_agents = {path.name for path in catalog.agents}
    canonical_prompts = {path.name for path in catalog.prompts}
    orphans: list[Path] = []
    if targets.skills.exists():
        orphans.extend(
            path for path in targets.skills.iterdir()
            if path.is_dir()
            and path.name.startswith(MANAGED_PREFIXES + LEGACY_PREFIXES)
            and path.name not in canonical_skills
        )
    if targets.agents.exists():
        orphans.extend(path for path in targets.agents.glob("*.agent.md") if path.name not in canonical_agents)
    if targets.prompts.exists():
        orphans.extend(path for path in targets.prompts.glob("*.prompt.md") if path.name not in canonical_prompts)
    result = InstallResult(dry_run=dry_run)
    if not orphans or not _confirm(f"Remove {len(orphans)} orphaned items?", dry_run=dry_run):
        return result
    for path in orphans:
        _remove(path, dry_run=dry_run)
        result.overwritten += 1
    return result