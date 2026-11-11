# Qt Quick interface

Production launches through `desktop_app.py` in the repository root. Install the
root requirements, run `python compile_shaders.py`, then start the desktop app.
See the root README, SETUP.md and BUILD_EXE.md for account and packaging details.

The QML view is connected to real snapshot/state services through `runtime.py`,
`backend.py`, `production_model.py` and `sections.py`. `SelectorLens.qml` is shared
by the slider handles and top-row buttons. `Glass.qml` and the two GLSL shaders
implement the optical surfaces and procedural wallpaper.

## Synthetic development harness

For isolated visual work without credentials or production state:

```powershell
powershell -ExecutionPolicy Bypass -File qml_app/setup.ps1
& './qml_app/.venv/Scripts/python.exe' -m qml_app.main --count 36
```

Optional harness flags include `--count 0`, `--count 1000`, `--mode performance`
and `--smoke`. Harness edits are memory-only. Production never selects these
fixtures. The `.venv`, generated shader binaries and evidence remain ignored.

The interface uses native Qt controls, queued service callbacks, list
virtualization, independent frosting/distortion, four procedural backgrounds,
reduced motion, high contrast and an opaque shader-error fallback. Frame timing
limits from the earlier prototype still apply; integration does not establish a
new performance advantage or 60 fps guarantee.

Background choices are Silk (the original Satin folds), Soft colours (the original
colour fields), Aurora (a teal/azure veil) and Contour (quiet pearl/slate folds).
Each has a light and dark appearance and uses the existing animation controls.
Reduced motion stops wallpaper animation. Silk and Soft colours retain their
original pixels; Aurora and Contour use the remaining saved indices.

## School panels

The bottom selector has five tabs: To-do, Planner, Grades, LVS and Messages.
To-do opens Missed and Completed assignments in separate floating sheets.
Missed includes every unfinished past-due task; both sheets allow details and
completion/restoration without changing the main list filters. Collections preserve
row identity and animate additions/removals. Saving updates state immediately;
only the exiting visual card is retained until its animation finishes. Successor
corners update immediately, including final-row and rapid-Undo cases. Search and
filtering stay immediate; reduced motion uses a short fade without displacement.
Shared sheets and toasts use restrained changes to the existing glass material.
The compact Gemini summary
button and its results sit inside the Week ahead graph card.

Planner combines the full timetable with lesson tasks from Schedule, retaining
classes without tasks, schedule-only events and attachments. Teacher replacements
opens a floating glass sheet. Planner keeps its title and replacement button
visible while timetable rows scroll underneath the header boundary. Each open or Refresh rediscovers the current link in
the approved replacement/room-change homepage block, follows only school/WOPI
redirects and validates a read-only Microsoft PowerPoint viewing form. Other
homepage blocks are excluded. The original provider supplies slide controls.

The embedded Qt WebEngine profile exists only while the sheet is open. It uses
memory-only storage, receives no school cookies, and POSTs the short-lived viewing
token only to the validated official PowerPoint viewer. Downloads, new windows,
local files, device permissions and certificate exceptions are blocked. Closing
the sheet or switching accounts discards the browser and any queued result. No
external document converter or persistent preview cache is used. This currently
supports the verified Smartschool WOPI PowerPoint ReadingView, not arbitrary PPTX
links or other document services.

Grades places Report cards opposite the subject selector on the same row.
Report cards offer View and Download. Both check freshness and reuse one cached
PDF per account/report. ETag/Last-Modified allow conditional requests; without
server validators, bytes must be fetched to compare SHA-256. Identical content
creates no duplicate saved file. Changed content atomically replaces that copy;
failed refreshes keep the old file and do not open a stale report. View opens the
native floating PDF viewer after a successful refresh. Reports filter by school year; actual
academic period names filter saved grades. Courses, teachers and support links
have been removed. Settings contains the central Offline files button; files
remain accessible from their original message, assignment or report. Copies and
local message tasks stay in account-specific `data/school/` directories.

