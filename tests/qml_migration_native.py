"""Production boundary with synthetic, isolated disk data and no network/vault access."""
import os, sys, json
from pathlib import Path
from unittest.mock import patch
os.environ['QSG_RHI_BACKEND']='d3d11'
os.environ['QSG_RENDER_LOOP']='basic'
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from PySide6.QtCore import Qt,QPointF,QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest
import credential_store,task_state
from qml_app.backend import Backend
from qml_app.model import Stopwatch
from test_qml_migration import snapshot
out=root/'tests/qml-migration/native';(out/'data').mkdir(parents=True,exist_ok=True)
assert (root/'tests').resolve() in out.resolve().parents
for filename in ['ui_settings.json','task_notes.json','pinned_tasks.json','completed_tasks.json']:
 (out/'data'/filename).unlink(missing_ok=True)
credentials=dict(main_url='school.example',username='synthetic')
(out/'data/planner_data.json').write_text(json.dumps(snapshot(credential_store.account_key(credentials))),encoding='utf-8')
mock=patch.object(credential_store,'load_credentials',return_value=credentials);mock.start()
QQuickStyle.setStyle('Basic');app=QGuiApplication(sys.argv)
backend=Backend(out);watch=Stopwatch();engine=QQmlApplicationEngine();warnings=[]
engine.warnings.connect(lambda ws:warnings.extend(w.toString() for w in ws))
for key,value in dict(backend=backend,tasks=backend.tasks,stopwatch=watch,initialCount=0,initialFancy=True,initialMatched=False,benchmarkEnabled=False).items():
 engine.rootContext().setContextProperty(key,value)
engine.load(QUrl.fromLocalFile(str(root/'qml_app/Main.qml')))
assert engine.rootObjects(),warnings
window=engine.rootObjects()[0];window.show();window.requestActivate();QTest.qWait(900)
def items(parent=None):
 for child in (parent or window.contentItem()).childItems():
  yield child;yield from items(child)
def named(name):return next(i for i in items() if i.objectName()==name and i.isVisible())
def button(text):return next(i for i in items() if i.isVisible() and i.property('text')==text and i.metaObject().indexOfSignal('clicked()')>=0)
def click(item):
 ancestor=item.parentItem()
 while ancestor is not None:
  if ancestor.metaObject().indexOfProperty('contentY')>=0:
   position=item.mapToItem(ancestor,QPointF(0,0))
   if position.y()<8 or position.y()+item.height()>ancestor.height()-8:
    target=ancestor.property('contentY')+position.y()-ancestor.height()+item.height()+16
    origin=ancestor.property('originY') or 0
    bottom=ancestor.property('bottomMargin') or 0
    ancestor.setProperty('contentY',max(origin,min(target,origin+max(0,ancestor.property('contentHeight')+bottom-ancestor.height()))))
    QTest.qWait(100)
   break
  ancestor=ancestor.parentItem()
 previous=None;stable=0
 for _ in range(100):
  p=item.mapToScene(QPointF(item.width()/2,item.height()/2)).toPoint()
  stable=stable+1 if previous==p else 0
  if stable>=3 and 0<p.x()<window.width() and 0<p.y()<window.height():break
  previous=p;QTest.qWait(40)
 else:raise AssertionError('Control did not settle: '+str(item.property('text')))
 QTest.mouseClick(window,Qt.LeftButton,Qt.NoModifier,p);QTest.qWait(350)
assert window.property('production') and backend.tasks.rowCount()==1
for section in range(6):
 window.setProperty('section',section);QTest.qWait(350)
 assert window.grabWindow().save(str(out/f'section-{section}.png'))
window.setProperty('section',0);QTest.qWait(400)
window.showTask('task-1','Quadratic functions',backend.tasks.taskNote('task-1'));QTest.qWait(350)
named('noteText').setProperty('text','Durable native note');click(button('Save note'))
assert task_state.load_notes(out)['task-1']=='Durable native note'
window.showTask('task-1','Quadratic functions','Durable native note');QTest.qWait(350)
named('noteText').setProperty('text','Unsaved draft')
with patch.object(task_state,'set_note',side_effect=OSError('disk full')):
 window.close();QTest.qWait(200)
 assert window.isVisible() and named('noteText').property('text')=='Unsaved draft'
assert task_state.load_notes(out)['task-1']=='Durable native note'
from PySide6.QtCore import QObject,QMetaObject
error_sheet=window.findChild(QObject,'errorSheet')
QMetaObject.invokeMethod(error_sheet,'close');QTest.qWait(500)
click(button('Save note'))
assert task_state.load_notes(out)['task-1']=='Unsaved draft'
click(button('Settings'));QTest.qWait(300)
assert window.grabWindow().save(str(out/'settings.png'))
print('SETTINGS BEFORE',window.property('appearance').property('fancy'),window.property('preferencesReady'),flush=True)
click(button('Performance'));QTest.qWait(500)
print('SETTINGS AFTER',window.property('appearance').property('fancy'),task_state.load_settings(out),warnings,flush=True)
assert task_state.load_settings(out)['renderingMode']=='performance'
QTest.keyClick(window,Qt.Key_Escape);QTest.qWait(350)
assert not warnings,warnings
assert window.close();backend.shutdown();QTest.qWait(100)
del engine;mock.stop()
print('Production QML, six sections, durable note slots, failed-save close veto and preferences PASS')
