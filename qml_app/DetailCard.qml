import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Pane {
    id:card
    property string title:''
    default property alias body:contents.data
    padding:Theme.fancy?18:10
    background:Surface {radius:Theme.fancy?18:5;tracking:card.y}
    contentItem:ColumnLayout {
        id:contents;spacing:Theme.fancy?12:8
        Label {textFormat:Text.PlainText;text:card.title;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text;font.pixelSize:(Theme.fancy?15:12)*Theme.textScale;font.bold:true}
    }
}
