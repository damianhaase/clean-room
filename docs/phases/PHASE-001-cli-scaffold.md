# PHASE-001: CLI scaffold + `--version`

**Status:** done
**Spec refs:** CR-CLI-001

## Scope

Add the stdlib-only Python package and console entry point for the `dh-skills` CLI. The CLI supports only `--version` in this phase and prints the project version; command handlers, path resolution, and content deployment are deferred to later phases.

## Files touched (<= 8)

- `pyproject.toml`
- `src/dh_skills/__init__.py`
- `src/dh_skills/cli.py`
- `tests/test_cli.py`

## Test file(s) - written BEFORE implementation

- `tests/test_cli.py` - covers CR-CLI-001: `main()` handles `--version`, prints `dh-skills 0.0.1`, and returns exit code 0.

## Definition of done

- [x] `pytest -q tests/test_cli.py` passes
- [x] Full suite (`pytest -q`) still green
- [x] `python -m dh_skills.cli --version` prints `dh-skills 0.0.1`
- [x] Diff stays within budget (<= 8 files / <= 400 changed lines, excluding docs/fixtures)
- [x] No new runtime dependency added
- [ ] Commit message: `PHASE-001: scaffold CLI version command`

## Notes / open questions

- The repository CI and README use `dh-skills`; this phase resolves the packaging placeholders to the importable package `dh_skills` and console script `dh-skills`.
