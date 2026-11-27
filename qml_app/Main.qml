import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtQuick.Dialogs
import QtQuick.Shapes
ApplicationWindow {
    id:app
    readonly property bool production:typeof backend!=='undefined' && backend!==null
    readonly property bool starting:typeof backend!=='undefined' && backend===null
    property bool workspaceLoadFailed:false
    readonly property bool startupPageReady: pageViewport.selectedPage.status===Loader.Ready && (app.section>=2 || app.sceneReady)
    property bool preferencesReady:false
    property var taskInfo:({})
    property var sectionInfo:({})
    property string detailToken:''
    property string errorText:''
    width:1100;height:800;minimumWidth:focusPresented?360:760;minimumHeight:focusPresented?420:600
    visible:false;title:I18n.t(production||starting?'Smartschool Planner':'Smartschool Planner · demo');color:Theme.bg
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
    readonly property var planner: tasksLoader.item
    readonly property var sectionPages: section === 2 ? scheduleLoader.item
        : !Theme.fancy ? null
        : section === 3 ? sectionsLoader.item
        : section === 4 ? glassResultsLoader.item
        : section === 5 ? glassLvsLoader.item : null
    readonly property var messagesPage: messagesLoader.item
    readonly property var settings: settingsLoader.item
    readonly property var notes: noteLoader.item
    readonly property var details: detailLoader.item
    readonly property var reports: reportLoader.item
    readonly property var offlineFiles: offlineLoader.item
    readonly property string workspaceAccount: production ? backend.features.accountKey : ''
    onWorkspaceAccountChanged: {
        if (notes) {
            notes.editorText = ''
            notes.close()
        }
        if (details) {
            details.bodyText = ''
            details.close()
        }
        reports?.close()
        offlineFiles?.close()
        taskInfo = ({})
        sectionInfo = ({})
        detailToken = ''
    }
    readonly property var filePreview: filePreviewLoader.item
    property bool settingsRequested: false
    property var pendingFilePreview: null
    property string pendingMessageId: ""
    property bool pendingMessageSearch: false
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
    function applyPreferences(p) {
        Theme.fancy = p.renderingMode !== 'performance'
        Theme.style = p.style || 'clear'
        Theme.scheme = p.scheme || 'light'
        Theme.glassLevel = p.glassLevel === undefined ? 0 : p.glassLevel
        Theme.refractionLevel = p.distortion === undefined ? .25 : p.distortion
        Theme.textScale = p.textSize || 1
        Theme.wallpaperIndex = p.wallpaperIndex === undefined ? 1 : p.wallpaperIndex
        Theme.reducedMotion = !!p.reducedMotion
        Theme.animatedBackground = p.animatedBackground !== false
        Theme.highContrast = !!p.highContrast
        I18n.language = p.language || 'en'
    }
    function checkRenderingChoice() {
        if (production && backend.renderingChoicePending) openSettings()
    }
    Component.onCompleted: {
        Theme.fancy = initialFancy
        Theme.matched = typeof initialMatched !== 'undefined' && initialMatched
        if (benchmarkEnabled || Theme.matched) Theme.scheme = 'light'
        if (Theme.matched) Theme.animatedBackground = false
        if (starting) applyPreferences(startupPreferences)
        else if (production) applyPreferences(backend.settings)
        preferencesReady = true
        Qt.callLater(checkRenderingChoice)
    }
    onStartingChanged: if (!starting) Qt.callLater(function() {
        pageViewport.selectedPage.openCurrentPage()
        checkRenderingChoice()
    })
    Timer{id:preferenceSave;interval:250;onTriggered:if(app.production&&app.preferencesReady)backend.saveSettings(app.preferences())}
    Connections {target:I18n;function onLanguageChanged(){preferenceSave.restart()}}
    Connections {target:Theme
        function onFancyChanged(){preferenceSave.restart()} function onStyleChanged(){preferenceSave.restart()} function onSchemeChanged(){preferenceSave.restart()}
        function onGlassLevelChanged(){preferenceSave.restart()} function onRefractionLevelChanged(){preferenceSave.restart()} function onTextScaleChanged(){preferenceSave.restart()}
        function onWallpaperIndexChanged(){preferenceSave.restart()} function onReducedMotionChanged(){preferenceSave.restart()} function onAnimatedBackgroundChanged(){preferenceSave.restart()} function onHighContrastChanged(){preferenceSave.restart()}
    }
    Connections {target:app.production?backend:null
        function onChanged(){app.busy=backend.busy;Qt.callLater(app.showNotice)}
        function onGroupsChanged(section){if(section<0&&app.detailToken.startsWith('notes:')){details?.close();app.detailToken='';app.sectionInfo=({});if(details)details.bodyText=''}if(section<0||app.section===section)app.fixtureRevision++;if(section<0&&notes?.visible&&notes.taskId)app.taskInfo=backend.taskDetail(notes.taskId)}
        function onError(message){app.errorText=message;errorSheet.open()}
        function onDetailReady(token,info){if(details?.visible&&token===app.detailToken){app.sectionInfo=info;details.bodyText=info.body}}
        function onQuitRequested(){app.close()}
    }

    Binding {target:Theme;property:'active';value:app.renderActive}
    Binding {target:Theme;property:'backdrop';value:backdrop}
    font.family:Theme.fancy?'Segoe UI Variable':'Segoe UI';font.pixelSize:14*Theme.textScale
    palette.text:Theme.text;palette.windowText:Theme.text;palette.buttonText:Theme.text;palette.highlight:Theme.blue;palette.base:Theme.elevated;palette.button:Theme.surface;palette.window:Theme.bg
    function showNotice(){if(!production)return;if(backend.notice.text){if(!noticeSheet.opened)noticeSheet.open()}else noticeSheet.close()}
    function searchFocus(){
        if(section!==6)search.forceActiveFocus()
        else if(messagesPage)messagesPage.focusSearch()
        else pendingMessageSearch=true
    }
    function toggleSearch(){if(section===6){searchFocus();return}searchOpen=!searchOpen;if(searchOpen)search.forceActiveFocus();else searchText=''}
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
    function flushEdits(){return (!notes?.visible||notes.beforeClose())&&(!production||backend.features.composer.flushForExit()&&backend.saveSettings(preferences()))}
    function changeAccount(){if(flushEdits()){notes?.close();focusOpen=false;backend.openSetup()}}
    function syncNow(){if(flushEdits()){notes?.close();backend.syncNow()}}
    function preferences(){return {language:I18n.language,renderingMode:Theme.fancy?'fancy':'performance',style:Theme.style,scheme:Theme.scheme,glassLevel:Theme.glassLevel,distortion:Theme.refractionLevel,textSize:Theme.textScale,wallpaperIndex:Theme.wallpaperIndex,reducedMotion:Theme.reducedMotion,animatedBackground:Theme.animatedBackground,highContrast:Theme.highContrast}}
    function showTask(id,title,note){
        taskInfo=production?backend.taskDetail(id):({})
        if(production&&Object.keys(taskInfo).length===0){errorText='This assignment is no longer available for editing. Sync again or open its lesson in Smartschool.';errorSheet.open();return}
        const sheet = loadDialog(noteLoader, "TaskNoteSheet.qml")
        if (!sheet) return
        sheet.taskId = id
        sheet.taskTitle = title
        sheet.editorText = note
        sheet.open()
    }
    function loadDialog(loader, source, properties) {
        if (!loader.item)
            loader.setSource(source, Object.assign({app:app, parent:app.contentItem}, properties || {}))
        return loader.item
    }
    function showDetail(title, body) {
        const sheet = loadDialog(detailLoader, "SectionDetailSheet.qml")
        if (!sheet) return false
        sheet.title = title || ''
        sheet.bodyText = body || ''
        sheet.open()
        return true
    }
    function openSection(item) {
        sectionInfo = item
        detailToken = item.id
        const lesson = item.kind === 'lesson'
        if (!showDetail(lesson ? item.lessonTitle : item.title, lesson ? item.lessonContent : item.body)) return
        if (item.kind === 'notes') {
            const cached = backend.noteDetails[item.id]
            if (cached) {
                backend.markRead(item.id)
                sectionInfo = cached
                details.bodyText = cached.body
            } else {
                details.bodyText = I18n.t('Loading note…')
                backend.openNote(item.id.slice(6))
            }
        } else if (item.kind === 'absences') {
            backend.markRead(item.id)
        }
    }
    function pickSection(i){focusOpen=false;if(i===5&&section===5&&sectionPages)sectionPages.requestTop();section=i}
    function openSourceMessage(id){
        pickSection(6)
        if(messagesPage)messagesPage.readMessage(id)
        else pendingMessageId=id
    }
    onSectionChanged:if(section===3||section>=6){headerCollapsed=false;searchOpen=false;settleHeader()}
    // Snap interrupted scroll motion before measuring a newly entered page.
    function settleHeader(){headerMotion.complete();headerFrame.Layout.preferredHeight=Qt.binding(function(){return app.headerCollapsed&&!app.searchOpen?0:headerFrame.implicitHeight});content.ensurePolished()}
    function restoreFocusBounds(){
        if(focusOpen||!focusPresented)return
        width=savedBounds.width;height=savedBounds.height;x=savedBounds.x;y=savedBounds.y
        focusOnTop=false;focusPresented=false
        if(wasMaximized)showMaximized()
    }
    function openSettings(){
        if (settings) settings.open()
        else {
            settingsRequested = true
            if (settingsLoader.status !== Loader.Loading)
                settingsLoader.setSource("SettingsPanel.qml", {app:app, backdrop:backdrop, parent:app.contentItem, objectName:"settingsPanel"})
        }
    }
    function loadFocus(){
        if(!focusLoader.item)
            focusLoader.setSource("FocusView.qml", {app:app, backdrop:backdrop})
        return focusLoader.item
    }
    function openFocus(id,title,done){
        const view=loadFocus()
        view.taskId=id
        view.taskTitle=title
        view.completed=done
        focusOpen=true
    }
    onFocusOpenChanged:{
        if(focusOpen&&!focusPresented){
            loadFocus()
            savedBounds=Qt.rect(x,y,width,height);wasMaximized=visibility===Window.Maximized
            focusPresented=true;showNormal();width=420;height=560
            stopwatch.reset();stopwatch.toggle()
        }else if(!focusOpen&&focusReveal===0)restoreFocusBounds()
    }
    onClosing:close=>{if(!flushEdits()){close.accepted=false;if(notes?.visible)notes.focusEditor();else if(messagesPage)messagesPage.focusDraft()}}
    component PageLoader: Loader {
        id: pageLoader
        required property string page
        required property bool current
        property var properties: ({app: app})
        asynchronous: !benchmarkEnabled
        visible: current && status === Loader.Ready

        function loadPage() {
            if (!app.starting && status === Loader.Null)
                setSource(page, properties)
        }
        Component.onCompleted: if(current)loadPage()
        function openCurrentPage() {
            if (app.starting || !current || status === Loader.Ready) return
            if (pageViewport.selectedPage === pageLoader && app.section >= 2) {
                // Give the requested page priority over its idle load.
                if (status === Loader.Loading) source = ""
                asynchronous = false
            }
            loadPage()
        }
        onCurrentChanged: if(current)Qt.callLater(openCurrentPage)
    }
    Timer {
        id: backgroundPages
        interval: 120
        repeat: true
        readonly property var pages: Theme.fancy ? [messagesLoader, sectionsLoader, glassResultsLoader, glassLvsLoader]
                                                  : [messagesLoader, timetableLoader, resultsLoader, lvsLoader]
        running: (app.sceneReady || app.section >= 2) && app.renderActive && pageViewport.selectedPage.status === Loader.Ready
                 && pages.some(page => page.status === Loader.Null)
        onTriggered: {
            if (!pages.some(page => page.status === Loader.Loading))
                pages.find(page => page.status === Loader.Null)?.loadPage()
        }
    }
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
        readonly property string accountLabel:app.starting?I18n.p('Your account','Je account'):app.production?(backend.accountName||I18n.p('Your account','Je account')):'Sam Example'
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
                Text {anchors.centerIn:parent;text:app.starting?'?':app.production?backend.accountInitial:'S';color:'#713326';font.bold:true;font.pixelSize:13*Theme.textScale}
            }
            Label {id:accountNameLabel;objectName:'accountNameLabel';Layout.minimumWidth:globalBar.compact?42:60;Layout.preferredWidth:implicitWidth;text:globalBar.accountLabel;textFormat:Text.PlainText;elide:Text.ElideRight;color:'white';font.pixelSize:(globalBar.compact?12:14)*Theme.textScale;font.weight:Font.Medium;Layout.maximumWidth:globalBar.tight?110*Theme.textScale:Math.min(240,app.width*.22)
                HoverHandler {id:accountNameHover}
                GlassToolTip {requested:accountNameLabel.truncated&&accountNameHover.hovered;text:accountNameLabel.text}
            }
            Item {Layout.fillWidth:true}
            LayoutItemProxy {target:navigationBar;visible:!globalBar.stackNavigation}
            GlobalAction {objectName:'globalSearch';text:I18n.t('Search');symbol:'searchBtn';onClicked:app.toggleSearch()}
            GlobalAction {objectName:'globalSettings';text:I18n.t('Settings');symbol:'settingsBtn';enabled:!app.starting;onClicked:app.openSettings()}
            GlobalAction {id:globalSync;objectName:'globalSync';text:I18n.t('Sync now');symbol:'syncBtn';spinning:app.busy;enabled:!app.starting&&(app.section!==6||!!messagesPage&&messagesPage.canRefresh);onClicked:app.section===6?messagesPage.refreshMessages():app.production?app.syncNow():refreshTimer.restart()}
            GlobalAction {objectName:'globalReplacements';text:I18n.t('Teacher replacements');symbol:'teacherOff';enabled:!app.starting;onClicked:app.showReplacements()}
        }
    }
    ColumnLayout {
        // Keep the reading position while Focus temporarily resizes the window.
        id:content;opacity:app.plannerReveal;enabled:!app.focusPresented
        x:Theme.fancy?20:(app.width<1000?12:20)*Theme.textScale;y:Theme.fancy?24:globalBar.height+12*Theme.textScale;width:(app.focusPresented?app.savedBounds.width:app.width)-2*x;height:(app.focusPresented?app.savedBounds.height:app.height)-y-(Theme.fancy?0:12*Theme.textScale);spacing:Theme.fancy?6:4
        Item {id:headerFrame;visible:Theme.fancy||app.section<3;Layout.fillWidth:true;implicitHeight:(Theme.fancy?75:52)*Theme.textScale;Layout.preferredHeight:Theme.fancy&&app.headerCollapsed&&!app.searchOpen?0:implicitHeight;clip:app.headerCollapsed;z:3
            opacity:Theme.fancy&&app.headerCollapsed&&!app.searchOpen?0:1
            Behavior on opacity{enabled:(!planner||!planner.entryPending)&&(!sectionPages||!sectionPages.topResetPending);NumberAnimation{duration:Theme.motion?200:0}}
            Behavior on Layout.preferredHeight{enabled:Theme.motion&&(app.section<2?(!planner||!planner.entryPending):(!sectionPages||!sectionPages.topResetPending));NumberAnimation{id:headerMotion;duration:220;easing.type:Easing.OutCubic}}
            Item {anchors.fill:parent;anchors.leftMargin:0;anchors.rightMargin:0
                ColumnLayout {anchors.left:parent.left;anchors.right:headerSlot.left;anchors.rightMargin:16;anchors.verticalCenter:parent.verticalCenter;spacing:3
                    Label {textFormat:Text.PlainText;text:I18n.t((Theme.fancy?['To-do','Overdue','Planner','Planner','Grades','LVS','Messages']:['Mijn taken','Gemist','Planner','Planner','Resultaten','LVS','Berichten'])[app.section]||'To-do');font.pixelSize:(Theme.fancy?34:21)*Theme.textScale;font.bold:Theme.fancy;color:Theme.text
                        MouseArea {anchors.fill:parent;onPressed:app.startSystemMove()} }
                    Label {id:syncStatus;visible:Theme.fancy;objectName:'syncStatus';Layout.fillWidth:true;elide:Text.ElideRight;textFormat:Text.PlainText;text:app.starting?'':I18n.t(app.production?backend.status:'Last synced · 24 Oct, 09:00 · Synthetic workspace');font.pixelSize:13*Theme.textScale;color:Theme.secondary
                        HoverHandler {id:statusHover}
                        GlassToolTip {requested:syncStatus.truncated&&statusHover.hovered;text:syncStatus.text}
                    }
                }
                Item {id:headerSlot;anchors.right:parent.right;anchors.verticalCenter:parent.verticalCenter;width:headerActions.implicitWidth;height:38
                Row {id:headerActions;parent:floatingControls;spacing:8
                readonly property point origin:app.controlPosition(headerSlot)
                x:origin.x;y:origin.y;opacity:headerFrame.opacity;visible:Theme.fancy&&!app.focusPresented&&opacity>0
                Capsule {selectorMaterial:true;backdrop:topSource;glassTracking:headerActions.x+headerActions.y; width:38;text:I18n.t('Search');symbol:'searchBtn';iconOnly:true;visible:app.section<7;onClicked:app.toggleSearch()}
                Capsule {id:syncControl;objectName:'syncButton';selectorMaterial:true;backdrop:topSource;glassTracking:headerActions.x+headerActions.y; width:38;text:I18n.t(app.production||app.starting?'Sync now':'Refresh synthetic data');symbol:'syncBtn';iconOnly:true;enabled:!app.starting;onClicked:{if(app.production){app.syncNow()}else{app.busy=true;refreshTimer.restart()}}
                    contentItem:Item {implicitWidth:20;implicitHeight:20
                        Icon {id:syncGlyph;objectName:'syncGlyph';anchors.centerIn:parent;width:20*Theme.textScale;height:20*Theme.textScale;name:'syncBtn';ink:syncControl.labelInk
                            RotationAnimator on rotation {objectName:'syncSpin';from:0;to:360;duration:900;loops:Animation.Infinite;running:syncControl.visible&&app.busy&&app.renderActive&&app.active&&Theme.motion;onStopped:syncGlyph.rotation=0}}
                    }}
                Capsule {selectorMaterial:true;backdrop:topSource;glassTracking:headerActions.x+headerActions.y; width:38;objectName:'settingsButton';text:I18n.t('Settings');symbol:'settingsBtn';iconOnly:true;enabled:!app.starting;onClicked:app.openSettings()}
                }
                }
            }
        }
        Capsule {objectName:'warningsButton';visible:app.production&&backend.warnings!=='';Layout.alignment:Qt.AlignLeft;text:I18n.t('Sync warnings');symbol:'warn';onClicked:warningsSheet.open()}
        TextField {id:search;objectName:'search';Layout.fillWidth:true;visible:app.searchOpen&&app.section<6;implicitWidth:1;implicitHeight:44;text:app.searchText;onTextChanged:app.searchText=text
            placeholderText:I18n.t(['Search tasks…','Search missed tasks…','Search schedule…','Search all classes…','Search grades…','Search LVS…'][app.section]||'');Accessible.name:I18n.t('Search current tab');color:Theme.text;placeholderTextColor:Theme.secondary;leftPadding:18;selectByMouse:true
            background:Surface{radius:Theme.fancy?22:3;border.color:search.activeFocus?Theme.blue:Theme.rim}
            Keys.onEscapePressed:{app.searchOpen=false;app.searchText=''}
        }
        Item {id:pageViewport;objectName:'pageViewport';clip:app.section===3||!app.headerCollapsed||app.searchOpen;Layout.fillWidth:true;Layout.fillHeight:true
        readonly property var selectedPage: app.section<2 ? tasksLoader
            : app.section===6 ? messagesLoader
            : app.section===2 ? scheduleLoader
            : app.section===3 ? (Theme.fancy ? sectionsLoader : timetableLoader)
            : app.section===4 ? (Theme.fancy ? glassResultsLoader : resultsLoader)
            : Theme.fancy ? glassLvsLoader : lvsLoader
        readonly property bool loading: !app.workspaceLoadFailed
            && (selectedPage.status === Loader.Loading || selectedPage.status === Loader.Null
                || app.settingsRequested || !!app.pendingFilePreview
                || (app.section===6 && !!(app.messagesPage?.composerLoading || app.messagesPage?.waitingForMessages)))
        onLoadingChanged: if(!loading)pageSpinner.showRing=false
        PageLoader {id:tasksLoader;page:"PlannerView.qml";anchors.fill:parent;current:app.section<2}
        Connections {target:app.planner
            function onFocusTask(id,title,done){app.openFocus(id,title,done)}
            function onEditNote(id,title,note){app.showTask(id,title,note)}
        }
        ColumnLayout {anchors.fill:parent;spacing:Theme.fancy?15:0;visible:app.section>=2&&app.section<6
            RowLayout {Layout.fillWidth:true;visible:Theme.fancy&&app.production&&app.section===3
                Capsule {objectName:'replacementButton';visible:app.section===3;text:I18n.t('Teacher replacements');symbol:'file';onClicked:app.showReplacements()}
                Item {Layout.fillWidth:true}
            }
            Item {Layout.fillWidth:true;Layout.fillHeight:true;clip:app.section===3
                PageLoader {id:timetableLoader;page:"TimetableView.qml";anchors.fill:parent;current:app.section===3&&!Theme.fancy}
                component ListPage: PageLoader {
                    required property int section
                    page: "SectionsView.qml"
                    properties: ({app: app, section: section})
                    anchors.fill: parent
                    anchors.leftMargin: Theme.fancy ? -16 : 0
                    anchors.rightMargin: Theme.fancy ? -16 : 0
                }
                ListPage {id:scheduleLoader;section:2;current:app.section===2}
                ListPage {id:sectionsLoader;section:3;current:Theme.fancy&&app.section===3}
                ListPage {id:glassResultsLoader;section:4;current:Theme.fancy&&app.section===4}
                ListPage {id:glassLvsLoader;section:5;current:Theme.fancy&&app.section===5}
                Connections {target:app.sectionPages
                    function onDetail(title,body){app.showDetail(title,body)}
                }
                PageLoader {id:resultsLoader;page:"ResultsLvsView.qml";anchors.fill:parent;current:!Theme.fancy&&app.section===4;properties:({app:app, grades:true})}
                PageLoader {id:lvsLoader;page:"ResultsLvsView.qml";anchors.fill:parent;current:!Theme.fancy&&app.section===5;properties:({app:app, grades:false})}
            }
        }
        PageLoader {id:messagesLoader;page:"MessagesView.qml";anchors.fill:parent;current:app.section===6
            onLoaded: {
                if (current && app.pendingMessageId)
                    item.readMessage(app.pendingMessageId)
                if (current && app.pendingMessageSearch)
                    item.focusSearch()
                app.pendingMessageId = ""
                app.pendingMessageSearch = false
            }
        }
        BusyIndicator {
            id: pageSpinner
            property bool showRing: false
            objectName: "pageLoadingIndicator"
            anchors.centerIn: parent
            width: 36 * Theme.textScale
            height: width
            padding: 0
            running: pageViewport.loading && showRing
            visible: running
            Accessible.name: I18n.p("Loading page…", "Pagina laden…")
            contentItem: Item {
                Rectangle {
                    anchors.fill: parent
                    radius: width / 2
                    color: "transparent"
                    border.width: 3 * Theme.textScale
                    border.color: Theme.alpha(Theme.blue, .22)
                }
                Shape {
                    id: spinnerArc
                    anchors.fill: parent
                    preferredRendererType: Shape.CurveRenderer
                    ShapePath {
                        fillColor: "transparent"
                        strokeColor: Theme.blue
                        strokeWidth: 3 * Theme.textScale
                        capStyle: ShapePath.RoundCap
                        PathAngleArc {
                            centerX: spinnerArc.width / 2
                            centerY: spinnerArc.height / 2
                            radiusX: centerX - 1.5 * Theme.textScale
                            radiusY: radiusX
                            startAngle: -90
                            sweepAngle: 105
                        }
                    }
                    RotationAnimator on rotation {
                        from: 0
                        to: 360
                        duration: 900
                        loops: Animation.Infinite
                        running: pageSpinner.running && app.renderActive && Theme.motion
                    }
                }
            }
        }
        Timer { interval: 120; running: pageViewport.loading; onTriggered: pageSpinner.showRing=true }
        Label {
            anchors.centerIn: parent
            visible: app.workspaceLoadFailed || pageViewport.selectedPage.status === Loader.Error
            text: I18n.p("This page could not be loaded.", "Deze pagina kon niet worden geladen.")
            color: Theme.text
        }
        }
    }
    }
    // One bounded capture for the floating controls; those controls live outside its source.
    ShaderEffectSource {id:topSource;objectName:'topControlSource';visible:false
        width:app.width;height:Math.min(app.height,(app.headerCollapsed?112:220)*Theme.textScale+(planner?.typeMenuVisible||sectionPages?.courseMenuVisible?240:0))
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
    Loader {id:focusLoader;anchors.fill:parent;visible:app.focusPresented;opacity:app.focusReveal
        scale:Theme.reducedMotion?1:.97+.03*app.focusReveal
        transform:Translate {y:Theme.reducedMotion?0:10*(1-app.focusReveal)}}
    Connections {target:focusLoader.item;function onLeave(){app.focusOpen=false}}
    Loader {
        id:settingsLoader
        asynchronous:true
        onLoaded: {
            if (app.settingsRequested) item.open()
            app.settingsRequested = false
        }
        onStatusChanged: if (status === Loader.Error && app.settingsRequested) {
            app.settingsRequested = false
            app.notify(I18n.p("Settings could not open.", "Instellingen konden niet worden geopend."), false)
        }
    }
    Loader {id:noteLoader}
    Loader {id:detailLoader}
    Loader {id:reportLoader}
    Loader {id:offlineLoader}
    function showOfflineFiles(){loadDialog(offlineLoader,"ResourceSheet.qml",{offlineOnly:true})?.open()}
    function showReports(){loadDialog(reportLoader,"ResourceSheet.qml")?.open()}
    Loader {
        id:filePreviewLoader
        asynchronous:true
        onLoaded: {
            if (app.pendingFilePreview) item.present(app.pendingFilePreview)
            app.pendingFilePreview = null
        }
        onStatusChanged: if (status === Loader.Error && app.pendingFilePreview) {
            app.pendingFilePreview = null
            app.notify(I18n.p("File preview could not open.", "Bestandsvoorbeeld kon niet worden geopend."), false)
        }
    }
    Connections {target:app.production?backend.features:null
        function onFilePreviewRequested(info){
            if (filePreview) filePreview.present(info)
            else {
                app.pendingFilePreview = info
                if (filePreviewLoader.status !== Loader.Loading)
                    filePreviewLoader.setSource("FilePreview.qml", {service:backend.features, parent:app.contentItem})
            }
        }
        function onCloseFilePreview(){
            app.pendingFilePreview = null
            filePreview?.clearAndClose()
        }
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
    Sheet {id:aiRequired;objectName:'aiRequired';title:I18n.t('AI required')
        Label {textFormat:Text.PlainText;text:I18n.t('AI requires a Gemini API key. Add one in Settings → Change login details.');color:Theme.text;Layout.fillWidth:true;wrapMode:Text.Wrap}
    }
    FileDialog {id:saveFile;property string downloadKey:'';fileMode:FileDialog.SaveFile;title:I18n.t('Save downloaded file')
        onAccepted:backend.features.exportDownloaded(downloadKey,selectedFile)
    }
    Connections {target:app.production?backend.features:null
        function onSaveRequested(key,url){saveFile.downloadKey=key;saveFile.selectedFile=url;saveFile.open()}
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
            Capsule {text:I18n.t('Undo');quiet:true;visible:app.toastUndo;enabled:app.toastText!=='';onClicked:{if(planner)planner.editMotion=true;tasks.undo();app.toastText=''}}
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
    Shortcut{sequence:'Ctrl+F';enabled:app.section<7&&!app.focusPresented&&!app.busy&&!notes?.visible&&!settings?.visible&&!details?.visible&&!errorSheet.visible&&!noticeSheet.visible&&!warningsSheet.visible&&!aiRequired.visible&&!reports?.visible&&!offlineFiles?.visible&&!replacements.visible&&!taskCollection.visible&&!filePreview?.visible&&(!messagesPage||!messagesPage.readerVisible&&!messagesPage.composerVisible);onActivated:{if(app.section<6)app.searchOpen=true;app.searchFocus()}}
    Shortcut{sequence:'Escape';enabled:app.focusOpen&&!app.busy&&!notes?.visible&&!settings?.visible&&!details?.visible&&!errorSheet.visible&&!noticeSheet.visible&&!warningsSheet.visible;onActivated:app.focusOpen=false}
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
    onScrollProgressChanged: planner?.benchmarkScroll(scrollProgress)
    Timer { id: transitionTimer; interval: 180; repeat: true
        onTriggered: { app.section = (++app.transitionStep) % 6; if (app.transitionStep >= 20) { stop(); app.section = 0 } } }
    function bench(action) {
        if (action === "scroll") { phase = "scroll"; frameSamples = []; scrollAnimation.start() }
        if (action === "transition") { phase = "transition"; frameSamples = []; transitionStep = 0; transitionTimer.start() }
        if (action === "idle") { phase = "idle" }
        if (action === "search") { planner?.benchmarkSearch("quadratic") }
        if (action === "clearSearch") { planner?.benchmarkSearch("") }
        if (action === "settings") openSettings()
        if (action === "closeSettings") settings?.close()
        if (action === "focus") { focusOpen = true }
    }
}
