"""Short-lived WOPI preview; school cookies never enter the browser."""
from html import escape
import re
from urllib.parse import parse_qs, urljoin, urlsplit

from bs4 import BeautifulSoup
from .school_services import fetch_homepage_links, _school_url, MAX_HOMEPAGE_BYTES


def wopi_url(url):
    try:
        part = urlsplit(url)
        return (part.scheme == 'https' and not part.username and not part.password
                and part.port in (None, 443) and not part.fragment
                and bool(re.fullmatch(r'wopi\d+\.smartschool\.be', part.hostname or '')))
    except ValueError:
        return False


def viewer_url(url):
    try:
        part = urlsplit(url)
        return (part.scheme == 'https' and not part.username and not part.password
                and part.port in (None, 443)
                and (part.hostname == 'officeapps.live.com' or (part.hostname or '').endswith('.officeapps.live.com')
                     or part.hostname == 'office.net' or (part.hostname or '').endswith('.office.net')
                     or wopi_url(url)))
    except ValueError:
        return False


def _bootstrap(body, base):
    if not wopi_url(base):
        raise ValueError('No Smartschool preview available')
    soup = BeautifulSoup(body, 'html.parser')
    for form in soup.select('form[action]'):
        action = urljoin(base, form['action'])
        part = urlsplit(action)
        if (part.scheme != 'https' or part.hostname != 'powerpoint.officeapps.live.com'
                or part.port not in (None, 443) or part.username or part.password
                or part.path != '/p/PowerPointFrame.aspx' or part.fragment
                or form.get('method', '').lower() != 'post'):
            continue
        query = parse_qs(part.query)
        source = query.get('WOPISrc', [])
        if len(source) != 1 or not wopi_url(source[0]) or query.get('PowerPointView') != ['ReadingView']:
            continue
        fields = {item.get('name'): item.get('value', '') for item in form.select('input[type=hidden]')}
        if not fields.get('access_token') or not fields.get('access_token_ttl', '').isdigit():
            continue
        inputs = ''.join('<input type="hidden" name="'+name+'" value="'+escape(fields[name], quote=True)+'">'
                         for name in ('access_token', 'access_token_ttl'))
        # Rebuild only the verified viewing form, without executing school page scripts.
        return ('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<meta name="referrer" content="no-referrer"></head><body style="margin:0;overflow:hidden">'
                '<iframe name="office_frame" title="Teacher replacements" style="position:fixed;inset:0;width:100%;height:100%;border:0"></iframe>'
                '<form method="post" target="office_frame" action="'+escape(action, quote=True)+'">'+inputs+'</form>'
                '<script>'
                'window.__plannerPresentationReady=false;'
                'const officeFrame=document.querySelector("iframe");'
                'const officeOrigin="https://powerpoint.officeapps.live.com";'
                'window.addEventListener("message",function(event){'
                'if(event.origin!==officeOrigin||event.source!==officeFrame.contentWindow)return;'
                'let message;try{message=typeof event.data==="string"?JSON.parse(event.data):event.data}catch(error){return}'
                'const values=message&&message.Values;'
                'if(message&&message.MessageId==="App_LoadingStatus"&&values&&'
                'typeof values.DocumentLoadedTime==="number"&&Number.isFinite(values.DocumentLoadedTime)&&values.DocumentLoadedTime>0&&'
                '(values.Status===undefined||values.Status==="Document_Loaded"))window.__plannerPresentationReady=true;'
                '});'
                'officeFrame.addEventListener("load",function(){'
                'officeFrame.contentWindow.postMessage(JSON.stringify({MessageId:"Host_PostmessageReady",SendTime:Date.now(),Values:{}}),officeOrigin);'
                '});'
                'document.forms[0].submit();</script></body></html>')
    raise ValueError('No supported read-only PowerPoint preview available')


def fetch_preview(session):
    """Rediscover the approved block each time; only follow school/WOPI redirects."""
    for link in fetch_homepage_links(session):
        try:
            target = _school_url(session, link['url'])
            for _ in range(6):
                if not wopi_url(target):
                    target = _school_url(session, target)
                response = session.get(target, stream=True, allow_redirects=False, timeout=(10, 30))
                try:
                    if response.url != target:
                        raise ValueError('Unexpected preview origin')
                    if response.status_code in (301, 302, 303, 307, 308):
                        location = response.headers.get('Location')
                        if not location:
                            raise ValueError('Missing preview redirect')
                        target = urljoin(target, location)
                        continue
                    response.raise_for_status()
                    if response.status_code != 200 or 'text/html' not in response.headers.get('Content-Type', '').lower():
                        raise ValueError('Preview unavailable')
                    body = bytearray()
                    for chunk in response.iter_content(65536):
                        body.extend(chunk)
                        if len(body) > MAX_HOMEPAGE_BYTES:
                            raise ValueError('Preview too large')
                    return dict(html=_bootstrap(bytes(body), target), base=target)
                finally:
                    response.close()
        except Exception:
            # An obsolete room-change link must not prevent the current deck opening.
            continue
    raise ValueError('Teacher replacements are unavailable; refresh or check school access')


def configure_profile(profile):
    from PySide6.QtWebEngineCore import QWebEngineUrlRequestInfo, QWebEngineUrlRequestInterceptor

    def static_asset(url, request):
        try:
            part = urlsplit(url)
            kind = QWebEngineUrlRequestInfo.ResourceType
            # Office moved its required viewer scripts/styles to this dedicated static CDN.
            return (part.scheme == 'https' and part.hostname == 'res.public.onecdn.static.microsoft'
                    and not part.username and not part.password and part.port in (None, 443)
                    and bytes(request.requestMethod()) == b'GET'
                    and request.resourceType() in (kind.ResourceTypeScript, kind.ResourceTypeStylesheet,
                                                  kind.ResourceTypeImage, kind.ResourceTypeFontResource))
        except ValueError:
            return False

    class ViewerRequests(QWebEngineUrlRequestInterceptor):
        def interceptRequest(self, request):
            url = request.requestUrl().toString()
            if not viewer_url(url) and not url.startswith(('about:', 'data:', 'blob:')) and not static_asset(url, request):
                request.block(True)
    interceptor = ViewerRequests(profile)
    profile.setUrlRequestInterceptor(interceptor)
    profile.downloadRequested.connect(lambda download: download.cancel())
    return interceptor
