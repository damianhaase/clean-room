# Phase tickets

One file per phase: `PHASE-NNN-<slug>.md`, copied from `../PHASE_TEMPLATE.md`.

| Phase | Title | Status |
|---|---|---|
| PHASE-001 | CLI scaffold + `--version` | done |
| PHASE-002 | Path resolution (per-OS targets) | done |
| PHASE-003 | `list` / `status` against fixture content dir | done |
| PHASE-004 | Download (shallow clone) + dir hash-diff | done |
| PHASE-005 | Deploy-state cache + `install` (no preserve logic) | done |
| PHASE-006 | Preserve-user-edits logic (agents/prompts) | done |
| PHASE-007 | `update`, `update --check`, `uninstall`, `clean` | done |
| PHASE-008 | Router: tokenizer + stemmer | done |
| PHASE-009 | Router: IDF-cosine scoring + calibration tables | done |
| PHASE-010 | Eval runner + `eval` / `route-score` commands | done |
| PHASE-011 | Handoff schema (full JSON-Schema mode) | not-started |
| PHASE-012 | Stdlib fallback validator + parity tests | not-started |
| PHASE-013 | `validate-handoff` CLI + YAML/JSON loader | not-started |
| PHASE-014 | Build hook + base-skill bundling | not-started |

## Note on route-score / eval CI gates

PHASE-010 implements `eval` and `route-score` correctly (auto-discovery of
`content/agents/*.agent.md` paired with `*.eval_queries.json`, per CR-CLI-007/018/019).
Their CI jobs in `.github/workflows/ci.yml` stay disabled (`if: false`) until one of:
- Milestone 4 content authoring begins and `content/agents/` has real agents, or
- a committed fixture agents dir (e.g. `tests/fixtures/agents/`) is added and the
  workflow is pointed at it via `--agents-dir` for an earlier, CI-only signal.
Do not flip these jobs to `if: true` without one of the above in place — see PHASE-010's
notes for what happened when this was done prematurely.

Update this table's Status column as part of closing out each phase (AGENTS.md gate checklist).
Do not add rows for phases beyond content authoring until Milestone 4 is reached — see
`../specs/00-REVERSE-ENGINEERING-PLAN.md` §5.
