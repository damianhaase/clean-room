# PHASE-006: Preserve user edits (agents/prompts)

**Status:** done
**Spec refs:** CR-CLI-022

## Scope

Update agent and prompt deployment so identical files count unchanged, modified user files are preserved with a warning unless `--force` is supplied, and new files are copied. Skill directory installation remains governed by Phase 005 and broader update/uninstall behavior remains deferred.

## Files touched (<= 8)

- `src/dh_skills/installer.py`
- `tests/test_preserve.py`

## Test file(s) - written BEFORE implementation

- `tests/test_preserve.py` - covers CR-CLI-022: identical artifact detection, modified-file preservation and warning, forced overwrite, new artifact copy, and dry-run non-writing behavior.

## Definition of done

- [x] `pytest -q tests/test_preserve.py` passes
- [x] Full suite (`pytest -q`) still green
- [x] Diff stays within budget (<= 8 files / <= 400 changed lines, excluding docs/fixtures)
- [x] No new runtime dependency added
- [ ] Commit message: `PHASE-006: preserve modified agent and prompt files`

## Notes / open questions

- Preservation applies to the no-name install path, which deploys agents and prompts; named skill installs do not touch those artifacts.
- `--force` remains an explicit overwrite request and is tested for both artifact types.
