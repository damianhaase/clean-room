# 02 — Package-Manager CLI Spec (engine, platform-agnostic)

Layer 1 is a small CLI that discovers, downloads, and deploys the content library, and hosts the
offline gates. This file specifies **every command and mechanic** precisely enough to re-implement
in any language (argparse in Python, commander/yargs in TypeScript, cobra in Go, …).

All behaviors are tagged `CR-CLI-NNN`. Exit codes follow the UNIX/argparse convention: **0** = ok,
**1** = operation failed, **2** = usage/precondition error.

---

## 1. Packaging & entry points (CR-CLI-001)

- One console entry point maps `<CLI_NAME>` → the CLI `main()`.
- Optionally expose extra entry points for bundled sub-engines (the original also exposes a
  `<PREFIX>kb` and `<PREFIX>kb-query` script for the knowledge-base engine — see file 12).
- **Runtime dependencies MUST be empty** (stdlib only). Heavy optionals (embeddings) live behind an
  install extra (e.g. `[generate]`) and are only needed at KB *generation* time.
- A **build hook** runs at install time (see §9).

## 2. Global options (apply to most subcommands) (CR-CLI-002)

| Option | Default | Effect |
|---|---|---|
| `--target PATH` | user skills dir (§3) | Override the skills destination. |
| `--agents-target PATH` | user agents dir (§3) | Override the agents destination. |
| `--prompts-target PATH` | IDE user-prompts dir (§3) | Override the prompts destination. |
| `--repo [PATH]` | off | Route **agents & prompts** into `<repo>/.github/{agents,prompts}` and append those dirs to `<repo>/.gitignore`. Skills are **never** redirected. No value ⇒ use CWD; a value ⇒ that path. **Errors (exit 2)** if the location is not inside a git repo. |
| `--dry-run` | off | Print intended changes; write nothing. |
| `--version` | — | Print `<CLI_NAME> <version>` and exit 0. |

Ref-selection options (on `install`/`update`/`clean`/`status`):

| Option | Effect |
|---|---|
| `--dev` | Use the `<DEV_BRANCH>` (e.g. `develop`) **and** include excluded/dev-only skills. |
| `--ref REF` | Use a specific branch **or** tag. Takes precedence over `--dev`. |

**Ref resolution precedence (CR-CLI-003):** explicit `--ref` › `--dev` (⇒ `<DEV_BRANCH>`) ›
default `<DEFAULT_BRANCH>` (e.g. `main`).

## 3. Default deploy targets, per OS (CR-CLI-004)

| Artifact | Windows | macOS | Linux/other |
|---|---|---|---|
| skills | `~/.agents/skills/` | same | same |
| agents | `~/.copilot/agents/` | same | same |
| prompts | `%APPDATA%\Code\User\prompts` (fallback `~/AppData/Roaming/…`) | `~/Library/Application Support/Code/User/prompts` | `${XDG_CONFIG_HOME:-~/.config}/Code/User/prompts` |

With `--repo`: agents → `<repo>/.github/agents/`, prompts → `<repo>/.github/prompts/` (skills
unchanged). Only override targets the user did **not** pass explicitly.

## 4. Module constants to define (CR-CLI-005)

```
BASE_SKILLS          = { "<PREFIX>shell-env-detection", "<PREFIX>saving-reports",
                         "<PREFIX>jira-access", "<PREFIX>confluence-page-access" }
EXCLUDED_SKILLS      = { "<PREFIX>create-skill", "<PREFIX>skills-validation",
                         "<PREFIX>agent-skills-spec", "<PREFIX>create-agent",
                         "<PREFIX>create-prompt", "<PREFIX>agents-validation",
                         "<PREFIX>prompts-validation" }
MANAGED_PREFIXES     = ( "<PREFIX>", )           # e.g. ("dh-",)
LEGACY_PREFIXES      = ( "<OLD_PREFIX>", )       # prior names `clean` should also treat as orphans
SKILL_ALIASES        = { }                       # old-name -> canonical-name (emits deprecation warning)
ROUTE_SCORE_THRESHOLD = 0.95
DEPLOY_STATE_FILENAME = ".<CLI_NAME>-deploy.json"
REPO_GIT_HTTP        = "https://<REPO_URL>.git"
```

- **`BASE_SKILLS`** are always included in any install and cannot be uninstalled by name; they are
  auto-pruned only once no other managed skill remains.
