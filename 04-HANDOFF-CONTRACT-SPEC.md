# 04 — Handoff Contract Spec (schema + validator, platform-agnostic)

Every SDLC phase emits one **typed handoff payload** to the coordinator at each phase boundary.
There is exactly **one** JSON Schema (JSON Schema Draft 2020-12) that every payload must satisfy,
and a validator that runs **offline** (no third-party dependency required). Behaviors are tagged
`CR-HS-NNN`.

---

## 1. Top-level shape (CR-HS-001)

- `type: object`, `additionalProperties: false` (unknown fields are rejected).
- **Universally required:** `phase`, `status`.
- Per-phase and cross-cutting requirements are layered via an `allOf` list of `if/then` blocks —
  each phase asserts **only** the subset it actually emits.

## 2. Field catalog (CR-HS-002)

### Universally required
| Field | Type | Enum / rule |
|---|---|---|
| `phase` | string | `requirements, design, planning, implementation, test, review, release` |
| `status` | string | `complete, blocked, in-flight, aborted, handback_to_planning` |

### Cross-cutting (optional at top level; some become required per phase)
| Field | Type | Notes |
|---|---|---|
| `mode` | string | `full, lightweight` — propagated from Requirements |
| `self_review` | string | `pass, blocked` — `pass` only when every success criterion holds |
| `self_review_failures` | array<string> | named failed checks; **required & non-empty when `self_review==blocked`** |
| `eval_score` | number | `0 ≤ x ≤ 1` — objective phase metric |
| `eval_threshold` | number | `0 ≤ x ≤ 1`, **default 0.9** |
| `artifact_path` | string | primary artifact produced |
| `coverage_report` | string | path to the FR-coverage report |
| `coverage_status` | string | `pass, waived` |
| `next_dispatch` | string | agent the coordinator should dispatch next |
| `phase_id` | string | pattern `^PHASE-[0-9]{3}$` |
| `branch`, `parent_branch` | string | chained-branch names |
| `questions_asked` | integer ≥ 0 | |
| `jira` | string \| integer \| null | ticket key/number |
| `treatment` | string | `feature, bug-fix` |

### Test-phase fields
`gate` (`green, red, spec_gap`), `test_report` (string), `suite_results` (object), `coverage`
(object), `req_coverage` (object).

### Review-phase fields
`mergeable` (`yes, no`; `yes` requires zero open findings at every severity P0–P3), `review_report`
(string), `findings_open`/`findings_resolved` (integer ≥ 0), `user_decision`
(`approve, revise, abort`), `phases_total`/`phases_completed`/`phases_pending` (integer ≥ 0),
`next_phase_id` (string \| null, pattern `^PHASE-[0-9]{3}$`).

### Revision / oversize fields
`revision_cycle` (integer ≥ 0 \| null), `revision_source` (`test, review, null`), `revision_request`
(object), `oversized_phase` (boolean), `measured_files`/`measured_lines` (integer ≥ 0),
`resplit_reason` (string \| null).

### Planning fields
`phase_count` (integer ≥ 0), `phase_size_estimates` (array of `{phase_id:^PHASE-\d{3}$, files≥0,
lines≥0}`), `resplit_from` (string \| null).

### Implementation fields
`format_check` (`pass, fail`), `backend_unit_tests`/`frontend_unit_tests` (`added, skipped,
failed`), `unit_test_report` (string), `backfilled` (array of `requirements|design|planning|none`).

### Release fields
`pr_number` (integer \| null), `pr_url` (string \| null), `release_report` (string), `detection`
(object), `artifacts` (object).

## 3. Per-phase conditional required blocks (CR-HS-003)

Implemented as `allOf` with `if: {properties:{phase:{const: X}}}` → `then: {required:[…]}`:

| `phase` == | `then.required` |
|---|---|
| `requirements` | `mode, artifact_path, self_review` |
| `design` | `mode, artifact_path, coverage_report, self_review` |
| `planning` | `mode, artifact_path, coverage_report, self_review` |
| `implementation` | `phase_id, branch, self_review` |
| `test` | `gate, phase_id, branch, test_report, self_review` |
| `review` | `mergeable, phase_id, review_report` |
| `release` | `phase_id, branch, release_report, self_review` |

