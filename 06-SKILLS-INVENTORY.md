# 06 — Skills Inventory (behavioral contracts, platform-agnostic)

34 skills. This file records each skill's **behavioral contract** — purpose, inputs, outputs,
guardrails, owned resources, and any script entry point — so you can **re-author** its `SKILL.md`
body from scratch (do not copy the original prose). Descriptions here are paraphrased contracts,
not the originals. All names use `<PREFIX>` (original `tds-`). Every skill ships an
`eval_queries.json` (positive/negative counts noted where they differ from ~10/10).

Legend: **B** = base (always installed), **X** = excluded/dev-only (hidden unless `--dev`),
**S** = ships a script entry point.

---

## Group A — Base skills (always installed) (CR-SK-A)

### `<PREFIX>shell-env-detection` — **B**
- **Purpose:** detect the active shell (Linux bash, Git Bash on Windows, PowerShell, CMD) at session
  start and record it for all other skills.
- **Inputs:** probe commands (`pwd`, `uname -s`, version checks). **Output:** a stored
  `DETECTED_SHELL` value + a command-translation table so every other skill emits correct syntax.
- **Guardrails:** run before any terminal command; documentation-only (no scripts).

### `<PREFIX>saving-reports` — **B**
- **Purpose:** decide where under `ai_generated_docs/` to save reports/docs/analyses, with proper
  categorization and folder structure.
- **Behavior:** categorize into `ai_generated_docs/<category>/`; create the category folder + a
  README when needed; apply a house theme; **never** save to project root.

### `<PREFIX>jira-access` — **B, S**
- **Purpose:** the **only** authenticated ticket-tracker client; other skills delegate ticket reads
  here.
- **Behavior:** resolve `JIRA_TOKEN` + `JIRA_BASE_URL` (halt if missing); GET an issue with full
  fields; resolve epic/parent link; map into a reusable `jira_context` record; derive epic/ticket
  slugs; **behind a confirmation gate**, PUT an updated description back.
- **Script:** `jira_io.py` with `main(argv)->int` (GET/PUT, error handling, slug derivation). It is
  the sole caller of this helper.

### `<PREFIX>confluence-page-access` — **B**
- **Purpose:** authenticated **read-only** wiki page access.
- **Behavior:** resolve `CONFLUENCE_TOKEN` + `CONFLUENCE_BASE_URL` (halt if missing); resolve a page
  by id-from-URL or title+space search; fetch body/title/version; strip storage-format HTML to
  plain text; map to a `page_context` record. **Never** edits/comments/creates.

## Group B — Code generation (CR-SK-B)

### `<PREFIX>generate-java-tests`
- **Purpose:** generate **or edit** JUnit 5 tests following BDD (Given-When-Then) with Mockito.
- **Behavior:** `@ExtendWith(MockitoExtension.class)`, `@Mock`, `var` (final only on request),
  naming `methodName_StateUnderTest_ExpectedResult`; complies with `format-local-variables`; works
  on the open Java file / files under test. Independent-mode variant used by the Test agent.

### `<PREFIX>generate-frontend-tests`
- **Purpose:** generate/edit Jest + React Testing Library tests for React/TS components (BDD).
- **Behavior:** Given-When-Then via RTL; custom render wrapper; `jest.mock()` + `userEvent`;
  snapshot testing; targets `*.test.tsx|*.spec.tsx|*.test.ts|*.spec.ts`.

### `<PREFIX>generate-jira-description`
- **Purpose:** draft ticket descriptions in the house "CLEAR" format; optionally estimate points.
- **Modes:** *show standards* (load estimation guidelines: points↔time, backend/frontend by point
  value, external-dependency overhead), *generate* (draft from requirements), *combined*.
- **Resources:** `references/ESTIMATION_GUIDELINES.md` + a description template.

### `<PREFIX>generate-mermaid-diagrams`
- **Purpose:** produce readable Mermaid diagrams (sequence, flowchart, state, ER, gantt).
- **Behavior:** house color palette, ≥18px font, dark-note backgrounds, consistent theming +
  visibility rules. **Resources:** `references/{COLOR_AND_THEME,TEMPLATES_AND_PATTERNS,
  TROUBLESHOOTING_AND_CHECKLIST}.md`.

### `<PREFIX>create-skill` — **X**
- **Purpose:** scaffold a new `SKILL.md` per the Agent Skills spec.
- **Behavior:** confirm target folder; gather purpose/inputs/outputs/use-cases/platforms; generate
  frontmatter + body + `eval_queries.json` + folder structure; apply project rules if an `AGENTS.md`
  exists. **Ships a frozen copy of the spec** under `references/`.

### `<PREFIX>create-agent` — **X**
- **Purpose:** scaffold a `.agent.md` per the Custom Agents spec.
- **Behavior:** gather mission/tools/wrapped-skills/dispatch; generate frontmatter + body + eval
  queries; **mandatorily run `agents-validation`** and refuse to exit on FAIL. `references/` holds a
  frozen spec; `steps/` holds scaffolding steps.

