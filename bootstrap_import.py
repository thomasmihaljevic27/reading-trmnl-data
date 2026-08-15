#!/usr/bin/env python3
"""
bootstrap_import.py

ONE-TIME setup script -- run this by hand (`python3 bootstrap_import.py`)
BEFORE you ever trigger the Shortcut, to seed reading_data.json with
history Margins can't export automatically:
  - books you've already finished this year (for the yearly goal count)
  - days you've already read this month (for the streak/calendar)

This is a separate file from update_reading_data.py on purpose: backfill
logic only ever runs once, so it shouldn't live inside the script that
runs on every screenshot for the rest of the year. It imports the same
recompute_streak/recompute_month_view functions from reading_lib.py, so
the numbers it produces are computed identically to how the recurring
script computes them -- no separate math to keep in sync.

HOW TO USE:
1. Edit the two values below to match your actual Margins data.
   - FINISHED_BOOKS_THIS_YEAR: title + author from Margins' "Read" list
     for 2026. ISBN is looked up automatically -- don't fill it in.
   - YEARLY_GOAL: your reading challenge target.
   - DAYS_READ_THIS_MONTH: look at the Stats calendar screenshot --
     just the day-of-month numbers for the teal/filled squares.
2. Run: python3 bootstrap_import.py
3. Check the printed summary and the resulting reading_data.json.
4. Commit it, THEN move on to setting up the Shortcut (SETUP.md step 5+).

Safe to re-run: it overwrites book/streak/goal history wholesale from
these lists rather than appending, so editing and re-running fixes a
typo without creating duplicates.

v2: FINISHED_BOOKS_THIS_YEAR entries are now {title, author} dicts
instead of bare title strings -- author is needed for the ISBN lookup,
which now runs here too, matching how update_reading_data.py stores
finished books (see that file's _finish_book() for why).
"""

from datetime import date, datetime, timezone
from reading_lib import (
    load_data,
    save_data,
    recompute_streak,
    recompute_month_view,
    lookup_isbn,
)

# --- EDIT THESE THREE VALUES ---

FINISHED_BOOKS_THIS_YEAR = [
    {"title": "Example Book One", "author": "Example Author"},
    {"title": "Example Book Two", "author": "Example Author"},
]

YEARLY_GOAL = 40

DAYS_READ_THIS_MONTH = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13]

# --- END EDITABLE SECTION ---


def main():
    data = load_data()
    today = date.today()

    # Goal: the list IS the source of truth; the count is derived from
    # it, same as _finish_book() does in the recurring script. ISBN
    # lookup runs here (once,
