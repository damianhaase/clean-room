# PHASE-004: Download (shallow clone) + directory hash

**Status:** done
**Spec refs:** CR-CLI-023

## Scope

Add an offline-testable shallow-clone context manager and deterministic directory content hashing. Clone failures are surfaced without fallback, successful temporary checkouts are removed on exit, and hashes include sorted relative POSIX paths plus file bytes while ignoring metadata.

## Files touched (<= 8)

- `src/dh_skills/download.py`
- `tests/test_download.py`

## Test file(s) - written BEFORE implementation

- `tests/test_download.py` - covers CR-CLI-023: exact shallow-clone invocation, yielded checkout, cleanup, failure propagation, deterministic content hashing, metadata insensitivity, and binary content.

## Definition of done

- [x] `pytest -q tests/test_download.py` passes
- [x] Full suite (`pytest -q`) still green
- [x] Diff stays within budget (<= 8 files / <= 400 changed lines, excluding docs/fixtures)
- [x] No new runtime dependency added
- [ ] Commit message: `PHASE-004: add shallow download and directory hashing`

## Notes / open questions

- `clone_repo` accepts an injectable command runner and temporary-root factory so tests never invoke git or network access.
- The caller owns the yielded checkout only for the context duration; cleanup occurs on both success and failure.
