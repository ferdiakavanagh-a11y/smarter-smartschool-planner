"""Account-bound native message drafts and one-attempt delivery."""
from copy import deepcopy
from html import escape
from itertools import islice
import hashlib
from pathlib import Path
import uuid

import requests
from PySide6.QtCore import QObject, Property, Signal, Slot, QTimer, QUrl
from smartschool import MessageComposerForm, RecipientType
from .school_services import _school_url


def _identity(user):
    identity = (user.user_id, user.ss_id, user.user_lt)
    if (any(type(value) is not int for value in identity) or identity[0] <= 0
            or identity[1] < 0 or identity[2] < 0):
        raise ValueError('Only a resolved school user can receive a new message')
    return identity


def _group_identity(group):
    if (type(group.group_id) is not int or group.group_id <= 0
            or type(group.ss_id) is not int or group.ss_id < 0):
        raise ValueError('Only a resolved school group can receive a new message')
    return ('group', group.group_id, group.ss_id)


def _coaccount_name(user):
    return str(user.coaccountname or user.value)[:300]


def _sdk_recipients(form, query, coaccounts=False):
    if coaccounts:
        if form.can_send_to_coaccounts is not True:
            raise ValueError('This school account cannot message co-accounts')
        # Verified SDK 0.12 adapter: public search_users only searches main accounts.
        return form._search_recipients(query, coaccount=True)
    return form.search_users(query)


def _search(session, query, coaccounts=False):
    form = MessageComposerForm.create(session=session)
    available = form.can_send_to_coaccounts is True
    if coaccounts and not available:
        return dict(choices=[], coaccountsAvailable=False)
    users, groups = _sdk_recipients(form, query, coaccounts)
    choices = []
    for user in islice(users, 20):
        try:
            identity = _identity(user)
        except ValueError:
            continue
        if (identity[2] > 0) != coaccounts: continue
        detail = ' · '.join(str(value)[:200] for value in (user.classname, user.schoolname) if value)
        if coaccounts: detail = 'Co-account for '+str(user.value)[:300]+(' · '+detail if detail else '')
        choices.append(dict(identity=identity, name=_coaccount_name(user) if coaccounts else str(user.value)[:300], query=query, detail=detail))
    for group in islice(groups if not coaccounts else [], 20):
        try:
            identity = _group_identity(group)
        except ValueError:
            continue
        detail = str(group.description or '')[:300]
        choices.append(dict(identity=identity, name=str(group.value)[:300], query=query,
                            detail='Group'+(' · '+detail if detail else '')))
    return dict(choices=choices, coaccountsAvailable=available)


def _attachment_descriptors(paths, existing, current):
    additions = []
    total = sum(a['bytes'] for a in existing)
    for raw in paths:
        if not current(): raise ValueError('Account changed')
        path = Path(raw)
        if not path.is_absolute() or str(path).startswith(('\\\\', '//')): raise ValueError('Local files only')
        for part in (path, *path.parents):
            if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
                raise ValueError('Linked files are not supported')
        path = path.resolve(strict=True)
        if not path.is_file(): raise ValueError('Invalid file')
        from .school_services import _attachment_name
        _attachment_name(path.name)
        if any(a['path'] == str(path) for a in existing+additions): continue
        size = path.stat().st_size
        total += size
        if total > 50*1024*1024 or len(existing+additions) >= 20: raise ValueError('Too large')
        digest, read = hashlib.sha256(), 0
        with path.open('rb') as source:
            while chunk := source.read(min(1024*1024, size-read+1)):
                read += len(chunk)
                if read > size or not current(): raise ValueError('File changed')
                digest.update(chunk)
        if read != size: raise ValueError('File changed')
        additions.append(dict(path=str(path), name=path.name, bytes=size, sha256=digest.hexdigest()))
    if not current(): raise ValueError('Account changed')
    return additions


