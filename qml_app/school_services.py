"""School views and explicit, authenticated downloads; no independent session store."""
from itertools import islice
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import tempfile
import uuid
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree

from bs4 import BeautifulSoup
import requests
from smartschool import Attachments, BoxType, Courses, Message, MessageHeaders, MessageMoveToTrash, Periods, Reports, StudentSupportLinks
from planner_details import html_to_text

MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
MAX_RECORDS = 2000
MAX_HOMEPAGE_BYTES = 2 * 1024 * 1024
_BLOCKED_SUFFIXES = {'.exe', '.com', '.dll', '.msi', '.msp', '.cmd', '.bat', '.ps1', '.vbs', '.vbe', '.js', '.jse', '.wsf', '.wsh', '.hta', '.lnk', '.url', '.scr', '.cpl', '.pif', '.reg', '.jar', '.application', '.gadget', '.html', '.htm', '.svg', '.docm', '.dotm', '.xlsm', '.xlam', '.pptm', '.ppam'}


def _plain(value, limit=100_000):
    return html_to_text(str(value or '')[:limit])


def _id(value):
    value = str(value)
    if not re.fullmatch(r'[0-9]{1,20}', value):
        raise ValueError('Invalid school record identifier')
    return value


def _date(value):
    return value.isoformat() if hasattr(value, 'isoformat') else str(value or '')[:32]


def _records(values, limit=MAX_RECORDS):
    return islice(values, limit)


def _message_box(folder):
    boxes = {'inbox': BoxType.INBOX, 'sent': BoxType.SENT, 'outbox': BoxType.SENT,
             'trash': BoxType.TRASH, 'draft': BoxType.DRAFT, 'scheduled': BoxType.SCHEDULED}
    if not isinstance(folder, str) or folder not in boxes:
        raise ValueError('Unknown school message folder')
    return boxes[folder]


def _message_query(factory, session, folder, *args):
    box = _message_box(folder)
    return factory(session, *args) if box is BoxType.INBOX else factory(session, *args, box_type=box)


def fetch_messages(session, limit=50, folder='inbox'):
    if type(limit) is not int or not 1 <= limit <= MAX_RECORDS:
        raise ValueError('Invalid message limit')
    return [dict(id=_id(m.id), sender=_plain(getattr(m, 'from_', '')), subject=_plain(getattr(m, 'subject', '')),
                 date=_date(getattr(m, 'date', '')), unread=bool(getattr(m, 'unread', False)),
                 hasAttachments=bool(getattr(m, 'attachment', 0)), folder=folder)
            for m in _records(_message_query(MessageHeaders, session, folder), limit)
            if folder == 'trash' or not getattr(m, 'deleted', False)]


def _message_attachment(message_id, item, folder='inbox'):
    return dict(kind='message', messageId=message_id, id=_id(item.file_id), name=str(item.name or 'Attachment')[:255],
                size=str(getattr(item, 'size', '') or '')[:40], mime=str(getattr(item, 'mime', '') or '')[:128], folder=folder)


def fetch_message(session, message_id, folder='inbox'):
    message_id = _id(message_id)
    message = _message_query(Message, session, folder, int(message_id)).get()
    if _id(message.id) != message_id:
        raise ValueError('Message identity did not match')
    return dict(id=message_id, sender=_plain(getattr(message, 'from_', '')), subject=_plain(message.subject),
                date=_date(message.date), body=_plain(message.body), folder=folder,
                to=[_plain(value, 500) for value in _records(getattr(message, 'receivers', []), 100)],
                cc=[_plain(value, 500) for value in _records(getattr(message, 'ccreceivers', []), 100)],
                bcc=[_plain(value, 500) for value in _records(getattr(message, 'bccreceivers', []), 100)],
                canReply=bool(getattr(message, 'can_reply', False)),
                attachments=[_message_attachment(message_id, item, folder) for item in
                             _records(_message_query(Attachments, session, folder, int(message_id)), 100)])


