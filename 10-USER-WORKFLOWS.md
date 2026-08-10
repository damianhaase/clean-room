# 10 — User Workflows (how users use it, end-to-end)

This file reconstructs **what the system does for users and how they use it**. Commands use
`<CLI>` (original `tds-skills`) and `<PREFIX>` (original `tds-`). Behaviors tagged `CR-UX-NNN`.

---

## Journey 1 — Install the CLI (one-time per machine) (CR-UX-001)

- Install the package manager once with the host language's installer, pointed at the content repo:
  `pip install "git+https://<REPO_URL>.git@<DEFAULT_BRANCH>"` (or the npm/etc. equivalent in a TS
  port). This installs **the CLI only** and runs the build hook, which:
  - bundles the content into the package,
  - **auto-installs the base skills** into `~/.agents/skills/` (skipping any already present),
  - adds `ai_generated_docs/` to the user's global gitignore.
- Verify: `<CLI> --help`, `<CLI> status`.
- Windows: open a **new terminal** so PATH updates take effect (the CLI adds the per-user Scripts
  dir to `HKCU\Environment\Path`).
- **Mental model:** `pip/npm install …` = install the CLI (rare). `<CLI> …` = manage content
  (frequent). Content updates never re-run the package installer.

## Journey 2 — Install the content (CR-UX-002)

- **VS Code (default):** `<CLI> install --force`
  - skills → `~/.agents/skills/`; agents → `~/.copilot/agents/`; prompts → the IDE user-prompts dir.
  - Copilot Chat auto-discovers agents and prompts from these locations.
- **IntelliJ (repo-scoped):** `cd <project> && <CLI> install --repo --force`
  - skills stay user-level; agents → `<repo>/.github/agents/`; prompts → `<repo>/.github/prompts/`;
    both added to `<repo>/.gitignore`.
- Options: `--force` (overwrite), `--dry-run` (preview), `--dev` (include authoring tools),
  `--ref <branch|tag>` (pin), `--target/--agents-target/--prompts-target` (override destinations).

## Journey 3 — Configure credentials & IDE (only if needed) (CR-UX-003)

Credentials are required **only** for skills/agents that touch external systems; the system halts
and points to the credentials guide when one is missing.

| System | Env vars | Used by |
|---|---|---|
| Ticket tracker (Jira) | `JIRA_TOKEN` (required), `JIRA_BASE_URL` (default `<JIRA_BASE>`) | requirements, planning, implementation-planning |
| Wiki (Confluence) | `CONFLUENCE_TOKEN`, `CONFLUENCE_BASE_URL` (default `<CONF_BASE>`) | implementation-planning, kb-universal |
| Git host | `gh auth login` (GitHub CLI) | release, git-rebase |

- Set per-shell (`export`/`$env:`) or persist (`~/.bashrc`, `[Environment]::SetEnvironmentVariable`).
- **Security rules:** never paste tokens into chat; never write them to committable files; rotate
  regularly; use minimal scopes.
- IDE: VS Code needs no extra config; IntelliJ auto-detects `.github/agents|prompts` after the repo
  install; other assistants (Claude, hosted Copilot) can `load ~/.agents/skills/<skill>/SKILL.md`
  directly since skills are plain markdown + optional scripts.

## Journey 4 — Invoke a single skill (ad-hoc, no gates) (CR-UX-004)

1. Start the skill by slash command, then state the task in natural language:
   ```
   /<PREFIX>code-review
   review my changes
   ```
2. Fallback when slash commands aren't available: `load ~/.agents/skills/<PREFIX>code-review/SKILL.md`
   then the request.

Representative single-skill uses: code review; generate Java/frontend tests; format local
variables; draft a commit message; rebase; generate a Mermaid diagram; save a report; extract
image/Excel/Word/email to markdown; prepare a release / build a JAR; toggle deployment.

**Safety:** skills show diffs and never auto-commit; the user runs `git add`/`git commit` after
review; skills stay on feature branches and never push to protected branches.

## Journey 5 — Run the full multi-agent SDLC pipeline (CR-UX-005)

1. Entry: `/<PREFIX>coordinator implement <TICKET>` (or a free-text goal).
2. The coordinator produces a **routing plan** (goal-decomposition) and asks you to approve/revise/
   abort, choosing `mode: full` or `lightweight`.
