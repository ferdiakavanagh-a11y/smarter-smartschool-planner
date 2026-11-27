import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Sheet {
    id:sheet
    required property var app
    property bool offlineOnly:false
    objectName:offlineOnly?'offlineFiles':'reportCards'
    title:I18n.t(offlineOnly?'Offline files':'Report cards')
    implicitHeight:offlineOnly?Math.min(560*Theme.textScale,app.height*.75):Math.min(620*Theme.textScale,app.height*.8)
    ResourcesView {
        app:sheet.app
        offlineOnly:sheet.offlineOnly
        Layout.fillWidth:true
        Layout.preferredHeight:Math.max(160,sheet.scrollView.height-24)
    }
}
