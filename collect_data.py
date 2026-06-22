"""
Reddit r/nba data collector for TakeMeter.
Uses Reddit's public JSON API — no account, PRAW, or API key required.

Usage:
    python collect_data.py

Output:
    nba_raw.json  — raw collected posts/comments
    nba_data.csv  — pre-labeled CSV ready for your review and correction

The CSV has columns: text, label, notes
  - text:  the post title + body (or comment body)
  - label: pre-assigned label (REVIEW AND CORRECT EVERY ROW before uploading)
  - notes: why this was assigned this label (to help you review)

Label map:
  analysis  — structured argument with specific, verifiable evidence
  hot_take  — bold opinion asserted without meaningful supporting evidence
  reaction  — immediate emotional response to a specific event
"""

import requests
import json
import csv
import time
import re

HEADERS = {"User-Agent": "TakeMeter/1.0 (AI201 class project; contact: student)"}

# ── Sources to collect from ────────────────────────────────────────────────
SOURCES = [
    # Analysis-heavy posts (flaired or titled)
    ("https://www.reddit.com/r/nba/search.json", {"q": "analysis breakdown stats", "sort": "top", "t": "year", "limit": 25, "restrict_sr": 1}),
    ("https://www.reddit.com/r/nba/search.json", {"q": "film breakdown advanced metrics", "sort": "top", "t": "year", "limit": 25, "restrict_sr": 1}),
    ("https://www.reddit.com/r/nba/search.json", {"q": "historically best worst all time compared", "sort": "top", "t": "year", "limit": 25, "restrict_sr": 1}),
    # Hot take / opinion posts
    ("https://www.reddit.com/r/nba/search.json", {"q": "unpopular opinion hot take overrated", "sort": "top", "t": "year", "limit": 25, "restrict_sr": 1}),
    ("https://www.reddit.com/r/nba/search.json", {"q": "change my mind controversial take", "sort": "top", "t": "year", "limit": 25, "restrict_sr": 1}),
    # Reaction posts
    ("https://www.reddit.com/r/nba/search.json", {"q": "cannot believe insane unbelievable just happened", "sort": "top", "t": "month", "limit": 25, "restrict_sr": 1}),
    ("https://www.reddit.com/r/nba/search.json", {"q": "trade reaction free agency signing", "sort": "top", "t": "year", "limit": 25, "restrict_sr": 1}),
    # General hot/top posts for variety
    ("https://www.reddit.com/r/nba/top.json", {"t": "month", "limit": 50}),
    ("https://www.reddit.com/r/nba/top.json", {"t": "week", "limit": 50}),
]

# ── Heuristic pre-labeler ─────────────────────────────────────────────────
# These patterns give a starting label. YOU MUST REVIEW AND CORRECT ALL OF THEM.

ANALYSIS_SIGNALS = [
    r'\d+\.?\d*%',           # percentages
    r'\b(per game|per 36|per 100|net rating|ts%|efg%|ortg|drtg|war|bpm|vorp|win share)\b',
    r'\b(historically|history|all.time|ever recorded|since \d{4})\b',
    r'\b(film|tape|breakdown|tactically|scheme|defensive rotation|offensive system)\b',
    r'\b(compared to|relative to|in context|adjusted for|controlling for)\b',
    r'\b(data show|stats show|numbers suggest|evidence|proof)\b',
]

HOT_TAKE_SIGNALS = [
    r'\b(overrated|underrated|no debate|change my mind|unpopular opinion|hot take|actually|controversial)\b',
    r'\b(never|always|best ever|worst ever|most overrated|most underrated)\b',
    r'\b(cope|delusional|wrong|admit it|face it|wake up)\b',
    r'\b(goat|not goat|shouldn.t be|doesn.t deserve|fraudulent)\b',
]

REACTION_SIGNALS = [
    r'\b(WHAT|OMG|WOW|NO WAY|ARE YOU KIDDING|UNBELIEVABLE|INSANE|HOLY|OH MY|I CANNOT)\b',
    r'\b(just happened|right now|tonight|this game|that play|did you see)\b',
    r'\b(traded|trade|signing|signed|fired|hired|injury|injured|out for)\b',
    r'!{2,}',                # multiple exclamation marks
    r'[A-Z]{4,}',            # all-caps words (emotional)
]


def count_signals(text, patterns):
    text_lower = text.lower()
    text_upper = text.upper()
    count = 0
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            count += 1
    return count


def heuristic_label(text):
    a = count_signals(text, ANALYSIS_SIGNALS)
    h = count_signals(text, HOT_TAKE_SIGNALS)
    r = count_signals(text, REACTION_SIGNALS)
    scores = {"analysis": a, "hot_take": h, "reaction": r}
    winner = max(scores, key=scores.get)
    if scores[winner] == 0:
        return "hot_take", "no clear signals — defaulted to hot_take; REVIEW"
    if list(scores.values()).count(scores[winner]) > 1:
        return "hot_take", f"tied ({scores}) — defaulted to hot_take; REVIEW"
    note = f"signals: analysis={a}, hot_take={h}, reaction={r}"
    return winner, note


def fetch_posts(url, params):
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("data", {}).get("children", [])
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return []


def clean_text(title, body):
    text = title.strip()
    if body and body not in ("[removed]", "[deleted]", ""):
        body_clean = body.strip().replace("\n", " ")
        text = text + " " + body_clean
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def main():
    all_posts = []
    seen_ids = set()

    print("Collecting r/nba posts...")
    for url, params in SOURCES:
        print(f"  Fetching: {url} ({params.get('q', params.get('t', ''))})")
        children = fetch_posts(url, params)
        for child in children:
            post = child.get("data", {})
            pid = post.get("id", "")
            if not pid or pid in seen_ids:
                continue
            seen_ids.add(pid)

            title = post.get("title", "")
            body = post.get("selftext", "")
            text = clean_text(title, body)

            # Skip very short posts (likely just image/video links)
            if len(text.split()) < 8:
                continue
            # Skip removed/deleted
            if "[removed]" in text or "[deleted]" in text:
                continue

            all_posts.append({
                "id": pid,
                "text": text[:600],  # cap at 600 chars
                "score": post.get("score", 0),
                "flair": post.get("link_flair_text", ""),
            })
        time.sleep(1.5)  # polite delay

    print(f"\nCollected {len(all_posts)} unique posts")

    # Save raw
    with open("nba_raw.json", "w") as f:
        json.dump(all_posts, f, indent=2)
    print("Saved: nba_raw.json")

    # Pre-label and write CSV
    rows = []
    label_counts = {"analysis": 0, "hot_take": 0, "reaction": 0}

    for post in all_posts:
        label, note = heuristic_label(post["text"])
        label_counts[label] += 1
        rows.append({
            "text": post["text"],
            "label": label,
            "notes": note,
        })

    with open("nba_data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "notes"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved: nba_data.csv ({len(rows)} rows)")
    print("\nPre-label distribution (BEFORE your review):")
    for label, count in label_counts.items():
        pct = count / len(rows) * 100 if rows else 0
        print(f"  {label:12s}: {count:3d}  ({pct:.0f}%)")

    print("\n⚠️  NEXT STEPS:")
    print("  1. Open nba_data.csv in a spreadsheet app (Numbers, Excel, Google Sheets)")
    print("  2. Read every row and correct the 'label' column where wrong")
    print("  3. Add more rows manually if any label is under ~60 examples")
    print("  4. Delete the 'notes' column before uploading to Colab")
    print("  5. Save final file as nba_labeled.csv")


if __name__ == "__main__":
    main()
