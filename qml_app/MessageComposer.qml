import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
Sheet {
    id:composer;objectName:'messageComposer';title:Theme.smartschool?I18n.t('Nieuw bericht'):service&&service.draftMode!=='new'?(service.draftMode==='forward'?I18n.t('Forward message'):service.draftMode==='replyAll'?I18n.t('Reply to all'):I18n.t('Reply')):I18n.t('New message')
    popupType:Theme.fancy?Popup.Item:Popup.Window
    bodyMargin:Theme.fancy?20:width>=800?70:16
    headerColor:Theme.fancy?'transparent':'#252525'
    headerInk:Theme.fancy?Theme.text:'white'
    property var service:null
    function plainBody(){return body.getText(0,body.length)}
    function saveContent(){if(service)service.updateRichContent(subject.text,plainBody(),body.text)}
    function escaped(value){return String(value).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>')}
    property string draftAccount:''
    property bool suggestionsDismissed:false
    property bool pickerRequested:false
    property var activeRecipientInput:toRecipients.input
    readonly property real recipientLabelWidth:(Theme.fancy?64:80)*Theme.textScale
    width:Math.min((Theme.fancy?760:1000)*Theme.textScale,parent.width-24,Theme.fancy?parent.width:Math.max(700,parent.height-20))
    height:Math.min((Theme.fancy?730:1000)*Theme.textScale,parent.height-(Theme.fancy?70:20))
    implicitHeight:Math.min((Theme.fancy?730:820)*Theme.textScale,parent.height*.9)
    handleEscape:function(){if(recipientPopup.visible){recipientPopup.close();return true}return false}
    beforeClose:function(){
        recipientPopup.close()
        saveContent()
        return !service||service.saveDraft()
    }
    function clearDraft(){toRecipients.input.text='';ccRecipients.input.text='';bccRecipients.input.text='';activeRecipientInput=toRecipients.input;subject.text='';body.text=''}
    function loadDraft(){
        recipientPopup.close();toRecipients.input.text='';ccRecipients.input.text='';bccRecipients.input.text='';activeRecipientInput=toRecipients.input
        if(service){subject.text=service.draftSubject;body.text=service.draftHtml||'<p>'+escaped(service.draftBody)+'</p>'}
    }
    function repositionSuggestions(){
        if(!recipientPopup.parent||!activeRecipientInput)return
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
    Binding {target:composer.bodyColumn;property:'spacing';value:Theme.fancy?10:0}
    Component.onCompleted:{draftAccount=service?service.accountKey:'';loadDraft()}
    Connections {target:composer
        function onAboutToShow(){Qt.callLater(function(){
            if(!composer.visible||composer.closing)return
            for(let item=composer.hostWindow.activeFocusItem;item;item=item.parent)
                if(item===composer.bodyColumn||item===recipientPopup.contentItem)return
            activeRecipientInput.forceActiveFocus()
        })}
    }
    onAboutToHide:{recipientPopup.close();scheduleCalendarPopup.close();scheduleDialog.close();if(service)service.saveDraft()}
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
        text:composer.service?I18n.t('Resolve the original recipients: ')+composer.service.recipientHints.map(function(r){return r.field+': '+r.name}).join(' · '):''
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
        Label {text:I18n.t(row.field==='To'?'To:':row.field==='Cc'?'Cc:':'Bcc:');horizontalAlignment:Text.AlignRight;textFormat:Text.PlainText;color:Theme.secondary;Layout.preferredWidth:composer.recipientLabelWidth;Layout.alignment:Qt.AlignTop;Layout.topMargin:12}
        ColumnLayout {Layout.fillWidth:true;spacing:6
            Flow {id:rowChips;Layout.fillWidth:true;spacing:6
                readonly property var recipients:composer.service?composer.service.selectedRecipients.filter(r=>r.field===row.field):[]
                visible:recipients.length>0
                Repeater {model:rowChips.recipients
                    Capsule {required property var modelData;objectName:'selectedRecipient';quiet:false;text:modelData.name+(modelData.coaccount?I18n.t(' (Co-account)'):'');symbol:'close';width:Math.min(implicitWidth,rowChips.width)
                        Accessible.name:I18n.t('Remove ')+I18n.t(modelData.field)+(modelData.coaccount?I18n.t(' co-account'):'')+I18n.t(' recipient ')+modelData.name
                        enabled:!!composer.service&&!composer.service.sending&&!composer.service.deliveryLocked
                        onClicked:composer.service.removeRecipient(modelData.index)}
                }
            }
            TextField {id:searchInput;objectName:row.field==='To'?'composeRecipientSearch':row.field==='Cc'?'composeCcSearch':'composeBccSearch'
                Layout.fillWidth:true;implicitHeight:Theme.fancy?44:34;maximumLength:100
                KeyNavigation.tab:addRecipient
                placeholderText:Theme.fancy?I18n.t('Name, class or school group'):'';Accessible.name:I18n.t(row.field)+I18n.t(' recipient name or group');selectByMouse:true;color:Theme.text;placeholderTextColor:Theme.secondary
                enabled:!!composer.service&&!composer.service.sending&&!composer.service.deliveryLocked
                onTextEdited:{composer.activateRecipientInput(searchInput,row.field);composer.suggestionsDismissed=false;composer.service.updateRecipientQuery(text);composer.updateSuggestions()}
                onActiveFocusChanged:if(activeFocus){composer.activateRecipientInput(searchInput,row.field);Qt.callLater(composer.updateSuggestions)}
                Keys.onDownPressed:{composer.openRecipientPicker(searchInput,row.field);composer.focusSuggestion(0)}
                onAccepted:if(recipientPopup.visible&&choices.count>0)composer.chooseSuggestion();else if(text.trim().length>=2)composer.service.searchRecipients(text);else row.nextInput.forceActiveFocus()
                background:Surface {radius:Theme.fancy?12:3}
            }
        }
        Capsule {id:addRecipient;objectName:'add'+row.field+'Recipient';text:'+';implicitWidth:44;implicitHeight:Theme.fancy?44:34;leftPadding:0;rightPadding:0;font.pixelSize:28*Theme.textScale
            background:Rectangle {color:Theme.fancy?Theme.fill:'transparent'}
            contentItem:Item {Icon {anchors.centerIn:parent;name:'add';width:24*Theme.textScale;height:24*Theme.textScale;ink:Theme.fancy||Theme.highContrast?Theme.text:Theme.dark?'#91D77C':'#3E8E24'}}
            Layout.alignment:Qt.AlignBottom;Accessible.name:I18n.t('Add ')+row.field+I18n.t(' recipients');KeyNavigation.tab:row.nextInput;KeyNavigation.backtab:searchInput
            enabled:!!composer.service&&!composer.service.sending&&!composer.service.deliveryLocked
            onClicked:composer.openRecipientPicker(searchInput,row.field)}
    }
    property RowLayout sendControls: RowLayout {id:composeToolbar;spacing:8
        Capsule {id:sendButton;objectName:'sendMessage';text:composer.service&&composer.service.sending?I18n.t('Versturen…'):composer.service&&composer.service.scheduleAt?I18n.p('Schedule message','Plan bericht'):I18n.t('Send');primary:true;Layout.preferredWidth:Theme.fancy?150:186;implicitHeight:35
            enabled:!!composer.service&&!composer.service.busy&&!composer.service.deliveryLocked&&!!composer.service.recipient&&subject.text.trim().length>0&&composer.plainBody().trim().length>0
            onClicked:composer.service.sendRich(subject.text,composer.plainBody(),body.text)}
        Capsule {objectName:'messageSendOptions';text:'▾';primary:true;implicitWidth:32;implicitHeight:35;Accessible.name:I18n.t('Verzendopties');enabled:!!composer.service&&!composer.service.busy&&!composer.service.deliveryLocked;onClicked:sendMenu.open()
            PlannerMenu {id:sendMenu
                PlannerMenuItem {objectName:'scheduleMessageOption';text:I18n.p('Choose send time…','Kies een verzendmoment…');onTriggered:{let stamp=composer.service.scheduleAt||composer.service.scheduleDefault;scheduleDialog.selectedDate=new Date(Number(stamp.slice(0,4)),Number(stamp.slice(5,7))-1,Number(stamp.slice(8,10)),12);scheduleHour.currentIndex=Number(stamp.slice(11,13));scheduleMinute.currentIndex=Number(stamp.slice(14,16));scheduleError.text='';scheduleDialog.open()}}
                PlannerMenuItem {text:I18n.p('Send immediately instead','Toch meteen versturen');visible:!!composer.service&&!!composer.service.scheduleAt;onTriggered:composer.service.setSchedule('','')}
                PlannerMenuItem {text:I18n.t('Concept opslaan en sluiten');onTriggered:composer.dismiss()}
            }}
    }
    readonly property bool dockSend:Theme.smartschool && height<800*Theme.textScale
    LayoutItemProxy {target:composeToolbar;visible:!composer.dockSend;Layout.alignment:Qt.AlignLeft}
    Label {objectName:'messageScheduleSummary';Layout.fillWidth:true;visible:!!composer.service&&!!composer.service.scheduleAt;text:I18n.p('Smartschool will send at ','Smartschool verstuurt op ')+(composer.service?composer.service.scheduleAt.replace('T',' ').slice(0,16):'')+I18n.p(' (Belgium time). Press Schedule message to confirm.',' (Belgische tijd). Klik op Plan bericht als alles klopt.');wrapMode:Text.Wrap;color:Theme.secondary;font.pixelSize:12*Theme.textScale}
    Dialog {id:scheduleDialog;objectName:'scheduleMessageDialog';property date selectedDate:new Date();parent:composer.contentItem;modal:true;focus:true;title:I18n.p('When should Smartschool send it?','Wanneer mag Smartschool je bericht versturen?');background:Surface {strong:true;radius:Theme.fancy?20:8}
        header:Label {text:scheduleDialog.title;wrapMode:Text.Wrap;padding:14;color:Theme.text;font.bold:true;background:null}
        width:Math.min(440*Theme.textScale,composer.width-32);x:(parent.width-width)/2;y:Math.max(12,(parent.height-height)/2)
        contentItem:ColumnLayout {spacing:12
            Label {Layout.fillWidth:true;text:I18n.p('Smartschool sends it even when this app is closed.','Smartschool verstuurt het ook als deze app dicht is.');color:Theme.text;wrapMode:Text.Wrap}
            Label {text:I18n.p('Date','Datum');color:Theme.secondary}
            Capsule {id:scheduleDay;objectName:'scheduledSendDate';quiet:false;Layout.fillWidth:true;text:scheduleDialog.selectedDate.toLocaleDateString(I18n.locale,'dddd d MMMM yyyy');symbol:'cal';Accessible.name:I18n.p('Choose send date','Kies de verzenddatum')
                onClicked:{scheduleCalendar.month=scheduleDialog.selectedDate.getMonth();scheduleCalendar.year=scheduleDialog.selectedDate.getFullYear();let point=mapToItem(composer.contentItem,0,height);scheduleCalendarPopup.x=Math.max(12,Math.min(point.x,composer.width-scheduleCalendarPopup.width-12));scheduleCalendarPopup.y=Math.max(12,Math.min(point.y+6,composer.height-scheduleCalendarPopup.height-12));scheduleCalendarPopup.open()}}

            Label {text:I18n.p('Time in Belgium','Tijd in België');color:Theme.secondary}
            RowLayout {Layout.fillWidth:true;spacing:8
                GlassComboBox {id:scheduleHour;objectName:'scheduledSendHour';Layout.fillWidth:true;model:Array.from({length:24},(_,i)=>String(i).padStart(2,'0'));Accessible.name:I18n.p('Send hour in Belgium','Verzenduur in België')}
                Label {text:':';color:Theme.text}
                GlassComboBox {id:scheduleMinute;objectName:'scheduledSendMinute';Layout.fillWidth:true;model:Array.from({length:60},(_,i)=>String(i).padStart(2,'0'));Accessible.name:I18n.p('Send minute','Verzendminuut')}
            }

            Label {id:scheduleError;Layout.fillWidth:true;visible:text!=='';textFormat:Text.PlainText;color:Theme.red;wrapMode:Text.Wrap}
        }
        footer:DialogButtonBox {
            background:Item {}
            Capsule {primary:true;text:I18n.p('Use this time','Gebruik dit moment');DialogButtonBox.buttonRole:DialogButtonBox.ActionRole;onClicked:{if(composer.service.setSchedule(Qt.formatDate(scheduleDialog.selectedDate,'yyyy-MM-dd'),scheduleHour.currentText+':'+scheduleMinute.currentText))scheduleDialog.close();else scheduleError.text=I18n.t(composer.service.error)}}
            Capsule {text:I18n.p('Cancel','Annuleren');DialogButtonBox.buttonRole:DialogButtonBox.RejectRole;onClicked:scheduleDialog.close()}
        }
    }
    Popup {id:scheduleCalendarPopup;objectName:'scheduledDateCalendar';parent:composer.contentItem;modal:true;focus:true;padding:12;width:Math.min(360*Theme.textScale,composer.width-24);height:calendarContents.implicitHeight+24;closePolicy:Popup.CloseOnEscape|Popup.CloseOnPressOutside
        background:Surface {strong:true;radius:Theme.fancy?18:8}
        contentItem:ColumnLayout {id:calendarContents;spacing:6
            RowLayout {Layout.fillWidth:true
                Capsule {objectName:'schedulePreviousMonth';enabled:scheduleCalendar.year>new Date().getFullYear()||scheduleCalendar.year===new Date().getFullYear()&&scheduleCalendar.month>new Date().getMonth();text:'‹';Accessible.name:I18n.p('Previous month','Vorige maand');onClicked:{if(scheduleCalendar.month===0){scheduleCalendar.month=11;scheduleCalendar.year--}else scheduleCalendar.month--}}
                Label {text:scheduleCalendar.title;color:Theme.text;Layout.fillWidth:true;horizontalAlignment:Text.AlignHCenter;font.bold:true}
                Capsule {objectName:'scheduleNextMonth';enabled:scheduleCalendar.year<new Date().getFullYear()+1||scheduleCalendar.year===new Date().getFullYear()+1&&scheduleCalendar.month<new Date().getMonth();text:'›';Accessible.name:I18n.p('Next month','Volgende maand');onClicked:{if(scheduleCalendar.month===11){scheduleCalendar.month=0;scheduleCalendar.year++}else scheduleCalendar.month++}}
            }
            DayOfWeekRow {locale:I18n.locale;Layout.fillWidth:true;Layout.preferredHeight:24*Theme.textScale;palette.windowText:Theme.secondary}
            MonthGrid {id:scheduleCalendar;objectName:'scheduleMonthGrid';locale:I18n.locale;Layout.fillWidth:true;Layout.preferredHeight:6*34*Theme.textScale+30;spacing:3
                delegate:Button {required property var model;objectName:'scheduledDay_'+Qt.formatDate(model.date,'yyyy-MM-dd');readonly property string isoDate:Qt.formatDate(model.date,'yyyy-MM-dd');readonly property bool selected:isoDate===Qt.formatDate(scheduleDialog.selectedDate,'yyyy-MM-dd')
                    width:(scheduleCalendar.availableWidth-18)/7;height:34*Theme.textScale;leftPadding:0;rightPadding:0
                    enabled:{let day=new Date(model.year,model.month,model.day,12),today=new Date(),last=new Date(today.getFullYear()+1,today.getMonth(),today.getDate(),12);today.setHours(0,0,0,0);return day>=today&&day<=last}
                    Accessible.name:new Date(model.year,model.month,model.day,12).toLocaleDateString(I18n.locale,'dddd d MMMM yyyy');Accessible.selected:selected
                    background:Rectangle {radius:6;color:parent.selected?Theme.selection:parent.down?Theme.fill:'transparent';border.width:parent.visualFocus||parent.model.today?1:0;border.color:Theme.blue}
                    contentItem:Label {text:parent.model.day;color:parent.enabled?Theme.text:Theme.secondary;opacity:parent.model.month===scheduleCalendar.month?1:.5;horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter;font.pixelSize:12*Theme.textScale}
                    onClicked:{scheduleDialog.selectedDate=new Date(model.year,model.month,model.day,12);scheduleCalendarPopup.close();scheduleDay.forceActiveFocus()}
                }
            }
        }
    }
    Label {id:recipientSummaryLabel;Layout.topMargin:10;Layout.bottomMargin:6;visible:!Theme.fancy&&!composer.dockSend;text:I18n.t('Dit bericht wordt verstuurd naar');color:Theme.secondary;font.pixelSize:12*Theme.textScale}
    Flow {id:recipientSummary;visible:!Theme.fancy&&!composer.dockSend;Layout.fillWidth:true;spacing:8
        Repeater {model:[{label:I18n.t('Hoofdaccounts'),kind:'main'},{label:I18n.t('Co-accounts'),kind:'co'},{label:I18n.t('Groepen'),kind:'group'},{label:I18n.t('Ontvangers'),kind:'all'}]
            Rectangle {required property var modelData;implicitWidth:summary.implicitWidth+24;implicitHeight:40;radius:20;color:Theme.fill
                Label {id:summary;anchors.centerIn:parent;color:Theme.secondary;font.pixelSize:12*Theme.textScale
                    text:(composer.service?composer.service.selectedRecipients.filter(r=>modelData.kind==='all'||modelData.kind==='group'&&r.kind==='group'||modelData.kind==='co'&&r.coaccount||modelData.kind==='main'&&r.kind!=='group'&&!r.coaccount).length:0)+'    '+modelData.label}}
        }
    }
    Pane {id:recipientForm;Layout.fillWidth:true;padding:Theme.fancy?0:12;Layout.topMargin:Theme.fancy?0:28
        background:Rectangle {color:Theme.fancy?'transparent':Theme.fill;border.color:Theme.fancy?'transparent':Theme.separator;radius:3}
        contentItem:ColumnLayout {spacing:Theme.fancy?8:6
    RowLayout {Layout.fillWidth:true;spacing:6;Layout.topMargin:Theme.fancy?0:-32;Layout.bottomMargin:Theme.fancy?0:8
                Item {Layout.fillWidth:true}
                Capsule {objectName:'mainAccountsTab';Layout.minimumWidth:0;text:Theme.fancy?I18n.t('Main accounts'):I18n.t('Hoofdaccounts');
                    background:Rectangle {color:Theme.fancy?'transparent':parent.selected?Theme.fill:Theme.separator;border.color:Theme.separator;radius:8;ButtonGlass {anchors.fill:parent;visible:Theme.fancy;control:parent.parent}}
                    contentItem:Label {text:parent.text;color:Theme.text;horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter;font.pixelSize:14*Theme.textScale}
                    Layout.preferredWidth:Theme.fancy?-1:185;selectorMaterial:true;selected:!composer.service||composer.service.recipientMode==='main'
                    enabled:!!composer.service&&!composer.service.sending&&!composer.service.deliveryLocked
                    Accessible.name:I18n.t('Main accounts, ')+(composer.service?composer.service.selectedRecipients.filter(r=>!r.coaccount).length:0)+I18n.t(' selected recipients')
                    onClicked:{composer.suggestionsDismissed=false;composer.service.setRecipientMode('main');composer.service.updateRecipientQuery(composer.activeRecipientInput.text);composer.activeRecipientInput.forceActiveFocus();composer.updateSuggestions()}}
                Capsule {objectName:'coAccountsTab';Layout.minimumWidth:0;text:I18n.t('Co-accounts');
                    background:Rectangle {color:Theme.fancy?'transparent':parent.selected?Theme.fill:Theme.separator;border.color:Theme.separator;radius:8;ButtonGlass {anchors.fill:parent;visible:Theme.fancy;control:parent.parent}}
                    contentItem:Label {text:parent.text;color:Theme.text;horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter;font.pixelSize:14*Theme.textScale}
                    Layout.preferredWidth:Theme.fancy?-1:185;selectorMaterial:true;selected:!!composer.service&&composer.service.recipientMode==='coaccounts'
                    enabled:!!composer.service&&!composer.service.coaccountsUnavailable&&!composer.service.sending&&!composer.service.deliveryLocked
                    Accessible.description:composer.service&&composer.service.coaccountsUnavailable?I18n.t('Your school account does not allow messaging co-accounts.'):I18n.t('Search co-accounts, such as parents.')
                    Accessible.name:I18n.t('Co-accounts, ')+(composer.service?composer.service.selectedRecipients.filter(r=>r.coaccount).length:0)+I18n.t(' selected recipients')
                    onClicked:{composer.suggestionsDismissed=false;composer.service.setRecipientMode('coaccounts');composer.service.updateRecipientQuery(composer.activeRecipientInput.text);composer.activeRecipientInput.forceActiveFocus();composer.updateSuggestions()}}
    }
    RecipientRow {id:toRecipients;field:'To';nextInput:ccRecipients.input}
    RecipientRow {id:ccRecipients;field:'Cc';nextInput:bccRecipients.input}
    RecipientRow {id:bccRecipients;field:'Bcc';nextInput:subject}
    Popup {id:recipientPopup;objectName:'recipientDropdown';parent:Theme.fancy?Overlay.overlay:composer.contentItem;z:100
        popupType:Popup.Item;modal:false;focus:false;closePolicy:Popup.CloseOnPressOutside; padding:8
        width:Math.max(0,Math.min(activeRecipientInput?activeRecipientInput.width:0,(parent?parent.width:composer.width)-24))
        onClosed:{composer.suggestionsDismissed=true;composer.pickerRequested=false}
        background:Surface {radius:Theme.fancy?14:3;strong:true}
        contentItem:ColumnLayout {spacing:6
            PointHandler {onActiveChanged:if(active)composer.pressedInside=true}
            Label {objectName:'recipientModeNotice';Layout.fillWidth:true;Layout.preferredHeight:32*Theme.textScale;textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.secondary;font.pixelSize:12*Theme.textScale
                text:composer.service&&composer.service.coaccountsUnavailable?I18n.t('Your school account does not allow messaging co-accounts.'):composer.service&&composer.service.searching?I18n.t('Finding recipients…'):composer.service&&composer.service.recipientMode==='coaccounts'?I18n.t('Choose a co-account linked to the school account.'):I18n.t('Search people, classes and school groups.')}
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
                        background:Rectangle {radius:Theme.fancy?10:3;color:choice.down?Theme.alpha(Theme.text,.14):choice.hovered||choice.visualFocus?Theme.alpha(Theme.text,.08):'transparent'
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
                    visible:choices.count===0;text:I18n.t(composer.service?.error||'')||(composer.service?.searching?I18n.t('Searching…'):I18n.t(composer.service?.status||'')||(composer.activeRecipientInput.text.trim().length<2?I18n.t('Type at least two characters to find recipients.'):I18n.t('Suggestions will appear here.')))}
            }
        }
    }
    RowLayout {Layout.fillWidth:true;spacing:8
        Label {text:Theme.fancy?I18n.t('Subject'):I18n.t('Onderwerp:');horizontalAlignment:Text.AlignRight;textFormat:Text.PlainText;color:Theme.secondary;Layout.preferredWidth:composer.recipientLabelWidth}
        TextField {id:subject;objectName:'composeSubject';Layout.fillWidth:true;implicitHeight:Theme.fancy?44:34;maximumLength:250
            Accessible.name:I18n.t('Message subject');selectByMouse:true;color:Theme.text;readOnly:!!composer.service&&(composer.service.sending||composer.service.deliveryLocked)
            onTextEdited:composer.saveContent()
            onActiveFocusChanged:if(activeFocus)recipientPopup.close()
            background:Surface {radius:Theme.fancy?12:3}}
        Item {Layout.preferredWidth:44}
    }
        }
    }
    RowLayout {id:composeActions;Layout.fillWidth:true;Layout.topMargin:12;Layout.bottomMargin:8
        Item {Layout.fillWidth:true}
        Capsule {text:Theme.fancy?I18n.t('Template'):I18n.t('Sjabloon');symbol:'note';onClicked:templateMenu.open()
            PlannerMenu {id:templateMenu;PlannerMenuItem {text:I18n.t('Begroeting');onTriggered:{body.insert(body.cursorPosition,'<p>Beste,</p><p><br></p><p>Met vriendelijke groeten,</p>');composer.saveContent()}}}}
        Capsule {id:attachButton;objectName:'attachMessageFile';text:Theme.fancy?I18n.t('Attach files'):I18n.t('Bijlagen');symbol:'clip';enabled:!!composer.service&&!composer.service.busy&&!composer.service.deliveryLocked
            KeyNavigation.tab:sendButton;KeyNavigation.backtab:body;onClicked:attachmentPicker.open()}
    }
    MessageEditorTools {id:editorTools;Layout.fillWidth:true;editor:body;service:composer.service;onEdited:composer.saveContent()}

    ScrollView {Layout.fillWidth:true;Layout.preferredHeight:Theme.fancy?190*Theme.textScale:Math.max(180*Theme.textScale,composer.scrollView.height-recipientForm.implicitHeight-(composer.dockSend?0:composeToolbar.implicitHeight+recipientSummaryLabel.implicitHeight+recipientSummary.implicitHeight)-composeActions.implicitHeight-editorTools.implicitHeight-80*Theme.textScale)
        TextArea {id:body;objectName:'composeBody';textFormat:TextEdit.RichText;persistentSelection:true;wrapMode:TextEdit.Wrap;selectByMouse:true
            function pasteSanitized(){if(readOnly||!composer.service)return;let start=selectionStart;remove(start,selectionEnd);insert(start,composer.service.formatting.clipboardHtml());composer.saveContent()}
            Keys.onPressed:function(event){if(event.matches(StandardKey.Paste)){pasteSanitized();event.accepted=true}}
            KeyNavigation.priority:KeyNavigation.BeforeItem;KeyNavigation.tab:attachButton;KeyNavigation.backtab:subject
            Accessible.name:I18n.t('Message text');color:Theme.text;readOnly:!!composer.service&&(composer.service.sending||composer.service.deliveryLocked)
            onTextChanged:if(composer.service&&activeFocus)composer.saveContent()
            onActiveFocusChanged:if(activeFocus)recipientPopup.close()
            background:Rectangle {radius:Theme.fancy?12:3;color:Theme.fancy?Theme.fill:Theme.elevated;border.color:Theme.separator}}
    }
    Repeater {model:composer.service?composer.service.attachments:[]
        RowLayout {required property var modelData;required property int index;Layout.fillWidth:true
            Label {Layout.fillWidth:true;text:modelData.name+' · '+Math.ceil(modelData.bytes/1024)+' KB';textFormat:Text.PlainText;elide:Text.ElideMiddle;color:Theme.text}
            Capsule {text:I18n.t('Remove');Accessible.name:I18n.t('Remove attachment ')+modelData.name;enabled:!!composer.service&&!composer.service.sending&&!composer.service.deliveryLocked
                onClicked:composer.service.removeAttachment(index)}}
    }
    Label {Layout.fillWidth:true;visible:!!composer.service&&!!composer.service.error&&!recipientPopup.visible;text:I18n.t(composer.service?composer.service.error:'')
        textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.text;font.weight:Font.DemiBold}
    Label {Layout.fillWidth:true;visible:!!composer.service&&!!composer.service.status;text:I18n.t(composer.service?composer.service.status:'')
        textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.secondary}
    footer:Component {Pane {padding:12;leftPadding:composer.bodyMargin;rightPadding:composer.bodyMargin;background:Rectangle {color:Theme.elevated}
        contentItem:RowLayout {spacing:8
        LayoutItemProxy {target:composeToolbar;visible:composer.dockSend}
        Label {Layout.fillWidth:true;horizontalAlignment:Theme.fancy?Text.AlignLeft:Text.AlignRight;text:Theme.fancy?I18n.t('Drafts stay on this device for this account.'):composer.service&&composer.service.savedAt?I18n.t('⟳ Lokaal opgeslagen als concept om ')+Qt.formatDateTime(new Date(composer.service.savedAt),'hh:mm'):I18n.t('Concept wordt lokaal op dit apparaat bewaard.');textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.secondary;font.pixelSize:12*Theme.textScale}
        Capsule {objectName:'startNewDraft';visible:!!composer.service&&composer.service.deliveryLocked;text:I18n.t('New message');enabled:!!composer.service&&!composer.service.busy
            onClicked:if(composer.service.newDraft())composer.loadDraft()}

    }
    }}
    FileDialog {id:attachmentPicker;title:I18n.t('Attach files');fileMode:FileDialog.OpenFiles
        onAccepted:if(composer.service)composer.service.addAttachments(selectedFiles)}
}



