# PHASE-002: Path resolution (per-OS targets)

**Status:** done
**Spec refs:** CR-CLI-002, CR-CLI-004

## Scope

Add deterministic target resolution for skills, agents, and prompts across macOS, Linux/other, and Windows defaults. Support explicit target overrides and repository mode, where only agents and prompts move under `<repo>/.github`; command dispatch and deployment behavior remain deferred.

## Files touched (<= 8)

- `src/dh_skills/paths.py`
- `tests/test_paths.py`

## Test file(s) - written BEFORE implementation

- `tests/test_paths.py` - covers CR-CLI-002/004: platform defaults, explicit overrides, and repository target precedence.

## Definition of done

- [x] `pytest -q tests/test_paths.py` passes
- [x] Full suite (`pytest -q`) still green
- [x] Diff stays within budget (<= 8 files / <= 400 changed lines, excluding docs/fixtures)
- [x] No new runtime dependency added
- [ ] Commit message: `PHASE-002: add cross-platform target resolution`

## Notes / open questions

- The resolver accepts an injectable platform and environment so behavior can be tested offline without mutating the host environment.
- A repository target is treated as already validated by the caller; git-repository validation belongs to the later CLI argument/command phase.
