"""Focused synthetic reproductions: --missed, --lvs, or --tooltip."""
from pathlib import Path
bootstrap=Path(__file__).with_name('qml_ui_issues.py').read_text(encoding='utf-8').split('for label in cases:')[0]
exec(compile(bootstrap,__file__,'exec'))
from PySide6.QtQml import QQmlExpression,qmlContext
from datetime import timedelta
evidence=root/'tests/ui-issues/popups-missed-lvs';evidence.mkdir(parents=True,exist_ok=True)
def capture(label):assert window.grabWindow().save(str(evidence/(label+'.png')))

if '--missed' in sys.argv:
    case('Worst case')
    for i,item in enumerate(backend.data['todos']):item['due_date']=(date.today()-timedelta(days=i%6+1)).isoformat()
    backend.tasks.replace(backend.data);backend.changed.emit()
    window.setProperty('section',1);QTest.qWait(700)
    rows=sorted([i for i in items() if i.objectName()=='taskDelegate' and i.isVisible() and 120<i.mapToScene(QPointF(0,0)).y()<window.height()-200],key=lambda i:i.mapToScene(QPointF(0,0)).y())
    assert len(rows)>=2
    row,neighbor=rows[:2];task_id=row.property('taskId');title=row.property('title');next_id=neighbor.property('taskId')
    check=named('done-'+task_id)
    QTest.mouseClick(window,Qt.LeftButton,Qt.NoModifier,check.mapToScene(QPointF(check.width()/2,check.height()/2)).toPoint())
    assert task_id in task_state.load_completed_ids(out) and next_id not in task_state.load_completed_ids(out)
    QTest.qWait(70)
    bottom=row.mapToScene(QPointF(0,row.height())).y();top=neighbor.mapToScene(QPointF(0,0)).y()
    print('MISSED',task_id,next_id,'row bottom',bottom,'next top',top,'opacity',row.opacity(),flush=True)
    assert row.property('title')==title,'Do not borrow the next task’s text while exiting'
    assert top>=bottom-1 or row.opacity()<.05,'The next task slides underneath the still-visible completed row'
    QTest.qWait(210)
    assert row.isVisible() and row.opacity()>0,'The confirmation should remain visible longer'
    capture('missed-check-280ms')
    QTest.qWait(600)
    assert len(task_state.load_completed_ids(out))==1
    assert backend.tasks.undo();QTest.qWait(200)
    view=named('taskList');view.setProperty('contentY',view.property('originY')+600);QTest.qWait(450)
    rows=sorted([i for i in items() if i.objectName()=='taskDelegate' and i.isVisible() and 100<i.mapToScene(QPointF(0,0)).y()<window.height()-200],key=lambda i:i.mapToScene(QPointF(0,0)).y())
    assert rows
    task_id=rows[0].property('taskId');check=named('done-'+task_id)
    QTest.mouseClick(window,Qt.LeftButton,Qt.NoModifier,check.mapToScene(QPointF(check.width()/2,check.height()/2)).toPoint())
    assert task_id in task_state.load_completed_ids(out)
    view.setProperty('currentIndex',-1);view.forceActiveFocus();view.setProperty('contentY',view.property('originY')+1400);QTest.qWait(100)
    for check_control in [i for i in items() if i.objectName().startswith('done-') and i.isVisible() and not i.property('checked')]:
        tick=next(i for i in items(check_control) if i.objectName()=='completionTick')
        assert tick.property('opacity')==0,'A reused row must not inherit another task’s check animation'
    window.setProperty('section',5);QTest.qWait(750)
    assert named('sectionList').property('atYBeginning')
    window.setProperty('section',1);QTest.qWait(350)
    assert backend.tasks.rowCount()==17 and len(task_state.load_completed_ids(out))==1

elif '--lvs' in sys.argv:
    case('Worst case')
    for previous in [4,2,0,3,4]:
        window.setProperty('section',previous);QTest.qWait(450)
        view=named('taskList' if previous<2 else 'sectionList')
        view.setProperty('contentY',view.property('originY')+750);QTest.qWait(350)
        window.setProperty('section',5);QTest.qWait(550)
        view=named('sectionList');mark=button('Mark all as read')
        top=view.mapToScene(QPointF(0,0)).y();point=mark.mapToScene(QPointF(0,0))
        print('LVS FROM',previous,'content',view.property('contentY'),'origin',view.property('originY'),'header',point.y(),'viewport',top,flush=True)
        capture('lvs-from-'+str(previous))
        assert view.property('atYBeginning') and point.y()>=top-1,'LVS must reveal its complete header on entry'
        assert not window.property('headerCollapsed')
    view.setProperty('contentY',view.property('originY')+500);QTest.qWait(300)
    window.pickSection(5);QTest.qWait(550)
    assert view.property('atYBeginning'),'Reselecting LVS should reveal its header too'

elif '--tooltip' in sys.argv:
    case('Demo data')
    backend.data['todos'][0]['due_date_corrected']=True
    backend.tasks.replace(backend.data);backend.changed.emit();QTest.qWait(400)
    icon=next(i for i in items() if i.isVisible() and i.property('name')=='cal')
    QTest.mouseMove(window,icon.mapToScene(QPointF(icon.width()/2,icon.height()/2)).toPoint());QTest.qWait(700)
    tip=window.property('activeToolTip') if window.metaObject().indexOfProperty('activeToolTip')>=0 else None
    if not tip:
        value=QQmlExpression(qmlContext(icon.parentItem()),icon.parentItem(),'ToolTip.toolTip').evaluate();tip=value[0] if isinstance(value,tuple) else value
    assert tip and tip.property('visible')
    capture('date-tooltip')
    assert 'SelectorLens' in tip.property('background').metaObject().className(),'Informational popups must use the shared glass material'
    assert tip.property('text')=='Corrected date'
    QTest.mouseMove(window,QPointF(5,5).toPoint());QTest.qWait(220)
    search=button('Search')
    QTest.mouseMove(window,search.mapToScene(QPointF(search.width()/2,search.height()/2)).toPoint());QTest.qWait(640)
    tip=window.property('activeToolTip')
    assert tip and tip.property('text')=='Search'
    assert 0<tip.property('opacity')<=1 and .95<=tip.property('scale')<=1
    QTest.qWait(220);capture('button-tooltip')
else:raise AssertionError('Choose --missed, --lvs or --tooltip')

assert not warnings,warnings
toggle.close();assert window.close();backend.shutdown();mock.stop()
print('Focused UI case PASS',flush=True)
