import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Sheet {
    id:preview;objectName:'filePreview';title:info.title||'File preview'
    required property var service
    property var info:({})
    property string account:''
    width:Math.min(1440*Theme.textScale,parent.width-24)
    implicitHeight:parent.height-24
    height:implicitHeight
    function present(value){account=service.accountKey;info=value;open()}
    function clearAndClose(){info=({});close()}
    onClosed:info=({})
    RowLayout {Layout.fillWidth:true;visible:preview.info.kind!=='pdf'
        Label {Layout.fillWidth:true;textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.secondary
            text:preview.info.truncated?'Showing the first 256 KB. Save the original for the complete file.':'Saved on this computer'}
        Capsule {text:'Save as';visible:!!preview.info.key;onClicked:preview.service.saveDownloaded(preview.info.key)}
    }
    Loader {id:content;objectName:'filePreviewLoader';Layout.fillWidth:true;Layout.preferredHeight:Math.max(180,preview.scrollView.height-24)
        active:preview.visible&&!preview.closing&&preview.info.kind==='pdf'
        sourceComponent:Component {PdfFileView {source:preview.info.url||'';canSave:!!preview.info.key;onSaveRequested:preview.service.saveDownloaded(preview.info.key)}}
        visible:preview.info.kind==='pdf'
    }
    Item {Layout.fillWidth:true;Layout.preferredHeight:Math.max(180,preview.scrollView.height-80);visible:preview.info.kind==='image'
        Image {id:picture;objectName:'filePreviewImage';anchors.fill:parent;fillMode:Image.PreserveAspectFit;asynchronous:true;cache:false
            source:preview.visible&&!preview.closing&&preview.info.kind==='image'?preview.info.url:'';sourceSize:Qt.size(2048,2048)
            Accessible.name:preview.info.title||'Image'}
        Label {anchors.centerIn:parent;visible:picture.status===Image.Error;text:'This image could not be opened.';textFormat:Text.PlainText;color:Theme.orange}
    }
    ScrollView {Layout.fillWidth:true;Layout.preferredHeight:Math.max(180,preview.scrollView.height-80);visible:preview.info.kind==='text'
        TextArea {objectName:'filePreviewText';text:preview.info.text||'';textFormat:TextEdit.PlainText;readOnly:true;selectByMouse:true;wrapMode:TextEdit.Wrap;color:Theme.text;Accessible.name:preview.info.title||'Text document'}
    }
    Connections {target:preview.service
        function onChanged(){if(preview.visible&&preview.account!==preview.service.accountKey)preview.clearAndClose()}
    }
}
