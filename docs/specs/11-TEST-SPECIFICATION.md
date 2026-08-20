# 11 — Test Specification (language-neutral)

A re-implementation is **correct** when it passes this suite. Cases are written implementation-
neutral (port to pytest, jest/vitest, go test, …). They mirror the original's **~170 tests** across
11 files, including its **"independent test"** discipline: author each assertion from the
*requirement* (this spec) — never from the implementation — and use **stub routers, temp catalogs,
and synthetic payloads** so a bug copied into both code and test can't hide. IDs map to the `CR-*`
requirements in files 02–09.

Conventions: use a temp dir per test; a `repo_env` fixture points targets at temp dirs and content
at a fixture library; a `_StubRouter(lookup_table)` implements only `route(query)`.

---

## §A — CLI & deploy model (→ file 02)

**A1 list/status**
- `list` default hides excluded skills; `list --dev` includes them. (CR-CLI-005/010)
- `list` marks installed skills `[installed]`, base skills `*`. (CR-CLI-010)
- `list --agents` prints installed agents sorted, each mapped to its wrapped skills; empty target ⇒
  "no agents" message, exit 0. (CR-CLI-010)
- `status` reports `installed/available` skills and per-location agent/prompt counts. (CR-CLI-016)

**A2 install**
- Installing a **subset always also installs `BASE_SKILLS`**. (CR-CLI-011)
- Unknown skill name ⇒ error on stderr, exit 1. (CR-CLI-011)
- Excluded skill by name **without** `--dev` ⇒ error, exit 1; **with** `--dev` ⇒ installed. (CR-CLI-011)
- Without `--force`, an existing skill is **skipped**; with `--force` it is **overwritten**. (CR-CLI-011)
- Identical source/dest (equal dir-hash) counts **unchanged**, writes nothing. (CR-CLI-011/023)
- `--dry-run` writes nothing and prefixes intended actions with `[dry-run]`. (CR-CLI-027)
- `install` (no names) also creates the agents & prompts dirs and deploys them. (CR-CLI-011/022)

**A3 preserve user edits**
- A user-modified agent/prompt file whose content differs from the bundle is **preserved** (warned,
  not overwritten) unless `--force`. Identical files count unchanged. (CR-CLI-022)

**A4 uninstall**
- `uninstall <skill>` removes it; a **base skill cannot** be removed by name (exit 1). (CR-CLI-014)
- `uninstall <missing>` reports "not found". (CR-CLI-014)
- `uninstall` (no names) requires `y/N` confirmation; base skills preserved until nothing managed
  remains, then pruned. `--dry-run` deletes nothing. (CR-CLI-014)
- Scope flags valid only with no names (else exit 2). (CR-CLI-014)

**A5 update**
- `update` forces reinstall of content (overwrites). (CR-CLI-013)
- `update --check` is read-only: prints "up to date" / "update available" / "no deploy recorded";
  prints the pip-upgrade command when a newer CLI version exists; writes nothing; exit 0. (CR-CLI-013)

**A6 clean**
- `clean` removes orphaned managed-prefix skills/agents/prompts absent from the canonical set,
  **including legacy-prefix** items; asks before deleting; `--dry-run` deletes nothing; aborts on a
  non-`y` answer. No orphans ⇒ "nothing to clean", exit 0. (CR-CLI-015)

**A7 helpers/parsing**
- Frontmatter list parser handles inline `[a, b]` and block `- a` forms; missing frontmatter ⇒ `[]`.
  (CR-CLI-022)
- Version-tuple parser degrades gracefully on suffixes (`1.6.0+local` → (1,6,0)). (CR-CLI-023)
- `--repo` outside a git repo ⇒ exit 2. (CR-CLI-024)
- `main` dispatches to the selected subcommand handler. (CR-CLI-001)

**A8 advisories**
- "newer package" advisory prints the pip command when remote > local; silent when offline; special
  line for local/editable (`+local`) installs. (CR-CLI-023)
