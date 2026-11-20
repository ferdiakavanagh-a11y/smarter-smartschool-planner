import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtQuick.Dialogs
ApplicationWindow {
    id:app
    readonly property bool production:typeof backend!=='undefined'
    property bool preferencesReady:false
    property var taskInfo:({})
    property var sectionInfo:({})
    property string detailToken:''
    property string errorText:''
    width:1100;height:800;minimumWidth:focusPresented?360:760;minimumHeight:focusPresented?420:600
    visible:false;title:I18n.t(production?'Smartschool Planner':'Smartschool Planner · demo');color:Theme.bg
    flags:Qt.Window | Qt.FramelessWindowHint | (focusPresented&&focusOnTop?Qt.WindowStaysOnTopHint:0)
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
    readonly property var navigationSections:[0,3,4,5,6]
    property bool focusOpen:false
    property bool focusPresented:false
    property real plannerReveal:focusPresented?0:1
    Behavior on plannerReveal {enabled:!app.focusPresented;NumberAnimation {duration:Theme.motion?140:0;easing.type:Easing.OutCubic}}
    property real focusReveal:focusOpen?1:0
    Behavior on focusReveal {NumberAnimation {duration:!app.renderActive?0:Theme.reducedMotion?100:app.focusOpen?220:140;easing.type:Easing.OutCubic}}
    onFocusRevealChanged:if(focusReveal===0&&!focusOpen)restoreFocusBounds()
    property bool focusOnTop:false
    property bool searchOpen:false
    property string searchText:''
    property bool headerCollapsed:false
    property bool sceneReady:false
    property bool busy:false
    property string toastText:''
    property bool toastUndo:true
    property var activeToolTip:null
    property rect savedBounds
    property bool wasMaximized:false
    readonly property bool renderActive:visible&&visibility!==Window.Minimized
    readonly property bool motion:Theme.motion
    property string phase:'idle'
    property var frameSamples:[]
    property real scrollProgress:0
    property int transitionStep:0
    QtObject {id:themeProxy;property bool fancy:Theme.fancy;property bool reducedMotion:Theme.reducedMotion;property real textScale:Theme.textScale
        onFancyChanged:Theme.fancy=fancy;onReducedMotionChanged:Theme.reducedMotion=reducedMotion;onTextScaleChanged:Theme.textScale=textScale}
    Component.onCompleted:{Theme.fancy=initialFancy;Theme.matched=typeof initialMatched!=='undefined'&&initialMatched;if(benchmarkEnabled||Theme.matched)Theme.scheme='light';if(Theme.matched)Theme.animatedBackground=false
        if(production){let p=backend.settings;Theme.fancy=p.renderingMode!=='performance';Theme.style=p.style||'clear';Theme.scheme=p.scheme||'light';Theme.glassLevel=p.glassLevel===undefined?0:p.glassLevel;Theme.refractionLevel=p.distortion===undefined?.25:p.distortion;Theme.textScale=p.textSize||1;Theme.wallpaperIndex=p.wallpaperIndex===undefined?1:p.wallpaperIndex;Theme.reducedMotion=!!p.reducedMotion;Theme.animatedBackground=p.animatedBackground!==false;Theme.highContrast=!!p.highContrast;I18n.language=p.language||'en'}
        preferencesReady=true
        if(production&&backend.renderingChoicePending)Qt.callLater(settings.open)
    }
    Timer{id:preferenceSave;interval:250;onTriggered:if(app.production&&app.preferencesReady)backend.saveSettings(app.preferences())}
    Connections {target:I18n;function onLanguageChanged(){preferenceSave.restart()}}
    Connections {target:Theme
        function onFancyChanged(){preferenceSave.restart()} function onStyleChanged(){preferenceSave.restart()} function onSchemeChanged(){preferenceSave.restart()}
        function onGlassLevelChanged(){preferenceSave.restart()} function onRefractionLevelChanged(){preferenceSave.restart()} function onTextScaleChanged(){preferenceSave.restart()}
        function onWallpaperIndexChanged(){preferenceSave.restart()} function onReducedMotionChanged(){preferenceSave.restart()} function onAnimatedBackgroundChanged(){preferenceSave.restart()} function onHighContrastChanged(){preferenceSave.restart()}
    }
    Connections {target:app.production?backend:null
        function onChanged(){app.busy=backend.busy;Qt.callLater(app.showNotice)}
        function onGroupsChanged(section){if(section<0&&app.detailToken.startsWith('notes:')){details.close();app.detailToken='';app.sectionInfo=({});detailsText.text=''}if(section<0||app.section===section)app.fixtureRevision++;if(section<0&&notes.visible&&notes.taskId)app.taskInfo=backend.taskDetail(notes.taskId)}
        function onError(message){app.errorText=message;errorSheet.open()}
        function onDetailReady(token,info){if(details.visible&&token===app.detailToken){app.sectionInfo=info;detailsText.text=info.body}}
        function onQuitRequested(){app.close()}
    }

    Binding {target:Theme;property:'active';value:app.renderActive}
    Binding {target:Theme;property:'backdrop';value:backdrop}
    font.family:Theme.fancy?'Segoe UI Variable':'Segoe UI';font.pixelSize:14*Theme.textScale
    palette.text:Theme.text;palette.windowText:Theme.text;palette.buttonText:Theme.text;palette.highlight:Theme.blue;palette.base:Theme.elevated;palette.button:Theme.surface;palette.window:Theme.bg
    function showNotice(){if(!production)return;if(backend.notice.text){if(!noticeSheet.opened)noticeSheet.open()}else noticeSheet.close()}
    function searchFocus(){if(section===6)messagesPage.focusSearch();else search.forceActiveFocus()}
    function toggleSearch(){if(section===6){messagesPage.focusSearch();return}searchOpen=!searchOpen;if(searchOpen)search.forceActiveFocus();else searchText=''}
    function requestAI(kind){
        if(!production)return
        if(!backend.features.aiAvailable){aiRequired.open();return}
        if(kind==='reply')backend.features.draftReply()
        else if(kind==='week')backend.features.summariseWeek()
    }
    function controlPosition(item){
        // Reading ancestor geometry keeps the binding current through layout and tab motion.
        let geometry=0
        for(let p=item;p;p=p.parent)geometry+=p.x+p.y+p.width+p.height+(p.glassMotion||0)
        return item.mapToItem(floatingControls,0,0)
    }
    function notify(message,undo=true){toastText=message;toastUndo=undo;toastTimer.restart()}
    function flushEdits(){return (!notes.visible||notes.beforeClose())&&messagesPage.flushDraft()&&(!production||backend.saveSettings(preferences()))}
    function changeAccount(){if(flushEdits()){notes.close();focusOpen=false;backend.openSetup()}}
    function syncNow(){if(flushEdits()){notes.close();backend.syncNow()}}
    function preferences(){return {language:I18n.language,renderingMode:Theme.fancy?'fancy':'performance',style:Theme.style,scheme:Theme.scheme,glassLevel:Theme.glassLevel,distortion:Theme.refractionLevel,textSize:Theme.textScale,wallpaperIndex:Theme.wallpaperIndex,reducedMotion:Theme.reducedMotion,animatedBackground:Theme.animatedBackground,highContrast:Theme.highContrast}}
    function showTask(id,title,note){
        taskInfo=production?backend.taskDetail(id):({})
        if(production&&Object.keys(taskInfo).length===0){errorText='This assignment is no longer available for editing. Sync again or open its lesson in Smartschool.';errorSheet.open();return}
        notes.taskId=id;notes.taskTitle=title;noteText.text=note;notes.open()
    }
    function openSection(item){sectionInfo=item;detailToken=item.id;details.title=details.lessonDetails?item.lessonTitle:item.title;detailsText.text=details.lessonDetails?item.lessonContent:item.body;details.open();if(item.kind==='notes'){let cached=backend.noteDetails[item.id];if(cached){backend.markRead(item.id);sectionInfo=cached;detailsText.text=cached.body}else{detailsText.text=I18n.t('Loading note…');backend.openNote(item.id.slice(6))}}else if(item.kind==='absences')backend.markRead(item.id)}
    function pickSection(i){focusOpen=false;if(i===5&&section===5)sectionPages.requestTop();section=i}
    onSectionChanged:if(section===3||section>=6){headerCollapsed=false;searchOpen=false;settleHeader()}
    // Snap interrupted scroll motion before measuring a newly entered page.
    function settleHeader(){headerMotion.complete();headerFrame.Layout.preferredHeight=Qt.binding(function(){return app.headerCollapsed&&!app.searchOpen?0:headerFrame.implicitHeight});content.ensurePolished()}
    function restoreFocusBounds(){
        if(focusOpen||!focusPresented)return
        width=savedBounds.width;height=savedBounds.height;x=savedBounds.x;y=savedBounds.y
        focusOnTop=false;focusPresented=false
        if(wasMaximized)showMaximized()
    }
    onFocusOpenChanged:{
        if(focusOpen&&!focusPresented){
            savedBounds=Qt.rect(x,y,width,height);wasMaximized=visibility===Window.Maximized
            focusPresented=true;showNormal();width=420;height=560
            stopwatch.reset();stopwatch.toggle()
        }else if(!focusOpen&&focusReveal===0)restoreFocusBounds()
    }
    onClosing:close=>{if(!flushEdits()){close.accepted=false;if(notes.visible)noteText.forceActiveFocus();else messagesPage.focusDraft()}}
    Item {id:plannerScene;anchors.fill:parent
    Wallpaper {id:backdrop;objectName:'backdrop';anchors.fill:parent;animate:Theme.fancy&&Theme.animatedBackground&&!Theme.reducedMotion&&!app.focusPresented&&app.active&&!app.busy}
    Item {
        id:windowBar;width:parent.width;height:Theme.fancy?32:56*Theme.textScale;visible:!app.focusPresented;opacity:app.plannerReveal;z:5
        MouseArea {anchors.fill:parent;enabled:Theme.fancy;onPressed:app.startSystemMove();onDoubleClicked:app.visibility===Window.Maximized?app.showNormal():app.showMaximized()}
        Row {
            id:captionButtons
            anchors.right:parent.right;anchors.rightMargin:Theme.fancy?14:4
            spacing:Theme.fancy?8:0
            anchors.verticalCenter:parent.verticalCenter
            Repeater {
                model:['minimize','maximize','close']
                Button {
                    id:windowControl
                    required property string modelData
                    required property int index
                    readonly property bool restore:index===1 && app.visibility===Window.Maximized
                    objectName:'caption_'+modelData
                    text:index===0?I18n.p('Minimize','Minimaliseren'):index===2?I18n.p('Close','Sluiten'):restore?I18n.p('Restore window','Venster herstellen'):I18n.p('Maximize','Maximaliseren')
                    Accessible.name:text
                    width:Theme.fancy?24:globalBar.compact?36:46
                    height:Theme.fancy?24:Math.min(windowBar.height,44)
                    padding:0;hoverEnabled:true
                    background:Rectangle {
                        objectName:'windowDot'
                        anchors.centerIn:parent
                        width:Theme.fancy?13:parent.width-2;height:Theme.fancy?13:parent.height-4
                        radius:Theme.fancy?height/2:6
                        color:Theme.fancy?['#ffbd2e','#28c840','#ff5f57'][windowControl.index]
                            :windowControl.index===2&&(windowControl.hovered||windowControl.down)?(windowControl.down?'#A71926':'#C62837')
                            :windowControl.down?'#55FFFFFF':windowControl.hovered?'#36FFFFFF':'#12FFFFFF'
                        border.width:windowControl.visualFocus?2:0;border.color:Theme.fancy?Theme.text:'white'
                    }
                    contentItem:Item {
                        Text {
                            anchors.centerIn:parent
                            visible:Theme.fancy && windowControl.hovered
                            text:['−','+','×'][windowControl.index]
                            color:'#242424'
                        }
                        Icon {
                            anchors.centerIn:parent;width:24;height:width;visible:!Theme.fancy
                            name:windowControl.restore?'restoreWindow':windowControl.modelData
                            ink:'white'
                        }
                    }
                    GlassToolTip {requested:!Theme.fancy&&(windowControl.hovered||windowControl.visualFocus);text:windowControl.text}
                    onClicked:index===0?app.showMinimized():index===1?(app.visibility===Window.Maximized?app.showNormal():app.showMaximized()):app.close()
                }
            }
        }
    }
    component GlobalAction:Button {
        id:actionControl
        property string symbol:''
        property bool spinning:false
        implicitWidth:(globalBar.compact?32:42)*Math.min(Theme.textScale,1.15);implicitHeight:implicitWidth
        Layout.minimumWidth:implicitWidth;Layout.preferredWidth:implicitWidth;Layout.preferredHeight:implicitHeight
        padding:6;hoverEnabled:true;Accessible.name:text
        scale:down&&!Theme.reducedMotion?.97:1
        Behavior on scale {NumberAnimation {duration:Theme.motion?120:0;easing.type:Easing.OutCubic}}
        background:Rectangle {radius:height/2;color:parent.down?'#55ffffff':parent.hovered||parent.visualFocus?'#30ffffff':'transparent';border.width:parent.visualFocus?2:0;border.color:'white'}
        contentItem:Item {Icon {id:glyph;anchors.centerIn:parent;width:20*Theme.textScale;height:20*Theme.textScale;name:parent.parent.symbol;ink:'white'
            RotationAnimator on rotation {objectName:'actionSpin';from:0;to:360;duration:900;loops:Animation.Infinite;running:globalBar.visible&&glyph.parent.parent.spinning&&app.renderActive&&app.active&&Theme.motion;onStopped:glyph.rotation=0}}}
        GlassToolTip {requested:actionControl.hovered||actionControl.visualFocus;text:actionControl.text}
    }
    Rectangle {id:globalBar;objectName:'smartschoolGlobalBar';visible:!Theme.fancy&&!app.focusPresented;anchors.top:parent.top;width:parent.width;height:topHeight+(stackNavigation?navigationBar.implicitHeight:0);color:Theme.globalBar;z:4
        readonly property bool stackNavigation:app.width<730*Theme.textScale
        readonly property real topHeight:56*Theme.textScale
        readonly property bool compact:app.width<1000*Theme.textScale
        readonly property bool tight:app.width<850*Theme.textScale
        readonly property string accountLabel:app.production?(backend.accountName||I18n.p('Your account','Je account')):'Sam Example'
        readonly property var navigation:[{label:'Mijn taken',shortEn:'Tasks',shortNl:'Taken',section:0},{label:'Planner',section:3},{label:'Resultaten',shortEn:'Results',shortNl:'Cijfers',section:4},{label:'LVS',section:5},{label:'Berichten',shortEn:'Mail',shortNl:'Berichten',section:6}]
        MouseArea {anchors.fill:parent;onPressed:app.startSystemMove()}
        RowLayout {id:navigationBar;objectName:'smartschoolNavigation';Layout.minimumWidth:implicitWidth;Layout.preferredWidth:implicitWidth;Layout.preferredHeight:44*Theme.textScale;spacing:globalBar.compact?2:4
            Repeater {model:globalBar.navigation
                Button {id:navigationButton;required property var modelData;objectName:'smartschoolNavigate'+modelData.section;text:globalBar.tight&&modelData.shortEn?I18n.p(modelData.shortEn,modelData.shortNl):I18n.t(modelData.label);Accessible.name:I18n.t(modelData.label);Layout.minimumWidth:implicitWidth;implicitHeight:40*Theme.textScale;leftPadding:globalBar.compact?4:8;rightPadding:leftPadding;hoverEnabled:true
                    GlassToolTip {requested:navigationButton.hovered||navigationButton.visualFocus;text:I18n.t(navigationButton.modelData.label)}
                    contentItem:Text {text:parent.text;color:'white';font.pixelSize:(globalBar.compact?12:14)*Theme.textScale;font.weight:Font.Medium;verticalAlignment:Text.AlignVCenter}
                    background:Rectangle {color:parent.down?'#55ffffff':parent.hovered?'#20ffffff':app.section===parent.modelData.section?'#29702D22':'transparent';border.width:parent.visualFocus?2:0;border.color:'white'
                        Rectangle {anchors.bottom:parent.bottom;anchors.horizontalCenter:parent.horizontalCenter;width:parent.width-8;height:2;color:'white';visible:app.section===navigationButton.modelData.section}
                    }
                    onClicked:app.pickSection(modelData.section)
                }
            }
        }
        RowLayout {anchors.horizontalCenter:parent.horizontalCenter;anchors.top:parent.top;anchors.topMargin:globalBar.topHeight;visible:globalBar.stackNavigation
            LayoutItemProxy {target:navigationBar;visible:globalBar.stackNavigation}
        }
        RowLayout {anchors.top:parent.top;anchors.left:parent.left;anchors.right:parent.right;height:globalBar.topHeight;anchors.leftMargin:12;anchors.rightMargin:captionButtons.width+captionButtons.anchors.rightMargin+6;spacing:globalBar.compact?2:6
            Rectangle {objectName:'accountAvatar';Layout.minimumWidth:30;implicitWidth:30;implicitHeight:30;radius:15;color:'#F0D6CF';Accessible.name:globalBar.accountLabel
                Text {anchors.centerIn:parent;text:app.production?backend.accountInitial:'S';color:'#713326';font.bold:true;font.pixelSize:13*Theme.textScale}
            }
            Label {id:accountNameLabel;objectName:'accountNameLabel';Layout.minimumWidth:globalBar.compact?42:60;Layout.preferredWidth:implicitWidth;text:globalBar.accountLabel;textFormat:Text.PlainText;elide:Text.ElideRight;color:'white';font.pixelSize:(globalBar.compact?12:14)*Theme.textScale;font.weight:Font.Medium;Layout.maximumWidth:globalBar.tight?110*Theme.textScale:Math.min(240,app.width*.22)
                HoverHandler {id:accountNameHover}
                GlassToolTip {requested:accountNameLabel.truncated&&accountNameHover.hovered;text:accountNameLabel.text}
            }
            Item {Layout.fillWidth:true}
            LayoutItemProxy {target:navigationBar;visible:!globalBar.stackNavigation}
            GlobalAction {objectName:'globalSearch';text:I18n.t('Search');symbol:'searchBtn';onClicked:app.toggleSearch()}
            GlobalAction {objectName:'globalSettings';text:I18n.t('Settings');symbol:'settingsBtn';onClicked:settings.open()}
            GlobalAction {id:globalSync;objectName:'globalSync';text:I18n.t('Sync now');symbol:'syncBtn';spinning:app.busy;enabled:app.section!==6||messagesPage.canRefresh;onClicked:app.section===6?messagesPage.refreshMessages():app.production?app.syncNow():refreshTimer.restart()}
            GlobalAction {objectName:'globalReplacements';text:I18n.t('Teacher replacements');symbol:'teacherOff';onClicked:app.showReplacements()}
        }
    }
    ColumnLayout {
        // Keep the reading position while Focus temporarily resizes the window.
        id:content;opacity:app.plannerReveal;enabled:!app.focusPresented
        x:Theme.fancy?20:(app.width<1000?12:20)*Theme.textScale;y:Theme.fancy?24:globalBar.height+12*Theme.textScale;width:(app.focusPresented?app.savedBounds.width:app.width)-2*x;height:(app.focusPresented?app.savedBounds.height:app.height)-y-(Theme.fancy?0:12*Theme.textScale);spacing:Theme.fancy?6:4
        Item {id:headerFrame;visible:Theme.fancy||app.section<3;Layout.fillWidth:true;implicitHeight:(Theme.fancy?75:52)*Theme.textScale;Layout.preferredHeight:Theme.fancy&&app.headerCollapsed&&!app.searchOpen?0:implicitHeight;clip:app.headerCollapsed;z:3
            opacity:Theme.fancy&&app.headerCollapsed&&!app.searchOpen?0:1
            Behavior on opacity{enabled:!planner.entryPending&&!sectionPages.topResetPending;NumberAnimation{duration:Theme.motion?200:0}}
            Behavior on Layout.preferredHeight{enabled:Theme.motion&&(app.section<2?!planner.entryPending:!sectionPages.topResetPending);NumberAnimation{id:headerMotion;duration:220;easing.type:Easing.OutCubic}}
            Item {anchors.fill:parent;anchors.leftMargin:0;anchors.rightMargin:0
                ColumnLayout {anchors.left:parent.left;anchors.right:headerSlot.left;anchors.rightMargin:16;anchors.verticalCenter:parent.verticalCenter;spacing:3
                    Label {textFormat:Text.PlainText;text:I18n.t((Theme.fancy?['To-do','Overdue','Planner','Planner','Grades','LVS','Messages']:['Mijn taken','Gemist','Planner','Planner','Resultaten','LVS','Berichten'])[app.section]||'To-do');font.pixelSize:(Theme.fancy?34:21)*Theme.textScale;font.bold:Theme.fancy;color:Theme.text
                        MouseArea {anchors.fill:parent;onPressed:app.startSystemMove()} }
                    Label {id:syncStatus;visible:Theme.fancy;objectName:'syncStatus';Layout.fillWidth:true;elide:Text.ElideRight;textFormat:Text.PlainText;text:I18n.t(app.production?backend.status:'Last synced · 24 Oct, 09:00 · Synthetic workspace');font.pixelSize:13*Theme.textScale;color:Theme.secondary
                        HoverHandler {id:statusHover}
                        GlassToolTip {requested:syncStatus.truncated&&statusHover.hovered;text:syncStatus.text}
                    }
                }
                Item {id:headerSlot;anchors.right:parent.right;anchors.verticalCenter:parent.verticalCenter;width:headerActions.implicitWidth;height:38
                Row {id:headerActions;parent:floatingControls;spacing:8
                readonly property point origin:app.controlPosition(headerSlot)
                x:origin.x;y:origin.y;opacity:headerFrame.opacity;visible:Theme.fancy&&!app.focusPresented&&opacity>0
                Capsule {selectorMaterial:true;backdrop:topSource;glassTracking:headerActions.x+headerActions.y; width:38;text:I18n.t('Search');symbol:'searchBtn';iconOnly:true;visible:app.section<7;onClicked:app.toggleSearch()}
                Capsule {id:syncControl;objectName:'syncButton';selectorMaterial:true;backdrop:topSource;glassTracking:headerActions.x+headerActions.y; width:38;text:I18n.t(app.production?'Sync now':'Refresh synthetic data');symbol:'syncBtn';iconOnly:true;onClicked:{if(app.production){app.syncNow()}else{app.busy=true;refreshTimer.restart()}}
                    contentItem:Item {implicitWidth:20;implicitHeight:20
                        Icon {id:syncGlyph;objectName:'syncGlyph';anchors.centerIn:parent;width:20*Theme.textScale;height:20*Theme.textScale;name:'syncBtn';ink:syncControl.labelInk
                            RotationAnimator on rotation {objectName:'syncSpin';from:0;to:360;duration:900;loops:Animation.Infinite;running:syncControl.visible&&app.busy&&app.renderActive&&app.active&&Theme.motion;onStopped:syncGlyph.rotation=0}}
                    }}
                Capsule {selectorMaterial:true;backdrop:topSource;glassTracking:headerActions.x+headerActions.y; width:38;objectName:'settingsButton';text:I18n.t('Settings');symbol:'settingsBtn';iconOnly:true;onClicked:settings.open()}
                }
                }
            }
        }
        Capsule {objectName:'warningsButton';visible:app.production&&backend.warnings!=='';Layout.alignment:Qt.AlignLeft;text:I18n.t('Sync warnings');symbol:'warn';onClicked:warningsSheet.open()}
        TextField {id:search;objectName:'search';Layout.fillWidth:true;visible:app.searchOpen&&app.section<6;implicitHeight:44;text:app.searchText;onTextChanged:app.searchText=text
            placeholderText:I18n.t(['Search tasks…','Search missed tasks…','Search schedule…','Search all classes…','Search grades…','Search LVS…'][app.section]||'');Accessible.name:I18n.t('Search current tab');color:Theme.text;placeholderTextColor:Theme.secondary;leftPadding:18;selectByMouse:true
            background:Surface{radius:Theme.fancy?22:3;border.color:search.activeFocus?Theme.blue:Theme.rim}
            Keys.onEscapePressed:{app.searchOpen=false;app.searchText=''}
        }
        Item {objectName:'pageViewport';clip:app.section===3||!app.headerCollapsed||app.searchOpen;Layout.fillWidth:true;Layout.fillHeight:true
        PlannerView {id:planner;app:app;anchors.fill:parent;visible:app.section<2
            onFocusTask:(id,title,done)=>{focusView.taskId=id;focusView.taskTitle=title;focusView.completed=done;app.focusOpen=true}
            onEditNote:(id,title,note)=>app.showTask(id,title,note)
        }
        ColumnLayout {anchors.fill:parent;spacing:Theme.fancy?15:0;visible:app.section>=2&&app.section<6
            RowLayout {Layout.fillWidth:true;visible:Theme.fancy&&app.production&&app.section===3
                Capsule {objectName:'replacementButton';visible:app.section===3;text:I18n.t('Teacher replacements');symbol:'file';onClicked:app.showReplacements()}
                Item {Layout.fillWidth:true}
            }
            Item {Layout.fillWidth:true;Layout.fillHeight:true;clip:app.section===3
                TimetableView {app:app;anchors.fill:parent;visible:app.section===3&&!Theme.fancy}
                SectionsView {id:sectionPages;app:app;anchors.fill:parent;visible:Theme.fancy||app.section===2;anchors.leftMargin:Theme.fancy?-16:0;anchors.rightMargin:Theme.fancy?-16:app.section===4||app.section===5?parent.width*.55+8:0;onDetail:(title,body)=>{details.title=title;detailsText.text=body;details.open()}}
                ResultsLvsView {app:app;anchors.fill:parent;visible:!Theme.fancy&&(app.section===4||app.section===5)}
                Rectangle {id:sectionPreview;visible:false;anchors.top:parent.top;anchors.bottom:parent.bottom;anchors.right:parent.right;width:parent.width*.55;color:Theme.elevated;border.color:Theme.separator
                    readonly property var entry:sectionPages.previewItem
                    ScrollView {id:sectionPreviewScroll;anchors.fill:parent;anchors.margins:18;clip:true;contentWidth:availableWidth
                        ColumnLayout {width:sectionPreviewScroll.availableWidth;spacing:16
                            Label {text:I18n.t(app.section===4?'Result details':'Student follow-up');color:Theme.secondary;Layout.fillWidth:true;wrapMode:Text.Wrap;font.pixelSize:12*Theme.textScale}
                            Label {text:sectionPreview.entry.title||I18n.t('Select an item');textFormat:Text.PlainText;color:Theme.text;Layout.fillWidth:true;wrapMode:Text.Wrap;font.pixelSize:22*Theme.textScale;font.bold:true}
                            Rectangle {visible:app.section===4;Layout.alignment:Qt.AlignHCenter;implicitWidth:100*Theme.textScale;implicitHeight:100*Theme.textScale;radius:width/2;color:Theme.elevated;border.width:6;border.color:sectionPreview.entry.tone==='green'?Theme.green:sectionPreview.entry.tone==='orange'?Theme.orange:sectionPreview.entry.tone==='red'?Theme.red:Theme.blue
                                Label {anchors.fill:parent;anchors.margins:10;horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter;wrapMode:Text.Wrap;text:sectionPreview.entry.percentText||sectionPreview.entry.extra||sectionPreview.entry.title||'—';textFormat:Text.PlainText;color:Theme.text;font.pixelSize:19*Theme.textScale;font.bold:true}
                            }
                            Label {text:sectionPreview.entry.meta||'';textFormat:Text.PlainText;color:Theme.secondary;Layout.fillWidth:true;wrapMode:Text.Wrap}
                            Rectangle {Layout.fillWidth:true;height:1;color:Theme.separator}
                            TextArea {text:sectionPreview.entry.body||I18n.t('Choose an item from the list to see its saved details.');textFormat:TextEdit.PlainText;readOnly:true;selectByMouse:true;wrapMode:TextEdit.Wrap;color:Theme.text;Layout.fillWidth:true;background:Item {}}
                            Capsule {text:I18n.t('Open details');enabled:!!sectionPreview.entry.id;onClicked:app.openSection(sectionPreview.entry)}
                        }
                    }
                }
            }
        }
        MessagesView {id:messagesPage;app:app;anchors.fill:parent;visible:app.section===6}
        }
    }
    }
    // One bounded capture for the floating controls; those controls live outside its source.
    ShaderEffectSource {id:topSource;objectName:'topControlSource';visible:false
        width:app.width;height:Math.min(app.height,(app.headerCollapsed?112:220)*Theme.textScale+(planner.typeMenuVisible||sectionPages.courseMenuVisible?240:0))
        sourceItem:Theme.fancy&&app.renderActive&&!app.focusPresented&&!Theme.highContrast?plannerScene:null
        sourceRect:Qt.rect(0,0,width,height);textureSize:Qt.size(Math.ceil(width*(Theme.fancy?1:.65)),Math.ceil(height*(Theme.fancy?1:.65)))
        hideSource:false;live:app.renderActive&&!app.focusPresented;mipmap:true;smooth:true
    }
    Item {id:floatingControls;anchors.fill:parent;visible:!app.focusPresented;opacity:app.plannerReveal;z:4}
    ShaderEffectSource {
        id:dockSource;objectName:'dockSource';visible:false
        x:navigation.x-72;y:navigation.y-72;width:navigation.width+144;height:navigation.height+144
        sourceItem:Theme.fancy&&app.renderActive&&!app.focusPresented&&!Theme.highContrast?plannerScene:null
        sourceRect:Qt.rect(x,y,width,height);textureSize:Qt.size(Math.ceil(width*(Theme.fancy?1:.65)),Math.ceil(height*(Theme.fancy?1:.65)))
        hideSource:false;live:app.renderActive&&!app.focusPresented;mipmap:true;smooth:true
    }
    LensBar {id:navigation;objectName:'navigation';visible:Theme.fancy&&!app.focusPresented;opacity:app.plannerReveal
        x:Theme.fancy?(parent.width-width)/2:12;y:Theme.fancy?parent.height-height-10:32;width:Theme.fancy?Math.min(parent.width-32,540*Theme.textScale):Math.min(parent.width-24,720*Theme.textScale);height:(Theme.fancy?74:44)*Theme.textScale
        backdrop:dockSource;labels:(['To-do','Planner','Grades','LVS','Messages']).map(value=>I18n.t(value));symbols:['todo','schedule','grades','lvs','message'];unreadCount:app.production?backend.unreadCount:0;unreadIndex:3;current:Math.max(0,app.navigationSections.indexOf(app.section));onPicked:i=>app.pickSection(app.navigationSections[i])
    }
    FocusView {id:focusView;app:app;backdrop:backdrop;anchors.fill:parent;visible:app.focusPresented;opacity:app.focusReveal
        scale:Theme.reducedMotion?1:.97+.03*app.focusReveal
        transform:Translate {y:Theme.reducedMotion?0:10*(1-app.focusReveal)}
        onLeave:app.focusOpen=false}
    SettingsPanel {id:settings;objectName:'settingsPanel';app:app;backdrop:backdrop}
    function showOfflineFiles(){offlineFiles.open()}
    function showReports(){reports.open()}
    FilePreview {id:filePreview;service:app.production?backend.features:null}
    Connections {target:app.production?backend.features:null
        function onFilePreviewRequested(info){filePreview.present(info)}
        function onCloseFilePreview(){filePreview.clearAndClose()}
    }
    function showReplacements(){replacements.open()}
    function showTaskCollection(collection){taskCollection.collection=collection;taskCollection.open()}
    TaskCollectionSheet {id:taskCollection;objectName:'taskCollectionSheet';app:app}
    Sheet {id:replacements;objectName:'replacementSheet';title:I18n.t('Teacher replacements')
        property string viewingAccount:''
        onAboutToShow:viewingAccount=app.production?backend.features.accountKey:''
        width:Math.min(1100*Theme.textScale,app.width-24)
        implicitHeight:app.height*.86
        onClosed:if(app.production)backend.features.closeReplacement()
        Loader {objectName:'replacementLoader';Layout.fillWidth:true;Layout.preferredHeight:Math.max(160,replacements.scrollView.height-24)
            active:replacements.visible&&app.production
            source:active?'ReplacementViewer.qml':''
            onLoaded:item.start(backend.features)
        }
        Connections {target:app.production?backend.features:null
            function onChanged(){if(replacements.visible&&backend.features.accountKey!==replacements.viewingAccount)replacements.close()}
        }
    }
    Sheet {id:reports;objectName:'reportCards';title:I18n.t('Report cards')
        implicitHeight:Math.min(620*Theme.textScale,app.height*.8)
        ResourcesView {app:app;Layout.fillWidth:true;Layout.preferredHeight:Math.max(160,reports.scrollView.height-24)}
    }
    Sheet {id:offlineFiles;objectName:'offlineFiles';title:I18n.t('Offline files')
        implicitHeight:Math.min(560*Theme.textScale,app.height*.75)
        ResourcesView {app:app;offlineOnly:true;Layout.fillWidth:true;Layout.preferredHeight:Math.max(160,offlineFiles.scrollView.height-24)}
    }
    Sheet {id:aiRequired;objectName:'aiRequired';title:I18n.t('AI required')
        Label {textFormat:Text.PlainText;text:I18n.t('AI requires a Gemini API key. Add one in Settings → Change login details.');color:Theme.text;Layout.fillWidth:true;wrapMode:Text.Wrap}
    }
    FileDialog {id:saveFile;property string downloadKey:'';fileMode:FileDialog.SaveFile;title:I18n.t('Save downloaded file')
        onAccepted:backend.features.exportDownloaded(downloadKey,selectedFile)
    }
    Connections {target:app.production?backend.features:null
        function onSaveRequested(key,url){saveFile.downloadKey=key;saveFile.selectedFile=url;saveFile.open()}
    }
    Sheet {
        id:notes;objectName:'noteDialog';property string taskId:'';property string taskTitle:''
        title:Theme.fancy?I18n.t('Task details'):notes.taskTitle
        headingColor:Theme.fancy?Theme.elevated:Theme.lesson
        width:Theme.fancy?Math.min(820*Theme.textScale,parent.width-24):app.width>1150?Math.min(1180*Theme.textScale,app.width-470):parent.width-28
        x:!Theme.fancy&&app.width>1150?app.width-width-48:(parent.width-width)/2
        implicitHeight:parent.height*.9
        readonly property var taskDate:(app.taskInfo.facts||[]).find(f=>f.label==='Due')
        readonly property var contextDays:{let revision=app.fixtureRevision;return app.production?backend.groups(3,'','All subjects'):[]}
        readonly property var dayContext:contextDays.find(day=>day.items.some(lesson=>(lesson.assignments||[]).some(task=>task.id===notes.taskId)))||contextDays[0]||{heading:'Mijn planner',items:[]}
        beforeClose:function(){if(noteText.length>5000){noteError.text='Your note is too long. Shorten it to keep your changes.';return false}return tasks.change(taskId,'note',noteText.text)}
        footer:Component {Rectangle {implicitHeight:44*Theme.textScale;color:Theme.fill;border.color:Theme.separator
            RowLayout {anchors.fill:parent;anchors.leftMargin:14;anchors.rightMargin:14
                Label {Layout.fillWidth:true;text:(app.taskInfo.facts||[]).filter(f=>f.label==='Posted').map(f=>I18n.p('Published','Gepubliceerd')+' '+f.value).join('');color:Theme.secondary;font.pixelSize:10*Theme.textScale;elide:Text.ElideRight}
                Capsule {visible:Theme.fancy;text:I18n.t('Bewaren en sluiten');primary:true;onClicked:notes.dismiss()}
            }
        }}
        RowLayout {Layout.fillWidth:true;spacing:18;Layout.alignment:Qt.AlignTop
            Rectangle {visible:false;Layout.preferredWidth:notes.width*.26;Layout.preferredHeight:Math.max(450,notes.scrollView.height-24);Layout.alignment:Qt.AlignTop;color:Theme.elevated;border.color:Theme.separator;radius:4
                ColumnLayout {anchors.fill:parent;anchors.margins:12;spacing:8
                    Label {text:I18n.t('Mijn planner');color:Theme.secondary;font.pixelSize:20*Theme.textScale}
                    Label {text:I18n.t(notes.dayContext.heading||'');color:Theme.text;font.pixelSize:12*Theme.textScale;Layout.fillWidth:true;wrapMode:Text.Wrap;Layout.bottomMargin:12}
                    Repeater {model:notes.dayContext.items
                        Rectangle {required property var modelData;Layout.fillWidth:true;implicitHeight:Math.max(66,contextText.implicitHeight+16);radius:3;color:Theme.lesson
                            ColumnLayout {id:contextText;anchors.fill:parent;anchors.margins:8;spacing:3
                                Label {text:parent.parent.modelData.meta.split(' · ')[0];color:Theme.secondary;font.pixelSize:10*Theme.textScale}
                                Label {text:parent.parent.modelData.title;textFormat:Text.PlainText;color:Theme.text;font.bold:true;font.pixelSize:12*Theme.textScale;Layout.fillWidth:true;wrapMode:Text.Wrap}
                                Label {text:parent.parent.modelData.extra||'';textFormat:Text.PlainText;color:Theme.text;font.pixelSize:11*Theme.textScale;Layout.fillWidth:true;wrapMode:Text.Wrap;maximumLineCount:2;elide:Text.ElideRight}
                                TapHandler {onTapped:app.openSection(parent.parent.modelData)}
                            }
                        }
                    }
                    Item {Layout.fillHeight:true}
                }
            }
            ColumnLayout {Layout.fillWidth:true;Layout.alignment:Qt.AlignTop;spacing:12
                Rectangle {visible:!Theme.fancy;Layout.fillWidth:true;implicitHeight:28*Theme.textScale;color:Theme.dark?'#19383E':'#E7F8FC'
                    Label {anchors.left:parent.left;anchors.leftMargin:12;anchors.verticalCenter:parent.verticalCenter;anchors.right:parent.right;anchors.rightMargin:12;elide:Text.ElideRight;text:'⚑  '+I18n.p('My task','Eigen to-do')+' · '+notes.taskTitle;color:Theme.text;font.pixelSize:12*Theme.textScale}
                }
                RowLayout {Layout.fillWidth:true;spacing:16;Layout.alignment:Qt.AlignTop
                    ColumnLayout {Layout.fillWidth:true;Layout.alignment:Qt.AlignTop;spacing:10
                        ColumnLayout {visible:!Theme.fancy&&app.production&&!(app.taskInfo.sections||[]).some(section=>!!section.body.trim());Layout.fillWidth:true;Layout.topMargin:36;Layout.bottomMargin:36;spacing:10
                            Icon {name:'todo';ink:Theme.teal;Layout.alignment:Qt.AlignHCenter;Layout.preferredWidth:48;Layout.preferredHeight:48}
                            Label {text:I18n.t('Er is geen inhoud bij deze opdracht.');color:Theme.secondary;Layout.fillWidth:true;horizontalAlignment:Text.AlignHCenter;wrapMode:Text.Wrap;font.pixelSize:12*Theme.textScale}
                        }
                        Label {visible:Theme.fancy;text:notes.taskTitle;textFormat:Text.PlainText;color:Theme.text;Layout.fillWidth:true;wrapMode:Text.Wrap;font.pixelSize:22*Theme.textScale;font.bold:true}
                        Repeater {model:app.production?(app.taskInfo.sections||[]):[{title:I18n.t('Instructions'),body:'Synthetic study material.'}]
                            DetailCard {required property var modelData;objectName:'instructionCard';title:modelData.title;Layout.fillWidth:true
                                Label {objectName:'instructionBody';textFormat:Text.PlainText;text:modelData.body.replace(/\n\s*\n(?=• )/g,'\n');visible:text!=='';Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text;font.pixelSize:(Theme.fancy?14:12)*Theme.textScale;lineHeight:1.15}
                            }
                        }
                        DetailCard {title:I18n.t('Bestanden en koppelingen');Layout.fillWidth:true;visible:app.production&&(app.taskInfo.links||[]).length>0
                            Repeater {model:app.production?(app.taskInfo.links||[]):[]
                                RowLayout {required property var modelData;required property int index;Layout.fillWidth:true
                                    Icon {name:'file';ink:Theme.red;Layout.preferredWidth:18;Layout.preferredHeight:18}
                                    Capsule {text:modelData.name||modelData.url||I18n.t('Bijlage');Layout.fillWidth:true;enabled:!!modelData.url&&!backend.features.featureBusy;onClicked:if(modelData.downloadable)backend.features.viewPlanner(notes.taskId,index);else backend.openExternal(modelData.url)}
                                    Capsule {text:I18n.t('Offline');symbol:'file';visible:!!modelData.downloadable;enabled:app.production&&!backend.features.featureBusy;onClicked:backend.features.downloadPlanner(notes.taskId,index)}
                                }
                            }
                        }
                        DetailCard {title:I18n.t('Persoonlijke notitie');Layout.fillWidth:true
                            TextArea {id:noteText;objectName:'noteText';Layout.fillWidth:true;Layout.preferredHeight:Theme.fancy?150:100;wrapMode:TextEdit.Wrap;selectByMouse:true;Accessible.name:I18n.t('Task note');placeholderText:I18n.t('Voeg een notitie toe…');color:Theme.text;font.pixelSize:12*Theme.textScale
                                background:Rectangle {radius:3;color:Theme.elevated;border.width:noteText.activeFocus?2:1;border.color:noteText.activeFocus?Theme.blue:Theme.separator}}
                            Capsule {visible:!Theme.fancy;text:I18n.t('Bewaren en sluiten');primary:true;onClicked:notes.dismiss()}
                            Label {id:noteError;Layout.fillWidth:true;wrapMode:Text.Wrap;text:noteText.length+' / 5,000 · '+I18n.p('only on this device','alleen op dit apparaat');color:noteText.length>5000?Theme.red:Theme.secondary;font.pixelSize:10*Theme.textScale}
                        }
                    }
                    ColumnLayout {Layout.preferredWidth:Theme.fancy?220:Math.min(280,notes.width*.20);Layout.maximumWidth:Theme.fancy?notes.width*.36:280;Layout.alignment:Qt.AlignTop;spacing:12
                        DetailCard {title:I18n.t('Opdrachtgegevens');Layout.fillWidth:true
                            Repeater {model:app.production?(app.taskInfo.facts||[]):[]
                                RowLayout {required property var modelData;Layout.fillWidth:true;spacing:7
                                    Icon {name:parent.modelData.label==='Due'?'clock':parent.modelData.label==='Course'?'cal':'school';ink:Theme.secondary;Layout.preferredWidth:14;Layout.preferredHeight:14;Layout.alignment:Qt.AlignTop}
                                    ColumnLayout {Layout.fillWidth:true;spacing:2
                                        Label {text:I18n.t(Theme.fancy?parent.parent.modelData.label:({'Due':'Deadline','Posted':'Gepubliceerd','Course':'Vak','Type':'Type','Teacher':'Leerkracht','Classroom':'Lokaal'})[parent.parent.modelData.label]||parent.parent.modelData.label);color:Theme.secondary;font.pixelSize:10*Theme.textScale}
                                        Label {text:parent.parent.modelData.value;textFormat:Text.PlainText;color:Theme.text;font.pixelSize:11*Theme.textScale;Layout.fillWidth:true;wrapMode:Text.Wrap}
                                    }
                                }
                            }
                        }
                        DetailCard {title:I18n.t('Afwerken');Layout.fillWidth:true
                            RowLayout {Layout.fillWidth:true
                                TaskCheck {markSize:18;checked:tasks.completedIds.indexOf(notes.taskId)>=0;Accessible.name:I18n.t('Opdracht voltooien');onClicked:if(tasks.change(notes.taskId,'done',checked))app.notify(checked?'Taak voltooid':'Taak hersteld');else checked=Qt.binding(function(){return tasks.completedIds.indexOf(notes.taskId)>=0})}
                                Label {text:I18n.t('Opdracht voltooid');color:Theme.text;font.pixelSize:11*Theme.textScale;Layout.fillWidth:true;wrapMode:Text.Wrap}
                            }
                            Capsule {text:I18n.t('Focus');symbol:'focus';onClicked:if(notes.beforeClose()){focusView.taskId=notes.taskId;focusView.taskTitle=notes.taskTitle;notes.close();app.focusOpen=true}}
                        }
                        Label {visible:!!app.taskInfo.status;text:I18n.t(app.taskInfo.status||'');color:Theme.orange;Layout.fillWidth:true;wrapMode:Text.Wrap;font.pixelSize:11*Theme.textScale}
                        Capsule {text:I18n.t('Bronbericht openen');visible:app.production&&!!app.taskInfo.messageId;enabled:app.production&&!backend.features.featureBusy;Layout.fillWidth:true;onClicked:if(notes.beforeClose()){notes.close();app.pickSection(6);messagesPage.readMessage(app.taskInfo.messageId)}}
                    }
                }
            }
        }
    }

    Popup {id:taskDayPopup;objectName:'taskDayContext';parent:Overlay.overlay;visible:notes.visible&&!Theme.fancy&&app.width>1150;modal:false;focus:false;closePolicy:Popup.NoAutoClose;popupType:Popup.Item;padding:0
        width:390; height:notes.height;x:notes.x-width-18;y:notes.y;z:notes.z+1
        background:Rectangle {color:Theme.elevated;border.color:Theme.separator;radius:5}
        contentItem:ColumnLayout {spacing:0
            Label {text:I18n.t('Mijn planner');color:Theme.secondary;font.pixelSize:22*Theme.textScale;padding:18;Layout.fillWidth:true}
            Label {text:I18n.t(notes.dayContext.heading||'');textFormat:Text.PlainText;color:Theme.text;font.pixelSize:12*Theme.textScale;Layout.fillWidth:true;horizontalAlignment:Text.AlignHCenter;bottomPadding:16}
            ScrollView {id:taskDayScroll;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;contentWidth:availableWidth
                ColumnLayout {width:taskDayScroll.availableWidth;spacing:6
                    Repeater {model:notes.dayContext.items
                        RowLayout {required property var modelData;Layout.fillWidth:true;spacing:5
                            Label {text:parent.modelData.meta.split(' · ')[0].split(' – ')[0];color:Theme.secondary;font.pixelSize:10;Layout.preferredWidth:40;Layout.alignment:Qt.AlignTop;topPadding:8}
                            Rectangle {Layout.fillWidth:true;implicitHeight:Math.max(78,dayLessonText.implicitHeight+16);radius:4;color:Theme.lesson
                                ColumnLayout {id:dayLessonText;anchors.fill:parent;anchors.margins:8;spacing:3
                                    Label {text:parent.parent.parent.modelData.title;textFormat:Text.PlainText;color:Theme.text;font.bold:true;font.pixelSize:12*Theme.textScale;Layout.fillWidth:true;wrapMode:Text.Wrap}
                                    Label {text:parent.parent.parent.modelData.meta;textFormat:Text.PlainText;color:Theme.secondary;font.pixelSize:10*Theme.textScale;Layout.fillWidth:true;wrapMode:Text.Wrap}
                                    Label {text:parent.parent.parent.modelData.extra||'';textFormat:Text.PlainText;color:Theme.text;font.pixelSize:11*Theme.textScale;Layout.fillWidth:true;wrapMode:Text.Wrap;maximumLineCount:3;elide:Text.ElideRight}
                                    TapHandler {onTapped:app.openSection(parent.parent.parent.modelData)}
                                }
                            }
                        }
                    }
                    Item {implicitHeight:12}
                }
            }
        }
    }
    Sheet {id:details
        readonly property bool lessonDetails:app.sectionInfo.kind==='lesson'
        readonly property var links:app.sectionInfo.links||[]
        readonly property var contentLinks:lessonDetails?links.filter(link=>!link.lessonPage):links
        readonly property var lessonPage:lessonDetails?links.find(link=>link.lessonPage):null
        width:Math.min((lessonDetails?(Theme.fancy?800:940):560)*Theme.textScale,parent.width-24)
        height:Math.min(implicitHeight+(lessonDetails?64*Theme.textScale:0),parent.height*.86)
        headerColor:lessonDetails&&!Theme.fancy?Theme.lesson:Theme.elevated
        footer:lessonDetails?lessonFooter:null
        Component {id:lessonFooter
            Pane {padding:Theme.fancy?16:10;background:Rectangle {color:Theme.fancy?"transparent":Theme.elevated;Rectangle {width:parent.width;height:1;color:Theme.separator;visible:!Theme.fancy}}
                contentItem:RowLayout {Item {Layout.fillWidth:true}
                    Capsule {visible:!!details.lessonPage;text:details.lessonPage?details.lessonPage.name:'';symbol:'ext';onClicked:backend.openExternal(details.lessonPage.url)}
                    Capsule {primary:true;text:I18n.t('Close');onClicked:details.dismiss()}
                }
            }
        }
        GridLayout {Layout.fillWidth:true;columns:details.lessonDetails&&details.width>=680*Theme.textScale?2:1;columnSpacing:18;rowSpacing:12
            ColumnLayout {Layout.fillWidth:true;Layout.preferredWidth:details.lessonDetails?details.width*.6:-1;Layout.minimumWidth:0;Layout.alignment:Qt.AlignTop;spacing:12
                ColumnLayout {objectName:'emptyLessonContent';visible:details.lessonDetails&&!detailsText.text.trim()&&!details.contentLinks.length&&!(app.sectionInfo.assignments||[]).length
                    Layout.fillWidth:true;Layout.preferredHeight:(parent.parent.columns===2?230:108)*Theme.textScale;spacing:8
                    Item {Layout.fillHeight:true}
                    Icon {name:'file';ink:Theme.teal;Layout.alignment:Qt.AlignHCenter;implicitWidth:36*Theme.textScale;implicitHeight:implicitWidth}
                    Label {text:I18n.p('There is no content for this lesson.','Er is geen inhoud bij deze les.');Layout.fillWidth:true;wrapMode:Text.Wrap;horizontalAlignment:Text.AlignHCenter;color:Theme.secondary}
                    Item {Layout.fillHeight:true}
                }
                Label {textFormat:Text.PlainText;id:detailsText;visible:text.length>0;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text;font.pixelSize:16*Theme.textScale}
                Capsule {visible:app.production&&app.detailToken.startsWith('notes:');text:I18n.t('Reload note');onClicked:{detailsText.text=I18n.t('Loading note…');backend.openNote(app.detailToken.slice(6))}}
                Capsule {visible:app.production&&backend.school!==''&&app.sectionInfo.kind!=='lesson';text:I18n.t('Open Smartschool');onClicked:backend.openExternal('https://'+backend.school.replace(/^https?:\/\//,''))}
                Repeater {model:app.production?details.contentLinks:[];Capsule {required property var modelData;Layout.fillWidth:true;text:modelData.name||I18n.t('Open link');enabled:!!modelData.url&&!backend.features.featureBusy;onClicked:if(modelData.downloadable)backend.features.viewLinkedFile(modelData.url);else backend.openExternal(modelData.url)}}
                Repeater {model:app.production?(app.sectionInfo.assignments||[]):[]
                    ColumnLayout {id:assignmentDetail;required property var modelData;Layout.fillWidth:true
                        LessonAssignment {app:details.hostWindow;modelData:assignmentDetail.modelData;onOpened:details.close()}
                        Label {text:assignmentDetail.modelData.body||'';visible:text.length>0;textFormat:Text.PlainText;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text}
                        Repeater {model:assignmentDetail.modelData.links||[]
                            Capsule {required property var modelData;Layout.fillWidth:true;text:modelData.name||I18n.t('Open link');enabled:!!modelData.url&&!backend.features.featureBusy;onClicked:if(modelData.downloadable)backend.features.viewLinkedFile(modelData.url);else backend.openExternal(modelData.url)}
                        }
                    }
                }
            }
            Pane {visible:details.lessonDetails;Layout.fillWidth:true;Layout.minimumWidth:0;Layout.preferredWidth:parent.columns===2?details.width*.34:0;Layout.alignment:Qt.AlignTop;padding:16
                background:Surface {radius:Theme.fancy?18:6;backdrop:null;border.color:Theme.fancy?Theme.rim:Theme.separator}
                contentItem:ColumnLayout {spacing:9
                    Label {text:app.sectionInfo.title||'';visible:text.length>0;Layout.fillWidth:true;wrapMode:Text.Wrap;textFormat:Text.PlainText;color:Theme.text;font.bold:true}
                    Label {text:app.sectionInfo.schedule||'';Layout.fillWidth:true;wrapMode:Text.Wrap;textFormat:Text.PlainText;color:Theme.secondary;lineHeight:1.25}
                }
            }
        }
    }
    Surface {id:toast;objectName:'toast';anchors.horizontalCenter:parent.horizontalCenter;anchors.bottom:parent.bottom;anchors.bottomMargin:110*Theme.textScale;width:toastRow.implicitWidth+24;height:52;radius:Theme.fancy?26:3;visible:opacity>0;opacity:presence;strong:true;z:3
        property string displayedText:''
        property real presence:app.toastText!==''?1:0
        scale:Theme.motion?.99+.01*presence:1
        refraction:28+6*(1-presence)
        Behavior on presence{NumberAnimation{duration:Theme.motion?(app.toastText!==''?140:120):0;easing.type:Easing.OutCubic}}
        // Keep the message and surface width intact until the exit has finished.
        onOpacityChanged:if(opacity===0)displayedText=''
        Connections {target:app;function onToastTextChanged(){if(app.toastText!=='')toast.displayedText=app.toastText}}
        RowLayout {id:toastRow;anchors.centerIn:parent
            Label {textFormat:Text.PlainText;text:toast.displayedText;color:Theme.text}
            Capsule {text:I18n.t('Undo');quiet:true;visible:app.toastUndo;enabled:app.toastText!=='';onClicked:{planner.editMotion=true;tasks.undo();app.toastText=''}}
        }
    }
    Timer{id:toastTimer;interval:3500;onTriggered:app.toastText=''}
    Timer{id:refreshTimer;interval:1100;onTriggered:{app.busy=false;app.notify('Synthetic workspace refreshed',false)}}
    ShaderEffectSource {id:syncSource;visible:false;width:app.width;height:app.height;sourceItem:app.busy&&app.renderActive?plannerScene:null
        sourceRect:Qt.rect(0,0,width,height);textureSize:Qt.size(Math.ceil(width*.65),Math.ceil(height*.65));live:false;mipmap:true;smooth:true
        Connections {target:Theme
            function onDarkChanged(){if(app.busy)Qt.callLater(syncSource.scheduleUpdate)}
            function onStyleChanged(){if(app.busy)Qt.callLater(syncSource.scheduleUpdate)}
        }
    }
    onBusyChanged:if(busy)Qt.callLater(syncSource.scheduleUpdate)
    SyncProgress {app:app;backdrop:syncSource;action:app.production?backend.busyAction:'sync'}
    Sheet {id:noticeSheet;objectName:'noticeSheet';title:I18n.t(!app.production?'':backend.notice.kind==='release'?"What's new":backend.notice.kind==='update'?'Update available':'Update status')
        beforeClose:function(){if(app.production)backend.dismissNotice();return true}
        Label {objectName:'releaseNotesText';textFormat:Text.MarkdownText;text:I18n.t(app.production?(backend.notice.text||''):'');Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text;font.pixelSize:14*Theme.textScale;onLinkActivated:link=>backend.openExternal(link)}
        Capsule {text:I18n.t('Install update');visible:app.production&&backend.notice.kind==='update';enabled:!app.busy;onClicked:if(app.flushEdits())backend.installUpdate()}
        Capsule {text:I18n.t('Dismiss');onClicked:noticeSheet.dismiss()}
    }
    Sheet {id:warningsSheet;objectName:'warningsSheet';title:I18n.t('Sync warnings')
        Label {textFormat:Text.PlainText;text:I18n.t(app.production?backend.warnings:'');Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text}
        Capsule {text:I18n.t('Dismiss');onClicked:warningsSheet.close()}
    }
    Sheet {id:errorSheet;objectName:'errorSheet';title:I18n.t('Could not complete the action');Label {textFormat:Text.PlainText;text:I18n.t(app.errorText);Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text} Capsule {text:I18n.t('Retry sync');enabled:!app.busy;onClicked:{errorSheet.close();app.syncNow()}} Capsule {text:I18n.t('Change login details');onClicked:app.changeAccount()}}
    Shortcut{sequence:'Ctrl+F';enabled:app.section<7&&!app.focusPresented&&!app.busy&&!notes.visible&&!settings.visible&&!details.visible&&!errorSheet.visible&&!noticeSheet.visible&&!warningsSheet.visible&&!aiRequired.visible&&!reports.visible&&!offlineFiles.visible&&!replacements.visible&&!taskCollection.visible&&!filePreview.visible&&!messagesPage.readerVisible&&!messagesPage.composerVisible;onActivated:{if(app.section<6)app.searchOpen=true;app.searchFocus()}}
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
