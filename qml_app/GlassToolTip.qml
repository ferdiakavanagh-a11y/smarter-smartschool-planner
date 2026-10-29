import QtQuick
import QtQuick.Controls
ToolTip {
    id: tip
    objectName: 'glassToolTip'
    property bool requested: false
    readonly property var hostWindow: ApplicationWindow.window
    visible: requested && text.length>0 && parent && parent.visible && Theme.active
    popupType: Popup.Item
    margins: 8; padding: 10; delay: 300; timeout: 6000
    width: Math.min(implicitWidth,hostWindow?hostWindow.width-32:720)
    transformOrigin: y<0?Popup.Bottom:Popup.Top
    onAboutToShow: {
        if(!hostWindow)return
        if(hostWindow.activeToolTip && hostWindow.activeToolTip!==tip)hostWindow.activeToolTip.close()
        hostWindow.activeToolTip=tip
    }
    onClosed: if(hostWindow && hostWindow.activeToolTip===tip)hostWindow.activeToolTip=null
    contentItem: Text {textFormat:Text.PlainText;text:tip.text;color:Theme.text;font.pixelSize:13*Theme.textScale;wrapMode:Text.Wrap}
    background: SelectorLens {backdrop:Theme.backdrop;radius:Math.min(18,height/2)}
    enter: Transition {ParallelAnimation {
        NumberAnimation {property:'opacity';from:0;to:1;duration:Theme.motion?160:0;easing.type:Easing.OutCubic}
        NumberAnimation {property:'scale';from:.96;to:1;duration:Theme.motion?180:0;easing.type:Easing.OutCubic}
    }}
    exit: Transition {ParallelAnimation {
        NumberAnimation {property:'opacity';to:0;duration:Theme.motion?100:0}
        NumberAnimation {property:'scale';to:.98;duration:Theme.motion?100:0;easing.type:Easing.OutCubic}
    }}
}
