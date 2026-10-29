"""Completed disclosure containment, centering and toggling; synthetic/offscreen."""
from pathlib import Path
bootstrap=Path(__file__).with_name('qml_ui_issues.py').read_text(encoding='utf-8').split('for label in cases:')[0]
exec(compile(bootstrap,__file__,'exec'))
evidence=root/'tests/full-audit/completed-button';evidence.mkdir(exist_ok=True)
case('Worst case')
for index in range(1,7):
    assert backend.tasks.change('stress-'+str(index),'done',True)
for scale in [1,1.35,2]:
    window.setProperty('preferencesReady',False);theme.setProperty('textScale',scale)
    QTest.qWait(200)
    view=named('taskList');view.positionViewAtEnd();QTest.qWait(350)
    view.setProperty('contentY',view.property('originY')+max(0,view.property('contentHeight')+view.property('bottomMargin')-view.height()));QTest.qWait(200)
    control=button('Completed  6');content=control.property('contentItem')
    for item in content.childItems():
        if not item.isVisible():continue
        p=item.mapToItem(content,QPointF(0,0))
        assert p.x()>=-1 and p.x()+item.width()<=content.width()+1
        assert abs(p.y()+item.height()/2-content.height()/2)<1,'Disclosure contents must be vertically centered'
    capture('closed-'+str(scale))
    click(control);assert backend.tasks.completed_open
    QTest.qWait(250);capture('open-'+str(scale))
    click(control);assert not backend.tasks.completed_open
assert not warnings,warnings
from shiboken6 import isValid
if isValid(toggle):toggle.close()
if isValid(window):window.close()
backend.shutdown();mock.stop()
print('Completed button containment, centering and toggle PASS')