3. It then runs the seven phases (file 09) and pauses at **G1** (after Design), **G2** (after
   Planning), **G3** (after Review). Reply `approved` / `revise <reason>` / `abort` at each.
4. Between gates, boundaries auto-progress; Test/Review failures auto-loop back to Implementation
   (≤ 3 cycles/phase). Oversized phases bounce to Planning and re-fire G2.
5. After G3, Release runs commit→push→PR (each git command needs an explicit per-call `approved`),
   then the KB refresh runs under the same G3.
6. Multi-phase tickets repeat Implementation→Test→Review→Release per phase.

**Direct entry / resume:** invoke any agent directly (e.g. `/<PREFIX>planning <TICKET>`); it
backfills missing upstream artifacts (with confirmation) before proceeding — useful to resume a
crashed run mid-pipeline.

## Journey 6 — Build & use the knowledge base (CR-UX-006)

- Build: `/<PREFIX>kb-universal` then "build the KB" (or `<PREFIX>kb build`). The **markdown tier**
  (curated digest) always works and provides the token savings; the **vector tier** (embeddings) is
  optional and falls back to a deterministic stub embedder when the `[generate]` extras/model aren't
  available.
- **Auto-refresh:** at session start and on KB load, a cheap `git fetch <DEV_BRANCH>` checks each
  topic's last-indexed commit; only drifted topics regenerate. Configure via `kb-config.yml`
  (`auto_refresh.mode: prompt|auto|off`).
- **KB-first discovery:** discovery skills read the KB first, scan the codebase only as a narrow
  fallback, and surface gaps rather than broadening the search — keeping context small.

## Journey 7 — Maintain & update (CR-UX-007)

| Task | Command |
|---|---|
| Check for updates (read-only) | `<CLI> update --check` |
| Update content (main) | `<CLI> update` |
| Update from dev branch | `<CLI> update --dev` |
| Pin to a tag/branch | `<CLI> update --ref <ref>` |
| Update one skill | `<CLI> update <skill>` |
| See deployed commit | read `~/.agents/skills/.<CLI>-deploy.json` |
| Upgrade the CLI itself (rare) | `pip install --upgrade "git+https://<REPO_URL>.git@<DEFAULT_BRANCH>"` |
| List content | `<CLI> list [--agents] [--dev]` |
| Remove orphans | `<CLI> clean` |

Content updates never touch the CLI package (no Windows self-lock). Start a new chat session after
updating so the IDE reloads frontmatter. `status`/`update --check` auto-detect and print the exact
CLI-upgrade command when a newer CLI exists.

## Journey 8 — Team workflow (CR-UX-008)

- New member: `pip install "git+https://<REPO_URL>.git@<DEFAULT_BRANCH>" && <CLI> install --force`.
- Weekly: everyone runs `<CLI> update`.
- Test a proposed change: `<CLI> update --ref <branch>`; pin with `--ref <tag>` in CI.
- Mixed VS Code + IntelliJ teams: run both `<CLI> install --force` (user-level) and
  `<CLI> install --repo --force` (repo-level); skills are shared, agents/prompts duplicated.

## Journey 9 — Troubleshooting (reveals functional behaviors) (CR-UX-009)

| Symptom | Cause → fix |
|---|---|
| Slash commands not recognized | not installed → `<CLI> install --force`; IDE cache → restart / new chat; client lacks slash → `load …/SKILL.md` |
| `FileNotFoundError: <script>.py` | skill missing → `<CLI> install --force <skill>` |
| Skills "keep reloading" | expected — each new chat reloads skills |
| Agent halts "TOKEN not set" | set the env var (Journey 3) and verify |
| Agent changed files but didn't commit | **correct** — review the diff and commit manually |
| "Oversized phase" handback | expected — Planning re-splits, G2 re-fires |
| Revision-cap hit after 3 cycles | adaptive escalation — accept re-route / approve-as-is / abort / extend one |
| KB drift flagged | auto-refresh prompts; silence with `auto_refresh.mode: auto` |

## 10 — Reference/spec directories users may see (CR-UX-010)

`skills/skills_spec/` mirrors the three upstream format specs; `skills/skills_rules/` holds the
mandatory execution rules (no auto-commit; protected branches); `skills/ai-model2-spec*/` hold the
requirements/solution/implementation package **templates** (canonical phase shape, reverse-
engineering guidance, and a lightweight "CLEAR" variant) that the SDLC skills consume.
