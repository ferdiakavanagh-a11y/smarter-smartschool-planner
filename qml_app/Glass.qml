import QtQuick
// Padded slab and optical parameters adapted from MacShell GlassSlab.qml (MIT).
Item {
    id: glass
    objectName: "glassSurface"
    required property var backdrop
    property bool fancy: Theme.fancy
    property real radius: height / 2
    property real bezel: Math.min(height*.36,26)
    property real strength: 22
    property real magnification: opticalStrength/22*.05
    property real tint: .22
    property color surfaceColor: Theme.elevated
    property real blur: 0
    property real rim: .3
    property real shadow: .5
    property real flatInner: 0
    property real sheen: 0
    property real ring: -.6
    property bool failed: false
    property real tracking: 0
    readonly property real shadowPadding: Math.min(width,height)>80 ? 16 : 10
    readonly property real opticalStrength: Theme.matched ? 0 : strength * 1.5 * Theme.refractionLevel
    Rectangle {
        anchors.fill: parent; radius: glass.radius
        color: Theme.highContrast ? Theme.elevated : Theme.surface; border.color: Theme.rim
        visible: glass.failed || Theme.highContrast
    }
    Loader {
        anchors.fill: parent
        active: glass.visible && Theme.active && !glass.failed && !Theme.highContrast && glass.backdrop !== null
        sourceComponent: Item {
            ShaderEffect {
                x: -glass.shadowPadding; y: -glass.shadowPadding
                width: glass.width+2*glass.shadowPadding; height: glass.height+2*glass.shadowPadding
                fragmentShader: "shaders/glass.frag.qsb"
                property var src: glass.backdrop
                property vector2d itemSize: Qt.vector2d(width,height)
                property vector2d glassSize: Qt.vector2d(glass.width,glass.height)
                property vector2d srcSize: Qt.vector2d(Math.max(1,glass.backdrop.width),Math.max(1,glass.backdrop.height))
                property vector2d srcOffset: {
                    let geometry = glass.tracking+glass.x+glass.y+glass.parent.x+glass.parent.y+glass.backdrop.x+glass.backdrop.y+glass.backdrop.width+glass.backdrop.height
                    // Refraction stays registered to the wallpaper while ancestors scroll or slide.
                    for(let item=glass.parent;item;item=item.parent){
                        geometry+=item.x+item.y+item.width+item.height+item.scale+item.rotation
                        geometry+=item.glassMotion||0
                    }
                    let p = glass.mapToItem(glass.backdrop,0,0)
                    return Qt.vector2d(p.x-glass.shadowPadding,p.y-glass.shadowPadding)
                }
                property real pad: glass.shadowPadding
                property real radius: glass.radius
                property real bezel: glass.bezel
                property real thickness: glass.opticalStrength*1.6
                property real dispersion: glass.opticalStrength/22*.06
                property real magnify: glass.magnification
                property real blurPx: Theme.matched ? 0 : glass.blur
                property real tintMix: glass.tint
                property real saturation: 1.15
                property real dark: Theme.dark ? 1 : 0
                property real debug: 0
                property real rim: glass.rim
                property real grain: glass.fancy && glass.sheen>.5 ? .004 : 0
                property real shadowAmt: glass.shadow
                property real rimTint: .65
                property real ringW: glass.ring
                property real flatInner: glass.flatInner
                property real sheen: glass.sheen
                property real frost: Theme.matched ? 0 : Math.max(0,Math.min(1,Theme.glassLevel))
                property color surfaceColor: glass.surfaceColor
                property real quality: glass.fancy ? 1 : 0
                onStatusChanged: if (status === ShaderEffect.Error) { console.error("Glass shader:",log); glass.failed=true }
            }
        }
    }
}
