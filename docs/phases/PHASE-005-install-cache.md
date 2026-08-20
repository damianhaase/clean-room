# PHASE-005: Deploy-state cache + `install` (no preserve logic)

**Status:** done
**Spec refs:** CR-CLI-011, CR-CLI-023

## Scope

Implement local fixture installation for skills, agents, and prompts, including base-skill inclusion, force/unchanged/skip behavior, dry-run support, and deploy-state cache writes. User-edit preservation for agents and prompts, remote download orchestration, and update behavior are deferred to later phases.

## Files touched (<= 8)

- `src/dh_skills/installer.py`
- `tests/test_installer.py`

## Test file(s) - written BEFORE implementation

- `tests/test_installer.py` - covers CR-CLI-011/023: base-skill inclusion, validation errors, skip/force/hash behavior, dry-run, artifact deployment, and cache contents.

## Definition of done

- [x] `pytest -q tests/test_installer.py` passes
- [x] Full suite (`pytest -q`) still green
- [x] Diff stays within budget (<= 8 files / <= 400 changed lines, excluding docs/fixtures)
- [x] No new runtime dependency added
- [ ] Commit message: `PHASE-005: add install and deploy-state cache`

## Notes / open questions

- This phase exposes `install_content` as the local deployment primitive; remote clone/ref resolution is deferred while preserving the specified deploy-state format.
- Existing agent/prompt files are skipped rather than compared for preservation; the dedicated preservation contract belongs to PHASE-006.
