import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ColumnLayout {
    id: planner
    required property var app
    signal focusTask(string taskId,string title,bool done)
    signal editNote(string taskId,string title,string note)
    property string course: 'All courses'
    property bool pinsOnly: false
    property string kind: 'All types'
    property bool completedOpen: false
    property bool entryPending:true
    property int entryFrames:0
    property bool centeredEntry:false
    function requestEntry(){entryPending=true;entryFrames=0;app.headerCollapsed=false;scrollMotion.stop();list.cancelFlick();Qt.callLater(list.positionEntry)}
    Component.onCompleted:requestEntry()
    onVisibleChanged:if(visible)requestEntry()
    Connections {target:tasks;function onChoicesChanged(){if(planner.visible)planner.requestEntry()}}
    property int activeRemovals:0
    property bool keepCompletionTop:false
    function finishFeedback(){Qt.callLater(function(){
        planner.activeRemovals=Math.max(0,planner.activeRemovals-1)
        if(!planner.activeRemovals&&planner.keepCompletionTop&&planner.visible){list.resetTop();app.headerCollapsed=false}
    })}
    readonly property bool typeMenuVisible: typePicker.popup.visible
    spacing: 15
    function applyFilters(){scrollMotion.stop();tasks.filter(app.searchText,course,kind,pinsOnly);Qt.callLater(list.resetTop)}
    function benchmarkScroll(f){list.contentY=list.originY+Math.max(0,list.contentHeight-list.height)*f}
    function benchmarkSearch(text){app.searchText=text;applyFilters()}
    function focusSearch(){app.searchOpen=true;app.searchFocus()}
    Connections {target:app;function onSearchTextChanged(){if(planner.visible)debounce.restart()} function onSectionChanged(){if(app.section>=2)return;course='All courses';kind='All types';tasks.setSection(app.section);applyFilters();requestEntry()}}
    Timer {id:debounce;interval:140;onTriggered:planner.applyFilters()}
    Connections {target:Theme;function onTextScaleChanged(){planner.requestEntry()}}
    Item {id:chipsSlot;objectName:'filterSlot';Layout.fillWidth:true;Layout.leftMargin:-10;Layout.rightMargin:-10;implicitHeight:56
    Flickable {
        id:chips;objectName:'filterChips';parent:app.controlsLayer;width:chipsSlot.width;height:chipsSlot.height;clip:true
        readonly property point origin:app.controlPosition(chipsSlot)
        x:origin.x;y:origin.y;visible:planner.visible&&!app.focusOpen
        contentWidth:chipRow.width+20;contentHeight:height;flickableDirection:Flickable.HorizontalFlick;boundsBehavior:Flickable.StopAtBounds;acceptedButtons:Qt.LeftButton
        Row {id:chipRow;spacing:8;x:10;y:8
            Item {width:typePicker.occupiedWidth;height:typePicker.height
            GlassComboBox {id:typePicker;objectName:'typeFilter';selectorMaterial:true;backdrop:app.controlsBackdrop;width:Math.max(112,implicitContentWidth+46)*Theme.textScale;height:40;model:tasks.kinds;currentIndex:Math.max(0,tasks.kinds.indexOf(planner.kind));Accessible.name:'Filter by assignment type'
                onActivated:{planner.kind=currentText;planner.applyFilters()}
            }
            }
            Repeater {model:tasks.courses
                Capsule {objectName:'courseFilter';selectorMaterial:true;backdrop:app.controlsBackdrop;glassTracking:chips.contentX+chips.y;required property string modelData;text:modelData==='All courses'?'All':modelData;selected:planner.course===modelData;height:40;font.pixelSize:13*Theme.textScale
                    onClicked:{planner.course=modelData;planner.applyFilters()}}
            }
            Capsule {selectorMaterial:true;backdrop:app.controlsBackdrop;text:'Pinned only';symbol:'pin';selected:planner.pinsOnly;onClicked:{planner.pinsOnly=!planner.pinsOnly;planner.applyFilters()}}
        }
        SmoothScroll { view:chips; horizontal:true }
    }
    }
    ListView {
        id:list;objectName:'taskList';
        opacity:planner.entryPending?0:1
        function positionEntry(){
            if(!planner.visible||height<=0)return
            forceLayout()
            let index=app.section===0&&!app.searchText.trim()?tasks.todayIndex():-1
            planner.centeredEntry=index>=0
            if(index>=0)positionViewAtIndex(index,ListView.Center)
            else positionViewAtBeginning()
        }
        function resetTop(){planner.centeredEntry=false;scrollMotion.stop();forceLayout();positionViewAtBeginning()}
        Layout.fillWidth:true;Layout.fillHeight:true;Layout.leftMargin:-16;Layout.rightMargin:-16
        clip:false;model:planner.visible?tasks:null;reuseItems:true;cacheBuffer:180;spacing:0;topMargin:planner.centeredEntry?height/2:0;bottomMargin:Math.max(100*Theme.textScale,planner.centeredEntry?height/2:0)
        displayMarginBeginning:220*Theme.textScale
        Connections {target:app
            function onFrameSwapped(){
                if(!planner.entryPending||!planner.visible||list.height<=0)return
                list.positionEntry()
                if(++planner.entryFrames>=2){planner.entryPending=false;app.sceneReady=true}
            }
        }
        boundsBehavior:Flickable.DragOverBounds;acceptedButtons:Qt.LeftButton;keyNavigationEnabled:true;activeFocusOnTab:true;Accessible.name:'Tasks grouped by due date'
        ScrollBar.vertical:ScrollBar{}
        SmoothScroll { id:scrollMotion; objectName:'taskScrollMotion'; view:list }
        removeDisplaced:Transition {NumberAnimation {property:'y';duration:Theme.motion?260:0;easing.type:Easing.OutCubic}}
        onWidthChanged:if(planner.entryPending)Qt.callLater(positionEntry)
        onContentYChanged:{
            if(planner.entryPending)return
            if(planner.activeRemovals&&(dragging||scrollMotion.glide.running))planner.keepCompletionTop=false
            if(planner.visible&&!planner.activeRemovals)app.headerCollapsed=app.sceneReady&&contentY-originY>80&&!app.searchOpen
        }
        header:Column {
            spacing:10
            x:16;width:list.width-32;visible:app.section===0&&!app.searchText&&planner.course==='All courses'&&planner.kind==='All types'&&!planner.pinsOnly
            height:visible?overview.implicitHeight+58:0
            Label {textFormat:Text.PlainText;text:'Week ahead';font.pixelSize:24*Theme.textScale;font.bold:true;color:Theme.text;x:0;y:4}
            Surface {
                id:overview;backdrop:app.sceneBackdrop;tracking:list.contentY+list.y+planner.y;refraction:20;width:parent.width;implicitHeight:Math.max(184*Theme.textScale,overviewContent.implicitHeight+36)
                ColumnLayout {id:overviewContent;anchors.fill:parent;anchors.margins:18;spacing:8
                    Label {textFormat:Text.PlainText;text:tasks.weekSummary;color:Theme.text;font.pixelSize:14*Theme.textScale;Layout.fillWidth:true;wrapMode:Text.Wrap}
                    RowLayout {Layout.fillWidth:true;Layout.fillHeight:true;spacing:8
                        Repeater {model:tasks.week
                            Column {required property var modelData;Layout.fillWidth:true;Layout.alignment:Qt.AlignBottom;spacing:4
                                Accessible.role:Accessible.StaticText;Accessible.name:modelData.label+': '+modelData.count+' tasks'
                                Label {textFormat:Text.PlainText;text:parent.modelData.count||'';anchors.horizontalCenter:parent.horizontalCenter;color:Theme.text;font.pixelSize:12;font.weight:Font.DemiBold}
                                Rectangle {anchors.horizontalCenter:parent.horizontalCenter;width:Math.min(36,parent.width);height:parent.modelData.barHeight;radius:7;color:!parent.modelData.count?'#32465d':parent.modelData.test?Theme.red:parent.modelData.kind==='Taak'?Theme.blue:Theme.orange
                                    Behavior on height {NumberAnimation{duration:Theme.motion?300:0;easing.type:Easing.OutCubic}}}
                                Label {textFormat:Text.PlainText;text:parent.modelData.label;anchors.horizontalCenter:parent.horizontalCenter;color:Theme.secondary;font.pixelSize:12;font.weight:Font.DemiBold}
                            }
                        }
                    }
                    Label {textFormat:Text.PlainText;text:'Busier days are taller · tests count extra';color:Theme.secondary;font.pixelSize:11}
                }
            }
        }
        section.property:'group';section.criteria:ViewSection.FullString
        // Qt updates the section context when reusing headings; a required property can retain its old value.
        section.delegate:Item {x:16;width:list.width-32;height:56*Theme.textScale
            Label {textFormat:Text.PlainText;anchors.left:parent.left;anchors.bottom:parent.bottom;anchors.bottomMargin:10;text:section;font.pixelSize:24*Theme.textScale;font.bold:true;color:Theme.text}
            Label {textFormat:Text.PlainText;anchors.right:parent.right;anchors.rightMargin:8;anchors.bottom:parent.bottom;anchors.bottomMargin:13;text:tasks.groupCounts[section]||0;font.pixelSize:13*Theme.textScale;font.weight:Font.DemiBold;color:Theme.secondary}}
        delegate:Item {
            id:taskRow;objectName:'taskDelegate'
            required property string taskId
            required property string title
            required property string course
            required property string kind
            required property string body
            required property string posted
            required property string due
            required property bool done
            required property bool pinned
            required property string note
            required property var indicators
            required property bool first
            required property bool last
            required property int index
            property bool finishing:false
            property bool pooled:false
            function complete(){
                let id=taskId,target=!done,host=planner.app
                let feedback=Theme.motion&&target&&(app.section===1||!planner.completedOpen&&!app.searchText.trim())
                if(feedback){if(!planner.activeRemovals)planner.keepCompletionTop=list.atYBeginning;finishing=true;planner.activeRemovals++}
                let saved=feedback?tasks.complete(id):tasks.change(id,'done',target)
                if(saved){if(feedback)completionExit.start();host.notify(target?'Task completed':'Task restored')}
                else{if(finishing)planner.finishFeedback();finishing=false;check.checked=Qt.binding(function(){return taskRow.finishing||taskRow.done})}
            }
            width:list.width-32;height:Math.max(110*Theme.textScale,row.implicitHeight+30);opacity:finishing?1:done?.55:1
            ListView.onPooled:{pooled=true;if(finishing){if(index>=0)planner.keepCompletionTop=false;completionExit.stop();planner.finishFeedback();finishing=false}}
            ListView.onReused:{completionExit.stop();if(finishing)planner.finishFeedback();finishing=false;opacity=Qt.binding(function(){return taskRow.finishing?1:taskRow.done?.55:1});pooled=false}
            Component.onDestruction:if(finishing)planner.finishFeedback()
            SequentialAnimation {id:completionExit
                PauseAnimation {duration:200}
                NumberAnimation {target:taskRow;property:'opacity';to:0;duration:300;easing.type:Easing.OutCubic}
            }
            transform:Translate{x:16}
            // Clip only internal slice joins; keep the group's exterior corners and shadows intact.
            Item {objectName:'taskSurfaceClip';x:-16;y:taskRow.first?-16:0;width:parent.width+32
                height:parent.height+(taskRow.first?16:0)+(taskRow.last?16:0);clip:true
                Surface {sheen:false;continuous:true;tracking:list.contentY+list.y+planner.y;refraction:18
                    x:16;y:taskRow.first?16:-52;width:taskRow.width
                    height:taskRow.height+(taskRow.first?0:52)+(taskRow.last?0:52)}
            }
            Rectangle {x:4;y:taskRow.first?4:0;width:parent.width-8;height:parent.height-(taskRow.first?4:0)-(taskRow.last?4:0)
                topLeftRadius:taskRow.first?28:0;topRightRadius:topLeftRadius
                bottomLeftRadius:taskRow.last?28:0;bottomRightRadius:bottomLeftRadius
                color:Theme.fill;opacity:hover.hovered||(taskRow.ListView.isCurrentItem&&list.activeFocus)?.5:0;Behavior on opacity{NumberAnimation{duration:Theme.motion?150:0}}}
            HoverHandler{id:hover}
            RowLayout {
                id:row;anchors.left:parent.left;anchors.right:parent.right;anchors.verticalCenter:parent.verticalCenter;anchors.margins:16;spacing:14
                TaskCheck {id:check;animateFeedback:!taskRow.pooled;Layout.alignment:Qt.AlignTop;objectName:'done-'+taskRow.taskId;checked:taskRow.finishing||taskRow.done;Accessible.name:(taskRow.done?'Restore ':'Complete ')+taskRow.title
                    onClicked:taskRow.complete()
                }
                ColumnLayout {
                    Layout.fillWidth:true;spacing:3
                    RowLayout {Layout.fillWidth:true
                        Label {textFormat:Text.PlainText;text:taskRow.course;color:Theme.text;font.pixelSize:15*Theme.textScale;font.weight:Font.Bold;elide:Text.ElideRight;Layout.minimumWidth:0;Layout.maximumWidth:row.width*.35}
                        Rectangle {color:Theme.dark?Theme.alpha(Theme.badge,.55):Theme.alpha(Theme.typeColor(taskRow.kind),.2);radius:12;implicitWidth:Math.min(badge.implicitWidth+16,row.width*.24);implicitHeight:badge.implicitHeight+6
                            Label {textFormat:Text.PlainText;id:badge;anchors.centerIn:parent;width:parent.width-16;text:taskRow.kind;elide:Text.ElideRight;color:Theme.badgeInk(taskRow.kind);font.pixelSize:10*Theme.textScale;font.bold:true}
                            HoverHandler {id:badgeHover}
                            GlassToolTip {requested:badge.truncated&&(badgeHover.hovered||check.visualFocus);text:taskRow.kind}
                        }
                        Repeater {model:taskRow.indicators
                            FocusScope {id:statusHint;required property var modelData;implicitWidth:22;implicitHeight:24;activeFocusOnTab:true
                                Accessible.role:Accessible.StaticText;Accessible.name:modelData.label
                                Icon {anchors.centerIn:parent;width:18;height:18;name:parent.modelData.icon;ink:parent.modelData.tone==='purple'?Theme.purple:Theme.orange}
                                Rectangle {anchors.fill:parent;radius:6;color:'transparent';border.width:parent.activeFocus?1:0;border.color:Theme.text}
                                HoverHandler {id:indicatorHover}
                                GlassToolTip {requested:indicatorHover.hovered||statusHint.activeFocus;text:statusHint.modelData.label}
                            }
                        }
                        Item {Layout.fillWidth:true}
                    }
                    Label {textFormat:Text.PlainText;text:taskRow.title;Layout.fillWidth:true;wrapMode:Text.Wrap;maximumLineCount:2;elide:Text.ElideRight;font.pixelSize:15*Theme.textScale;font.weight:Font.Medium;font.strikeout:taskRow.done;color:Theme.text}
                    Label {textFormat:Text.PlainText;visible:taskRow.body!=='';text:taskRow.body;Layout.fillWidth:true;wrapMode:Text.Wrap;maximumLineCount:2;elide:Text.ElideRight;font.pixelSize:13*Theme.textScale;color:Theme.secondary}
                    Label {textFormat:Text.PlainText;text:Qt.formatDate(new Date(taskRow.due+'T12:00:00'),'ddd, d MMM')+'  ·  posted '+Qt.formatDate(new Date(taskRow.posted+'T12:00:00'),'ddd d MMM');Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.tertiary;font.pixelSize:12*Theme.textScale}
                    Label {textFormat:Text.PlainText;visible:taskRow.note!=='';text:taskRow.note;Layout.fillWidth:true;elide:Text.ElideRight;color:Theme.orange;font.italic:true;font.pixelSize:13*Theme.textScale}
                    TapHandler {onTapped:planner.editNote(taskRow.taskId,taskRow.title,taskRow.note)}
                }
                Capsule {text:taskRow.pinned?'Unpin':'Pin';symbol:'pin';iconOnly:true;quiet:true;opacity:hover.hovered||taskRow.pinned||activeFocus?1:0;onClicked:{let host=planner.app;if(tasks.change(taskRow.taskId,'pinned',!taskRow.pinned))host.notify('Pin updated')}}
                Capsule {visible:!app.production||backend.canFocus(taskRow.taskId);objectName:'focus-'+taskRow.taskId;text:'Focus';symbol:'focus';iconOnly:true;quiet:true;opacity:hover.hovered||activeFocus?1:0;onClicked:planner.focusTask(taskRow.taskId,taskRow.title,taskRow.done)}
            }
            Rectangle {visible:!taskRow.last;x:58;width:parent.width-74;height:1;anchors.bottom:parent.bottom;color:Theme.separator}
        }
        footer:Column {objectName:'taskFooter';visible:!planner.activeRemovals;x:16;width:list.width-32;spacing:18;topPadding:24*Theme.textScale
            Label {textFormat:Text.PlainText;visible:tasks.count===0;text:app.section===1?'All caught up · no missed tasks':'No matching tasks';font.pixelSize:22*Theme.textScale;color:Theme.text;padding:28;anchors.horizontalCenter:parent.horizontalCenter}
            Capsule {id:completedButton;visible:tasks.completedCount>0&&app.section===0;text:'Completed  '+tasks.completedCount;quiet:true;selectorMaterial:true
                implicitHeight:Math.max(38,contentItem.implicitHeight+16)
                contentItem:Item {
                    implicitWidth:completedContent.implicitWidth;implicitHeight:completedContent.implicitHeight
                    RowLayout {id:completedContent;anchors.centerIn:parent;spacing:8
                        Icon {name:'chevron';ink:completedButton.labelInk;Layout.preferredWidth:16*Theme.textScale;Layout.preferredHeight:16*Theme.textScale;rotation:planner.completedOpen?0:-90
                            Behavior on rotation{enabled:Theme.motion;SpringAnimation{spring:4;damping:.9}}}
                        Text {textFormat:Text.PlainText;text:'Completed';color:completedButton.labelInk;font:completedButton.font}
                        Text {textFormat:Text.PlainText;text:tasks.completedCount;color:Theme.secondary;font:completedButton.font}
                    }
                }
                onClicked:{planner.completedOpen=!planner.completedOpen;tasks.expandCompleted(planner.completedOpen)}}
        }
        Keys.onSpacePressed:if(currentItem)currentItem.complete()
        Keys.onReturnPressed:if(currentItem)planner.editNote(currentItem.taskId,currentItem.title,currentItem.note)
    }
}
