"""Memory-only prototype state. Does not import production services or storage."""
import time
import re
from datetime import date
from collections import Counter
from difflib import SequenceMatcher
from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Slot, Signal, Property, QObject, QTimer
TEST_KIND = re.compile(r'toets|evaluatie|test|examen|proef', re.I)
try:
    from .fixtures import make_tasks
except ImportError:
    from fixtures import make_tasks


class Tasks(QAbstractListModel):
    countChanged = Signal()
    choicesChanged = Signal()
    fields = ('taskId', 'title', 'course', 'kind', 'due', 'done', 'pinned', 'note', 'group', 'first', 'last', 'body', 'posted', 'indicators')

    def __init__(self, count=36, today=None):
        super().__init__()
        self.today = today or date(2026,10,24)
        self.all = make_tasks(count)
        self.rows = self.all[:]
        self.filters = ('', 'All courses', 'All types', False)
        self.section = 0
        self.completed_open = False
        self.undo_change = None
        self._feedback_task_id = None
        self.filter(*self.filters)

    def roleNames(self):
        return {Qt.UserRole + i: name.encode() for i, name in enumerate(self.fields)}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def data(self, index, role):
        field = role - Qt.UserRole
        if index.isValid() and 0 <= index.row() < len(self.rows) and 0 <= field < len(self.fields):
            key = self.fields[field]
            row = index.row()
            if key == 'first':
                return row == 0 or self.rows[row-1]['group'] != self.rows[row]['group']
            if key == 'last':
                return row == len(self.rows)-1 or self.rows[row+1]['group'] != self.rows[row]['group']
            return self.rows[row].get(key, [] if key == 'indicators' else '')

    @Property(int, notify=countChanged)
    def count(self):
        return len(self.rows)

    @Property(int, notify=countChanged)
    def completedCount(self):
        return sum(t['done'] for t in self.all)

    @Property('QStringList', notify=countChanged)
    def completedIds(self):
        return [t['taskId'] for t in self.all if t['done']]

    @Property(int, notify=countChanged)
    def missedCount(self):
        return sum(not t['done'] and -7 <= (date.fromisoformat(t['due'])-self.today).days < 0 for t in self.all)

    @Property('QVariantList', notify=countChanged)
    def week(self):
        from datetime import timedelta
        days = [dict(label='Today' if i == 0 else (self.today+timedelta(days=i)).strftime('%a'), count=0, score=0, kinds=Counter()) for i in range(7)]
        for task in self.all:
            offset = (date.fromisoformat(task['due'])-self.today).days
            if not task['done'] and 0 <= offset < 7:
                day = days[offset]
                day['count'] += 1
                day['score'] += 3 if TEST_KIND.search(task['kind']) else 1
                day['kinds'][task['kind']] += 1
        peak = max(1, max(day['score'] for day in days))
        for i, day in enumerate(days):
            kinds = day.pop('kinds')
            leaders = [kind for kind, count in kinds.items() if count == max(kinds.values())]
            # Equal category counts rotate deterministically; otherwise show the dominant category.
            day['kind'] = leaders[i % len(leaders)] if leaders else ''
            day['test'] = bool(TEST_KIND.search(day['kind']))
            day['barHeight'] = max(4, 52 * day['score'] / peak)
        return days

    @Property(str, notify=countChanged)
    def weekSummary(self):
        days = self.week
        total = sum(day['count'] for day in days)
        if not total:
            return 'No tasks are due in the next 7 days. Your week is clear.'
        tests = sum(not t['done'] and bool(TEST_KIND.search(t['kind'])) and 0 <= (date.fromisoformat(t['due'])-self.today).days < 7 for t in self.all)
        busiest = max(days, key=lambda day: day['score'])
        return (f"{total} {'task is' if total == 1 else 'tasks are'} due in the next 7 days, including "
                f"{tests} {'test or evaluation' if tests == 1 else 'tests or evaluations'}. "
                f"Busiest day: {busiest['label']} ({busiest['count']} {'item' if busiest['count'] == 1 else 'items'}).")

    @Property('QStringList', notify=choicesChanged)
    def courses(self):
        return ['All courses'] + list(dict.fromkeys(t['course'] for t in self.all))

    @Property('QStringList', notify=choicesChanged)
    def kinds(self):
        return ['All types'] + list(dict.fromkeys(t['kind'] for t in self.all))

    @Property('QVariantMap', notify=countChanged)
    def groupCounts(self):
        return dict(Counter(t['group'] for t in self.rows if not t['done'] or t['group']=='Completed'))

    @Slot(result=int)
    def todayIndex(self):
        active = [(i, task) for i, task in enumerate(self.rows) if not task['done']]
        today = self.today.isoformat()
        exact = next((i for i, task in active if task['group'] == 'Today'), None)
        if exact is not None:
            return exact
        future = [(task['due'], i) for i, task in active if task['due'] >= today]
        return min(future)[1] if future else active[-1][0] if active else -1

    @Slot(int)
    def setSection(self, section):
        self.section = section
        self.filter(*self.filters)

    @Slot(bool)
    def expandCompleted(self, value):
        self.completed_open = value
        self.filter(*self.filters)

    @Slot(str, str, str, bool)
    def filter(self, query, course, kind, pins):
        self.filters = query, course, kind, pins
        query = query.casefold().strip()
        rows = [t for t in self.all if
                     (not query or query in ' '.join(t.get(k, '') for k in ('title', 'course', 'note', 'body', 'kind')).casefold())
                     and (course == 'All courses' or t['course'] == course)
                     and (kind == 'All types' or t['kind'] == kind)
                     and (not pins or t['pinned'])]
        for t in rows:
            days = (date.fromisoformat(t['due'])-self.today).days
            t['group'] = 'Completed' if t['done'] else 'Pinned' if t['pinned'] else 'Last 7 days' if days < 0 else 'Today' if days == 0 else 'Tomorrow' if days == 1 else 'This week' if days < 7 else 'Later'
        if self.section == 1:
            rows = [t for t in rows if not t['done'] and -7 <= (date.fromisoformat(t['due'])-self.today).days < 0]
        else:
            rows = [t for t in rows if t['group'] != 'Last 7 days' and (not t['done'] or self.completed_open or query)]
        order = ['Pinned','Last 7 days','Today','Tomorrow','This week','Later','Completed']
        rows.sort(key=lambda t:(order.index(t['group']),t['due'],t['taskId']))
        # Preserve Qt's visible delegates and scroll anchor when local edits change the list.
        old_ids = [t['taskId'] for t in self.rows]
        new_ids = [t['taskId'] for t in rows]
        kept = {index for block in SequenceMatcher(None, old_ids, new_ids, autojunk=False).get_matching_blocks()
                for index in range(block.a, block.a+block.size)}
        for index in range(len(self.rows)-1, -1, -1):
            if index not in kept:
                self.beginRemoveRows(QModelIndex(), index, index)
                del self.rows[index]
                self.endRemoveRows()
        for index, task in enumerate(rows):
            if index >= len(self.rows) or self.rows[index]['taskId'] != task['taskId']:
                self.beginInsertRows(QModelIndex(), index, index)
                self.rows.insert(index, task)
                self.endInsertRows()
            self.rows[index] = task
        if self.rows:
            self.dataChanged.emit(self.index(0), self.index(len(self.rows)-1), [])
        self.countChanged.emit()

    @Slot(int)
    def dataset(self, count):
        self.all = make_tasks(count)
        self.undo_change = None
        self.choicesChanged.emit()
        self.filter(*self.filters)

    @Slot(str, str, 'QVariant', result=bool)
    def change(self, task_id, field, value):
        if field not in ('done', 'pinned', 'note'):
            return False
        if field == 'note' and (not isinstance(value, str) or len(value) > 5000):
            return False
        if field != 'note' and not isinstance(value, bool):
            return False
        task = next((t for t in self.all if t['taskId'] == task_id), None)
        if task is None:
            return False
        if task[field] == value:
            return True
        self.undo_change = task_id, field, task[field]
        task[field] = value
        hides_done = self.section == 1 or not (self.completed_open or self.filters[0].strip())
        if field == 'done' and value and hides_done and task in self.rows:
            row = self.rows.index(task)
            self.dataChanged.emit(self.index(row), self.index(row), [Qt.UserRole+self.fields.index('done')])
            if self._feedback_task_id == task_id:
                self.countChanged.emit()
            else:
                self._retire_completed(task_id)
        else:
            self.filter(*self.filters)
        return True

    @Slot(str, result=bool)
    def complete(self, task_id):
        self._feedback_task_id = task_id
        try:
            saved = self.change(task_id, 'done', True)
        finally:
            self._feedback_task_id = None
        if saved:
            # Retire only the presentation row; the state is already saved.
            QTimer.singleShot(600, self, lambda: self._retire_completed(task_id))
        return saved

    def _retire_completed(self, task_id):
        task = next((t for t in self.rows if t['taskId'] == task_id and t['done']), None)
        if task is None or (self.section != 1 and (self.completed_open or self.filters[0].strip())):
            return
        row = self.rows.index(task)
        self.beginRemoveRows(QModelIndex(), row, row)
        del self.rows[row]
        self.endRemoveRows()
        if self.rows:
            self.dataChanged.emit(self.index(max(0,row-1)), self.index(min(row,len(self.rows)-1)),
                                  [Qt.UserRole+self.fields.index(key) for key in ('first','last')])
        self.countChanged.emit()

    @Slot(result=bool)
    def undo(self):
        if self.undo_change is None:
            return False
        task_id,field,value = self.undo_change
        result = self.change(task_id,field,value)
        if result:
            self.undo_change = None
        return result


class Stopwatch(QObject):
    changed = Signal()

    def __init__(self, clock=time.monotonic):
        super().__init__()
        self.clock = clock
        self.started = None
        self.accumulated = 0

    @Property(bool, notify=changed)
    def running(self):
        return self.started is not None

    @Slot(result=float)
    def seconds(self):
        return self.accumulated + (self.clock() - self.started if self.running else 0)

    @Slot()
    def toggle(self):
        if self.running:
            self.accumulated = self.seconds()
            self.started = None
        else:
            self.started = self.clock()
        self.changed.emit()

    @Slot()
    def reset(self):
        self.accumulated = 0
        self.started = None
        self.changed.emit()