class MessageMutationUncertain(RuntimeError):
    """The school may have applied the change; refresh before another attempt."""


def trash_message(session, message_id, folder='inbox', current=None):
    """Use the SDK's verified quick-delete command once, never its retrying POST."""
    message_id = _id(message_id)
    if _message_box(folder) not in (BoxType.INBOX, BoxType.SENT):
        raise ValueError('Only Inbox and Sent messages can be moved to Trash')
    query = MessageMoveToTrash(session, int(message_id))
    url = _school_url(session, query._url)
    if session.get_adapter(url).max_retries.total not in (0, False):
        raise ValueError('Message mutation retries must be disabled')
    if current is not None and not current():
        raise ValueError('Account changed before the message action')
    if not any(_id(item.id) == message_id and not getattr(item, 'deleted', False)
               for item in _records(_message_query(MessageHeaders, session, folder))):
        raise ValueError('This message is no longer in the selected folder. Refresh the folder first.')
    session.ensure_authenticated()
    if current is not None and not current():
        raise ValueError('Account changed before the message action')
    response = None
    try:
        response = requests.Session.request(session, 'POST', url,
            data={'command': query._construct_command()}, headers={'X-Requested-With': 'XMLHttpRequest'},
            allow_redirects=False, timeout=(10, 30), stream=True)
        _school_url(session, response.url)
        if response.status_code != 200:
            raise ValueError('The school did not confirm the message change')
        body = bytearray()
        for chunk in response.iter_content(65536):
            body.extend(chunk)
            if len(body) > 1024 * 1024:
                raise ValueError('The message response is too large')
        if b'<!DOCTYPE' in body.upper() or b'<!ENTITY' in body.upper():
            raise ValueError('Invalid message response')
        root = ElementTree.fromstring(body)
        details = root.findall('.//data/details')
        if (root.findtext('.//status') == 'error' or len(details) != 1 or
                details[0].findtext('msgID') != message_id or
                details[0].findtext('status') not in ('1', 'true') or
                details[0].findtext('box_type') not in ('inbox', 'outbox', 'trash')):
            raise ValueError('The school did not confirm the selected message change')
        return dict(id=message_id, state='trashed')
    except Exception as exc:
        raise MessageMutationUncertain('The message change could not be confirmed. Refresh the folder before trying again.') from exc
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass


def upload_message_attachment(session, form, attachment, current):
    """Upload exactly the locally selected bytes to this fresh compose form once."""
    if not current():
        raise ValueError('Account changed before attachment upload')
    path = Path(attachment.get('path', ''))
    name = _attachment_name(attachment.get('name'))
    size = attachment.get('bytes')
    digest = attachment.get('sha256')
    if (not path.is_absolute() or str(path).startswith(('\\\\', '//')) or path.name != name or
            any(_is_link(part) for part in (path, *path.parents)) or not path.is_file() or
            type(size) is not int or not 0 <= size <= MAX_DOWNLOAD_BYTES or
            not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest)):
        raise ValueError('The selected attachment is not a safe local file')
    with path.open('rb') as file:
        body = file.read(MAX_DOWNLOAD_BYTES+1)
    if len(body) != size or len(body) > MAX_DOWNLOAD_BYTES or hashlib.sha256(body).hexdigest() != digest:
        raise ValueError('The selected attachment changed. Select it again before sending.')
    upload_dir = form.payload.get('randomDir')
    if not isinstance(upload_dir, str) or not upload_dir or len(upload_dir) > 1024 or any(ord(c) < 32 for c in upload_dir):
        raise ValueError('The school did not provide a valid attachment upload form')
    url = _school_url(session, '/Upload/Upload/Index')
    if session.get_adapter(url).max_retries.total not in (0, False):
        raise ValueError('Attachment upload retries must be disabled')
    if not current():
        raise ValueError('Account changed before attachment upload')
    response = None
    try:
        response = requests.Session.request(session, 'POST', url,
            files={'file': (name, body, mimetypes.guess_type(name)[0] or 'application/octet-stream'),
                   'uploadDir': (None, upload_dir)},
            allow_redirects=False, timeout=(10, 30), stream=True)
        _school_url(session, response.url)
        result = bytearray()
        for chunk in response.iter_content(1024):
            result.extend(chunk)
            if len(result) > 1024:
                raise ValueError('Invalid attachment response')
        if response.status_code != 200 or bytes(result).strip().lower() != b'true':
            raise ValueError('Attachment upload was not confirmed')
        if not current():
            raise ValueError('Account changed during attachment upload')
    except Exception:
        raise ValueError('The attachment upload could not be confirmed. No message was sent.') from None
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass


def _class(item):
    return _plain(getattr(getattr(item, 'class_', None), 'name', ''))


def _year(item):
    year = getattr(item, 'skore_work_year', None)
    return _plain(getattr(item, 'schoolyear_label', '') or getattr(year, 'id', ''))


def _report(item):
    result = dict(id=_id(item.id), name=_plain(item.name), date=_date(item.date), className=_class(item),
                  schoolYear=_year(item), downloadable=bool(getattr(item, 'download_url', '')))
    if getattr(item, 'period_id', None) is not None:
        result['periodId'] = str(item.period_id)
    return result


def fetch_resources(session):
    result = dict(reports=[], periods=[], courses=[], support=[], homepage=[], errors={})
    sources = dict(
        reports=(Reports, _report),
        periods=(Periods, lambda p: dict(id=_id(p.id), name=_plain(p.name), active=bool(p.is_active), className=_class(p), schoolYear=_year(p))),
        homepage=(fetch_homepage_links, lambda link: link))
    for key, (source, convert) in sources.items():
        try:
            result[key] = [convert(item) for item in _records(source(session)) if key != 'support' or getattr(item, 'is_visible', False)]
        except Exception:
            # Optional school modules fail independently; never present permission errors as an empty success.
            result['errors'][key] = 'This section could not be loaded. Check your school access and try again.'
    return result


def fetch_homepage_links(session):
    """Read only the approved replacement timetable block; never fetch its links."""
    response = _get(session, '/')
    try:
        body = bytearray()
        for chunk in response.iter_content(65536):
            body.extend(chunk)
            if len(body) > MAX_HOMEPAGE_BYTES:
                raise ValueError('The school homepage is too large')
        soup = BeautifulSoup(bytes(body), 'html.parser')
        for element in soup.select('script, style, template, noscript'):
            element.decompose()
        links, seen = [], set()
        for block in _records(soup.select('div.homepage__block'), 100):
            heading = block.select_one('.homepage__block__top__title')
            content = block.select_one('.homepage__block__content')
            title = ' '.join(heading.get_text(' ', strip=True).split())[:300] if heading else ''
            # The user approved this item alone; do not expose other homepage blocks.
            if content is None or not re.fullmatch(r'(?:vervangingsrooster|lokaalwissel)(?:[\s/,;&\u2013\u2014-]+(?:vervangingsrooster|lokaalwissel))*', title.casefold()):
                continue
            for anchor in _records(content.select('a[href]'), 30):
                href = anchor.get('href')
                if not isinstance(href, str) or not href or href.startswith('#') or '\\' in href or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in href):
                    continue
                try:
                    url = urljoin(response.url, href)
                    parsed = urlsplit(url)
                    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
                        continue
                except ValueError:
                    continue
                if url not in seen:
                    links.append(dict(title=title, url=url, label=' '.join(anchor.get_text(' ', strip=True).split())[:300] or title))
                    seen.add(url)
        return links
    finally:
        response.close()


