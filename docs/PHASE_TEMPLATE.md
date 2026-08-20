# PHASE-NNN: <short title>

**Status:** not-started
**Spec refs:** CR-XXX-NNN, CR-XXX-NNN

## Scope

<One or two sentences. What does this phase add, and what does it explicitly NOT do yet?>

## Files touched (≤ 8)

- `src/<pkg>/...`
- `tests/...`

## Test file(s) — written BEFORE implementation

- `tests/test_<module>.py` — covers CR-XXX-NNN cases: <list the specific assertions>

## Definition of done

- [ ] `pytest -q tests/test_<module>.py` passes
- [ ] Full suite (`pytest -q`) still green
- [ ] Diff stays within budget (≤ 8 files / ≤ 400 changed lines, excluding docs/fixtures)
- [ ] No new runtime dependency added (or: added behind an extra + fallback, per AGENTS.md)
- [ ] Commit message: `PHASE-NNN: <summary>`

## Notes / open questions

<Anything ambiguous in the spec that needed a judgment call, and what was decided.>
