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
    property bool entryPending:true
    property bool editMotion:false
    onEditMotionChanged:if(!editMotion&&list)list.settleReflow()
    function requestEntry(){editMotion=false;entryPending=true;app.headerCollapsed=false;scrollMotion.stop();list.cancelFlick();Qt.callLater(list.positionEntry)}
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
    function applyFilters(){editMotion=false;scrollMotion.stop();tasks.filter(app.searchText,course,kind,pinsOnly);Qt.callLater(list.resetTop)}
    function benchmarkScroll(f){list.contentY=list.originY+Math.max(0,list.contentHeight-list.height)*f}
    function benchmarkSearch(text){app.searchText=text;applyFilters()}
    function focusSearch(){app.searchOpen=true;app.searchFocus()}
    Connections {target:app;function onSearchTextChanged(){if(planner.visible)debounce.restart()} function onSectionChanged(){if(app.section>=2)return;course='All courses';kind='All types';tasks.setSection(app.section);applyFilters();requestEntry()}}
    Timer {id:debounce;interval:140;onTriggered:planner.applyFilters()}
    Connections {target:Theme;function onTextScaleChanged(){planner.requestEntry()}}
    Connections {target:app.production?backend.features:null
        // Capture the beginning before a delivered summary changes the graph's height.
        function onChanged(){if(planner.visible&&list.atYBeginning&&!list.moving&&!scrollMotion.active&&!scrollMotion.glide.running)list.headerTopPending=true}
    }
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
        property real previousOriginY:0
        property bool headerTopPending:false
        onOriginYChanged:{
            let wasAtTop=Math.abs(contentY-previousOriginY)<2
            previousOriginY=originY
            // Growing AI content must keep the beginning visible without moving a reader farther down.
            if(wasAtTop&&planner.visible&&!planner.entryPending&&!moving&&!scrollMotion.active&&!scrollMotion.glide.running)contentY=originY
        }
        opacity:planner.entryPending?0:1
        function positionEntry(){
            if(!planner.visible||height<=0)return
            forceLayout()
            positionViewAtBeginning()
        }
        function resetTop(){scrollMotion.stop();forceLayout();positionViewAtBeginning()}
        Layout.fillWidth:true;Layout.fillHeight:true;Layout.leftMargin:-16;Layout.rightMargin:-16
        clip:false;model:planner.visible?tasks:null;reuseItems:true;cacheBuffer:180;spacing:0;topMargin:0;bottomMargin:100*Theme.textScale
        displayMarginBeginning:220*Theme.textScale
        property var reflowPositions:({})
        property bool reflowQueued:false
        property int pendingLifetimes:0
        function ownsHeading(heading){
            for(let item of contentItem.children)
                if(item.objectName==='taskDelegate'&&item.index>=0&&!item.retiring&&!item.pooled&&item.first&&
                   heading.motionKey==='section:'+item.group&&Math.abs(item.y-heading.y-heading.height)<1){
                    for(let candidate of contentItem.children)
                        if(candidate.motionKey===heading.motionKey&&candidate.visible&&Math.abs(item.y-candidate.y-candidate.height)<1)return candidate===heading
                }
            return false
        }
        // Qt changes section ownership and originY during first-row removal.
        // Compensate actual visible positions, then animate only transforms.
        function settleReflow(){
            reflowQueued=false;reflowPositions=({});pendingLifetimes=0
            for(let item of contentItem.children)if(typeof item.settleReflow==='function')item.settleReflow()
        }
        function rememberPositions(){
            if(!planner.editMotion||reflowQueued)return
            reflowQueued=true
            let positions={}
            for(let item of contentItem.children)if(item.motionKey!==undefined&&item.visible&&item.opacity>0&&!item.retiring&&!item.pooled)
                positions[item.motionKey]=item.mapToItem(list,0,0).y
            reflowPositions=positions
        }
        function restorePositions(){
            if(!reflowQueued)return
            if(!planner.editMotion){reflowQueued=false;return}
            forceLayout()
            for(let item of contentItem.children)if(item.motionKey!==undefined&&item.visible&&item.opacity>0&&!item.retiring&&!item.pooled&&reflowPositions[item.motionKey]!==undefined)
                item.reflowFrom(reflowPositions[item.motionKey],pendingLifetimes>0)
            if(pendingLifetimes)return
            reflowQueued=false
            reflowPositions=({})
        }
        Connections {target:tasks
            function onRowsAboutToBeRemoved(){list.rememberPositions()}
            function onRowsAboutToBeInserted(){list.rememberPositions()}
            function onRowsRemoved(){Qt.callLater(list.restorePositions)}
            function onRowsInserted(){Qt.callLater(list.restorePositions)}
        }
        Connections {target:Theme;function onMotionChanged(){if(!Theme.motion)list.settleReflow()}}
        Connections {target:app
            function onAfterAnimating(){
                if(list.headerTopPending){
                    list.headerTopPending=false
                    if(planner.visible&&!list.moving&&!scrollMotion.active&&!scrollMotion.glide.running)list.positionViewAtBeginning()
                }
                if(!planner.entryPending||!planner.visible||list.height<=0)return
                app.settleHeader()
                list.positionEntry()
                planner.entryPending=false;app.sceneReady=true
            }
        }
        boundsBehavior:Flickable.StopAtBounds;acceptedButtons:Qt.LeftButton;keyNavigationEnabled:true;activeFocusOnTab:true;Accessible.name:'Tasks grouped by due date'
        ScrollBar.vertical:ScrollBar{id:scrollBar;parent:planner.parent;visible:planner.visible;x:planner.x+list.x+list.width-width-16;y:planner.y+list.y;height:list.height}
        SmoothScroll { id:scrollMotion; objectName:'taskScrollMotion'; view:list }
        add:Transition {enabled:planner.editMotion;ParallelAnimation {
            NumberAnimation {property:'opacity';from:0;duration:Theme.motion?160:80;easing.type:Easing.OutCubic}
            NumberAnimation {property:'scale';from:Theme.motion?.98:1;to:1;duration:Theme.motion?220:0;easing.type:Easing.OutCubic}
        }}
        remove:Transition {enabled:planner.editMotion&&list.count>0;ParallelAnimation {
            NumberAnimation {property:'opacity';to:0;duration:Theme.motion?180:80;easing.type:Easing.InCubic}
            NumberAnimation {property:'scale';to:Theme.motion?.98:1;duration:Theme.motion?220:0;easing.type:Easing.OutCubic}
        }}
        onWidthChanged:if(planner.entryPending)Qt.callLater(positionEntry)
        onContentYChanged:{
            if(planner.entryPending)return
            if(planner.activeRemovals&&(dragging||scrollMotion.glide.running))planner.keepCompletionTop=false
            if(planner.visible&&!planner.activeRemovals&&(atYBeginning||moving||scrollMotion.active||scrollMotion.glide.running||scrollBar.pressed))app.headerCollapsed=app.sceneReady&&contentY-originY>80&&!app.searchOpen
        }
        header:Column {
            readonly property bool showWeek:!app.searchText&&planner.course==='All courses'&&planner.kind==='All types'&&!planner.pinsOnly
            spacing:10
            x:16;width:list.width-32;visible:app.section===0
            height:visible?implicitHeight:0
            Label {visible:parent.showWeek;textFormat:Text.PlainText;text:'Week ahead';font.pixelSize:24*Theme.textScale;font.bold:true;color:Theme.text;x:0;y:4}
            Surface {
                visible:parent.showWeek
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
                Capsule {objectName:'summariseWeek';text:app.production&&backend.features.featureBusy?'Working…':'Summarise with Gemini';symbol:'ai';Layout.alignment:Qt.AlignLeft;Layout.maximumWidth:overviewContent.width
                    opacity:app.production&&backend.features.aiAvailable?1:.45;enabled:app.production&&!backend.features.featureBusy;Accessible.description:'Sends this week’s unfinished task instructions to Gemini. Dates stay unchanged. A Gemini API key is required.';onClicked:app.requestAI('week')}
                Label {visible:app.production&&backend.features.weeklySummaryReady&&backend.features.weeklySummary.length===0;text:'No unfinished tasks in the next seven days.';textFormat:Text.PlainText;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text}
                Repeater {model:app.production?backend.features.weeklySummary:[]
                    ColumnLayout {required property var modelData;Layout.fillWidth:true
                        Label {text:modelData.date;textFormat:Text.PlainText;color:Theme.text;font.bold:true}
                        Repeater {model:parent.modelData.tasks
                            Label {required property var modelData;text:'• '+modelData.summary;textFormat:Text.PlainText;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text}
                        }
                    }
                }
            }
            }
            Row {spacing:10
                Capsule {objectName:'missedButton';text:'Missed · '+tasks.missedTasks.length;onClicked:app.showTaskCollection('missed')}
                Capsule {objectName:'completedButton';text:'Completed · '+tasks.completedCount;onClicked:app.showTaskCollection('completed')}
            }
        }
        section.property:'group';section.criteria:ViewSection.FullString
        // Qt updates the section context when reusing headings; a required property can retain its old value.
        section.delegate:Item {id:heading;x:16;width:list.width-32;height:64*Theme.textScale
            property string motionKey:'section:'+section
            // Qt retains the outgoing row's section while transferring the heading to its successor.
            // Only the heading attached to a live first row may paint or participate in reflow.
            readonly property bool owned:list.ownsHeading(heading)
            opacity:owned?1:0
            onOwnedChanged:if(!owned&&headingMotion)settleReflow()
            onVisibleChanged:if(!visible&&headingMotion)settleReflow()
            onMotionKeyChanged:if(headingMotion)settleReflow()
            property real reflowY:0
            function settleReflow(){headingMotion.stop();reflowY=0}
            function reflowFrom(previousY,hold){headingMotion.stop();reflowY+=previousY-mapToItem(list,0,0).y;if(Theme.motion){if(!hold)headingMotion.start()}else reflowY=0}
            // A scroll-origin correction may move the preceding header while reflow is running.
            transform:Translate {y:planner.editMotion?Math.max(heading.reflowY,list.headerItem?list.headerItem.y+list.headerItem.height-heading.y:heading.reflowY):0}
            NumberAnimation {id:headingMotion;target:heading;property:'reflowY';to:0;duration:240;easing.type:Easing.OutCubic}
            Label {textFormat:Text.PlainText;anchors.left:parent.left;anchors.bottom:parent.bottom;anchors.bottomMargin:10;text:section;font.pixelSize:22*Theme.textScale;font.bold:true;color:Theme.text}
            Label {textFormat:Text.PlainText;anchors.right:parent.right;anchors.rightMargin:8;anchors.bottom:parent.bottom;anchors.bottomMargin:13;text:tasks.groupCounts[section]||0;font.pixelSize:13*Theme.textScale;font.weight:Font.DemiBold;color:Theme.secondary}}
        delegate:Item {
            id:taskRow;objectName:'taskDelegate'
            required property string taskId
            required property string group
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
            property bool retiring:false
            property bool pooled:false
            property int exitRevision:0
            property real retirementY:0
            property string motionKey:'task:'+taskId
            property real reflowY:0
            function settleReflow(){rowMotion.stop();reflowY=0}
            function reflowFrom(previousY,hold){rowMotion.stop();reflowY+=previousY-mapToItem(list,0,0).y;if(Theme.motion){if(!hold)rowMotion.start()}else reflowY=0}
            NumberAnimation {id:rowMotion;target:taskRow;property:'reflowY';to:0;duration:240;easing.type:Easing.OutCubic}
            function complete(){
                let id=taskId,target=!done,host=planner.app
                planner.editMotion=true
                if(tasks.change(id,'done',target))host.notify(target?'Task completed':'Task restored')
                else check.checked=Qt.binding(function(){return taskRow.done})
            }
            width:list.width-32;height:Math.max(76*Theme.textScale,row.implicitHeight+28);opacity:pooled?0:retiring?1:done?.55:1
            enabled:!retiring&&!pooled&&index>=0
            ListView.onRemove:{
                if(planner.editMotion){
                    let revision=++exitRevision
                    if(!planner.activeRemovals)planner.keepCompletionTop=list.atYBeginning
                    retirementY=list.reflowPositions[motionKey]===undefined?mapToItem(list,0,0).y:list.reflowPositions[motionKey]
                    retiring=true;planner.activeRemovals++
                    ListView.delayRemove=true
                    // Keep the visual through Qt's current-item handoff before native removal.
                    // The final empty model needs its own exit because Qt takes a fast-clear path.
                    if(list.count===0)completionExit.start()
                    else {
                        list.pendingLifetimes++
                        Qt.callLater(function(){
                            if(taskRow&&taskRow.exitRevision===revision&&taskRow.retiring)taskRow.ListView.delayRemove=false
                            list.pendingLifetimes=Math.max(0,list.pendingLifetimes-1)
                            Qt.callLater(list.restorePositions)
                        })
                    }
                }
            }
            ParallelAnimation {id:completionExit
                NumberAnimation {target:taskRow;property:'opacity';to:0;duration:Theme.motion?180:80;easing.type:Easing.InCubic}
                NumberAnimation {target:taskRow;property:'scale';to:Theme.motion?.98:1;duration:Theme.motion?220:0;easing.type:Easing.OutCubic}
                onFinished:taskRow.ListView.delayRemove=false
            }
            ListView.onPooled:{exitRevision++;pooled=true;rowMotion.stop();reflowY=0;completionExit.stop();ListView.delayRemove=false;if(retiring){retiring=false;planner.finishFeedback()}}
            ListView.onReused:{exitRevision++;rowMotion.stop();reflowY=0;completionExit.stop();ListView.delayRemove=false;retiring=false;opacity=Qt.binding(function(){return taskRow.pooled?0:taskRow.retiring?1:taskRow.done?.55:1});scale=1;pooled=false}
            Component.onDestruction:if(retiring)planner.finishFeedback()
            // Hold the clicked visual in viewport space while Qt transfers section/origin ownership.
            transform:Translate{x:16;y:planner.editMotion?(taskRow.retiring?taskRow.retirementY-taskRow.y+list.contentY-(1-taskRow.scale)*taskRow.height/2:taskRow.reflowY):0}
            // Clip only internal slice joins; keep the group's exterior corners and shadows intact.
            Item {objectName:'taskSurfaceClip';x:-16;y:taskRow.first?-16:0;width:parent.width+32
                height:parent.height+(taskRow.first?16:0)+(taskRow.last?16:0);clip:true
                Surface {sheen:false;continuous:true;tracking:list.contentY+list.y+planner.y;refraction:18
                    x:16;y:taskRow.first?16:-52;width:taskRow.width
                    height:taskRow.height+(taskRow.first?0:52)+(taskRow.last?0:52)}
            }
            Rectangle {x:4;y:taskRow.first?4:0;width:parent.width-8;height:parent.height-(taskRow.first?4:0)-(taskRow.last?4:0)
                topLeftRadius:taskRow.first?24:0;topRightRadius:topLeftRadius
                bottomLeftRadius:taskRow.last?24:0;bottomRightRadius:bottomLeftRadius
                color:Theme.fill;opacity:hover.hovered||(taskRow.ListView.isCurrentItem&&list.activeFocus)?.5:0;Behavior on opacity{NumberAnimation{duration:Theme.motion?150:0}}}
            HoverHandler{id:hover}
            RowLayout {
                id:row;anchors.left:parent.left;anchors.right:parent.right;anchors.verticalCenter:parent.verticalCenter;anchors.margins:16;spacing:14
                TaskCheck {id:check;animateFeedback:!taskRow.pooled;Layout.alignment:Qt.AlignTop;objectName:'done-'+taskRow.taskId;checked:taskRow.done;Accessible.name:(taskRow.done?'Restore ':'Complete ')+taskRow.title
                    onClicked:taskRow.complete()
                }
                ColumnLayout {
                    Layout.fillWidth:true;spacing:3
                    RowLayout {Layout.fillWidth:true
                        Label {textFormat:Text.PlainText;text:taskRow.course;color:Theme.text;font.pixelSize:15*Theme.textScale;font.weight:Font.DemiBold;elide:Text.ElideRight;Layout.minimumWidth:0;Layout.maximumWidth:row.width*.35}
                        Rectangle {color:Theme.dark?Theme.alpha(Theme.badge,.55):Theme.alpha(Theme.typeColor(taskRow.kind),.2);radius:12;implicitWidth:Math.min(badge.implicitWidth+16,row.width*.24);implicitHeight:badge.implicitHeight+6
                            Label {textFormat:Text.PlainText;id:badge;anchors.centerIn:parent;width:parent.width-16;text:taskRow.kind;elide:Text.ElideRight;color:Theme.badgeInk(taskRow.kind);font.pixelSize:10*Theme.textScale;font.bold:true}
                            HoverHandler {id:badgeHover}
                            GlassToolTip {requested:badge.truncated&&(badgeHover.hovered||check.visualFocus);text:taskRow.kind}
                        }
                        Repeater {model:taskRow.indicators.length
                            FocusScope {id:statusHint;required property int index;readonly property var modelData:taskRow.indicators[index];implicitWidth:22;implicitHeight:24;activeFocusOnTab:true
                                Accessible.role:Accessible.StaticText;Accessible.name:modelData.label
                                Icon {anchors.centerIn:parent;width:18;height:18;name:parent.modelData.icon;ink:parent.modelData.tone==='purple'?Theme.purple:Theme.orange}
                                Rectangle {anchors.fill:parent;radius:6;color:'transparent';border.width:parent.activeFocus?1:0;border.color:Theme.text}
                                HoverHandler {id:indicatorHover}
                                GlassToolTip {requested:indicatorHover.hovered||statusHint.activeFocus;text:statusHint.modelData.label}
                            }
                        }
                        Item {Layout.fillWidth:true}
                    }
                    Label {textFormat:Text.PlainText;text:taskRow.title;Layout.fillWidth:true;wrapMode:Text.Wrap;maximumLineCount:2;elide:Text.ElideRight;font.pixelSize:15*Theme.textScale;font.weight:Font.Normal;font.strikeout:taskRow.done;color:Theme.text}
                    Label {textFormat:Text.PlainText;visible:taskRow.body!=='';text:taskRow.body;Layout.fillWidth:true;wrapMode:Text.Wrap;maximumLineCount:2;elide:Text.ElideRight;font.pixelSize:13*Theme.textScale;color:Theme.secondary}
                    Label {textFormat:Text.PlainText;text:Qt.formatDate(new Date(taskRow.due+'T12:00:00'),'ddd, d MMM')+'  ·  posted '+Qt.formatDate(new Date(taskRow.posted+'T12:00:00'),'ddd d MMM');Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.tertiary;font.pixelSize:12*Theme.textScale}
                    Label {textFormat:Text.PlainText;visible:taskRow.note!=='';text:taskRow.note;Layout.fillWidth:true;elide:Text.ElideRight;color:Theme.orange;font.italic:true;font.pixelSize:13*Theme.textScale}
                    TapHandler {onTapped:planner.editNote(taskRow.taskId,taskRow.title,taskRow.note)}
                }
                Capsule {Layout.preferredWidth:30;Layout.preferredHeight:30;text:taskRow.pinned?'Unpin':'Pin';symbol:'pin';iconOnly:true;quiet:true;opacity:hover.hovered||taskRow.pinned||activeFocus?1:0;onClicked:{let host=planner.app;if(tasks.change(taskRow.taskId,'pinned',!taskRow.pinned))host.notify('Pin updated')}}
                Capsule {Layout.preferredWidth:30;Layout.preferredHeight:30;visible:!app.production||backend.canFocus(taskRow.taskId);objectName:'focus-'+taskRow.taskId;text:'Focus';symbol:'focus';iconOnly:true;quiet:true;opacity:hover.hovered||activeFocus?1:0;onClicked:planner.focusTask(taskRow.taskId,taskRow.title,taskRow.done)}
            }
            Rectangle {visible:!taskRow.last;x:58;width:parent.width-74;height:1;anchors.bottom:parent.bottom;color:Theme.separator}
        }
        footer:Column {objectName:'taskFooter';visible:!planner.activeRemovals;x:16;width:list.width-32;spacing:18;topPadding:24*Theme.textScale
            Label {textFormat:Text.PlainText;visible:tasks.count===0;text:app.section===1?'All caught up · no missed tasks':'No matching tasks';font.pixelSize:22*Theme.textScale;color:Theme.text;padding:28;anchors.horizontalCenter:parent.horizontalCenter}
        }
        Keys.onSpacePressed:if(currentItem)currentItem.complete()
        Keys.onReturnPressed:if(currentItem)planner.editNote(currentItem.taskId,currentItem.title,currentItem.note)
        Keys.onReleased:event=>{event.accepted=false;if([Qt.Key_Up,Qt.Key_Down,Qt.Key_PageUp,Qt.Key_PageDown,Qt.Key_Home,Qt.Key_End].indexOf(event.key)>=0){list.positionViewAtIndex(list.currentIndex,ListView.Contain);Qt.callLater(function(){if(!planner.entryPending)app.headerCollapsed=list.contentY-list.originY>80&&!app.searchOpen})}}
    }
}
