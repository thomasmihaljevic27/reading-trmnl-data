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
1. Edit the three values below to match your actual Margins data.
   - FINISHED_BOOKS_THIS_YEAR: look at Margins' "Read" list for 2026.
   - YEARLY_GOAL: your reading challenge target.
   - DAYS_READ_THIS_MONTH: look at the Stats calendar screenshot --
     just the day-of-month numbers for the teal/filled squares.
2. Run: python3 bootstrap_import.py
3. Check the printed summary and the resulting reading_data.json.
4. Commit it, THEN move on to setting up the Shortcut (SETUP.md step 5+).

Safe to re-run: it overwrites book/streak/goal history wholesale from
these three lists rather than appending, so editing and re-running fixes
a typo without creating duplicates.
"""

from datetime import date, datetime, timezone
from reading_lib import load_data, save_data, recompute_streak, recompute_month_view

# --- EDIT THESE THREE VALUES ---

FINISHED_BOOKS_THIS_YEAR = [
    "Example Book One",
    "Example Book Two",
]

YEARLY_GOAL = 40

DAYS_READ_THIS_MONTH = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13]

# --- END EDITABLE SECTION ---


def main():
    data = load_data()
    today = date.today()

    # Goal: the list IS the source of truth; the count is derived from
    # it, same as _finish_book() does in the recurring script.
    data["goal"]["finished_books"] = FINISHED_BOOKS_THIS_YEAR
    data["goal"]["books_read_this_year"] = len(FINISHED_BOOKS_THIS_YEAR)
    data["goal"]["yearly_goal"] = YEARLY_GOAL

    # Streak: convert day-of-month numbers to full ISO dates for the
    # CURRENT month/year -- see reading_lib.recompute_streak for why
    # full dates matter (day-of-month alone can't cross a month
    # boundary correctly).
    month_prefix = today.strftime("%Y-%m-")
    new_dates = {f"{month_prefix}{day:02d}" for day in DAYS_READ_THIS_MONTH}
    existing_dates = set(data["streak"]["days_read"])
    data["streak"]["days_read"] = sorted(existing_dates | new_dates)

    # Recompute every derived field the same way the recurring script does.
    data["streak"]["current_streak"] = recompute_streak(data["streak"]["days_read"])
    days_in_month, first_weekday, current_month_days_read = recompute_month_view(
        data["streak"]["days_read"]
    )
    data["streak"]["days_in_month"] = days_in_month
    data["streak"]["first_weekday"] = first_weekday
    data["streak"]["current_month_days_read"] = current_month_days_read
    data["last_updated"] = datetime.now(timezone.utc).isoformat()

    save_data(data)
    print(
        f"Backfilled {len(FINISHED_BOOKS_THIS_YEAR)} finished books, "
        f"{len(new_dates)} reading days this month.\n"
        f"streak={data['streak']['current_streak']}  "
        f"goal={data['goal']['books_read_this_year']}/{data['goal']['yearly_goal']}"
    )


if __name__ == "__main__":
    main()