- "content update" advisory prints `update` when remote commit ≠ cached; "up to date" when equal;
  handles no-deploy-recorded; silent when offline; appends `--dev`/`--ref` suffix. (CR-CLI-013)

## §B — build hook (→ file 02 §9)
- Bundles content into the package dir; registers artifacts. (CR-CLI-025)
- Auto-installs only `BASE_SKILLS`, **skipping already-present** ones. (CR-CLI-025)
- Adds `ai_generated_docs/` to the global gitignore idempotently; creates+registers one if none.
  (CR-CLI-025)

## §C — router, eval runner, route-score (→ file 03)

**C1 score arithmetic (stub router)**
- All assertions satisfied ⇒ `route_score == 1.0`. (CR-RT-008)
- 3 of 4 pass ⇒ `route_score == 0.75` (exact matched/total). (CR-RT-008)
- Every positive mis-routes ⇒ `0.0`. (CR-RT-008)
- Empty catalog ⇒ `0.0`; empty assertion list ⇒ `0.0`. (CR-RT-009)
- `route_score` equals the eval-runner's matched/total counts (consistency). (CR-RT-008)

**C2 router determinism**
- Empty query ⇒ `None`. (CR-RT-009)
- Ties break by **ascending agent name** (deterministic). (CR-RT-006)
- Unknown-agent **positive** assertion counts as a failure; unknown-agent **negative** passes.
  (CR-RT-009)
- `route_score` on the live catalog is **reproducible** across repeated builds. (CR-RT-009)

**C3 threshold & CLI**
- `ROUTE_SCORE_THRESHOLD == 0.95` (documented). (CR-RT-008)
- `route-score` **passes at exactly 0.95** (`>=` boundary), fails just below, passes above.
  (CR-RT-008/CR-CLI-019)
- `route-score` prints the measured score; exit 0 pass / 1 fail; exit 2 with no agents dir.
  (CR-CLI-019)
- The live catalog's `route-score` meets the threshold and the CLI exits 0. (CR-RT-008)

**C4 eval regression**
- `eval` over the **current library is green** and exits 0. (CR-CLI-018)
- A synthetic failing assertion forces a per-agent FAIL and a **non-zero exit**. (CR-CLI-018)
- The agents-dir resolver prefers the **repo source** over the bundle. (CR-CLI-007)
- Per-agent report shape: `PASS/FAIL agent: passed/total` + overall accuracy line. (CR-CLI-018)

**C5 calibration honesty**
- Coordinator phrases force-route to the coordinator regardless of specialist overlap. (CR-RT-006)
- Veto phrases bar their agent (e.g. "ask the knowledge base" never routes to the KB agent). (CR-RT-006)
- (Author your own trigger/negative queries; **never** edit eval files to force a pass.) (CR-RT-007)

## §D — handoff schema & validator (→ file 04)

**D1 schema shape**
- The schema is itself a valid JSON-Schema document. (CR-HS-001)
- `phase` enum covers all seven roles; `status` enum covers all five states. (CR-HS-002)
- `eval_threshold` default is `0.9`; `eval_score`/`eval_threshold` are numbers in `[0,1]`. (CR-HS-002)
- `self_review` enum limited to `pass|blocked`; `self_review_failures` is an array. (CR-HS-002)

**D2 acceptance**
- A well-formed **full-field** payload validates for **every** phase. (CR-HS-003)
- Planning payload with `phase_count`/`phase_size_estimates`/`resplit_from` accepted. (CR-HS-002)
- Implementation payload with `format_check`/unit-test fields accepted. (CR-HS-002)
- Review payload with `phases_total/…/next_phase_id` accepted. (CR-HS-002)

**D3 rejection**
- Empty payload missing `phase`/`status` rejected. (CR-HS-001)
- Unknown/typo field rejected (`additionalProperties:false`). (CR-HS-001)
- Unknown `phase` / `status` value rejected. (CR-HS-002)
- `eval_score` outside `[0,1]` rejected; `phase_id` pattern violation rejected. (CR-HS-002)
- **Per-phase required field** dropped ⇒ rejected (parametrized over all phases). (CR-HS-003)
- `self_review:blocked` **without** `self_review_failures` rejected; with an **empty** list
  rejected; with a non-empty list accepted. (CR-HS-003)
