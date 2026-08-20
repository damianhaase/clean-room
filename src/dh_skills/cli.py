"""Command-line entry point for the dh-skills package manager."""

import sys
import argparse
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .catalog import list_content, status_content
from .installer import install_content
from .lifecycle import clean_content, uninstall_content, update_check, update_content
from .paths import Targets

CLI_NAME = "dh-skills"


def main(
    argv: Sequence[str] | None = None,
    *,
    content_dir: Path | None = None,
    targets: Targets | None = None,
    repo_targets: Targets | None = None,
    remote_commit: str | None = None,
) -> int:
    """Run the CLI scaffold and local catalog reporting commands."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if "--version" in arguments:
        print(f"{CLI_NAME} {__version__}")
        return 0

    parser = argparse.ArgumentParser(prog=CLI_NAME)
    subparsers = parser.add_subparsers(dest="command")
    for command in ("list", "status", "install", "update", "uninstall", "clean"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--dev", action="store_true")
        if command == "list":
            command_parser.add_argument("--skills", action="store_true")
            command_parser.add_argument("--agents", action="store_true")
            command_parser.add_argument("--prompts", action="store_true")
        if command == "install":
            command_parser.add_argument("names", nargs="*")
            command_parser.add_argument("--force", action="store_true")
            command_parser.add_argument("--dry-run", action="store_true")
            command_parser.add_argument("--ref", default="main")
        if command == "update":
            command_parser.add_argument("names", nargs="*")
            command_parser.add_argument("--check", action="store_true")
            command_parser.add_argument("--dry-run", action="store_true")
            command_parser.add_argument("--ref", default="main")
            command_parser.add_argument("--remote-commit")
        if command == "uninstall":
            command_parser.add_argument("names", nargs="*")
            command_parser.add_argument("--skills-only", action="store_true")
            command_parser.add_argument("--agents-only", action="store_true")
            command_parser.add_argument("--prompts-only", action="store_true")
            command_parser.add_argument("--dry-run", action="store_true")
        if command == "clean":
            command_parser.add_argument("--dry-run", action="store_true")
    options = parser.parse_args(arguments)
    if options.command not in {"list", "status", "install", "update", "uninstall", "clean"}:
        print(f"{CLI_NAME}: no command specified", file=sys.stderr)
        return 2

    source = Path("content") if content_dir is None else Path(content_dir)
    resolved_targets = Targets(Path(), Path(), Path()) if targets is None else targets
    if options.command == "update":
        if options.check:
            return update_check(resolved_targets, remote_commit=options.remote_commit or remote_commit)
        return update_content(
            source,
            resolved_targets,
            names=options.names,
            dev=options.dev,
            dry_run=options.dry_run,
            ref=options.ref,
            commit=options.remote_commit or "",
        ).exit_code
    if options.command == "uninstall":
        return uninstall_content(
            resolved_targets,
            names=options.names,
            skills_only=options.skills_only,
            agents_only=options.agents_only,
            prompts_only=options.prompts_only,
            dry_run=options.dry_run,
        ).exit_code
    if options.command == "clean":
        return clean_content(source, resolved_targets, dry_run=options.dry_run).exit_code
    if options.command == "install":
        result = install_content(
            source,
            resolved_targets,
            names=options.names,
            force=options.force,
            dev=options.dev,
            dry_run=options.dry_run,
            ref=options.ref,
        )
        return result.exit_code
    if options.command == "list":
        show_any = options.skills or options.agents or options.prompts
        list_content(
            source,
            resolved_targets,
            dev=options.dev,
            show_skills=options.skills or not show_any,
            show_agents=options.agents or not show_any,
            show_prompts=options.prompts or not show_any,
        )
    else:
        status_content(source, resolved_targets, repo_targets=repo_targets, dev=options.dev)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())