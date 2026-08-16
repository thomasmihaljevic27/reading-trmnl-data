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
            # The Shortcut only sends this when current_page reached
            # total_pages AND you confirmed the "Finished?" prompt --
            # never inferred silently, since OCR misreads near the end
            # of a book (e.g. 42/427 vs 427/427) are exactly the kind
            # of thing worth a human glance before it counts.
            _finish_book(data, data["book"]["title"], data["book"]["author"])

    else:
        # --- A different book is now showing: title changed ---
        if book_finished:
            # You confirmed via the prompt that the PREVIOUS book (still
            # in `data["book"]` at this point) was finished.
            _finish_book(data, data["book"]["title"], data["book"]["author"])

        new_title, new_author = parse_title_author_from_ocr(raw_ocr_text)
        isbn = lookup_isbn(new_title, new_author) if new_title else ""

        data["book"] = {
            "title": new_title or "(unrecognized)",
            "author": new_author,
            "isbn": isbn,
            "current_page": current_page,
            "total_pages": total_pages,
        }

    # --- Recompute every derived field from the source-of-truth lists ---
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
        f"same_book={same_book} finished={book_finished}  "
        f"book={data['book']['title']!r}  "
        f"page={data['book']['current_page']}/{data['book']['total_pages']}  "
        f"streak={data['streak']['current_streak']}  "
        f"goal={data['goal']['books_read_this_year']}/{data['goal']['yearly_goal']}"
    )


def _finish_book(data, title, author=""):
    """
    Record a finished book: append to the list, count derives from len().

    v2: finished_books now stores {title, author, isbn} dicts instead of
    bare title strings, so yearly_goal.liquid can render cover art.
    Reuses lookup_isbn() -- the same Open Library helper this script
    already calls for the currently-reading book -- so there's no second
    ISBN-lookup implementation to keep in sync.
    """
    if not title:
        return
    existing_titles = {b["title"] for b in data["goal"]["finished_books"]}
    if title not in existing_titles:
        isbn = lookup_isbn(title, author)
        data["goal"]["finished_books"].append({
            "title": title,
            "author": author,
            "isbn": isbn,
        })
    data["goal"]["books_read_this_year"] = len(data["goal"]["finished_books"])


if __name__ == "__main__":
    main()
