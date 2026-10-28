"""keeps track of current version, bump when pushing a new release"""

__version__ = "2.1.2"

# Prepared for the next release; the version/tag must be selected before publishing.
RELEASE_NOTES = """## Reliability and data safety
Improved deadline parsing, safer handling of incomplete school responses,
and protection against conflicting saves. Saved sections show a warning when
they are out of date; permission failures do not restore private cached data.

## Notes and accessibility
Pending notes are saved before closing. Keyboard navigation, long text and
browser dashboard account separation have been improved.

## Safer updates
Automatic installation requires a trusted publisher signature. It remains
paused while signing approval is pending; manual downloads remain available.
"""
