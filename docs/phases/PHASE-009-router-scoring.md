# PHASE-009: Router IDF-cosine scoring + calibration tables

**Status:** done
**Spec refs:** CR-RT-003, CR-RT-004, CR-RT-005, CR-RT-006, CR-RT-007, CR-RT-008

## Scope

Implement agent feature profiles, smoothed unigram/bigram IDF, weighted cosine scoring, flat name/signal/phrase bonuses, and deterministic route selection with coordinator and veto behavior. Eval-file loading and CLI gates remain deferred to PHASE-010.

## Files touched (<= 8)

- `src/dh_skills/router.py`
- `tests/test_router.py`

## Test file(s) - written BEFORE implementation

- `tests/test_router.py` - covers CR-RT-003 through CR-RT-008: feature construction, IDF formula, score arithmetic, bonuses, tie ordering, coordinator override, vetoes, empty queries, and threshold.

## Definition of done

- [x] `pytest -q tests/test_router.py` passes
- [x] Full suite (`pytest -q`) still green
- [x] Diff stays within budget (<= 8 files / <= 400 changed lines, excluding docs/fixtures)
- [x] No new runtime dependency added
- [ ] Commit message: `PHASE-009: add deterministic router scoring`

## Notes / open questions

- Calibration tables are authored for the neutral `dh-` agent naming already used by the repository; later content phases may extend them.
- Agent descriptions are injected as `{agent_key: description}` mappings; frontmatter parsing belongs to the later catalog/router integration work.
