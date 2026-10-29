import QtQuick
import QtQuick.Controls
ComboBox {
    id: picker
    property var backdrop: Theme.backdrop
    property bool selectorMaterial: false
    property bool pointerMotion: false
    readonly property real occupiedWidth: menu.visible?menu.width:width
    PointHandler { onActiveChanged:if(active)picker.pointerMotion=true }
    Keys.onPressed: event=>{picker.pointerMotion=false;event.accepted=false}
    implicitHeight: 40
    leftPadding: 16; rightPadding: 30
    font.pixelSize: 13*Theme.textScale; font.weight: Font.DemiBold
    background: ButtonGlass { control: picker;backdrop:picker.backdrop;selectorMaterial:picker.selectorMaterial;opacity:menu.visible?0:1 }
    contentItem: Text {textFormat:Text.PlainText; text: picker.displayText; font: picker.font; color: Theme.text; elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter;opacity:menu.visible?1-menu.reveal:1 }
    indicator: Icon { name: 'chevron'; width: 14; height: 14; ink: Theme.secondary
        opacity:menu.visible?1-menu.reveal:1
        anchors.right: parent.right; anchors.rightMargin: 13; anchors.verticalCenter: parent.verticalCenter
        rotation: picker.popup.visible ? 180 : 0
        Behavior on rotation { NumberAnimation { duration: Theme.motion?180:0; easing.type: Easing.OutCubic } } }
    delegate: ItemDelegate {
        id: option
        enabled:menu.visible
        required property int index
        required property var modelData
        width: picker.popup.width-12; height: 40*Theme.textScale
        text: modelData; font: picker.font
        highlighted: picker.highlightedIndex===index
        leftPadding: 12; rightPadding: 26
        background: Item {
            Rectangle { anchors.fill: parent; radius: 12; color: Theme.alpha(Theme.text, .1); visible: option.highlighted }
            Rectangle { x:12; y:parent.height-1; width:parent.width-24; height:1; color:Theme.alpha(Theme.text,.08); visible:option.index<picker.count-1 }
        }
        contentItem: Text {textFormat:Text.PlainText; text: option.text; font: option.font; color: Theme.text; elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter }
        Icon { name:'ok'; width:14; height:14; anchors.right:parent.right; anchors.rightMargin:8; anchors.verticalCenter:parent.verticalCenter; visible:option.index===picker.currentIndex }
    }
    popup: Popup {
        id:menu;objectName:'glassMenu'
        property real reveal: 0
        readonly property bool animate:Theme.motion&&picker.pointerMotion
        readonly property real expandedWidth:Math.max(picker.width,190*Theme.textScale)
        readonly property real expandedHeight:Math.min(240,contentItem.implicitHeight+12)
        y:0;width:picker.width+(expandedWidth-picker.width)*reveal;height:picker.height+(expandedHeight-picker.height)*reveal
        padding: 6; focus:true; popupType:Popup.Item
        onAboutToShow:if(!animate)reveal=1
        onClosed:{reveal=0;picker.pointerMotion=false}
        background: Item {
            // Morph only the optical surface; menu labels keep their native size and hit targets.
            SelectorLens {objectName:'menuGlass';backdrop:picker.backdrop
                blur:picker.selectorMaterial?5*menu.reveal:0
                x:0;y:0
                width:menu.width;height:menu.height
                radius:picker.height/2+(22-picker.height/2)*menu.reveal
            }
        }
        contentItem: ListView {implicitHeight:contentHeight;model:menu.visible?picker.delegateModel:null;currentIndex:picker.highlightedIndex;clip:true;spacing:0
            opacity:Math.max(0,Math.min(1,(menu.reveal-.55)/.45))
            Keys.onPressed:event=>{picker.pointerMotion=false;event.accepted=false}
        }
        enter: Transition {NumberAnimation {target:menu;property:'reveal';to:1;duration:menu.animate?220:0;easing.type:Easing.OutCubic}}
        exit: Transition {NumberAnimation {target:menu;property:'reveal';to:0;duration:menu.animate?160:0;easing.type:Easing.OutCubic}}
    }
}
