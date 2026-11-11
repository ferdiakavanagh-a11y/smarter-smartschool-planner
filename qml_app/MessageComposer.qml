import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
Sheet {
    id:composer;objectName:'messageComposer';title:service&&service.draftMode!=='new'?(service.draftMode==='forward'?'Forward message':service.draftMode==='replyAll'?'Reply to all':'Reply'):'New message'
    property var service:null
    property string draftAccount:''
    property bool suggestionsDismissed:false
    property bool pickerRequested:false
    property var activeRecipientInput:toRecipients.input
    readonly property real recipientLabelWidth:64*Theme.textScale
    width:Math.min(760*Theme.textScale,parent.width-24)
    implicitHeight:Math.min(730*Theme.textScale,parent.height*.86)
    handleEscape:function(){if(recipientPopup.visible){recipientPopup.close();return true}return false}
    beforeClose:function(){
        recipientPopup.close()
        if(service)service.updateContent(subject.text,body.text)
        return !service||service.saveDraft()
    }
    function clearDraft(){toRecipients.input.text='';ccRecipients.input.text='';bccRecipients.input.text='';activeRecipientInput=toRecipients.input;subject.text='';body.text=''}
    function loadDraft(){
        recipientPopup.close();toRecipients.input.text='';ccRecipients.input.text='';bccRecipients.input.text='';activeRecipientInput=toRecipients.input
        if(service){subject.text=service.draftSubject;body.text=service.draftBody}
    }
    function repositionSuggestions(){
        let p=activeRecipientInput.mapToItem(recipientPopup.parent,0,0), margin=12
        recipientPopup.x=Math.max(margin,Math.min(p.x,recipientPopup.parent.width-recipientPopup.width-margin))
        let below=recipientPopup.parent.height-p.y-activeRecipientInput.height-margin,above=p.y-margin
        let space=below>=Math.min(220*Theme.textScale,above)?below:above
        recipientPopup.height=Math.min(260*Theme.textScale,Math.max(64,space))
        recipientPopup.y=below>=Math.min(220*Theme.textScale,above)?p.y+activeRecipientInput.height+6:p.y-recipientPopup.height-6
    }
    function updateSuggestions(){
        if(visible&&!suggestionsDismissed&&(activeRecipientInput.text.trim().length>=2||pickerRequested)&&service&&!service.deliveryLocked
                &&(activeRecipientInput.activeFocus||recipientPopup.activeFocus)){
            repositionSuggestions();recipientPopup.open()
        }else if(!recipientPopup.activeFocus)recipientPopup.close()
    }
    function focusSuggestion(index){
        if(!recipientPopup.visible||choices.count===0)return
        choices.currentIndex=Math.max(0,Math.min(choices.count-1,index))
        choices.positionViewAtIndex(choices.currentIndex,ListView.Contain)
        if(choices.currentItem)choices.currentItem.forceActiveFocus(Qt.TabFocusReason)
        else Qt.callLater(function(){if(recipientPopup.visible&&choices.currentItem)choices.currentItem.forceActiveFocus(Qt.TabFocusReason)})
    }
    function chooseSuggestion(chosenIndex){
        if(!service||!recipientPopup.visible||choices.count===0||service.searching)return
        let controller=service,input=activeRecipientInput,index=chosenIndex===undefined?Math.max(0,choices.currentIndex):chosenIndex
        controller.selectRecipient(index);recipientPopup.close();input.text='';input.forceActiveFocus()
    }
    Component.onCompleted:{draftAccount=service?service.accountKey:'';bodyColumn.spacing=10;loadDraft()}
    Connections {target:composer
        function onAboutToShow(){Qt.callLater(function(){
            if(!composer.visible||composer.closing)return
            for(let item=composer.hostWindow.activeFocusItem;item;item=item.parent)
                if(item===composer.bodyColumn||item===recipientPopup.contentItem)return
            activeRecipientInput.forceActiveFocus()
        })}
    }
    onAboutToHide:{recipientPopup.close();if(service)service.saveDraft()}
    onXChanged:if(recipientPopup.visible)repositionSuggestions()
    onYChanged:if(recipientPopup.visible)repositionSuggestions()
    Connections {target:composer.scrollView.contentItem
        function onContentYChanged(){if(recipientPopup.visible)composer.repositionSuggestions()}
    }
    Connections {target:composer.service
        function onDraftChanged(){composer.loadDraft()}
        function onChanged(){
            if(composer.service.accountKey!==composer.draftAccount){
                composer.draftAccount=composer.service.accountKey;composer.clearDraft();composer.close()
            }else composer.updateSuggestions()
        }
    }
    Label {Layout.fillWidth:true;visible:!!composer.service&&composer.service.recipientHints.length>0
        text:composer.service?'Resolve the original recipients: '+composer.service.recipientHints.map(function(r){return r.field+': '+r.name}).join(' · '):''
        textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.secondary;font.pixelSize:12*Theme.textScale}
    function activateRecipientInput(input,field){
        if(activeRecipientInput!==input||service.recipientField!==field){
            activeRecipientInput=input;service.setRecipientField(field)
            if(input.text.trim().length>=2)service.updateRecipientQuery(input.text)
        }
    }
    function openRecipientPicker(input,field){
        activateRecipientInput(input,field);pickerRequested=true;suggestionsDismissed=false
        input.forceActiveFocus();updateSuggestions()
    }
    component RecipientRow: RowLayout {
        id:row;required property string field
        property alias input:searchInput
        property var nextInput:subject
        Layout.fillWidth:true;spacing:8
        Label {text:row.field;textFormat:Text.PlainText;color:Theme.secondary;Layout.preferredWidth:composer.recipientLabelWidth;Layout.alignment:Qt.AlignTop;Layout.topMargin:12}
        ColumnLayout {Layout.fillWidth:true;spacing:6
            Flow {id:rowChips;Layout.fillWidth:true;spacing:6
                readonly property var recipients:composer.service?composer.service.selectedRecipients.filter(r=>r.field===row.field):[]
                visible:recipients.length>0
                Repeater {model:rowChips.recipients
                    Capsule {required property var modelData;objectName:'selectedRecipient';text:modelData.name+(modelData.coaccount?' (Co-account)':'');symbol:'close';width:Math.min(implicitWidth,rowChips.width)
                        Accessible.name:'Remove '+modelData.field+(modelData.coaccount?' co-account':'')+' recipient '+modelData.name
                        enabled:!!composer.service&&!composer.service.sending&&!composer.service.deliveryLocked
                        onClicked:composer.service.removeRecipient(modelData.index)}
                }
            }
            TextField {id:searchInput;objectName:row.field==='To'?'composeRecipientSearch':row.field==='Cc'?'composeCcSearch':'composeBccSearch'
                Layout.fillWidth:true;implicitHeight:44;maximumLength:100
                KeyNavigation.tab:addRecipient
                placeholderText:'Name, class or school group';Accessible.name:row.field+' recipient name or group';selectByMouse:true;color:Theme.text;placeholderTextColor:Theme.secondary
                enabled:!!composer.service&&!composer.service.sending&&!composer.service.deliveryLocked
                onTextEdited:{composer.activateRecipientInput(searchInput,row.field);composer.suggestionsDismissed=false;composer.service.updateRecipientQuery(text);composer.updateSuggestions()}
                onActiveFocusChanged:if(activeFocus){composer.activateRecipientInput(searchInput,row.field);Qt.callLater(composer.updateSuggestions)}
                Keys.onDownPressed:{composer.openRecipientPicker(searchInput,row.field);composer.focusSuggestion(0)}
                onAccepted:if(recipientPopup.visible&&choices.count>0)composer.chooseSuggestion();else if(text.trim().length>=2)composer.service.searchRecipients(text);else row.nextInput.forceActiveFocus()
                background:Surface {radius:12}
            }
        }
        Capsule {id:addRecipient;objectName:'add'+row.field+'Recipient';text:'+';implicitWidth:44;implicitHeight:44;leftPadding:0;rightPadding:0;font.pixelSize:24*Theme.textScale
            Layout.alignment:Qt.AlignBottom;Accessible.name:'Add '+row.field+' recipients';KeyNavigation.tab:row.nextInput;KeyNavigation.backtab:searchInput
            enabled:!!composer.service&&!composer.service.sending&&!composer.service.deliveryLocked
            onClicked:composer.openRecipientPicker(searchInput,row.field)}
    }
    RowLayout {Layout.fillWidth:true;spacing:6
                Item {Layout.fillWidth:true}
                Capsule {objectName:'mainAccountsTab';Layout.minimumWidth:0;text:'Main accounts';selectorMaterial:true;selected:!composer.service||composer.service.recipientMode==='main'
                    enabled:!!composer.service&&!composer.service.sending&&!composer.service.deliveryLocked
                    Accessible.name:'Main accounts, '+(composer.service?composer.service.selectedRecipients.filter(r=>!r.coaccount).length:0)+' selected recipients'
                    onClicked:{composer.suggestionsDismissed=false;composer.service.setRecipientMode('main');composer.service.updateRecipientQuery(composer.activeRecipientInput.text);composer.activeRecipientInput.forceActiveFocus();composer.updateSuggestions()}}
                Capsule {objectName:'coAccountsTab';Layout.minimumWidth:0;text:'Co-accounts';selectorMaterial:true;selected:!!composer.service&&composer.service.recipientMode==='coaccounts'
                    enabled:!!composer.service&&!composer.service.coaccountsUnavailable&&!composer.service.sending&&!composer.service.deliveryLocked
                    Accessible.description:composer.service&&composer.service.coaccountsUnavailable?'Your school account does not allow messaging co-accounts.':'Search co-accounts, such as parents.'
                    Accessible.name:'Co-accounts, '+(composer.service?composer.service.selectedRecipients.filter(r=>r.coaccount).length:0)+' selected recipients'
                    onClicked:{composer.suggestionsDismissed=false;composer.service.setRecipientMode('coaccounts');composer.service.updateRecipientQuery(composer.activeRecipientInput.text);composer.activeRecipientInput.forceActiveFocus();composer.updateSuggestions()}}
    }
    RecipientRow {id:toRecipients;field:'To';nextInput:ccRecipients.input}
    RecipientRow {id:ccRecipients;field:'Cc';nextInput:bccRecipients.input}
    RecipientRow {id:bccRecipients;field:'Bcc';nextInput:subject}
    Popup {id:recipientPopup;objectName:'recipientDropdown';parent:Overlay.overlay;z:100
        popupType:Popup.Item;modal:false;focus:false;closePolicy:Popup.CloseOnPressOutside; padding:8
        width:Math.min(activeRecipientInput.width,parent.width-24)
        onClosed:{composer.suggestionsDismissed=true;composer.pickerRequested=false}
        background:Surface {radius:14;strong:true}
        contentItem:ColumnLayout {spacing:6
            PointHandler {onActiveChanged:if(active)composer.pressedInside=true}
            Label {objectName:'recipientModeNotice';Layout.fillWidth:true;Layout.preferredHeight:32*Theme.textScale;textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.secondary;font.pixelSize:12*Theme.textScale
                text:composer.service&&composer.service.coaccountsUnavailable?'Your school account does not allow messaging co-accounts.':composer.service&&composer.service.searching?'Finding recipients…':composer.service&&composer.service.recipientMode==='coaccounts'?'Choose a co-account linked to the school account.':'Search people, classes and school groups.'}
            Item {Layout.fillWidth:true;Layout.fillHeight:true
                ListView {id:choices;objectName:'composeRecipients';anchors.fill:parent
                    model:composer.service?composer.service.recipients:[];clip:true;spacing:0;activeFocusOnTab:true
                    onCountChanged:currentIndex=count>0?0:-1
                    Keys.onReturnPressed:composer.chooseSuggestion()
                    Keys.onDownPressed:composer.focusSuggestion(currentIndex+1)
                    Keys.onUpPressed:if(currentIndex<=0)activeRecipientInput.forceActiveFocus();else composer.focusSuggestion(currentIndex-1)
                    ScrollBar.vertical:ScrollBar {}
                    delegate:Capsule {id:choice;objectName:'recipientChoice';required property var modelData;width:choices.width;height:56*Theme.textScale
                        text:modelData.name;Accessible.name:modelData.name+(modelData.detail?'. '+modelData.detail:'')
                        enabled:!!composer.service&&!composer.service.searching
                        background:Rectangle {radius:10;color:choice.down?Theme.alpha(Theme.text,.14):choice.hovered||choice.visualFocus?Theme.alpha(Theme.text,.08):'transparent'
                            border.width:choice.visualFocus?2:0;border.color:Theme.text
                            Rectangle {x:8;y:parent.height-1;width:parent.width-16;height:1;color:Theme.separator;visible:choice.modelData.index<choices.count-1}}
                        contentItem:ColumnLayout {spacing:3
                            Label {Layout.fillWidth:true;text:choice.modelData.name;textFormat:Text.PlainText;elide:Text.ElideRight;color:Theme.text}
                            Label {Layout.fillWidth:true;text:choice.modelData.detail;textFormat:Text.PlainText;elide:Text.ElideRight;color:Theme.secondary;font.pixelSize:12*Theme.textScale}}
                        KeyNavigation.tab:subject;KeyNavigation.backtab:activeRecipientInput
                        Keys.onDownPressed:composer.focusSuggestion(modelData.index+1)
                        Keys.onUpPressed:if(modelData.index===0)activeRecipientInput.forceActiveFocus();else composer.focusSuggestion(modelData.index-1)
                        onClicked:composer.chooseSuggestion(modelData.index)
                    }
                }
                Label {objectName:'recipientLookupState';anchors.centerIn:parent;width:parent.width-24;horizontalAlignment:Text.AlignHCenter;wrapMode:Text.Wrap;textFormat:Text.PlainText
                    color:composer.service?.error?Theme.text:Theme.secondary;font.weight:composer.service?.error?Font.DemiBold:Font.Normal;font.pixelSize:12*Theme.textScale
                    visible:choices.count===0;text:composer.service?.error||(composer.service?.searching?'Searching…':composer.service?.status||(composer.activeRecipientInput.text.trim().length<2?'Type at least two characters to find recipients.':'Suggestions will appear here.'))}
            }
        }
    }
    RowLayout {Layout.fillWidth:true;spacing:8
        Label {text:'Subject';textFormat:Text.PlainText;color:Theme.secondary;Layout.preferredWidth:composer.recipientLabelWidth}
        TextField {id:subject;objectName:'composeSubject';Layout.fillWidth:true;implicitHeight:44;maximumLength:250
            Accessible.name:'Message subject';selectByMouse:true;color:Theme.text;readOnly:!!composer.service&&(composer.service.sending||composer.service.deliveryLocked)
            onTextEdited:if(composer.service)composer.service.updateContent(text,body.text)
            onActiveFocusChanged:if(activeFocus)recipientPopup.close()
            background:Surface {radius:12}}
        Item {Layout.preferredWidth:44}
    }
    Label {text:'Message';textFormat:Text.PlainText;color:Theme.secondary}
    ScrollView {Layout.fillWidth:true;Layout.preferredHeight:190*Theme.textScale
        TextArea {id:body;objectName:'composeBody';textFormat:TextEdit.PlainText;wrapMode:TextEdit.Wrap;selectByMouse:true
            KeyNavigation.priority:KeyNavigation.BeforeItem;KeyNavigation.tab:attachButton;KeyNavigation.backtab:subject
            Accessible.name:'Message text';color:Theme.text;readOnly:!!composer.service&&(composer.service.sending||composer.service.deliveryLocked)
            onTextChanged:if(composer.service&&activeFocus)composer.service.updateContent(subject.text,text)
            onActiveFocusChanged:if(activeFocus)recipientPopup.close()
            background:Rectangle {radius:12;color:Theme.fill;border.color:Theme.separator}}
    }
    Repeater {model:composer.service?composer.service.attachments:[]
        RowLayout {required property var modelData;required property int index;Layout.fillWidth:true
            Label {Layout.fillWidth:true;text:modelData.name+' · '+Math.ceil(modelData.bytes/1024)+' KB';textFormat:Text.PlainText;elide:Text.ElideMiddle;color:Theme.text}
            Capsule {text:'Remove';Accessible.name:'Remove attachment '+modelData.name;enabled:!!composer.service&&!composer.service.sending&&!composer.service.deliveryLocked
                onClicked:composer.service.removeAttachment(index)}}
    }
    Label {Layout.fillWidth:true;visible:!!composer.service&&!!composer.service.error&&!recipientPopup.visible;text:composer.service?composer.service.error:''
        textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.text;font.weight:Font.DemiBold}
    Label {Layout.fillWidth:true;visible:!!composer.service&&!!composer.service.status;text:composer.service?composer.service.status:''
        textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.secondary}
    RowLayout {Layout.fillWidth:true;spacing:8
        Capsule {id:attachButton;objectName:'attachMessageFile';text:'Attach files';symbol:'clip';enabled:!!composer.service&&!composer.service.busy&&!composer.service.deliveryLocked
            KeyNavigation.tab:sendButton;KeyNavigation.backtab:body;onClicked:attachmentPicker.open()}
        Label {Layout.fillWidth:true;text:'Drafts stay on this device for this account.';textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.secondary;font.pixelSize:12*Theme.textScale}
        Capsule {objectName:'startNewDraft';visible:!!composer.service&&composer.service.deliveryLocked;text:'New message';enabled:!!composer.service&&!composer.service.busy
            onClicked:if(composer.service.newDraft())composer.loadDraft()}
        Capsule {id:sendButton;objectName:'sendMessage';text:composer.service&&composer.service.sending?'Sending…':'Send';primary:true
            enabled:!!composer.service&&!composer.service.busy&&!composer.service.deliveryLocked&&!!composer.service.recipient&&subject.text.trim().length>0&&body.text.trim().length>0
            onClicked:composer.service.send(subject.text,body.text)}
    }
    FileDialog {id:attachmentPicker;title:'Attach files';fileMode:FileDialog.OpenFiles
        onAccepted:if(composer.service)composer.service.addAttachments(selectedFiles)}
}



