# 03 — Deterministic Router Spec (platform-agnostic)

The router is a **stdlib-only, fully deterministic** text classifier that maps a free-text user
query to **exactly one agent** (or `None`). It exists so routing correctness is an **offline CI
gate** — the same inputs always produce the same decision. The algorithm is standard information
retrieval; re-implement it freshly. Behaviors are tagged `CR-RT-NNN`.

---

## 1. Inputs & corpus (CR-RT-001)

- One router is built from **all** `*.agent.md` files in the agents dir. The **agent key** is the
  file stem (e.g. `<PREFIX>implementation`).
- For each agent, extract from frontmatter the `name` and `description` (the description may span
  multiple lines until the next top-level key such as `tools:` or the closing `---`). The scored
  document is `"{agent_key} {description}"`.
- Requires ≥ 1 agent; raise if the corpus is empty.

## 2. Tokenisation & stemming (CR-RT-002)

1. Lowercase the text; extract tokens with regex `[a-z0-9]+`.
2. **Light suffix-stripping stemmer** `stem(token)`: repeatedly strip the **first matching** suffix
   from this ordered list (longest/most-specific first), each time only if ≥ 3 chars remain:
   ```
   izations, ization, ations, ation, ements, ement, ments, ment, ings, ing,
   edly, ies, ned, ged, es, ed, ors, or, er, s
   ```
   After no suffix applies, if the result is > 3 chars and ends in `e`, drop the trailing `e`.
   (So "implementation"→"imple", "tests"/"testing"→"test", "code"/"coding"→"cod".)
3. Two token views:
   - **`raw_tokens`** — stem every token, **keep** stopwords (used for bigrams).
   - **`content_tokens`** — drop stopwords and pure-digits, stem, then drop results < 2 chars or
     that are themselves stopwords.
4. **Bigrams** = adjacent pairs from `raw_tokens`, **excluding** pairs where *both* members are
   stopwords.

Keep the **stopword set** small, explicit, and deterministic (common English function words plus
boilerplate like `agent`, `phase`, `step`, `run`, `use`, `list`, `show`). It is *your* set to
re-derive; see file 05 for authoring guidance. (~120 words in the original.)

## 3. Feature model (CR-RT-003)

