#!/usr/bin/env python3
"""Tag low-star App Store reviews with complaint themes and count them.

Usage:
  tag_reviews.py reviews.json [more.json ...] [--themes themes.json]
                 [--max-rating 3] [--since YYYY-MM-DD] [--examples 2]
                 [--exclude-app NAME ...] [--by-app] [--dump low.txt]
  tag_reviews.py --print-themes > themes.json   # copy, extend, pass back with --themes

Themes are case-insensitive regexes matched against title + body. Keyword
tags over- and under-count: always read the --dump file too, and look at the
untagged reviews for themes the regexes miss. Shares overlap (one review can
hit several themes).

Several input files are merged and de-duplicated, so partial fetches can be
combined. Any JSON list of {app, rating, title, body, date} works, so reviews
from another source (Google Play, a CSV you converted) can be tagged too.
If one app supplies more than ~30% of low-star reviews it is flagged: report
shares with and without it (--exclude-app NAME).
"""
import argparse
import json
import re
import sys
from collections import Counter

GENERIC_THEMES = {
    "ads, pop-ups and upselling": r"\bads?\b|advert|pop.?ups?|upsell|commercial",
    "paywall, price rises, free turned paid": r"paywall|subscri|premium|pay(ing)? (for|to)|price|expensive|money|\$\d|used to be free|no longer free|cost",
    "billing, trials, cancelling, refunds": r"charg(ed|ing)|bill(ed|ing)|free trial|trial (ended|period)|cancel|refund|auto.?renew|renewal|scam",
    "locked out, lost data, can't export": r"lost (all|my)|losing|deleted|disappear|gone|can'?t (export|download|get (my|them))|export|held hostage|locked out|backup",
    "crashes, bugs, slow": r"crash|bug|glitch|freez|slow|lag|broken|doesn'?t work|not working|won'?t (load|open)",
    "sync and upload problems": r"sync|upload|icloud|not saving|won'?t save|stuck",
    "sign-in and account problems": r"log ?in|sign ?in|password|account|verification|two.?factor|log(ged)? (me )?out",
    "sharing and inviting others is hard": r"\bshar(e|ing)\b|invite|family members?|partner|spouse|collaborat",
    "privacy, data selling, AI concerns": r"privacy|data (sell|sold|collect|shar)|sell(s|ing)? (my|your|our) data|track(s|ing)? (me|you|users|my location)|third.part(y|ies)|\bAI\b|artificial intelligence|creepy|permissions?\b",
    "missing or removed features": r"removed|no longer|missing|wish (it|there|you)|please add|feature request|bring back|can'?t even",
    "bad redesign or confusing UI": r"update ruined|new (update|design|version)|redesign|confusing|cluttered|interface|\bUI\b|hard to (use|find|navigate)|unintuitive",
    "notifications broken or spammy": r"notification|reminder|spam|alerts?\b",
    "support unresponsive": r"support|customer service|no (reply|response)|never (heard|responded|replied)",
    "platform gaps (iPad, Mac, web, dark mode)": r"ipad|\bmac\b|desktop|web (version|app)|browser|dark mode|apple watch|android",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reviews", nargs="*")
    ap.add_argument("--themes", help="JSON file of {theme: regex}; replaces the generic themes")
    ap.add_argument("--max-rating", type=int, default=3)
    ap.add_argument("--since", help="YYYY-MM-DD; also report shares for reviews on/after this date")
    ap.add_argument("--examples", type=int, default=2)
    ap.add_argument("--exclude-app", nargs="+", default=[], help="drop these apps (e.g. one dominating the sample)")
    ap.add_argument("--by-app", action="store_true", help="also print a theme x app table of counts")
    ap.add_argument("--dump", help="write every low-star review to this text file")
    ap.add_argument("--print-themes", action="store_true")
    a = ap.parse_args()

    if a.print_themes:
        json.dump(GENERIC_THEMES, sys.stdout, indent=2)
        print()
        return
    if not a.reviews:
        ap.error("reviews.json is required unless --print-themes")

    themes = GENERIC_THEMES
    if a.themes:
        with open(a.themes) as f:
            themes = json.load(f)
    rx = {k: re.compile(v, re.I) for k, v in themes.items()}

    reviews, seen = [], set()
    for path in a.reviews:
        with open(path) as f:
            for r in json.load(f):
                if not isinstance(r, dict):
                    sys.exit(f"{path}: expected a JSON list of review objects")
                key = r.get("id") or (r.get("app"), r.get("title"), r.get("date"), r.get("body", "")[:80])
                if key in seen:
                    continue
                seen.add(key)
                reviews.append(r)
    if a.exclude_app:
        drop = {x.lower() for x in a.exclude_app}
        reviews = [r for r in reviews if str(r.get("app", "")).lower() not in drop]
    low = [r for r in reviews if (r.get("rating") or 0) <= a.max_rating]
    low.sort(key=lambda r: r.get("date", ""), reverse=True)  # newest first -> recent examples
    recent = [r for r in low if a.since and r.get("date", "") >= a.since]

    hits = {k: [] for k in rx}
    untagged = 0
    for r in low:
        text = f"{r.get('title', '')}\n{r.get('body', '')}"
        tagged = False
        for k, pat in rx.items():
            if pat.search(text):
                hits[k].append(r)
                tagged = True
        untagged += not tagged

    apps = sorted({r["app"] for r in reviews})
    print(f"{len(reviews)} reviews across {len(apps)} apps; {len(low)} rated 1-{a.max_rating}*")
    if a.since:
        print(f"{len(recent)} low-star reviews since {a.since}")
    if low:
        print(f"{untagged} low-star reviews matched no theme ({untagged / len(low):.0%}): read them in the dump for missed themes")
    if low:
        pool = recent or low
        big, n_big = Counter(r["app"] for r in pool).most_common(1)[0]
        if n_big / len(pool) > 0.3 and len(apps) > 2:
            print(f"NOTE: {big} supplies {n_big / len(pool):.0%} of "
                  f"{'recent ' if recent else ''}low-star reviews; "
                  f"rerun with --exclude-app \"{big}\" and report shares both ways")
    print()

    for k, rs in sorted(hits.items(), key=lambda kv: len(kv[1]), reverse=True):
        if not rs:
            continue
        share = len(rs) / len(low)
        line = f"{k}: {len(rs)} ({share:.0%})"
        if a.since and recent:
            n_recent = sum(1 for r in rs if r.get("date", "") >= a.since)
            line += f", since {a.since}: {n_recent} ({n_recent / len(recent):.0%})"
        print(line)
        top = Counter(r["app"] for r in rs).most_common(4)
        print("   apps: " + ", ".join(f"{n} {c}" for n, c in top))
        for r in rs[: a.examples]:
            print(f'   {r["app"]} {r.get("date", "")}: "{r.get("title", "")}"')
    if a.by_app:
        pool = recent if a.since else low
        ids = {id(r) for r in pool}
        top_apps = [x for x, _ in Counter(r["app"] for r in pool).most_common(8)]
        print(f"\nlow-star counts by theme and app (top 8 apps{', since ' + a.since if a.since else ''}):")
        print(f"{'theme':42}" + "".join(f"{x[:10]:>11}" for x in top_apps))
        print(f"{'(all low-star)':42}" + "".join(f"{sum(1 for r in pool if r['app'] == x):>11}" for x in top_apps))
        for k, rs in sorted(hits.items(), key=lambda kv: len(kv[1]), reverse=True):
            c = Counter(r["app"] for r in rs if id(r) in ids)
            print(f"{k[:42]:42}" + "".join(f"{c[x]:>11}" for x in top_apps))
    if a.dump:
        with open(a.dump, "w") as f:
            for r in low:
                f.write(f"[{r['app']} | {r.get('rating')}* | {r.get('date', '')} | {r.get('country', '')}] "
                        f"{r.get('title', '')}\n{r.get('body', '')}\n\n")
        print(f"\nwrote {len(low)} low-star reviews to {a.dump}")


if __name__ == "__main__":
    main()
