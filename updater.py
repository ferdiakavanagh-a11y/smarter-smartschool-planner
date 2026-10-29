"""Checks GitHub Releases for a newer version and runs its installer silently.
"""

from __future__ import annotations

import hashlib
import base64
import json
import os
import re
import secrets
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

REPO = "ferdiakavanagh-a11y/smarter-smartschool-planner"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"  # skips drafts and prereleases
INSTALLER_NAME = "SmartschoolPlanner-Setup.exe"
CHECKSUM_NAME = INSTALLER_NAME + ".sha256"
ALLOWED_HOSTS = {"api.github.com", "github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com"}
MAX_INSTALLER_BYTES = 300 * 1024 * 1024
MAX_RELEASE_BYTES = 2 * 1024 * 1024
TIMEOUT = 20
ALLOW_ANY_URL_FOR_TESTS = False  # only the offline tests flip this
# Populate with the approved signing certificate's SHA-256 fingerprint before releasing signed updates.
TRUSTED_SIGNER_SHA256: frozenset[str] = frozenset()
_download_tokens: dict[Path, str] = {}


class UpdateError(Exception):
    """Something went wrong with the update; the message is safe to show."""


def parse_version(text: str) -> tuple[int, ...] | None:
    m = re.fullmatch(r"v?(\d+(?:\.\d+)*)(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?(?:\+[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?", (text or "").strip())
    return tuple(int(p) for p in m.group(1).split(".")) if m else None


def is_newer(latest: tuple[int, ...], current: tuple[int, ...]) -> bool:
    n = max(len(latest), len(current))
    return latest + (0,) * (n - len(latest)) > current + (0,) * (n - len(current))


def _url_ok(url: str) -> bool:
    if ALLOW_ANY_URL_FOR_TESTS:
        return True
    try:
        p = urlparse(url)
        return (p.scheme == "https" and (p.hostname or "").lower() in ALLOWED_HOSTS
                and p.port in (None, 443) and p.username is None and p.password is None)
    except (ValueError, TypeError, AttributeError):
        return False


