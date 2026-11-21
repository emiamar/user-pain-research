---
name: user-pain-research
description: Research what users of competing apps complain about (App Store reviews, Reddit and forums, tech press), find the gaps in the incumbent or built-in app, check those pains against the developer's own codebase, write a shareable opportunity brief, and file GitHub issues (labelled feature or bug, written as handovers a coding session can pick up). Use this whenever someone building an app asks what users want, what competitors get wrong, what to build next, which features are missing compared with an incumbent (e.g. "what does iPhone Photos not do"), wants App Store reviews mined for complaints, wants market or user research turned into a roadmap, or wants research findings turned into GitHub issues, even if they don't say "research" or "issues" explicitly.
---

# User pain research → brief → GitHub issues

You're helping a developer find out what real users of apps like theirs struggle with, decide what that means for *their* app, and turn it into work their team (or a coding agent) can pick up. The value is in three things a quick web search doesn't give them:

1. **Evidence, not vibes:** counted complaints from real reviews, with honest caveats.
2. **Grounding in their code:** each opportunity is checked against what the app already does. The most valuable finding is often that the app *already breaks* a promise users care about.
3. **Ready-to-run issues:** every issue carries enough context that a coding session with no memory of this research can start work.

## Match the depth to the ask

The full workflow below is the one that worked for "research and file issues". Most requests need less, and doing more than asked makes the answer worse, not better. Pick the path first:

| The user wants | Do | Skip |
|---|---|---|
| **A quick answer** ("top 5 complaints, rough numbers") | Step 2 with 5-10 apps on the fetch script's light defaults, fetched in the background while you run one quick search; then answer in the length and file they asked for: the list, each item with a number, one line on what the numbers are based on | Steps 1, 3-6. No brief, no issues, no long caveats section |
| **A brief, no code yet** ("something I can send my cofounder") | Steps 2, 3 and 5 | The codebase check (step 4) and issues (step 6). Mark recommendations by priority instead of built/missing |
| **Research turned into work** ("…and turn it into issues") | Everything | Nothing |

Whatever the path, the counted review evidence (step 2) is what sets this apart from a web search, so don't drop it even for a quick answer. Where the user names a file, format or length, that wins over anything below.

## 1. Understand the product first

Before searching anything, learn what the developer is building and for whom, so you search the right category and judge fit later:

- Read the repo's README, CLAUDE.md or AGENTS.md, the app's name and bundle info, and any App Store metadata in the repo.
- Skim the main features in code (screens, models, API routes) and the existing GitHub issues (`gh issue list --state all --limit 100`). This tells you what's built, what's planned and which labels exist.
- No repo or no GitHub? Skip the parts that need them and carry on.
- Identify the **incumbent** (the built-in or dominant app users would otherwise use: iPhone Photos, Google Photos, Notion…) and **direct competitors**. If the category or competitors are unclear, ask; one question saves a wrong research run.

Keep the user's and project's details private: search for the category ("baby photo sharing app"), never the developer's name, email or unreleased product details.

## 2. Gather the evidence

Run these in parallel where you can.

### App Store reviews (the quantitative core)
Use the bundled scripts (pure Python standard library, public Apple endpoints, no keys):

```bash
S=<skill-dir>/scripts
python3 $S/find_apps.py "baby photo album" "family photo sharing" --country us   # pick 8-15 competitors, favour many ratings
python3 $S/fetch_reviews.py 521633042:Tinybeans 935672069:FamilyAlbum ... --out <scratch>/reviews.json   # run in the background
# light defaults (4 countries, 5 pages); rerun only the apps it lists as thin with --countries nz ie in sg za / --max-pages 10
# reruns merge into the same file, never overwrite (--fresh to restart)
python3 $S/tag_reviews.py <scratch>/reviews.json --since <2 years ago> --examples 3 --by-app --dump <scratch>/low.txt
python3 $S/tag_reviews.py --print-themes > <scratch>/themes.json   # then add product-specific themes and rerun with --themes
```

- **The feed is flaky.** It returns empty pages or 403s that work a minute later, throttles long runs, and may serve nothing at all to cloud machines. The fetch script retries and lists the app/country combinations that stayed empty; wait a minute and rerun for those. If it stays empty for everything, say so plainly and use another counted source: Google Play review pages, or comments from a forum archive (below) tagged with the same script (it accepts any JSON list of `{app, rating, title, body, date}`). Don't silently swap in the App Store page's handful of "featured" reviews; they're curated and mostly 5-star.
- **One app can swamp the sample.** If the tagger flags an app with over ~30% of low-star reviews, report shares with and without it (`--exclude-app`). In a quick answer, one clause is enough ("~43%, 36% without Headspace").
- **Split money complaints.** The generic themes keep "too expensive / paywall" apart from "billing, trials, cancelling, refunds"; for subscription apps the second is often the angrier, more fixable one. Keep them separate when you report.

- Save working files in the session's scratch or temp directory, not the repo.
- **Read the low-star dump, not just the counts.** Keyword tags over- and under-count. Reading surfaces the specific, quotable pains ("a 2026 update removed dates and captions from the upload screen"), app-by-app patterns and themes the regexes missed (check the untagged count).
- Focus on recent reviews (the last ~2 years). Old complaints about long-fixed bugs mislead.
- Record the sample honestly: number of apps, reviews, low-star count, countries, date pulled, and the feed's limits. Apple serves only the newest ~500 per app, country and sort; big apps dominate; some apps return nothing.

### Forums, press and the incumbent's gaps (the qualitative layer)
Use web search for:
- **Reddit and forum threads** where users vent or ask for alternatives (`"<incumbent> alternative" reddit`, `"<category> app" "switched from"`).
- **Platform forums:** Apple Community, Google support forums, MacRumors.
- **Recent tech press** on the incumbent's latest release. Check what it *just added*, so you don't recommend building something the OS now does free.

