import QtQuick
import QtQuick.Controls

Menu {
    id:menu
    focus:true
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
    Binding {target:menu;property:'popupType';value:Popup.Item;when:Theme.smartschool}
    padding:Theme.smartschool ? 5 : 0
    margins:Theme.smartschool ? 6 : 0
    background:Rectangle {
        implicitWidth:200
        implicitHeight:40
        radius:Theme.smartschool ? 8 : 0
        color:Theme.smartschool ? Theme.elevated : menu.palette.window
        border.color:Theme.smartschool ? (Theme.highContrast ? Theme.text : Theme.separator) : menu.palette.dark
    }
}