- **`EXCLUDED_SKILLS`** are hidden from `list`/`status` and skipped by `install` unless `--dev`.
- These constants are **duplicated** in the build hook (it can't import the package being built) —
  keep the two copies in sync (CR-CLI-006).

## 5. Content discovery (CR-CLI-007)

Skills/agents/prompts are sourced in this precedence:
1. **Download override** — when a command is actively deploying from a fresh clone, use that
   checkout's `skills/{skills,agents,prompts}/`.
2. **Bundled copy** inside the installed package (wheel/npm package) — `_skills/`, `_agents/`,
   `_prompts/`.
3. **Repo layout** relative to the source tree — `skills/{skills,agents,prompts}/` (editable/dev
   installs).
If none exist, raise a clear "reinstall" error.

> The `eval`/`route-score` commands invert #1/#2: they prefer the **repo source** of agents so CI
> checks the *current* library, then the download, then the bundle.

## 6. Command surface — behavioral spec

### 6.1 `list [--skills|--agents|--prompts] [--dev]` (CR-CLI-010)
- No filter ⇒ list all three sections. Multiple sections ⇒ print a combined summary line.
- **Skills:** show each available skill with markers: `[installed]` if present in target, `*` for
  base skills, `[dev only]` for excluded (only shown with `--dev`). Print an installed count.
- **Agents:** list installed `*.agent.md` in the agents target, each with the skills it wraps
  (parsed from `skills:`/`tools:` frontmatter — inline `[a,b]` or block `- a` forms).
- **Prompts:** list installed `*.prompt.md` names.
- Always exit 0.

### 6.2 `install [names…] [--force] [--dev] [--ref REF]` (CR-CLI-011)
Deploys content from the resolved ref. Steps:
1. On Windows, best-effort add the per-user Scripts dir to `HKCU\Environment\Path` if missing
   (helps `pip --user` users) — skip in `--dry-run` except to print the intent.
2. Apply `--repo` override if set.
3. Resolve names: apply `SKILL_ALIASES` (warn on use); reject `EXCLUDED_SKILLS` by name unless
   `--dev` (exit 1); reject unknown names (exit 1). No names ⇒ all available.
4. **Always add `BASE_SKILLS`** even when a subset is requested.
5. For each skill dir: if destination exists and **not** `--force` ⇒ **skip** (report). If it
   exists and its **directory hash equals** the source hash ⇒ count **unchanged**, no write. Else
   remove + copy. Report new/overwritten/unchanged/skipped counts.
6. If **no specific names** were requested, also install agents & prompts (§6.10) and, in non-repo
   mode, clean up legacy install dirs; in repo mode, append the gitignore entries.
7. Print a final summary line describing whether changes were applied.
- `install` (remote) = wrap the above in a **download of the resolved ref**, then on success write
  the deploy-state cache. A download failure is an error (exit 1) — never fall back to the bundle
  (CR-CLI-012).

### 6.3 `update [names…] [--check] [--dev] [--ref REF]` (CR-CLI-013)
- Without `--check`: identical to `install` but **forces overwrite of content** (`--force` implied).
  Never touches the CLI package itself.
- With `--check`: **read-only.** Compare the deploy-state cache's commit to the live remote commit
  of the ref and print advice; also compare the installed CLI version to the version declared in
  the remote's project metadata and print the exact upgrade command if newer. Writes nothing;
  always exit 0 (a check that can't reach the host is informational, not a failure).

### 6.4 `uninstall [names…] [--skills-only|--agents-only|--prompts-only]` (CR-CLI-014)
- **Named:** for each name, resolve across skills (dir), agents (`<name>.agent.md`), prompts
  (`<name>.prompt.md`); first match wins; remove it. Base skills cannot be removed by name (exit 1).
  After removal, **prune base skills** if no other managed skill remains.
- **No names:** remove **all** managed items (managed-prefix skills except base; all agents; all
  prompts), honoring the scope flag. Requires interactive `y/N` confirmation unless `--dry-run`.
  Then prune base skills if nothing managed remains.
- Scope flags are mutually exclusive and only valid with no names (else exit 2).

### 6.5 `clean [--dev] [--ref REF]` (CR-CLI-015)
- Determine the canonical name set from the ref that was **last installed** (from the deploy-state
  cache; `--dev`/`--ref` override; else default branch). Download that ref.
- Find **orphans**: target items whose names start with a managed **or legacy** prefix but are
  **absent** from the canonical set (skills by dir name; agents/prompts by filename).
- List them; require `y/N` confirmation (skip in `--dry-run`); delete on yes. Exit 0.

### 6.6 `status [--dev] [--ref REF]` (CR-CLI-016)
- Download the canonical list from the ref so "available" reflects the remote.
- Show: skills installed/available (user-level); agents & prompts available with per-location
  install counts (**user** and, when CWD is in a git repo, **repo** `.github/`), using tags
  `[user]`/`[repo]`/`[user+repo]`/`[ ]`.
- After the listing, print two advisories: run `update` when deployed content is behind the remote
  commit; the package-installer upgrade command when a newer CLI version exists on the ref.

### 6.7 `doctor` (CR-CLI-017)
- Print a diagnostic block: OS, language runtime version, executable path, CLI version, content
  bundle path, template counts (skills/agents/prompts), the three targets.
- On Windows: report whether the per-user Scripts dir is on `PATH` and recommend a remedy if not.
- Print the installed VCS commit (from install metadata, if any) and the deployed content commit
  (from the deploy-state cache). Exit 0.

### 6.8 `eval` (CR-CLI-018)
- Locate the agents dir (prefer repo source, then download, then bundle). Route **every**
  `*.eval_queries.json` assertion through the router; print per-agent `PASS/FAIL n/total` plus an
  overall line with accuracy. **Exit 1 on any failed assertion**, else 0. Exit 2 if no agents dir.

### 6.9 `route-score` (CR-CLI-019)
- Compute the aggregate routing accuracy (matched / total across all agents' eval files). Print
  `[PASS|FAIL] routing accuracy X.XXX (threshold >= 0.95)`. **Exit 1 below `ROUTE_SCORE_THRESHOLD`**,
  else 0. Exit 2 if no agents dir.

### 6.10 `validate-handoff <payload>` (CR-CLI-020)
- Load a YAML **or** JSON payload; validate against the single handoff schema (file 04). Print
  `[PASS]`/`[FAIL] … N schema violation(s)` with each message. **Exit 1** on any violation,
  **exit 2** if the file is missing/unparseable, else 0.

### 6.11 `run <skill> [args…]` (CR-CLI-021)
- Resolve `<skill>` to an installed skill's importable module (try the literal name with `-`→`_`,
  then strip known prefixes). Forward all trailing args to the skill's `main(argv) -> int`. Exit 2
  on unknown skill or missing/non-callable `main`; otherwise propagate the skill's return code.

### 6.12 Agents/prompts file install helper (CR-CLI-022)
Copying `*.agent.md` / `*.prompt.md` to their target must **preserve user edits**: if a destination
exists and its content **differs** from the bundle and `--force` is **not** set, **leave it** and
warn (`preserve …`); if it's identical, count unchanged; otherwise copy. Report
copied/preserved/unchanged counts. (Skills use whole-directory hash-diff for the same purpose.)

## 7. Download & deploy-state mechanics (CR-CLI-023)

- **Download:** shallow clone `git clone --depth 1 --branch <ref> <REPO_GIT_HTTP> <tmp>`; `<ref>`
  may be branch or tag. Capture `HEAD` commit via `git rev-parse`. Clean up the tmp dir afterward.
  Return `None`/error on any failure (git missing, clone fails, timeout) — callers must **not** use
  the bundle as a fallback for install/update/clean/status.
- **Remote SHA (for `--check`/advisories):** `git ls-remote <url> refs/heads/<ref> refs/tags/<ref>
  refs/tags/<ref>^{}`; prefer the dereferenced (`^{}`) commit for annotated tags.
- **Deploy-state cache:** after a successful deploy, write `{ref, commit, deployed_at(ISO-8601)}`
  to `<skills-target>/<DEPLOY_STATE_FILENAME>` (best-effort; ignore write errors).
- **Directory content hash:** hash a dir tree as `Σ (relative-posix-path ‖ NUL ‖ bytes ‖ NUL)` over
  files sorted by path; ignore timestamps/permissions. Used to detect "unchanged" skills and to
  preserve user-modified agent/prompt files.
- **Remote CLI version:** read the `version` from the remote project-metadata file (prefer an
  already-downloaded checkout; else fetch the raw metadata over HTTPS). Compare numerically
  (parse leading digits of each dotted component; `+local` marks editable installs, which are never
  prompted to upgrade).

## 8. Windows PATH & repo helpers (CR-CLI-024)
- **Windows user Scripts dir:** `%APPDATA%\Python\Python<XY>\Scripts`. `install`/`doctor` add it to
  `HKCU\Environment\Path` when missing and broadcast a settings-change so new terminals pick it up.
- **`--repo` git-root detection:** walk up from the chosen start dir looking for `.git`; exit 2 if
  none. Redirect only the default agent/prompt targets. Append `.github/agents/` and
  `.github/prompts/` to the repo `.gitignore` idempotently.
- **Legacy dir migration:** silently remove obsolete `~/.agents/{agents,prompts}/` install
  locations that no IDE reads (non-repo installs).

## 9. Build-time hook (CR-CLI-025)
Runs during package install on the user's machine. It must:
1. **Bundle content** — copy `skills/skills/ → <pkg>/_skills/` and `skills/{agents,prompts}/ →
   <pkg>/_{agents,prompts}/`. Register the generated dirs as build artifacts so they land in the
   distributable. Refresh only bundle subdirs that have a source counterpart (leave importable
   engine modules in place).
2. **Auto-install base skills** — copy only `BASE_SKILLS` into `~/.agents/skills/`, **skipping any
   already present** (preserve local edits). Report installed/skipped counts.
3. **Update the user's global gitignore** — add `ai_generated_docs/` to the configured
   `core.excludesfile`; if none is configured, create `~/.gitignore` and register it. Idempotent.

## 10. Exit-code summary (CR-CLI-026)

| Situation | Code |
|---|---|
| Success | 0 |
| `eval` had a failed assertion; `route-score` below threshold; `validate-handoff` schema violation; install of unknown/excluded-without-dev skill; download failure | 1 |
| Usage/precondition error (`--repo` not in a git repo; unknown `run` skill / no `main`; unreadable payload; no agents dir for eval) | 2 |

## 11. stdout/stderr conventions (CR-CLI-027)
- Progress + results to **stdout**; errors + "preserve" warnings to **stderr**.
- Most mutating commands end with a one-line `Summary: …`.
- `--dry-run` prefixes intended actions with `[dry-run]` and writes nothing.
