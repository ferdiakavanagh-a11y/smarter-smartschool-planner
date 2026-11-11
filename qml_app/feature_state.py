"""Account-scoped local tasks and optional school-feature cache."""
import hashlib
import re
from datetime import date
from pathlib import Path
import task_state


def directory(root, account):
    if not isinstance(account, str) or not account:
        raise ValueError('An authenticated account is required.')
    return Path(root)/'data'/'school'/hashlib.sha256(account.encode()).hexdigest()


def load(root, account):
    data = task_state._load_json(directory(root, account)/'state.json', dict, True)
    _validate(data)
    return data


def _validate(data):
    def records(value):
        if not isinstance(value, list) or not all(isinstance(x, dict) for x in value):
            raise ValueError('Invalid school records.')
        return value

    def strings(record, fields, required=()):
        if (any(key in record and not isinstance(record[key], str) for key in fields) or
                any(not isinstance(record.get(key), str) or not record[key] for key in required)):
            raise ValueError('Invalid school record fields.')

    for key in ('messages', 'downloads', 'tasks'):
        records(data.get(key, []))
    for key in ('details', 'resources'):
        if key in data and not isinstance(data[key], dict):
            raise ValueError('School cache is invalid; existing data was kept.')
    for message in data.get('messages', []):
        strings(message, ('id', 'sender', 'subject', 'date', 'preview'), ('id',))
    folders=data.get('messageFolders',{})
    if not isinstance(folders,dict) or any(folder not in ('outbox','trash','scheduled','draft') for folder in folders):
        raise ValueError('Invalid message folders.')
    for messages in folders.values():
        for message in records(messages):strings(message,('id','sender','subject','date','preview'),('id',))
    for action in records(data.get('messageActions',[])):
        if action.get('folder') not in ('inbox','outbox') or not re.fullmatch('[0-9]{1,20}',str(action.get('id',''))):
            raise ValueError('Invalid pending message action.')
    for identity, message in data.get('details', {}).items():
        if not isinstance(message, dict) or message.get('id') != identity:
            raise ValueError('Invalid cached message.')
        strings(message, ('id', 'sender', 'subject', 'date', 'body'), ('id',))
        for field in ('to','cc','bcc'):
            if field in message and (not isinstance(message[field],list) or len(message[field])>100 or not all(isinstance(name,str) for name in message[field])):
                raise ValueError('Invalid message recipients.')
        for attachment in records(message.get('attachments', [])):
            strings(attachment, ('id', 'messageId', 'name', 'kind', 'size', 'mime'), ('id', 'name'))
    resources = data.get('resources', {})
    for key in ('reports', 'periods', 'courses', 'support', 'homepage'):
        for record in records(resources.get(key, [])):
            strings(record, ('id', 'name', 'title', 'date', 'schoolYear', 'className', 'description', 'url', 'label'))
            if 'teachers' in record and (not isinstance(record['teachers'], list) or not all(isinstance(t, str) for t in record['teachers'])):
                raise ValueError('Invalid teacher list.')
    errors = resources.get('errors', {})
    if not isinstance(errors, dict) or not all(isinstance(v, str) for v in errors.values()):
        raise ValueError('Invalid school errors.')
    for record in data.get('downloads', []):
        strings(record, ('key', 'file', 'name', 'source', 'sourceId', 'sha256', 'etag', 'lastModified', 'resourceKey'), ('key', 'file', 'name'))
        if Path(record['file']).name != record['file'] or record['file'] in ('.', '..'):
            raise ValueError('Invalid downloaded file.')
        for key in ('sha256', 'resourceKey'):
            if key in record and not re.fullmatch(r'[0-9a-f]{64}', record[key]):
                raise ValueError('Invalid downloaded file digest.')
        for key in ('etag', 'lastModified'):
            if key in record and (len(record[key]) > 1024 or any(ord(c) < 32 or ord(c) == 127 for c in record[key])):
                raise ValueError('Invalid downloaded file validator.')
    for task in data.get('tasks', []):
        strings(task, ('id', 'description', 'course', 'type', 'body', 'message_id', 'due_date', 'posted_date'),
                ('id', 'description', 'message_id', 'due_date', 'posted_date'))
        if not task['id'].startswith('local:'):
            raise ValueError('Invalid local task.')
        for key in ('due_date', 'posted_date'):
            if date.fromisoformat(task[key]).isoformat() != task[key]: raise ValueError('Invalid local task date.')


@task_state.state_write
def update(root, account, key, value):
    data = load(root, account)
    data[key] = value
    _validate(data)
    folder = directory(root, account)
    folder.mkdir(parents=True, exist_ok=True)
    task_state._atomic_json(folder/'state.json', data)
    return data


@task_state.state_write
def move_message_to_trash(root,account,identifier):
    data=load(root,account)
    folders=dict(data.get('messageFolders',{}))
    sources=[data.get('messages',[]),*folders.values()]
    header=next((dict(m) for rows in sources for m in rows if m.get('id')==identifier),None)
    data['messages']=[m for m in data.get('messages',[]) if m.get('id')!=identifier]
    folders={folder:[m for m in rows if m.get('id')!=identifier] for folder,rows in folders.items()}
    if header:
        header['folder']='trash'
        folders['trash']=[header,*folders.get('trash',[])][:2000]
    data['messageFolders']=folders
    data['messageActions']=[action for action in data.get('messageActions',[]) if action['id']!=identifier]
    if identifier in data.get('details',{}):
        detail=data['details'][identifier];detail['folder']='trash'
        for attachment in detail.get('attachments',[]):attachment['folder']='trash'
    _validate(data)
    folder=directory(root,account);folder.mkdir(parents=True,exist_ok=True)
    task_state._atomic_json(folder/'state.json',data)
    return data


def cached_path(root, account, record):
    folder = directory(root, account)/'downloads'
    if any(part.is_symlink() or (hasattr(part,'is_junction') and part.is_junction()) for part in (folder,*folder.parents)):
        raise ValueError('Linked download directories are not supported.')
    folder = folder.resolve()
    name = record.get('file', '')
    if not isinstance(name, str) or Path(name).name != name or not name:
        raise ValueError('Invalid downloaded file.')
    path = folder/name
    if path.is_symlink() or path.resolve().parent != folder:
        raise ValueError('Invalid downloaded file.')
    return path