### `<PREFIX>create-prompt` — **X**
- **Purpose:** scaffold a `.prompt.md` per the Prompt Files spec.
- **Behavior:** gather purpose/inputs/expected-output/mode; generate frontmatter + body + eval
  queries; **mandatorily run `prompts-validation`** and refuse to exit on FAIL.

## Group C — Code quality (CR-SK-C)

### `<PREFIX>code-review`
- **Purpose:** structured review of a git diff vs a resolved parent (upstream → origin/`<DEV_BRANCH>`
  → `<DEV_BRANCH>`), covering staged/unstaged/untracked.
- **Focus:** SOLID & architecture boundaries, removal candidates, security risks, maintainability.
- **Guardrails:** **review-only** by default (no code changes unless the user asks); warn if the
  compare base isn't the dev branch. **Resources:** SOLID/architecture references, length-smell
  examples, quick reference.

### `<PREFIX>format-local-variables`
- **Purpose:** refactor Java locals to `var` (Java 10+) with readable names; inline one-use vars.
- **Behavior:** `var` without `final` by default (`final var` only on request); does **not** touch
  fields/params/return types/array inits without inference. Used as the **FR-018 post-step** by the
  Implementation agent. **Resource:** `FINAL_VAR_RULE.md`.

## Group D — Git workflow (CR-SK-D)

### `<PREFIX>git-commit-message`
- **Purpose:** build a `<TICKET_RE>`-prefixed commit message from the branch name + a change
  summary (`git status --short` + `git diff --stat`) and present a ready-to-run command.
- **Guardrail:** **never executes** the commit — user runs it.

### `<PREFIX>git-rebase`
- **Purpose:** safe, step-by-step rebase of a feature branch onto its resolved parent; interactive
  squash/reword/drop; conflict guidance.
- **Guardrails:** mandatory approval gates before destructive actions; **hard stop** when on
  `<DEFAULT_BRANCH>`/`<DEV_BRANCH>`; explicitly not for merge/cherry-pick/branch-creation/pushing to
  protected branches.

## Group E — Docs / extraction (CR-SK-E) — most ship a script (**S**)

Each converts a source document to markdown/text under `ai_generated_docs/`, applies the house
theme, and reuses a bundled script (`main()` entry point) rather than rebuilding it each run.
Typical eval counts 8/8.

| Skill | Input → Output | Script |
|---|---|---|
| `<PREFIX>extract-email-to-md` **S** | Outlook `.msg` → markdown; saves attachments; **routes attachments to the matching extract skill** | `extract_msg_to_markdown.py` |
| `<PREFIX>extract-excel-to-md` **S** | `.xlsx` → markdown; prompts for sheet selection; builds a sheet index with back-links when >1 | `extract_excel_to_markdown.py` |
| `<PREFIX>extract-image-to-text` **S** | image → OCR text; asks TXT vs Markdown first; layout-preserving | `extract_image_text.py` |
| `<PREFIX>extract-word-to-md` **S** | `.docx` → markdown (Mammoth, plain-text fallback); preserves headings/lists | `extract_word_to_markdown.py` |
| `<PREFIX>image-analysis` | image → described contents/labels/structured info; fallback for workflows needing image content | — (vision) |

## Group F — Infra / DevOps (CR-SK-F)

### `<PREFIX>dev-env-fix` — repair the workspace dev environment
- Verifies/repairs **Java** (VS Code `settings.json` + IntelliJ `misc.xml`; cross-check pom version;
  find matching JDK), **Python venv** (create/health-check/rebuild), **Node** (match `.nvmrc`/engines),
  and **CLI tools** (`gh`, `jq` via winget). Uses shell-env-detection for correct syntax.

### `<PREFIX>jar-creation` — **S**
- Prepare a JAR release: set up venv, install deps, **update pom version** for major releases,
  **disable auto-deployment** (CDProperties). Scripts: `update_version.py`, `toggle_cdproperties.py`.

### `<PREFIX>toggle-auto-deployment` — **S**
- Enable/disable/check a `CDProperties:` block in a component YAML (comment/uncomment).
  Script: `toggle_cdproperties.py`.

### `<PREFIX>release-preparation` — **S**
- Update deployment YAML (`EDP.yml` + component files): activate apps/datacenters, bump versions,
  set binary URLs. **Files-only** — presents git commands and waits for approve/skip. Script:
  `prepare_release.py`.

## Group G — Project management / SDLC core (CR-SK-G)

### `<PREFIX>requirements-package`
- **Purpose:** gather/scaffold/generate/review/validate/reformat modular **requirements packages**;
  also **catalog open PR review comments** into one table for G1 sign-off.
- **Templates:** tiny (default), standard, full. **Resources:** `steps/`, `templates/`. Grounded in
  the KB + domain.

