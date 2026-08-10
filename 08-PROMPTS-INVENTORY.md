# 08 — Prompts Inventory (platform-agnostic)

13 `.prompt.md` files. All are **thin** — they route to an agent via a subagent call or provide a
reusable template. **No prompt does SDLC work itself.** Two kinds: **dispatchers** (9) and **utility
templates** (3). Each pairs with an `eval_queries.json`. Behaviors tagged `CR-PR-NNN`.
(The original names the goal-decomposition + phase-approval + coverage-report prompts as the 3
utility templates and one dispatcher per agent including the coordinator ⇒ 9 dispatchers, plus the
coordinator entry sometimes counted separately; treat the set below as canonical.)

---

## 1. Agent dispatchers (CR-PR-DISP)

One thin prompt per agent. Contract for every dispatcher:
- Frontmatter: `agent: agent` (or `mode:`), a one-line `description` carrying the trigger intent.
- Body: **forward the user's text verbatim** to the named agent via the runtime's subagent
  mechanism; **do not do the work in the prompt**; return the agent's reply verbatim.

| Prompt | Dispatches to | Forwarded context (intent) |
|---|---|---|
| `<PREFIX>coordinator.prompt.md` | coordinator | the goal (Jira id / feature title / PRD link / RFC excerpt); coordinator owns dispatch order, mode propagation, gates |
| `<PREFIX>requirements.prompt.md` | requirements | goal; agent picks full/lightweight and sets `mode` |
| `<PREFIX>design.prompt.md` | design | goal + Requirements package path; honors upstream `mode`; G1 |
| `<PREFIX>planning.prompt.md` | planning | goal + Solutions path; G2 |
| `<PREFIX>implementation.prompt.md` | implementation | goal + phase id; FR-018 + FR-019 gate handoff to Test |
| `<PREFIX>test.prompt.md` | test | goal + phase id/branch; independent tests + full-suite gate |
| `<PREFIX>review.prompt.md` | review | goal + diff target; SOLID/security review; G3 |
| `<PREFIX>release.prompt.md` | release | goal + target branch/version; per-call git approval |
| `<PREFIX>kb.prompt.md` | kb | goal + optional jira/phase/slug; verify→re-index; zero git |

## 2. Utility templates (CR-PR-UTIL)

### `<PREFIX>goal-decomposition.prompt.md`
- **Role:** coordinator-side. Decompose one user goal into a **routing plan** before any dispatch.
- **Inputs:** `{user_goal}` + `{skill_catalog}` (discovered from `~/.agents/skills/` at run time).
- **Behavior:** detect entry shape (Jira-only → lightweight; else full); build the fixed 7-phase
  list; pick wrapped skill(s) per phase from the catalog (never invent). **Output** a YAML block:
  ```yaml
  goal: "{user_goal}"
  mode: <full|lightweight>
  jira: <NUMBER|null>
  phases:
    - { phase: requirements, agent: requirements, skills: [...] }
    - ...  # all 7 phases
  notes: "<caveats>"
  ```
  Then ask "approve / revise / abort" before dispatching Requirements.

### `<PREFIX>phase-approval-prompt.prompt.md`
- **Role:** the standard gate prompt reused at G1/G2/G3 (and role-agent internal gates).
- **Inputs:** `{phase_id, agent_name, phase_summary, artifact_path, handoff_status, next_agent}`.
- **Behavior:** present summary + artifact + status; ask for exactly one of **approve** (advance to
  `{next_agent}`), **revise `<reason>`** (return to `{agent_name}`), **abort** (stop). Coordinator
  interprets and dispatches accordingly.

### `<PREFIX>coverage-report-template.prompt.md`
- **Role:** the FR-019 coverage report used by Design, Planning, Implementation.
- **Inputs:** `{phase, feature_slug, date, upstream_path, downstream_path}`.
- **Behavior:** generate `ai_generated_docs/reports/{phase}/{feature_slug}-{date}.md` with a table
  (upstream item | where covered | status ✅/⚠️/❌ | notes/waiver), a counts summary, and a handoff
  verdict. **Pass criterion:** zero ❌ (or each ❌ has `WAIVED: <reason> — <user> <date>`); block
  handoff otherwise.

## 3. Rules to preserve (CR-PR-RULES)

- Dispatchers must never embed the work — they only route. This keeps prompts trivially correct and
  lets the agent (which loads the skills) own behavior.
- Utility templates are injected by the coordinator/role agents at fixed points; keep their output
  shapes stable so downstream parsing (and the coverage gate) is deterministic.
- Prompt bodies must contain the `## Inputs` and `## Expected Output` sections the prompts-validator
  checks (file 05 §7).
