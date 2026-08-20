import os
import subprocess
from pathlib import Path

import pytest

from dh_skills.download import clone_repo, directory_hash


def test_clone_repo_uses_shallow_ref_and_cleans_checkout(tmp_path):
    calls = []

    def runner(command, check, capture_output, text):
        calls.append((command, check, capture_output, text))
        checkout = Path(command[-1])
        (checkout / "README.md").write_text("fixture", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    with clone_repo("https://example.invalid/content.git", "develop", runner=runner, temp_root=tmp_path) as checkout:
        assert checkout.is_dir()
        assert (checkout / "README.md").read_text(encoding="utf-8") == "fixture"
        assert calls == [
            (
                ["git", "clone", "--depth", "1", "--branch", "develop", "https://example.invalid/content.git", str(checkout)],
                True,
                True,
                True,
            )
        ]
        checkout_path = checkout

    assert not checkout_path.exists()


def test_clone_repo_propagates_git_failure_and_cleans_checkout(tmp_path):
    checkout_path = None

    def runner(command, check, capture_output, text):
        nonlocal checkout_path
        checkout_path = Path(command[-1])
        raise subprocess.CalledProcessError(1, command, stderr="clone failed")

    with pytest.raises(subprocess.CalledProcessError):
        with clone_repo("repo", "main", runner=runner, temp_root=tmp_path):
            raise AssertionError("clone should fail before yielding")

    assert checkout_path is not None
    assert not checkout_path.exists()


def test_directory_hash_is_ordered_and_ignores_file_metadata(tmp_path):
    root = tmp_path / "tree"
    (root / "nested").mkdir(parents=True)
    (root / "b.txt").write_bytes(b"b")
    (root / "nested" / "a.txt").write_bytes(b"a")

    original = directory_hash(root)
    os.utime(root / "b.txt", (1, 1))
    os.chmod(root / "b.txt", 0o600)

    assert directory_hash(root) == original
    (root / "nested" / "a.txt").write_bytes(b"changed")
    assert directory_hash(root) != original


def test_directory_hash_includes_relative_paths_and_binary_bytes(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "a.bin").write_bytes(b"one\x00two")
    (second / "b.bin").write_bytes(b"one\x00two")

    assert directory_hash(first) != directory_hash(second)
