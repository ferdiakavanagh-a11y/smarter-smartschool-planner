import QtQuick
import QtQuick.Controls

MenuItem {
    id:option
    leftPadding:12
    rightPadding:leftPadding
    font.pixelSize:14*Theme.textScale
    Binding {target:option.contentItem;property:'color';value:option.enabled ? Theme.text : Theme.secondary}
    background:Rectangle {
        implicitWidth:200
        implicitHeight:36*Theme.textScale
        radius:Theme.fancy ? 8 : 5
        color:option.down ? Theme.fill : option.highlighted || option.hovered ? Theme.alpha(Theme.blue,.18) : 'transparent'
        border.width:option.visualFocus ? 2 : 0
        border.color:Theme.blue
    }
}
