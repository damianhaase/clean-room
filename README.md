# Clean-Room Specification — `tds-skills` (platform-agnostic)

This folder is a **complete, implementation-language-neutral specification** of every piece of
core functionality in the original repository. It exists so a second team can **re-implement the
same behavior from scratch — in Python, TypeScript, Go, or anything else — without copying the
original's protected expression** (its prose, calibration tables, or banking-specific content).

It supersedes the single-file `../CLEAN_ROOM_RECIPE.md` (kept only as a launcher).

---

## What the product *is*, in one paragraph

`tds-skills` is a **two-layer developer-productivity system**. Layer 1 is a tiny **package
manager CLI** that downloads a library of markdown "content" from a git host and copies it into
the well-known folders that AI coding assistants (VS Code Copilot Chat, IntelliJ Copilot, Claude,
etc.) read. Layer 2 is that **content library**: ~34 *skills* (deterministic single-task
workflows), 9 *agents* (role orchestrators), and ~13 *prompts* (slash-command dispatchers +
templates). Together they let an AI assistant walk a Jira ticket through a full, gated SDLC —
**Requirements → Design → Planning → Implementation → Test → Review → Release** — plus a
knowledge-base companion. A small **stdlib-only engine** inside Layer 1 (a deterministic text
*router*, an eval *runner*, and a handoff-payload *schema validator*) makes routing accuracy and
the inter-agent contract **offline-checkable CI gates**.

---

## How to read this spec

Read in order for a full mental model; jump directly to a numbered file to build one component.

| # | File | What it specifies | Primary reader |
|---|---|---|---|
| — | [00-REVERSE-ENGINEERING-PLAN.md](00-REVERSE-ENGINEERING-PLAN.md) | The **method** for extracting, re-authoring, and verifying — and the work breakdown | Project lead |
| 1 | [01-SYSTEM-OVERVIEW.md](01-SYSTEM-OVERVIEW.md) | Architecture, actors, glossary, distribution model, why it's built this way | Everyone |
| 2 | [02-PACKAGE-MANAGER-CLI-SPEC.md](02-PACKAGE-MANAGER-CLI-SPEC.md) | Every CLI command, option, exit code, path-resolution & download/deploy mechanics | Engine dev |
| 3 | [03-DETERMINISTIC-ROUTER-SPEC.md](03-DETERMINISTIC-ROUTER-SPEC.md) | The IDF-cosine lexical router: tokenizer, stemmer, scoring, calibration, thresholds | Engine dev |
| 4 | [04-HANDOFF-CONTRACT-SPEC.md](04-HANDOFF-CONTRACT-SPEC.md) | The inter-agent handoff JSON Schema + the stdlib fallback validator | Engine dev |
| 5 | [05-CONTENT-FORMATS-AND-VALIDATION-SPEC.md](05-CONTENT-FORMATS-AND-VALIDATION-SPEC.md) | File formats (SKILL.md / .agent.md / .prompt.md / eval_queries.json) + budgets | Content author |
| 6 | [06-SKILLS-INVENTORY.md](06-SKILLS-INVENTORY.md) | All 34 skills: purpose, inputs, outputs, guardrails, structure | Content author |
| 7 | [07-AGENTS-AND-INVARIANTS-SPEC.md](07-AGENTS-AND-INVARIANTS-SPEC.md) | All 9 agents + the shared invariants every agent obeys | Content author |
| 8 | [08-PROMPTS-INVENTORY.md](08-PROMPTS-INVENTORY.md) | All prompts: dispatchers vs utility templates | Content author |
| 9 | [09-SDLC-PIPELINE-SPEC.md](09-SDLC-PIPELINE-SPEC.md) | The gated pipeline: gates, loops, phase sizing, branch model, modes | Content author + engine dev |
| 10 | [10-USER-WORKFLOWS.md](10-USER-WORKFLOWS.md) | End-to-end user journeys: install → configure → use → maintain | Docs + QA |
| 11 | [11-TEST-SPECIFICATION.md](11-TEST-SPECIFICATION.md) | Language-neutral test suite: every behavior to assert + acceptance criteria | QA / TDD dev |
| 12 | [12-KB-ENGINE-SPEC.md](12-KB-ENGINE-SPEC.md) | The nested knowledge-base engine (adapters, chunking, index, query) | Optional/advanced |

Every functional requirement is tagged **`CR-<area>-NNN`** (Clean-Room requirement) so the test
spec (file 11) can reference behaviors unambiguously.

---

## Clean-room legal boundary (read before writing any code)

The original is licensed **Proprietary**. A clean-room re-implementation reproduces **behavior and
interfaces**, never protected expression. Use this split:

| Layer | Clean-room status | Rationale |
|---|---|---|
| **File formats & protocols** (SKILL.md, `.agent.md`, `.prompt.md`, handoff schema *shape*) | ✅ Use directly | Public specifications; formats aren't copyrightable. Sources cited in file 05. |
| **The engine** (CLI behavior, router algorithm, validator) | ✅ Re-implement from this spec | Behavior/interface documented here; write fresh code. Router is standard IR. |
| **Skill/agent/prompt *content*** (the actual banking prose, calibration wording) | ⚠️ Re-author from scratch | This is the proprietary IP. Re-derive from the public sources in file 05 + your own domain. |
| **Org specifics** (Jira/Confluence URLs, ticket-key regex, GitHub org, `tds-`/`LEN-` names) | ❌ Replace | Organization-specific. Substitute your own endpoints, prefixes, and branch names. |

**Recommended two-person protocol.** Person A reads the original and maintains *this spec*
(interfaces + behavior only). Person B implements the engine and authors the content **from this
spec and public sources only**, never reading the original's `.md` text. This document is written
so Person B never needs to open the original.

---

## Naming: parameterize everything org-specific

Throughout this spec, treat these as **configuration**, not literals:

| Placeholder | Original value | Your value |
|---|---|---|
| `<CLI_NAME>` | `tds-skills` | e.g. `acme-skills` |
| `<PREFIX>` | `tds-` | e.g. `acme-` |
| `<TICKET_RE>` | `LEN-\d+` | your tracker's key pattern |
| `<REPO_URL>` | `github.com/TD-Universe/CorpBankTech_skills` | your content repo |
| `<JIRA_BASE>` / `<CONF_BASE>` | `track.td.com` / `collaborate.td.com` | your endpoints |
| `<DEFAULT_BRANCH>` / `<DEV_BRANCH>` | `main` / `develop` | your branch names |

The behavior is identical regardless of these values.
