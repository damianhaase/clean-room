"""Offline-testable git download and directory hashing helpers."""

import hashlib
import subprocess
import tempfile
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


@contextmanager
def clone_repo(
    repository: str,
    ref: str,
    *,
    runner: CommandRunner = subprocess.run,
    temp_root: Path | None = None,
) -> Iterator[Path]:
    """Shallow-clone a ref and remove its temporary checkout afterward."""
    with tempfile.TemporaryDirectory(dir=temp_root, prefix="dh-skills-") as directory:
        checkout = Path(directory)
        command = ["git", "clone", "--depth", "1", "--branch", ref, repository, str(checkout)]
        runner(command, check=True, capture_output=True, text=True)
        yield checkout


def directory_hash(root: Path) -> str:
    """Return a deterministic hash of file paths and contents below ``root``."""
    digest = hashlib.sha256()
    base = Path(root)
    files = sorted(path for path in base.rglob("*") if path.is_file())
    for path in files:
        relative_path = path.relative_to(base).as_posix().encode("utf-8")
        digest.update(relative_path)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()