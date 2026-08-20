# PHASE-007: `update`, `update --check`, `uninstall`, `clean`

**Status:** done
**Spec refs:** CR-CLI-013, CR-CLI-014, CR-CLI-015

## Scope

Add local lifecycle commands for forceful update, read-only deploy-state checks, uninstall, and orphan cleanup. Canonical content and remote commit values are injected for deterministic offline tests; network download and CLI-version advisories remain deferred.

## Files touched (<= 8)

- `src/dh_skills/lifecycle.py`
- `src/dh_skills/cli.py`
- `tests/test_lifecycle.py`

## Test file(s) - written BEFORE implementation

- `tests/test_lifecycle.py` - covers CR-CLI-013/014/015: forced update, cache check states, named/base uninstall, confirmed/dry-run bulk removal, and managed/legacy orphan cleanup.

## Definition of done

- [x] `pytest -q tests/test_lifecycle.py` passes
- [x] Full suite (`pytest -q`) still green
- [x] Diff stays within budget (<= 8 files / <= 400 changed lines, excluding docs/fixtures)
- [x] No new runtime dependency added
- [ ] Commit message: `PHASE-007: add lifecycle commands`

## Notes / open questions

- `update --check` receives `remote_commit` instead of making a network call; a missing value is treated as informational/offline.
- The lifecycle helpers operate on local content and targets. Download orchestration and repository validation remain future work.
