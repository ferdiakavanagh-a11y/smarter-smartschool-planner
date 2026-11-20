import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: progress
    objectName: "syncDialog"
    required property var app
    required property var backdrop
    font.family: "Segoe UI Variable"
    property string action: "sync"
    readonly property bool animate: visible && app.renderActive && app.active && Theme.motion
    readonly property string heading: action === "setup" ? I18n.t("Waiting for account details")
        : action === "install" ? I18n.t("Preparing your update")
        : app.production ? I18n.t("Syncing your planner") : I18n.t("Refreshing your workspace")
    readonly property string explanation: action === "setup" ? I18n.t("Complete the account window to continue.")
        : action === "install" ? I18n.t("The planner will close when the update is ready.")
        : app.production ? I18n.t("Fetching your latest assignments, schedule, grades and LVS.")
        : I18n.t("Updating the synthetic planner data.")
    property var previousFocus
    visible: app.busy
    modal: true
    focus: true
    closePolicy: Popup.NoAutoClose
    popupType: Popup.Item
    padding: 28
    width: Math.min(460 * Theme.textScale, app.width - 40)
    height: Math.min(contentItem.implicitHeight + 2 * padding, app.height - 40)
    x: (app.width - width) / 2
    y: (app.height - height) / 2
    onAboutToShow: { previousFocus = app.activeFocusItem; body.contentItem.contentY = 0 }
    onClosed: if (previousFocus && previousFocus.visible) previousFocus.forceActiveFocus()
    background: Item {
        SelectorLens { anchors.fill:parent;visible:Theme.fancy;backdrop:progress.backdrop;radius:32;blur:5*progress.opacity }
        Rectangle {objectName:'syncOpaqueSurface';anchors.fill:parent;visible:!Theme.fancy;radius:32;color:Theme.elevated;border.color:Theme.rim}
    }
    Overlay.modal: Rectangle { color: Theme.alpha(Theme.bg, .48) }
    enter: Transition { ParallelAnimation {
        NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.motion ? 200 : 0; easing.type: Easing.OutCubic }
        NumberAnimation { property: "scale"; from: .96; to: 1; duration: Theme.motion ? 240 : 0; easing.type: Easing.OutCubic }
    } }
    exit: Transition { ParallelAnimation {
        NumberAnimation { property: "opacity"; to: 0; duration: Theme.motion ? 140 : 0 }
        NumberAnimation { property: "scale"; to: .98; duration: Theme.motion ? 140 : 0; easing.type: Easing.InCubic }
    } }
    contentItem: ScrollView {
        id: body
        implicitHeight: column.implicitHeight
        contentWidth: availableWidth; contentHeight: column.implicitHeight
        clip: true; focus: true
        Keys.onPressed: event=>{
            if([Qt.Key_Up,Qt.Key_Down,Qt.Key_PageUp,Qt.Key_PageDown,Qt.Key_Home,Qt.Key_End].indexOf(event.key)<0)return
            let view=body.contentItem,limit=Math.max(0,view.contentHeight-view.height)
            let step=event.key===Qt.Key_Up?-40:event.key===Qt.Key_Down?40:event.key===Qt.Key_PageUp?-view.height:view.height
            view.contentY=event.key===Qt.Key_Home?0:event.key===Qt.Key_End?limit:Math.max(0,Math.min(limit,view.contentY+step))
            event.accepted=true
        }
        Accessible.role: Accessible.Dialog
        Accessible.name: progress.heading
        Accessible.description: progress.explanation
        ColumnLayout {
        id: column
        width: body.availableWidth; spacing: 16
        Item {
            objectName: "syncVisual"
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: 6
            implicitWidth: 144; implicitHeight: 124
            Accessible.ignored: true
            Rectangle {
                objectName: "syncOrbitRing"
                anchors.centerIn: parent; width: 110; height: 110; radius: 55
                color: "transparent"
                border.color: Theme.alpha(Theme.blue, Theme.highContrast ? .8 : .12)
            }
            Item {
                id: orbit;objectName: "syncOrbit"
                anchors.centerIn: parent; width: 110; height: 110
                visible: progress.action !== "setup"
                RotationAnimator on rotation {
                    objectName: "syncOrbitSpin"
                    from: 0; to: 360; duration: 2400; loops: Animation.Infinite
                    running: progress.animate && progress.action !== "setup"
                }
                Repeater {
                    model: 3
                    Item {
                        required property int index
                        anchors.fill: parent; rotation: index * 120
                        Rectangle {
                            anchors.horizontalCenter: parent.horizontalCenter; y: -3
                            width: 7; height: 7; radius: 3.5
                            color: Theme.highContrast ? Theme.text : [Theme.blue, Theme.teal, Theme.purple][parent.index]
                        }
                    }
                }
            }
            Rectangle {
                objectName: "syncBackplate"
                anchors.centerIn: parent; anchors.verticalCenterOffset: 5
                width: 72; height: 72; radius:24; rotation: -9
                color: Theme.fancy ? Theme.alpha(Theme.blue, Theme.highContrast ? 0 : .09) : Qt.tint(Theme.elevated, Theme.alpha(Theme.blue, Theme.highContrast ? 0 : .09))
                border.color: Theme.alpha(Theme.blue, Theme.highContrast ? 0 : .2)
            }
            SelectorLens {
                visible:Theme.fancy
                anchors.centerIn: parent; width: 72; height: 72; radius:24
                backdrop: progress.backdrop; strength: 18; blur: 5; tint: .18
            }
            Rectangle {
                objectName: "syncTile"
                anchors.centerIn: parent; width: 72; height: 72; radius:24
                color: !Theme.fancy || Theme.highContrast ? Theme.elevated : Theme.alpha(Theme.elevated, .38)
                border.color: Theme.highContrast ? Theme.text : Theme.alpha(Theme.blue, .2)
                Icon {
                    objectName: "syncDialogGlyph"
                    anchors.centerIn: parent; width: 30; height: 30
                    name: progress.action === "setup" ? "settingsBtn" : "syncBtn"
                    ink: Theme.highContrast ? Theme.text : Theme.blue
                    RotationAnimator on rotation { objectName:"syncDialogSpin";from: 0; to: 360; duration: 1800; loops: Animation.Infinite
                        running: progress.animate && progress.action !== "setup" }
                }
            }
        }
        Label {
            Layout.fillWidth: true; Layout.topMargin: 6
            textFormat: Text.PlainText; text: progress.heading
            objectName: "syncHeading"
            font.pixelSize: 22 * Theme.textScale; font.weight: Font.DemiBold
            horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap; color: Theme.text
        }
        Label {
            Layout.fillWidth: true
            textFormat: Text.PlainText; text: progress.explanation
            horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap
            color: Theme.secondary; font.pixelSize: 14 * Theme.textScale
        }
        Rectangle {
            id: track
            Layout.fillWidth: true; Layout.topMargin: 6; Layout.bottomMargin: 4
            implicitHeight: 4; radius: 2; clip: true
            visible: progress.action !== "setup"
            color: Theme.highContrast ? Theme.alpha(Theme.text, .25) : Theme.alpha(Theme.blue, .13)
            Accessible.role: Accessible.ProgressBar
            Accessible.name: progress.heading
            Rectangle {
                width: track.width * .3; height: track.height; radius: height / 2
                x: (track.width - width) / 2
                color: Theme.highContrast ? Theme.text : Theme.blue
                // Indeterminate motion reflects activity, never an invented completion percentage.
                XAnimator on x {
                    objectName: "syncIndeterminate"
                    from: -track.width * .3; to: track.width; duration: 1600; loops: Animation.Infinite
                    running: progress.animate && progress.action !== "setup"; easing.type: Easing.InOutCubic
                }
            }
        }
        }
    }
}
