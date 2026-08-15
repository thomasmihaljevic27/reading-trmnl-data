#!/usr/bin/env python3
"""
update_reading_data.py

Regenerates reading_data.json from a single OCR'd Margins screenshot.
Runs inside .github/workflows/update-reading.yml, which sets the
os.environ.get(...) values below from the Shortcut's repository_dispatch
payload.

WHAT THE SHORTCUT HAS ALREADY DECIDED BEFORE THIS RUNS:
The Shortcut fetches the current reading_data.json itself, compares the
OCR'd text against the stored book title, and only prompts you when
something is genuinely ambiguous (you appear to have finished a book, or
a different book is now showing). This script trusts those flags rather
than re-deriving them -- SAME_BOOK and BOOK_FINISHED are decisions, not
raw data, and re-deciding them here (possibly differently) would let the
two ends of the pipeline disagree with each other.

INPUTS (all set by the GitHub Actions workflow from client_payload):
  CURRENT_PAGE   - int, OCR'd current page
  TOTAL_PAGES    - int, OCR'd total pages
  SAME_BOOK      - "true"/"false" -- does the OCR text still match the
                   book already stored in reading_data.json?
  BOOK_FINISHED  - "true"/"false" -- only meaningful when the Shortcut
                   actually asked (see above); defaults to "false"
  RAW_OCR_TEXT   - the full Live Text dump of the screenshot -- only
                   parsed for title/author when SAME_BOOK is false,
                   since the same-book case already has that data

v2: goal.finished_books now stores {title, author, isbn} objects instead
of bare title strings, so the yearly_goal TRMNL plugin can show cover
art for each finished book. _finish_book() below does the ISBN lookup.
"""

import os
from datetime import datetime, date, timezone
from reading_lib import (
    load_data,
    save_data,
    recompute_streak,
    recompute_month_view,
    lookup_isbn,
    parse_title_author_from_ocr,
)


def env_flag(name, default="false"):
    return os.environ.get(name, default).strip().lower() == "true"


def main():
    data = load_data()
    today_iso = date.today().isoformat()

    current_page = int(os.environ["CURRENT_PAGE"])
    total_pages = int(os.environ["TOTAL_PAGES"])
    same_book = env_flag("SAME_BOOK", "true")
    book_finished = env_flag("BOOK_FINISHED", "false")
    raw_ocr_text = os.environ.get("RAW_OCR_TEXT", "")

    # A successful, parseable screenshot of the Currently Reading card is
    # itself the "I engaged with reading today" signal -- see SETUP.md
    # for the tradeoff (a screenshot with no new pages still counts).
    if today_iso not in data["streak"]["days_read"]:
        data["streak"]["days_read"].append(today_iso)

    if same_book:
        # --- Ordinary progress update: same book, page count moved ---
        data["book"]["current_page"] = current_page
        data["book"]["total_pages"] = total_pages

        if book_finished:
