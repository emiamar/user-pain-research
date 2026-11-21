# Handover issue template

Every issue should let a coding session that has never seen the research start work. Keep the headings; drop a section only if it truly doesn't apply. Write in plain language. Use real file paths, functions and endpoints you checked in the code.

```markdown
## Why
<1-3 sentences: the user pain (with the evidence: "~44% of low-star competitor
reviews cite ads") and why it matters for this app. For a bug: what's wrong
today and who it hurts.>

## Where things stand
<What exists now, with dates. Mention open PRs or branches this builds on,
feature flags or settings in play, and anything switched off in production.>

## Code pointers
- **<area>:** `path/to/file.ext` (`functionName`, `:line` if useful): <what it does today>
- **Endpoint:** `GET /api/...` in `app/views.py` `ViewName`
- **Tests to extend:** `path/to/tests_x.py`

## What to build
- <Concrete, testable behaviour>
- <Edge cases: who's excluded, what must never happen>
- <Cost, privacy or security constraints>
- <Product decision needed first, if any: say who decides>

## Done when
- [ ] <Observable outcome 1>
- [ ] <Observable outcome 2>
- [ ] Tests cover <x>

Refs: #<related issue>, <brief link> (section/item), <handover doc link>
```

## Title style
Say the outcome, not the activity:
- Good: "Download all photos: in-app bulk export at original quality"
- Good: "Storage sizes show inconsistent precision ("20 GB of 5.0 GB")"
- Avoid: "Export", "Research follow-up #3", "Fix bug"

## Labels
- `feature`: new capability, copy or guardrail work.
- `bug`: something wrong today, including the app contradicting a promise users care about.
- Add `critical` only for data loss, runaway cost or security, and say why in the body.
