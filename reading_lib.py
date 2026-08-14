"""
reading_lib.py

Shared functions for the Margins -> TRMNL pipeline. Imported by:
  - update_reading_data.py   (runs on every screenshot, via GitHub Actions)
  - bootstrap_import.py      (runs once, by hand, to backfill history)

Keeping this logic in one shared file means the streak/calendar math is
defined exactly once -- the recurring script and the one-time backfill
script can never quietly drift apart and produce different answers for
the same input.
"""

import json
import urllib.request
import urllib.parse
from datetime import date, timedelta
from calendar import monthrange

DATA_PATH = "reading_data.json"


def load_data():
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)
    with open(DATA_PATH, "a") as f:
        f.write("\n")


def recompute_streak(days_read_iso):
    """
    Count consecutive reading days ending today.

    WHY FULL ISO DATES ("2026-08-13") AND NOT JUST DAY-NUMBERS:
    Day-of-month resets every month, so day 31 and day 1 look unrelated
    unless you know which months they belong to. Full date objects
    subtract cleanly across month and year boundaries.
    """
    read_set = set(days_read_iso)
    streak = 0
    cursor = date.today()
    while cursor.isoformat() in read_set:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def recompute_month_view(days_read_iso, today=None):
    """
    Derive the three fields the calendar plugin needs to draw itself:
      - days_in_month, first_weekday (Sunday=0), current_month_days_read
    See update_reading_data.py for why this lives here instead of Liquid.
    """
    today = today or date.today()
    days_in_month = monthrange(today.year, today.month)[1]

    first_of_month = date(today.year, today.month, 1)
    first_weekday = (first_of_month.weekday() + 1) % 7  # Mon=0..Sun=6 -> Sun=0..Sat=6

    month_prefix = today.strftime("%Y-%m-")
    current_month_days_read = sorted(
        int(d.split("-")[2])
        for d in days_read_iso
        if d.startswith(month_prefix)
    )

    return days_in_month, first_weekday, current_month_days_read


def lookup_isbn(title, author):
    """
    Best-effort ISBN lookup via Open Library's free search API -- used
    when a new book is detected from OCR text, which has no ISBN on
    screen (Margins' Currently Reading card never shows one).

    Returns "" on any failure (no match, network error, rate limit) --
    the cover image just won't render for that book, which is a fine
    degraded state for a personal e-ink display. Never raises, so a
    flaky lookup can't fail the whole Action run.
    """
    try:
        query = urllib.parse.urlencode({
            "title": title,
            "author": author,
            "limit": 1,
            "fields": "isbn",
        })
        url = f"https://openlibrary.org/search.json?{query}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        docs = data.get("docs", [])
        if docs and docs[0].get("isbn"):
            return docs[0]["isbn"][0]
    except Exception as e:
        print(f"ISBN lookup failed for {title!r} by {author!r}: {e}")
    return ""


def parse_title_author_from_ocr(raw_text, page_line_marker="PAGES"):
    """
    Best-effort title/author extraction from a full-screen OCR dump.

    ASSUMPTION THIS RELIES ON (true for Margins' Currently Reading card
    as of this writing -- re-check if Margins changes its layout):
    title and author sit as the two non-empty lines immediately above
    the "X / Y PAGES" line, in that order, with nothing else between
    them. Live Text preserves local top-to-bottom adjacency within a
    single visual block even when it jumbles order across a full,
    multi-column screenshot -- so anchoring on the two lines directly
    above the page count is more reliable than trying to parse the
    whole page.

    Only used when a NEW book is detected (title changed) -- the
    common "same book, more pages" case never calls this, since the
    title is already known from the stored data.

    Returns (title, author) -- either may be "" if parsing comes up
    short; caller should treat empty strings as "couldn't tell" rather
    than crash.
    """
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    page_idx = next(
        (i for i, l in enumerate(lines) if page_line_marker.upper() in l.upper()),
        None,
    )
    if page_idx is None or page_idx < 2:
        return "", ""
    author = lines[page_idx - 1]
    title = lines[page_idx - 2]
    return title, author
