#!/usr/bin/env python3
"""Find App Store apps for one or more search terms.

Usage: find_apps.py TERM [TERM...] [--country us] [--limit 15] [--json]

Uses Apple's public iTunes Search API (no key). Results from all terms are
de-duplicated by trackId and printed most-rated first:

    id  ratings  avgRating  name  (seller, genre)

Pass the ids to fetch_reviews.py as ID:Name.
"""
import argparse
import json
import sys
import time
import urllib.parse
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (compatible; user-pain-research/1.0)"


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


def search(term, country, limit):
    q = urllib.parse.urlencode(
        {"term": term, "entity": "software", "country": country, "limit": limit}
    )
    return fetch_json(f"https://itunes.apple.com/search?{q}").get("results", [])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("terms", nargs="+")
    ap.add_argument("--country", default="us")
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--json", action="store_true", help="print JSON instead of a table")
    a = ap.parse_args()

    apps = {}
    for term in a.terms:
        try:
            for r in search(term, a.country, a.limit):
                apps.setdefault(r["trackId"], r)
        except Exception as e:  # keep going on a failed term
            print(f"search failed for {term!r}: {e}", file=sys.stderr)

    rows = sorted(apps.values(), key=lambda r: r.get("userRatingCount", 0), reverse=True)
    if a.json:
        keep = ("trackId", "trackName", "sellerName", "primaryGenreName",
                "userRatingCount", "averageUserRating", "price", "trackViewUrl")
        json.dump([{k: r.get(k) for k in keep} for r in rows], sys.stdout, indent=2)
        print()
        return
    for r in rows:
        print(f"{r['trackId']}  {r.get('userRatingCount', 0):>8}  "
              f"{r.get('averageUserRating', 0):.2f}  {r.get('trackName')}  "
              f"({r.get('sellerName')}, {r.get('primaryGenreName')})")
    if not rows:
        print("no apps found", file=sys.stderr)


if __name__ == "__main__":
    main()