For each agent, precompute:
- **Unigram set** = `content_tokens(name+description)` **plus** the stemmed `ROLE_ALIASES` for that
  agent (domain synonyms the eval queries use but the prose doesn't literally contain).
- **Bigram set** = `bigrams(raw_tokens(name+description))`.
- **Role stem** = `stem(last "-"-segment of the agent key)` (e.g. `…-design` → stem of `design`).
- **Signal stems** = `{ stem(s) for s in STRONG_SIGNALS[agent] }`.

## 4. IDF weighting (CR-RT-004)

Compute a smoothed inverse-document-frequency over the agent corpus, separately for unigrams and
bigrams:

$$ \mathrm{idf}(t) = \ln\!\frac{N+1}{\mathrm{df}(t)+1} + 1 $$

where `N` = number of agents, `df(t)` = number of agents whose feature set contains term `t`. This
suppresses boilerplate shared by many descriptions and amplifies terms unique to one agent.

## 5. Scoring a query against an agent (CR-RT-005)

Let bigram weight `BIGRAM_WEIGHT = 2.2`, `NAME_BONUS = 0.45`, `SIGNAL_BONUS = 0.55`.

1. Build the query's unigram set (`content_tokens`), bigram set (`bigrams(raw_tokens)`), and
   lowercase form.
2. **IDF-weighted cosine** of query vs agent term vectors (a term's weight is its idf; a bigram's
   weight is `BIGRAM_WEIGHT × idf`):
   - `dot` = Σ over shared unigrams `idf(u)²` + Σ over shared bigrams `(BIGRAM_WEIGHT·idf(b))²`.
   - `‖q‖`, `‖a‖` = Euclidean norms of the query and agent vectors (each `√Σ weight²`; floor to 1.0
     to avoid divide-by-zero).
   - `cosine = dot / (‖q‖·‖a‖)`. Cosine normalises by length so a long, broad description (the
     coordinator) can't win merely by overlapping more words.
3. **Name bonus:** if the agent's role stem ∈ query unigrams, add `NAME_BONUS`.
4. **Strong-signal bonus:** add `SIGNAL_BONUS ×` |query unigrams ∩ agent signal stems|.
5. **Phrase-signal bonus:** add `SIGNAL_BONUS ×` (number of `PHRASE_SIGNALS[agent]` substrings that
   appear in the lowercased query).
6. The agent's score is the sum. Return a `{agent → score}` map.

## 6. Deciding the winner (CR-RT-006)

1. **Coordinator override:** if the corpus has an orchestrator (agent key ending `coordinator`) and
   the query contains any `COORDINATOR_PHRASE` substring, **return the coordinator immediately**.
2. Otherwise score all agents.
3. **Veto:** for each agent with `VETO_PHRASES`, if the query contains any of them, set that
   agent's score to `-1.0` (bars it).
4. **Winner:** `argmax` by `(score, -index_in_sorted_names)` — i.e. highest score, ties broken
   **deterministically by ascending agent name**.
5. If the winning score ≤ 0.0, return `None` (nothing matched).

## 7. Calibration tables (CR-RT-007)

Five small per-behavior tables tune the matcher. **They are matcher tuning you re-derive for your
own agents — never edit the published `eval_queries.json` to force a decision.**

| Table | Shape | Purpose |
|---|---|---|
| `COORDINATOR_PHRASES` | tuple of substrings | Explicit orchestration cues that force-route to the coordinator (e.g. "the agents", "end-to-end", "the pipeline", "orchestrate", "pr comments", "through release"). Deliberately **excludes** bare "SDLC"/"pipeline" that specialist queries also use. |
| `ROLE_ALIASES` | `agent → extra terms` | Domain synonyms folded into an agent's unigram set (e.g. planning ← "decompose, scaffold, breakdown"; test ← "verification, coverage, suite"). |
| `STRONG_SIGNALS` | `agent → terms` | Distinctive unigrams; each match adds a flat `SIGNAL_BONUS` (e.g. release ← "rebase, squash, jar, deploy"; kb ← "embeddings, reindex"). |
| `PHRASE_SIGNALS` | `agent → substrings` | Multi-word phrases whose individual words are ambiguous (e.g. planning ← "implementation plan"; kb ← "knowledge base", "db index"). |
| `VETO_PHRASES` | `agent → substrings` | Bar a query from an agent (e.g. kb ← "ask the knowledge", "how does the knowledge" — those are content questions, not KB maintenance). |

## 8. The score & its threshold (CR-RT-008)

- The **eval runner** loads each `*.eval_queries.json` (a list of `{query, should_trigger}`),
  routes each query, and passes an assertion when:
  - `should_trigger:true` ⇒ predicted == owning agent key;
  - `should_trigger:false` ⇒ predicted != owning agent key.
- **`route_score` = matched / total** across all assertions (0.0 when none).
- `route-score` **must stay ≥ `ROUTE_SCORE_THRESHOLD` (0.95)** or CI fails. The current catalog's
  baseline is 1.000; the floor is the documented pass line.

## 9. Determinism & edge cases to preserve (CR-RT-009)

- Empty query ⇒ `None`. Empty catalog / no assertions ⇒ score 0.0.
- An eval file naming an **unknown agent**: a positive assertion for it always fails (router can't
  route to an agent it doesn't know); a negative assertion always passes.
- Ties **must** break by agent name so results are reproducible across runs and machines.
- No randomness, no network, no model — pure function of `(agent descriptions, calibration tables,
  query)`.

## 10. Reference pseudocode (CR-RT-010)

```text
function route(query):
    if orchestrator exists and any(p in lower(query) for p in COORDINATOR_PHRASES):
        return orchestrator
    scores = score(query)                      # §5 for every agent
    for agent, phrases in VETO_PHRASES:
        if agent in scores and any(p in lower(query) for p in phrases):
            scores[agent] = -1.0
    best = argmax over sorted(agent_names) by (scores[agent], -index(agent))
    return best if scores[best] > 0.0 else None
```

## 11. Scaling note (CR-RT-011)
Document a written scaling path tied to a concrete catalog-size trigger (e.g. "when the catalog
exceeds ~30 agents, re-tune calibration and consider raising the floor"). The tests assert such a
note exists.
