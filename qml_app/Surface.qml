import QtQuick
Rectangle {
    id: panel
    property bool strong: false
    property bool control: false
    property bool sheen: true
    property var backdrop: Theme.backdrop
    property bool continuous: false
    property real tracking: 0
    property real refraction: 28
    radius: 32
    color: Theme.highContrast ? Theme.elevated : backdrop ? 'transparent' : Theme.surface
    border.color: Theme.rim; border.width: Theme.highContrast ? 1.5 : backdrop ? 0 : 1
    Rectangle { visible: panel.sheen && !panel.backdrop; anchors.fill: parent; anchors.margins: 1; radius: Math.max(0,panel.radius - 1)
        topLeftRadius: Math.max(0,panel.topLeftRadius-1); topRightRadius: Math.max(0,panel.topRightRadius-1)
        bottomLeftRadius: Math.max(0,panel.bottomLeftRadius-1); bottomRightRadius: Math.max(0,panel.bottomRightRadius-1)
        gradient: Gradient {
            GradientStop { position: 0; color: Theme.dark ? (panel.control ? "#38ffffff" : "#14ffffff") : "#40ffffff" }
            GradientStop { position: panel.control ? .26 : .4; color: "transparent" }
            GradientStop { position: 1; color: panel.control && Theme.dark ? "#30000000" : "#04ffffff" }
        }
    }
    Glass {visible:panel.backdrop!==null;anchors.fill:parent;anchors.margins:panel.border.width
        backdrop:panel.backdrop;tracking:panel.tracking;radius:Math.max(0,panel.radius-1)
        strength:panel.refraction;bezel:panel.continuous?10:26
        magnification:panel.continuous?0:opticalStrength/22*.05
        surfaceColor:Theme.elevated
        tint:panel.strong?.12:.04
        blur:0;rim:.32;ring:-.5;shadow:.55;flatInner:1;sheen:0
    }
}
