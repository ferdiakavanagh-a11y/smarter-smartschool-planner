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
    onVisibleChanged:if(visible)refresh()
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
        Item {Layout.fillWidth:true;implicitHeight:76
            SelectorLens {objectName:'focusActionBar';anchors.fill:parent;backdrop:view.backdrop}
            RowLayout {anchors.fill:parent;anchors.margins:8;spacing:4
                Repeater {model:4
                    Button {id:action;required property int index;Layout.fillWidth:true;Layout.fillHeight:true
                        property string label:index===0?(stopwatch.running?'Pause':'Resume'):index===1?'On top':index===2?(view.completed?'Done':'Complete'):'Exit'
                        property string symbol:index===0?(stopwatch.running?'pause':'play'):index===1?'pin':index===2?'ok':'focus'
                        Accessible.name:label;text:label
                        enabled:index!==2||!view.completed;hoverEnabled:true
                        background:ButtonGlass {control:action;selectorMaterial:true;backdrop:view.backdrop;selected:action.index===1&&app.focusOnTop||action.index===2&&view.completed}
                        contentItem:Column {spacing:3
                            Icon {name:action.symbol;anchors.horizontalCenter:parent.horizontalCenter;ink:action.index===2&&view.completed?Theme.green:Theme.text}
                            Text {textFormat:Text.PlainText;text:action.label;anchors.horizontalCenter:parent.horizontalCenter;color:Theme.text;font.pixelSize:12}
                        }
                        onClicked:{if(index===0)stopwatch.toggle();if(index===1){app.focusOnTop=!app.focusOnTop;app.show()}if(index===2&&tasks.change(view.taskId,'done',true))view.completed=true;if(index===3)view.leave()}
                    }
                }
            }
        }
    }
}
