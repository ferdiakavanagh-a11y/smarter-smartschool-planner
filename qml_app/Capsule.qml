import QtQuick
import QtQuick.Controls
Button {
    id: control
    property bool selected: false
    property bool quiet: false
    property string symbol: ""
    property bool iconOnly: false
    property bool primary: false
    property var backdrop: Theme.backdrop
    property bool selectorMaterial: false
    property real glassTracking: 0
    readonly property color labelInk: Theme.highContrast && (selected || primary) ? (Theme.dark && Theme.clear ? '#102438' : 'white') : Theme.text
    implicitHeight: 38
    font.pixelSize: 13 * Theme.textScale; font.weight: Font.DemiBold
    leftPadding: 16; rightPadding: 16
    Accessible.name: text
    Accessible.selected: selected
    hoverEnabled: true
    GlassToolTip {requested:(control.iconOnly||label.truncated)&&(control.hovered||control.visualFocus);text:control.text;delay:600}
    implicitWidth: iconOnly ? 38 : Math.max(50, contentItem.implicitWidth + leftPadding + rightPadding)
    Keys.onReturnPressed: { if (checkable) checked = !checked; clicked() }
    background: ButtonGlass {
        control: control
        selectorMaterial:control.selectorMaterial
        selected: control.selected || control.primary
        backdrop:control.backdrop
        tracking:control.glassTracking
    }
    contentItem: Item {
        implicitWidth: label.implicitWidth + (control.symbol && !control.iconOnly ? 28 : 0)
        implicitHeight: Math.max(20,label.implicitHeight)
        Icon { visible: control.symbol !== ""; name: control.symbol; width: 20; height: 20
            anchors.verticalCenter: parent.verticalCenter; x: control.iconOnly ? (parent.width-width)/2 : 0
            ink: control.labelInk }
        Text {textFormat:Text.PlainText; id: label; visible: !control.iconOnly; text: control.iconOnly ? "" : control.text
            anchors.fill: parent; anchors.leftMargin: control.symbol && !control.iconOnly ? 28 : 0
            color: control.labelInk; font: control.font
            elide: Text.ElideRight
            horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
    }
}
