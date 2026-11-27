import QtQuick
import QtQuick.Controls

Menu {
    id:menu
    focus:true
    popupType:Popup.Item
    enter: Transition {NumberAnimation {property:'opacity';from:0;to:1;duration:Theme.motion?120:0;easing.type:Easing.OutCubic}}
    exit: Transition {NumberAnimation {property:'opacity';to:0;duration:Theme.motion?85:0}}
    onOpened:{
        if (Theme.smartschool && currentIndex<0) {
            for (let i=0; i<count; i++) {
                const option=itemAt(i)
                if (option && option.visible && option.enabled) {
                    option.forceActiveFocus(Qt.PopupFocusReason)
                    break
                }
            }
        }
    }
    padding:Theme.fancy ? 7 : 5
    margins:6
    background:Surface {
        implicitWidth:200
        implicitHeight:40
        radius:Theme.fancy ? 14 : 8
        backdrop:null
        color:Theme.fancy ? Theme.alpha(Theme.elevated,.98) : Theme.elevated
        border.color:Theme.highContrast ? Theme.text : Theme.rim
    }
}
