"""Translate the existing snapshot and persist edits before updating the view."""
from datetime import date
import re
from PySide6.QtCore import Signal, Slot
import task_state
from planner_details import html_to_text
from .model import Tasks


def text(value):
    return html_to_text(str(value or ''))


def fields_text(pairs):
    if isinstance(pairs, dict):
        pairs = pairs.items()
    return '\n'.join(f'{text(k)}: {text(v)}' for k, v in pairs or [] if v not in (None, ''))


def written_date(value, full=False):
    try:
        day = date.fromisoformat(str(value)[:10])
        return f"{day.strftime('%A' if full else '%a')} {day.day} {day.strftime('%B' if full else '%b')}"
    except ValueError:
        return text(value)


def task_indicators(item):
    indicators = []
    for key, label in [('due_date_corrected', 'Corrected date'), ('warning', 'Check assignment'), ('detail_stale', 'Saved instructions · sync to refresh')]:
        if item.get(key):
            indicators.append(dict(icon={'due_date_corrected':'cal','warning':'warn','detail_stale':'clock'}[key], label=label, tone='orange'))
    if item.get('due_date_source') in ('ai', 'gemini'):
        indicators.append(dict(icon='ai', label='AI date — verify', tone='purple'))
    return indicators


def planner_url(data, item, posted):
    host = str(data.get('main_url') or '').removeprefix('https://').removeprefix('http://').rstrip('/')
    if not host:
        return ''
    generic = 'https://'+host+'/planner'
    platform, user = str(data.get('platform_id') or ''), str(data.get('user_id') or '')
    moment = str(item.get('moment_id') or '')
    if not (re.fullmatch(r'\d+', platform) and re.fullmatch(r'\d+(?:_\d+_\d+)?', user) and
            re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', moment) and
            (item.get('element_source') or item.get('source')) == 'planner_api'):
        return generic
    try:
        date.fromisoformat(str(posted))
    except ValueError:
        return generic
    user = user if '_' in user else f'{platform}_{user}_0'
    kind = str(item.get('element_type') or '')
    kind = kind if re.fullmatch(r'planned-[a-z-]+', kind) else 'planned-assignments'
    return f'{generic}/main/user/{user}/{posted}/{kind}/{platform}/{moment}'


class PlannerTasks(Tasks):
    failed = Signal(str)

    def __init__(self, root, verify_account):
        self.root, self.verify_account = root, verify_account
        super().__init__(0, today=date.today())

    def replace(self, snapshot):
        completed = task_state.load_completed_ids(self.root)
        pinned = task_state.load_pinned_ids(self.root)
        notes = task_state.load_notes(self.root)
        rows = []
        for item in snapshot.get('todos', []):
            task_id = str(item.get('id') or '')
            if not task_id:
                continue
            due = str(item.get('due_date') or item.get('posted_date') or '')[:10]
            try:
                date.fromisoformat(due)
            except ValueError:
                continue
            rows.append(dict(taskId=task_id, title=text(item.get('description')), course=text(item.get('course')),
                             kind=text(item.get('type')) or 'Task', due=due, posted=str(item.get('posted_date') or due)[:10],
                             body=text(item.get('body')), done=task_id in completed, pinned=task_id in pinned,
                             note=notes.get(task_id, ''), indicators=task_indicators(item)))
        self.all = rows
        self.today = date.today()
        self.undo_change = None
        self.choicesChanged.emit()
        self.filter(*self.filters)

    @Slot(str, str, 'QVariant', result=bool)
    def change(self, task_id, field, value):
        if field not in ('done', 'pinned', 'note') or not any(t['taskId'] == task_id for t in self.all):
            return False
        if (field == 'note' and (not isinstance(value, str) or len(value) > 5000)) or (field != 'note' and not isinstance(value, bool)):
            return False
        try:
            self.verify_account()
            writer = {'done': task_state.set_task_done, 'pinned': task_state.set_task_pinned, 'note': task_state.set_note}[field]
            writer(self.root, task_id, value)
        except Exception:
            self.failed.emit('Could not save your change. The original data and your draft were kept. Check your login and disk access, then try again.')
            return False
        return super().change(task_id, field, value)

    @Slot(str, result=str)
    def taskNote(self, task_id):
        return next((t['note'] for t in self.all if t['taskId'] == task_id), '')
