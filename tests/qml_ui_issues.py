"""Native stress harness, synthetic production boundary. --interactive leaves its dev toggle open."""
from pathlib import Path
bootstrap = Path(__file__).with_name('qml_migration_native.py').read_text(encoding='utf-8').split("assert window.property('production')")[0]
exec(compile(bootstrap, __file__, 'exec'))
from copy import deepcopy
from datetime import date, timedelta
from PySide6.QtCore import QObject, Slot, QMetaObject
from PySide6.QtQml import QQmlComponent

evidence = root/'tests/ui-issues/evidence'
evidence.mkdir(parents=True, exist_ok=True)
theme = window.property('appearance')
theme.setProperty('animatedBackground', False)
cases = ['Demo data', 'Worst case', 'Empty', 'One', '1,000 rows']

def fixture(case):
    data = snapshot(credential_store.account_key(credentials))
    data['all_classes'] = deepcopy(data['days'])
    if case == 'Demo data':
        return data
    count = {'Worst case':18, 'Empty':0, 'One':1, '1,000 rows':1000}[case]
    today = date.today()
    data.update(todos=[], days=[], all_classes=[], results=[], lvs=dict(since='2026-09-01', notes=[], absences=[]))
    courses = ['Wetenschappen – interdisciplinair onderzoeksproject en duurzame ontwikkeling', 'Jo', '日本語・ภาษาไทย・Tiếng Việt・العربية 🌍', 'Nederlands']
    names = ['Verwerkingsopdracht film La Tresse (bookwidget) – vergelijk de perspectieven en motiveer je antwoord', 'PE', 'https://school.example/assignments/research/klimaatverandering-in-de-eenentwintigste-eeuw-bijlage-definitieve-versie', 'Bereid het practicum voor: meetresultaten, onzekerheden en een onderbouwde conclusie']
    for i in range(count):
        day = (today+timedelta(days=i%5-1)).isoformat()
        task = dict(id=f'stress-{i}', description=names[i%4], course=courses[i%4], type=['Productevaluatie / onderzoekscompetenties', 'Taak', 'Toets', 'Voorbereiding'][i%4],
                    due_date=day, posted_date=today.isoformat(), body='InstructionNeedle: Lees de volledige opdracht. Zoë · 日本語 · نور.\n'+('Bespreek je resultaten en motiveer de gemaakte keuzes. '*8 if i%4==0 else ''),
                    due_date_corrected=i%3==0, due_date_source='ai' if i%3==0 else 'local', warning=i%4==0, detail_stale=i%4==0,
                    detail_fields=[('organisers.users[0].pictureUrl', 'https://school.example/avatar')])
        data['todos'].append(task)
        event = dict(moment_id=f'lesson-{i}', course=task['course'], start='08:25', end='09:15', classroom='302', teacher='Aleksandra Wiśniewska-Kowalczyk, Catherine Schommer', groups='5LAWE, 5MTWE, 6WEWI, 6HUWE',
                     note='LessonNeedle: onderzoeksopdracht', info=dict(assignments=[dict(id=task['id'], description=task['description'])]))
        data['days'].append(dict(date=day, events=[event]))
        data['all_classes'].append(dict(date=day, events=[deepcopy(event)]))
        grade = dict(id=f'grade-{i}', name=names[i%4], course=courses[i%4], date=day, score=22.5 if i%4 else None, max=30 if i%4 else None, counts=i%3!=0,
                     color='yellow' if i%4==0 else '', text='bullet_square_yellow' if i%4==0 else '', feedback=['GradeNeedle: goed uitgewerkt'], teacher='Aleksandra Wiśniewska-Kowalczyk')
        data['results'].append(grade)
        data['lvs']['absences' if i%2 else 'notes'].append(dict(id=str(i), date=day, title=names[i%4], description='LvsNeedle: School record', author='Aleksandra Wiśniewska-Kowalczyk'))
    if count:
        data['todos'][-1]['body']=''
        data['days'][-1]['events'][0].update(classroom='',teacher='',groups='')
        data['todos'][0]['attachments']=[dict(name='Onderzoeksopdracht klimaatverandering – aanvullende bronnen, meettabellen en de definitieve beoordelingscriteria.pdf',url='https://school.example/attachment')]
    return data

