import QtQuick
import QtQuick.Controls
CheckBox {
    id: control
    property bool animateFeedback:true
    property real markSize:26
    padding: 0
    implicitWidth: 36; implicitHeight: 36
    indicator: Item {
        implicitWidth: control.markSize; implicitHeight: control.markSize
        x: (control.width-width)/2; y: (control.height-height)/2
        SelectorLens { anchors.fill: parent; backdrop:Theme.backdrop }
        Rectangle { anchors.fill: parent; radius: height/2
            color: control.checked ? '#246fae' : 'transparent'
            border.width: control.visualFocus ? 2 : 1
            border.color: control.visualFocus ? Theme.text : control.checked ? '#246fae' : Theme.alpha(Theme.text,.35)
            Behavior on color {enabled:control.animateFeedback; ColorAnimation { duration: Theme.motion ? 180 : 0 } }
        }
        Icon {objectName:'completionTick'; name:'check'; ink:'white'; width:control.markSize*.65; height:width; anchors.centerIn:parent
            opacity:control.checked?1:0
            scale:control.checked?1:.7
            Behavior on opacity {enabled:control.animateFeedback; NumberAnimation { duration:Theme.motion?180:0 } }
            Behavior on scale {enabled:control.animateFeedback;NumberAnimation {duration:Theme.motion?240:0;easing.type:Easing.OutCubic}}
        }
    }
    contentItem: Item {}
}
