import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ListView {
    id:view;objectName:'sectionList'
    required property var app
    property var readNotes: ({})
    property bool topResetPending:false
    property string gradeCourse:'All subjects'
    readonly property bool courseMenuVisible:headerItem?headerItem.courseMenuVisible:false
    function resetTop(){
        if(!visible||app.section<2||height<=0)return
        scrollMotion.stop();cancelFlick()
        if(headerItem)headerItem.forceLayout()
        forceLayout();positionViewAtBeginning();app.headerCollapsed=false
        if(app.production&&(app.section===2||app.section===3)&&!app.searchText.trim()){
            let today=Qt.formatDate(new Date(),'yyyy-MM-dd'),target=-1,lastDay=-1
            for(let i=0;i<model.length;i++)if(model[i].date&&(i===0||model[i].date!==model[i-1].date)){
                lastDay=i
                if(model[i].date>=today){target=i;break}
            }
            if(target<0)target=lastDay
            if(target>=0)positionViewAtIndex(target,ListView.Beginning)
        }
    }
    function requestTop(){topResetPending=true;scrollMotion.stop();cancelFlick();Qt.callLater(resetTop)}
    onVisibleChanged:if(visible&&app.section>=2)requestTop()
    onHeightChanged:if(topResetPending&&height>0)Qt.callLater(resetTop)
    function flatten(groups){
        let rows=[]
        for(let group of groups)for(let i=0;i<group.items.length;i++)
            rows.push({date:group.date||'',heading:i===0?group.heading:'',average:i===0?group.average||'':'',items:[group.items[i]],first:i===0,last:i===group.items.length-1,rowIndex:i})
        return rows
    }
    signal detail(string title,string body)
    Layout.leftMargin:-16;Layout.rightMargin:-16
    clip:false;spacing:0;bottomMargin:120*Theme.textScale;reuseItems:true;cacheBuffer:180
    displayMarginBeginning:220*Theme.textScale
    model: {
        let revision=app.fixtureRevision
        if(app.production)return flatten(backend.groups(app.section,app.searchText,app.section===4?gradeCourse:'All subjects'))
        if(app.datasetIndex===0)return []
        let rows=[]
        let courses=['Mathematics','Nederlands','Sciences','History','Français','日本語 & cultuur']
        if(app.section===2||app.section===3){
            for(let i=0;i<18;i++)rows.push({id:'lesson-'+i,heading:i%6===0?['Monday, 26 October','Tuesday, 27 October','Wednesday, 28 October'][Math.floor(i/6)]:'',title:courses[i%6],meta:(8+Math.floor(i%6))+':30 – '+(9+Math.floor(i%6))+':20 · Room '+(101+i%6)+' · Demo teacher',body:'Lesson overview\n\nSynthetic study material for '+courses[i%6]+'.\n\nAssignment: prepare one question for our next lesson.',extra:i%3===0?'Assignment · prepare one question':''})
        }else if(app.section===4){
            rows.push({id:'average',heading:'Overall average',title:'80%',meta:'Weighted by available points · synthetic results',body:'128 / 160 counting points. This demonstration includes counting and noncounting results.',extra:'Saved example · refresh unavailable'})
            for(let i=0;i<12;i++)rows.push({id:'grade-'+i,heading:i%2===0?courses[Math.floor(i/2)]:'',title:i%2===0?'Chapter review':'Class participation',meta:'23 Oct · '+(i%3===0?'Doesn’t count':'Counts toward total'),body:'Course: '+courses[Math.floor(i/2)]+'\n\nFeedback: explain your reasoning and check the final step.\n\nSynthetic result; no account connected.',extra:[ '8 / 10','14 / 20','18 / 20'][i%3]})
        }else if(app.section===5){
            for(let i=0;i<8;i++)rows.push({id:'lvs-'+i,heading:i===0?'Notes':i===5?'Absences':'',title:i<5?['Study progress','A note about participation','Project feedback','Planning support','Next steps'][i-0]:'Absence · authorised',meta:'23 Oct · '+(i<5?'Demo tutor':'Morning · A'),body:i<5?'Public synthetic note\n\nKeep using your planner to break larger assignments into small steps.\n\nZoë · 日本語 · نور':'Synthetic authorised absence. No personal school record.',extra:'',unread:!readNotes['lvs-'+i]})
        }
        let q=app.searchText.toLocaleLowerCase()
        let groups=[],heading='',lastHeading=''
        for(let row of rows){
            if(row.heading)heading=row.heading
            if(q&&!(row.title+' '+row.meta+' '+row.body).toLocaleLowerCase().includes(q))continue
            if(app.section===4||!groups.length||heading!==lastHeading){
                groups.push({heading:heading!==lastHeading?heading:'',items:[]})
            }
            groups[groups.length-1].items.push(row)
            lastHeading=heading
        }
        return flatten(groups)
    }
    ScrollBar.vertical:ScrollBar{}
    SmoothScroll {id:scrollMotion; view:view }
    Connections {target:app
        function onSectionChanged(){if(app.section>=2)view.requestTop()}
        function onSearchTextChanged(){if(view.visible)view.requestTop()}
        function onFixtureRevisionChanged(){view.readNotes={};if(app.production&&backend.gradeCourses.indexOf(view.gradeCourse)<0)view.gradeCourse='All subjects';if(view.visible&&(app.section===2||app.section===3))view.requestTop()}
        function onFrameSwapped(){if(view.topResetPending&&view.visible&&view.height>0){view.resetTop();view.topResetPending=false}}
    }
    onContentYChanged:if(view.visible&&!topResetPending)app.headerCollapsed=contentY-originY>80&&!app.searchOpen
    header:Column {
        readonly property bool courseMenuVisible:gradePicker.popup.visible
        x:16;width:view.width-32;spacing:10
        Item {id:gradeSlot;visible:app.section===4&&app.production;width:parent.width;height:visible?48:0
            GlassComboBox {id:gradePicker;objectName:'gradeCourseFilter';parent:app.controlsLayer
                readonly property point origin:app.controlPosition(gradeSlot)
                x:origin.x;y:origin.y;visible:gradeSlot.visible&&view.visible&&!app.focusOpen
                width:Math.min(gradeSlot.width,Math.max(160,implicitContentWidth+46)*Theme.textScale);height:40
                selectorMaterial:true;backdrop:app.controlsBackdrop
                model:app.production?backend.gradeCourses:[];currentIndex:Math.max(0,model.indexOf(view.gradeCourse));Accessible.name:'Filter grades by subject'
                onActivated:{view.gradeCourse=currentText;view.requestTop()}
            }
        }
        Label {textFormat:Text.PlainText;visible:app.section===5;text:app.production?'This school year':'This school year · Synthetic workspace';color:Theme.secondary;padding:8}
        Capsule {objectName:'markAllRead';visible:app.section===5;text:'Mark all as read';onClicked:{if(app.production){backend.markRead('*');return}let next={};for(let i=0;i<8;i++)next['lvs-'+i]=true;view.readNotes=next}}
    }
    delegate:Column {
        id:entry;required property var modelData;width:view.width-32;spacing:0
        transform:Translate{x:16}
        Item {width:1;height:entry.modelData.first?12:0}
        RowLayout {width:parent.width;visible:entry.modelData.heading!==''
            Label {textFormat:Text.PlainText;text:entry.modelData.heading;color:Theme.text;font.pixelSize:22*Theme.textScale;font.bold:true;padding:8;Layout.fillWidth:true;wrapMode:Text.Wrap}
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
                        property bool lesson:app.section===2||app.section===3
                        property bool summary:modelData.kind==='summary'
                        property color scoreInk:modelData.tone==='red'?Theme.red:modelData.tone==='orange'?Theme.orange:modelData.tone==='green'?Theme.green:Theme.text
                        width:groupRows.width;height:Math.max(82*Theme.textScale,cardContent.implicitHeight+30)
                        padding:16;leftPadding:lesson?22:20;hoverEnabled:true
                        Accessible.name:modelData.title+', '+modelData.meta+', '+modelData.extra+(modelData.unread?', unread':'')+(modelData.square?', '+modelData.resultLabel:'')
                        background:Rectangle {
                            topLeftRadius:entry.modelData.first?32:0;topRightRadius:topLeftRadius
                            bottomLeftRadius:entry.modelData.last?32:0;bottomRightRadius:bottomLeftRadius
                            color:Theme.alpha(Theme.text,card.down?.09:card.hovered?.045:0)
                            Behavior on color {ColorAnimation {duration:Theme.motion&&!card.down?120:0}}
                            border.width:card.visualFocus?2:0;border.color:Theme.text}
                        contentItem:RowLayout {id:cardContent;spacing:16
                            Label {textFormat:Text.PlainText;visible:card.lesson;text:card.modelData.meta.split(' · ')[0].replace(' – ','\n')
                                Layout.preferredWidth:62*Theme.textScale;Layout.alignment:Qt.AlignTop;color:Theme.secondary;font.pixelSize:13*Theme.textScale;font.weight:Font.DemiBold}
                            Rectangle {visible:card.lesson;Layout.preferredWidth:4;Layout.fillHeight:true;radius:2;color:[Theme.red,Theme.blue,Theme.green][entry.modelData.rowIndex%3]}
                            ColumnLayout {Layout.fillWidth:true;spacing:6
                                RowLayout {Layout.fillWidth:true
                                    Label {textFormat:Text.PlainText;text:card.summary?'Weighted counting results':card.modelData.title;Layout.fillWidth:true;Layout.minimumWidth:0;wrapMode:Text.Wrap;color:card.summary?Theme.secondary:Theme.text;font.pixelSize:(card.summary?14:16)*Theme.textScale;font.weight:card.summary?Font.Medium:Font.DemiBold}
                                    ColumnLayout {visible:app.section===4;Layout.maximumWidth:cardContent.width*.4;spacing:3
                                        Rectangle {id:resultSquare;objectName:'gradeSquare';visible:!!card.modelData.square;Layout.alignment:Qt.AlignRight;implicitWidth:28;implicitHeight:28;radius:8;color:card.modelData.square||'transparent'
                                            border.width:1;border.color:Theme.alpha(Theme.text,.12)
                                            GlassToolTip {requested:resultSquare.visible&&(card.hovered||card.visualFocus);text:card.modelData.resultLabel||''}
                                        }
                                        Label {objectName:'gradeScore';textFormat:Text.PlainText;visible:!card.modelData.square;text:card.summary?card.modelData.title:card.modelData.extra;Layout.fillWidth:true;wrapMode:Text.Wrap;horizontalAlignment:Text.AlignRight;color:card.scoreInk;font.pixelSize:(card.summary?30:18)*Theme.textScale;font.weight:Font.Bold}
                                        Label {objectName:'gradePercent';textFormat:Text.PlainText;visible:!!card.modelData.percentText;text:card.modelData.percentText||'';Layout.fillWidth:true;horizontalAlignment:Text.AlignRight;color:Theme.secondary;font.pixelSize:13*Theme.textScale}
                                    }
                                }
                                Label {textFormat:Text.PlainText;visible:card.lesson&&card.modelData.extra!==''&&!(card.modelData.assignments||[]).length;text:card.modelData.extra;color:Theme.text;font.pixelSize:14*Theme.textScale;Layout.fillWidth:true;wrapMode:Text.Wrap}
                                Label {textFormat:Text.PlainText;visible:!card.summary;text:card.lesson?card.modelData.meta.split(' · ').slice(1).join(' · '):card.modelData.meta;color:Theme.secondary;font.pixelSize:13*Theme.textScale;Layout.fillWidth:true;wrapMode:Text.Wrap}
                                Repeater {model:card.lesson?(card.modelData.assignments||[]):[]
                                    SelectorLens {id:assignment;objectName:'lessonAssignment';required property var modelData;Layout.fillWidth:true;implicitHeight:assignmentRow.implicitHeight+20;radius:16;backdrop:app.sceneBackdrop;tracking:view.contentY
                                        RowLayout {id:assignmentRow;anchors.fill:parent;anchors.margins:10;spacing:8
                                            TaskCheck {id:lessonCheck;objectName:'lesson-done-'+assignment.modelData.id;Layout.alignment:Qt.AlignTop;enabled:assignment.modelData.editable;checked:tasks.completedIds.indexOf(assignment.modelData.id)>=0;Accessible.name:(checked?'Restore ':'Complete ')+assignment.modelData.title
                                                onClicked:{let id=assignment.modelData.id,done=checked,host=app;if(tasks.change(id,'done',done))host.notify(done?'Task completed':'Task restored');else checked=Qt.binding(function(){return tasks.completedIds.indexOf(assignment.modelData.id)>=0})}
                                            }
                                            ColumnLayout {Layout.fillWidth:true;spacing:4
                                                Label {textFormat:Text.PlainText;text:assignment.modelData.title;font.pixelSize:14*Theme.textScale;font.weight:Font.DemiBold;font.strikeout:lessonCheck.checked;color:Theme.text;Layout.fillWidth:true;wrapMode:Text.Wrap}
                                                Label {textFormat:Text.PlainText;text:assignment.modelData.kind+(assignment.modelData.due?' · due '+assignment.modelData.due:'');font.pixelSize:12*Theme.textScale;color:Theme.secondary;Layout.fillWidth:true;wrapMode:Text.Wrap}
                                                TapHandler {enabled:assignment.modelData.editable;onTapped:{let item=assignment.modelData;app.showTask(item.id,item.title,tasks.taskNote(item.id))}}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        Rectangle {objectName:'unreadDot';visible:!!card.modelData.unread;anchors.right:parent.right;anchors.top:parent.top;anchors.margins:13;width:8;height:8;radius:4;color:'#df342e'}
                        Rectangle {visible:!entry.modelData.first;x:card.lesson?100*Theme.textScale:20;y:0;width:parent.width-x-18;height:1;color:Theme.alpha(Theme.text,.12)}
                        onClicked:{if(app.production){app.openSection(modelData);return}let title=modelData.title,body=modelData.body,id=modelData.id,host=view;if(app.section===5){let next=Object.assign({},view.readNotes);next[id]=true;view.readNotes=next}host.detail(title,body)}
                    }
                }
            }
        }
        Item {width:1;height:entry.modelData.last?12:0}
    }
    Label {textFormat:Text.PlainText;visible:view.count===0;anchors.centerIn:parent;text:app.searchText?'No matching items':'Nothing available yet';color:Theme.secondary;font.pixelSize:22}
}
