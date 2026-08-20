# PHASE-003: `list` / `status` against fixture content dir

**Status:** done
**Spec refs:** CR-CLI-005, CR-CLI-010, CR-CLI-016

## Scope

Add local catalog discovery and the `list` and `status` CLI commands against a fixture content directory. The commands report visible/dev-only skills, installed markers, base-skill markers, installed agents/prompts, and user/repository counts; downloading and deployment remain deferred.

## Files touched (<= 8)

- `src/dh_skills/catalog.py`
- `src/dh_skills/cli.py`
- `tests/test_catalog.py`

## Test file(s) - written BEFORE implementation

- `tests/test_catalog.py` - covers CR-CLI-005/010/016: filtered and dev skill listings, installed/base markers, agent and prompt listings, and status counts.

## Definition of done

- [x] `pytest -q tests/test_catalog.py` passes
- [x] Full suite (`pytest -q`) still green
- [x] Diff stays within budget (<= 8 files / <= 400 changed lines, excluding docs/fixtures)
- [x] No new runtime dependency added
- [ ] Commit message: `PHASE-003: add list and status commands`

## Notes / open questions

- Content discovery is injected through `content_dir` for deterministic tests; later download and bundle precedence will supply the production source.
- Repository counts are derived from the resolved targets when provided; no git validation is introduced in this phase.
