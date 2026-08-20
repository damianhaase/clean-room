# PHASE-010: Eval runner + `eval` / `route-score` commands

**Status:** done
**Spec refs:** CR-RT-008, CR-RT-009, CR-CLI-018, CR-CLI-019

## Scope

Implement offline routing evaluation over injected assertions and agent descriptions, including per-agent PASS/FAIL reports, aggregate route score, unknown-agent semantics, deterministic repeated builds, and the `0.95` threshold gate. Catalog file discovery and richer eval-file loading remain minimal and local.

## Files touched (<= 8)

- `src/dh_skills/eval_runner.py`
- `src/dh_skills/cli.py`
- `tests/test_eval_runner.py`

## Test file(s) - written BEFORE implementation

- `tests/test_eval_runner.py` - covers CR-RT-008/009 and CR-CLI-018/019: exact score arithmetic, empty cases, unknown-agent assertions, report shape, threshold boundary, and CLI exit codes.

## Definition of done

- [x] `pytest -q tests/test_eval_runner.py` passes
- [x] Full suite (`pytest -q`) still green
- [x] Diff stays within budget (<= 8 files / <= 400 changed lines, excluding docs/fixtures)
- [x] No new runtime dependency added
- [ ] Commit message: `PHASE-010: add eval and route-score gates`

## Notes / open questions

- Assertions are injected as `(owner, query, should_trigger)` tuples for deterministic unit tests; optional JSON loading is limited to the local runner helper.
- The CLI accepts `--agents-dir` and `--eval-file` so CI and tests can point at a source catalog without network or bundle discovery.
