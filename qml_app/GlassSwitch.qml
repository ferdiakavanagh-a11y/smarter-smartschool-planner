import QtQuick
import QtQuick.Controls
Switch {
    id: toggle
    implicitHeight: Math.max(48*Theme.textScale,contentItem.implicitHeight+20)
    leftPadding: 0; rightPadding: 76
    Accessible.name: text
    contentItem: Text { textFormat:Text.PlainText; text:toggle.text; color:Theme.text
        font.pixelSize:15*Theme.textScale; verticalAlignment:Text.AlignVCenter; wrapMode:Text.Wrap }
    indicator: Item {
        x:toggle.width-60; y:(toggle.height-height)/2; implicitWidth:58; implicitHeight:32
        Rectangle { id:track; anchors.fill:parent; radius:height/2; color:toggle.checked?Theme.green:Theme.fill
            border.width:1; border.color:Theme.alpha(Theme.text,.18)
            Behavior on color { ColorAnimation { duration:Theme.motion?160:0 } }
        }
        ShaderEffectSource { id:trackSource; anchors.fill:parent; sourceItem:toggle.visible&&Theme.active?track:null
            visible:false; live:toggle.visible&&Theme.active; mipmap:true; smooth:true }
        SelectorLens { x:2+toggle.visualPosition*26; y:(parent.height-height)/2; width:28; height:28
            visible:Theme.fancy
            backdrop:trackSource
            Rectangle {anchors.fill:parent;visible:!Theme.fancy;radius:12;color:Theme.elevated;border.color:Theme.separator}
            Behavior on x { enabled:Theme.motion&&!toggle.down; SpringAnimation { spring:4; damping:.8; epsilon:.1 } }
        }
        Rectangle {visible:!Theme.fancy;x:2+toggle.visualPosition*26;y:2;width:28;height:28;radius:14;color:Theme.elevated;border.color:Theme.separator
            Behavior on x {enabled:Theme.motion;NumberAnimation {duration:140}}
        }
        Rectangle { anchors.fill:parent; radius:height/2; color:'transparent'; border.width:toggle.visualFocus?2:0; border.color:Theme.text }
    }
}
