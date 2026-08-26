# iOS Shortcut structure

The Shortcut ("TRMNL Margins Tracker") lives only on-device in the Shortcuts app -- it has never been exported, and this file is the only record of its structure outside the app itself. Use this to rebuild it if it's ever lost, or to port the logic elsewhere.

## Trigger
Personal Automation -> **Screenshot Taken** (saved to Photos, Files, or Clipboard) -> **Ask Before Running: OFF**.

## Action sequence

1. **Extract Text from Image** -- Image input: Shortcut Input -> output: `Extracted Text`
2. **If** `Extracted Text` **does not contain** `PAGES` -> **Stop This Shortcut**
3. **Match Text** -- regex `(\d+)\s*[/|]?\s*(\d+)\s*PAGES`, searching in `Extracted Text` -> `Matches`
4. **If** `Matches` **does not have any value** -> **Stop This Shortcut**
5. **Get Group At Index** `1` in `Matches` -> **Set Variable** `Page Count`
6. **Get Group At Index** `2` in `Matches` -> **Set Variable** `Total Pages`
7. **Get Contents of URL** (GET) -> `https://raw.githubusercontent.com/thomasmihaljevic27/reading-trmnl-data/main/reading_data.json`
8. **Get Dictionary from Input** -> input: previous result
9. **Get Value** for `book` in Dictionary
10. **Get Value** for `title` in Dictionary Value -> **Set Variable** `Stored Title`
11. **If** `Extracted Text` **contains** `Stored Title`:
    - **Set Variable** `Same Book` = literal text `true`
    - **If** `Page Count` **is greater than or equal to** `Total Pages`:
      - **Choose from Menu** -- prompt "Finished Book?" -- options Yes / No
      - Yes -> **Set Variable** `Finished` = literal text `true`
      - No -> **Set Variable** `Finished` = literal text `false`
    - **Otherwise:**
      - **Set Variable** `Finished` = literal text `false`
12. **Otherwise** (title not found in the OCR text -- a new book):
    - **Set Variable** `Same Book` = literal text `false`
    - **Choose from Menu** -- prompt "New book detected, mark old as finished?" -- options Yes / No
    - Yes -> **Set Variable** `Finished` = literal text `true`
    - No -> **Set Variable** `Finished` = literal text `false`
13. **Get Contents of URL** (POST) -- the dispatch call:
    - URL: `https://api.github.com/repos/thomasmihaljevic27/reading-trmnl-data/dispatches`
    - Headers: `Accept: application/vnd.github+json`, `Authorization: Bearer <PAT>`
    - Body (JSON):
      ```json
      {
        "event_type": "margins-update",
        "client_payload": {
          "current_page": "<Page Count>",
          "total_pages": "<Total Pages>",
          "same_book": "<Same Book>",
          "book_finished": "<Finished>",
          "raw_ocr_text": "<Extracted Text>"
        }
      }
      ```
    - `client_payload` must be a nested Dictionary-type field in the Get Contents of URL action's Request Body, not five flat top-level fields -- the workflow reads `github.event.client_payload.current_page`, etc., and a flat structure won't match that path.

## Notes on literal true/false values
Shortcuts' "Set Variable" action only accepts Magic Variables as input, not typed text directly. To set a variable to the literal string `true` or `false`: add a **Text** action containing just that word, then Set Variable -> Select Variable -> pick that Text action's output. Using the Boolean type instead of literal text will not match `update_reading_data.py`'s `env_flag()` check, which does an exact string comparison against `"true"`.

## Testing without a real screenshot
Play (▶) does not reliably provide Shortcut Input the way a real screenshot trigger does. To test branching logic without taking a real screenshot, temporarily insert a **Text** action containing a fake OCR block, then a **Set Variable** action assigning it to `Extracted Text` (via Select Variable), placed immediately after step 1. Remove both before relying on the Shortcut normally -- leaving this in place means the Shortcut ignores real screenshots.
