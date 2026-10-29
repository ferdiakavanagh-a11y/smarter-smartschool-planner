import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
ApplicationWindow {
    id:app
    readonly property bool production:typeof backend!=='undefined'
    property bool preferencesReady:false
    property var taskInfo:({})
    property var sectionInfo:({})
    property string detailToken:''
    property string errorText:''
    width:1100;height:800;minimumWidth:focusOpen?360:760;minimumHeight:focusOpen?420:600
    visible:false;title:production?'Smartschool Planner':'Smartschool Planner · demo';color:Theme.bg
    flags:Qt.Window | Qt.FramelessWindowHint | (focusOpen&&focusOnTop?Qt.WindowStaysOnTopHint:0)
    property alias sceneBackdrop:backdrop
    property alias controlsBackdrop:topSource
    property alias controlsLayer:floatingControls
    property alias fancy:themeProxy.fancy
    property alias reducedMotion:themeProxy.reducedMotion
    property alias textScale:themeProxy.textScale
    property bool showSummary:true
    property int datasetIndex:initialCount===0?0:initialCount===36?1:2
    property int fixtureRevision:0
    property var appearance:Theme
    property int section:0
    property bool focusOpen:false
    property bool focusOnTop:false
    property bool searchOpen:false
    property string searchText:''
    property bool headerCollapsed:false
    property bool sceneReady:false
    property bool busy:false
    property string toastText:''
    property var activeToolTip:null
    property rect savedBounds
    property bool wasMaximized:false
    property int previousSection:0
    readonly property bool renderActive:visible&&visibility!==Window.Minimized
    readonly property bool motion:Theme.motion
    property string phase:'idle'
    property var frameSamples:[]
    property real scrollProgress:0
    property int transitionStep:0
    QtObject {id:themeProxy;property bool fancy:Theme.fancy;property bool reducedMotion:Theme.reducedMotion;property real textScale:Theme.textScale
        onFancyChanged:Theme.fancy=fancy;onReducedMotionChanged:Theme.reducedMotion=reducedMotion;onTextScaleChanged:Theme.textScale=textScale}
    Component.onCompleted:{Theme.fancy=initialFancy;Theme.matched=typeof initialMatched!=='undefined'&&initialMatched;if(benchmarkEnabled||Theme.matched)Theme.scheme='light';if(Theme.matched)Theme.animatedBackground=false
        if(production){let p=backend.settings;Theme.fancy=p.renderingMode!=='performance';Theme.style=p.style||'clear';Theme.scheme=p.scheme||'light';Theme.glassLevel=p.glassLevel===undefined?0:p.glassLevel;Theme.refractionLevel=p.distortion===undefined?.25:p.distortion;Theme.textScale=p.textSize||1;Theme.wallpaperIndex=p.wallpaperIndex===undefined?1:p.wallpaperIndex;Theme.reducedMotion=!!p.reducedMotion;Theme.animatedBackground=p.animatedBackground!==false;Theme.highContrast=!!p.highContrast}
        preferencesReady=true
        if(production&&backend.renderingChoicePending)Qt.callLater(settings.open)
    }
    Timer{id:preferenceSave;interval:250;onTriggered:if(app.production&&app.preferencesReady)backend.saveSettings(app.preferences())}
    Connections {target:Theme
        function onFancyChanged(){preferenceSave.restart()} function onStyleChanged(){preferenceSave.restart()} function onSchemeChanged(){preferenceSave.restart()}
        function onGlassLevelChanged(){preferenceSave.restart()} function onRefractionLevelChanged(){preferenceSave.restart()} function onTextScaleChanged(){preferenceSave.restart()}
        function onWallpaperIndexChanged(){preferenceSave.restart()} function onReducedMotionChanged(){preferenceSave.restart()} function onAnimatedBackgroundChanged(){preferenceSave.restart()} function onHighContrastChanged(){preferenceSave.restart()}
    }
    Connections {target:app.production?backend:null
        function onChanged(){app.fixtureRevision++;app.busy=backend.busy;Qt.callLater(app.showNotice)}
        function onError(message){app.errorText=message;errorSheet.open()}
        function onDetailReady(token,info){if(details.visible&&token===app.detailToken){app.sectionInfo=info;detailsText.text=info.body}}
        function onQuitRequested(){app.close()}
    }

    Binding {target:Theme;property:'active';value:app.renderActive}
    Binding {target:Theme;property:'backdrop';value:backdrop}
    font.family:'Segoe UI Variable';font.pixelSize:14*Theme.textScale
    palette.text:Theme.text;palette.windowText:Theme.text;palette.buttonText:Theme.text;palette.highlight:Theme.blue;palette.base:Theme.elevated;palette.button:Theme.surface;palette.window:Theme.bg
    function showNotice(){if(!production)return;if(backend.notice.text){if(!noticeSheet.opened)noticeSheet.open()}else noticeSheet.close()}
    function searchFocus(){search.forceActiveFocus()}
    function controlPosition(item){
        // Reading ancestor geometry keeps the binding current through layout and tab motion.
        let geometry=0
        for(let p=item;p;p=p.parent)geometry+=p.x+p.y+p.width+p.height+(p.glassMotion||0)
        return item.mapToItem(floatingControls,0,0)
    }
    function notify(message){toastText=message;toastTimer.restart()}
    function flushEdits(){return (!notes.visible||notes.beforeClose())&&(!production||backend.saveSettings(preferences()))}
    function changeAccount(){if(flushEdits()){notes.close();focusOpen=false;backend.openSetup()}}
    function syncNow(){if(flushEdits()){notes.close();backend.syncNow()}}
    function preferences(){return {renderingMode:Theme.fancy?'fancy':'performance',style:Theme.style,scheme:Theme.scheme,glassLevel:Theme.glassLevel,distortion:Theme.refractionLevel,textSize:Theme.textScale,wallpaperIndex:Theme.wallpaperIndex,reducedMotion:Theme.reducedMotion,animatedBackground:Theme.animatedBackground,highContrast:Theme.highContrast}}
    function showTask(id,title,note){
        taskInfo=production?backend.taskDetail(id):({})
        if(production&&Object.keys(taskInfo).length===0){errorText='This assignment is no longer available for editing. Sync again or open its lesson in Smartschool.';errorSheet.open();return}
        notes.taskId=id;notes.taskTitle=title;noteText.text=note;notes.open()
    }
    function openSection(item){sectionInfo=item;detailToken=item.id;details.title=item.title;detailsText.text=item.body;details.open();if(item.kind==='notes'){detailsText.text='Loading note…';backend.openNote(item.id.slice(6))}else if(item.kind==='absences')backend.markRead(item.id)}
    function pickSection(i){focusOpen=false;if(i===5&&section===5)sectionPages.requestTop();section=i}
    onSectionChanged:{let start=contentShift.running?tabShift.x:section>previousSection?14:-14;contentShift.stop();contentShift.from=start;contentShift.start();previousSection=section}
    onFocusOpenChanged:{
        if(focusOpen){savedBounds=Qt.rect(x,y,width,height);wasMaximized=visibility===Window.Maximized;showNormal();Qt.callLater(function(){if(app.focusOpen){app.width=420;app.height=560}});stopwatch.reset();stopwatch.toggle()}
        else if(savedBounds.width){width=savedBounds.width;height=savedBounds.height;x=savedBounds.x;y=savedBounds.y;focusOnTop=false;if(wasMaximized)showMaximized()}
    }
    onClosing:close=>{if(!flushEdits()){close.accepted=false;noteText.forceActiveFocus()}}
    Item {id:plannerScene;anchors.fill:parent
    Wallpaper {id:backdrop;objectName:'backdrop';anchors.fill:parent;animate:Theme.fancy&&Theme.animatedBackground&&!Theme.reducedMotion&&!app.focusOpen&&app.active&&!app.busy}
    Item {
        id:windowBar;width:parent.width;height:32;visible:!app.focusOpen;z:5
        MouseArea {anchors.fill:parent;onPressed:app.startSystemMove();onDoubleClicked:app.visibility===Window.Maximized?app.showNormal():app.showMaximized()}
        Row {anchors.right:parent.right;anchors.rightMargin:14;anchors.verticalCenter:parent.verticalCenter;spacing:8
            Repeater {model:[{name:'Minimize',color:'#ffbd2e',symbol:'−'},{name:'Maximize',color:'#28c840',symbol:'+'},{name:'Close',color:'#ff5f57',symbol:'×'}]
                Button {id:windowControl;required property var modelData;required property int index;width:24;height:24;Accessible.name:modelData.name
                    background:Item { Rectangle { objectName:'windowDot'; anchors.centerIn:parent;width:13;height:13;radius:6.5;color:windowControl.modelData.color;border.width:windowControl.visualFocus?2:0;border.color:Theme.text } }
                    contentItem:Text {textFormat:Text.PlainText;text:parent.hovered?parent.modelData.symbol:'';color:'#242424';horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter}
                    onClicked:index===0?app.showMinimized():index===1?(app.visibility===Window.Maximized?app.showNormal():app.showMaximized()):app.close()
                }
            }
        }
    }
    ColumnLayout {
        id:content;visible:!app.focusOpen
        anchors.fill:parent;anchors.topMargin:24;anchors.leftMargin:20;anchors.rightMargin:20;spacing:6
        transform:Translate{id:tabShift}
        readonly property real glassMotion:tabShift.x
        Item {id:headerFrame;Layout.fillWidth:true;implicitHeight:app.headerCollapsed&&!app.searchOpen?0:75*Theme.textScale;clip:app.headerCollapsed;z:3
            opacity:app.headerCollapsed&&!app.searchOpen?0:1
            Behavior on opacity{enabled:!planner.entryPending&&!sectionPages.topResetPending;NumberAnimation{duration:Theme.motion?200:0}}
            Behavior on implicitHeight{enabled:!planner.entryPending&&!sectionPages.topResetPending;NumberAnimation{duration:Theme.motion?300:0;easing.type:Easing.OutCubic}}
            Item {anchors.fill:parent;anchors.leftMargin:0;anchors.rightMargin:0
                ColumnLayout {anchors.left:parent.left;anchors.right:headerSlot.left;anchors.rightMargin:16;anchors.verticalCenter:parent.verticalCenter;spacing:3
                    Label {textFormat:Text.PlainText;text:['Planner','Missed','Schedule','All Classes','Grades','LVS'][app.section];font.pixelSize:34*Theme.textScale;font.bold:true;color:Theme.text
                        MouseArea {anchors.fill:parent;onPressed:app.startSystemMove()} }
                    Label {id:syncStatus;objectName:'syncStatus';Layout.fillWidth:true;elide:Text.ElideRight;textFormat:Text.PlainText;text:app.production?backend.status:'Last synced · 24 Oct, 09:00 · Synthetic workspace';font.pixelSize:13*Theme.textScale;color:Theme.secondary
                        HoverHandler {id:statusHover}
                        GlassToolTip {requested:syncStatus.truncated&&statusHover.hovered;text:syncStatus.text}
                    }
                }
                Item {id:headerSlot;anchors.right:parent.right;anchors.verticalCenter:parent.verticalCenter;width:headerActions.implicitWidth;height:38
                Row {id:headerActions;parent:floatingControls;spacing:8
                readonly property point origin:app.controlPosition(headerSlot)
                x:origin.x;y:origin.y;opacity:headerFrame.opacity;visible:!app.focusOpen&&opacity>0
                Capsule {selectorMaterial:true;backdrop:topSource;glassTracking:headerActions.x+headerActions.y; width:38;text:'Search';symbol:'searchBtn';iconOnly:true;onClicked:{app.searchOpen=!app.searchOpen;if(app.searchOpen)search.forceActiveFocus();else app.searchText=''}}
                Capsule {selectorMaterial:true;backdrop:topSource;glassTracking:headerActions.x+headerActions.y; width:38;text:app.production?'Sync now':'Refresh synthetic data';symbol:'syncBtn';iconOnly:true;onClicked:{if(app.production){app.syncNow()}else{app.busy=true;refreshTimer.restart()}}
                    RotationAnimator on rotation {from:0;to:360;duration:900;loops:Animation.Infinite;running:app.busy&&app.renderActive&&app.active&&Theme.motion}}
                Capsule {selectorMaterial:true;backdrop:topSource;glassTracking:headerActions.x+headerActions.y; width:38;objectName:'settingsButton';text:'Settings';symbol:'settingsBtn';iconOnly:true;onClicked:settings.open()}
                }
                }
            }
        }
        Capsule {objectName:'warningsButton';visible:app.production&&backend.warnings!=='';Layout.alignment:Qt.AlignLeft;text:'Sync warnings';symbol:'warn';onClicked:warningsSheet.open()}
        TextField {id:search;objectName:'search';Layout.fillWidth:true;visible:app.searchOpen;implicitHeight:44;text:app.searchText;onTextChanged:app.searchText=text
            placeholderText:['Search tasks…','Search missed tasks…','Search schedule…','Search all classes…','Search grades…','Search LVS…'][app.section];Accessible.name:'Search current tab';color:Theme.text;placeholderTextColor:Theme.secondary;leftPadding:18;selectByMouse:true
            background:Surface{radius:22;border.color:search.activeFocus?Theme.blue:Theme.rim}
            Keys.onEscapePressed:{app.searchOpen=false;app.searchText=''}
        }
        Item {objectName:'pageViewport';clip:true;Layout.fillWidth:true;Layout.fillHeight:true
        PlannerView {id:planner;app:app;anchors.fill:parent;visible:app.section<2
            onFocusTask:(id,title,done)=>{focusView.taskId=id;focusView.taskTitle=title;focusView.completed=done;app.focusOpen=true}
            onEditNote:(id,title,note)=>app.showTask(id,title,note)
        }
        SectionsView {id:sectionPages;app:app;anchors.fill:parent;anchors.leftMargin:-16;anchors.rightMargin:-16;visible:app.section>=2;onDetail:(title,body)=>{details.title=title;detailsText.text=body;details.open()}}
        }
    }
    NumberAnimation {id:contentShift;target:tabShift;property:'x';to:0;duration:Theme.motion?280:0;easing.type:Easing.OutCubic}
    }
    // One bounded capture for the floating controls; those controls live outside its source.
    ShaderEffectSource {id:topSource;objectName:'topControlSource';visible:false
        width:app.width;height:Math.min(app.height,(app.headerCollapsed?112:220)*Theme.textScale+(planner.typeMenuVisible||sectionPages.courseMenuVisible?240:0))
        sourceItem:app.renderActive&&!app.focusOpen&&!Theme.highContrast?plannerScene:null
        sourceRect:Qt.rect(0,0,width,height);textureSize:Qt.size(Math.ceil(width*(Theme.fancy?1:.65)),Math.ceil(height*(Theme.fancy?1:.65)))
        hideSource:false;live:app.renderActive&&!app.focusOpen;mipmap:true;smooth:true
    }
    Item {id:floatingControls;anchors.fill:parent;visible:!app.focusOpen;z:4}
    ShaderEffectSource {
        id:dockSource;objectName:'dockSource';visible:false
        x:navigation.x-72;y:navigation.y-72;width:navigation.width+144;height:navigation.height+144
        sourceItem:app.renderActive&&!app.focusOpen&&!Theme.highContrast?plannerScene:null
        sourceRect:Qt.rect(x,y,width,height);textureSize:Qt.size(Math.ceil(width*(Theme.fancy?1:.65)),Math.ceil(height*(Theme.fancy?1:.65)))
        hideSource:false;live:app.renderActive&&!app.focusOpen;mipmap:true;smooth:true
    }
    LensBar {id:navigation;objectName:'navigation';visible:!app.focusOpen
        anchors.bottom:parent.bottom;anchors.bottomMargin:10;anchors.horizontalCenter:parent.horizontalCenter;width:Math.min(parent.width-32,560*Theme.textScale);height:74*Theme.textScale
        backdrop:dockSource;labels:['To-Do','Missed','Schedule','All Classes','Grades','LVS'];symbols:['todo','missed','schedule','all','grades','lvs'];missedCount:tasks.missedCount;unreadCount:app.production?backend.unreadCount:0;current:app.section;onPicked:i=>app.pickSection(i)
    }
    FocusView {id:focusView;app:app;backdrop:backdrop;anchors.fill:parent;visible:app.focusOpen;onLeave:app.focusOpen=false}
    SettingsPanel {id:settings;objectName:'settingsPanel';app:app;backdrop:backdrop}
    Sheet {
        id:notes;objectName:'noteDialog';property string taskId:'';property string taskTitle:''
        title:'Task details';implicitHeight:600
        beforeClose:function(){if(noteText.length>5000){noteError.text='Your note is too long. Shorten it to keep your changes.';return false}return tasks.change(taskId,'note',noteText.text)}
        onOpened:noteText.forceActiveFocus()
        Label {textFormat:Text.PlainText;text:notes.taskTitle;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text;font.pixelSize:20*Theme.textScale;}
        Label {textFormat:Text.PlainText;text:'INSTRUCTIONS';color:Theme.secondary;font.bold:true;font.pixelSize:13}
        Label {textFormat:Text.PlainText;text:app.production?(app.taskInfo.body||'No additional instructions.'):'Synthetic study material. Review the topic, record your working and bring one question to class.';Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text}
        Label {textFormat:Text.PlainText;visible:app.production;text:app.taskInfo.metadata||'';Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.secondary}
        Label {textFormat:Text.PlainText;visible:app.production&&!!app.taskInfo.status;text:app.taskInfo.status||'';Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.orange}
        Repeater {model:app.production?(app.taskInfo.links||[]):[];Capsule {required property var modelData;text:modelData.name||modelData.url||'Attachment';Layout.fillWidth:true;enabled:!!modelData.url;onClicked:backend.openExternal(modelData.url)}}
        Label {textFormat:Text.PlainText;text:'YOUR NOTE';color:Theme.secondary;font.bold:true;font.pixelSize:13}
        TextArea {id:noteText;objectName:'noteText';Layout.fillWidth:true;Layout.preferredHeight:150;wrapMode:TextEdit.Wrap;selectByMouse:true;Accessible.name:'Task note';placeholderText:'Add a note…';color:Theme.text
            background:Rectangle{radius:18;color:Theme.fill;border.color:noteText.activeFocus?Theme.blue:'transparent'} }
        Label {textFormat:Text.PlainText;id:noteError;Layout.fillWidth:true;wrapMode:Text.Wrap;text:noteText.length+' / 5,000'+(app.production?' · saved on this computer':' · memory only');color:noteText.length>5000?Theme.red:Theme.secondary}
        Capsule {text:'Save note';primary:true;Layout.fillWidth:true;onClicked:notes.dismiss()}
    }
    Sheet {id:details;implicitHeight:500
        Capsule {visible:app.production&&app.detailToken.startsWith('notes:');text:'Reload note';onClicked:{detailsText.text='Loading note…';backend.openNote(app.detailToken.slice(6))}}
        Capsule {visible:app.production&&backend.school!=='';text:'Open Smartschool';onClicked:backend.openExternal('https://'+backend.school.replace(/^https?:\/\//,''))}
        Repeater {model:app.production?(app.sectionInfo.links||[]):[];Capsule {required property var modelData;Layout.fillWidth:true;text:modelData.name||'Open link';enabled:!!modelData.url;onClicked:backend.openExternal(modelData.url)}}
        Repeater {model:app.production?(app.sectionInfo.assignments||[]):[];Capsule {required property var modelData;text:modelData.title;Layout.fillWidth:true;onClicked:{let task=tasks.taskNote(modelData.id);details.close();app.showTask(modelData.id,modelData.title,task)}}}
        Label {textFormat:Text.PlainText;id:detailsText;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text;font.pixelSize:16*Theme.textScale}
    }
    Surface {anchors.horizontalCenter:parent.horizontalCenter;anchors.bottom:parent.bottom;anchors.bottomMargin:110*Theme.textScale;width:toastRow.implicitWidth+24;height:52;radius:26;visible:opacity>0;opacity:app.toastText!==''?1:0;strong:true;z:3
        Behavior on opacity{NumberAnimation{duration:Theme.motion?200:0}}
        transform:Translate{y:app.toastText!==''?0:12;Behavior on y{NumberAnimation{duration:Theme.motion?260:0;easing.type:Easing.OutCubic}}}
        RowLayout {id:toastRow;anchors.centerIn:parent
            Label {textFormat:Text.PlainText;text:app.toastText;color:Theme.text}
            Capsule {text:'Undo';quiet:true;onClicked:{tasks.undo();app.toastText=''}}
        }
    }
    Timer{id:toastTimer;interval:3500;onTriggered:app.toastText=''}
    Timer{id:refreshTimer;interval:1100;onTriggered:{app.busy=false;app.notify('Synthetic workspace refreshed')}}
    ShaderEffectSource {id:syncSource;visible:false;width:app.width;height:app.height;sourceItem:app.busy&&app.renderActive?plannerScene:null
        sourceRect:Qt.rect(0,0,width,height);textureSize:Qt.size(Math.ceil(width*.65),Math.ceil(height*.65));live:false;mipmap:true;smooth:true
        Connections {target:Theme
            function onDarkChanged(){if(app.busy)Qt.callLater(syncSource.scheduleUpdate)}
            function onStyleChanged(){if(app.busy)Qt.callLater(syncSource.scheduleUpdate)}
        }
    }
    onBusyChanged:if(busy)Qt.callLater(syncSource.scheduleUpdate)
    SyncProgress {app:app;backdrop:syncSource;action:app.production?backend.busyAction:'sync'}
    Sheet {id:noticeSheet;objectName:'noticeSheet';title:!app.production?'':backend.notice.kind==='release'?"What's new":backend.notice.kind==='update'?'Update available':'Update status'
        beforeClose:function(){if(app.production)backend.dismissNotice();return true}
        Label {objectName:'releaseNotesText';textFormat:Text.MarkdownText;text:app.production?(backend.notice.text||''):'';Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text;font.pixelSize:14*Theme.textScale;onLinkActivated:link=>backend.openExternal(link)}
        Capsule {text:'Install update';visible:app.production&&backend.notice.kind==='update';enabled:!app.busy;onClicked:if(app.flushEdits())backend.installUpdate()}
        Capsule {text:'Dismiss';onClicked:noticeSheet.dismiss()}
    }
    Sheet {id:warningsSheet;objectName:'warningsSheet';title:'Sync warnings'
        Label {textFormat:Text.PlainText;text:app.production?backend.warnings:'';Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text}
        Capsule {text:'Dismiss';onClicked:warningsSheet.close()}
    }
    Sheet {id:errorSheet;objectName:'errorSheet';title:'Could not complete the action';Label {textFormat:Text.PlainText;text:app.errorText;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text} Capsule {text:'Retry sync';enabled:!app.busy;onClicked:{errorSheet.close();app.syncNow()}} Capsule {text:'Change login details';onClicked:app.changeAccount()}}
    Shortcut{sequence:'Ctrl+F';enabled:!app.focusOpen&&!app.busy&&!notes.visible&&!settings.visible&&!details.visible&&!errorSheet.visible&&!noticeSheet.visible&&!warningsSheet.visible;onActivated:{app.searchOpen=true;search.forceActiveFocus()}}
    Shortcut{sequence:'Escape';enabled:app.focusOpen&&!app.busy&&!notes.visible&&!settings.visible&&!details.visible&&!errorSheet.visible&&!noticeSheet.visible&&!warningsSheet.visible;onActivated:app.focusOpen=false}
    Repeater{model:[Qt.TopEdge,Qt.BottomEdge,Qt.LeftEdge,Qt.RightEdge,Qt.TopEdge|Qt.LeftEdge,Qt.TopEdge|Qt.RightEdge,Qt.BottomEdge|Qt.LeftEdge,Qt.BottomEdge|Qt.RightEdge]
        MouseArea{required property int modelData;visible:app.visibility!==Window.Maximized;z:20
            width:(modelData&Qt.LeftEdge)||(modelData&Qt.RightEdge)?6:app.width-12
            height:(modelData&Qt.TopEdge)||(modelData&Qt.BottomEdge)?6:app.height-12
            x:modelData&Qt.RightEdge?app.width-width:modelData&Qt.LeftEdge?0:6
            y:modelData&Qt.BottomEdge?app.height-height:modelData&Qt.TopEdge?0:6
            cursorShape:width>6?Qt.SizeVerCursor:height>6?Qt.SizeHorCursor:Qt.SizeFDiagCursor
            onPressed:app.startSystemResize(modelData)
        }
    }
    // Benchmark hooks are dormant in ordinary use; animations still run entirely in Qt/QML.
    FrameAnimation { running: benchmarkEnabled && app.renderActive && (app.phase === "scroll" || app.phase === "transition")
        onTriggered: app.frameSamples.push(frameTime * 1000) }
    NumberAnimation on scrollProgress { id: scrollAnimation; running: false; from: 0; to: 1; duration: 4000 }
    onScrollProgressChanged: planner.benchmarkScroll(scrollProgress)
    Timer { id: transitionTimer; interval: 180; repeat: true
        onTriggered: { app.section = (++app.transitionStep) % 6; if (app.transitionStep >= 20) { stop(); app.section = 0 } } }
    function bench(action) {
        if (action === "scroll") { phase = "scroll"; frameSamples = []; scrollAnimation.start() }
        if (action === "transition") { phase = "transition"; frameSamples = []; transitionStep = 0; transitionTimer.start() }
        if (action === "idle") { phase = "idle" }
        if (action === "search") { planner.benchmarkSearch("quadratic") }
        if (action === "clearSearch") { planner.benchmarkSearch("") }
        if (action === "settings") settings.open()
        if (action === "closeSettings") settings.close()
        if (action === "focus") { focusOpen = true }
    }
}
