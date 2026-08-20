import sys

from dh_skills.cli import main


def test_version_prints_cli_name_and_version(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["dh-skills", "--version"])

    exit_code = main()

    assert exit_code == 0
    assert capsys.readouterr().out == "dh-skills 0.0.1\n"
