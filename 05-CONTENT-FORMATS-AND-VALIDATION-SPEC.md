# 05 — Content Formats & Validation Spec (platform-agnostic)

The content library is markdown with YAML frontmatter. The **formats are public specifications**
(safe to reproduce); the **content is proprietary** (re-author it). This file specifies the formats,
the budgets, and the validation rules the meta-skills enforce. Behaviors are tagged `CR-FMT-NNN`.

---

## 1. Where the formats come from (public sources) (CR-FMT-001)

| Artifact | Public specification | Rules to reproduce |
|---|---|---|
| **Skill** `SKILL.md` | Agent Skills spec — agentskills.io (also Anthropic "Agent Skills") | YAML frontmatter `name` + `description`; markdown body; progressive disclosure via `references/`, `steps/`, `scripts/`, `templates/`. |
| **Agent** `.agent.md` | VS Code Custom Chat Agents / chat modes | frontmatter `name`, `description`, `tools:` list; invoked by slash command matching the name. |
| **Prompt** `.prompt.md` | VS Code Prompt Files | frontmatter (`agent`/`mode`, `description`); reusable body; `/name` invocation. |
| **Handoff payload** | JSON Schema Draft 2020-12 — json-schema.org | see file 04. |

The original mirrors these under `skills/skills_spec/`; for a clean-room build, go to the upstream
sources directly. A dev-only meta-skill (`<PREFIX>agent-skills-spec`) keeps a local mirror synced.

## 2. Skill format `SKILL.md` (CR-FMT-002)

```markdown
---
name: <PREFIX>code-review
description: >
  <one paragraph, 0 < len ≤ 1024 chars. State WHAT it does + WHEN to use it.
  Pack trigger phrases here — the router reads THIS field.>
---

# SKILL: <Title>

## Quick Prompts                 # slash command + trigger phrases (mirror eval_queries.json)
## Summary                       # what it produces
## When to Use
## Inputs
## Guardrails (Non-Negotiable)   # e.g. review-only, never auto-commit
## Workflow                      # numbered steps; route to steps/ and references/ on demand
## Output format                 # the deterministic output template
```

**Budgets enforced by validation (CR-FMT-003):**
- `SKILL.md` ≤ **500 lines** → **hard error**.
- `SKILL.md` ≤ **~5000 tokens** (estimate = chars / 4) → **warning**.
- `description` length: `0 < len ≤ 1024` chars.
- **Progressive disclosure:** verbose detail lives in `references/*.md`, `steps/NN-*.md`,
  `templates/`, `scripts/`; the body loads them only when its workflow points to them.

**Optional owned resources:**
- `references/` — load-on-demand checklists/templates/policy.
- `steps/NN-*.md` — numbered sub-procedures.
- `scripts/*.py` (or `.ts`) — helper programs with a `main(argv) -> int` entry point (see §6).
- `templates/` — output templates.
- `README.md` — human-facing doc.

## 3. Agent format `.agent.md` (CR-FMT-004)

```markdown
---
name: <PREFIX>coordinator
description: >
  <≤ ~1500 chars. Mission + trigger phrases + the hard rules the router keys on.
  Keep within budget by referencing _shared/agent-invariants.md instead of restating.>
tools: ['search','read','edit','execute','web','vscode/askQuestions','agent', …]
---

# Mission
# Core Rules (non-negotiable)     # e.g. coordinator never authors code
# Wrapped Skills                  # table: which skills this agent loads
# Workflow / dispatch order
# Handoff payload                 # must conform to the JSON Schema (file 04)
```

**Budgets & rules (CR-FMT-005):**
- `description` soft cap **~1500 chars** (validation flags oversize).
- Body must **reference** `_shared/agent-invariants.md` (not restate the invariants).
- Body must reference the shared **self-check** and record an **`eval_score`** in its handoff.
- **No conflict markers** (`<<<<`, `====`, `>>>>`) anywhere.
- Agent `name` must equal the file stem.

## 4. Prompt format `.prompt.md` (CR-FMT-006)

```markdown
---
agent: agent            # or `mode:`
description: <one line>
tools: [...]            # optional
---

## Inputs               # placeholders the prompt expects
## Expected Output      # what invoking it yields
<body: dispatch to an agent via runSubagent, or a reusable template>
```

Two kinds: **dispatchers** (forward verbatim to an agent) and **utility templates**
(goal-decomposition, phase-approval, coverage-report). See file 08.

## 5. `eval_queries.json` (CR-FMT-007)

A JSON array of `{ "query": <str>, "should_trigger": <bool> }`. Conventions:
- Skills: paired with each `SKILL.md`; used by the router regression.
- Agents: paired with each `.agent.md`; **≥ 10 positive + ≥ 5 negative** queries each.
- Positive queries must route to the owning agent; negatives must not. Write your **own** queries
  for your reworded descriptions — do not copy the originals, and never edit them to force a pass
  (tune calibration instead; file 03).

## 6. Skill script entry points (CR-FMT-008)

Skills that ship executable helpers expose a `main(argv) -> int` (Python) / equivalent CLI, driven
via `<CLI> run <skill> [args]` (file 02 §6.11). The resolver maps `<skill>` to the module by trying
the literal name then stripping known prefixes. Skills with scripts in the original:
`jira-access` (`jira_io.py`), the four `extract-*` skills, `jar-creation` (`update_version.py`,
`toggle_cdproperties.py`), `toggle-auto-deployment`, `release-preparation` (`prepare_release.py`),
`skills-validation` (`validate_skills.py`). Details in file 06.

## 7. Validation rules the meta-skills enforce (CR-FMT-009)

| Meta-skill | Validates | PASS/FAIL contract |
|---|---|---|
| `<PREFIX>skills-validation` | `SKILL.md` frontmatter quality, budgets, README freshness, eval-query presence, base-skill integration, package structure | report + violations |
| `<PREFIX>agents-validation` | `.agent.md` vs Custom-Agents spec + repo conventions + orchestration rules: file under `agents/`, name==stem, **Implementation agent declares the FR-018 format post-step**, **Design/Planning/Implementation declare the FR-019 coverage post-step**, **coordinator has no hard-coded skill list**, every agent declares branch-protection/no-auto-commit/no-force-push | **exit 0 PASS / non-zero FAIL** |
| `<PREFIX>prompts-validation` | `.prompt.md` vs Prompt-Files spec: frontmatter (`agent`/`tools`/`description`), body has `## Inputs` + `## Expected Output`, file under `prompts/`, no name collisions | **exit 0 PASS / non-zero FAIL** |

The `create-*` meta-skills **must run the matching validator** on their output and refuse to exit
on FAIL (CR-FMT-010).

## 8. Repo layout to reproduce (CR-FMT-011)

```
content/
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md
│       ├── eval_queries.json
│       ├── references/ · steps/ · scripts/ · templates/   (optional)
│       └── README.md
├── agents/
│   ├── <agent>.agent.md
│   ├── <agent>.eval_queries.json
│   ├── _shared/agent-invariants.md          # single source of shared rules
│   └── schemas/handoff-payload.schema.json  # file 04
└── prompts/
    ├── <name>.prompt.md
    └── <name>.eval_queries.json
```

## 9. Authoring hygiene (CR-FMT-012)

- Descriptions carry the routing signal — pack the *intent* of the trigger phrases there (reworded).
- Keep bodies deterministic (numbered steps, fixed output templates) so AI output is repeatable.
- One responsibility per skill; compose skills via agents, not by bloating a skill.
- Every skill/agent gets an `eval_queries.json`; CI runs `route-score` + budgets on every PR.
