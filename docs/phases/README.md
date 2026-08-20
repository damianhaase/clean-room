# Phase tickets

One file per phase: `PHASE-NNN-<slug>.md`, copied from `../PHASE_TEMPLATE.md`.

| Phase | Title | Status |
|---|---|---|
| PHASE-001 | CLI scaffold + `--version` | done |
| PHASE-002 | Path resolution (per-OS targets) | done |
| PHASE-003 | `list` / `status` against fixture content dir | done |
| PHASE-004 | Download (shallow clone) + dir hash-diff | not-started |
| PHASE-005 | Deploy-state cache + `install` (no preserve logic) | not-started |
| PHASE-006 | Preserve-user-edits logic (agents/prompts) | not-started |
| PHASE-007 | `update`, `update --check`, `uninstall`, `clean` | not-started |
| PHASE-008 | Router: tokenizer + stemmer | not-started |
| PHASE-009 | Router: IDF-cosine scoring + calibration tables | not-started |
| PHASE-010 | Eval runner + `eval` / `route-score` commands | not-started |
| PHASE-011 | Handoff schema (full JSON-Schema mode) | not-started |
| PHASE-012 | Stdlib fallback validator + parity tests | not-started |
| PHASE-013 | `validate-handoff` CLI + YAML/JSON loader | not-started |
| PHASE-014 | Build hook + base-skill bundling | not-started |

Update this table's Status column as part of closing out each phase (AGENTS.md gate checklist).
Do not add rows for phases beyond content authoring until Milestone 4 is reached — see
`../specs/00-REVERSE-ENGINEERING-PLAN.md` §5.
