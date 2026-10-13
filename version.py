"""keeps track of current version, bump when pushing a new release"""

__version__ = "2.0.6"

# Update these notes alongside the version for each release (offline installer fallback).
RELEASE_NOTES = """## Updates
- Update prompts now use the planner's shared glass interface and themes.
- A What's new popup shows the new features once after an update.

## Performance and usability
- Faster planner redraws and glass texture generation.
- Less work when reopening Settings, with a shorter menu entrance.
- Unused glass filters are released after resizing or changing menus.
- Better keyboard visibility and labels for settings controls.
"""
