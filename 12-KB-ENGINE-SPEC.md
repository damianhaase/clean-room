# 12 — Knowledge-Base Engine Spec (optional/advanced, platform-agnostic)

The `<PREFIX>kb-universal` skill ships a **nested engine** (`<pkg>_kb/`) exposed as two console
scripts. It builds and queries a **developer-local, code-grounded knowledge base**. This is the most
optional subsystem — you can ship the SDLC pipeline without semantic search and still get the
markdown-tier token savings. Behaviors tagged `CR-KB-NNN`. Re-implement fresh; the design is
standard retrieval engineering.

---

## 1. Two tiers, deterministic fallback (CR-KB-001)

- **Markdown tier (always on):** curated digest files (architecture, data-model, per-topic files)
  plus trackers. Readable with **zero external dependencies** — this is where the token savings come
  from. The consumption path is **stdlib-only** (a minimal cosine helper importing only `math`).
- **Vector tier (optional):** semantic embeddings for ranking. The real embedder is a sentence-
  transformer model (identity tag `bge-small-en-v1.5`; loaded from `BAAI/bge-small-en-v1.5` or a
  local dir via an env override for offline use), with `sqlite-vec` storage. Both sit behind an
  install **extra** (`[generate]`) needed only at **generation** time.
- **Fallback:** when the model/extra is unavailable, a **deterministic hash-based stub embedder**
  keeps builds fast, offline, and reproducible. Vector *ranking* only works with the real model; the
  markdown digest savings remain intact either way.

## 2. Console scripts & command surface (CR-KB-002)

- **`<PREFIX>kb`** dispatcher → subcommands (each forwards argv to a module `main`):
  - `init` — bootstrap a complete KB on a fresh repo.
  - `re-index` (alias `reindex`) — rebuild a stale KB **in place via atomic swap**.
  - `verify [--fix]` — structurally validate a KB; `--fix` migrates/repairs (routes to re-index with
    `--migrate`/`--refresh-model`).
  - `detect <root>` — print the detected project profile as JSON.
  - Unknown command ⇒ usage + exit 2; `--help`/no args ⇒ usage.
- **`<PREFIX>kb-query`** — natural-language query against the embedding index:
  `<PREFIX>kb-query "where is JWT validated?" --top 5`. **JSON output by default** (one
  `json.loads`-able object per call); `--pretty` prints a **byte-stable** fixed-width table (for
  snapshot tests); `--db` selects the index.

## 3. Module map (recover each as a small, testable unit) (CR-KB-003)

| Module | Responsibility |
|---|---|
| `detector.py` | Auto-detect component types & frameworks from the tree. |
| `walker.py` | Navigate the code tree (respecting ignore rules). |
| `ids.py` | Stable id generation for chunks/topics. |
| `adapters/` | Stack-specific archetypes: `java_springboot`, `node_ts`, `react`, `python`, `polyglot`, `shell`, `markdown`. Each knows how to recognise controllers/services/routes/etc. for its stack. |
| `chunking/` | Split source & docs into embeddable chunks. |
| `index/embed.py` | **Idempotent embed loop** — injectable embedder function; re-running on an unchanged chunk stream yields **zero** new embed calls (hash-gated). |
| `index/storage.py` | Chunk storage: `upsert_chunk`, `get_existing_hash`, `manifest_set`, `quantize_int8`, `DEFAULT_MODEL`/`DEFAULT_DIM`. |
| `query/nl_map.py` | Map a natural-language query to ranked chunks (top-k). |
| `query/cosine_min.py` | **Stdlib-only** cosine (imports only `math`) — the consumption-time ranker. |
| `query/eval.py` | Query-quality evaluation helpers. |
| `cli/{init,reindex,swap,verify,detect,dispatch}.py` | The command implementations + atomic swap. |
| `config/` | `kb-config.yml` load/migrate (v1→v2), `auto_refresh` settings. |
| `manifestos/` | Design manifestos / topic archetypes (15+ domain topics). |
| `cookbook/`, `data/`, `delta/`, `runner/` | Templates/examples; data models; version-delta tracking; execution orchestration. |
| `tests/` | Engine unit tests (kept out of the distributed wheel). |

## 4. Lifecycle & guarantees (CR-KB-004)

- **Session mode:** generate one topic at a time under user guidance; architecture + data model kept
  current. Maintains `tracker.md` (completeness/gaps), `memory.md` (session state), `versions.md`
  (source hash tracking), `AGENTS.md` (agent-KB integration), `user-documents/`.
- **Idempotent indexing (NFR):** re-index only regenerates topics whose source **hash** changed;
  unchanged topics skipped ⇒ zero embed cost.
- **Atomic swap:** `re-index` builds a new index then swaps it in atomically, **preserving user-
  edited fenced sections and hand-augmented manifesto rows**.
- **Health/repair:** `verify` detects missing index/subdirs, model/dimension mismatch, and v1
  config; `verify --fix` migrates/repairs behind an explicit confirmation (hard-stop before
  destructive model-refresh).
- **Monorepo/split-repo** layouts supported; covers controllers, services, batch jobs, listeners,
  schedulers, repositories, frontend routing, and the cross-tier API contract; detects CI/CD and
  internal micro-frameworks and tech debt.

## 5. Auto-refresh (self-heal) (CR-KB-005)

- Triggered at **session start** and on **KB load**: a cheap `git fetch <DEV_BRANCH>` compares each
  topic's last-indexed commit against the integration branch; only drifted topics regenerate.
- Configured in `kb-config.yml → auto_refresh.mode` = `prompt` (default Y/n) | `auto` (silent) |
  `off` (warn-only).

## 6. KB-first discovery contract (CR-KB-006)

Discovery-oriented skills read the KB **first** (curated, hundreds of tokens), scan the codebase
**second** (narrow, targeted, fallback-only), and **surface the gap** (tell the user the KB needs an
entry) rather than broadening the search. This is the token-efficiency guarantee the whole content
library leans on.

## 7. Dependency policy (CR-KB-007)

- **Consumption-time** (query/read): stdlib-only; `cosine_min.py` imports only `math`.
- **Generation-time** (build/index with real semantics): `sentence-transformers` + `sqlite-vec`
  behind the `[generate]` extra; offline via a pre-downloaded model dir + `HF_HUB_OFFLINE`.
- Always provide the **deterministic stub embedder** so nothing hard-fails without the model.

## 8. Minimal re-implementation (if you skip semantics)
Ship only the markdown tier + `cosine_min`-style stdlib ranker over pre-computed stub vectors. You
keep KB-first discovery, session-mode topic generation, trackers, atomic swap, and auto-refresh —
and defer the sentence-transformer/`sqlite-vec` vector tier until needed. This satisfies every
pipeline behavior in file 09 that depends on the KB.
