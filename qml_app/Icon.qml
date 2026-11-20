import QtQuick
import "Icons.js" as Icons
Item {
    id: icon
    property string name: "ok"
    property color ink: Theme.text
    Image {
        anchors.fill: parent
        source: Icons.url(icon.name, Qt.rgba(icon.ink.r,icon.ink.g,icon.ink.b,1).toString())
        opacity: icon.ink.a
        sourceSize: Qt.size(Math.ceil(width*2),Math.ceil(height*2))
        fillMode: Image.PreserveAspectFit
    }
    Accessible.ignored: true
    implicitWidth: 20*Theme.textScale; implicitHeight: 20*Theme.textScale
    width: implicitWidth; height: implicitHeight
}
