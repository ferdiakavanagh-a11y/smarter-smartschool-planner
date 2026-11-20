import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Sheet {
    id:sheet
    objectName:'offlineFileSheet'
    required property var service
    property var entry:({})
    title:I18n.t('Offline file')
    function showFile(file){entry={key:String(file.key),name:String(file.name)};open()}
    Label {text:sheet.entry.name||I18n.t('Downloaded file');textFormat:Text.PlainText;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text;font.bold:true}
    Label {text:I18n.t('Saved on this computer. Removing this copy keeps the original school file.');textFormat:Text.PlainText;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.secondary}
    RowLayout {Layout.fillWidth:true
        Capsule {text:I18n.t('Open');Layout.fillWidth:true;enabled:!!sheet.service&&!sheet.service.featureBusy;onClicked:sheet.service.openDownloaded(String(sheet.entry.key))}
        Capsule {text:I18n.t('Save as');Layout.fillWidth:true;enabled:!!sheet.service;onClicked:sheet.service.saveDownloaded(String(sheet.entry.key))}
        Capsule {text:I18n.t('Remove copy');Layout.fillWidth:true;enabled:!!sheet.service;onClicked:sheet.service.removeDownloaded(String(sheet.entry.key))}
    }
    Connections {target:sheet.service
        function onChanged(){if(sheet.visible&&!sheet.service.downloadedFiles.some(f=>f.key===sheet.entry.key))sheet.close()}
    }
}
