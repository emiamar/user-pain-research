# user-pain-research

A Claude skill that researches what users of competing apps complain about, checks those pains against your own codebase, writes a short opportunity brief, and turns the findings into handover-style GitHub issues.

- **Evidence:** counts low-star App Store reviews by complaint theme, with Python scripts that need only the standard library and Apple's public endpoints (no API keys), plus Reddit, forum and press research.
- **Grounding:** each recommendation is marked already true, partly built, missing or contradicted by your code.
- **Issues:** each issue is labelled `feature` or `bug` and carries enough context for a coding session to start work.

It scales to the request: a quick top-5 answer, a brief for a cofounder, or a full research-to-backlog run.

## Install

Copy the `user-pain-research/` folder into `~/.claude/skills/` (Claude Code), or upload the `.skill` file from the releases in Claude.ai.

## Scripts

```bash
S=user-pain-research/scripts
python3 $S/find_apps.py "habit tracker" --country us
python3 $S/fetch_reviews.py 123456789:AppName --out reviews.json      # reruns merge
python3 $S/tag_reviews.py reviews.json --since 2024-11-01 --by-app --dump low.txt
```

Apple's review feed only returns the newest ~500 reviews per app, country and sort order, and it can be flaky or empty from cloud machines.

## Tests

`user-pain-research/evals/` holds three test cases in the skill-creator / `claude plugin eval` layout.

## License

MIT, see [LICENSE](LICENSE).
