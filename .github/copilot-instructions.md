# GitHub Copilot instructions for this repo

Read `AGENTS.md` at the repo root first — it is the primary contract for how work happens here.
The rules below are Copilot-specific reinforcement of that contract.

## Before suggesting or writing any code

1. Ask (or check `docs/phases/`) which `PHASE-NNN` ticket the current request belongs to. If none
   exists, propose a ticket in `docs/phases/PHASE-NNN-<slug>.md` (copy `docs/PHASE_TEMPLATE.md`)
   before generating implementation code.
2. Identify the `CR-*` requirement IDs the phase covers, from `docs/specs/`. Reference them in code
   comments and commit messages sparingly, but the test file must reference them explicitly.
3. Check the phase's declared file list. Do not touch files outside it. If a fix genuinely requires
   touching another file, say so explicitly and ask whether to widen the phase or open a new one.

## Test-first, always

- When asked to implement a phase, generate the test file(s) first, in `tests/`, mirroring the
  `src/` module path. Do not generate implementation code in the same turn unless the tests already
  exist and are shown failing.
- Tests must not import from the implementation module to build expected values — expected values
  come from the spec text, written as literals in the test.
- Use `tmp_path` (pytest) fixtures for anything touching the filesystem. Never write outside a temp
  dir in a test.
- Stub all network and git calls. `unittest.mock.patch` the download function; never let a test
  invoke real `git clone` or hit a real URL.

## Size discipline

- Keep generated diffs within the phase's stated budget (≤ 8 files, ≤ 400 changed lines,
  docs/fixtures excluded). If a request would blow the budget, stop and propose splitting into two
  phases instead of generating an oversized diff.
- Prefer several small, reviewable functions over one large one — this mirrors the router/schema
  modules in the spec, which are intentionally small and single-purpose.

## Style & dependencies

- Runtime code in `src/<pkg>/` must not import third-party packages unless the phase ticket
  explicitly says otherwise (and then only behind an optional extra + fallback, per `AGENTS.md`
  rule 6).
- Test code may use `pytest` and `pytest-mock`/`unittest.mock` freely.
- Type-hint public functions. Keep functions under roughly 40 lines; if a function is growing past
  that, it's a signal the phase should be split.
- Follow the exact algorithm/constants given in `docs/specs/03-DETERMINISTIC-ROUTER-SPEC.md` and
  `docs/specs/04-HANDOFF-CONTRACT-SPEC.md` verbatim (stemmer suffix list, IDF formula, JSON Schema
  shape) — these are specified precisely and are not open to creative reinterpretation.

## When generating content (skills/agents/prompts under `content/`)

- Never copy prose from any external source verbatim. Re-author from the structural contract in
  `docs/specs/05-CONTENT-FORMATS-AND-VALIDATION-SPEC.md` and the per-item behavioral contract in
  `docs/specs/06-SKILLS-INVENTORY.md` / `07-AGENTS-AND-INVARIANTS-SPEC.md` / `08-PROMPTS-INVENTORY.md`.
- Every skill/agent/prompt needs a paired `eval_queries.json` with genuinely new positive/negative
  queries — do not fabricate a token set just to make `route-score` pass artificially high.
- Respect budgets: `SKILL.md` ≤ 500 lines (hard), agent `description` ≤ ~1500 chars.

## Commit messages

Format: `PHASE-NNN: <short summary>`. One phase per commit where possible. Do not write "WIP" or
multi-phase commits.

## If a suggestion would violate any of the above

Say so explicitly in chat rather than silently complying — e.g. "this would touch 11 files, over
the phase's 8-file budget; want me to split it?" is the expected response, not a workaround.