def _school_url(session, url):
    school = str(session.creds.main_url).lower()
    base = urlsplit('https://' + school)
    if base.username or base.password or base.path or base.query or base.fragment or base.port not in (None, 443) or not base.hostname:
        raise ValueError('Invalid school origin')
    if not isinstance(url, str) or not url or url.startswith('//') or '\\' in url or any(ord(c) < 32 for c in url):
        raise ValueError('Invalid download address')
    parsed = urlsplit(urljoin('https://' + school + '/', url))
    if (parsed.scheme != 'https' or parsed.hostname != base.hostname or parsed.port not in (None, 443)
            or parsed.username or parsed.password or parsed.fragment
            or {'login', '2fa', 'account-verification'} & set(parsed.path.split('/'))):
        raise ValueError('Only authenticated files on your school are supported')
    return parsed.geturl()


def _get(session, url, conditional=None):
    for _ in range(6):
        url = _school_url(session, url)
        headers = {}
        if conditional and conditional.get('resourceKey') == hashlib.sha256(url.encode()).hexdigest():
            if conditional.get('etag'):
                headers['If-None-Match'] = _validator(conditional['etag'])
            elif conditional.get('lastModified'):
                headers['If-Modified-Since'] = _validator(conditional['lastModified'])
        response = session.get(url, stream=True, allow_redirects=False, timeout=(10, 30), **({'headers': headers} if headers else {}))
        try:
            _school_url(session, response.url)
            if response.status_code in (301, 302, 303, 307, 308):
                url = _school_url(session, urljoin(url, response.headers.get('Location', '')))
                if not response.headers.get('Location'):
                    raise ValueError('Invalid download redirect')
                response.close()
                continue
            response.raise_for_status()
            if response.status_code == 304 and headers:
                return response
            if response.status_code != 200:
                raise ValueError('The file is not available')
            return response
        except Exception:
            response.close()
            raise
    raise ValueError('Too many file redirects')


def _validator(value):
    if not isinstance(value, str) or len(value) > 1024 or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError('Invalid document validator')
    return value


def _attachment_name(value):
    name = str(value or '')
    if (not name or len(name) > 255 or name.strip() != name or name.endswith('.')
            or re.search(r'[<>:"/\\|?*\x00-\x1f\x7f]', name) or name in ('.', '..')
            or re.fullmatch(r'(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', name, re.I)):
        raise ValueError('This filename cannot be used safely')
    return name


def _filename(value):
    name = _attachment_name(value)
    if len(name) > 180 or Path(name).suffix.lower() in _BLOCKED_SUFFIXES:
        raise ValueError('This filename or file type cannot be downloaded safely')
    return name


def _is_link(path):
    return path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction())


def _directory(directory):
    path = Path(directory).absolute()
    if any(_is_link(part) for part in (path, *path.parents)):
        raise ValueError('Linked download directories are not supported')
    path.mkdir(parents=True, exist_ok=True)
    return path


