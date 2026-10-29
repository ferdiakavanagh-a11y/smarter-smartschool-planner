import QtQuick
import QtQuick.Controls
CheckBox {
    id: control
    property bool animateFeedback:true
    padding: 0
    implicitWidth: 36; implicitHeight: 36
    indicator: Item {
        implicitWidth: 28; implicitHeight: 28
        x: (control.width-width)/2; y: (control.height-height)/2
        SelectorLens { anchors.fill: parent; backdrop:Theme.backdrop }
        Rectangle { anchors.fill: parent; radius: height/2
            color: control.checked ? '#246fae' : 'transparent'
            border.width: control.visualFocus ? 2 : 1
            border.color: control.visualFocus ? Theme.text : control.checked ? '#246fae' : Theme.alpha(Theme.text,.35)
            Behavior on color {enabled:control.animateFeedback; ColorAnimation { duration: Theme.motion ? 180 : 0 } }
        }
        Icon {objectName:'completionTick'; name:'check'; ink:'white'; width:18; height:18; anchors.centerIn:parent
            opacity:control.checked?1:0
            scale:control.checked?1:.7
            Behavior on opacity {enabled:control.animateFeedback; NumberAnimation { duration:Theme.motion?180:0 } }
            Behavior on scale {enabled:control.animateFeedback;NumberAnimation {duration:Theme.motion?240:0;easing.type:Easing.OutCubic}}
        }
    }
    contentItem: Item {}
}
