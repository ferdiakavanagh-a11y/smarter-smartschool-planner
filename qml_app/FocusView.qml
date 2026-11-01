import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Item {
    id:view
    required property var app
    required property var backdrop
    property string taskId:''
    property string taskTitle:'Choose one thing. Give it your attention.'
    property int elapsed:0
    property bool completed:false
    signal leave()
    function refresh(){elapsed=Math.floor(stopwatch.seconds())}
    onVisibleChanged:if(visible){focusScroll.contentItem.cancelFlick();focusScroll.contentItem.contentY=0;refresh()}
    Connections {target:stopwatch;function onChanged(){view.refresh()}}
    Timer {interval:1000;repeat:true;running:view.visible&&app.renderActive&&stopwatch.running;onTriggered:view.refresh()}
    ColumnLayout {
        anchors.fill:parent;anchors.margins:16;spacing:14
        RowLayout {Layout.fillWidth:true
            Label {textFormat:Text.PlainText;text:'Focus';color:Theme.secondary;Layout.fillWidth:true;font.pixelSize:14;font.bold:true
                MouseArea{anchors.fill:parent;onPressed:app.startSystemMove()}}
            Capsule {selectorMaterial:true;backdrop:view.backdrop;text:'Minimize';iconOnly:true;symbol:'minimize';onClicked:app.showMinimized()}
        }
        Label {textFormat:Text.PlainText;text:stopwatch.running?'STOPWATCH':'PAUSED';color:Theme.secondary;font.pixelSize:11;font.letterSpacing:2;Layout.alignment:Qt.AlignHCenter}
        Label {textFormat:Text.PlainText;text:Math.floor(view.elapsed/3600).toString().padStart(2,'0')+':'+Math.floor(view.elapsed/60%60).toString().padStart(2,'0')+':'+(view.elapsed%60).toString().padStart(2,'0')
            color:Theme.text;font.pixelSize:40;font.weight:Font.Light;Layout.alignment:Qt.AlignHCenter;Accessible.name:'Elapsed focus time '+text}
        SelectorLens {objectName:'focusTaskGlass';Layout.fillWidth:true;Layout.fillHeight:true;backdrop:view.backdrop;radius:28
            ScrollView {id:focusScroll;anchors.fill:parent;anchors.margins:20;clip:true;contentWidth:availableWidth;contentHeight:focusText.implicitHeight
                ColumnLayout {id:focusText;width:focusScroll.availableWidth;spacing:18
                    Label {textFormat:Text.PlainText;text:view.taskTitle;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text;font.pixelSize:20*Theme.textScale;font.weight:Font.DemiBold}
                    Label {textFormat:Text.PlainText;text:'INSTRUCTIONS';color:Theme.secondary;font.pixelSize:11;font.bold:true;font.letterSpacing:1}
                    Label {textFormat:Text.PlainText;text:app.production?(backend.taskDetail(view.taskId).body||'No additional instructions.'):'Review the topic, record your working and bring one question to class.';Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text;font.pixelSize:15*Theme.textScale}
                    Label {textFormat:Text.PlainText;text:app.production?'':'Synthetic task · memory only';color:Theme.secondary;font.pixelSize:12}
                }
            }
        }
        Item {Layout.fillWidth:true;implicitHeight:Math.max(76,64*Theme.textScale)
            Accessible.role:Accessible.ToolBar;Accessible.name:'Focus controls'
            SelectorLens {objectName:'focusActionBar';anchors.fill:parent;backdrop:view.backdrop;radius:28}
            RowLayout {anchors.fill:parent;anchors.margins:8;spacing:0
                Repeater {model:4
                    Button {id:action;required property int index;Layout.fillWidth:true;Layout.fillHeight:true;Layout.preferredWidth:1;Layout.minimumWidth:44
                        property string label:index===0?(stopwatch.running?'Pause':'Resume'):index===1?'On top':index===2?(view.completed?'Done':'Complete'):'Exit'
                        property string symbol:index===0?(stopwatch.running?'pause':'play'):index===1?'pin':index===2?'ok':'focus'
                        readonly property bool selected:index===1&&app.focusOnTop
                        readonly property color ink:!Theme.highContrast&&index===2&&view.completed?Theme.green:Theme.text
                        leftPadding:4;rightPadding:4;topPadding:8;bottomPadding:8
                        Accessible.name:label;text:label
                        Accessible.checkable:index===1;Accessible.checked:selected
                        enabled:index!==2||!view.completed;hoverEnabled:true
                        background:Rectangle {radius:20
                            color:action.down?Theme.alpha(Theme.text,.12):action.selected?Theme.alpha(Theme.blue,.1):action.hovered?Theme.alpha(Theme.text,.06):'transparent'
                            border.width:action.visualFocus?2:0;border.color:Theme.highContrast?Theme.text:Theme.blue
                            Behavior on color {ColorAnimation {duration:Theme.motion?100:0}}
                        }
                        contentItem:Column {spacing:4;opacity:action.enabled?1:.55
                            Icon {name:action.symbol;anchors.horizontalCenter:parent.horizontalCenter;width:20;height:20;ink:action.ink}
                            Text {textFormat:Text.PlainText;text:action.label;width:parent.width;horizontalAlignment:Text.AlignHCenter;elide:Text.ElideRight;color:action.ink;font.pixelSize:12*Theme.textScale;font.weight:action.selected?Font.DemiBold:Font.Medium}
                        }
                        onClicked:{if(index===0)stopwatch.toggle();if(index===1){app.focusOnTop=!app.focusOnTop;app.show()}if(index===2&&tasks.change(view.taskId,'done',true))view.completed=true;if(index===3)view.leave()}
                    }
                }
            }
        }
    }
}