class Fixtures(QObject):
    @Slot(str)
    def choose(self, case):
        backend.data = fixture(case)
        backend.tasks.replace(backend.data)
        backend.changed.emit()

fixtures = Fixtures()
engine.rootContext().setContextProperty('stressHarness', fixtures)
control = QQmlComponent(engine)
control.setData(b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
Window { width:570; height:60; title:"UI test data (development only)"; flags:Qt.Tool
 Row {anchors.centerIn:parent;spacing:4
  Repeater {model:["Demo data","Worst case","Empty","One","1,000 rows"]
   Button {required property string modelData;text:modelData;onClicked:stressHarness.choose(modelData)}
  }
 }
}''', QUrl.fromLocalFile(str(Path(__file__).resolve())))
toggle = control.create()
assert toggle, control.errors()
if '--interactive' in sys.argv:
    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QDesktopServices
    def preview_job(name, action):
        if name.startswith('lvs:'):
            QTimer.singleShot(180,lambda:backend._receive(name,dict(text='Synthetic school note. Keep using the planner to divide larger assignments into manageable steps.',attachments=[]),None))
            return True
        if name != 'sync':return False
        window.setProperty('busy',True)
        QTimer.singleShot(1100,lambda:window.setProperty('busy',False))
        return True
    backend._job=preview_job
    external_guard=patch.object(QDesktopServices,'openUrl',return_value=False);external_guard.start()
    credentials['gemini_api_key']='synthetic-not-a-real-key'
    backend.setDateChecker('local')
    window.setTitle('UI review · synthetic test data')
    fixtures.choose('Worst case');toggle.show();window.requestActivate()
    sys.exit(app.exec())

def capture(label):
    assert window.grabWindow().save(str(evidence/(label+'.png')))

def case(case):
    fixtures.choose(case);window.setProperty('searchText','');QTest.qWait(280)

def overlap_checks():
    for row in [i for i in items() if i.objectName() in ('taskDelegate','sectionRow') and i.isVisible()]:
        top=row.mapToScene(QPointF(0,0)).y()
        if top>=window.height() or top+row.height()<=0:continue
        assert row.width()>0 and row.height()>0
        for label in [i for i in items(row) if i.isVisible() and i.metaObject().indexOfProperty('text')>=0 and i.metaObject().indexOfSignal('clicked()')<0]:
            if label.width()<=0 or label.height()<=0:continue
            p=label.mapToItem(row,QPointF(0,0))
            if not (p.x()>=-1 and p.x()+label.width()<=row.width()+1):
                capture('failure')
                raise AssertionError((window.property('section'),theme.property('style'),theme.property('scheme'),theme.property('textScale'),label.metaObject().className(),label.parentItem().metaObject().className(),label.property('text'),p.x(),label.width(),row.width()))

for label in cases:
    case(label)
    for section in range(6):
        window.setProperty('section',section);QTest.qWait(180)
        capture(label.replace(',','').replace(' ','-')+f'-{section}')
        overlap_checks()
        if label=='1,000 rows':
            delegates=sum(i.objectName() in ('taskDelegate','sectionRow') and i.isVisible() for i in items())
            print('DELEGATES',section,delegates,flush=True)
            assert delegates<100, (section,delegates)

case('Worst case')
for section, needle in enumerate(['InstructionNeedle','InstructionNeedle','LessonNeedle','LessonNeedle','GradeNeedle','LvsNeedle']):
    window.setProperty('section',section);window.setProperty('searchOpen',True);window.setProperty('searchText',needle);QTest.qWait(350)
    view=named('taskList' if section<2 else 'sectionList')
    assert view.property('count')>0,(section,needle)
    window.setProperty('searchText','NoSuchRecord983');QTest.qWait(300)
    assert view.property('count')==0,(section,view.property('count'))
    window.setProperty('searchText','');QTest.qWait(300)
    assert view.property('count')>0
    assert not window.property('headerCollapsed')
window.setProperty('searchOpen',False)

window.setProperty('preferencesReady',False)  # 200% is an injected stress value, outside the shipped 135% preference.
for style in ['vivid','clear']:
    for scheme in ['light','dark']:
        theme.setProperty('style',style);theme.setProperty('scheme',scheme)
        for scale,width in [(1,1100),(1.35,760),(2,760),(1,1920)]:
            theme.setProperty('textScale',scale);window.resize(width,800);QTest.qWait(600)
            for section in range(6):
                window.setProperty('section',section);QTest.qWait(350)
                capture(f'{style}-{scheme}-{scale}-{width}-{section}')
                overlap_checks()

theme.setProperty('textScale',1);window.setProperty('preferencesReady',True);window.resize(1100,800);window.setProperty('section',2);QTest.qWait(300)
target=named('lesson-done-stress-0');click(target)
assert backend.tasks.all[0]['done']
assert task_state.load_completed_ids(out)=={'stress-0'}
window.setProperty('section',0);QTest.qWait(300)
target=named('done-stress-1')
QTest.mouseClick(window,Qt.LeftButton,Qt.NoModifier,target.mapToScene(QPointF(target.width()/2,target.height()/2)).toPoint())
window.setProperty('section',4)
assert 'stress-1' in task_state.load_completed_ids(out),'Completion must save before a quick tab change'
window.setProperty('section',5);QTest.qWait(250)
assert named('unreadDot')
assert named('navigation').property('unreadCount')==18
backend.markRead('*');QTest.qWait(250)
assert named('navigation').property('unreadCount')==0
assert not any(i.objectName()=='unreadDot' and i.isVisible() for i in items())
window.setProperty('section',0);click(button('Settings'))
credentials['gemini_api_key']='synthetic-not-a-real-key';backend.changed.emit();QTest.qWait(100)
toggle_date=named('dateCheckerSwitch');click(toggle_date)
assert backend.checkerState['mode']=='local'
click(toggle_date);assert backend.checkerState['mode']=='gemini'
capture('date-switch');QTest.keyClick(window,Qt.Key_Escape);QTest.qWait(350)
window.showTask('stress-0','Research assignment','');QTest.qWait(350)
named('noteText').setProperty('text',('Mijn notities voor het onderzoeksproject. '*150)[:5000])
capture('details-long-note')
click(button('Save note'));assert len(backend.tasks.taskNote('stress-0'))==5000
window.showTask('stress-0','Research assignment',backend.tasks.taskNote('stress-0'));QTest.qWait(350)
attachment=button('Onderzoeksopdracht klimaatverandering – aanvullende bronnen, meettabellen en de definitieve beoordelingscriteria.pdf')
attachment.forceActiveFocus();QTest.qWait(700);capture('attachment-caption')
assert attachment.width()<=window.width()-40
QTest.keyClick(window,Qt.Key_Escape);QTest.qWait(350)
focus_button=button('Focus');focus_button.forceActiveFocus();click(focus_button);QTest.qWait(350)
window.resize(360,420);QTest.qWait(300);capture('focus-minimum');window.setProperty('focusOpen',False);QTest.qWait(350)
window.setProperty('busy',True);QTest.qWait(350);capture('sync-glass');window.setProperty('busy',False)
theme.setProperty('highContrast',True);theme.setProperty('reducedMotion',True);QTest.qWait(250);capture('high-contrast')
window.resize(320,800);QTest.qWait(600);capture('experimental-320')
print('Experimental width',window.width(),'declared minimum',window.minimumWidth(),flush=True)
window.resize(1100,800);QTest.qWait(400)
assert not warnings, warnings
assert window.close();backend.shutdown();toggle.close();mock.stop()
print('Native UI data, search, themes, 200% text, completion, LVS and settings PASS',flush=True)
