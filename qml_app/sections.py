"""Presentation rows for the unchanged sync snapshot format."""
from collections import defaultdict
from datetime import date
from functools import cache
import math
import re
from .production_model import text, fields_text, planner_url, written_date

GRADE_COLORS = dict(green='#34c759', red='#ff3b30', olive='#8a9a2b', yellow='#ffcc00', steel='#7d93a8', grass='#5fbf3f', orange='#ff9500', blue='#0a84ff', purple='#af52de', pink='#ff2d55', teal='#30b0c7', grey='#8e8e93', gray='#8e8e93')


def finite(value):
    try:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    except OverflowError:
        return False


def percentage(score, maximum):
    value = score/maximum*100 if maximum else None
    return value if finite(value) else None


def weighted_percentage(rows):
    points, possible = sum(row[1] for row in rows), sum(row[2] for row in rows)
    if finite(points) and finite(possible):
        return percentage(points, possible)
    # Normalize before summing so finite points cannot overflow their combined average.
    scale = max((max(abs(row[1]), row[2]) for row in rows), default=0)
    return percentage(sum(row[1]/scale for row in rows), sum(row[2]/scale for row in rows)) if scale else None


def percent_label(value):
    return f'{math.floor(value+.5)}%'


def grade_presentation(result):
    score, maximum, percent = result.get('score'), result.get('max'), result.get('percent')
    numeric = finite(score) and finite(maximum) and maximum > 0
    percent = percentage(score, maximum) if numeric else percent if finite(percent) else None
    color = str(result.get('color') or '').lower()
    square = GRADE_COLORS.get(color, color if re.fullmatch(r'#[0-9a-f]{3}(?:[0-9a-f]{3})?', color) else '')
    label = text(result.get('text') or result.get('label') or '—')
    if label.startswith('bullet_square_'):
        square = square or GRADE_COLORS.get(label.removeprefix('bullet_square_'), '')
        label = text(result.get('label'))
        if label.startswith('bullet_square_'):
            label = color
    number = lambda value: f'{value:.2f}'.rstrip('0').rstrip('.').replace('.', ',')
    extra = f'{number(score)} / {number(maximum)}' if numeric else percent_label(percent) if percent is not None else '' if square else label
    return dict(extra=extra, percentText=percent_label(percent) if numeric and percent is not None else '',
                tone='text' if percent is None else 'red' if percent < 50 else 'orange' if percent < 70 else 'green',
                square=square if percent is None else '', resultLabel=label or color or 'Result'), numeric


def row(key, title, meta='', body='', extra='', **values):
    return dict(id=str(key), title=text(title), meta=text(meta), body=text(body), extra=text(extra), links=[], assignments=[], **values)


def planner_days(data):
    days = {}
    for source in ('all_classes', 'days'):
        for day in data.get(source, []):
            events = days.setdefault(day.get('date', ''), {})
            for event in day.get('events', []):
                key = str(event.get('moment_id') or '') or tuple(str(event.get(k) or '') for k in ('start', 'end', 'course', 'classroom'))
                if key not in events:
                    events[key] = dict(event)
                    continue
                old = events[key]
                info = dict(old.get('info') or {})
                extra = event.get('info') or {}
                assignments = list(info.get('assignments') or [])
                for assignment in extra.get('assignments') or []:
                    if not any(a.get('id') == assignment.get('id') for a in assignments):
                        assignments.append(assignment)
                info.update({k:v for k,v in extra.items() if v and k != 'assignments'})
                info['assignments'] = assignments
                merged = dict(event)
                merged.update({k:v for k,v in old.items() if v or k not in merged})
                for field in ('attachments', 'weblinks'):
                    links = list(old.get(field) or [])
                    links.extend(link for link in event.get(field) or [] if link not in links)
                    merged[field] = links
                events[key] = dict(merged, info=info)
    return [dict(date=day, events=sorted(events.values(), key=lambda event:str(event.get('start') or ''))) for day,events in days.items()]


