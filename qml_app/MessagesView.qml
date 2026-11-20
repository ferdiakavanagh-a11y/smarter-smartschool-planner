import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ColumnLayout {
    id: view
    required property var app
    readonly property var service: app.production ? backend.features : null
    readonly property bool localDrafts:service&&service.messageFolder==='local'
    readonly property var folderIds:['inbox','outbox','local','trash','scheduled','draft']
    readonly property var folderLabels:[I18n.t('Inbox'),I18n.t('Sent'),I18n.t('Local drafts'),I18n.t('Trash'),I18n.t('Scheduled'),I18n.t('School drafts')]
    readonly property string selectedMessageId:reader.requestedId
    function showOfflineFile(file){fileSheet.showFile(file)}
    function initials(name){let parts=String(name||'?').trim().split(/\s+/);return (Array.from(parts[0])[0]+(parts.length>1?Array.from(parts[parts.length-1])[0]:'')).toUpperCase()}
    readonly property var messages: !service?[]:localDrafts?service.composer.savedDrafts.map(d=>Object.assign({},d,{sender:d.recipientSummary||I18n.t('No recipients selected'),date:d.updatedAt||'',preview:d.body||'',unread:false,hasAttachments:(d.attachments||[]).length>0})):service.messages
    property var previewMessage: ({})
    readonly property bool readerVisible:reader.visible
    readonly property bool composerVisible:composer.visible
    readonly property string draftAccount:service?service.accountKey:''
    onDraftAccountChanged:{view.previewMessage=({});if(reader)reader.requestedId='';if(reader)reader.close();if(fileSheet)fileSheet.close()}
    function focusSearch(){if(Theme.fancy)search.forceActiveFocus();else {inlineSearch.visible=true;inlineSearch.forceActiveFocus()}}
    readonly property bool canRefresh:!!service&&!localDrafts&&!service.featureBusy
    function refreshMessages(){if(canRefresh)service.loadMessages()}
    function flushDraft(){return !service||service.composer.flushForExit()}
    function focusDraft(){composer.open()}
    function readMessage(id){
        if(localDrafts){list.forceActiveFocus(Qt.TabFocusReason);if(service.composer.resumeDraft(String(id))||service.composer.error)composer.open();return}
        reader.requestedId=String(id);service.clearReply();if(service.openMessage(reader.requestedId)&&Theme.fancy)reader.open()
    }
    function composeReply(mode,body){
        if(reader.current&&service.composer.prepareReply(mode,reader.message,body||'')){
            let origin=reader.previousFocus;composer.open();if(origin&&origin.visible)composer.previousFocus=origin;reader.close()
        }else if(service.composer.error)composer.open()
    }
    function changeFolder(index){
        if(service.selectMessageFolder(folderIds[index])){view.previewMessage=({});reader.requestedId='';reader.close();fileSheet.close();service.loadMessages()}
    }
    readonly property var filteredMessages: {
        let query=search.text.trim().toLocaleLowerCase(), rows=[]
        for(let message of messages)
            if(!query||(message.subject+' '+message.sender+' '+(message.preview||'')).toLocaleLowerCase().includes(query))rows.push(message)
        return rows
    }
    spacing:Theme.fancy?12:6
    RowLayout {
        visible:Theme.fancy;Layout.fillWidth:true
        GlassComboBox {visible:Theme.fancy;objectName:'messageFolder';model:view.folderLabels;currentIndex:view.service?Math.max(0,view.folderIds.indexOf(view.service.messageFolder)):0;enabled:!!view.service&&!view.service.featureBusy
            Accessible.name:I18n.t('Message folder');onActivated:view.changeFolder(currentIndex)}
        Label {text:view.localDrafts?I18n.t('Saved on this computer'):view.messages.length+I18n.t(' messages loaded');textFormat:Text.PlainText;color:Theme.secondary;Layout.fillWidth:true;wrapMode:Text.Wrap}
        Capsule {objectName:'newMessage';text:I18n.t('New message');symbol:'message';enabled:!!view.service;onClicked:if(view.service.composer.newDraft()||view.service.composer.error)composer.open()}
        Capsule {objectName:'refreshMessages';visible:!view.localDrafts;text:service&&service.featureBusy?I18n.t('Loading…'):I18n.t('Refresh');symbol:'syncBtn';enabled:!!service&&!service.featureBusy;onClicked:service.loadMessages()}
    }
    Label {Layout.fillWidth:true;visible:!!view.service&&view.service.messageActionsBlocked;text:I18n.t('Refresh this folder to confirm the previous message action before trying again.');textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.text}
    TextField {id:search;objectName:'messageSearch';visible:Theme.fancy;Layout.fillWidth:true;implicitHeight:Theme.fancy?44:34;placeholderText:I18n.t('Search subjects or senders');Accessible.name:I18n.t('Search Smartschool messages');selectByMouse:true;color:Theme.text;placeholderTextColor:Theme.secondary;leftPadding:16;background:Surface {radius:Theme.fancy?22:3}}
    RowLayout {Layout.fillWidth:true;Layout.fillHeight:true;spacing:0
    Rectangle {visible:!Theme.fancy;Layout.preferredWidth:view.width<1000?156:Math.min(270,view.width*.20);Layout.fillHeight:true;color:Theme.fill
        ColumnLayout {anchors.fill:parent;anchors.margins:20;spacing:2
            Item {height:8}
            Repeater {model:view.folderLabels
                ItemDelegate {required property string modelData;required property int index;Layout.fillWidth:true;implicitHeight:34*Theme.textScale;text:modelData
                    enabled:!!view.service&&!view.service.featureBusy
                    background:Rectangle {color:parent.hovered?Theme.selection:'transparent'}
                    contentItem:RowLayout {spacing:10
                        Icon {name:['inbox','sent','drafts','trash','clock','note'][index];ink:['#298bb5','#55a52b','#db9f24','#89858f','#548eb6','#55a52b'][index];Layout.alignment:Qt.AlignVCenter}
                        Label {text:modelData;color:Theme.text;font.bold:!!view.service&&view.service.messageFolder===view.folderIds[index];font.pixelSize:12*Theme.textScale;Layout.fillWidth:true;elide:Text.ElideRight}
                        Label {text:view.service&&view.service.messageFolder===view.folderIds[index]?String(view.localDrafts?view.messages.length:view.messages.filter(m=>m.unread).length):'';color:Theme.secondary;font.pixelSize:11*Theme.textScale}}
                    onClicked:view.changeFolder(index)}
            }
            Rectangle {Layout.fillWidth:true;height:1;color:Theme.separator;Layout.topMargin:20;Layout.bottomMargin:14}
            Item {Layout.fillHeight:true}
            Label {text:I18n.t('Lokale concepten blijven op dit apparaat.');color:Theme.secondary;Layout.fillWidth:true;wrapMode:Text.Wrap;font.pixelSize:11*Theme.textScale}
        }
    }
    ColumnLayout {Layout.fillHeight:true;Layout.fillWidth:Theme.fancy;Layout.preferredWidth:Theme.fancy?-1:Math.min(430,view.width*.34);spacing:0
        RowLayout {visible:!Theme.fancy;Layout.fillWidth:true;Layout.margins:16
            Label {text:view.service?view.folderLabels[Math.max(0,view.folderIds.indexOf(view.service.messageFolder))]:I18n.t('Berichten');color:Theme.secondary;font.pixelSize:22*Theme.textScale;font.weight:Font.Light;Layout.fillWidth:true;elide:Text.ElideRight}
            Capsule {
                objectName:'smartschoolRefreshMessages';visible:!view.localDrafts
                text:I18n.t('Refresh');symbol:'syncBtn';iconOnly:view.width<1000*Theme.textScale
                enabled:view.canRefresh;onClicked:view.refreshMessages()
            }
        }
        TextField {id:inlineSearch;visible:false;Layout.fillWidth:true;Layout.margins:12;placeholderText:I18n.t('Onderwerp of afzender');color:Theme.text;onTextChanged:search.text=text;selectByMouse:true;Accessible.name:I18n.t('Zoeken in berichten');background:Surface {radius:2}}
    ListView {
        id:list;objectName:'messageList';Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:Theme.fancy?10:0;bottomMargin:(Theme.fancy?100:12)*Theme.textScale
        model:view.filteredMessages;reuseItems:true;boundsBehavior:Flickable.StopAtBounds;activeFocusOnTab:true
        ScrollBar.vertical:ScrollBar {}
        SmoothScroll {view:list}
        footer:Item {width:list.width;height:loadMore.visible?56:0
            Capsule {id:loadMore;objectName:'loadMoreMessages';anchors.horizontalCenter:parent.horizontalCenter;text:I18n.t('Load older messages')
                visible:!!view.service&&!view.localDrafts&&view.messages.length>=view.service.messageLimit&&view.service.messageLimit<2000
                enabled:!!view.service&&!view.service.featureBusy;onClicked:view.service.loadMoreMessages()}}
        delegate:Capsule {
            id:messageRow
            required property var modelData
            enabled:!!view.service&&!view.service.featureBusy
            width:list.width;height:Math.max((Theme.fancy?84:64)*Theme.textScale,contents.implicitHeight+(Theme.fancy?28:16));leftPadding:18;rightPadding:18
            text:String(modelData.subject||I18n.t('No subject'));Accessible.name:(modelData.unread?I18n.t('Unread. '):'')+text+'. '+String(modelData.sender||'')
            background:Rectangle {color:Theme.fancy?'transparent':String(messageRow.modelData.id)===view.selectedMessageId?(Theme.dark?'#263f50':'#dcecf9'):messageRow.hovered?Theme.selection:Theme.elevated;ButtonGlass {anchors.fill:parent;visible:Theme.fancy;control:messageRow;radius:14}}
            contentItem:RowLayout {
                spacing:12
                Rectangle {visible:!Theme.fancy;Layout.alignment:Qt.AlignTop;Layout.topMargin:4;width:32;height:32;radius:16;color:Theme.dark?'#3d5146':['#d9ead0','#ffdfbc','#daf0e9','#edf4bc'][String(messageRow.modelData.sender||'').length%4];Label {anchors.centerIn:parent;text:view.initials(messageRow.modelData.sender);color:Theme.text;font.pixelSize:12}}
                ColumnLayout {
                id:contents;spacing:5
                Label {visible:!Theme.fancy;Layout.fillWidth:true;text:messageRow.modelData.sender||I18n.t('Onbekende afzender');textFormat:Text.PlainText;elide:Text.ElideRight;color:Theme.text;font.bold:!!messageRow.modelData.unread;font.pixelSize:14*Theme.textScale}
                RowLayout {Layout.fillWidth:true;spacing:8
                    Label {textFormat:Text.PlainText;text:messageRow.modelData.subject||(Theme.fancy?I18n.t('No subject'):I18n.t('Geen onderwerp'));Layout.fillWidth:true;elide:Text.ElideRight;font.bold:Theme.fancy&&!!messageRow.modelData.unread;color:Theme.text;font.pixelSize:(Theme.fancy?15:12)*Theme.textScale}
                    RowLayout {visible:!Theme.fancy;spacing:5;Icon {visible:!!messageRow.modelData.hasAttachments;name:'clip';ink:Theme.secondary;width:14*Theme.textScale;height:width} Label {text:String(messageRow.modelData.date||'');color:Theme.secondary;font.pixelSize:10*Theme.textScale;textFormat:Text.PlainText}}
                }
                Label {visible:Theme.fancy;textFormat:Text.PlainText;text:(Theme.fancy?(messageRow.modelData.sender||I18n.t('Unknown sender'))+' · ':'')+(view.localDrafts?I18n.locale.toString(new Date(messageRow.modelData.date),'ddd, d MMM · hh:mm'):(messageRow.modelData.date||''));Layout.fillWidth:true;elide:Text.ElideRight;color:Theme.secondary;font.pixelSize:12*Theme.textScale}
                Label {visible:Theme.fancy&&!!messageRow.modelData.hasAttachments;text:I18n.t('Attachments included');textFormat:Text.PlainText;color:Theme.secondary;font.pixelSize:11*Theme.textScale}
                Label {Layout.fillWidth:true;visible:view.localDrafts&&!!messageRow.modelData.deliveryState&&messageRow.modelData.deliveryState!=='editing'
                    text:messageRow.modelData.deliveryState==='accepted'?I18n.t('Previous send accepted · check Sent'):I18n.t('Delivery unconfirmed · check Sent before retrying');textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.text;font.pixelSize:12*Theme.textScale}
                Capsule {objectName:'discardSavedDraft';visible:view.localDrafts;text:I18n.t('Discard draft');enabled:!!view.service&&!view.service.composer.busy
                    onClicked:view.service.composer.deleteDraft(messageRow.modelData.id)}
                }
            }
            onClicked:{view.previewMessage=modelData;view.readMessage(modelData.id)}
        }
        Label {anchors.centerIn:parent;width:parent.width-32;horizontalAlignment:Text.AlignHCenter;wrapMode:Text.Wrap;visible:list.count===0;text:view.messages.length?I18n.t('No matching messages'):view.localDrafts?I18n.t('Your saved drafts will appear here.'):I18n.t('Press Refresh to load this folder.');textFormat:Text.PlainText;color:Theme.secondary;font.pixelSize:16*Theme.textScale}
    }
    }
    Rectangle {visible:!Theme.fancy;Layout.preferredWidth:44*Theme.textScale;Layout.fillHeight:true;color:Theme.elevated
        Rectangle {anchors.right:parent.right;width:1;height:parent.height;color:Theme.separator}
        ColumnLayout {anchors.top:parent.top;anchors.topMargin:70;anchors.horizontalCenter:parent.horizontalCenter;spacing:4
            Repeater {model:[{symbol:'add',label:I18n.t('Nieuw bericht'),action:'new',color:'#55b526'}, {symbol:'reply',label:I18n.t('Beantwoorden'),action:'reply',color:'#55b526'}, {symbol:'replyAll',label:I18n.t('Allen beantwoorden'),action:'replyAll',color:'#55b526'}, {symbol:'forward',label:I18n.t('Doorsturen'),action:'forward',color:'#2696be'}, {symbol:'copy',label:I18n.t('Tekst kopiëren'),action:'copy',color:'#89858f'}, {symbol:'trash',label:I18n.t('Naar prullenmand'),action:'trash',color:'#c52828'}, {symbol:'more',label:I18n.t('Taak maken / meer acties'),action:'more',color:'#55b526'}]
                ToolButton {id:messageAction;required property var modelData;implicitWidth:36*Theme.textScale;implicitHeight:34*Theme.textScale;text:modelData.label;Accessible.name:modelData.label;GlassToolTip {requested:messageAction.hovered||messageAction.visualFocus;text:messageAction.modelData.label}
                    enabled:!!view.service&&!view.service.featureBusy&&(modelData.action==='new'||reader.current)&&(!(modelData.action==='reply'||modelData.action==='replyAll')||!!reader.message.canReply)&&(modelData.action!=='trash'||(!view.service.messageActionsBlocked&&['inbox','outbox'].indexOf(view.service.messageFolder)>=0))
                    contentItem:Item {Icon {anchors.centerIn:parent;name:messageAction.modelData.symbol;ink:Theme.highContrast?Theme.text:messageAction.modelData.color}}
                    onClicked:{let action=modelData.action;if(action==='new'){if(view.service.composer.newDraft()||view.service.composer.error)composer.open()}else if(action==='copy')readingPane.copyText();else if(action==='trash'){if(view.service.trashMessage(reader.requestedId)){view.previewMessage=({});reader.requestedId=''}}else if(action==='more')reader.open();else view.composeReply(action,'')}
                }
            }
        }
    }
    MessageReadingPane {id:readingPane;visible:!Theme.fancy;Layout.fillWidth:true;Layout.fillHeight:true;controller:view}
    }
    MessageComposer {id:composer;parent:view.app.contentItem;service:view.service?view.service.composer:null}
    Sheet {
        id:reader;objectName:'messageReader';parent:view.app.contentItem;title:I18n.t('Message');width:Math.min(820*Theme.textScale,parent.width-24)
        property string requestedId:''
        readonly property var message:view.service?view.service.messageDetail:({})
        readonly property bool current:String(message.id||'')===requestedId&&requestedId!==''
        Label {textFormat:Text.PlainText;text:reader.current?(reader.message.subject||I18n.t('No subject')):view.service&&view.service.messageLoading?I18n.t('Loading message…'):I18n.t('Message unavailable');Layout.fillWidth:true;wrapMode:Text.Wrap;font.pixelSize:22*Theme.textScale;font.bold:true;color:Theme.text}
        DetailCard {title:I18n.t('Message unavailable');Layout.fillWidth:true;visible:!!view.service&&view.service.messageError!==''
            Label {text:view.service?view.service.messageError:'';textFormat:Text.PlainText;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.secondary}
            Capsule {text:I18n.t('Retry message');enabled:!!view.service&&!view.service.featureBusy;onClicked:view.service.openMessage(reader.requestedId)}
        }
        Label {textFormat:Text.PlainText;text:reader.current?(reader.message.sender||'')+' · '+(reader.message.date||''):'';Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.secondary}
        Label {Layout.fillWidth:true;visible:reader.current&&(reader.message.to||[]).length>0;text:I18n.t('To: ')+(reader.message.to||[]).join(', ');textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.secondary}
        Label {Layout.fillWidth:true;visible:reader.current&&(reader.message.cc||[]).length>0;text:I18n.t('Cc: ')+(reader.message.cc||[]).join(', ');textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.secondary}
        Label {Layout.fillWidth:true;visible:reader.current&&reader.message.folder==='outbox'&&(reader.message.bcc||[]).length>0;text:I18n.t('Bcc: ')+(reader.message.bcc||[]).join(', ');textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.secondary}
        Flow {Layout.fillWidth:true;spacing:8;visible:reader.current
            Capsule {objectName:'replyMessage';text:I18n.t('Reply');enabled:!!reader.message.canReply;onClicked:view.composeReply('reply','')}
            Capsule {objectName:'replyAllMessage';text:I18n.t('Reply all');enabled:!!reader.message.canReply;onClicked:view.composeReply('replyAll','')}
            Capsule {objectName:'forwardMessage';text:I18n.t('Forward');onClicked:view.composeReply('forward','')}
            Capsule {objectName:'copyMessage';text:I18n.t('Copy text');onClicked:{messageBody.selectAll();messageBody.copy();messageBody.deselect();view.app.notify(I18n.t('Message text copied'),false)}}
            Capsule {objectName:'trashMessage';text:I18n.t('Move to Trash');visible:!!view.service&&['inbox','outbox'].indexOf(view.service.messageFolder)>=0;enabled:!!view.service&&!view.service.featureBusy&&!view.service.messageActionsBlocked
                onClicked:if(view.service.trashMessage(reader.requestedId))reader.close()}
        }
        DetailCard {title:I18n.t('Message');Layout.fillWidth:true;visible:reader.current
            TextArea {id:messageBody;objectName:'messageBody';textFormat:TextEdit.PlainText;readOnly:true;selectByMouse:true;text:reader.message.body||I18n.t('No message text.');Layout.fillWidth:true;wrapMode:TextEdit.Wrap;color:Theme.text;font.pixelSize:14*Theme.textScale;background:null;Accessible.name:I18n.t('Message text')}
        }
        DetailCard {title:I18n.t('Attachments');Layout.fillWidth:true;visible:reader.current&&(reader.message.attachments||[]).length>0
            Repeater {model:reader.current?(reader.message.attachments||[]):[]
                Capsule {required property var modelData;Layout.fillWidth:true;text:I18n.t('Download · ')+(modelData.name||I18n.t('Attachment'));enabled:!!view.service&&!view.service.featureBusy;onClicked:view.service.downloadAttachment('message',String(modelData.id))}
            }
        }
        Repeater {model:view.service?view.service.downloadedFiles.filter(f=>f.source==='message'&&f.sourceId===reader.requestedId):[]
            Capsule {objectName:'messageOfflineFile';required property var modelData;text:I18n.t('Offline · ')+modelData.name;Layout.fillWidth:true;onClicked:fileSheet.showFile(modelData)}
        }
        Capsule {objectName:'draftMessageReply';Layout.fillWidth:true;text:I18n.t('Draft a reply with Gemini');symbol:'ai';visible:reader.current;opacity:view.service&&view.service.aiAvailable?1:.45;enabled:!!view.service&&!view.service.featureBusy&&!!reader.message.canReply;Accessible.description:!reader.message.canReply?I18n.t('Replies are unavailable for this message.'):view.service&&view.service.aiAvailable?I18n.t('Generate an editable draft. Nothing is sent automatically.'):I18n.t('Gemini API key required. Activate for details.');onClicked:view.app.requestAI('reply')}
        Label {text:reader.message.canReply?I18n.t('The message text is sent to Gemini when you request a draft. Review and edit the result before using it.'):I18n.t('Replies are unavailable for this message.');textFormat:Text.PlainText;Layout.fillWidth:true;wrapMode:Text.Wrap;visible:reader.current;color:Theme.secondary;font.pixelSize:12*Theme.textScale}
        DetailCard {title:I18n.t('Create a local task');Layout.fillWidth:true;visible:reader.current
            Label {text:I18n.t('Keep this message as a task in your planner. Choose its due date.');textFormat:Text.PlainText;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.secondary}
            TextField {id:dueDate;objectName:'messageTaskDate';Layout.fillWidth:true;implicitHeight:44;text:Qt.formatDate(new Date(),'yyyy-MM-dd');placeholderText:'YYYY-MM-DD';Accessible.name:I18n.t('Due date for message task');color:Theme.text;selectByMouse:true;leftPadding:14;background:Surface {radius:Theme.fancy?18:3}}
            Capsule {text:I18n.t('Create task');Layout.fillWidth:true;enabled:!!view.service&&!view.service.featureBusy;onClicked:if(view.service.addMessageTask(dueDate.text)){reader.close();view.app.notify(I18n.t('Task added to your planner'),false)}}
        }
    }
    Connections {target:view.service
        function onReplyDraftSaved(){view.app.notify(I18n.t('Gemini reply saved in Local drafts'),false)}
        function onReplyDraftReady(message,body){
            if(composer.visible){
                if(view.service.composer.saveReplyAsDraft(message,body))view.app.notify(I18n.t('Gemini reply saved in Local drafts'),false)
                return
            }
            if(view.service.composer.prepareReply('reply',message,body)){
            let origin=reader.visible?reader.previousFocus:list;composer.open();if(origin&&origin.visible)composer.previousFocus=origin;reader.close()
        }else if(view.service.composer.error)composer.open()}
    }
    OfflineFileSheet {id:fileSheet;parent:view.app.contentItem;service:view.service}
}