Messages offers Inbox, Sent, Local drafts, Trash, Scheduled and School drafts.
Refresh loads 50 messages; Load older messages increases the bounded inventory up
to 2,000. Search filters loaded subjects/senders. Readers support selectable/copyable
plain text, Reply, Reply all, Forward, downloads and local planner tasks. Replies
respect school permissions. The installed API returns display names rather than
recipient identities, so reply hints require explicit school-recipient selection.
Replies/forwards open editable new-form drafts with a plain-text quote; no unverified
thread-mode number is used. Bcc is never copied to reply/forward context. Original
attachments require explicit local reattachment.

The native composer supports multiple To/Cc/Bcc recipients and local files. Search
suggestions float above the form without moving Subject/body; they preserve typing
focus and keyboard selection. Classes/offices such as Secretariaat appear when the
school publishes them. Each selected identity is freshly resolved before sending.
File preparation runs off the GUI thread, limited to 20 files and 50 MB combined;
selected local bytes are checked again before their one-attempt upload. Uploads
accept explicit local file types as data; download/open restrictions are separate.
No file is uploaded before Send.

Drafts save locally per account, while typing and when closing the composer/app.
The atomic store permits 200 drafts and 25 MiB total. Oversized text is retained
with a save error rather than silently truncated. Account changes flush old local
work before clearing the view; failed writes remain private in account-specific
memory recovery, and app exit is blocked until that work is saved. Send snapshots
are durably locked before the final POST. Redirects, transport retries and SDK
authentication replay are disabled for sending; uncertain delivery stays locked
across restart until the user explicitly starts another message. Actual delivery
has not been tested with a real message.

Inbox/Sent messages can move to Trash using the verified one-attempt command and
live folder membership. An uncertain change blocks further message actions until
an explicit successful refresh. Cached attachments follow the new folder; offline
files remain. The SDK has no verified restore, scheduling-edit, remote draft-save
or threaded-reply mapping, so those operations remain in Smartschool. School drafts,
scheduled messages and Trash are readable here without unsupported mutation buttons.

Gemini replies open the native composer. A late generated result saves separately
in Local drafts if a newer draft is active, preserving current input and focus.
No message is sent automatically. All development sends/deletes/contacts were mocked.

The two Gemini actions are explicit: draft an editable message reply, or summarise
unfinished tasks for the next seven days. They send school text only when pressed,
never send a message, and never change school deadlines. Without an API key, the
grey buttons explain the requirement in a glass sheet.

Downloads validate account, source membership, school origin and redirects, reject
active file types and HTML login pages, and are limited to 50 MB. Planner downloads
use attachment URLs already supplied by Smartschool; ID-only routes are not invented.
Reports, task attachments and registered lesson files share a floating viewer for
PDFs, images and plain text. PDFs open at readable page width with vertical scrolling;
a compact bottom glass toolbar holds page navigation, bounded zoom, whole-page fit,
selectable page text and Save as. The sheet uses the available window space and the
toolbar wraps at narrow widths. Text is inert and limited to 256 KB. Closing releases the
PDF handle. Account changes clear the preview. Supported Office documents, archives
and media download locally and open in their associated local application, as
requested; other formats retain Save as. No files are uploaded for conversion.
Planner files reuse a cache entry and verify freshness before viewing. Locally
edited Office copies are protected from overwrite: Save as or remove that copy
before refreshing it.

Validation uses synthetic offscreen UI data. The live approved replacement block,
redirect chain and read-only PowerPoint form were checked with the saved session.
A scoped real Office browser probe reproduced the blocked required static CDN
assets. Allowing only the exact observed HTTPS CDN host for GET scripts, styles,
images and fonts produced loaded acknowledgement, 14 controls and 2 canvases.
A 45-second deadline surfaces failure instead of an indefinite splash; validated
Office origin/frame messages and a load revision prevent false/stale readiness.
A final live rerun of the strengthened acknowledgement was blocked by session
expiry; no further login/MFA retries were attempted. The packaged EXE is unverified.
Qt WebEngine's own sandbox remains enabled; its synthetic browser test requires a
process environment that permits Chromium's child processes.

## Attribution

See THIRD_PARTY_NOTICES.md and preserve the adapted material code's MIT notices.