Reddit often blocks automated fetches and the search tool may not return reddit pages. If so, use a `site:reddit.com` search for thread titles and snippets, then the sources that usually answer: the apps' own community forums and feedback boards, Apple Community, and Hacker News (`https://hn.algolia.com/api/v1/search?query=<terms>`). The PullPush archive of Reddit comments (`https://api.pullpush.io/reddit/search/comment/?q=<terms>&size=100`) sometimes works and sometimes refuses automated requests; try it once, don't fight it. Say which sources you used. Filter out developers promoting their own apps; they're common in these threads.

Keep a source link for every claim you'll use.

## 3. Synthesize

Produce two ranked views:
- **Complaints about competitors:** theme, approximate share of low-star reviews (state that shares overlap), main apps, and a one-line concrete example.
- **Gaps in the incumbent:** gap, what users say (with source), and how well it fits this app.

Then the part that matters most: **what this app should do**, in priority order. Favour:
- trust promises competitors have broken (ads, surprise paywalls, data held hostage, lost uploads);
- pains the app is well placed to solve given its architecture.

Each recommendation is one bold claim plus one or two sentences of rationale.

## 4. Check each recommendation against the codebase

Before writing anything up for the team, grep and read enough code to classify each recommendation:

- **Already true:** say so; it may only need copy or a guardrail.
- **Partly built:** name the files and the gap.
- **Missing.**
- **Contradicted:** the app currently does the thing users hate. Flag these prominently, with file and line. These are often the most urgent findings, and sometimes a live risk to users (for example a job that deletes data). If something is actively harming users, tell the developer straight away and offer the immediate fix. Don't change production systems without explicit approval.

## 5. Write the brief

A short, shareable one-pager; skimmable in two minutes:
1. **Bottom line:** 2-3 sentences plus 3 bullets.
2. **Where the incumbent falls short:** a table.
3. **What users complain about in competitors:** a table with shares.
4. **What we should do:** a ranked list, each item marked already true, partial, missing or contradicted where you know.
5. **Method, caveats and sources.**

If the user named a file or place, put it there. Otherwise put it where the team can share it: Claude's document/artifact tool if available (it gives a link), or a markdown file such as `docs/research/<date>-user-pains.md`. Don't commit it without asking.

Keep it skimmable: tables and short lines over paragraphs. Around 1,500-2,000 words is plenty for a full brief; length usually means unread.

Quote reviews sparingly: short phrases, not paragraphs. Paraphrase the rest; the reviews are other people's writing.

## 6. File GitHub issues

1. **Decide the list.** One issue per independently shippable piece of work. Skip anything already done, already in an open PR or already filed: search existing issues (and any backlog file in the repo) by keyword first. If research adds to an existing item, say so in the brief or comment on that item rather than filing a broader copy of it. Split things that need a product decision (pricing, retention periods) into their own issue, and say so in the issue.
2. **Labels.** Every issue gets exactly one of `feature` (new capability) or `bug` (something wrong today, including "the app contradicts a promise"); a coding agent triaging the backlog relies on it. Extra labels (area, priority, needs-decision) can go alongside, never instead. Check `gh label list`; if a label is missing, create it (`gh label create feature --color 1D76DB`), mention it, and reuse the repo's existing conventions where they exist. Add a severity label like `critical` only when it's clearly warranted (data loss, runaway cost, security).
3. **Confirm before publishing,** unless the user already told you to create them. Filing issues is outward-facing. Show the titles and labels as a table and wait for a yes.
4. **Write each body as a handover.** Use the template in `references/issue-template.md`. Each issue must stand alone for a coding session that has never seen this conversation: why, current state, code pointers (paths, functions, endpoints), what to build, a "done when" checklist, and links to the brief and related issues. Use real paths you verified, not guesses.
5. **Create them.** If the repo isn't on GitHub, `gh` isn't available or the user said not to post, write each issue as a file in the format they asked for (e.g. `issues/NN-slug.md`: title on line 1, then `Labels:`, then the template body) and skip creation. Otherwise create them with `gh issue create --label <label> --body-file <file>`, writing bodies to temp files so quoting can't break them. Then link related issues: a comment on the parent or umbrella issue listing its follow-ups is cheap and helps.

## 7. Report back

End with:
- the brief's link;
- a table of the issues created (number with link, title, label), grouped by source;
- what you deliberately left out and why (already done, policy not code, duplicate);
- anything urgent from step 4 that needs the developer's decision.

## Pitfalls seen in practice

- **Feed thinness:** the review feed often returns a single page, and nothing for small apps. Widen countries and pages for the thin apps (reruns merge) before concluding there's no data, and say which apps returned nothing.
- **Over-fetching:** a few hundred recent low-star reviews per app is enough for theme shares. Tens of thousands of reviews cost minutes of waiting without changing the ranking; widen only where the sample is thin.
- **Category drift:** competitors found by search terms can include unrelated apps (generic photo editors for a baby-journal search). Filter by what the app actually does.
- **Recommending what the OS just shipped:** always check the incumbent's latest release notes.
- **Issues that say "see the brief":** a coding session may not be able to open it. Put the essential context in the issue itself.
- **Themes that misfire for the category:** a generic regex can match the category's own vocabulary ("tracking" in every habit-tracker review). Glance at each theme's example titles; if they don't fit, tighten or drop the theme in your themes file.
- **Non-English reviews** from multi-country pulls slip past English regexes and inflate the untagged count. Mention it, and read a few if they matter.
- **Over-filing:** twenty thin issues are worse than ten solid ones. Merge closely related items (e.g. privacy policy, website and in-app copy for the same promise).
