# Code signing policy

Free code signing provided by [SignPath.io](https://signpath.io), certificate by [SignPath Foundation](https://signpath.org).

> **Status: pending.** We have applied to the SignPath Foundation open-source program. Until the
> application is approved and signing is set up, Windows release files are **not signed** and
> Windows SmartScreen may show a warning. This page will be updated when that changes.

Automatic installation is paused while signing is pending. The updater now requires
a Windows-valid Authenticode signature whose signing certificate SHA-256 fingerprint
is listed in `updater.TRUSTED_SIGNER_SHA256`. An empty list refuses installation before
downloading; an unsigned, invalid or unexpected signer is refused. This source change
does not change the behavior of already installed older releases.

The release workflow builds a candidate with read-only repository access. Its separate
publication job checks the same publisher rule before attaching files. Until signing
is approved and integrated, candidates can be built locally or downloaded as workflow
artifacts, but this publication gate will reject them. No certificate was invented or
added by this change.

Before enabling signed releases: obtain the approved public certificate, verify its
identity out of band, compute SHA-256 over the certificate DER bytes, and place that
fingerprint in the source allowlist. Configure the approved signing service to sign
the app and installer before checksum creation. Test an authentic signed installer,
a modified binary, an unsigned binary and a different publisher. Certificate rotation
requires a reviewed allowlist update distributed before the old certificate retires.
Never put signing private keys in this repository.

Windows signature checks use Microsoft's
[Get-AuthenticodeSignature](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/get-authenticodesignature).
Actions use verified full commit pins following
[GitHub's secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use).

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
