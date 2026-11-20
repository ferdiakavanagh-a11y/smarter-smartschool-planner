import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
SelectorLens {id:assignment;objectName:'lessonAssignment';required property var modelData;required property var app;property real scrollOffset:0;signal opened();Layout.fillWidth:true;implicitHeight:assignmentRow.implicitHeight+16;radius:Theme.fancy?12:3;backdrop:app.sceneBackdrop;tracking:scrollOffset
    RowLayout {id:assignmentRow;anchors.fill:parent;anchors.margins:8;spacing:8
        TaskCheck {id:lessonCheck;markSize:20;implicitWidth:24;implicitHeight:24;objectName:'lesson-done-'+assignment.modelData.id;Layout.alignment:Qt.AlignTop;enabled:assignment.modelData.editable;checked:tasks.completedIds.indexOf(assignment.modelData.id)>=0;Accessible.name:(checked?I18n.t('Restore '):I18n.t('Complete '))+assignment.modelData.title
            onClicked:{let id=assignment.modelData.id,done=checked,host=app;if(tasks.change(id,'done',done))host.notify(done?I18n.t('Task completed'):I18n.t('Task restored'));else checked=Qt.binding(function(){return tasks.completedIds.indexOf(assignment.modelData.id)>=0})}
        }
        Button {id:openTask;Layout.fillWidth:true;padding:2;flat:true;enabled:assignment.modelData.editable;Accessible.name:assignment.modelData.title
            onClicked:{let item=assignment.modelData;assignment.app.showTask(item.id,item.title,tasks.taskNote(item.id));assignment.opened()}
            background:Rectangle {color:'transparent';radius:4;border.color:openTask.visualFocus?Theme.text:'transparent'}
            contentItem:ColumnLayout {spacing:4
            Label {textFormat:Text.PlainText;text:assignment.modelData.title;font.pixelSize:14*Theme.textScale;font.weight:Font.DemiBold;font.strikeout:lessonCheck.checked;color:Theme.text;Layout.fillWidth:true;wrapMode:Text.Wrap}
            Label {textFormat:Text.PlainText;text:assignment.modelData.kind+(assignment.modelData.due?I18n.t(' · due ')+assignment.modelData.due:'');font.pixelSize:12*Theme.textScale;color:Theme.secondary;Layout.fillWidth:true;wrapMode:Text.Wrap}
            }
        }
    }
}
