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

This program will not transfer any information to other networked systems unless specifically
requested by the user or the person installing or operating it.

**Where your data is kept:** everything the app saves is stored in files on your own computer.
Your login details, planner data, grades, notes, pinned and checked-off tasks and settings are kept
in the folder the app is installed in, and uninstalling the app removes them. The Smartschool
login library also keeps a login-session cache (so you don't have to log in on every sync) in the
`.cache\smartschool` folder of your Windows user profile. That folder also stays on your computer.

**The only places the app connects to, and only because the user asks it to:**

1. **Your own Smartschool address**, to log in and fetch your planner. This is the app's purpose,
   and your username and password are sent only there.
2. **Google's Gemini API, only if you add your own Gemini API key.** In that case, the text of your
   assignments (task title, the "Info voor de leerling" text and the date it was posted) is sent to
   Google to find deadlines written in the text. Your username, password and school address are
   not sent. Without a key, nothing is ever sent to Google.

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
