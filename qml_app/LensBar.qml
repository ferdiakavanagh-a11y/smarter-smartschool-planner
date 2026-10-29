// Lens growth adapted from MacShell GlassSegmented.qml (MIT).
import QtQuick
import QtQuick.Controls
Item {
    id: bar
    required property var backdrop
    property var labels: []
    property var symbols: []
    property int missedCount: 0
    property int unreadCount: 0
    property int current: 0
    property bool fancy: Theme.fancy
    property bool motion: Theme.motion
    property real textScale: Theme.textScale
    property bool canceled: false
    property bool ready: false
    property bool movingRight: true
    property real grabOffset: cell/2
    Component.onCompleted: ready=true
    onCurrentChanged: if(ready)movingRight=10+current*cell>=leftEdge
    signal picked(int index)
    implicitHeight: symbols.length ? 76 : 48
    readonly property real cell: (width - 20) / Math.max(1,labels.length)
    readonly property int preview: Math.max(0,Math.min(labels.length-1,Math.floor((scrub.centroid.position.x-10)/cell)))
    readonly property real dragLeft: Math.max(0,Math.min(width-cell,scrub.centroid.position.x-grabOffset))
    property real leftEdge: scrub.active ? dragLeft : 10 + current * cell
    property real rightEdge: scrub.active ? dragLeft + cell : 10 + (current+1) * cell
    Behavior on leftEdge { enabled: bar.motion && !scrub.active; SpringAnimation { spring: bar.movingRight?4.1:4.8; damping: .32; epsilon: .1 } }
    Behavior on rightEdge { enabled: bar.motion && !scrub.active; SpringAnimation { spring: bar.movingRight?4.8:4.1; damping: .34; epsilon: .1 } }
    // Navigation samples the app scene; settings lenses share the continuous wallpaper.
    property real pressT: contact.active && bar.motion ? 1 : 0
    Behavior on pressT { enabled:bar.motion; NumberAnimation {duration:contact.active?150:280;easing.type:Easing.OutCubic} }
    Surface { visible:!bar.symbols.length; anchors.fill: parent; radius: height/2 }
    SelectorLens {objectName:'navigationGlass';visible:bar.symbols.length>0;anchors.fill:parent;backdrop:bar.backdrop;fancy:bar.fancy;strength:18;rim:.24;ring:-.4;shadow:.6}
    Repeater {model:bar.symbols.length?0:Math.max(0,bar.labels.length-1)
        Rectangle {required property int index;x:10+(index+1)*bar.cell;y:bar.height*.3;width:1;height:bar.height*.4;color:Theme.rim;visible:index!==bar.current&&index+1!==bar.current}
    }
    SelectorLens { objectName:'selectionLens';backdrop: bar.backdrop; fancy: bar.fancy
        x: Math.min(bar.leftEdge,bar.rightEdge)-bar.cell*.06*bar.pressT; y: (bar.height-height)/2
        width: Math.max(16,Math.abs(bar.rightEdge-bar.leftEdge))+bar.cell*.12*bar.pressT; height: (bar.height-16)*(1+.12*bar.pressT)
        strength:bar.symbols.length?24:30
    }
    Row { x: 10; y: 8
        Repeater { model: bar.labels
            Button {
                id: tab
                required property string modelData
                required property int index
                text:modelData
                width: bar.cell; height: bar.height-16
                hoverEnabled: true
                Accessible.role: Accessible.PageTab
                Accessible.selected: index===bar.current
                Accessible.name: modelData+(index===1&&bar.missedCount?', '+bar.missedCount+' missed':index===5&&bar.unreadCount?', '+bar.unreadCount+' unread':'')
                background: Item {
                    Rectangle {anchors.fill:parent;radius:height/2;color:'transparent';border.width:tab.visualFocus?2:0;border.color:Theme.text}
                }
                contentItem: Column { spacing: 2
                    Icon { visible: bar.symbols.length>0; name: bar.symbols[tab.index] || 'ok'; anchors.horizontalCenter: parent.horizontalCenter
                        ink: tab.index===bar.current || tab.hovered || (scrub.active && tab.index===bar.preview) ? Theme.text : Theme.secondary }
                    Text {textFormat:Text.PlainText; anchors.horizontalCenter: parent.horizontalCenter; width:bar.cell-8;wrapMode:Text.Wrap;horizontalAlignment:Text.AlignHCenter;text: tab.modelData; font.pixelSize: (bar.symbols.length ? 12 : 14)*bar.textScale
                        color: tab.index===bar.current || tab.hovered ? Theme.text : Theme.secondary; font.weight: Font.DemiBold }
                }
                onClicked: bar.picked(index)
                Rectangle {objectName:'tabBadge';property int count:tab.index===1?bar.missedCount:tab.index===5?bar.unreadCount:0
                    visible:count>0;width:Math.max(20,countLabel.implicitWidth+10);height:20;radius:10;x:parent.width/2+8;y:0;color:'#c9322b'
                    Text {id:countLabel;textFormat:Text.PlainText;anchors.centerIn:parent;text:parent.count>99?'99+':parent.count;color:'white';font.pixelSize:12;font.bold:true} }
                Keys.onReturnPressed: bar.picked(index)
                Keys.onLeftPressed: { bar.picked((bar.current+bar.labels.length-1)%bar.labels.length); }
                Keys.onRightPressed: { bar.picked((bar.current+1)%bar.labels.length); }
            }
        }
    }
    Item {
        anchors.fill:parent;z:2
        PointHandler {
            id:contact;target:null
            onActiveChanged:if(active){
                let x=point.position.x,left=Math.min(bar.leftEdge,bar.rightEdge),right=Math.max(bar.leftEdge,bar.rightEdge)
                bar.grabOffset=x>=left&&x<=right?x-left:bar.cell/2
            }
        }
    }
    DragHandler {
        id: scrub; objectName: 'navigationScrub'; target: null; yAxis.enabled: false; dragThreshold: 6
        onActiveChanged: {
            if (active) bar.canceled=false
            else { let selected=bar.preview; Qt.callLater(function(){if(!bar.canceled)bar.picked(selected)}) }
        }
        onCanceled: bar.canceled=true
    }
}
