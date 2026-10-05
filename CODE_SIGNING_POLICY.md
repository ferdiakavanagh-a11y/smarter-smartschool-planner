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

This program will not transfer any information to other networked systems unless specifically
requested by the user or the person installing or operating it.

In practice: login details are stored only on the user's own computer. The app connects to the
user's own Smartschool address to log in and fetch the planner. If, and only if, the user adds a
Gemini API key, assignment text is sent to Google's Gemini service to find deadlines. Nothing is
sent to the developer.

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
