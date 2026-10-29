import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Popup {
    id: sheet
    property string title: ''
    property real offset: 0
    property bool dragging: false
    property var previousFocus
    readonly property var hostWindow:ApplicationWindow.window
    property var beforeClose: function(){return true}
    default property alias body: bodyColumn.data
    property alias scrollView: scroll
    property alias bodyColumn: bodyColumn
    implicitWidth: 560; implicitHeight: 660
    width: Math.min(560*Theme.textScale,parent.width-24)
    height: Math.min(implicitHeight,parent.height*.86)
    x: (parent.width-width)/2; y: parent.height-height+offset
    padding: 0; modal: true; focus: true; popupType: Popup.Item
    closePolicy: Popup.NoAutoClose
    function dismiss(){ if(beforeClose())close() }
    function interactiveAt(item,point){
        let child=item.childAt(point.x,point.y)
        if(!child)return false
        if(child instanceof AbstractButton || child instanceof TextInput || child instanceof TextEdit || child instanceof Slider || child instanceof ComboBox)return true
        return interactiveAt(child,child.mapFromItem(item,point))
    }
    function settle(velocity){if((offset>40 && offset+velocity*.499>height*.5) || offset>height*.6) dismiss(); offset=0}
    function revealFocus(){
        let item=hostWindow.activeFocusItem, inside=false
        // Keep a pointer's hit target stationary; keyboard focus still reveals clipped controls.
        if(item && item.focusReason===Qt.MouseFocusReason)return
        for(let ancestor=item;ancestor;ancestor=ancestor.parent)if(ancestor===bodyColumn){inside=true;break}
        if(!inside)return
        scrollMotion.stop()
        let p=item.mapToItem(scroll,0,0), flick=scroll.contentItem
        if(p.y<8)flick.contentY=Math.max(0,flick.contentY+p.y-8)
        else if(p.y+item.height>scroll.height-8)flick.contentY=Math.min(Math.max(0,flick.contentHeight-flick.height),flick.contentY+p.y+item.height-scroll.height+8)
    }
    onAboutToShow: { previousFocus=ApplicationWindow.window.activeFocusItem; offset=0 }
    onClosed: if(previousFocus)previousFocus.forceActiveFocus()
    Behavior on offset { enabled: !sheet.dragging && Theme.motion; SpringAnimation { spring: 4; damping: .9; epsilon: .2 } }
    background: Surface { radius: 30; strong: true; tracking:sheet.x+sheet.y }
    Overlay.modal: Rectangle { color: '#66000000'
        TapHandler { onTapped: point=>{let p=point.scenePosition;if(p.x<sheet.x || p.x>sheet.x+sheet.width || p.y<sheet.y || p.y>sheet.y+sheet.height)sheet.dismiss()} }
    }
    enter: Transition { NumberAnimation { property: 'opacity'; from: 0; to: 1; duration: Theme.motion ? 200 : 0 } NumberAnimation { target: sheet; property: 'offset'; from: sheet.height; to: 0; duration: Theme.motion ? 300 : 0; easing.type: Easing.OutCubic } }
    exit: Transition { ParallelAnimation {
        NumberAnimation { property: 'opacity'; to: 0; duration: Theme.motion ? 200 : 0 }
        NumberAnimation { target:sheet;property:'offset';to:sheet.height;duration:Theme.motion?300:0;easing.type:Easing.OutCubic }
    } }
    contentItem: ColumnLayout {
        spacing: 0
        Item {
            id: head; objectName: 'sheetHandle'; Layout.fillWidth: true; implicitHeight: 76
            Rectangle { anchors.top: parent.top; anchors.topMargin: 9; anchors.horizontalCenter: parent.horizontalCenter; width: 40; height: 5; radius: 3; color: Theme.secondary; opacity: .4 }
            Label {textFormat:Text.PlainText; anchors.left: parent.left; anchors.leftMargin: 20; anchors.verticalCenter: parent.verticalCenter; anchors.right: closeButton.left
                text: sheet.title; font.pixelSize: 22*Theme.textScale; font.bold: true; color: Theme.text; elide: Text.ElideRight }
            Capsule { id: closeButton; anchors.right: parent.right; anchors.rightMargin: 20; anchors.verticalCenter: parent.verticalCenter
                text: 'Close'; symbol: 'close'; iconOnly: true; onClicked: sheet.dismiss() }
            DragHandler { id: drag; target: null; xAxis.enabled: false; dragThreshold: 8
                property real start: 0
                onActiveChanged: { sheet.dragging=active; if(active)start=sheet.offset; else sheet.settle(centroid.velocity.y) }
                onActiveTranslationChanged: if(active){let raw=start+activeTranslation.y; sheet.offset=raw<0 ? raw*sheet.height*.55/(sheet.height+.55*Math.abs(raw)) : raw}
                onCanceled: { sheet.dragging=false; sheet.offset=0 }
            }
        }
        ScrollView { id: scroll; objectName: 'sheetScroll'; Layout.fillWidth: true; Layout.fillHeight: true; clip: true
            contentWidth: availableWidth; contentHeight: bodyColumn.implicitHeight+24
            SmoothScroll { id:scrollMotion; view:scroll.contentItem }
            ColumnLayout { id: bodyColumn; width: scroll.availableWidth-40; x: 20; spacing: 18
            }
            Item {
                id:gestureLayer;parent:scroll;anchors.fill:parent
                PointHandler {id:pressGuard;acceptedButtons:Qt.LeftButton}
                DragHandler {id:bodyDrag;objectName:'sheetBodyDrag';target:null;xAxis.enabled:false;dragThreshold:8
                    property real start:0
                    enabled:scroll.contentItem.contentY<=0 && (!pressGuard.point.pressed || !sheet.interactiveAt(bodyColumn,bodyColumn.mapFromItem(gestureLayer,pressGuard.point.pressPosition)))
                    onActiveChanged:{sheet.dragging=active;if(active)start=sheet.offset;else sheet.settle(centroid.velocity.y)}
                    onActiveTranslationChanged:if(active){if(activeTranslation.y<0){sheet.offset=0;return}sheet.offset=start+activeTranslation.y}
                    onCanceled:{sheet.dragging=false;sheet.offset=0}
                }
            }
        }
    }
    Shortcut { sequence: 'Escape'; enabled: sheet.opened; onActivated: sheet.dismiss() }
    Connections {target:sheet.opened?sheet.hostWindow:null
        function onActiveFocusItemChanged(){Qt.callLater(sheet.revealFocus)}
    }
}
