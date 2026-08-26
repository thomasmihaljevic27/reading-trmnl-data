# TRMNL plugin settings

These `.liquid` files are the source of truth for the markup, but the settings below only exist inside TRMNL's own UI -- there's no way to store or version them in this repo. If a plugin ever needs to be rebuilt from scratch, use this as the reference.

All three plugins share identical settings except for the pasted markup itself:

| Field | Value |
|---|---|
| Strategy | Polling |
| Polling URL | `https://raw.githubusercontent.com/thomasmihaljevic27/reading-trmnl-data/main/reading_data.json` |
| Polling Verb | GET |
| Polling Headers | (blank -- public repo, no auth needed) |
| Polling Body | (blank -- only applies to POST) |
| Enable OAuth | No |
| Form Fields | (blank -- no user-configurable settings) |
| Remove bleed margin | No |
| Enable Dark Mode | No |
| Refresh interval | 15 min |

**Framework CSS version:** whatever the dropdown currently shows as latest. Never confirmed a specific version number against TRMNL's docs -- worth checking `trmnl.com/framework/docs` if a future template edit behaves unexpectedly, since TRMNL has released multiple framework versions (v1.2, v2, v3) with real behavioral differences between them.

## Deploying an edit
There's no auto-deploy. After changing a `.liquid` file here:
1. Open the matching plugin in TRMNL's dashboard
2. Open the Markup Editor
3. Paste the full updated file contents (Full tab)
4. Save
5. Click **Force Refresh** -- the live-typing preview in the editor can show stale/placeholder data, so always Force Refresh before judging whether an edit worked

## Multiple view sizes
Each plugin also has separate tabs in the Markup Editor for Half Horizontal, Half Vertical, and Quadrant layouts (in addition to Full). TRMNL only allows a plugin to be placed in a mashup slot of a given size if that tab has markup in it -- an empty tab makes that size unselectable in the Playlist/mashup builder. If a plugin is missing from a size option, check whether that tab actually has content.
