import QtQuick
Item {
    id: wallpaper
    property bool animate: false
    layer.enabled: true
    layer.mipmap: true
    layer.smooth: true
    layer.textureSize: Qt.size(Math.min(1200,width),Math.min(800,height))
    Image { anchors.fill: parent; visible: Theme.matched; source: 'backdrop.svg'; fillMode: Image.Stretch }
    ShaderEffect { anchors.fill: parent; visible: !Theme.matched
    property real phase: 0
    property color base: Theme.bg
    property color blue: Theme.blue
    property color purple: Theme.purple
    property color teal: Theme.teal
    property color warm: Theme.clear ? (Theme.dark ? "#6F9BCB" : "#CFE6FA") : Theme.orange
    property color pink: Theme.pink
    property real dark: Theme.dark ? 1 : 0
    property real preset: Theme.wallpaperIndex
    fragmentShader: "shaders/wallpaper.frag.qsb"
    NumberAnimation on phase {
        from: 0; to: Math.PI * 2; duration: Theme.clear ? 80000 : 52000
        loops: Animation.Infinite; running: wallpaper.animate && Theme.active
    }
}
}
