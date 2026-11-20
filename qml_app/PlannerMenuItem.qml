import QtQuick
import QtQuick.Controls

MenuItem {
    id:option
    leftPadding:Theme.smartschool ? 12 : 6
    rightPadding:leftPadding
    Binding {target:option;property:'font.pixelSize';value:14*Theme.textScale;when:Theme.smartschool}
    Binding {target:option.contentItem;property:'color';value:option.enabled ? Theme.text : Theme.secondary;when:Theme.smartschool}
    background:Rectangle {
        implicitWidth:200
        implicitHeight:Theme.smartschool ? 36*Theme.textScale : 40
        radius:Theme.smartschool ? 5 : 0
        color:Theme.smartschool ? (option.down || option.highlighted || option.hovered ? Theme.selection : 'transparent')
                                : (option.highlighted ? option.palette.midlight : 'transparent')
        border.width:Theme.smartschool && option.visualFocus ? 2 : 0
        border.color:Theme.blue
    }
}
