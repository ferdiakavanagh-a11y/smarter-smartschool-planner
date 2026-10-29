"""Local task actions preserve scroll; synthetic/offscreen only."""
from pathlib import Path
bootstrap=Path(__file__).with_name('qml_ui_issues.py').read_text(encoding='utf-8').split('for label in cases:')[0]
exec(compile(bootstrap,__file__,'exec'))
from shiboken6 import isValid
case('Worst case')
for index in range(1,5):
    assert backend.tasks.change('stress-'+str(index),'done',True)
QTest.qWait(450)
view=named('taskList')
def offset():return view.property('contentY')-view.property('originY')
def unchanged(action,label,anchor=False):
    before=offset()
    assert before>300,(label,'not scrolled',before)
    candidates=[i for i in items(view) if i.objectName()=='taskDelegate' and i.property('taskId')!='stress-7' and 0<=i.mapToItem(view,QPointF(0,0)).y()<view.height()/2]
    row=candidates[0] if anchor else None
    task_id=row.property('taskId') if row else None
    top=row.mapToItem(view,QPointF(0,0)).y() if row else None
    action();QTest.qWait(450)
    after=offset()
    print(label,before,after,flush=True)
    if anchor:
        assert task_id,'Need a visible reading anchor'
        row=next(i for i in items(view) if i.objectName()=='taskDelegate' and i.property('taskId')==task_id)
        delta=abs(row.mapToItem(view,QPointF(0,0)).y()-top)
        print('anchor delta',label,delta,flush=True)
        assert after>300 and delta<3,(label,'reading anchor lost',delta)
    else:assert abs(after-before)<3,(label,before,after)
for fancy in [True,False]:
    theme.setProperty('fancy',fancy)
    view.positionViewAtEnd();QTest.qWait(450)
    unchanged(lambda:QMetaObject.invokeMethod(button('Completed  4'),'clicked'),'expand completed',True)
    view.positionViewAtEnd();QTest.qWait(350)
    QMetaObject.invokeMethod(button('Completed  4'),'clicked');QTest.qWait(450)
    assert offset()>300,'Collapsing must clamp to the remaining page, not jump to its top'
    view.setProperty('contentY',view.property('originY')+550);QTest.qWait(350)
    unchanged(lambda:backend.tasks.change('stress-7','pinned',True),'pin task',True)
    unchanged(lambda:backend.tasks.change('stress-7','note','Saved note'),'save note',True)
    unchanged(lambda:backend.tasks.undo(),'undo note',True)
    unchanged(lambda:backend.tasks.change('stress-7','pinned',False),'unpin task',True)
window.setProperty('searchText','InstructionNeedle');QTest.qWait(500)
assert view.property('atYBeginning'),'A deliberate new search still starts at the top'
window.setProperty('searchText','');QTest.qWait(500)
view.setProperty('contentY',view.property('originY')+550);QTest.qWait(300)
window.setProperty('section',1);QTest.qWait(500)
window.setProperty('section',0);QTest.qWait(500)
assert view.property('atYBeginning'),'A deliberate tab change still starts at the top'
assert not warnings,warnings
if isValid(toggle):toggle.close()
if isValid(window):window.close()
backend.shutdown();mock.stop()
print('Local task actions preserve scroll in both rendering modes PASS',flush=True)
