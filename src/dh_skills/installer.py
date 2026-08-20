"""Local content installation and deploy-state recording."""

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .catalog import BASE_SKILLS, EXCLUDED_SKILLS, discover_catalog
from .download import directory_hash
from .paths import Targets

DEPLOY_STATE_FILENAME = ".dh-skills-deploy.json"


@dataclass
class InstallResult:
    exit_code: int = 0
    installed: int = 0
    overwritten: int = 0
    unchanged: int = 0
    skipped: int = 0
    preserved: int = 0
    dry_run: bool = False


def _error(message: str) -> InstallResult:
    print(f"dh-skills: {message}", file=__import__("sys").stderr)
    return InstallResult(exit_code=1)


def _copy_skill(source: Path, destination: Path, result: InstallResult, *, force: bool, dry_run: bool) -> None:
    if destination.is_dir():
        if directory_hash(source) == directory_hash(destination):
            result.unchanged += 1
            return
        if not force:
            result.skipped += 1
            return
        result.overwritten += 1
    else:
        result.installed += 1
    if dry_run:
        return
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def _copy_artifact(
    source: Path,
    destination: Path,
    result: InstallResult,
    *,
    force: bool,
    dry_run: bool,
) -> None:
    if destination.exists():
        if source.read_bytes() == destination.read_bytes():
            result.unchanged += 1
            return
        if not force:
            result.preserved += 1
            print(f"dh-skills: preserve {destination}", file=__import__("sys").stderr)
            return
        result.overwritten += 1
    else:
        result.installed += 1
    if not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _write_state(target: Path, ref: str, commit: str) -> None:
    payload = {
        "ref": ref,
        "commit": commit,
        "deployed_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        target.mkdir(parents=True, exist_ok=True)
        (target / DEPLOY_STATE_FILENAME).write_text(json.dumps(payload) + "\n", encoding="utf-8")
    except OSError:
        return


def install_content(
    content_dir: Path,
    targets: Targets,
    *,
    names: list[str] | None = None,
    force: bool = False,
    dev: bool = False,
    dry_run: bool = False,
    ref: str = "main",
    commit: str = "",
) -> InstallResult:
    """Install selected local content and optionally record its deployment."""
    catalog = discover_catalog(Path(content_dir))
    available = set(catalog.skills)
    requested_all = names is None or len(names) == 0
    selected = set(available if requested_all else names or [])
    unknown = selected - available
    if unknown:
        return _error(f"unknown skill: {sorted(unknown)[0]}")
    excluded = selected & EXCLUDED_SKILLS
    if excluded and not dev:
        return _error(f"skill {sorted(excluded)[0]} is dev-only; use --dev")

    selected.update(BASE_SKILLS)
    result = InstallResult(dry_run=dry_run)
    for name in sorted(selected):
        _copy_skill(
            Path(content_dir) / "skills" / name,
            targets.skills / name,
            result,
            force=force,
            dry_run=dry_run,
        )

    if requested_all:
        for source in catalog.agents:
            _copy_artifact(source, targets.agents / source.name, result, force=force, dry_run=dry_run)
        for source in catalog.prompts:
            _copy_artifact(source, targets.prompts / source.name, result, force=force, dry_run=dry_run)

    if not dry_run and result.exit_code == 0:
        _write_state(targets.skills, ref, commit)
    return result