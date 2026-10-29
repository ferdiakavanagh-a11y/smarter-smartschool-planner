"""Persist session cookies using DPAPI, scoped to this installation and school account."""
import hashlib
from http.cookiejar import LWPCookieJar, LoadError
import io
from pathlib import Path
from urllib.parse import urlsplit

from smartschool import Smartschool
from smartschool._common import bs4_html, parse_smsc_vars
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
        password = creds.password
        super().__init__(creds)
        # The dependency trims every credential field; preserve significant password whitespace.
        object.__setattr__(self.creds, 'password', password)

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
            response = self.get('/')
            self._parse_login_information(response)
        if self._authenticated_user is None:
            from app_errors import SyncError
            parsed = urlsplit(response.url)
            page = parsed.path if parsed.path in ('/', '/login', '/2fa', '/account-verification') else 'other'
            content = response.headers.get('Content-Type', '').split(';', 1)[0].lower()
            content = content if content in ('text/html', 'application/json') else 'other'
            raise SyncError('login', 'Could not verify the signed-in account',
                            'Smartschool did not return account information the planner could read.',
                            'Check your saved login details. If they are correct, Smartschool may have changed its login page. Copy sync diagnostics to investigate.',
                            f'Account identity unavailable; HTTP {response.status_code}; page={page}; content={content}')
        return self._authenticated_user

    @authenticated_user.setter
    def authenticated_user(self, value):
        self._authenticated_user = value

    def _parse_login_information(self, response):
        # Current bootstrap scripts no longer necessarily use jQuery's extend.
        for script in bs4_html(response).select('script:not([src])'):
            values = parse_smsc_vars(script.get_text())
            user = values.get('authenticatedUser') if isinstance(values, dict) else None
            identity = user.get('id') if isinstance(user, dict) else None
            if type(identity) in (str, int) and str(identity).strip():
                self.authenticated_user = user
                return

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
        if urlsplit(prepared_request.url).scheme != 'https':
            raise ValueError('Refused to follow an insecure session redirect')
        if prepared_request.body is not None and not self._approved_origin(prepared_request.url):
            raise ValueError('Refused to forward login data to an unapproved address')
        return super().rebuild_auth(prepared_request, response)
