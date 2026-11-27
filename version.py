"""Shared application and installer release version."""

__version__ = "3.2.1-beta.1"

RELEASE_NOTES = """## Faster startup and navigation

- The app opens in your saved theme while it loads Tasks.
- Saved Tasks can become usable while the Smartschool integration loads.
- Loaded tabs respond faster, and notes, lesson details, reports and offline files open on demand.

## Messages and account safety

- Cached messages stay readable during inbox refresh.
- The app checks account ownership before showing cached mail and cancels pending reads when the account changes.
- Smartschool adapts its message reader to narrow windows and larger text. Both themes place Gemini next to Reply.

## Windows installer

- The Windows build now uses Python 3.14 and bundles precompiled UI files.

This is a prerelease for testing startup, messaging and the Windows installer.
"""
