"""Optional school panels; network and AI operations stay off the GUI thread."""
import shutil
import uuid
import hashlib
from datetime import date, timedelta
from pathlib import Path
from PySide6.QtCore import QObject, Property, Signal, Slot, QUrl, QStandardPaths
from PySide6.QtGui import QDesktopServices
import credential_store
from smartschool import AppCredentials
from secure_session import SecureSmartschool
from . import feature_state, school_services, school_ai
from .message_composer import MessageComposer


class _RequestExpired(ValueError):
    pass


class _LocalCopyChanged(ValueError):
    pass


class SchoolFeatures(QObject):
    changed = Signal()
    messagesChanged = Signal()
    resourcesChanged = Signal()
    downloadsChanged = Signal()
    saveRequested = Signal(str, QUrl)
    replacementReady = Signal(str, QUrl)
    filePreviewRequested = Signal('QVariantMap')
    closeFilePreview = Signal()
    replyDraftReady = Signal('QVariantMap',str)
    replyDraftSaved = Signal()

    def __init__(self, backend):
        super().__init__(backend)
        self.backend = backend
        self._cache, self._detail = {}, {}
        self._reply, self._summary, self._period = '', [], ''
        self._summary_ready = False
        self._message_loading, self._message_error = False, ''
        self._message_folder = 'inbox'
        self._message_limit = 50
        self._generation = 0
        self._replacement_request = 0
        self._replacement_profiles = {}
        self._composer = MessageComposer(self)
        self._composer_account = self.accountKey
        self._replacement_loading, self._replacement_error = False, ''
        backend.changed.connect(self.changed.emit)

    def reset(self):
        # Invalidate account-bound work before any observer can resume a queued request.
        self._generation += 1
        if self._composer_account != self.accountKey:
            self._composer.reset()
            self._composer_account = self.accountKey
        self._cache, self._detail = {}, {}
        self._reply, self._summary, self._period = '', [], ''
        self._summary_ready = False
        self._message_loading, self._message_error = False, ''
        self._message_folder = 'inbox'
        self._message_limit = 50
        account = self.backend.data.get('account_key')
        if account:
            try:
                self._cache = feature_state.load(self.backend.root, account)
            except (ValueError, OSError):
                self.backend.error.emit('Saved school information could not be read. Existing files were kept.')
        self.closeFilePreview.emit()
        self.closeReplacement()
        self.messagesChanged.emit(); self.resourcesChanged.emit(); self.downloadsChanged.emit()
        self.changed.emit()

    @Property('QVariantList', notify=messagesChanged)
    def messages(self):
        return self._cache.get('messages', []) if self._message_folder=='inbox' else self._cache.get('messageFolders', {}).get(self._message_folder, [])
    @Property(str, notify=messagesChanged)
    def messageFolder(self): return self._message_folder
    @Property(int, notify=messagesChanged)
    def messageLimit(self): return self._message_limit
    @Property(bool, notify=changed)
    def messageActionsBlocked(self):
        return any(action['folder']==self._message_folder for action in self._cache.get('messageActions',[]))
    @Property(str, notify=changed)
    def accountKey(self): return self.backend.data.get('account_key', '')
    @Property('QVariantMap', notify=changed)
    def messageDetail(self): return self._detail
    @Property(bool, notify=changed)
    def messageLoading(self): return self._message_loading
    @Property(str, notify=changed)
    def messageError(self): return self._message_error
    @Property('QVariantMap', notify=resourcesChanged)
    def resources(self): return self._cache.get('resources', {})
    @Property('QVariantList', notify=downloadsChanged)
    def downloadedFiles(self):
        return [dict(key=r['key'], name=r['name'], source=r.get('source', ''), sourceId=r.get('sourceId', '')) for r in self._cache.get('downloads', [])]
    @Property(bool, notify=changed)
    def featureBusy(self): return any(n.startswith('feature:') for n in self.backend._jobs)
    @Property(bool, notify=changed)
    def aiAvailable(self):
        try:
            return bool(credential_store.load_credentials(self.backend.root/'credentials.yml').get('gemini_api_key', '').strip())
        except Exception:
            return False
    @Property(str, notify=changed)
    def aiReply(self): return self._reply
    @Property('QVariantList', notify=changed)
    def weeklySummary(self): return self._summary
    @Property(bool, notify=changed)
    def weeklySummaryReady(self): return self._summary_ready
    @Property(str, notify=changed)
    def selectedPeriod(self): return self._period
    @Property(QObject, constant=True)
    def composer(self): return self._composer
    @Property(bool, notify=changed)
    def replacementLoading(self): return self._replacement_loading
    @Property(str, notify=changed)
    def replacementError(self): return self._replacement_error

    @Slot()
    def closeReplacement(self):
        self._replacement_request += 1
        self._replacement_loading, self._replacement_error = False, ''
        self.changed.emit()

    @Slot(QObject)
    def configureReplacementProfile(self, profile):
        from .replacement_viewer import configure_profile
        key = id(profile)
        self._replacement_profiles[key] = (profile, configure_profile(profile))
        profile.destroyed.connect(lambda: self._replacement_profiles.pop(key, None))

    @Slot()
    def loadReplacement(self):
        from .replacement_viewer import fetch_preview
        self._replacement_request += 1
        request = self._replacement_request
        self._replacement_loading, self._replacement_error = True, ''
        self.changed.emit()
        if not self._start('replacement', lambda c, a: dict(request=request, preview=self._session(c, fetch_preview))):
            self._replacement_loading = False
            self._replacement_error = 'Wait for the current request, then retry.'
            self.changed.emit()

    def _start(self, kind, action):
        try:
            account, generation = self.backend.data.get('account_key'), self._generation
            self.backend.verify_account()
            if self.featureBusy:
                raise ValueError('Wait for the current school request to finish.')
            credentials = dict(credential_store.load_credentials(self.backend.root/'credentials.yml'))
            if credential_store.account_key(credentials) != account:
                raise ValueError('Account changed before the request.')
            def current():
                try:
                    return self._generation == generation and self.backend.account() == account
                except Exception:
                    return False
            def work():
                if not current(): raise _RequestExpired()
                try:
                    value = action(credentials, account)
                except Exception:
                    if not current(): raise _RequestExpired() from None
                    raise
                if not current(): raise _RequestExpired()
                return dict(account=account, generation=generation, value=value)
            return self.backend._job('feature:'+kind, work)
        except Exception:
            self.backend.error.emit('Sync this account first, or wait for the current request to finish.')
            return False

    def _session(self, credentials, action):
        login = AppCredentials(username=credentials.get('username', ''), password=credentials.get('password', ''),
                               main_url=credentials.get('main_url', ''), mfa=credentials.get('mfa') or 'REPLACE_ME')
        session = SecureSmartschool(login, self.backend.root)
        try:
            session.authenticated_user
            return action(session)
        finally:
            session.close()

    def receive(self, kind, result, failure):
        if kind.startswith('compose_'):
            self._composer.receive(kind, result, failure)
            self.changed.emit()
            return
        if isinstance(failure, _RequestExpired):
            if kind == 'message': self._message_loading = False
            self.changed.emit()
            return
        if failure is not None:
            if kind=='trash_message':
                self.backend.error.emit('The move to Trash could not be confirmed. Refresh this folder before trying another message action.')
                self.changed.emit()
                return
            if isinstance(failure,_LocalCopyChanged):
                self.backend.error.emit('This downloaded file has local changes. Save those changes elsewhere or remove the local copy before fetching the school version again.')
                self.changed.emit()
                return
            if kind == 'view_report':
                self.backend.error.emit('The report could not be checked for changes. Your saved copy was kept; retry when connected.')
                self.changed.emit()
                return
            if kind == 'message':
                self._message_loading = False
                self._message_error = 'This message could not be refreshed. Check your connection and retry. Any saved copy is shown below.'
            if kind == 'replacement':
                self._replacement_loading = False
                self._replacement_error = 'Teacher replacements could not be opened. Check your connection and school access, then retry.'
                self.changed.emit()
                return
            self.backend.error.emit('The school or AI request could not be completed. Check your connection, account access and API key, then retry.')
        elif (result.get('account') == self.backend.data.get('account_key') and
              result.get('generation') == self._generation and result['account'] == self.backend.account()):
            value, account = result['value'], result['account']
            try:
                if kind in ('messages', 'resources'):
                    if kind == 'resources':
                        value = dict(value)
                        for section in value.get('errors', {}):
                            if section in self.resources:
                                value[section] = self.resources[section]
                    if kind=='messages' and isinstance(value,dict):
                        folder,rows=value['folder'],value['items']
                        if folder=='inbox':self._cache=feature_state.update(self.backend.root,account,'messages',rows)
                        else:
                            folders=dict(self._cache.get('messageFolders',{}));folders[folder]=rows
                            self._cache=feature_state.update(self.backend.root,account,'messageFolders',folders)
                        actions=[a for a in self._cache.get('messageActions',[]) if a['folder']!=folder]
                        if actions!=self._cache.get('messageActions',[]):self._cache=feature_state.update(self.backend.root,account,'messageActions',actions)
                    else:self._cache = feature_state.update(self.backend.root, account, kind, value)
                    if kind == 'messages': self.messagesChanged.emit()
                    else: self.resourcesChanged.emit()
                    if kind == 'resources' and not value.get('errors', {}).get('periods') and self._period and not any(p.get('name') == self._period for p in value.get('periods', [])):
                        self._period = ''
                        self.backend.groupsChanged.emit(4)
                elif kind == 'message':
                    details = dict(self._cache.get('details', {})); details[value['id']] = value
                    self._cache = feature_state.update(self.backend.root, account, 'details', details)
                    self._detail = value
                    self._message_loading, self._message_error = False, ''
                elif kind == 'reply':
                    if isinstance(value,dict):
                        self._reply=value['body']
                        if value.get('draftRevision',self._composer.draftRevision)!=self._composer.draftRevision:
                            if self._composer.saveReplyAsDraft(value['message'],self._reply):self.replyDraftSaved.emit()
                            else:self.backend.error.emit('The Gemini reply could not be saved. Your active draft was kept; check disk access and retry.')
                        else:self.replyDraftReady.emit(value['message'],self._reply)
                    else:self._reply=value
                elif kind=='trash_message':
                    identifier=value['id']
                    self._cache=feature_state.move_message_to_trash(self.backend.root,account,identifier)
                    self._detail={};self.messagesChanged.emit()
                elif kind == 'week': self._summary = value; self._summary_ready = True
                elif kind == 'replacement' and value['request'] == self._replacement_request:
                    self._replacement_loading = False
                    self._replacement_error = ''
                    self.replacementReady.emit(value['preview']['html'], QUrl(value['preview']['base']))
                elif kind in ('download', 'view_report', 'view_planner'):
                    entries = self._cache.get('downloads', [])
                    if value.get('source') in ('report','planner') and value.get('sourceId'):
                        entries = [r for r in entries if not (r.get('source') == value['source'] and r.get('sourceId') == value['sourceId'])]
                    entries = entries+[value]
                    self._cache = feature_state.update(self.backend.root, account, 'downloads', entries)
                    self.downloadsChanged.emit()
                    if kind in ('view_report','view_planner'): self._open_downloaded(value['key'])
            except Exception:
                if kind == 'message':
                    self._message_loading = False
                    self._message_error = 'This message could not be saved. Check disk access and retry.'
                self.backend.error.emit('The result could not be saved. Existing data was kept.')
        self.changed.emit()

    @Slot()
    def loadMessages(self):
        folder=self._message_folder
        if folder=='local':self.messagesChanged.emit();return
        limit=self._message_limit
        self._start('messages',lambda c,a:dict(folder=folder,items=self._session(c,lambda s:school_services.fetch_messages(s,limit=limit,folder=folder))))
    @Slot()
    def loadMoreMessages(self):
        if not self.featureBusy and self._message_folder!='local' and self._message_limit<school_services.MAX_RECORDS:
            self._message_limit=min(school_services.MAX_RECORDS,self._message_limit+50)
            self.messagesChanged.emit();self.loadMessages()
    @Slot(str,result=bool)
    def selectMessageFolder(self,folder):
        if folder not in ('inbox','outbox','trash','scheduled','draft','local') or self.featureBusy:return False
        self._message_folder=folder;self._detail={};self._message_loading=False;self._message_error=''
        self._message_limit=max(50,min(school_services.MAX_RECORDS,len(self.messages)))
        self.messagesChanged.emit();self.changed.emit()
        return True
    @Slot()
    def loadResources(self): self._start('resources', lambda c, a: self._session(c, school_services.fetch_resources))
    @Slot(str, result=bool)
    def openMessage(self, message_id):
        listed=any(m.get('id') == message_id for m in self.messages)
        if not (listed or
                any(t.get('message_id') == message_id for t in self._cache.get('tasks', []))): return False
        if self.featureBusy: return False
        self._reply = ''
        cached=self._cache.get('details', {}).get(message_id,{})
        folder=self._message_folder if listed else cached.get('folder','inbox')
        self._detail=cached if cached.get('folder','inbox')==folder else {}
        if folder=='local':return False
        self._message_loading, self._message_error = True, ''
        self.changed.emit()
        started = self._start('message', lambda c, a: self._session(c, lambda s: school_services.fetch_message(s, message_id,folder=folder)))
        if not started:
            self._message_loading = False
            self.changed.emit()
        return bool(started)
    @Slot(str,result=bool)
    def trashMessage(self,message_id):
        folder=self._message_folder
        if self.featureBusy or self.messageActionsBlocked or folder not in ('inbox','outbox') or not any(m.get('id')==message_id for m in self.messages):return False
        generation,account=self._generation,self.accountKey
        try:
            self.backend.verify_account()
            actions=list(self._cache.get('messageActions',[]))+[dict(folder=folder,id=message_id)]
            self._cache=feature_state.update(self.backend.root,account,'messageActions',actions)
        except Exception:
            self.backend.error.emit('The message action could not be saved safely. Check disk access before trying again.')
            return False
        def action(credentials,expected):
            def current():return generation==self._generation and expected==account==self.accountKey==self.backend.account()
            self._session(credentials,lambda s:school_services.trash_message(s,message_id,folder=folder,current=current))
            return dict(id=message_id)
        started=bool(self._start('trash_message',action))
        if not started:
            try:self._cache=feature_state.update(self.backend.root,account,'messageActions',[a for a in actions if a['id']!=message_id])
            except Exception:pass
        self.changed.emit()
        return started
    @Slot()
    def clearReply(self): self._reply = ''; self.changed.emit()
    def _key(self, credentials):
        key = credentials.get('gemini_api_key', '')
        if not key.strip(): raise ValueError('AI requires a Gemini API key.')
        return key
    @Slot()
    def draftReply(self):
        if not self._detail or self._detail.get('canReply',True) is False: return
        message = dict(self._detail)
        revision=self._composer.draftRevision
        self._start('reply', lambda c, a:dict(message=message,body=school_ai.draft_reply(self._key(c), message),draftRevision=revision))
    @Slot()
    def summariseWeek(self):
        start, end = date.today(), date.today()+timedelta(days=6)
        tasks = [dict(id=t['taskId'], date=t['due'], title=t['title'], body=t['body']) for t in self.backend.tasks.all
                 if not t['done'] and start.isoformat() <= t['due'] <= end.isoformat()]
        self._start('week', lambda c, a: school_ai.summarise_week(self._key(c), tasks))
    @Slot(str)
    def selectPeriod(self, name):
        if name and not any(p.get('name') == name for p in self.resources.get('periods', [])): return
        self._period = name
        self.backend.groupsChanged.emit(4); self.changed.emit()
    @Slot(str, result=bool)
    def addMessageTask(self, due):
        try:
            account = self.backend.data.get('account_key')
            self.backend.verify_account()
            if date.fromisoformat(due).isoformat() != due: raise ValueError('Use YYYY-MM-DD.')
            if not self._detail: raise ValueError('Open a message first.')
            task = dict(id='local:'+uuid.uuid4().hex, description=self._detail['subject'][:300] or 'Message task',
                        course='Messages', type='Task', body=self._detail.get('body', '')[:10000],
                        due_date=due, posted_date=date.today().isoformat(), message_id=self._detail['id'])
            saved = feature_state.load(self.backend.root, account).get('tasks', [])+[task]
            feature_state.update(self.backend.root, account, 'tasks', saved)
            self.backend.reload()
            return True
        except Exception:
            self.backend.error.emit('The local task could not be saved. Choose a valid YYYY-MM-DD date and sync this account.')
            return False

    def _download(self, credentials, account, descriptor):
        folder = feature_state.directory(self.backend.root, account)/'downloads'
        previous = None
        if descriptor['kind'] in ('report','planner') and descriptor.get('id'):
            previous = next((r for r in reversed(feature_state.load(self.backend.root, account).get('downloads', []))
                             if r.get('source') == descriptor['kind'] and r.get('sourceId') == descriptor['id']), None)
        cached = dict(previous, path=str(feature_state.cached_path(self.backend.root, account, previous))) if previous else None
        if cached and descriptor['kind'] == 'planner' and cached.get('sha256'):
            from .file_preview import LOCAL_APPLICATIONS
            path = Path(cached['path'])
            if path.suffix.lower() in LOCAL_APPLICATIONS and path.is_file():
                with path.open('rb') as file:
                    if hashlib.file_digest(file,'sha256').hexdigest() != cached['sha256']:
                        raise _LocalCopyChanged()
        if cached and descriptor['kind'] == 'planner' and Path(previous['file']).suffix.lower() != Path(descriptor['name']).suffix.lower():
            cached = None
        result = self._session(credentials, lambda s: school_services.download(s, descriptor, folder, cached=cached)
                               if descriptor['kind'] in ('report','planner') else school_services.download(s, descriptor, folder))
        path = Path(result['path'])
        if path.resolve().parent != folder.resolve(): raise ValueError('Invalid download destination.')
        record = dict(key=previous['key'] if previous else uuid.uuid4().hex, file=path.name, name=result['name'],
                      source=descriptor['kind'], sourceId=descriptor.get('messageId', descriptor.get('id', '')))
        record.update({key:result[key] for key in ('sha256','etag','lastModified','resourceKey') if key in result})
        return record

    @Slot(str)
    def viewReport(self, identifier):
        known = any(r.get('id') == identifier for r in self.resources.get('reports', [])) or any(
            r.get('source') == 'report' and r.get('sourceId') == identifier for r in self._cache.get('downloads', []))
        if known:
            self.closeFilePreview.emit()
            descriptor = dict(kind='report', id=identifier)
            self._start('view_report', lambda c, a: self._download(c, a, descriptor))
    @Slot(str, str)
    def downloadAttachment(self, source, identifier):
        if source == 'message':
            descriptor = next((a for a in self._detail.get('attachments', []) if a.get('id') == identifier), None)
        elif source == 'report':
            descriptor = dict(kind='report', id=identifier) if any(r.get('id') == identifier for r in self.resources.get('reports', [])) else None
        else: descriptor = None
        if descriptor: self._start('download', lambda c, a: self._download(c, a, dict(descriptor)))
    @Slot(str, int)
    def downloadPlanner(self, task_id, index):
        descriptor = self._planner_file(task_id, index)
        if descriptor:self._start('download', lambda c, a: self._download(c, a, descriptor))

    def _planner_file(self, task_id, index):
        try:
            info = self.backend.taskDetail(task_id)
            if index < 0: return
            attachment = info['links'][index]
            if not attachment.get('downloadable'): return
            url = attachment.get('url', '')
            return dict(kind='planner', name=attachment.get('name', ''), url=url, id=hashlib.sha256(url.encode()).hexdigest())
        except (KeyError, IndexError, TypeError, AttributeError): return None

    @Slot(str, int)
    def viewPlanner(self, task_id, index):
        descriptor = self._planner_file(task_id, index)
        if descriptor:
            self.closeFilePreview.emit()
            self._start('view_planner', lambda c, a: self._download(c, a, descriptor))

    @Slot(str)
    def viewLinkedFile(self, url):
        if not isinstance(url,str) or not url:return
        items = list(self.backend.data.get('todos', []))
        for source in ('days','all_classes'):
            items.extend(event for day in self.backend.data.get(source, []) for event in day.get('events', []))
        attachment = next((a for item in items for a in item.get('attachments') or [] if a.get('url') == url), None)
        if attachment:
            descriptor = dict(kind='planner',name=attachment.get('name',''),url=url,id=hashlib.sha256(url.encode()).hexdigest())
            self.closeFilePreview.emit()
            self._start('view_planner',lambda c,a:self._download(c,a,descriptor))
    def _record(self, key):
        account = self.backend.data.get('account_key')
        self.backend.verify_account()
        record = next(r for r in self._cache.get('downloads', []) if r['key'] == key)
        return record, feature_state.cached_path(self.backend.root, account, record)
    @Slot(str)
    def openDownloaded(self, key):
        try:
            record, _ = self._record(key)
            if record.get('source') == 'report':
                self.viewReport(record['sourceId'])
            else: self._open_downloaded(key)
        except Exception:
            self.backend.error.emit('This file cannot be opened. Download it again or check your account.')

    def _open_downloaded(self, key):
        try:
            from .file_preview import describe
            record, path = self._record(key)
            info = dict(describe(path,record['name']),key=key)
            if info['kind'] == 'external':
                if not QDesktopServices.openUrl(info['url']): raise ValueError('No local application could open this file')
            else:self.filePreviewRequested.emit(info)
        except Exception:
            self.backend.error.emit('This file cannot be opened here. Use Save as to inspect it, or download it again.')
    @Slot(str)
    def saveDownloaded(self, key):
        try:
            record, path = self._record(key)
            if not path.is_file(): raise ValueError('File unavailable.')
            folder = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
            self.saveRequested.emit(key, QUrl.fromLocalFile(str(Path(folder)/Path(record['name']).name)))
        except Exception:
            self.backend.error.emit('The file could not be saved. Your offline copy was kept.')
    @Slot(str, QUrl)
    def exportDownloaded(self, key, destination):
        try:
            if not destination.isLocalFile(): raise ValueError('Choose a local file.')
            _, path = self._record(key)
            shutil.copyfile(path, destination.toLocalFile())
        except Exception:
            self.backend.error.emit('The file could not be saved. Your offline copy was kept.')
    @Slot(str)
    def removeDownloaded(self, key):
        try:
            account = self.backend.data.get('account_key')
            _, path = self._record(key)
            path.unlink(missing_ok=True)
            self._cache = feature_state.update(self.backend.root, account, 'downloads', [r for r in self._cache['downloads'] if r['key'] != key])
            self.downloadsChanged.emit()
            self.changed.emit()
        except Exception:
            self.backend.error.emit('The offline copy could not be removed.')
