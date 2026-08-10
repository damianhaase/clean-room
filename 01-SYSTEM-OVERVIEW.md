# 01 — System Overview (platform-agnostic)

## 1. The two-layer model

```
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER 1 — The package manager (a small CLI, installed once)                │
│   • Installed via the host language's package installer (pip / npm / …).   │
│   • Its ONLY job at runtime: download the content library from a git host  │
│     and copy files into the IDE's well-known folders.                      │
│   • Ships a stdlib-only ENGINE used as offline CI gates:                    │
│        – deterministic lexical ROUTER + eval RUNNER                         │
│        – handoff-payload SCHEMA VALIDATOR                                   │
└──────────────────────────────────────────────────────────────────────────┘
                     │  shallow git clone of a branch/tag
                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER 2 — The content library (markdown, not code)                          │
│   • skills/   → deterministic single-task workflows (SKILL.md + resources) │
│   • agents/   → role orchestrators (.agent.md) + shared invariants + schema│
│   • prompts/  → slash-command dispatchers & templates (.prompt.md)         │
│   Read at runtime by GitHub Copilot / Claude / IntelliJ AI assistants.     │
└──────────────────────────────────────────────────────────────────────────┘
```

**Why two layers (CR-OV-001).** The CLI rarely changes; the content changes often. Splitting them
lets `update` refresh content **without** re-running the language package installer — which avoids
the Windows self-lock you get when a running executable tries to overwrite itself, and lets content
ship on its own cadence.

## 2. Actors

| Actor | Role |
|---|---|
| **Developer (end user)** | Installs the CLI once, deploys content, then invokes skills/agents from their IDE's AI chat. Approves at pipeline gates. |
| **Skill author** | Uses the dev-only meta-skills to create/validate new skills, agents, prompts. |
| **CI system** | Runs `route-score`, `eval`, `validate-handoff`, and budget checks on every PR — no network, no LLM. |
| **AI assistant** | Reads the deployed markdown and executes the procedures; the *runtime* that "runs" skills/agents. |

## 3. The content taxonomy

| Kind | File | Count | What it is |
|---|---|---|---|
| **Skill** | `SKILL.md` (+ `references/`, `steps/`, `scripts/`, `templates/`) | 34 | A self-contained, budgeted procedure for one task (e.g. "code review", "generate Java tests"). Deterministic; the AI must load it before acting. |
| **Agent** | `<name>.agent.md` | 9 | A role orchestrator that *wraps* one or more skills and emits a typed handoff payload. 1 coordinator + 7 SDLC roles + 1 KB companion. |
| **Prompt** | `<name>.prompt.md` | 13 | A thin slash-command entry: 9 agent dispatchers + 1 goal-decomposition + 1 phase-approval + 1 coverage-report template (plus the coordinator dispatcher). |

Every skill and agent ships a paired `eval_queries.json` (positive + negative routing examples).

## 4. Distribution & deployment model (CR-OV-002)

- Users do **not** clone the content repo. The CLI **fetches it from the git host at runtime**
  (`install` / `update`) via a shallow clone of a resolved ref (branch or tag).
- Deploy targets (defaults; all overridable):
  - **skills** → user-level `~/.agents/skills/`
  - **agents** → `~/.copilot/agents/` (or `<repo>/.github/agents/` in repo mode)
  - **prompts** → the IDE's user-prompts dir (or `<repo>/.github/prompts/` in repo mode)
- A **deploy-state cache** file inside the skills target records `{ref, commit, deployed_at}` so
  `update --check` can compare the deployed commit against the remote **offline-friendly**.
- The build step of the CLI **bundles a copy** of the content into the installed package, but
  `install`/`update` **deliberately never fall back** to that bundle — a failed download is an
  error. (The bundle exists for `list`/`status`/`eval` discovery and dev installs.)

## 5. The value delivered to users

1. **One-command capability install.** `pip/npm install …` then `<CLI> install` puts dozens of
   reusable AI workflows into the IDE, discoverable as `/`-slash commands.
2. **Deterministic, repeatable AI.** Each skill is a fixed procedure; the AI loads it before
   acting, so output shape is reproducible run-to-run.
3. **A gated, end-to-end SDLC.** A single entry (`/<PREFIX>coordinator implement <TICKET>`) walks a
   ticket through Requirements → Design → Planning → Implementation → Test → Review → Release, with
   exactly **three human approval gates** and automatic revision loops.
4. **Safety by construction.** No auto-commit/push; only one agent (Release) may mutate git, only
   after the final gate; protected branches are never touched.
5. **Offline-checkable quality.** Routing accuracy and the inter-agent contract are CI gates that
   need no network or model.

## 6. Design principles to preserve (CR-OV-003)

- **Stdlib-only engine.** Layer-1 runtime dependencies are empty; heavy optionals (embeddings for
  the KB) sit behind an extra and always have a deterministic offline fallback.
- **Progressive disclosure.** A skill's `SKILL.md` stays small; heavy detail lives in
  `references/`, `steps/`, `templates/`, `scripts/`, loaded only when the workflow points to them.
- **Single sources of truth.** One handoff JSON Schema; one `_shared/agent-invariants.md`
  referenced by every agent; one deploy-state cache.
- **Deterministic before probabilistic.** Anything that *can* be a deterministic check (routing,
  schema, budgets) is one, so the probabilistic part (the LLM) has a smaller job.

## 7. Glossary

| Term | Meaning |
|---|---|
| **Base skills** | The small always-installed, never-removed-while-needed set (shell-env detection, saving-reports, jira-access, confluence-page-access). |
| **Excluded / dev skills** | Meta/authoring skills hidden from normal `list`/`install`, shown only with `--dev`. |
| **Managed prefix** | The `<PREFIX>` (e.g. `tds-`) that marks artifacts this tool owns; used by `clean` to find orphans. |
| **Deploy-state cache** | JSON file in the skills target recording the last deployed `{ref, commit, deployed_at}`. |
| **Router** | The deterministic text classifier mapping a query to exactly one agent. |
| **Handoff payload** | The typed record each SDLC phase emits to the coordinator; validated against one JSON Schema. |
| **Gate (G1/G2/G3)** | The three human approval points (after Design, Planning, Review). |
| **Mode** | `full` (new feature, all documents) or `lightweight` (small/bug fix, minimal documents). |
| **Phase** | One `PHASE-NNN` slice of implementation work (≤ 8 files, ≤ 400 code lines). |
