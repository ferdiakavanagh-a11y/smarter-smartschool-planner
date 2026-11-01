import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Pane {
    id:card
    property string title:''
    default property alias body:contents.data
    padding:18
    background:Surface {radius:18;tracking:card.y}
    contentItem:ColumnLayout {
        id:contents;spacing:12
        Label {textFormat:Text.PlainText;text:card.title;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text;font.pixelSize:15*Theme.textScale;font.bold:true}
    }
}
