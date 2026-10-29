"""Native UI boundary. Network work stays off the Qt thread; storage stays compatible."""
import json
import math
import os
import subprocess
import sys
import threading
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from PySide6.QtCore import QObject, Property, Signal, Slot, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
import credential_store
import task_state
from .production_model import PlannerTasks, text, fields_text, planner_url, written_date, task_indicators


def log_error(root, info):
    try:
        path = root/'error.log'
        if path.exists() and path.stat().st_size > 200_000:
            path.write_text('', encoding='utf-8')
        with path.open('a', encoding='utf-8') as stream:
            stream.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {info.get('kind')}: {info.get('title')} - {info.get('message')}\n")
            stream.write(str(info.get('details') or '')[-4000:]+'\n')
    except OSError:
        pass


class Backend(QObject):
    changed = Signal()
    error = Signal(str)
    detailReady = Signal(str, 'QVariantMap')
    quitRequested = Signal()
    _finished = Signal(str, object, object)

    def __init__(self, root):
        super().__init__()
        self.root = Path(root)
        self.data = {}
        self._settings = task_state.load_settings(self.root)
        self._jobs = set()
        self._closed = False
        self._status = ''
        self._last_failure = None
        self._update = None
        self._updates_checked = False
        self._notice = {}
        self.sync_after_choice = False
        self.tasks = PlannerTasks(self.root, self.verify_account)
        self.tasks.failed.connect(self.error)
        self._finished.connect(self._receive, Qt.QueuedConnection)
        self.reload()

    def account(self):
        return credential_store.account_key(credential_store.load_credentials(self.root/'credentials.yml'))

    def verify_account(self):
        if not self.data.get('account_key') or self.data['account_key'] != self.account():
            raise ValueError('Sync this account before editing saved data.')

    def reload(self):
        self.data = {}
        try:
            data = json.loads((self.root/'data/planner_data.json').read_text(encoding='utf-8'))
            if not isinstance(data, dict) or data.get('account_key') != self.account():
                raise ValueError('Saved planner belongs to another or unverified account.')
            def records(value):
                if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
                    raise ValueError('Invalid saved planner records')
                return value
            for key in ('todos', 'days', 'all_classes', 'results', 'warnings'):
                records(data.get(key, []))
            if data.get('lvs') is not None and not isinstance(data['lvs'], dict):
                raise ValueError('Invalid saved LVS data')
            for key in ('notes', 'absences'):
                records((data.get('lvs') or {}).get(key, []))
            entries = list(data.get('todos', []))
            for key in ('days', 'all_classes'):
                for day in data.get(key, []):
                    for event in records(day.get('events', [])):
                        info = event.get('info')
                        if info is not None and not isinstance(info, dict):
                            raise ValueError('Invalid saved lesson info')
                        records((info or {}).get('assignments') or [])
                        entries.append(event)
            for item in entries:
                for key in ('attachments', 'weblinks'):
                    records(item.get(key) or [])
            for result in data.get('results', []):
                if result.get('feedback') is not None and not isinstance(result['feedback'], list):
                    raise ValueError('Invalid saved grade feedback')
            if data.get('optional_section_status') is not None and not isinstance(data['optional_section_status'], dict):
                raise ValueError('Invalid saved section status')
            self.data = data
            timestamp = str(data.get('generated_at') or '')
            try:
                self._status = 'Last synced · '+written_date(timestamp)+datetime.fromisoformat(timestamp).strftime(', %H:%M')
            except ValueError:
                self._status = 'Last synced · unknown'
        except FileNotFoundError:
            self._status = 'Not synced yet · use Sync to load your planner'
        except Exception:
            self._status = 'Saved planner unavailable · check login details and sync again'
        self.tasks.replace(self.data)
        self.changed.emit()

    @Property(str, notify=changed)
    def status(self):
        return self._status

    @Property(bool, notify=changed)
    def busy(self):
        return bool(self._jobs & {'sync', 'setup', 'install'})

    @Property(str, notify=changed)
    def busyAction(self):
        return next((name for name in ('sync', 'setup', 'install') if name in self._jobs), '')

    @Property(bool, notify=changed)
    def renderingChoicePending(self):
        return task_state.rendering_choice_pending(self.root)

    @Property('QVariantMap', notify=changed)
    def settings(self):
        values = self._settings.copy()
        if values.get('qmlVersion') != 1:
            size = values.get('textSize')
            values['textSize'] = {'s': .9, 'm': 1, 'l': 1.15}.get(size, 1) if isinstance(size, str) else 1
            level = values.get('glassLevel', 0)
            values['glassLevel'] = max(0, min(2, level))/2 if type(level) in (int, float) and (not isinstance(level, float) or math.isfinite(level)) else 0
        for key, options in dict(renderingMode=('fancy', 'performance'), style=('clear', 'vivid'), scheme=('light', 'dark', 'auto')).items():
            if values.get(key) not in options:
                values[key] = options[0]
        for key, (low, high, default) in dict(glassLevel=(0, 1, 0), distortion=(0, 1, .25), textSize=(.9, 1.35, 1), wallpaperIndex=(0, 3, 1)).items():
            value = values.get(key)
            if type(value) not in (int, float) or not low <= value <= high or not math.isfinite(value):
                values[key] = default
        for key, default in dict(reducedMotion=False, animatedBackground=True, highContrast=False).items():
            if not isinstance(values.get(key), bool):
                values[key] = default
        for key, value in values.items():
            if key.startswith('lvsRead:') and (not isinstance(value, list) or not all(isinstance(token, str) for token in value)):
                values[key] = []
        return values

    @Property('QVariantMap', notify=changed)
    def notice(self):
        return self._notice

    @Property(str, notify=changed)
    def school(self):
        return str(self.data.get('main_url') or '')

    @Property(str, notify=changed)
    def warnings(self):
        messages = [text(w.get('title'))+': '+text(w.get('message')) for w in self.data.get('warnings', []) if isinstance(w, dict)]
        if self.data.get('results_note'):
            messages.append(text(self.data['results_note']))
        lvs = self.data.get('lvs') or {}
        messages += [text(lvs[k]) for k in ('notes_error', 'absences_error') if lvs.get(k)]
        return '\n\n'.join(messages)

    def _job(self, name, action):
        if name in self._jobs or self._closed or (name in ('sync', 'setup') and self._jobs & {'sync', 'setup', 'install'}):
            return False
        self._jobs.add(name)
        self.changed.emit()
        def run():
            try:
                result, failure = action(), None
            except Exception as exc:
                result, failure = None, exc
            if not self._closed:
                self._finished.emit(name, result, failure)
        threading.Thread(target=run, daemon=True).start()
        return True

    @Slot(str, object, object)
    def _receive(self, name, result, failure):
        if self._closed:
            return
        self._jobs.discard(name)
        if failure is not None:
            import app_errors
            info = app_errors.explain(failure, app_errors.read_main_url(self.root/'credentials.yml'))
            self._last_failure = dict(kind=info['kind'], trace=app_errors.safe_traceback(failure))
            if isinstance(failure, app_errors.SyncError) and failure.title == 'Could not verify the signed-in account':
                self._last_failure['account_response'] = failure.details
            log_error(self.root, info)
            self.error.emit('\n\n'.join(str(info.get(k) or '') for k in ('title', 'message', 'hint')))
        elif name == 'sync' or (name == 'setup' and result):
            self._last_failure = None
            self.reload()
            if name == 'setup' and not self.renderingChoicePending:
                self.syncNow()
        elif name == 'check-update' and result:
            self._update = result
            self._notice = dict(kind='update', text=f"Version {result['version']} is available.")
        elif name == 'install':
            self.quitRequested.emit()
        elif name.startswith('lvs:'):
            token, account = name[4:].rsplit('|', 1)
            if self.data.get('account_key') == account:
                try:
                    self.verify_account()
                    if result.get('private') or result.get('deleted'):
                        raise ValueError('This note is no longer available.')
                    self.markRead(token)
                    self.detailReady.emit(token, dict(title='LVS note', body='\n\n'.join(filter(None, [text(result.get('text')), fields_text(result.get('fields')), fields_text([('Choice', result.get('choice')), ('Date', result.get('date'))])])), links=result.get('attachments') or []))
                except Exception:
                    self.error.emit('The note is no longer available for this account. Sync LVS and try again.')
        self.changed.emit()

    @Slot(result=bool)
    def syncNow(self):
        if self.renderingChoicePending:
            self.error.emit('Choose Fancy or Performance in Settings before the first sync.')
            return False
        def sync_now():
            import sync
            return sync.run(days_back=10, days_ahead=21)
        return self._job('sync', sync_now)

    @Slot(result=bool)
    def openSetup(self):
        def setup():
            path = self.root/'credentials.yml'
            before = path.stat().st_mtime_ns if path.exists() else None
            command = [sys.executable]
            if not getattr(sys, 'frozen', False):
                command.append(str(Path(__file__).resolve().parents[1]/'desktop_app.py'))
            process = subprocess.run(command+['--setup-only'], env=dict(os.environ, PYINSTALLER_RESET_ENVIRONMENT='1'), check=False,
                                     creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            after = path.stat().st_mtime_ns if path.exists() else None
            return process.returncode == 0 and before != after
        return self._job('setup', setup)

    @Slot('QVariantMap', result=bool)
    def saveSettings(self, values):
        choices = dict(renderingMode=('fancy', 'performance'), style=('vivid', 'clear'), scheme=('auto', 'dark', 'light'))
        try:
            if self._settings.get('qmlVersion') != 1:
                names = set(choices) | {'glassLevel', 'distortion', 'textSize', 'wallpaperIndex', 'reducedMotion', 'animatedBackground', 'highContrast'}
                values = {**{k: v for k, v in self.settings.items() if k in names}, **values}
            for key, value in values.items():
                if key in choices:
                    if value not in choices[key]:
                        raise ValueError('Unknown appearance choice')
                elif key in ('glassLevel', 'distortion', 'textSize', 'wallpaperIndex'):
                    bounds = {'glassLevel': (0, 1), 'distortion': (0, 1), 'textSize': (.9, 1.35), 'wallpaperIndex': (0, 3)}[key]
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not bounds[0] <= value <= bounds[1] or not math.isfinite(value):
                        raise ValueError('Invalid appearance value')
                elif key in ('reducedMotion', 'animatedBackground', 'highContrast'):
                    if not isinstance(value, bool):
                        raise ValueError('Invalid accessibility value')
                else:
                    raise ValueError('Unknown setting')
            if self._settings.get('qmlVersion') != 1 or any(self._settings.get(k) != v for k, v in values.items()):
                self._settings = task_state.save_appearance_settings(self.root, values)
            return True
        except (OSError, ValueError):
            self.error.emit('Could not save settings. Check disk access and try again.')
            return False

    @Slot(str, result=bool)
    def chooseRendering(self, mode):
        if not self.saveSettings(dict(renderingMode=mode)):
            return False
        try:
            (self.root/'data/rendering_choice_pending').unlink(missing_ok=True)
        except OSError:
            self.error.emit('Could not save your rendering choice. Please try again.')
            return False
        self.changed.emit()
        if self.sync_after_choice:
            self.sync_after_choice = False
            self.syncNow()
        return True

    @Slot(str, result=bool)
    def setDateChecker(self, mode):
        try:
            self._settings = task_state.set_setting(self.root, 'dateChecker', mode)
            self.changed.emit()
            return True
        except Exception:
            self.error.emit('Could not change the date checker. Check your API key and login settings.')
            return False

    @Slot(result='QVariantMap')
    def dateChecker(self):
        try:
            return task_state.date_checker_state(self.root)
        except Exception:
            return dict(mode='local', geminiAvailable=False)

    @Property('QVariantMap', notify=changed)
    def checkerState(self):
        return self.dateChecker()

    def read_key(self):
        return 'lvsRead:'+json.dumps([self.data.get('main_url') or '', self.data.get('user_id') or '', (self.data.get('lvs') or {}).get('since') or ''], ensure_ascii=False, separators=(',', ':'))

    @Property(int, notify=changed)
    def unreadCount(self):
        read = self.settings.get(self.read_key(), [])
        return sum(kind+':'+str(item.get('id') or '') not in read for kind in ('notes', 'absences') for item in (self.data.get('lvs') or {}).get(kind, []))

    @Slot(str, result=bool)
    def markRead(self, token):
        try:
            self.verify_account()
            all_tokens = [kind+':'+str(item['id']) for kind in ('notes', 'absences') for item in (self.data.get('lvs') or {}).get(kind, [])]
            selected = all_tokens if token == '*' else [token] if token in all_tokens else []
            current = task_state.load_settings(self.root, strict=True).get(self.read_key(), [])
            if not isinstance(current, list) or not all(isinstance(token, str) for token in current):
                raise ValueError('Invalid read state')
            self._settings = task_state.set_setting(self.root, self.read_key(), list(dict.fromkeys(current+selected)))
            self.changed.emit()
            return True
        except Exception:
            self.error.emit('Could not save LVS read status. Please try again.')
            return False

    @Slot(str, result=bool)
    def openExternal(self, url):
        try:
            parsed = urlsplit(url)
            return bool(parsed.scheme.lower() in ('https', 'http') and parsed.hostname and not parsed.username and QDesktopServices.openUrl(QUrl(url)))
        except ValueError:
            return False

    @Slot(result=bool)
    def copyDiagnostics(self):
        from PySide6.QtGui import QGuiApplication
        from version import __version__
        payload = dict(version=__version__, generated_at=self.data.get('generated_at'),
                       last_failure=self._last_failure,
                       counts={k: len(self.data.get(k) or []) for k in ('todos', 'days', 'all_classes', 'results')},
                       optional_sections={k: v.get('status') for k, v in (self.data.get('optional_section_status') or {}).items() if isinstance(v, dict)})
        QGuiApplication.clipboard().setText(json.dumps(payload, indent=2))
        return True

    @Slot(str, result='QVariantMap')
    def taskDetail(self, task_id):
        try:
            self.verify_account()
        except Exception:
            return {}
        item = next((t for t in self.data.get('todos', []) if str(t.get('id')) == task_id), None)
        if not item:
            return {}
        flags = self.taskBadges(task_id)
        metadata = fields_text([('Course', item.get('course')), ('Type', item.get('type')), ('Posted', written_date(item.get('posted_date'))), ('Due', written_date(item.get('due_date')))])
        body = text(item.get('body'))
        links = list(item.get('attachments') or [])+list(item.get('weblinks') or [])
        if self.school:
            links.append(dict(name='Open in Smartschool', url=planner_url(self.data, item, item.get('posted_date'))))
        return dict(body=body, metadata=metadata, status=flags, links=links)

    @Slot(str, result=str)
    def taskBadges(self, task_id):
        item = next((t for t in self.data.get('todos', []) if str(t.get('id')) == task_id), {})
        return ' · '.join(indicator['label'] for indicator in task_indicators(item))

    @Slot(str, result=bool)
    def canFocus(self, task_id):
        item = next((t for t in self.data.get('todos', []) if str(t.get('id')) == task_id), {})
        return bool(item) and not re.search(r'\b(meenemen|meebrengen|meebreng|herinnering|herinneringen|reminder|reminders|materiaal|materialen)\b|^ME$', str(item.get('type') or '').strip(), re.I)

    @Property('QStringList', notify=changed)
    def gradeCourses(self):
        return ['All subjects'] + sorted({text(r.get('course')) for r in self.data.get('results', []) if text(r.get('course'))})

    @Slot(int, str, result='QVariantList')
    @Slot(int, str, str, result='QVariantList')
    def groups(self, section, query, course='All subjects'):
        from .sections import groups
        return groups(self, section, query, course)

    @Slot(str)
    def openNote(self, note_id):
        try:
            self.verify_account()
            if not any(str(n.get('id')) == note_id for n in (self.data.get('lvs') or {}).get('notes', [])):
                raise ValueError('Unknown note')
            account = self.data['account_key']
        except Exception:
            self.error.emit('Sync this account before opening LVS notes.')
            return
        def fetch():
            import sync
            credentials = credential_store.smartschool_credentials(self.root/'credentials.yml')
            detail = sync.fetch_lvs_note_detail(sync.TimeoutSmartschool(credentials), note_id)
            if self.account() != account:
                raise ValueError('Login details changed during the request.')
            return detail
        self._job('lvs:notes:'+note_id+'|'+account, fetch)

    def startUpdates(self):
        import updater
        from version import __version__, RELEASE_NOTES
        try:
            if '--updated' in sys.argv:
                updater.prepare_installed_notice(self.root, __version__, RELEASE_NOTES)
            self._notice = updater.load_update_notice(self.root, __version__) or {}
            if self._notice:
                self._notice = dict(kind='release', text=self._notice.get('notes') or RELEASE_NOTES)
            elif updater.pending_install_failure(self.root):
                self._notice = dict(kind='failure', text='The previous update could not finish. Your existing app was kept. Try the update again.')
            self.changed.emit()
        except OSError:
            pass
        if not self._notice:
            self._check_updates()

    def _check_updates(self):
        if not self._updates_checked and (getattr(sys, 'frozen', False) or os.environ.get('SSP_UPDATE_TEST')):
            import updater
            from version import __version__
            self._updates_checked = True
            self._job('check-update', lambda: updater.check_for_update(__version__))

    @Slot()
    def dismissNotice(self):
        import updater
        from version import __version__
        try:
            if self._notice.get('kind') == 'release':
                updater.dismiss_update_notice(self.root, __version__)
            elif self._notice.get('kind') == 'failure':
                updater.acknowledge_install_failure(self.root)
            self._notice = {}
            self.changed.emit()
            self._check_updates()
        except OSError:
            self.error.emit('Could not save your dismissal. Please try again.')

    @Slot(result=bool)
    def installUpdate(self):
        if not self._update or self.busy:
            return False
        info = self._update.copy()
        def install():
            import updater
            path = updater.download_and_verify(info)
            updater.save_update_notice(self.root, info)
            updater.launch_installer(path, self.root)
        return self._job('install', install)

    def shutdown(self):
        self._closed = True
