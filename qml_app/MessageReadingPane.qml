import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: pane
    required property var controller
    readonly property var service: controller.service
    readonly property var message: service ? service.messageDetail : ({})
    readonly property bool current: controller.selectedMessageId !== '' && String(message.id || '') === controller.selectedMessageId
    color: Theme.elevated
    ScrollView {
        anchors { top:parent.top; left:parent.left; right:parent.right; bottom:actions.visible?actions.top:parent.bottom; margins:24 }
        clip:true
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width; spacing: 16
            Label {Layout.fillWidth:true; text:pane.current ? pane.message.subject || I18n.t('Geen onderwerp') : pane.service && pane.service.messageLoading ? I18n.t('Bericht laden…') : I18n.t('Selecteer een bericht'); textFormat:Text.PlainText; wrapMode:Text.Wrap; font.pixelSize:23*Theme.textScale; font.weight:Font.Light; color:Theme.secondary}
            Label {Layout.fillWidth:true; visible:pane.current&&(pane.message.to||[]).length>0; text:I18n.t('Ontvangers: ')+(pane.message.to||[]).join(', '); textFormat:Text.PlainText; wrapMode:Text.Wrap; color:Theme.secondary; font.pixelSize:12*Theme.textScale}
            Label {Layout.fillWidth:true; visible:pane.current&&(pane.message.cc||[]).length>0; text:I18n.t('Kopie: ')+(pane.message.cc||[]).join(', '); textFormat:Text.PlainText; wrapMode:Text.Wrap; color:Theme.secondary}
            Label {Layout.fillWidth:true; visible:pane.current&&pane.message.folder==='outbox'&&(pane.message.bcc||[]).length>0; text:I18n.t('Blinde kopie: ')+(pane.message.bcc||[]).join(', '); textFormat:Text.PlainText; wrapMode:Text.Wrap; color:Theme.secondary}
            RowLayout {visible:pane.current; Layout.fillWidth:true; spacing:12
                Rectangle {width:30; height:30; radius:15; color:Theme.dark?'#344e49':'#d9eadc'
                    Label {anchors.centerIn:parent; text:pane.controller.initials(pane.message.sender); color:Theme.text; font.pixelSize:12}}
                Label {Layout.fillWidth:true; text:(pane.message.sender||'')+'   '+(pane.message.date||''); textFormat:Text.PlainText; wrapMode:Text.Wrap; color:Theme.secondary; font.pixelSize:12*Theme.textScale}
            }
            Rectangle {Layout.fillWidth:true; height:1; color:Theme.separator; visible:pane.current; Layout.topMargin:12; Layout.bottomMargin:12}
            Label {Layout.fillWidth:true; visible:!!pane.service&&!!pane.service.messageError; text:I18n.t(pane.service?pane.service.messageError:''); textFormat:Text.PlainText; wrapMode:Text.Wrap; color:Theme.text}
            Capsule {visible:!!pane.service&&!!pane.service.messageError; text:I18n.t('Opnieuw proberen'); enabled:!!pane.service&&!pane.service.featureBusy; onClicked:pane.controller.readMessage(pane.controller.selectedMessageId)}
            TextArea {id:body; objectName:'inlineMessageBody'; Layout.fillWidth:true; visible:pane.current; text:pane.current?pane.message.body||I18n.t('Geen berichttekst.'):''; textFormat:TextEdit.PlainText; readOnly:true; selectByMouse:true; wrapMode:TextEdit.Wrap; color:Theme.text; font.pixelSize:14*Theme.textScale; padding:0; background:null; Accessible.name:I18n.t('Berichttekst')}
            RowLayout {visible:pane.current&&(pane.message.attachments||[]).length>0; Layout.fillWidth:true; Layout.topMargin:20
                Label {text:I18n.t('Bijlagen'); color:Theme.text; font.bold:true; font.pixelSize:12*Theme.textScale}
                Rectangle {Layout.fillWidth:true; height:1; color:Theme.separator}}
            Repeater {model:pane.current?pane.message.attachments||[]:[]
                ItemDelegate {required property var modelData; Layout.fillWidth:true; implicitHeight:42*Theme.textScale; text:modelData.name||I18n.t('Bijlage'); enabled:!!pane.service&&!pane.service.featureBusy
                    contentItem:RowLayout {spacing:12
                        Icon {name:'file';ink:/\.pdf$/i.test(modelData.name||'')?'#ba2535':Theme.blue}
                        Label {Layout.fillWidth:true; text:modelData.name||I18n.t('Bijlage'); textFormat:Text.PlainText; elide:Text.ElideMiddle; color:Theme.text}
                        Label {text:String(modelData.size||'');textFormat:Text.PlainText;color:Theme.secondary;font.pixelSize:12*Theme.textScale}
                        Icon {name:'download';ink:Theme.blue}}
                    onClicked:pane.service.downloadAttachment('message',String(modelData.id))}
            }
            Repeater {model:pane.current&&pane.service?pane.service.downloadedFiles.filter(f=>f.source==='message'&&f.sourceId===pane.controller.selectedMessageId):[]
                Capsule {required property var modelData; Layout.fillWidth:true; text:I18n.t('Offline · ')+modelData.name; onClicked:pane.controller.showOfflineFile(modelData)}}
        }
    }
    RowLayout {
        id:actions
        visible:pane.current
        anchors { left:parent.left; right:parent.right; bottom:parent.bottom; margins:12 }
        spacing:4
        Capsule {
            objectName:'inline_reply';text:I18n.t('Reply');primary:true
            enabled:!!pane.service&&!pane.service.featureBusy&&!!pane.message.canReply
            onClicked:pane.controller.composeReply('reply','')
        }
        Capsule {
            objectName:'inlineDraftReply'
            readonly property bool compact:pane.width<375*Theme.textScale
            text:compact?'Gemini':I18n.p('Draft with Gemini','Concept met Gemini')
            Accessible.name:I18n.p('Draft with Gemini','Concept met Gemini')
            symbol:compact?'':'ai'
            leftPadding:compact?6:12;rightPadding:leftPadding
            enabled:!!pane.service&&!pane.service.featureBusy&&!!pane.message.canReply
            Accessible.description:I18n.p('Gemini reads this message to draft an editable reply. Nothing is sent automatically.','Gemini gebruikt dit bericht voor een antwoord dat je zelf nog kunt aanpassen. Er wordt niets vanzelf verstuurd.')
            onClicked:pane.controller.app.requestAI('reply')
        }
        Capsule {
            objectName:'inlineReplyOptions';text:I18n.p('More actions','Meer acties');symbol:'more';iconOnly:true
            enabled:!!pane.service&&!pane.service.featureBusy
            onClicked:options.open()
            PlannerMenu {
                id:options
                y:-implicitHeight
                PlannerMenuItem {objectName:'inline_replyAll';text:I18n.t('Reply all');enabled:!!pane.message.canReply;onTriggered:pane.controller.composeReply('replyAll','')}
                PlannerMenuItem {objectName:'inline_forward';text:I18n.t('Forward');onTriggered:pane.controller.composeReply('forward','')}

            }
        }
        Item {Layout.fillWidth:true}
    }
    function copyText(){body.selectAll();body.copy();body.deselect()}
}
