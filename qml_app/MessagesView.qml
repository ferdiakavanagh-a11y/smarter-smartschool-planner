import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ColumnLayout {
    id: view
    required property var app
    readonly property var service: app.production ? backend.features : null
    readonly property bool localDrafts:service&&service.messageFolder==='local'
    readonly property var folderIds:['inbox','outbox','local','trash','scheduled','draft']
    readonly property var folderLabels:['Inbox','Sent','Local drafts','Trash','Scheduled','School drafts']
    readonly property var messages: !service?[]:localDrafts?service.composer.savedDrafts.map(d=>Object.assign({},d,{sender:d.recipientSummary||'No recipients selected',date:d.updatedAt||'',preview:d.body||'',unread:false,hasAttachments:(d.attachments||[]).length>0})):service.messages
    readonly property bool readerVisible:reader.visible
    readonly property bool composerVisible:composer.visible
    readonly property string draftAccount:service?service.accountKey:''
    onDraftAccountChanged:{if(reader)reader.close();if(fileSheet)fileSheet.close()}
    function focusSearch(){search.forceActiveFocus()}
    function flushDraft(){return !service||service.composer.flushForExit()}
    function focusDraft(){composer.open()}
    function readMessage(id){
        if(localDrafts){list.forceActiveFocus(Qt.TabFocusReason);if(service.composer.resumeDraft(String(id))||service.composer.error)composer.open();return}
        reader.requestedId=String(id);service.clearReply();if(service.openMessage(reader.requestedId))reader.open()
    }
    function composeReply(mode,body){
        if(reader.current&&service.composer.prepareReply(mode,reader.message,body||'')){
            let origin=reader.previousFocus;composer.open();if(origin&&origin.visible)composer.previousFocus=origin;reader.close()
        }else if(service.composer.error)composer.open()
    }
    function changeFolder(index){
        if(service.selectMessageFolder(folderIds[index])){reader.close();fileSheet.close();service.loadMessages()}
    }
    readonly property var filteredMessages: {
        let query=search.text.trim().toLocaleLowerCase(), rows=[]
        for(let message of messages)
            if(!query||(message.subject+' '+message.sender+' '+(message.preview||'')).toLocaleLowerCase().includes(query))rows.push(message)
        return rows
    }
    spacing:12
    RowLayout {
        Layout.fillWidth:true
        GlassComboBox {objectName:'messageFolder';model:view.folderLabels;currentIndex:view.service?Math.max(0,view.folderIds.indexOf(view.service.messageFolder)):0;enabled:!!view.service&&!view.service.featureBusy
            Accessible.name:'Message folder';onActivated:view.changeFolder(currentIndex)}
        Label {text:view.localDrafts?'Saved on this computer':view.messages.length+' messages loaded';textFormat:Text.PlainText;color:Theme.secondary;Layout.fillWidth:true;wrapMode:Text.Wrap}
        Capsule {objectName:'newMessage';text:'New message';symbol:'message';enabled:!!view.service;onClicked:if(view.service.composer.newDraft()||view.service.composer.error)composer.open()}
        Capsule {objectName:'refreshMessages';visible:!view.localDrafts;text:service&&service.featureBusy?'Loading…':'Refresh';symbol:'syncBtn';enabled:!!service&&!service.featureBusy;onClicked:service.loadMessages()}
    }
    Label {Layout.fillWidth:true;visible:!!view.service&&view.service.messageActionsBlocked;text:'Refresh this folder to confirm the previous message action before trying again.';textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.text}
    TextField {id:search;objectName:'messageSearch';Layout.fillWidth:true;implicitHeight:44;placeholderText:'Search subjects or senders';Accessible.name:'Search Smartschool messages';selectByMouse:true;color:Theme.text;placeholderTextColor:Theme.secondary;leftPadding:16;background:Surface {radius:22}}
    ListView {
        id:list;objectName:'messageList';Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:10;bottomMargin:100*Theme.textScale
        model:view.filteredMessages;reuseItems:true;boundsBehavior:Flickable.StopAtBounds;activeFocusOnTab:true
        ScrollBar.vertical:ScrollBar {}
        SmoothScroll {view:list}
        footer:Item {width:list.width;height:loadMore.visible?56:0
            Capsule {id:loadMore;objectName:'loadMoreMessages';anchors.horizontalCenter:parent.horizontalCenter;text:'Load older messages'
                visible:!!view.service&&!view.localDrafts&&view.messages.length>=view.service.messageLimit&&view.service.messageLimit<2000
                enabled:!!view.service&&!view.service.featureBusy;onClicked:view.service.loadMoreMessages()}}
        delegate:Capsule {
            id:messageRow
            required property var modelData
            enabled:!!view.service&&!view.service.featureBusy
            width:list.width;height:Math.max(84,contents.implicitHeight+28);leftPadding:18;rightPadding:18
            text:String(modelData.subject||'No subject');Accessible.name:(modelData.unread?'Unread. ':'')+text+'. '+String(modelData.sender||'')
            background:ButtonGlass {control:messageRow;radius:14}
            contentItem:ColumnLayout {
                id:contents;spacing:5
                Label {textFormat:Text.PlainText;text:parent.parent.modelData.subject||'No subject';Layout.fillWidth:true;elide:Text.ElideRight;font.bold:!!parent.parent.modelData.unread;color:Theme.text;font.pixelSize:15*Theme.textScale}
                Label {textFormat:Text.PlainText;text:(parent.parent.modelData.sender||'Unknown sender')+' · '+(view.localDrafts?Qt.formatDateTime(new Date(parent.parent.modelData.date),'ddd, d MMM · hh:mm'):(parent.parent.modelData.date||''));Layout.fillWidth:true;elide:Text.ElideRight;color:Theme.secondary;font.pixelSize:12*Theme.textScale}
                Label {visible:!!parent.parent.modelData.hasAttachments;text:'Attachments included';textFormat:Text.PlainText;color:Theme.secondary;font.pixelSize:11*Theme.textScale}
                Label {Layout.fillWidth:true;visible:view.localDrafts&&!!messageRow.modelData.deliveryState&&messageRow.modelData.deliveryState!=='editing'
                    text:messageRow.modelData.deliveryState==='accepted'?'Previous send accepted · check Sent':'Delivery unconfirmed · check Sent before retrying';textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.text;font.pixelSize:12*Theme.textScale}
                Capsule {objectName:'discardSavedDraft';visible:view.localDrafts;text:'Discard draft';enabled:!!view.service&&!view.service.composer.busy
                    onClicked:view.service.composer.deleteDraft(messageRow.modelData.id)}
            }
            onClicked:view.readMessage(modelData.id)
        }
        Label {anchors.centerIn:parent;width:parent.width-32;horizontalAlignment:Text.AlignHCenter;wrapMode:Text.Wrap;visible:list.count===0;text:view.messages.length?'No matching messages':view.localDrafts?'Your saved drafts will appear here.':'Press Refresh to load this folder.';textFormat:Text.PlainText;color:Theme.secondary;font.pixelSize:16*Theme.textScale}
    }
    MessageComposer {id:composer;parent:view.app.contentItem;service:view.service?view.service.composer:null}
    Sheet {
        id:reader;objectName:'messageReader';parent:view.app.contentItem;title:'Message';width:Math.min(820*Theme.textScale,parent.width-24)
        property string requestedId:''
        readonly property var message:view.service?view.service.messageDetail:({})
        readonly property bool current:String(message.id||'')===requestedId&&requestedId!==''
        Label {textFormat:Text.PlainText;text:reader.current?(reader.message.subject||'No subject'):view.service&&view.service.messageLoading?'Loading message…':'Message unavailable';Layout.fillWidth:true;wrapMode:Text.Wrap;font.pixelSize:22*Theme.textScale;font.bold:true;color:Theme.text}
        DetailCard {title:'Message unavailable';Layout.fillWidth:true;visible:!!view.service&&view.service.messageError!==''
            Label {text:view.service?view.service.messageError:'';textFormat:Text.PlainText;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.secondary}
            Capsule {text:'Retry message';enabled:!!view.service&&!view.service.featureBusy;onClicked:view.service.openMessage(reader.requestedId)}
        }
        Label {textFormat:Text.PlainText;text:reader.current?(reader.message.sender||'')+' · '+(reader.message.date||''):'';Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.secondary}
        Label {Layout.fillWidth:true;visible:reader.current&&(reader.message.to||[]).length>0;text:'To: '+(reader.message.to||[]).join(', ');textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.secondary}
        Label {Layout.fillWidth:true;visible:reader.current&&(reader.message.cc||[]).length>0;text:'Cc: '+(reader.message.cc||[]).join(', ');textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.secondary}
        Label {Layout.fillWidth:true;visible:reader.current&&reader.message.folder==='outbox'&&(reader.message.bcc||[]).length>0;text:'Bcc: '+(reader.message.bcc||[]).join(', ');textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.secondary}
        Flow {Layout.fillWidth:true;spacing:8;visible:reader.current
            Capsule {objectName:'replyMessage';text:'Reply';enabled:!!reader.message.canReply;onClicked:view.composeReply('reply','')}
            Capsule {objectName:'replyAllMessage';text:'Reply all';enabled:!!reader.message.canReply;onClicked:view.composeReply('replyAll','')}
            Capsule {objectName:'forwardMessage';text:'Forward';onClicked:view.composeReply('forward','')}
            Capsule {objectName:'copyMessage';text:'Copy text';onClicked:{messageBody.selectAll();messageBody.copy();messageBody.deselect();view.app.notify('Message text copied',false)}}
            Capsule {objectName:'trashMessage';text:'Move to Trash';visible:!!view.service&&['inbox','outbox'].indexOf(view.service.messageFolder)>=0;enabled:!!view.service&&!view.service.featureBusy&&!view.service.messageActionsBlocked
                onClicked:if(view.service.trashMessage(reader.requestedId))reader.close()}
        }
        DetailCard {title:'Message';Layout.fillWidth:true;visible:reader.current
            TextArea {id:messageBody;objectName:'messageBody';textFormat:TextEdit.PlainText;readOnly:true;selectByMouse:true;text:reader.message.body||'No message text.';Layout.fillWidth:true;wrapMode:TextEdit.Wrap;color:Theme.text;font.pixelSize:14*Theme.textScale;background:null;Accessible.name:'Message text'}
        }
        DetailCard {title:'Attachments';Layout.fillWidth:true;visible:reader.current&&(reader.message.attachments||[]).length>0
            Repeater {model:reader.current?(reader.message.attachments||[]):[]
                Capsule {required property var modelData;Layout.fillWidth:true;text:'Download · '+(modelData.name||'Attachment');enabled:!!view.service&&!view.service.featureBusy;onClicked:view.service.downloadAttachment('message',String(modelData.id))}
            }
        }
        Repeater {model:view.service?view.service.downloadedFiles.filter(f=>f.source==='message'&&f.sourceId===reader.requestedId):[]
            Capsule {objectName:'messageOfflineFile';required property var modelData;text:'Offline · '+modelData.name;Layout.fillWidth:true;onClicked:fileSheet.showFile(modelData)}
        }
        Capsule {objectName:'draftMessageReply';Layout.fillWidth:true;text:'Draft a reply with Gemini';symbol:'ai';visible:reader.current;opacity:view.service&&view.service.aiAvailable?1:.45;enabled:!!view.service&&!view.service.featureBusy&&!!reader.message.canReply;Accessible.description:!reader.message.canReply?'Replies are unavailable for this message.':view.service&&view.service.aiAvailable?'Generate an editable draft. Nothing is sent automatically.':'Gemini API key required. Activate for details.';onClicked:view.app.requestAI('reply')}
        Label {text:reader.message.canReply?'The message text is sent to Gemini when you request a draft. Review and edit the result before using it.':'Replies are unavailable for this message.';textFormat:Text.PlainText;Layout.fillWidth:true;wrapMode:Text.Wrap;visible:reader.current;color:Theme.secondary;font.pixelSize:12*Theme.textScale}
        DetailCard {title:'Create a local task';Layout.fillWidth:true;visible:reader.current
            Label {text:'Keep this message as a task in your planner. Choose its due date.';textFormat:Text.PlainText;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.secondary}
            TextField {id:dueDate;objectName:'messageTaskDate';Layout.fillWidth:true;implicitHeight:44;text:Qt.formatDate(new Date(),'yyyy-MM-dd');placeholderText:'YYYY-MM-DD';Accessible.name:'Due date for message task';color:Theme.text;selectByMouse:true;leftPadding:14;background:Surface {radius:18}}
            Capsule {text:'Create task';Layout.fillWidth:true;enabled:!!view.service&&!view.service.featureBusy;onClicked:if(view.service.addMessageTask(dueDate.text)){reader.close();view.app.notify('Task added to your planner',false)}}
        }
    }
    Connections {target:view.service
        function onReplyDraftSaved(){view.app.notify('Gemini reply saved in Local drafts',false)}
        function onReplyDraftReady(message,body){
            if(composer.visible){
                if(view.service.composer.saveReplyAsDraft(message,body))view.app.notify('Gemini reply saved in Local drafts',false)
                return
            }
            if(view.service.composer.prepareReply('reply',message,body)){
            let origin=reader.visible?reader.previousFocus:list;composer.open();if(origin&&origin.visible)composer.previousFocus=origin;reader.close()
        }else if(view.service.composer.error)composer.open()}
    }
    OfflineFileSheet {id:fileSheet;parent:view.app.contentItem;service:view.service}
}
