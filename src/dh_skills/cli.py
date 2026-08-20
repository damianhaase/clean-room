"""Command-line entry point for the dh-skills package manager."""

import sys
from collections.abc import Sequence

from . import __version__

CLI_NAME = "dh-skills"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI scaffold and handle the version option."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if "--version" in arguments:
        print(f"{CLI_NAME} {__version__}")
        return 0

    print(f"{CLI_NAME}: no command specified", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())