def groups(backend, section, query, course='All subjects'):
    cached_date = cache(written_date)
    def format_date(value, full=False):
        return cached_date(value, full) if isinstance(value, str) else written_date(value, full)
    data, query = backend.data, query.casefold().strip()
    matches = lambda item: not query or query in ' '.join(str(item.get(k) or '') for k in ('title', 'meta', 'body', 'extra')).casefold()
    output = []
    if section in (2, 3):
        tasks = {task['taskId']: task for task in backend.tasks.all}
        days = data.get('days', []) if section == 2 else planner_days(data)
        for day in sorted(days, key=lambda day: str(day.get('date') or '')):
            items = []
            for event in day.get('events', []):
                info = event.get('info') or {}
                assignments = info.get('assignments') or []
                body = '\n\n'.join(filter(None, [text(event.get('title')), text(event.get('note')), text(info.get('topic')), text(info.get('description')), text(info.get('materials')), '\n'.join(text(a.get('description')) for a in assignments)]))
                item = row(event.get('moment_id'), event.get('course'), ' · '.join(filter(None, [str(event.get('start') or '')+' – '+str(event.get('end') or ''), text(event.get('classroom')), text(event.get('teacher')), text(event.get('groups'))])), body,
                           '\n'.join(text(a.get('description')) for a in assignments), kind='lesson')
                item['assignments'] = []
                for assignment in assignments:
                    task_id = str(assignment.get('id') or '')
                    if not task_id:
                        continue
                    task = tasks.get(task_id, {})
                    due = task.get('due') or assignment.get('due_date') or ''
                    due_text = 'Today' if due == date.today().isoformat() else format_date(due)
                    item['assignments'].append(dict(id=task_id, title=task.get('title') or text(assignment.get('description')),
                                                    kind=task.get('kind') or text(assignment.get('type')), due=due_text,
                                                    done=task.get('done', False), editable=bool(task)))
                item['links'] = [dict(a,downloadable=bool(a.get('url'))) for a in event.get('attachments') or []]
                item['links'] += [dict(a,downloadable=False) for a in event.get('weblinks') or []]
                link = planner_url(data, event, day.get('date'))
                if link:
                    item['links'].append(dict(name='Open lesson in Smartschool', url=link))
                if event.get('detail_stale'):
                    item['extra'] += '\nSaved details · sync to refresh'
                if matches(item):
                    items.append(item)
            if items or not query:
                output.append(dict(date=str(day.get('date') or '')[:10], heading=format_date(day.get('date'), full=True), items=items or [row('', 'No lessons scheduled', kind='empty')]))
    elif section == 4:
        by_course = defaultdict(list)
        for result in data.get('results', []):
            period = getattr(getattr(backend, 'features', None), 'selectedPeriod', '')
            if period and text(result.get('period')) != period:
                continue
            if course != 'All subjects' and text(result.get('course')) != course:
                continue
            score, maximum = result.get('score'), result.get('max')
            presentation, numeric = grade_presentation(result)
            body = fields_text([(k, result.get(v)) for k, v in [('Course', 'course'), ('Date', 'date'), ('Teacher', 'teacher'), ('Period', 'period')]])+'\n\n'+presentation['extra']+'\n\n'+'\n\n'.join(text(v) for v in result.get('feedback') or [])
            meta = ' · '.join(filter(None, [format_date(result.get('date')), '' if result.get('counts') else 'Doesn’t count']))
            item = row(result.get('id'), result.get('name') or 'Evaluation', meta, body, kind='grade')
            item.update(presentation)
            if matches(item):
                by_course[text(result.get('course'))].append((item, score if numeric and result.get('counts') else 0, maximum if numeric and result.get('counts') else 0))
        total = sum(v[1] for rows in by_course.values() for v in rows)
        maximum = sum(v[2] for rows in by_course.values() for v in rows)
        percent = weighted_percentage([value for rows in by_course.values() for value in rows])
        if percent is not None:
            points_text = f'{total:g} / {maximum:g}' if finite(total) and finite(maximum) else 'Counting results combined across courses.'
            output.append(dict(heading='Overall average', items=[row('overall', percent_label(percent), 'Weighted counting results', points_text, kind='summary', tone='red' if percent < 50 else 'orange' if percent < 70 else 'green')]))
        for course, rows in sorted(by_course.items()):
            percent = weighted_percentage(rows)
            output.append(dict(heading=course, average=percent_label(percent) if percent is not None else '', items=[value[0] for value in rows]))
    elif section == 5:
        lvs = data.get('lvs') or {}
        read = backend.settings.get(backend.read_key(), [])
        for kind, heading in [('notes', 'Notes'), ('absences', 'Absences')]:
            items = []
            for source in lvs.get(kind, []):
                token = kind+':'+str(source.get('id') or '')
                item = row(token, source.get('title') or source.get('description') or source.get('subject') or ('Note' if kind == 'notes' else 'Absence'),
                           ' · '.join(format_date(source.get(k)) if k == 'date' else text(source.get(k)) for k in ('date', 'category', 'author', 'part') if source.get(k)),
                           fields_text(source), kind=kind, unread=token not in read)
                if matches(item):
                    items.append(item)
            if items:
                output.append(dict(heading=heading, items=items))
    return output