class _UpdateRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _url_ok(newurl):
            raise UpdateError("The update redirected to an unexpected address, so it was refused.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _open(url: str, accept: str = "*/*"):
    if not _url_ok(url):
        raise UpdateError("The update address was unexpected, so it was refused.")
    req = urllib.request.Request(url, headers={"User-Agent": "SmartschoolPlanner-updater", "Accept": accept})
    resp = urllib.request.build_opener(_UpdateRedirectHandler()).open(req, timeout=TIMEOUT)
    if not _url_ok(resp.geturl()):
        resp.close()
        raise UpdateError("The update was offered from an unexpected address, so it was refused.")
    return resp


def check_for_update(current_version: str) -> dict | None:
    """Info about a newer release ({version, tag, installer_url, checksum_url, digest, size, page}) or None."""
    with _open(API_URL, "application/vnd.github+json") as resp:
        body = resp.read(MAX_RELEASE_BYTES + 1)
    if len(body) > MAX_RELEASE_BYTES:
        raise UpdateError("The release information was too large.")
    data = json.loads(body.decode("utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("assets", []), list):
        raise UpdateError("The release information was not in the expected format.")
    if data.get("draft") or data.get("prerelease"):
        return None
    tag = str(data.get("tag_name") or "")
    latest, current = parse_version(tag), parse_version(current_version)
    stable_over_beta = latest == current and "-" in current_version.split("+", 1)[0] and "-" not in tag.split("+", 1)[0]
    if latest is None or current is None or not (is_newer(latest, current) or stable_over_beta):
        return None
    assets = {a.get("name"): a for a in data.get("assets", [])
              if isinstance(a, dict) and isinstance(a.get("name"), str)}
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
        "notes": str(data.get("body") or "")[:100_000],
    }


def save_update_notice(root: Path, info: dict) -> None:
    """Persist public release notes before the installer can close the running app."""
    path = root / "data" / "update_notice.json"
    path.parent.mkdir(exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"version": info["version"], "notes": str(info.get("notes") or "")[:100_000]}, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def _read_update_notice(root: Path) -> dict | None:
    try:
        notice = json.loads((root / "data" / "update_notice.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return notice if isinstance(notice, dict) else None


def prepare_installed_notice(root: Path, version: str, notes: str) -> None:
    """Also cover upgrades launched by older updaters that didn't save release notes."""
    notice = _read_update_notice(root)
    if not notice or notice.get("version") != version:
        save_update_notice(root, {"version": version, "notes": notes})


def load_update_notice(root: Path, version: str) -> dict | None:
    notice = _read_update_notice(root)
    if not notice or notice.get("version") != version or notice.get("dismissed"):
        return None  # failed install or another version: do not announce an update that didn't happen
    return {"version": version, "notes": str(notice.get("notes") or "")[:100_000]}


def dismiss_update_notice(root: Path, version: str) -> bool:
    notice = _read_update_notice(root)
    if not notice or notice.get("version") != version:
        return False
    path = root / "data" / "update_notice.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"version": version, "dismissed": True}), encoding="utf-8")
    temporary.replace(path)
    return True


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


def verify_installer_signature(path: Path) -> None:
    """Check the pinned publisher when signing is configured; otherwise allow unsigned releases."""
    if not TRUSTED_SIGNER_SHA256:
        return
    literal = "'" + str(path.resolve()).replace("'", "''") + "'"
    script = ("$ErrorActionPreference='Stop'; $s=Get-AuthenticodeSignature -LiteralPath " + literal + "; "
              "@{status=[string]$s.Status; certificate=$(if($s.SignerCertificate){"
              "[Convert]::ToBase64String($s.SignerCertificate.RawData)}else{''})}|ConvertTo-Json -Compress")
    try:
        result = subprocess.run(
            [str(Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'),
             '-NoProfile', '-NonInteractive', '-EncodedCommand', base64.b64encode(script.encode('utf-16-le')).decode('ascii')],
            capture_output=True, text=True, timeout=30, check=True,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
        signature = json.loads(result.stdout.lstrip('\ufeff'))
        fingerprint = hashlib.sha256(base64.b64decode(signature['certificate'], validate=True)).hexdigest()
        if signature['status'] == 'Valid' and fingerprint in TRUSTED_SIGNER_SHA256:
            return
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        pass
    raise UpdateError("The installer is unsigned or its publisher could not be verified. Nothing was installed.")


def _cleanup_token(path: Path) -> str | None:
    token = _download_tokens.get(path)
    try:
        if (token and path.name == INSTALLER_NAME and path.parent.parent.resolve() == Path(tempfile.gettempdir()).resolve()
                and path.parent.resolve() == path.parent.absolute()
                and (path.parent / '.ssp-owner').read_text(encoding='ascii') == token):
            return token
    except OSError:
        pass
    return None


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
        verify_installer_signature(path)
        token = secrets.token_hex(32)
        (path.parent / '.ssp-owner').write_text(token, encoding='ascii')
        _download_tokens[path] = token
    except BaseException:
        path.unlink(missing_ok=True)
        (path.parent / '.ssp-owner').unlink(missing_ok=True)
        path.parent.rmdir()
        raise
    return path


def launch_installer(path: Path, root: Path | None = None) -> None:
    """Start the installer with no window at all (it closes this app, replaces the files and relaunches it)."""
    root = root or Path(__file__).resolve().parent
    verify_installer_signature(path)
    def literal(value):
        return "'" + str(value).replace("'", "''") + "'"
    result = root / 'data' / 'install_result.json'
    result.parent.mkdir(exist_ok=True)
    result.unlink(missing_ok=True)
    cleanup = ''
    token = _cleanup_token(path)
    if token:
        cleanup = f"""
try {{
  $folder = Get-Item -LiteralPath {literal(path.parent)} -Force
  if (-not ($folder.Attributes -band [IO.FileAttributes]::ReparsePoint) -and
      [IO.File]::ReadAllText({literal(path.parent / '.ssp-owner')}) -eq {literal(token)}) {{
    Remove-Item -LiteralPath {literal(path)} -Force
    Remove-Item -LiteralPath {literal(path.parent / '.ssp-owner')} -Force
    [IO.Directory]::Delete({literal(path.parent)}, $false)
  }}
}} catch {{ }}
"""
    # The hidden monitor survives the app's graceful exit.
    script = f"""
$ErrorActionPreference = 'Stop'
[System.IO.File]::WriteAllText({literal(result)}, '{{"status":"running"}}')
$code = -1
try {{
  $process = Start-Process -FilePath {literal(path)} -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS' -WindowStyle Hidden -PassThru -Wait
  $code = $process.ExitCode
}} catch {{ $code = -1 }}
{cleanup}
$result = @{{status = $(if ($code -eq 0) {{'ok'}} else {{'failed'}}); code = $code}} | ConvertTo-Json -Compress
[System.IO.File]::WriteAllText({literal(result.with_suffix('.tmp'))}, $result)
Move-Item -LiteralPath {literal(result.with_suffix('.tmp'))} -Destination {literal(result)} -Force
if ($code -ne 0) {{ Start-Process -FilePath {literal(root / 'SmartschoolPlanner.exe')} -ArgumentList '--update-failed' -WindowStyle Normal }}
"""
    encoded = base64.b64encode(script.encode('utf-16-le')).decode('ascii')
    env = dict(os.environ, PYINSTALLER_RESET_ENVIRONMENT="1")
    # Windows PowerShell may exit without executing its script with DETACHED_PROCESS.
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    log_path = result.parent / 'install_monitor.log'
    with log_path.open('wb') as log:
        worker = subprocess.Popen(  # noqa: S603
            [str(Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / 'WindowsPowerShell' / 'v1.0' / 'powershell.exe'),
             '-NoProfile', '-NonInteractive', '-WindowStyle', 'Hidden', '-EncodedCommand', encoded],
            env=env, creationflags=flags, close_fds=True,
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
        )
    deadline = time.monotonic() + 5
    while not result.exists():
        code = worker.poll()
        if code is not None or time.monotonic() >= deadline:
            reason = f'exit code {code}' if code is not None else 'startup timed out'
            raise UpdateError(f'The installer monitor could not start ({reason}). See data/install_monitor.log.')
        time.sleep(0.05)


def pending_install_failure(root: Path) -> bool:
    try:
        result = json.loads((root / 'data' / 'install_result.json').read_text(encoding='utf-8-sig'))
        return result.get('status') == 'failed'
    except (OSError, ValueError, AttributeError):
        return False


def acknowledge_install_failure(root: Path) -> None:
    (root / 'data' / 'install_result.json').unlink(missing_ok=True)
