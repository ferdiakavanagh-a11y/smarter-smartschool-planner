import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Popup {
    id: sheet
    property string title: ''
    property var previousFocus
    readonly property var hostWindow:ApplicationWindow.window
    property var beforeClose: function(){return true}
    default property alias body: bodyColumn.data
    property alias scrollView: scroll
    property alias bodyColumn: bodyColumn
    implicitWidth: 560
    implicitHeight: head.implicitHeight+bodyColumn.implicitHeight+24
    width: Math.min(560*Theme.textScale,parent.width-24)
    height: Math.min(implicitHeight,parent.height*.86)
    x: (parent.width-width)/2; y: (parent.height-height)/2
    padding: 0; modal: true; focus: true; popupType: Popup.Item
    closePolicy: Popup.NoAutoClose
    function dismiss(){ if(beforeClose())close() }
    function revealFocus(){
        let item=hostWindow.activeFocusItem, inside=false
        if(item && item.focusReason===Qt.MouseFocusReason)return
        for(let ancestor=item;ancestor;ancestor=ancestor.parent)if(ancestor===bodyColumn){inside=true;break}
        if(!inside)return
        scrollMotion.stop()
        let p=item.mapToItem(scroll,0,0), flick=scroll.contentItem
        if(p.y<8)flick.contentY=Math.max(0,flick.contentY+p.y-8)
        else if(p.y+item.height>scroll.height-8)flick.contentY=Math.min(Math.max(0,flick.contentHeight-flick.height),flick.contentY+p.y+item.height-scroll.height+8)
    }
    onAboutToShow: { previousFocus=ApplicationWindow.window.activeFocusItem; scrollMotion.stop(); scroll.contentItem.cancelFlick(); scroll.contentItem.contentY=0 }
    onClosed: if(previousFocus && previousFocus.visible)previousFocus.forceActiveFocus()
    background: Surface { radius: 30; strong: true; tracking:sheet.x+sheet.y }
    Overlay.modal: Rectangle { color: '#66000000'
        TapHandler { onTapped: point=>{let p=point.scenePosition;if(p.x<sheet.x || p.x>sheet.x+sheet.width || p.y<sheet.y || p.y>sheet.y+sheet.height)sheet.dismiss()} }
    }
    enter: Transition { ParallelAnimation {
        NumberAnimation { property: 'opacity'; from: 0; to: 1; duration: Theme.motion ? 200 : 0; easing.type: Easing.OutCubic }
        NumberAnimation { property: 'scale'; from: .96; to: 1; duration: Theme.motion ? 240 : 0; easing.type: Easing.OutCubic }
    } }
    exit: Transition { ParallelAnimation {
        NumberAnimation { property: 'opacity'; to: 0; duration: Theme.motion ? 140 : 0 }
        NumberAnimation { property: 'scale'; to: .98; duration: Theme.motion ? 140 : 0 }
    } }
    contentItem: ColumnLayout {
        spacing: 0
        Item {
            id: head; objectName: 'sheetHandle'; Layout.fillWidth: true; implicitHeight: Math.max(64,52*Theme.textScale)
            Label {textFormat:Text.PlainText; anchors.left: parent.left; anchors.leftMargin: 20; anchors.verticalCenter: parent.verticalCenter; anchors.right: closeButton.left; anchors.rightMargin: 12
                text: sheet.title; font.pixelSize: 22*Theme.textScale; font.bold: true; color: Theme.text; elide: Text.ElideRight }
            Capsule { id: closeButton; anchors.right: parent.right; anchors.rightMargin: 20; anchors.verticalCenter: parent.verticalCenter
                text: 'Close'; symbol: 'close'; iconOnly: true; onClicked: sheet.dismiss() }
        }
        ScrollView { id: scroll; objectName: 'sheetScroll'; Layout.fillWidth: true; Layout.fillHeight: true; clip: true
            contentWidth: availableWidth; contentHeight: bodyColumn.implicitHeight+24
            SmoothScroll { id:scrollMotion; view:scroll.contentItem }
            ColumnLayout { id: bodyColumn; objectName:'dialogBody'; width: scroll.availableWidth-40; x: 20; spacing: 18 }
        }
    }
    Shortcut { sequence: 'Escape'; enabled: sheet.opened; onActivated: sheet.dismiss() }
    Connections {target:sheet.opened?sheet.hostWindow:null
        function onActiveFocusItemChanged(){Qt.callLater(sheet.revealFocus)}
    }
}
