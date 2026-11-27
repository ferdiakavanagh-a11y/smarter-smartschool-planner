import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "ResultPalette.js" as ResultPalette
ListView {
    id:view;objectName:'sectionList'
    required property var app
    property int section:app.section
    property string query:''
    property int revision:0
    property var readNotes: ({})
    property bool topResetPending:false
    opacity:topResetPending?0:1
    property string gradeCourse:'All subjects'
    property string lvsKind:'all'
    property var preview:({})
    readonly property var previewItem:Object.keys(preview).length?preview:(model&&model.length&&model[0].items.length?model[0].items[0]:({}))
    readonly property bool courseMenuVisible:headerItem?headerItem.courseMenuVisible:false
    function resetTop(){
        if(!visible||view.section<2||height<=0)return
        scrollMotion.stop();cancelFlick()
        if(headerItem)headerItem.forceLayout()
        forceLayout();app.headerCollapsed=false
        let target=-1
        if(app.production&&(view.section===2||view.section===3)&&!query.trim()){
            let today=Qt.formatDate(new Date(),'yyyy-MM-dd'),lastDay=-1
            for(let i=0;i<model.length;i++)if(model[i].date&&(i===0||model[i].date!==model[i-1].date)){
                lastDay=i
                if(model[i].date>=today){target=i;break}
            }
            if(target<0)target=lastDay
        }
        if(target>=0)positionViewAtIndex(target,ListView.Center)
        else positionViewAtBeginning()
    }
    function requestTop(){topResetPending=true;app.headerCollapsed=false;scrollMotion.stop();cancelFlick()}
    onVisibleChanged:if(visible&&view.section>=2){query=app.searchText;requestTop()}
    function flatten(groups){
        let rows=[]
        for(let group of groups)for(let i=0;i<group.items.length;i++)
            rows.push({date:group.date||'',heading:i===0?group.heading:'',average:i===0?group.average||'':'',items:[group.items[i]],first:i===0,last:i===group.items.length-1,rowIndex:i})
        return rows
    }
    signal detail(string title,string body)
    Layout.leftMargin:-16;Layout.rightMargin:-16
    clip:false;spacing:0;topMargin:0;bottomMargin:Math.max((Theme.fancy?120:24)*Theme.textScale,(view.section===2||view.section===3)&&!query.trim()?height/2:0);reuseItems:true;cacheBuffer:180
    boundsBehavior:Flickable.StopAtBounds
    displayMarginBeginning:220*Theme.textScale
    model: {
        let dataRevision=view.revision
        if(app.production){let groups=backend.groups(view.section,query,view.section===4?gradeCourse:'All subjects');if(view.section===5&&lvsKind!=='all')groups=groups.map(group=>Object.assign({},group,{items:group.items.filter(item=>item.kind===lvsKind)})).filter(group=>group.items.length);return flatten(groups)}
        if(app.datasetIndex===0)return []
        let rows=[]
        let courses=['Mathematics','Nederlands','Sciences','History','Français','日本語 & cultuur']
        if(view.section===2||view.section===3){
            for(let i=0;i<18;i++)rows.push({id:'lesson-'+i,heading:i%6===0?['Monday, 26 October','Tuesday, 27 October','Wednesday, 28 October'][Math.floor(i/6)]:'',title:courses[i%6],meta:(8+Math.floor(i%6))+':30 – '+(9+Math.floor(i%6))+':20 · Room '+(101+i%6)+' · Demo teacher',body:'Lesson overview\n\nSynthetic study material for '+courses[i%6]+'.\n\nAssignment: prepare one question for our next lesson.',extra:i%3===0?'Assignment · prepare one question':''})
        }else if(view.section===4){
            rows.push({id:'average',heading:'Overall average',title:'80%',meta:'Weighted by available points · synthetic results',body:'128 / 160 counting points. This demonstration includes counting and noncounting results.',extra:'Saved example · refresh unavailable'})
            for(let i=0;i<12;i++)rows.push({id:'grade-'+i,heading:i%2===0?courses[Math.floor(i/2)]:'',title:i%2===0?'Chapter review':'Class participation',meta:'23 Oct · '+(i%3===0?'Doesn’t count':'Counts toward total'),body:'Course: '+courses[Math.floor(i/2)]+'\n\nFeedback: explain your reasoning and check the final step.\n\nSynthetic result; no account connected.',extra:[ '8 / 10','14 / 20','18 / 20'][i%3]})
        }else if(view.section===5){
            for(let i=0;i<8;i++)rows.push({id:'lvs-'+i,heading:i===0?I18n.t('Notes'):i===5?I18n.t('Absences'):'',title:i<5?['Study progress','A note about participation','Project feedback','Planning support','Next steps'][i-0]:'Absence · authorised',meta:'23 Oct · '+(i<5?'Demo tutor':'Morning · A'),body:i<5?'Public synthetic note\n\nKeep using your planner to break larger assignments into small steps.\n\nZoë · 日本語 · نور':'Synthetic authorised absence. No personal school record.',extra:'',unread:!readNotes['lvs-'+i]})
        }
        let q=query.toLocaleLowerCase()
        let groups=[],heading='',lastHeading=''
        for(let row of rows){
            if(row.heading)heading=row.heading
            if(q&&!(row.title+' '+row.meta+' '+row.body).toLocaleLowerCase().includes(q))continue
            if(view.section===4||!groups.length||heading!==lastHeading){
                groups.push({heading:heading!==lastHeading?heading:'',items:[]})
            }
            groups[groups.length-1].items.push(row)
            lastHeading=heading
        }
        return flatten(groups)
    }
    ScrollBar.vertical:ScrollBar{id:scrollBar;parent:view.parent;visible:view.visible;x:view.x+view.width-width-16;y:view.y;height:view.height}
    SmoothScroll {id:scrollMotion; view:view }
    Connections {target:app
        function onSearchTextChanged(){if(view.visible){view.query=app.searchText;view.requestTop()}}
        function onAfterAnimating(){if(view.topResetPending&&view.visible&&view.height>0){app.settleHeader();view.resetTop();view.topResetPending=false}}
    }
    Connections {target:app.production?backend:null
        function onGroupsChanged(section){
            if(section>=0&&section!==view.section)return
            view.preview=({})
            view.readNotes=({})
            if(view.section===4&&backend.gradeCourses.indexOf(view.gradeCourse)<0)view.gradeCourse='All subjects'
            view.revision++
            if(view.visible&&(view.section===2||view.section===3))view.requestTop()
        }
    }
    onContentYChanged:if(view.visible&&!topResetPending&&(atYBeginning||moving||scrollMotion.active||scrollMotion.glide.running||scrollBar.pressed))app.headerCollapsed=view.section!==3&&contentY-originY>80&&!app.searchOpen
    Keys.onReleased:event=>{event.accepted=false;if([Qt.Key_Up,Qt.Key_Down,Qt.Key_PageUp,Qt.Key_PageDown,Qt.Key_Home,Qt.Key_End].indexOf(event.key)>=0){view.positionViewAtIndex(view.currentIndex,ListView.Contain);Qt.callLater(function(){if(!view.topResetPending)app.headerCollapsed=view.section!==3&&view.contentY-view.originY>80&&!app.searchOpen})}}
    header:Column {
        readonly property bool courseMenuVisible:gradePicker.popup.visible
        x:16;width:view.width-32;spacing:10
        Item {id:gradeSlot;visible:view.section===4&&app.production;width:parent.width;height:visible?Math.max(48,gradeReports.height):0
            GlassComboBox {id:gradePicker;objectName:'gradeCourseFilter';parent:app.controlsLayer
                readonly property point origin:app.controlPosition(gradeSlot)
                x:origin.x;y:origin.y;visible:gradeSlot.visible&&view.visible&&!app.focusOpen&&origin.y>=app.controlPosition(view).y-1
                width:Math.min(gradeSlot.width-gradeReports.width-12,Math.max(160,implicitContentWidth+46)*Theme.textScale);height:40
                selectorMaterial:true;backdrop:app.controlsBackdrop
                model:app.production?backend.gradeCourses:[];currentIndex:Math.max(0,model.indexOf(view.gradeCourse));Accessible.name:I18n.t('Filter grades by subject')
                onActivated:{view.gradeCourse=currentText;view.requestTop()}
            }
            Capsule {id:gradeReports;objectName:'reportCardsButton';parent:app.controlsLayer
                readonly property point origin:app.controlPosition(gradeSlot)
                x:origin.x+gradeSlot.width-width;y:origin.y
                visible:gradeSlot.visible&&view.visible&&!app.focusOpen&&origin.y>=app.controlPosition(view).y-1
                text:I18n.t('Report cards');symbol:'file';onClicked:app.showReports()
            }
        }
        Row {visible:view.section===5&&!Theme.fancy;spacing:4
            Repeater {model:[{name:I18n.t('All'),kind:'all'},{name:I18n.t('Notes'),kind:'notes'},{name:I18n.t('Absences'),kind:'absences'}];Capsule {required property var modelData;text:modelData.name;selected:view.lvsKind===modelData.kind;onClicked:{view.lvsKind=modelData.kind;view.preview=({});view.requestTop()}}}
        }
        Label {textFormat:Text.PlainText;visible:view.section===5;text:app.production?I18n.t('This school year'):I18n.t('This school year · Synthetic workspace');color:Theme.secondary;padding:8}
        Capsule {visible:view.section===4&&app.production&&backend.features.selectedPeriod!=='';text:app.production?I18n.t('Period: ')+backend.features.selectedPeriod+I18n.t(' · Clear'):'';onClicked:backend.features.selectPeriod('')}
        Capsule {objectName:'markAllRead';visible:view.section===5;text:I18n.t('Mark all as read');onClicked:{if(app.production){backend.markRead('*');return}let next={};for(let i=0;i<8;i++)next['lvs-'+i]=true;view.readNotes=next}}
    }
    delegate:Column {
        id:entry;required property var modelData;width:view.width-32;spacing:0
        transform:Translate{x:16}
        Item {width:1;height:entry.modelData.first?14:0}
        RowLayout {width:parent.width;visible:entry.modelData.heading!==''
            Label {textFormat:Text.PlainText;text:entry.modelData.heading;color:Theme.text;font.pixelSize:(Theme.fancy?22:17)*Theme.textScale;font.bold:true;padding:8;Layout.fillWidth:true;wrapMode:Text.Wrap}
            Label {textFormat:Text.PlainText;text:entry.modelData.average||'';color:Theme.secondary;font.pixelSize:14*Theme.textScale;padding:8}
        }
        Item {
            objectName:'contentGroup';width:parent.width;height:groupRows.height
            Item {x:-16;y:entry.modelData.first?-16:0;width:parent.width+32;height:parent.height+(entry.modelData.first?16:0)+(entry.modelData.last?16:0);clip:true
                Surface {x:16;y:entry.modelData.first?16:-52;width:parent.width-32;height:groupRows.height+(entry.modelData.first?0:52)+(entry.modelData.last?0:52);tracking:view.contentY;refraction:24;continuous:true}
            }
            Column {id:groupRows;width:parent.width
                Repeater {model:entry.modelData.items
                    ItemDelegate {
                        id:card;objectName:'sectionRow';required property var modelData;required property int index
                        property bool lesson:view.section===2||view.section===3
                        property bool summary:modelData.kind==='summary'
                        property color scoreInk:view.section===4?ResultPalette.ink(modelData,Theme.dark):Theme.text
                        width:groupRows.width;height:Math.max(64*Theme.textScale,cardContent.implicitHeight+(Theme.fancy?28:20))
                        padding:14;leftPadding:16;rightPadding:16;hoverEnabled:true
                        Accessible.name:modelData.title+', '+modelData.meta+', '+modelData.extra+(modelData.unread?I18n.t(', unread'):'')+(modelData.square?', '+modelData.resultLabel:'')
                        background:Rectangle {
                            topLeftRadius:entry.modelData.first?(Theme.fancy?24:3):0;topRightRadius:topLeftRadius
                            bottomLeftRadius:entry.modelData.last?(Theme.fancy?24:3):0;bottomRightRadius:bottomLeftRadius
                            color:!Theme.fancy&&card.lesson?Theme.lesson:Theme.alpha(Theme.text,card.down?.09:card.hovered?.045:0)
                            Behavior on color {ColorAnimation {duration:Theme.motion&&!card.down?120:0}}
                            border.width:card.visualFocus?2:0;border.color:Theme.text}
                        contentItem:RowLayout {id:cardContent;spacing:12
                            Label {textFormat:Text.PlainText;visible:card.lesson;text:card.modelData.meta.split(' · ')[0].replace(' – ','\n')
                                Layout.preferredWidth:62*Theme.textScale;Layout.alignment:Qt.AlignTop;color:Theme.secondary;font.pixelSize:13*Theme.textScale;font.weight:Font.DemiBold}
                            Rectangle {visible:card.lesson;Layout.preferredWidth:4;Layout.fillHeight:true;radius:2;color:Theme.fancy?[Theme.red,Theme.blue,Theme.green][entry.modelData.rowIndex%3]:Theme.teal}
                            ColumnLayout {Layout.fillWidth:true;spacing:4
                                RowLayout {Layout.fillWidth:true
                                    ColumnLayout {Layout.fillWidth:true;Layout.minimumWidth:0;spacing:2
                                        Label {textFormat:Text.PlainText;text:card.summary?I18n.t('Weighted counting results'):card.modelData.title;Layout.fillWidth:true;wrapMode:Text.Wrap;color:card.summary?Theme.secondary:Theme.text;font.pixelSize:(card.summary?14:15)*Theme.textScale;font.weight:card.summary?Font.Medium:Font.DemiBold}
                                        Label {
                                            textFormat:Text.PlainText
                                            text:app.production && card.modelData.kind==='notes'?(backend.noteDetails[card.modelData.id]||{}).body||'':''
                                            visible:text.length>0;Layout.fillWidth:true;maximumLineCount:2
                                            wrapMode:Text.Wrap;elide:Text.ElideRight;color:Theme.text;font.pixelSize:14*Theme.textScale
                                        }
                                        Label {textFormat:Text.PlainText;visible:!card.lesson&&!card.summary;text:card.modelData.meta;color:Theme.secondary;font.pixelSize:13*Theme.textScale;Layout.fillWidth:true;wrapMode:Text.Wrap}
                                    }
                                    ColumnLayout {visible:view.section===4;Layout.maximumWidth:cardContent.width*(Theme.fancy?.4:.5);spacing:3
                                        Rectangle {id:resultSquare;objectName:'gradeSquare';visible:!!card.modelData.square;Layout.alignment:Qt.AlignRight;implicitWidth:28;implicitHeight:28;radius:8;color:card.modelData.square||'transparent'
                                            border.width:1;border.color:Theme.alpha(Theme.text,.12)
                                            GlassToolTip {requested:resultSquare.visible&&(card.hovered||card.visualFocus);text:card.modelData.resultLabel||''}
                                        }
                                        Label {objectName:'gradeScore';textFormat:Text.PlainText;visible:!card.modelData.square;text:card.summary?card.modelData.title:card.modelData.extra;Layout.fillWidth:true;wrapMode:Theme.fancy?Text.Wrap:Text.NoWrap;horizontalAlignment:Text.AlignRight;color:card.scoreInk;font.pixelSize:(card.summary?(Theme.fancy?28:21):17)*Theme.textScale;font.weight:Font.Bold}
                                        Label {objectName:'gradePercent';textFormat:Text.PlainText;visible:!!card.modelData.percentText;text:card.modelData.percentText||'';Layout.fillWidth:true;horizontalAlignment:Text.AlignRight;color:Theme.secondary;font.pixelSize:13*Theme.textScale}
                                    }
                                }
                                Label {textFormat:Text.PlainText;visible:card.lesson&&card.modelData.extra!==''&&!(card.modelData.assignments||[]).length;text:card.modelData.extra;color:Theme.text;font.pixelSize:14*Theme.textScale;Layout.fillWidth:true;wrapMode:Text.Wrap}
                                Label {textFormat:Text.PlainText;visible:card.lesson;text:card.lesson?card.modelData.meta.split(' · ').slice(1).join(' · '):card.modelData.meta;color:Theme.secondary;font.pixelSize:13*Theme.textScale;Layout.fillWidth:true;wrapMode:Text.Wrap}
                                Repeater {model:card.lesson?(card.modelData.assignments||[]):[]
                                    LessonAssignment {app:view.app;scrollOffset:view.contentY}
                                }
                            }
                        }
                        Rectangle {objectName:'unreadDot';visible:!!card.modelData.unread;anchors.right:parent.right;anchors.top:parent.top;anchors.margins:13;width:8;height:8;radius:4;color:'#df342e'}
                        Rectangle {visible:!entry.modelData.first;x:card.lesson?100*Theme.textScale:20;y:0;width:parent.width-x-18;height:1;color:Theme.alpha(Theme.text,.12)}
                        onClicked:{view.preview=modelData;if(!Theme.fancy&&view.section===4)return;if(app.production){app.openSection(modelData);return}let title=modelData.title,body=modelData.body,id=modelData.id,host=view;if(view.section===5){let next=Object.assign({},view.readNotes);next[id]=true;view.readNotes=next}host.detail(title,body)}
                    }
                }
            }
        }
        Item {width:1;height:entry.modelData.last?12:0}
    }
    Label {textFormat:Text.PlainText;visible:view.count===0;anchors.centerIn:parent;text:app.searchText?I18n.t('No matching items'):I18n.t('Nothing available yet');color:Theme.secondary;font.pixelSize:22}
}
