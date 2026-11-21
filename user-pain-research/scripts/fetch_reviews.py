#!/usr/bin/env python3
"""Fetch App Store customer reviews from Apple's public RSS feed.

Usage:
  fetch_reviews.py ID[:Name] ... [--countries us gb ca au]
                   [--sorts mostrecent mosthelpful] [--max-pages 5]
                   [--empty-retries 2] [--out reviews.json] [--fresh]

Feed: https://itunes.apple.com/{country}/rss/customerreviews/page={p}/id={id}/sortby={sort}/json

Limits worth stating in any write-up: Apple serves at most about the newest
500 reviews (10 pages of 50) per app, country and sort order. Big apps
dominate any pooled sample.

Defaults are deliberately light (4 countries x 2 sorts x 5 pages, up to
~2,000 reviews per app): plenty for theme shares, and a run over 10 apps
usually finishes in a few minutes. Apps that come back thin are listed at the
end; widen only those (--countries nz ie in sg za, --max-pages 10) and rerun,
since results merge. Run long fetches in the background. Results are saved
after each app, so an interrupted run keeps what it fetched.

The feed is also flaky: it often answers with an empty page (or a 403) that
has data a few seconds later, and it throttles long runs. So this script
retries empty first pages, and by default MERGES into an existing --out file
(de-duplicated by review id) instead of overwriting it. Rerunning for the
apps or countries that came back thin is safe and only adds reviews. Pass
--fresh to start a new file.

Output: a JSON list of {id, app, country, rating, title, body, date, version}.
Per-app counts (this run and file total) go to stderr.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter

UA = "Mozilla/5.0 (compatible; user-pain-research/1.0)"
URL = "https://itunes.apple.com/{c}/rss/customerreviews/page={p}/id={id}/sortby={s}/json"


def fetch_json(url, tries=4):
    """GET JSON, retrying the intermittent 403/429/5xx Apple's CDN returns."""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code not in (403, 429, 500, 502, 503, 504) or i == tries - 1:
                raise
        except (urllib.error.URLError, TimeoutError):
            if i == tries - 1:
                raise
        time.sleep(1.5 * (i + 1))


def get_page(app_id, country, sort, page):
    feed = fetch_json(URL.format(c=country, p=page, id=app_id, s=sort)).get("feed", {})
    entries = feed.get("entry", [])
    if isinstance(entries, dict):
        entries = [entries]
    return [e for e in entries if "im:rating" in e]  # first entry can be app metadata


def save(out, path):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)


def lab(e, key):
    v = e.get(key, {})
    return v.get("label", "") if isinstance(v, dict) else ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("apps", nargs="+", help="App Store id, optionally ID:Name")
    ap.add_argument("--countries", nargs="+", default="us gb ca au".split())
    ap.add_argument("--sorts", nargs="+", default=["mostrecent", "mosthelpful"])
    ap.add_argument("--max-pages", type=int, default=5,
                    help="pages of 50 per country and sort (feed max 10; default 5)")
    ap.add_argument("--empty-retries", type=int, default=2,
                    help="times to retry an empty first page before giving up (default 2)")
    ap.add_argument("--out", default="reviews.json")
    ap.add_argument("--fresh", action="store_true", help="overwrite --out instead of merging into it")
    a = ap.parse_args()
    # accept "us,gb ca" as well as "us gb ca"
    a.countries = [c.strip().lower() for x in a.countries for c in x.split(",") if c.strip()]
    a.sorts = [c.strip() for x in a.sorts for c in x.split(",") if c.strip()]

    out = []
    if os.path.exists(a.out) and not a.fresh:
        with open(a.out) as f:
            out = json.load(f)
        print(f"merging into {a.out} ({len(out)} reviews already there)", file=sys.stderr)
    seen = {r["id"] for r in out if r.get("id")}
    # older files may lack ids: match their reviews by content instead
    seen_alt = {(r["app"], r.get("title"), r.get("date"), r.get("body", "")[:80]) for r in out if not r.get("id")}
    before = len(out)
    added = Counter()
    empty_slots = []

    for spec in a.apps:
        app_id, _, name = spec.partition(":")
        name = name or app_id
        for c in a.countries:
            for s in a.sorts:
                for p in range(1, a.max_pages + 1):
                    entries, err = [], None
                    for attempt in range(1 + (a.empty_retries if p == 1 else 0)):
                        try:
                            entries = get_page(app_id, c, s, p)
                        except Exception as e:
                            err = e
                        if entries:
                            break
                        time.sleep(2 * (attempt + 1))
                    if not entries:
                        if p == 1:
                            empty_slots.append(f"{name} {c} {s}" + (f" ({err})" if err else ""))
                        break
                    for e in entries:
                        rid = lab(e, "id")
                        content = e.get("content", {})
                        rec = {
                            "id": rid,
                            "app": name,
                            "country": c,
                            "rating": int(lab(e, "im:rating") or 0),
                            "title": lab(e, "title"),
                            "body": content.get("label", "") if isinstance(content, dict) else "",
                            "date": lab(e, "updated")[:10],
                            "version": lab(e, "im:version"),
                        }
                        alt = (name, rec["title"], rec["date"], rec["body"][:80])
                        if (rid and rid in seen) or alt in seen_alt:
                            continue
                        if rid:
                            seen.add(rid)
                        else:
                            seen_alt.add(alt)
                        out.append(rec)
                        added[name] += 1
                    time.sleep(0.2)
        save(out, a.out)  # after each app, so an interrupted run keeps what it got

    save(out, a.out)

    total = Counter(r["app"] for r in out)
    low = Counter(r["app"] for r in out if r.get("rating", 0) <= 3)
    print(f"\n+{len(out) - before} new reviews; {len(out)} in {a.out}", file=sys.stderr)
    print(f"{'app':30} {'new':>6} {'total':>7} {'1-3*':>6}", file=sys.stderr)
    for spec in a.apps:
        name = spec.partition(":")[2] or spec.partition(":")[0]
        flag = "  <- nothing yet" if not total[name] else ""
        print(f"{name[:30]:30} {added[name]:>6} {total[name]:>7} {low[name]:>6}{flag}", file=sys.stderr)
    thin = [s.partition(":")[2] or s.partition(":")[0] for s in a.apps
            if 0 < total[s.partition(":")[2] or s.partition(":")[0]] < 100]
    if thin:
        print(f"\nthin (<100 reviews): {', '.join(thin)}. If they matter, rerun just those with"
              " --countries nz ie in sg za and/or --max-pages 10 (results merge).", file=sys.stderr)
    if empty_slots:
        print(f"\n{len(empty_slots)} app/country/sort combinations came back empty even after retries;"
              " rerun later for those (results merge):", file=sys.stderr)
        for e in empty_slots[:15]:
            print("  " + e, file=sys.stderr)
        if len(empty_slots) > 15:
            print(f"  ... and {len(empty_slots) - 15} more", file=sys.stderr)
    if not out:
        print("\nWARNING: no reviews for any app. Apple serves empty feeds to some networks\n"
              "(often cloud IPs), when throttling, and for small apps. Wait a minute and rerun\n"
              "(it merges), try other --countries; if it stays empty, say so in the write-up and\n"
              "use another counted source (see SKILL.md) rather than presenting no numbers.",
              file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