def _reply_content(mode, detail, body_override):
    original_subject = str(detail.get('subject', ''))[:250]
    prefix = 'Fwd: ' if mode == 'forward' else 'Re: '
    subject = (original_subject if original_subject.lower().startswith(prefix.lower()) else prefix+original_subject)[:250]
    sender = str(detail.get('sender', ''))[:300]
    original_body = str(detail.get('body', ''))
    quote = original_body[:90_000]
    if len(original_body) > 90_000: quote += '\n[Original message shortened to fit this draft.]'
    headers, hints = '', ([dict(field='To', name=sender)] if sender and mode != 'forward' else [])
    for label, key in (('To', 'to'), ('Cc', 'cc')):
        values = detail.get(key, [])
        if isinstance(values, str): values = [values] if values else []
        if isinstance(values, list) and values:
            headers += label+': '+', '.join(str(value)[:500] for value in values[:50])+'\n'
            if mode == 'replyAll': hints.extend(dict(field=label, name=str(value)[:500]) for value in values[:50] if value)
    body = ((body_override.strip()+'\n\n' if body_override.strip() else '')
            +'— Original message —\n'+('From: '+sender+'\n' if sender else '')
            +headers+'Subject: '+original_subject+'\n\n'+quote)
    return dict(subject=subject, body=body, sourceId=str(detail.get('id', ''))[:200],
                sourceFolder=str(detail.get('folder', 'inbox'))[:100]), hints


def _send(session, selected, subject, body, current, attempt):
    if not current(): raise ValueError('Account changed')
    form = MessageComposerForm.create(session=session)
    recipients = selected if isinstance(selected, list) else [selected]
    if any(r['identity'][0] != 'group' and r['identity'][2] > 0 for r in recipients) and form.can_send_to_coaccounts is not True:
        raise ValueError('This school account cannot message co-accounts')
    resolved = {}
    for choice in recipients:
        if not current(): raise ValueError('Account changed')
        is_group = choice['identity'][0] == 'group'
        coaccounts = not is_group and choice['identity'][2] > 0
        key = (choice['query'], coaccounts)
        if key not in resolved:
            resolved[key] = _sdk_recipients(form, choice['query'], coaccounts)
        users, groups = resolved[key]
        identity = _group_identity if is_group else _identity
        recipient = None
        for user in islice(groups if is_group else users, 100):
            try:
                if identity(user) == tuple(choice['identity']) and (not coaccounts or _coaccount_name(user) == choice['name']):
                    recipient = user
                    break
            except ValueError:
                continue
        if recipient is None or not current(): raise ValueError('Recipient changed')
        form.add_recipient(recipient, {'To': RecipientType.TO, 'Cc': RecipientType.CC,
                                      'Bcc': RecipientType.BCC}[choice.get('field', 'To')])
    form.set_subject(subject)
    form.set_message_html('<p>'+escape(body).replace('\n', '<br>')+'</p>')
    if not current(): raise ValueError('Account changed')
    url = _school_url(session, form._url)
    files = {key: (None, value) for key, value in form.payload.items()}
    if session.get_adapter(url).max_retries.total not in (0, False):
        raise ValueError('Message send retries must be disabled')
    for attachment in attempt.get('attachments', []):
        from .school_services import upload_message_attachment
        upload_message_attachment(session, form, attachment, current)
    if not current(): raise ValueError('Account changed')
    if attempt.get('persist_lock'):
        attempt['persist_lock']()
    if not current(): raise ValueError('Account changed')
    response = None
    try:
        # The SDK replays authenticated POSTs; sending a message must be attempted only once.
        attempt['started'] = True
        response = requests.Session.request(session, 'POST', url, files=files,
                                            allow_redirects=False, timeout=(10, 30))
        _school_url(session, response.url)
        return 'accepted' if 200 <= response.status_code < 300 else 'unknown'
    except Exception:
        return 'unknown'
    finally:
        if response is not None:
            try: response.close()
            except Exception: pass


