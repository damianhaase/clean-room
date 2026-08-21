# AGENTS.md — How to work in this repo

This repo is a clean-room re-implementation of a two-layer AI coding toolchain (package-manager
CLI + content library). It is being built **phase by phase**, and every agent working in this repo
— human or AI — follows the same discipline the *product itself* enforces on its users. Read this
file before writing any code.

## The non-negotiable rules

1. **Spec before code.** Every phase has a spec (in `docs/specs/`, numbered files 00–12) and a
   phase ticket (in `docs/phases/PHASE-NNN-*.md`). Do not write implementation code without a
   phase ticket. If no ticket exists for the work you're about to do, stop and create one first.
2. **Tests before implementation.** For each phase: read the relevant `CR-*` requirement IDs in
   `docs/specs/11-TEST-SPECIFICATION.md`, write the test file(s) first, confirm they fail for the
   right reason, then implement until green. Tests must be authored **from the spec**, never
   reverse-engineered from the implementation you just wrote.
3. **Phase size cap.** ≤ 8 files touched, ≤ 400 changed lines of code per phase (docs, fixtures,
   and generated files excluded from the line count, but new files still count toward the file
   cap). If a phase is trending oversized, stop and split it — do not silently exceed the cap.
4. **One phase in flight at a time.** Finish, test, and commit the current `PHASE-NNN` before
   starting the next. Do not interleave phases.
5. **No network, no LLM in tests.** All tests in this repo run offline and deterministically. Stub
   git downloads, stub routers with lookup tables, use synthetic payloads and temp dirs. A CI run
   with no network access must pass in full.
6. **Stdlib-only runtime.** The CLI package's runtime dependencies are empty. Anything requiring a
   third-party library (e.g. `jsonschema`, embeddings) must (a) live behind an optional extra, and
   (b) have a working stdlib fallback path that is *also* tested.
7. **Never fabricate calibration content.** Router tables, agent descriptions, and skill prose are
   proprietary content to re-author from scratch — never copy from an external original, never
   invent plausible-sounding numbers to make a test pass. If a test is failing, fix the code or the
   calibration table, never edit `eval_queries.json` to force a result.
8. **Data dependencies must exist before enabling CI.** A CI job's code being implemented is not
   sufficient reason to enable it — confirm any data/content dependency it needs (e.g.
   `content/agents/` for route-score/eval) actually exists first. Check
   `docs/phases/README.md`'s CI-gates note before flipping any `if: false` job to enabled.

## Where things live

```
docs/specs/          the 13 clean-room spec files (00–12) — source of truth, do not edit casually
docs/phases/          one ticket per phase: PHASE-001-*.md, PHASE-002-*.md, ...
src/<pkg>/            implementation
tests/                mirrors src/ layout; one test module per implementation module
content/              skills/agents/prompts markdown library (Layer 2)
```

## Phase ticket contract

Every `docs/phases/PHASE-NNN-*.md` must contain, before any code is written:
- **Scope** — one or two sentences, referencing the `CR-*` IDs it implements.
- **Files touched** — explicit list, must be ≤ 8.
- **Test file(s)** — written and committed *before* the implementation commit.
- **Definition of done** — the exact test command that must pass, plus any manual check.
- **Status** — `not-started` / `in-progress` / `blocked` / `done`.

See `docs/PHASE_TEMPLATE.md` for the format to copy.

## Gate before advancing

A phase is done, and the next phase may start, only when:
- [ ] Its test file(s) pass locally and in CI.
- [ ] `git diff` for the phase stays within the file/line budget.
- [ ] The phase ticket's status is updated to `done`.
- [ ] The commit references the phase id (`PHASE-004: ...`).

Do not batch multiple phases into one commit or one PR. If Copilot or another agent proposes a
change spanning more than one `PHASE-NNN`, split the proposal before proceeding.

## Commands agents should know

```bash
pytest -q                     # full suite, must stay offline/deterministic
pytest -q tests/test_router.py -k C1   # run one spec section's tests
python -m <pkg>.cli --version # smoke check the CLI entry point
python -m <pkg>.cli route-score        # once phase 010 lands: routing accuracy gate
python -m <pkg>.cli validate-handoff <file>  # once phase 013 lands
```

## When you (the AI agent) are unsure

- If a requested change isn't covered by an existing `docs/phases/PHASE-NNN-*.md`, propose a new
  phase ticket first and wait for approval rather than writing code speculatively.
- If a spec file (`docs/specs/0X-*.md`) seems to conflict with a request, the spec wins — flag the
  conflict instead of silently resolving it.
- Prefer the smallest change that makes the phase's tests pass. Do not "improve" adjacent code
  outside the phase's declared file list.
