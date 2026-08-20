## Phase

`PHASE-NNN` — link to `docs/phases/PHASE-NNN-*.md`

## Spec refs

CR-XXX-NNN, CR-XXX-NNN

## Checklist (do not merge unless all checked)

- [ ] This PR implements exactly one `PHASE-NNN` — no other phase's work is mixed in
- [ ] Test file(s) were committed before (or in the same commit as, clearly separable from) the implementation
- [ ] `pytest -q` passes locally with no network access
- [ ] Diff stays within budget: ≤ 8 files, ≤ 400 changed lines (docs/fixtures excluded)
- [ ] No new runtime dependency added, or it's behind an optional extra with a tested fallback
- [ ] Phase ticket status updated to `done`

## What this phase does NOT do

<Explicitly list what's deferred to a later phase, so reviewers don't expect it here.>
