import QtQuick
import QtQuick.Controls
import QtQuick.Shapes
import "ResultPalette.js" as ResultPalette
Item {
    id:ring
    property var entry:({})
    property bool large:false
    readonly property string percentage:entry.percentText||(/%$/.test(entry.extra||'')?entry.extra:'')
    readonly property real value:Math.max(0,Math.min(100,ResultPalette.percent(entry)||0))
    readonly property color ink:ResultPalette.ink(entry,Theme.dark)
    readonly property bool colorOnly:!!entry.square
    implicitWidth:(large?120:42)*Theme.textScale
    implicitHeight:colorOnly?(large?48:32)*Theme.textScale:implicitWidth
    Rectangle {visible:ring.large&&!ring.colorOnly;anchors.fill:parent;radius:width/2;color:Theme.elevated;border.color:Theme.separator;border.width:1}
    Rectangle {visible:ring.large&&!ring.colorOnly;anchors.fill:parent;anchors.margins:14*Theme.textScale;radius:width/2;color:Theme.alpha(ring.ink,.08)}
    Shape {visible:!ring.colorOnly;anchors.fill:parent;antialiasing:true;preferredRendererType:Shape.CurveRenderer
        ShapePath {fillColor:'transparent';strokeColor:Theme.alpha(ring.ink,.17);strokeWidth:(ring.large?8:4)*Theme.textScale
            PathAngleArc {centerX:ring.width/2;centerY:ring.height/2;radiusX:Math.max(0,ring.width/2-5*Theme.textScale);radiusY:radiusX;startAngle:0;sweepAngle:360}
        }
        ShapePath {fillColor:'transparent';strokeColor:ring.ink;strokeWidth:(ring.large?8:4)*Theme.textScale;capStyle:ShapePath.RoundCap
            PathAngleArc {centerX:ring.width/2;centerY:ring.height/2;radiusX:Math.max(0,ring.width/2-5*Theme.textScale);radiusY:radiusX;startAngle:-90;sweepAngle:360*ring.value/100}
        }
    }
    Rectangle {
        visible:ring.colorOnly
        anchors.centerIn:parent
        width:(ring.large?36:20)*Theme.textScale
        height:width
        radius:4*Theme.textScale
        color:ring.entry.square||'transparent'
        border.color:Theme.separator
        Accessible.role:Accessible.StaticText
        Accessible.name:ring.entry.resultLabel||I18n.p('Grade color','Beoordelingskleur')
    }
    Label {anchors.fill:parent;anchors.margins:8;visible:!ring.colorOnly;text:ring.large?((ring.entry.extra||'—')+(ring.percentage?'\n'+ring.percentage:'')):(ring.percentage||ring.entry.extra||'—');textFormat:Text.PlainText;color:Theme.text;horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter;wrapMode:Text.Wrap;font.pixelSize:(ring.large?19:10)*Theme.textScale;Accessible.name:ring.entry.resultLabel||text}
}
