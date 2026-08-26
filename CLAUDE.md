# CLAUDE.md

## Purpose
Personal reading-tracker pipeline turning a Margins app screenshot into three live TRMNL e-ink dashboard widgets (currently-reading, streak calendar, yearly goal). An iOS Shortcut OCRs the screenshot, POSTs a `repository_dispatch` to this repo, GitHub Actions runs a Python script that updates `reading_data.json`, and three TRMNL Private Plugins poll that file directly via its raw GitHub URL.

## Stack
- Python 3 (stdlib only -- urllib, json, datetime, calendar)
- GitHub Actions (repository_dispatch trigger)
- TRMNL Private Plugins, Liquid templates (Polling strategy, GET, no auth)
- Open Library API (free, keyless) for ISBN lookup + cover art
- iOS Shortcuts (external -- lives on-device only, not in this repo)

## Layout
- `reading_data.json` -- live state. MUST stay committed + public at repo root; TRMNL polls it directly via raw.githubusercontent.com. Never gitignore this.
- `reading_lib.py` -- shared streak/calendar/ISBN-lookup logic
- `update_reading_data.py` -- runs on every screenshot via the Actions workflow
- `bootstrap_import.py` -- one-time manual backfill, safe to re-run
- `.github/workflows/update-reading.yml` -- repository_dispatch -> Python -> commit
- `trmnl-plugins/*.liquid` -- source of truth for the 3 plugin templates. Not auto-deployed -- after any edit, manually paste into TRMNL's Markup Editor, Save, then Force Refresh. See `trmnl-plugins/README.md` for the exact per-plugin settings (strategy, headers, refresh interval, etc.) that live only in TRMNL's UI otherwise.
- `docs/shortcut-notes.md` -- iOS Shortcut structure, for reference if it ever needs rebuilding or porting.

## Running it
- Local test, no real screenshot needed:
  `SAME_BOOK=true BOOK_FINISHED=false CURRENT_PAGE=45 TOTAL_PAGES=496 python3 update_reading_data.py`
- Backfill: edit the constants at the top of bootstrap_import.py, then `python3 bootstrap_import.py`
- Real pipeline has no local trigger: screenshot in Margins -> iOS Shortcut -> GitHub Actions -> commit
- After any .liquid edit: paste into TRMNL's Markup Editor -> Save -> Force Refresh. The editor's live-typing preview can show stale/placeholder data -- always Force Refresh before trusting what renders.

## Don't
- Don't assume the OCR'd page separator is `/`. Live Text has rendered it as `/`, `|`, and nothing at all across different screenshots. Regex must tolerate all three: `(\d+)\s*[/|]?\s*(\d+)\s*PAGES`.
- Don't store finished_books entries as bare strings. They're `{title, author, isbn}` dicts, with an optional `cover_url` that overrides the ISBN-based Open Library lookup when present. `_finish_book()`'s dedup logic assumes dict access.
- Don't put a GitHub PAT anywhere in this repo or in client-visible code. It lives only in the iOS Shortcut's Authorization header, on-device.
- Don't set `height: 100%` inline on a TRMNL `.layout` element. The platform calculates that height automatically; overriding it has silently broken vertical centering before. Use `layout--center-y` instead.
- Don't hand-edit reading_data.json without validating the JSON first. One missing comma once broke all three plugins simultaneously, since they all poll this one file.
- Don't move files into a src/ layout without also updating update-reading.yml's `run:` step -- the workflow assumes repo-root execution.

Every time I get corrected on something, add a rule here so it doesn't repeat.