class MessageComposer(QObject):
    changed = Signal()
    recipientsChanged = Signal()
    draftChanged = Signal()
    selectionChanged = Signal()
    attachmentsChanged = Signal()
    savedDraftsChanged = Signal()

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self._choices, self._rows = [], []
        self._recovery = {}
        self._revision, self._query_serial = 0, 0
        self._lookup_timer = QTimer(self)
        self._lookup_timer.setSingleShot(True)
        self._lookup_timer.setInterval(200)
        self._lookup_timer.timeout.connect(self._dispatch_lookup)
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(500)
        self._save_timer.timeout.connect(self.saveDraft)
        self.reset()
        owner.changed.connect(self._resume_lookup)

    def reset(self):
        availability = getattr(self, '_coaccounts_available', None) if getattr(self, '_account', None) == self.owner.accountKey else None
        unsaved_other_account = False
        if (hasattr(self, '_account') and self._account != self.owner.accountKey
                and not self.sending and (self._subject or self._body or self._selected_many or self._attachments)):
            draft = self._draft()
            try:
                self._persist(draft, self._account)
                self._recovery.pop(self._account, None)
            except (OSError, ValueError):
                self._recovery[self._account] = (draft, deepcopy(self._hints))
                unsaved_other_account = True
        self._revision += 1
        self._account = self.owner.accountKey
        self._query_serial += 1
        self._lookup_timer.stop()
        self._save_timer.stop()
        self._query, self._queued_query, self._operation = '', None, ''
        self._active_query_serial = -1
        self._set_choices([])
        self._selected = None
        self._selected_many = []
        self._field = 'To'
        self._recipient_mode, self._coaccounts_available = 'main', availability
        self._subject, self._body = '', ''
        self._draft_id = uuid.uuid4().hex
        self._mode, self._source_id, self._source_folder = 'new', '', 'inbox'
        self._hints, self._attachments, self._saved = [], [], []
        self._delivery_state, self._snapshot = 'editing', {}
        self._busy, self._locked = False, False
        self._error, self._status = '', ''
        self._save_warning = ''
        self._attempt = dict(started=False)
        try:
            self._saved = self._load_saved()
        except (OSError, ValueError):
            self._error = 'Saved drafts could not be read. Existing files were kept.'
        recovery = self._recovery.get(self._account)
        if recovery:
            durable = next((d for d in self._saved if d['id'] == recovery[0]['id']
                            and d['deliveryState'] != 'editing'), None)
            if durable:
                self._restore(durable)
                self._recovery.pop(self._account, None)
            else:
                self._restore(recovery[0])
                self._hints = recovery[1]
                self._error = 'Your latest draft was recovered in memory. Keep this window open until it can be saved.'
                self._save_warning = self._error
        elif unsaved_other_account:
            self._error = 'A draft from another account could not be saved. It is kept privately in memory; switch back to recover it.'
        self._selection_changed()
        self.attachmentsChanged.emit()
        self.savedDraftsChanged.emit()
        self.changed.emit()
        self.draftChanged.emit()

    def _selection_changed(self):
        self._selected_rows = [dict(index=i, name=r['name'], field=r['field'],
                                   kind='group' if r['identity'][0] == 'group' else 'user',
                                   coaccount=r['identity'][0] != 'group' and r['identity'][2] > 0)
                               for i, r in enumerate(self._selected_many)]
        self.selectionChanged.emit()

    def _load_saved(self):
        root = getattr(self.owner.backend, 'root', None)
        if root is None: return []  # Small offline owner fixtures have no application storage.
        from . import message_drafts
        return message_drafts.load(root, self._account)

    def _draft(self):
        return dict(id=self._draft_id, subject=self._subject, body=self._body, mode=self._mode,
                    sourceId=self._source_id, sourceFolder=self._source_folder,
                    recipients=[dict(kind='group' if r['identity'][0] == 'group' else 'user',
                                     identity=list(r['identity']), query=r['query'], name=r['name'], field=r['field'])
                                for r in self._selected_many], attachments=deepcopy(self._attachments),
                    deliveryState=self._delivery_state, attemptSnapshot=deepcopy(self._snapshot))

    def _persist(self, draft=None, account=None):
        root = getattr(self.owner.backend, 'root', None)
        if root is None: return
        from . import message_drafts
        message_drafts.save(root, account or self._account, draft or self._draft())

    @Slot(result=bool)
    def saveDraft(self):
        self._save_timer.stop()
        if self.sending: return True  # The immutable send snapshot is already saved.
        if self._account != self.owner.accountKey: return False
        if len(self._subject) > 250 or len(self._body) > 100_000:
            self._error = 'This draft exceeds the subject (250) or message (100,000) character limit. Shorten it before closing; your text is still here.'
            self._save_warning = self._error
            self.changed.emit(); return False
        if not (self._subject or self._body or self._selected_many or self._attachments) and not any(d['id'] == self._draft_id for d in self._saved): return True
        try:
            self._persist()
            self._recovery.pop(self._account, None)
            self._saved = self._load_saved()
        except (OSError, ValueError):
            warning = 'This draft could not be saved. Keep this window open and retry.'
            if self._locked and self._error:
                if warning not in self._error: self._error += ' '+warning
            else:
                self._error = warning
            self._save_warning = warning
            self.changed.emit()
            return False
        if self._save_warning:
            self._error = self._error.replace(self._save_warning, '').strip()
            self._save_warning = ''
        self.changed.emit()
        self.savedDraftsChanged.emit()
        return True

    @Slot(str, result=bool)
    def deleteDraft(self, draft_id):
        if self._busy or self._account != self.owner.accountKey: return False
        try:
            from . import message_drafts
            root = getattr(self.owner.backend, 'root', None)
            if root is not None: message_drafts.delete(root, self._account, draft_id)
            if draft_id == self._draft_id: self.reset()
            else:
                self._saved = self._load_saved()
                self.savedDraftsChanged.emit()
                self.changed.emit()
            return True
        except (OSError, ValueError):
            self._error = 'This draft could not be removed. Existing files were kept.'
            self.changed.emit(); return False

    @Slot(result=bool)
    def flushForExit(self):
        if not self.saveDraft(): return False
        for account, (draft, _) in list(self._recovery.items()):
            try:
                root = getattr(self.owner.backend, 'root', None)
                if root is not None:
                    from . import message_drafts
                    durable = next((d for d in message_drafts.load(root, account)
                                    if d['id'] == draft['id'] and d['deliveryState'] != 'editing'), None)
                    if not durable: self._persist(draft, account)
                self._recovery.pop(account, None)
            except (OSError, ValueError):
                self._error = 'A draft from another account is not saved yet. Switch back to recover it before closing the app.'
                self.changed.emit(); return False
        return True

    @Slot(str, str)
    def updateContent(self, subject, body):
        if self._locked or self.sending or self._account != self.owner.accountKey: return
        self._subject, self._body = subject, body
        self._save_timer.start()

    @Property(str, notify=draftChanged)
    def draftSubject(self): return self._subject
    @Property(str, notify=draftChanged)
    def draftBody(self): return self._body
    @Property(str, notify=draftChanged)
    def draftMode(self): return self._mode
    @Property(int, notify=draftChanged)
    def draftRevision(self): return self._revision
    @Property('QVariantList', notify=changed)
    def recipientHints(self): return self._hints
    @Property('QVariantList', notify=selectionChanged)
    def selectedRecipients(self): return self._selected_rows
    @Property('QVariantList', notify=attachmentsChanged)
    def attachments(self): return self._attachments
    @Property('QVariantList', notify=savedDraftsChanged)
    def savedDrafts(self):
        return [dict(d, recipientSummary=', '.join(r['name'] for r in d.get('recipients', [])))
                for d in self._saved]
    @Property(str, notify=changed)
    def recipientField(self): return self._field
    @Property(str, notify=changed)
    def recipientMode(self): return self._recipient_mode
    @Property(bool, notify=changed)
    def coaccountsUnavailable(self): return self._coaccounts_available is False

    @Slot(str)
    def setRecipientMode(self, mode):
        if (mode not in ('main', 'coaccounts') or mode == self._recipient_mode or self.sending or self._locked
                or mode == 'coaccounts' and self._coaccounts_available is False): return
        self._recipient_mode = mode
        self.updateRecipientQuery(self._query)

    @Slot(str)
    def setRecipientField(self, field):
        if field in ('To', 'Cc', 'Bcc') and not self.sending and not self._locked:
            self._field = field
            self.updateRecipientQuery('')

    @Slot(int)
    def removeRecipient(self, index):
        if self.sending or self._locked or not 0 <= index < len(self._selected_many): return
        self._selected_many.pop(index)
        self._selected = self._selected_many[-1] if self._selected_many else None
        self._selection_changed()
        self.changed.emit()
        self._save_timer.start()

    @Slot('QVariantList', result=bool)
    def addAttachments(self, urls):
        if self._busy or self._locked or self.owner.featureBusy: return False
        try:
            paths = []
            for value in urls:
                url = value if isinstance(value, QUrl) else QUrl(str(value))
                if not url.isLocalFile(): raise ValueError('Local files only')
                paths.append(url.toLocalFile())
            if not paths: return False
        except ValueError:
            self._error = 'Choose up to 20 local files, at most 50 MB together. Unreadable files were not attached.'
            self.changed.emit(); return False
        existing = deepcopy(self._attachments)
        self._start('compose_attach', lambda _, current: _attachment_descriptors(paths, existing, current), local=True)
        return True

    @Slot(int)
    def removeAttachment(self, index):
        if not self.sending and not self._locked and 0 <= index < len(self._attachments):
            self._attachments.pop(index)
            self.attachmentsChanged.emit()
            self.changed.emit()
            self._save_timer.start()

    @Slot(str, result=bool)
    def resumeDraft(self, draft_id):
        if self._busy or not self.saveDraft(): return False
        try: saved = self._load_saved()
        except (OSError, ValueError): return False
        draft = next((d for d in saved if d['id'] == draft_id), None)
        if draft is None: return False
        self.reset()
        self._restore(draft)
        self._selection_changed()
        self.attachmentsChanged.emit()
        self.changed.emit(); self.draftChanged.emit()
        return True

    def _restore(self, draft):
        self._draft_id = draft['id']
        self._subject, self._body = draft['subject'], draft['body']
        self._mode = draft['mode']; self._source_id = draft.get('sourceId', '')
        self._source_folder = draft.get('sourceFolder', 'inbox')
        self._selected_many = deepcopy(draft['recipients'])
        for recipient in self._selected_many: recipient['identity'] = tuple(recipient['identity'])
        self._selected = self._selected_many[-1] if self._selected_many else None
        self._attachments = deepcopy(draft['attachments'])
        self._delivery_state = draft['deliveryState']; self._snapshot = draft['attemptSnapshot']
        self._locked = self._delivery_state != 'editing'
        if self._locked: self._status = 'This draft has a previous send attempt. Check Sent in Smartschool before starting another message.'

    @Slot(str, 'QVariantMap', result=bool)
    @Slot(str, 'QVariantMap', str, result=bool)
    def prepareReply(self, mode, detail, bodyOverride=''):
        if mode not in ('reply', 'replyAll', 'forward') or self._busy or not self.saveDraft(): return False
        if mode != 'forward' and not detail.get('canReply', True):
            self._error = 'This school message does not allow replies.'
            self.changed.emit(); return False
        self.reset()
        content, self._hints = _reply_content(mode, detail, bodyOverride)
        self._mode = mode
        self._subject, self._body = content['subject'], content['body']
        self._source_id, self._source_folder = content['sourceId'], content['sourceFolder']
        # Display names from message details are hints, never trusted recipient identities.
        self._status = ('Choose the school recipients explicitly before sending. ' if mode != 'forward' else 'Choose who should receive this forwarded message. ')
        if detail.get('attachments'): self._status += 'Original attachments are not automatically forwarded; attach any local copies you want to include.'
        self.changed.emit(); self.draftChanged.emit()
        return True

    @Slot('QVariantMap', str, result=bool)
    def saveReplyAsDraft(self, detail, body):
        if self._account != self.owner.accountKey or not detail.get('canReply', True): return False
        content, _ = _reply_content('reply', detail, body)
        draft = dict(content, id=uuid.uuid4().hex, mode='reply', recipients=[], attachments=[],
                     deliveryState='editing', attemptSnapshot={})
        try:
            self._persist(draft, self._account)
            self._saved = self._load_saved()
        except (OSError, ValueError):
            self._error = 'The generated reply could not be saved. Your current draft was kept.'
            self.changed.emit(); return False
        self.savedDraftsChanged.emit()
        return True

    @Property(str, notify=changed)
    def accountKey(self): return self.owner.accountKey
    @Property(bool, notify=changed)
    def busy(self): return self._busy
    @Property(bool, notify=changed)
    def searching(self): return self._busy and self._operation == 'compose_search'
    @Property(bool, notify=changed)
    def sending(self): return self._busy and self._operation == 'compose_send'
    @Property(bool, notify=changed)
    def deliveryLocked(self): return self._locked
    @Property(str, notify=changed)
    def error(self): return self._error
    @Property(str, notify=changed)
    def status(self): return self._status
    @Property(str, notify=changed)
    def recipient(self): return ', '.join(r['name'] for r in self._selected_many)
    @Property(bool, notify=changed)
    def recipientIsGroup(self): return bool(self._selected and self._selected['identity'][0] == 'group')
    @Property('QVariantList', notify=recipientsChanged)
    def recipients(self):
        return self._rows

    def _set_choices(self, choices):
        self._choices = choices
        rows = [dict(index=index, name=choice['name'], detail=choice['detail'])
                for index, choice in enumerate(choices)]
        if rows != self._rows:
            self._rows = rows
            self.recipientsChanged.emit()

    def _start(self, kind, action, local=False):
        revision = self._revision
        account_snapshot = self._account
        query_serial = self._query_serial if kind == 'compose_search' else None
        self._operation = kind
        self._busy, self._error, self._status = True, '', ''
        self.changed.emit()
        def run(credentials, account):
            def current():
                return (revision == self._revision and account == account_snapshot == self.owner.accountKey
                        and account == self.owner.backend.account()
                        and (query_serial is None or query_serial == self._query_serial))
            if not current(): raise ValueError('Account changed')
            result = action(None, current) if local else self.owner._session(credentials, lambda session: action(session, current))
            return dict(revision=revision, data=result)
        if not self.owner._start(kind, run):
            self._busy, self._locked = False, False
            self._operation = ''
            self._error = 'Wait for the current school request or sync this account, then retry.'
            self.changed.emit()

    @Slot(str)
    def updateRecipientQuery(self, query):
        if self.sending or self._locked: return
        self._query_serial += 1
        self._query, self._queued_query = query.strip(), None
        self._set_choices([])
        self._selected = None
        self._error, self._status = '', ''
        self._lookup_timer.stop()
        if 2 <= len(self._query) <= 100:self._lookup_timer.start()
        self.changed.emit()

    @Slot()
    def _dispatch_lookup(self):
        if not self._locked and not self.sending and 2 <= len(self._query) <= 100:
            self._queued_query = self._query
            if self.owner.featureBusy and not self._busy:
                self._status = 'Waiting for the current school request before finding people…'
                self.changed.emit()
            self._resume_lookup()

    @Slot()
    def _resume_lookup(self):
        if self._account != self.owner.accountKey:
            self.reset()
            return
        if not self._queued_query or self._busy or self._locked or self.owner.featureBusy:return
        query, self._queued_query = self._queued_query, None
        if query != self._query:return
        self._active_query_serial = self._query_serial
        coaccounts = self._recipient_mode == 'coaccounts'
        self._start('compose_search', lambda session, current: _search(session, query, True) if coaccounts else _search(session, query))

    @Slot(str)
    def searchRecipients(self, query):
        if self.sending or self._locked:return
        query = query.strip()
        if query != self._query:self.updateRecipientQuery(query)
        self._lookup_timer.stop()
        if not 2 <= len(query) <= 100:
            self._error = 'Enter between 2 and 100 characters to find a recipient.'
            self.changed.emit(); return
        if self.searching and self._active_query_serial == self._query_serial:return
        self._dispatch_lookup()

    @Slot(int)
    def selectRecipient(self, index):
        if self._busy or self._locked or not 0 <= index < len(self._choices): return
        self._selected = dict(self._choices[index])
        self._selected['field'] = self._field
        if not any(tuple(r['identity']) == tuple(self._selected['identity']) for r in self._selected_many):
            if len(self._selected_many) >= 100:
                self._error = 'A message can have up to 100 selected recipients.'
                self.changed.emit(); return
            self._selected_many.append(self._selected)
            self._selection_changed()
        self._lookup_timer.stop()
        self._queued_query = None
        self._error = ''
        self.changed.emit()
        self._save_timer.start()

    @Slot()
    def clearRecipient(self):
        if self.sending or self._locked: return
        self._selected_many = []
        self._selection_changed()
        self.updateRecipientQuery('')

    @Slot(str, str)
    def send(self, subject, body):
        if self._busy or self._locked: return
        if self.owner.featureBusy:
            self._error = 'Wait for the current school request to finish, then retry.'
            self.changed.emit(); return
        subject, body = subject.strip(), body.replace('\r\n', '\n').replace('\r', '\n')
        if not any(r.get('field', 'To') == 'To' for r in self._selected_many) or not 1 <= len(subject) <= 250 or not body.strip() or len(body) > 100_000:
            self._error = 'Choose a recipient, enter a subject (up to 250 characters) and a message (up to 100,000 characters).'
            self.changed.emit(); return
        self._subject, self._body = subject, body
        if not self.saveDraft(): return
        selected = deepcopy(self._selected_many)
        draft, account = self._draft(), self._account
        snapshot = dict(subject=subject, body=body, recipients=deepcopy(draft['recipients']),
                        attachments=deepcopy(self._attachments))
        self._snapshot = snapshot
        draft.update(deliveryState='locked', attemptSnapshot=snapshot)
        attempt = self._attempt = dict(started=False, persisted=False, attachments=deepcopy(self._attachments))
        def persist_lock():
            self._persist(draft, account)
            attempt['persisted'] = True
        attempt['persist_lock'] = persist_lock
        self._locked = True
        self._start('compose_send', lambda session, current: _send(session, selected, subject, body, current, attempt))

    @Slot(result=bool)
    def newDraft(self):
        if self._busy or not self.saveDraft(): return False
        self.reset()
        return True

    def receive(self, kind, result, failure):
        if not self._busy: return
        if kind == 'compose_search' and self._active_query_serial != self._query_serial:
            self._busy, self._operation = False, ''
            self.changed.emit()
            self._resume_lookup()
            return
        if failure is not None:
            self._busy = False
            self._locked = kind == 'compose_send' and self._attempt['started']
            self._error = ('Delivery could not be confirmed. Check Sent in Smartschool before starting another message. Your draft was kept.'
                           if self._locked else 'Message was not sent. Check your connection and selected recipient, then retry. Your draft was kept.'
                           if kind == 'compose_send' else 'Files could not be attached. Choose readable local files, at most 20 files and 50 MB together.'
                           if kind == 'compose_attach' else 'Suggestions could not be loaded. Check your connection, then keep typing or press Enter to retry.')
        elif (result.get('account') == self.owner.accountKey == self.owner.backend.account()
              and result.get('generation') == self.owner._generation
              and result.get('value', {}).get('revision') == self._revision):
            self._busy = False
            value = result['value']['data']
            if kind == 'compose_search':
                if isinstance(value, dict):
                    self._coaccounts_available = value['coaccountsAvailable']
                    value = value['choices']
                    if self._recipient_mode == 'coaccounts' and self._coaccounts_available is False:
                        self._recipient_mode = 'main'
                        self._error = 'Your school account does not allow messaging co-accounts. Choose a main account instead.'
                self._set_choices(value)
                self._status = '' if value else 'No matching people or groups found. Try another name.'
            elif kind == 'compose_attach':
                self._attachments.extend(value)
                self.attachmentsChanged.emit()
                self._save_timer.start()
            elif kind == 'compose_send':
                self._locked = True
                self._status = ('Send request accepted. Check Sent in Smartschool before sending this again.' if value == 'accepted'
                                else 'Delivery could not be confirmed. Check Sent in Smartschool before starting another message. Your draft was kept.')
        else:
            self._busy = False
            self._locked = kind == 'compose_send' and self._attempt['started']
            self._error = ('Delivery could not be confirmed. Check Sent in Smartschool before starting another message.'
                           if self._locked else 'This request expired. Your draft was kept; retry when ready.')
        self._operation = ''
        if kind == 'compose_send':
            if self._attempt.get('persisted'):
                self._delivery_state = ('accepted' if not failure and not self._error and self._status.startswith('Send request accepted') else 'unknown')
            elif self._attempt.get('started'):
                self._delivery_state = 'unknown'
            else:
                self._delivery_state, self._snapshot = 'editing', {}
            self._locked = self._delivery_state != 'editing'
            # A failure to update the outcome leaves the durable pre-send lock intact.
            self.saveDraft()
        self.changed.emit()
        self._resume_lookup()
