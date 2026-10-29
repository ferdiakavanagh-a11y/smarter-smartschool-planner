import QtQuick
// MacShell's grow-and-settle lens, shared by native controls without per-button captures.
Item {
    id: surface
    objectName: "buttonGlass"
    required property var control
    property var backdrop: Theme.backdrop
    property bool selected: !!control.checked
    property color accent: Theme.blue
    property real radius: height / 2
    property real tracking: 0
    property bool selectorMaterial: false
    property real pressT: control.down && control.enabled && Theme.motion ? 1 : 0
    property real hoverT: control.hovered && control.enabled ? 1 : 0
    visible: control.opacity > 0
    opacity: control.enabled ? 1 : .45
    Behavior on pressT { enabled: Theme.motion; NumberAnimation { duration: surface.control.down ? 140 : 240; easing.type: Easing.OutCubic } }
    Behavior on hoverT { NumberAnimation { duration: Theme.motion ? 160 : 0 } }
    Loader {
        id: lens
        x: -Math.min(10,surface.height*.18)*surface.pressT/2
        y: -surface.height*.08*surface.pressT/2
        width: surface.width-2*x; height: surface.height-2*y
        property real radius: surface.radius+surface.height*.04*surface.pressT
        sourceComponent:surface.selectorMaterial?selector:button
        Component {id:selector
            SelectorLens {z:-1;radius:lens.radius;backdrop:surface.backdrop;tracking:surface.tracking;rim:.26+(Theme.fancy?.04*surface.hoverT:0)}
        }
        Component {id:button
            Glass {z:-1;radius:lens.radius;backdrop:surface.backdrop;tracking:surface.tracking
                surfaceColor:surface.selected?surface.accent:Theme.elevated
                tint:surface.selected?.25:.035+.015*surface.hoverT
                strength:30+8*surface.pressT;rim:.3+.08*surface.hoverT;ring:-.7
                blur:0;sheen:0;shadow:.65;flatInner:1
            }
        }
        Rectangle { objectName:'selectionWash';anchors.fill:parent;radius:lens.radius;border.width:0;color:surface.selected?Theme.alpha(surface.accent,Theme.dark?.32:.24):'transparent'
            Behavior on color {ColorAnimation{duration:Theme.motion?160:0}} }
        Rectangle { anchors.fill: parent; radius: lens.radius; visible: Theme.highContrast
            color: surface.selected ? surface.accent : Theme.elevated; border.color: Theme.text }
        Rectangle { anchors.fill: parent; radius: lens.radius; color: "transparent"
            border.width: surface.control.visualFocus ? 2 : 0; border.color: Theme.text }
    }
}