Plus one non-phase conditional:

| `if` | `then` |
|---|---|
| `self_review == blocked` (and present) | `required: [self_review_failures]`, with `self_review_failures.minItems: 1` |

> Note (CR-HS-004): the **implementation** and **review** conditionals deliberately do **not**
> require `mode` or `eval_score`; those remain optional but, **when present**, are still range/enum
> checked. This keeps the schema strict without forcing fields a phase may legitimately omit.

## 4. The `revision_request` sub-object (CR-HS-005)

Populated by Test (`gate: red`) or Review (`mergeable: no`) to bounce work back to Implementation:

```
{ source: "test"|"review",
  test_report | review_report: <path>,
  findings: [ { id, severity: P0|P1|P2|P3, summary, file, line } ],
  user_comments: <verbatim gate text, may be empty>,
  phase_id: "PHASE-NNN", branch: <str>, cycle: <int> }   # cycle shared across Test+Review
```

## 5. Validator behavior (CR-HS-006)

The validator returns a **list of error message strings** (empty = valid). Two modes:

1. **Full mode** — when a JSON-Schema validator library is available, validate with Draft 2020-12
   and sort errors by JSON path.
2. **Stdlib fallback** — when no library is available (air-gapped consumer), a structural check
   covering exactly the constraints the schema uses:
   - top-level `required` present;
   - `additionalProperties:false` ⇒ reject any field not in `properties`;
   - per-field `enum` membership;
   - numeric `minimum`/`maximum` bounds;
   - each `allOf` `if/then` conditional-required block (a condition matches when every `const` in
     its `if.properties` equals the payload's value and every `if.required` field is present).

Both modes must agree on the acceptance/rejection of the documented cases in file 11 §D.

## 6. Payload loading (CR-HS-007)

- `load_payload(path)`: read the file; if suffix is `.json` or the content starts with `{`/`[`,
  parse as **JSON**; else parse as **YAML**.
- YAML parsing uses a YAML library when present; otherwise a **minimal flat-YAML reader** that
  handles `key: scalar`, inline lists `key: [a, b]`, and dash-list blocks under a key. It coerces
  scalars (`null/~/""`→null, `true/false`→bool, int, float, else string) and raises on nesting it
  doesn't understand.
- A non-mapping top-level payload is an error.

## 7. CLI contract (`validate-handoff`) (CR-HS-008)

| Outcome | stdout/stderr | Exit |
|---|---|---|
| Valid | `[PASS] <file>: valid handoff payload` | 0 |
| Schema violation(s) | `[FAIL] … N schema violation(s)` + one line per message (stderr) | 1 |
| Missing / unparseable file | error message (stderr) | 2 |

## 8. Full schema (reference — this *shape* is a public spec, safe to reproduce)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "multi-agent SDLC handoff payload",
  "type": "object",
  "required": ["phase", "status"],
  "additionalProperties": false,
  "properties": {
    "phase":  { "type": "string", "enum": ["requirements","design","planning","implementation","test","review","release"] },
    "status": { "type": "string", "enum": ["complete","blocked","in-flight","aborted","handback_to_planning"] },
    "mode":   { "type": "string", "enum": ["full","lightweight"] },
    "self_review": { "type": "string", "enum": ["pass","blocked"] },
    "self_review_failures": { "type": "array", "items": { "type": "string" } },
    "eval_score":     { "type": "number", "minimum": 0, "maximum": 1 },
    "eval_threshold": { "type": "number", "minimum": 0, "maximum": 1, "default": 0.9 },
    "artifact_path":  { "type": "string" },
    "coverage_report":{ "type": "string" },
    "coverage_status":{ "type": "string", "enum": ["pass","waived"] },
    "next_dispatch":  { "type": "string" },
    "phase_id":       { "type": "string", "pattern": "^PHASE-[0-9]{3}$" },
    "branch":         { "type": "string" },
    "parent_branch":  { "type": "string" },
    "questions_asked":{ "type": "integer", "minimum": 0 },
    "jira":           { "type": ["string","integer","null"] },
    "treatment":      { "type": "string", "enum": ["feature","bug-fix"] },
    "gate":           { "type": "string", "enum": ["green","red","spec_gap"] },
    "test_report":    { "type": "string" },
    "suite_results":  { "type": "object" },
    "coverage":       { "type": "object" },
    "req_coverage":   { "type": "object" },
    "mergeable":      { "type": "string", "enum": ["yes","no"] },
    "review_report":  { "type": "string" },
    "findings_open":     { "type": "integer", "minimum": 0 },
    "findings_resolved": { "type": "integer", "minimum": 0 },
    "user_decision":  { "type": "string", "enum": ["approve","revise","abort"] },
    "revision_cycle": { "type": ["integer","null"], "minimum": 0 },
    "revision_source":{ "type": ["string","null"], "enum": ["test","review",null] },
    "revision_request": { "type": "object" },
    "oversized_phase":{ "type": "boolean" },
    "measured_files": { "type": "integer", "minimum": 0 },
    "measured_lines": { "type": "integer", "minimum": 0 },
    "resplit_reason": { "type": ["string","null"] },
    "phase_count":    { "type": "integer", "minimum": 0 },
    "phase_size_estimates": { "type": "array", "items": { "type": "object",
        "properties": { "phase_id": { "type":"string","pattern":"^PHASE-[0-9]{3}$" },
                        "files": {"type":"integer","minimum":0}, "lines": {"type":"integer","minimum":0} } } },
    "resplit_from":   { "type": ["string","null"] },
    "format_check":   { "type": "string", "enum": ["pass","fail"] },
    "phases_total":     { "type": "integer", "minimum": 0 },
    "phases_completed": { "type": "integer", "minimum": 0 },
    "phases_pending":   { "type": "integer", "minimum": 0 },
    "next_phase_id":  { "type": ["string","null"], "pattern": "^PHASE-[0-9]{3}$" },
    "backfilled":     { "type": "array", "items": { "type": "string", "enum": ["requirements","design","planning","none"] } },
    "backend_unit_tests":  { "type": "string", "enum": ["added","skipped","failed"] },
    "frontend_unit_tests": { "type": "string", "enum": ["added","skipped","failed"] },
    "unit_test_report": { "type": "string" },
    "pr_number":      { "type": ["integer","null"] },
    "pr_url":         { "type": ["string","null"] },
    "release_report": { "type": "string" },
    "detection":      { "type": "object" },
    "artifacts":      { "type": "object" }
  },
  "allOf": [
    { "if": { "properties": { "phase": { "const": "requirements" } } },   "then": { "required": ["mode","artifact_path","self_review"] } },
    { "if": { "properties": { "phase": { "const": "design" } } },         "then": { "required": ["mode","artifact_path","coverage_report","self_review"] } },
    { "if": { "properties": { "phase": { "const": "planning" } } },       "then": { "required": ["mode","artifact_path","coverage_report","self_review"] } },
    { "if": { "properties": { "phase": { "const": "implementation" } } }, "then": { "required": ["phase_id","branch","self_review"] } },
    { "if": { "properties": { "phase": { "const": "test" } } },           "then": { "required": ["gate","phase_id","branch","test_report","self_review"] } },
    { "if": { "properties": { "phase": { "const": "review" } } },         "then": { "required": ["mergeable","phase_id","review_report"] } },
    { "if": { "properties": { "phase": { "const": "release" } } },        "then": { "required": ["phase_id","branch","release_report","self_review"] } },
    { "if": { "properties": { "self_review": { "const": "blocked" } }, "required": ["self_review"] },
      "then": { "required": ["self_review_failures"], "properties": { "self_review_failures": { "minItems": 1 } } } }
  ]
}
```
