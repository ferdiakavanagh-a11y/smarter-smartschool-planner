"""Atomic account-local drafts, including durable locks for uncertain sends."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import uuid

import task_state
from process_lock import file_lock
from .feature_state import directory

MAX_DRAFTS = 200
MAX_STORAGE_BYTES = 25 * 1024 * 1024
MAX_ATTACHMENT_BYTES = 50 * 1024 * 1024
_FIELDS = {'id', 'subject', 'body', 'mode', 'sourceId', 'sourceFolder', 'recipients',
           'attachments', 'updatedAt', 'deliveryState', 'attemptSnapshot'}


def _path(root, account):
    folder = directory(root, account)
    path = folder/'drafts.json'
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise ValueError('Linked draft storage is not supported.')
    return path


def _text(value, maximum):
    if not isinstance(value, str) or len(value) > maximum or '\x00' in value:
        raise ValueError('Invalid message draft text.')
    return value


def _validate(draft):
    if not isinstance(draft, dict) or set(draft) != _FIELDS:
        raise ValueError('Invalid message draft fields.')
    if not re.fullmatch('[0-9a-f]{32}', _text(draft['id'], 32)):
        raise ValueError('Invalid message draft identifier.')
    _text(draft['subject'], 300)
    _text(draft['body'], 100_000)
    if draft['mode'] not in ('new', 'reply', 'replyAll', 'forward'):
        raise ValueError('Invalid message draft mode.')
    if draft['sourceId'] and not re.fullmatch('[0-9]{1,20}', _text(draft['sourceId'], 20)):
        raise ValueError('Invalid draft source message.')
    _text(draft['sourceId'], 20)
    if draft['sourceFolder'] not in ('inbox', 'sent', 'outbox', 'trash', 'draft', 'scheduled'):
        raise ValueError('Invalid draft source folder.')
    if (not isinstance(draft['updatedAt'], str) or len(draft['updatedAt']) > 40 or
            datetime.fromisoformat(draft['updatedAt']).tzinfo is None):
        raise ValueError('Invalid message draft date.')
    recipients = draft['recipients']
    if not isinstance(recipients, list) or len(recipients) > 100:
        raise ValueError('Too many draft recipients.')
    seen = set()
    for recipient in recipients:
        if not isinstance(recipient, dict) or set(recipient) != {'kind', 'identity', 'query', 'name', 'field'}:
            raise ValueError('Invalid draft recipient.')
        identity = recipient['identity']
        if not isinstance(identity, (list, tuple)) or len(identity) != 3:
            raise ValueError('Invalid draft recipient identity.')
        if recipient['kind'] == 'group':
            valid = identity[0] == 'group' and type(identity[1]) is int and identity[1] > 0 and type(identity[2]) is int and identity[2] >= 0
        else:
            valid = (recipient['kind'] == 'user' and all(type(v) is int for v in identity)
                     and identity[0] > 0 and identity[1] >= 0 and identity[2] >= 0)
        if not valid or recipient['field'] not in ('To', 'Cc', 'Bcc'):
            raise ValueError('Invalid draft recipient identity or field.')
        if tuple(identity) in seen:
            raise ValueError('A recipient appears more than once.')
        seen.add(tuple(identity))
        _text(recipient['name'], 300)
        if not 2 <= len(_text(recipient['query'], 100).strip()) <= 100:
            raise ValueError('Invalid saved recipient search.')
    attachments = draft['attachments']
    if not isinstance(attachments, list) or len(attachments) > 20:
        raise ValueError('Too many draft attachments.')
    for attachment in attachments:
        if not isinstance(attachment, dict) or set(attachment) != {'path', 'name', 'bytes', 'sha256'}:
            raise ValueError('Invalid draft attachment.')
        path = Path(_text(attachment['path'], 32767))
        name = _text(attachment['name'], 255)
        if not path.is_absolute() or str(path).startswith(('\\\\', '//')) or path.name != name:
            raise ValueError('Invalid draft attachment path.')
        if type(attachment['bytes']) is not int or not 0 <= attachment['bytes'] <= MAX_ATTACHMENT_BYTES:
            raise ValueError('Invalid draft attachment size.')
        if not re.fullmatch('[0-9a-f]{64}', _text(attachment['sha256'], 64)):
            raise ValueError('Invalid draft attachment digest.')
    if sum(item['bytes'] for item in attachments) > MAX_ATTACHMENT_BYTES:
        raise ValueError('Draft attachments exceed 50 MB.')
    if draft['deliveryState'] not in ('editing', 'locked', 'accepted', 'unknown'):
        raise ValueError('Invalid draft delivery state.')
    if not isinstance(draft['attemptSnapshot'], dict):
        raise ValueError('Invalid saved send attempt.')
    if draft['deliveryState'] != 'editing' and not draft['attemptSnapshot']:
        raise ValueError('A locked draft requires its send snapshot.')
    if len(json.dumps(draft, ensure_ascii=False, allow_nan=False).encode('utf-8')) > 1024 * 1024:
        raise ValueError('Message draft is too large.')


def load(root, account):
    path = _path(root, account)
    if path.exists() and path.stat().st_size > MAX_STORAGE_BYTES:
        raise ValueError('Draft storage is too large. Existing drafts were kept.')
    data = task_state._load_json(path, dict, True)
    if not data:
        return []
    if set(data) != {'version', 'drafts'} or data['version'] != 1 or not isinstance(data['drafts'], list) or len(data['drafts']) > MAX_DRAFTS:
        raise ValueError('Invalid saved drafts. Existing drafts were kept.')
    identities = set()
    for draft in data['drafts']:
        _validate(draft)
        if draft['id'] in identities:
            raise ValueError('Duplicate saved draft identifiers.')
        identities.add(draft['id'])
    return sorted(data['drafts'], key=lambda item: item['updatedAt'], reverse=True)


def _write(path, drafts):
    data = {'version': 1, 'drafts': drafts}
    if len(json.dumps(data, ensure_ascii=False).encode('utf-8')) > MAX_STORAGE_BYTES:
        raise ValueError('Draft storage is full. Remove an old draft first. Existing drafts were kept.')
    task_state._atomic_json(path, data)


def save(root, account, draft):
    path = _path(root, account)
    try:
        value = json.loads(json.dumps(draft, ensure_ascii=False, allow_nan=False))
    except (TypeError, ValueError):
        raise ValueError('Invalid message draft data.') from None
    if not isinstance(value, dict) or set(value) - _FIELDS:
        raise ValueError('Invalid message draft fields.')
    value.setdefault('id', uuid.uuid4().hex)
    for key, default in dict(subject='', body='', mode='new', sourceId='', sourceFolder='inbox',
                             recipients=[], attachments=[], deliveryState='editing', attemptSnapshot={}).items():
        value.setdefault(key, default)
    value['updatedAt'] = datetime.now(timezone.utc).isoformat()
    _validate(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with file_lock(Path(root)/'data'/'.state.lock'):
        drafts = load(root, account)
        previous = next((item for item in drafts if item['id'] == value['id']), None)
        if previous and previous['deliveryState'] != 'editing':
            allowed = (previous['deliveryState'] == 'locked' and value['deliveryState'] in ('accepted', 'unknown')) or value['deliveryState'] == previous['deliveryState']
            immutable = _FIELDS - {'updatedAt', 'deliveryState'}
            if not allowed or any(value[key] != previous[key] for key in immutable):
                raise ValueError('This send attempt is locked. Save a new draft to compose again.')
        elif value['deliveryState'] in ('accepted', 'unknown'):
            raise ValueError('A send result requires an existing locked draft.')
        if not previous and len(drafts) >= MAX_DRAFTS:
            raise ValueError('Draft storage is full. Remove an old draft first.')
        _write(path, [value]+[item for item in drafts if item['id'] != value['id']])
    return value['id']


def delete(root, account, draft_id):
    if not isinstance(draft_id, str) or not re.fullmatch('[0-9a-f]{32}', draft_id):
        raise ValueError('Invalid draft identifier.')
    path = _path(root, account)
    path.parent.mkdir(parents=True, exist_ok=True)
    with file_lock(Path(root)/'data'/'.state.lock'):
        drafts = load(root, account)
        _write(path, [item for item in drafts if item['id'] != draft_id])
