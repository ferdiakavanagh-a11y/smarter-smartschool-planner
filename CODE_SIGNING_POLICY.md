# Code signing policy

Free code signing provided by [SignPath.io](https://signpath.io), certificate by [SignPath Foundation](https://signpath.org).

> **Status: pending.** We have applied to the SignPath Foundation open-source program. Until the
> application is approved and signing is set up, Windows release files are **not signed** and
> Windows SmartScreen may show a warning. This page will be updated when that changes.

## What gets signed

Once approved, only these Windows files, built from this repository, are signed:

- `SmartschoolPlanner-Setup.exe` (the installer)
- `SmartschoolPlanner.exe` (the app inside the installer)

Nothing else is signed. Third-party files are never signed with this project's certificate.

## How releases are built

Releases are built by the GitHub Actions workflow in
[`.github/workflows/release.yml`](.github/workflows/release.yml), on GitHub-hosted runners,
directly from the tagged commit in this public repository. No file built anywhere else is
submitted for signing.

## Roles

| Role | Who |
|---|---|
| Committers and reviewers | [ferdiakavanagh-a11y](https://github.com/ferdiakavanagh-a11y) |
| Approver of signing requests | [ferdiakavanagh-a11y](https://github.com/ferdiakavanagh-a11y) |

Every signing request needs manual approval. Everyone with repository or signing access uses
multi-factor authentication, and access is removed when it is no longer needed.

## Privacy

**Smarter Smartschool Planner does not collect any data.** The developer receives nothing: no
usage statistics, no analytics, no crash reports, no login details, no assignment data. There is
no developer server, and the app contains no tracking or telemetry.

**Where your data is kept:** login secrets live in Windows Credential Manager under your
Windows account. Nonsecret configuration, planner data, grades, LVS, notes, pins,
completion and settings stay in the app folder. Session cookies are encrypted with
Windows DPAPI in `data/sessions/`. Legacy authentication cache files for the account
are removed. Uninstall removes this installation's vault entries and local files;
backups and cloud file history are outside the app's control.

**Network connections:**

1. **Your approved Smartschool address**, when syncing or loading LVS details.
   Your username and password are sent only to that approved address.
2. **Google's Gemini API**, when Gemini is selected and you supply an API key.
   Assignment titles, instructions and posted dates are sent to find deadlines.
   Login credentials and school addresses are not included in that request.
3. **GitHub**, automatically on startup to check for new app releases and read
   release notes. Installing an offered update downloads the installer and checksum
   from GitHub. These requests contain no planner or login data.

Links you click open in your own web browser. The app does not load fonts, scripts or images from
the internet.

## How to verify a download

Once releases are signed: right-click `SmartschoolPlanner-Setup.exe`, choose **Properties**, open
the **Digital Signatures** tab, and check that the signer is **SignPath Foundation**. Only
download the installer from this repository's
[Releases page](../../releases).

## Reporting a problem

If you think a release is malicious, tampered with, or wrongly signed, please open an issue on
this repository. If signing is ever suspected to be compromised, signing and publishing will stop,
SignPath Foundation will be told, and revocation will be requested where appropriate.

## Disclaimer

This is an unofficial, community project. It is not affiliated with or endorsed by Smartschool.
