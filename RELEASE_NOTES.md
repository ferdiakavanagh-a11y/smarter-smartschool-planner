# Focus mode and faster startup

## New: task Focus mode

- Start Focus directly from a task row using the viewfinder icon beside Pin, or from the task's details.
- The icon appears on hover or keyboard focus and remains visible on touch devices.
- Reminder types such as Meenemen and Meebrengen are excluded.
- Work in a compact, resizable window with the task title, deadline, instructions, attachments, and links.
- Track elapsed time with a stopwatch and pause or resume whenever needed.
- Optionally keep the window on top of other applications.
- Mark the task complete separately from ending a session.
- Exit Focus to restore the previous window size, position, and maximized state.
- Active sessions and task details survive planner sync reloads. Sessions end when the app closes.

## Refined Focus interface

- A dedicated layout puts instructions first, with a quiet timer and a single bottom action bar.
- Focus controls share the main app's button styling and glass materials.
- Hover highlights use the navigation bar's liquid-glass bubble, with responsive press feedback.
- Fancy uses refraction; Performance uses lighter rendering.
- Reduced Motion settings are respected. Focus hover effects do not change normal navigation.

## Faster startup

- Installed libraries stay unpacked, avoiding extraction on every launch.
- Sync, updater, and other optional imports load when needed rather than delaying the first window.
- Local measurements reduced the Python import stage from a median of 3.09 seconds to 0.54 seconds; total launch time varies by device.
- Existing shortcuts, credentials, saved planner data, rendering choices, and update verification are preserved.

## Portable builds

Keep the `_internal` folder beside `SmartschoolPlanner.exe`. The installer includes it automatically.
