# PHASE-008: Router tokenizer + stemmer

**Status:** done
**Spec refs:** CR-RT-002

## Scope

Implement the deterministic router's lowercase token extraction, repeated ordered suffix stemming, stopword and digit filtering, and bigram construction. Corpus loading, scoring, calibration, and routing decisions remain deferred to later phases.

## Files touched (<= 8)

- `src/dh_skills/tokenizer.py`
- `tests/test_tokenizer.py`

## Test file(s) - written BEFORE implementation

- `tests/test_tokenizer.py` - covers CR-RT-002: alphanumeric extraction, case/punctuation normalization, specified suffix examples, repeated stripping, raw/content views, digit and stopword filtering, and bigram exclusion.

## Definition of done

- [x] `pytest -q tests/test_tokenizer.py` passes
- [x] Full suite (`pytest -q`) still green
- [x] Diff stays within budget (<= 8 files / <= 400 changed lines, excluding docs/fixtures)
- [x] No new runtime dependency added
- [ ] Commit message: `PHASE-008: add router tokenizer and stemmer`

## Notes / open questions

- The stopword set is explicit and intentionally small; it includes common function words and the boilerplate terms named by the router specification.