### `<PREFIX>solution-package`
- **Purpose:** create a **solution design package** from a golden template (18 sections / 9 parts),
  grounded in the requirements package + KB.
- **Lifecycle:** technical interview → scaffold → generate chunk-by-chunk → review → validate →
  reformat. **Resources:** `steps/`, `templates/`.

### `<PREFIX>implementation-planning`
- **Purpose:** create/scaffold/review/validate an **Implementation Package** using a *Canonical
  Phase Shape* (8 mandatory sections per phase). Supports **Jira-ticket-direct** (fetch ticket, log
  a bug into an existing plan, or scaffold a lightweight bug-fix phase).
- **Outputs:** `IMPLEMENTATION-INDEX.md`, `00-CHANGELOG.md`, `PHASE-NNN-<name>.md`, `phase-status.md`,
  `bugs-and-issues-log.md`.

### `<PREFIX>implementation-execution`
- **Purpose:** execute one phase via a *Phase Execution Guide*: phase education → game plan →
  checklist → definition of done → test-coverage requirements → branch creation → code → manual test
  plan + bug capture → commit workflow.
- **Guardrail:** **never auto-commits**; waits for explicit "go" to start and "approved" to commit.
  Integrates the FR-018 format post-step.

### `<PREFIX>spec-driven-development`
- **Purpose:** a self-contained multi-phase workflow (Requirements → Design → Planning → Development
  → Review → Handoff) with **approval gates**, task state under `docs/tasks/`. **Resources:**
  `ORCHESTRATOR.md`, templates. (A skill-level analogue of the agent pipeline.)

### `<PREFIX>kb-universal`
- **Purpose:** universal, adapter-based **knowledge-base lifecycle** skill; operates in **SESSION
  MODE** (one topic at a time) keeping architecture + data model current.
- **Maintains:** `tracker.md`, `memory.md`, `versions.md`, `AGENTS.md`, `user-documents/`.
- **Ships a nested engine** `<PREFIX_pkg>_kb/` — see [12-KB-ENGINE-SPEC.md](12-KB-ENGINE-SPEC.md).
  Extensive `references/` (CLI-OPERATIONS, GUARDRAILS, INPUTS-OUTPUTS, PER-PROMPT-PROTOCOL,
  post-release-refresh, TYPE-ENUMS, WORKFLOW-DETAIL, …), `steps/`, `templates/`.

## Group H — External access
Covered in Group A (`jira-access`, `confluence-page-access`) — they are base skills other skills
delegate to. Point them at **your** endpoints.

## Group I — Meta / validation (mostly **X**) (CR-SK-I)

### `<PREFIX>skills-validation` — **X, S**
- Validate skill packages vs the spec + repo rules (frontmatter, README freshness, eval-query
  presence, slash discoverability, base-skill integration, structure). Script: `validate_skills.py`.

### `<PREFIX>agents-validation` — **X**
- Validate `.agent.md` vs the Custom Agents spec + orchestration rules (see file 05 §7). **Exit
  0/PASS, non-zero/FAIL.**

### `<PREFIX>prompts-validation` — **X**
- Validate `.prompt.md` vs the Prompt Files spec + body conventions. **Exit 0/PASS, non-zero/FAIL.**

### `<PREFIX>agent-skills-spec` — **X**
- Maintain a local mirror of the three upstream specs (Agent Skills, Custom Agents, Prompt Files)
  under `skills/skills_spec/`; fetch → stage for human review → merge. Project-scoped.

### `<PREFIX>dev-env-fix`
- (Listed in Group F.) Not excluded; repairs the environment.

---

## Classification summary (CR-SK-Z)

| Set | Members |
|---|---|
| **Base** (always installed) | shell-env-detection, saving-reports, jira-access, confluence-page-access |
| **Excluded / dev-only** | create-skill, create-agent, create-prompt, skills-validation, agents-validation, prompts-validation, agent-skills-spec |
| **Ship a script** | jira-access, extract-email/excel/image/word, jar-creation, toggle-auto-deployment, release-preparation, skills-validation |
| **SDLC core (wrapped by role agents)** | requirements-package, solution-package, implementation-planning, implementation-execution, generate-java-tests, generate-frontend-tests, generate-mermaid-diagrams, code-review, format-local-variables, git-commit-message, git-rebase, jar-creation, release-preparation, kb-universal, generate-jira-description, skills-validation |

## Re-authoring guidance (CR-SK-Y)
Most skills are **generic engineering tasks** you can re-derive from public best practices — SOLID/
OWASP, Conventional Commits, JUnit/Mockito docs, React Testing Library, Mermaid docs, the Agent
Skills/Custom Agents/Prompt Files specs. Only the **domain-specific** ones (the CLEAR requirements/
solution/implementation packages, release-preparation's YAML shapes, the estimation guidelines) need
your own domain input. Point all external-access skills at **your** Jira/Confluence/GitHub.
