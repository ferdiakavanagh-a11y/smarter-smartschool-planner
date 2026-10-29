import QtQuick
import "Icons.js" as Icons
Image {
    property string name: "ok"
    property color ink: Theme.text
    source: Icons.url(name, Qt.rgba(ink.r,ink.g,ink.b,1).toString())
    opacity: ink.a
    sourceSize: Qt.size(32,32)
    width: 24; height: 24
}
