"""Checks GitHub Releases for a newer version and runs its installer silently.

Only the public GitHub API is contacted. No login details, data or identifiers are sent.
The installer is only run after its SHA-256 matches the checksum published with the release.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

REPO = "ferdiakavanagh-a11y/smarter-smartschool-planner"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"  # skips drafts and prereleases
INSTALLER_NAME = "SmartschoolPlanner-Setup.exe"
CHECKSUM_NAME = INSTALLER_NAME + ".sha256"
ALLOWED_HOSTS = {"github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com"}
MAX_INSTALLER_BYTES = 300 * 1024 * 1024
TIMEOUT = 20
ALLOW_ANY_URL_FOR_TESTS = False  # only the offline tests flip this


class UpdateError(Exception):
    """Something went wrong with the update; the message is safe to show."""


def parse_version(text: str) -> tuple[int, ...] | None:
    m = re.fullmatch(r"v?(\d+(?:\.\d+)*)", (text or "").strip())
    return tuple(int(p) for p in m.group(1).split(".")) if m else None


def is_newer(latest: tuple[int, ...], current: tuple[int, ...]) -> bool:
    n = max(len(latest), len(current))
    return latest + (0,) * (n - len(latest)) > current + (0,) * (n - len(current))


def _url_ok(url: str) -> bool:
    if ALLOW_ANY_URL_FOR_TESTS:
        return True
    p = urlparse(url)
    host = (p.hostname or "").lower()
    return p.scheme == "https" and (host in ALLOWED_HOSTS or host.endswith(".githubusercontent.com"))


def _open(url: str, accept: str = "*/*"):
    req = urllib.request.Request(url, headers={"User-Agent": "SmartschoolPlanner-updater", "Accept": accept})
    resp = urllib.request.urlopen(req, timeout=TIMEOUT)  # noqa: S310 - https only, checked below
    if not _url_ok(resp.geturl()):
        resp.close()
        raise UpdateError("The update was offered from an unexpected address, so it was refused.")
    return resp


def check_for_update(current_version: str) -> dict | None:
    """Info about a newer release ({version, tag, installer_url, checksum_url, digest, size, page}) or None."""
    with urllib.request.urlopen(
        urllib.request.Request(API_URL, headers={"User-Agent": "SmartschoolPlanner-updater", "Accept": "application/vnd.github+json"}),
        timeout=TIMEOUT,
    ) as resp:  # noqa: S310
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("draft") or data.get("prerelease"):
        return None
    latest, current = parse_version(data.get("tag_name", "")), parse_version(current_version)
    if latest is None or current is None or not is_newer(latest, current):
        return None
    assets = {a.get("name"): a for a in data.get("assets", [])}
    installer = assets.get(INSTALLER_NAME)
    if not installer:
        return None  # release exists but the installer isn't attached yet
    checksum = assets.get(CHECKSUM_NAME)
    digest = str(installer.get("digest") or "")
    return {
        "version": ".".join(map(str, latest)),
        "tag": data.get("tag_name"),
        "installer_url": installer.get("browser_download_url"),
        "checksum_url": checksum.get("browser_download_url") if checksum else None,
        "digest": digest.split(":", 1)[1].lower() if digest.lower().startswith("sha256:") else None,
        "size": installer.get("size"),
        "page": data.get("html_url"),
    }


def _expected_hash(info: dict) -> str:
    if info.get("checksum_url"):
        if not _url_ok(info["checksum_url"]):
            raise UpdateError("The checksum address was unexpected, so the update was refused.")
        with _open(info["checksum_url"]) as r:
            m = re.search(r"\b([0-9a-fA-F]{64})\b", r.read(4096).decode("utf-8", "replace"))
        if m:
            return m.group(1).lower()
    if info.get("digest") and re.fullmatch(r"[0-9a-f]{64}", info["digest"]):
        return info["digest"]
    raise UpdateError("This release has no checksum, so it can't be verified. Update was cancelled.")


def download_and_verify(info: dict, progress=None) -> Path:
    """Download the installer to a temp folder and check its SHA-256. Raises UpdateError if anything is off."""
    url = info.get("installer_url") or ""
    if not _url_ok(url):
        raise UpdateError("The installer address was unexpected, so the update was refused.")
    expected = _expected_hash(info)
    path = Path(tempfile.mkdtemp(prefix="ssp-update-")) / INSTALLER_NAME
    sha, done = hashlib.sha256(), 0
    try:
        with _open(url) as r, open(path, "wb") as f:
            total = int(r.headers.get("Content-Length") or info.get("size") or 0)
            while True:
                chunk = r.read(65536)
                if not chunk:
                    break
                done += len(chunk)
                if done > MAX_INSTALLER_BYTES:
                    raise UpdateError("The download was larger than expected, so it was cancelled.")
                sha.update(chunk)
                f.write(chunk)
                if progress:
                    progress(done, total)
        if sha.hexdigest() != expected:
            raise UpdateError("The download didn't match its checksum (corrupted or tampered). Nothing was installed.")
        with open(path, "rb") as f:
            if f.read(2) != b"MZ":
                raise UpdateError("The download isn't a Windows program. Nothing was installed.")
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def launch_installer(path: Path) -> None:
    """Start the installer silently (it closes this app, replaces the files and relaunches it)."""
    env = dict(os.environ, PYINSTALLER_RESET_ENVIRONMENT="1")  # so the relaunched exe starts fresh
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen(  # noqa: S603
        [str(path), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS"],
        env=env, creationflags=flags, close_fds=True,
    )
