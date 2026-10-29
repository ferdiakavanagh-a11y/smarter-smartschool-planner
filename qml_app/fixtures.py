"""Deterministic synthetic fixtures shared by both frontend experiments."""
from datetime import date, timedelta

COURSES = ['Mathematics', 'Nederlands', 'Sciences', 'History', 'Français', '日本語 & cultuur']
TYPES = ['Taak', 'Toets', 'Voorbereiding']
TITLES = [
    'Explore quadratic functions', 'Lees het verhaal — schrijf je eigen einde',
    'Energy in everyday life: prepare the experiment', 'A timeline of changing cities',
    'Écrire une lettre à Zoë · naïef, cœur & café',
    '言葉と文化 · نور · 🧭 — compare three perspectives',
    'A very long assignment title that should wrap without hiding completion, pin or note controls — '
    'bring your observations, explain each decision and include an alternative interpretation',
    '<script> is text, never executable & __proto__ is just a name',
]


def make_tasks(count=36):
    if count not in (0, 36, 1000):
        raise ValueError('Use the empty, typical or 1,000-task fixture')
    # Fixed dates make repeated measurements independent of the host calendar.
    return [dict(taskId=f'synthetic-{i}', title=TITLES[i % len(TITLES)],
                 course=COURSES[i % len(COURSES)], kind=TYPES[i % 3],
                 due=(date(2026, 10, 24) + timedelta(days=-(i//12+1) if i in (11,23,35) else i // 6)).isoformat(),
                 done=False, pinned=False, note='', posted='2026-10-24',
                 body='Synthetic study material. No account connected.') for i in range(count)]


def web_data(count):
    todos = [dict(id=t['taskId'], description=t['title'], course=t['course'],
                           type=t['kind'], due_date=t['due'], posted_date=t['posted'],
                           body=t['body'], attachments=[], weblinks=[])
                       for t in make_tasks(count)]
    days = [dict(date=f'2026-10-{26+d}', events=[dict(moment_id=f'lesson-{d*6+i}', course=c,
                start=f'{8+i}:30', end=f'{9+i}:20', classroom=str(101+i), teacher='Demo teacher',
                groups='Demo class', title='', info=dict(assignments=[])) for i,c in enumerate(COURSES)]) for d in range(3)] if count else []
    results = [dict(id=f'grade-{i}',name='Chapter review' if i%2==0 else 'Class participation',
                    course=COURSES[i//2], date='2026-10-23',score=[8,14,18][i%3],max=[10,20,20][i%3],
                    percent=[80,70,90][i%3],counts=i%3!=0, feedback=['Explain your reasoning and check the final step.']) for i in range(12)] if count else []
    notes = [dict(id=f'lvs-{i}',title=t,date='2026-10-23',author='Demo tutor',category='Study') for i,t in enumerate(['Study progress','A note about participation','Project feedback','Planning support','Next steps'])] if count else []
    absences = [dict(id=f'lvs-{i}',date='2026-10-23',description='Absence · authorised',part='Morning',code='A') for i in range(5,8)] if count else []
    return dict(todos=todos, days=days, all_classes=days, results=results,
                results_note='Saved synthetic example · refresh unavailable', lvs=dict(notes=notes, absences=absences),
                generated_at='2026-10-24T09:00:00', main_url='', account_key='qml-comparison-synthetic')
