"""Persist session cookies using DPAPI, scoped to this installation and school account."""
import hashlib
from http.cookiejar import LWPCookieJar, LoadError
import io
from pathlib import Path
from urllib.parse import urlsplit

from smartschool import Smartschool
from windows_security import atomic_bytes, protect, unprotect


def remove_legacy_session(username: str) -> None:
    root = (Path.home() / '.cache' / 'smartschool').resolve()
    target = (root / username).resolve()
    if not username or target.parent != root:
        return
    # The old dependency shared this location; remove authentication files only.
    for name in ('cookies.txt', 'authenticated_user.yml'):
        (target / name).unlink(missing_ok=True)


class EncryptedCookieJar(LWPCookieJar):
    def save(self, filename=None, ignore_discard=False, ignore_expires=False):
        text = '#LWP-Cookies-2.0\n' + self.as_lwp_str(ignore_discard, ignore_expires)
        atomic_bytes(Path(filename or self.filename), protect(text.encode('utf-8')))

    def load(self, filename=None, ignore_discard=False, ignore_expires=False):
        path = Path(filename or self.filename)
        text = unprotect(path.read_bytes()).decode('utf-8')
        self._really_load(io.StringIO(text), str(path), ignore_discard, ignore_expires)


class SecureSmartschool(Smartschool):
    def __init__(self, creds, root: Path):
        self._storage_root = root
        super().__init__(creds)

    @property
    def cache_path(self):
        identity = self.creds.main_url.lower() + '\0' + self.creds.username
        path = self._storage_root / 'data' / 'sessions' / hashlib.sha256(identity.encode()).hexdigest()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def _authenticated_user_file(self):
        return None  # Obtain the actual user from the authenticated homepage, not an old YAML cache.

    @property
    def authenticated_user(self):
        if self._authenticated_user is None:
            self._parse_login_information(self.get('/'))
        if self._authenticated_user is None:
            raise ValueError('Could not retrieve authenticated user information')
        return self._authenticated_user

    @authenticated_user.setter
    def authenticated_user(self, value):
        self._authenticated_user = value

    def _initialize_session(self):
        self.headers['User-Agent'] = 'unofficial Smartschool API interface'
        self.cookies = EncryptedCookieJar(self.cache_path / 'cookies.bin')
        try:
            self.cookies.load(ignore_discard=True)
        except (OSError, LoadError, ValueError, UnicodeError):
            pass  # A missing/unreadable cache requires a new login; never use plaintext storage.
        remove_legacy_session(self.creds.username)

    def _make_traced_request(self, request_method, method, url, **kwargs):
        if method.upper() not in ('GET', 'HEAD') and not self._approved_origin(url):
            raise ValueError('Refused to send login data to an unapproved address')
        kwargs.setdefault('timeout', (10, 30))
        return super()._make_traced_request(request_method, method, url, **kwargs)

    def _approved_origin(self, url):
        parsed = urlsplit(url)
        return parsed.scheme == 'https' and parsed.netloc.lower() == self.creds.main_url.lower()

    def rebuild_auth(self, prepared_request, response):
        if prepared_request.body is not None and not self._approved_origin(prepared_request.url):
            raise ValueError('Refused to forward login data to an unapproved address')
        return super().rebuild_auth(prepared_request, response)