- Implementation/review conditionals do **not** require `mode`/`eval_score`, but a present
  out-of-range `eval_score` is still rejected. (CR-HS-004)

**D4 loader + CLI**
- Loads YAML **and** JSON by content and by suffix; round-trips both. (CR-HS-007)
- Non-mapping payload rejected. (CR-HS-007)
- `validate-handoff`: exit 0 valid (YAML & JSON); exit 1 on schema violation / unknown field;
  exit 2 on missing file / unparseable JSON. (CR-HS-008)
- Missing schema file raises a clear error. (CR-HS-006)

**D5 stdlib fallback parity**
- The stdlib fallback validator: accepts valid full-field payloads; blocks unknown field + missing
  required; enforces enum/bounds/conditional-required blocks — **matching** the full validator on
  the documented cases. (CR-HS-006)

## §E — content contracts & budgets (→ file 05)

**E1 skill budgets**
- Every `SKILL.md` ≤ **500 lines** (hard); a synthetic 501-line file is flagged. (CR-FMT-003)
- `description` length `0 < len ≤ 1024`. (CR-FMT-003)
- Token estimate warning at ~5000 (chars/4). (CR-FMT-003)
- Every skill and agent has a paired `eval_queries.json`. (CR-FMT-007)

**E2 skill run bridge**
- `run <skill>` invokes the skill's `main(argv)`; unknown skill ⇒ exit 2; skill with no `main` ⇒
  exit 2; prefix-strip resolution works (`<PREFIX>foo` and `foo`). (CR-CLI-021)
- A representative script skill (e.g. an extract/`--all`/`--check`) processes multiple files and its
  `--check` mode exits 0 when there's no drift. (CR-FMT-008)
- `python -m <pkg>.cli --help` lists the subcommands (module entry works). (CR-CLI-001)

## §F — agents, invariants, pipeline behavior (→ files 07, 09)

**F1 shared invariants file**
- `_shared/agent-invariants.md` exists with its canonical section headings. (CR-AG-INV)
- Every role agent's body **references** the shared invariants file. (CR-AG-INV / CR-FMT-005)
- The invariants document the required rules (branch protection, single committer, self-check,
  typed payload, load-skill-before-execute) and explicitly state **no auto-commit / no auto-push /
  no force-push**. (CR-AG-INV)

**F2 agent budgets & structure**
- Every agent `description` is within the ~1500-char budget; an oversized description is flagged by
  the budget helper. (CR-FMT-005)
- Every role agent references the shared **self-check** and **records an `eval_score`**. (CR-AG-INV)
- No conflict markers in any agent file. (CR-FMT-005)

**F3 coordinator worked example**
- The coordinator body contains a worked-example section; its embedded handoff example **validates
  against the schema** and is a valid Implementation return; a **tampered** copy is **rejected**.
  (CR-AG-COORD / CR-HS-003)

**F4 docs coherence** (optional but in the original)
- The agents README documents the token-budget rule and references both the schema path and the
  shared-invariants file; the quick-reference documents the `eval`, `route-score`, and
  `validate-handoff` commands. (CR-FMT-005 / CR-CLI-018/019/020)

---

## Coverage matrix (subsystem → sections)

| Subsystem | Sections |
|---|---|
| A. CLI engine | §A1–A8 |
| B. Deploy model / build hook | §A2/A3/A6 + §B |
| C. Router + eval | §C1–C5 |
| D. Handoff contract | §D1–D5 |
| E. Content formats | §E1–E2 |
| F. Pipeline behavior | §F1–F4 |

## Test methodology to reproduce
- **Independent authoring** from this spec, not from the code.
- **No network, no LLM** — everything runs offline; downloads are stubbed/monkeypatched.
- **Stubs & temp catalogs** for the router; **synthetic payloads** for the schema.
- Wire `route-score`, `eval`, `validate-handoff`, and the budget checks into CI on every PR.