def download(session, attachment, directory, cached=None):
    """Save an explicit file to a caller-owned account directory; never open or execute it."""
    kind = attachment.get('kind')
    if kind == 'message':
        message_id, file_id = _id(attachment.get('messageId')), _id(attachment.get('id'))
        folder = attachment.get('folder', 'inbox')
        item = next((a for a in _records(_message_query(Attachments, session, folder, int(message_id)), 100)
                     if _id(a.file_id) == file_id), None)
        if item is None:
            raise ValueError('This file does not belong to the selected message')
        name = _filename(item.name)
        url = f'/?module=Messages&file=download&fileID={file_id}&target=0'
    elif kind == 'planner':
        name, url = _filename(attachment.get('name')), attachment.get('url')
        _school_url(session, url)
    elif kind == 'report':
        report_id = _id(attachment.get('id'))
        report = next((r for r in _records(Reports(session)) if _id(r.id) == report_id), None)
        if report is None:
            raise ValueError('This report is no longer available')
        name = _filename(re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', str(report.name)).strip().rstrip('.')[:150] + '.pdf')
        metadata = _get(session, report.download_url)
        try:
            body = bytearray()
            for chunk in metadata.iter_content(65536):
                body.extend(chunk)
                if len(body) > 1024 * 1024:
                    raise ValueError('Report download information is too large')
            payload = json.loads(body)
            url = payload.get('url') if isinstance(payload, dict) else None
            _school_url(session, url)
        finally:
            metadata.close()
    else:
        raise ValueError('Unsupported attachment type')
    folder = _directory(directory)
    previous, previous_hash, conditional = None, '', None
    if cached is not None:
        identity = report_id if kind == 'report' else attachment.get('id')
        if kind not in ('report','planner') or not identity or cached.get('source') != kind or cached.get('sourceId') != identity:
            raise ValueError('The cached copy does not belong to this file')
        previous = Path(cached.get('path', ''))
        if (previous.resolve().parent != folder.resolve() or _is_link(previous) or previous.suffix.lower() != Path(name).suffix.lower()
                or not previous.name or previous.name in ('.', '..')):
            raise ValueError('Invalid cached report destination')
        if previous.is_file() and 0 < previous.stat().st_size <= MAX_DOWNLOAD_BYTES:
            with previous.open('rb') as file:
                previous_hash = hashlib.file_digest(file, 'sha256').hexdigest()
            if previous_hash == cached.get('sha256'):
                conditional = cached
    response, temporary = _get(session, url, conditional), None
    try:
        metadata = dict(sha256='', etag=_validator(response.headers.get('ETag', '')),
                        lastModified=_validator(response.headers.get('Last-Modified', '')),
                        resourceKey=hashlib.sha256(response.url.encode()).hexdigest()) if kind in ('report','planner') else {}
        if response.status_code == 304:
            metadata.update(sha256=previous_hash, etag=metadata['etag'] or cached.get('etag', ''),
                            lastModified=metadata['lastModified'] or cached.get('lastModified', ''))
            return dict(path=str(previous), name=name, bytes=previous.stat().st_size,
                        mime='application/pdf' if kind == 'report' else '', reused=True, **metadata)
        mime = response.headers.get('Content-Type', '').split(';', 1)[0].lower()
        if mime in ('text/html', 'application/xhtml+xml', 'image/svg+xml'):
            raise ValueError('The school returned a web page instead of a downloadable file')
        length = response.headers.get('Content-Length')
        if length and (not length.isdigit() or int(length) > MAX_DOWNLOAD_BYTES):
            raise ValueError('This file exceeds the 50 MB download limit')
        total, prefix, digest = 0, bytearray(), hashlib.sha256()
        with tempfile.NamedTemporaryFile(dir=folder, suffix='.part', delete=False) as file:
            temporary = Path(file.name)
            for chunk in response.iter_content(65536):
                if not chunk:
                    continue
                if len(prefix) < 512:
                    prefix.extend(chunk[:512 - len(prefix)])
                    signature = bytes(prefix).lstrip(b'\xef\xbb\xbf \t\r\n')
                    if signature.startswith((b'MZ', b'#!')) or re.match(br'(?:<!doctype\s+html|<html|<script)', signature, re.I):
                        raise ValueError('The response is not a supported document')
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    raise ValueError('This file exceeds the 50 MB download limit')
                file.write(chunk)
                digest.update(chunk)
            if not total:
                raise ValueError('The school returned an empty file')
            if kind == 'report' and not bytes(prefix).lstrip(b'\xef\xbb\xbf \t\r\n').startswith(b'%PDF-'):
                raise ValueError('The school did not return a PDF report')
            file.flush()
            os.fsync(file.fileno())
        target = previous or folder / (uuid.uuid4().hex + '-' + name)
        reused = bool(previous_hash and digest.hexdigest() == previous_hash)
        if not reused:
            if previous:
                os.replace(temporary, target)
            else:
                os.rename(temporary, target)
        if kind in ('report','planner'):
            metadata['sha256'] = digest.hexdigest()
        return dict(path=str(target), name=name, bytes=total, mime=mime, reused=reused, **metadata)
    finally:
        response.close()
        if temporary is not None:
            temporary.unlink(missing_ok=True)
