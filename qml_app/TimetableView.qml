import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ColumnLayout {
    id: calendar;objectName:"timetableView"
    required property var app
    property bool listMode: false
    property int weekOffset: 0
    property int dayCount:7
    property bool assignmentsOnly:false
    property date currentTime:new Date()
    Timer {interval:60000;running:calendar.visible;repeat:true;onTriggered:calendar.currentTime=new Date()}
    property string query:''
    property int revision:0
    onVisibleChanged:if(visible)query=app.searchText
    Connections {target:app;function onSearchTextChanged(){if(calendar.visible)calendar.query=app.searchText}}
    Connections {target:app.production?backend:null;function onGroupsChanged(section){if(section<0||section===3)calendar.revision++}}
    readonly property var days: {let r=revision;return app.production?backend.groups(3,query,'All subjects'):[]}
    readonly property var baseDate: {
        let today=Qt.formatDate(new Date(),'yyyy-MM-dd'),chosen=today
        if(days.length){chosen=days[days.length-1].date;for(let day of days)if(day.date>=today){chosen=day.date;break}}
        let d=new Date(chosen+'T12:00:00');d.setDate(d.getDate()-(d.getDay()+6)%7);return d
    }
    readonly property var dates: {let result=[];for(let i=0;i<dayCount;i++){let d=new Date(baseDate);d.setDate(d.getDate()+weekOffset*7+i);result.push(Qt.formatDate(d,'yyyy-MM-dd'))}return result}
    readonly property var visibleDays: dates.map(date=>days.find(day=>day.date===date)||{date:date,items:[]})
    readonly property var upcoming: {let result=[];for(let day of visibleDays)for(let lesson of day.items)for(let task of lesson.assignments||[])result.push({day:day.date,task:task,meta:lesson.meta,course:lesson.title});return result}
    function assignmentFlags(lesson){
        let seen={},rows=[]
        for(let task of lesson.assignments||[])if(task.id&&!seen[task.id]){seen[task.id]=true;rows.push(task)}
        return rows
    }
    function flagLabel(task){
        let kind=String(task.kind||'').trim(),key=kind.toLocaleLowerCase()
        if(key==='productevaluatie')return 'PE'
        if(key==='oefenevaluatie')return 'OE'
        if(key==='werktijd')return 'WT'
        if(key==='meebrengen')return 'ME'
        if(key==='voorbereiding')return 'VO'
        if(key==='toets'||key==='test')return 'T'
        if(key==='taak'||key==='task'||key==='taak/opdracht')return 'TA'
        return kind?kind.slice(0,3).toLocaleUpperCase():'T'
    }
    function openAssignment(task,lesson){
        if(task.editable)app.showTask(task.id,task.title,tasks.taskNote(task.id))
        else app.openSection(lesson)
    }
    function minutes(value){let match=/^(\d{1,2}):(\d{2})$/.exec(value.trim());return match&&Number(match[1])<24&&Number(match[2])<60?Number(match[1])*60+Number(match[2]):-1}
    function events(day){
        let rows=[]
        for(let lesson of day.items){if(assignmentsOnly&&!(lesson.assignments||[]).length)continue;if(lesson.kind==='empty')continue;let times=lesson.meta.split(' · ')[0].split(' – '),start=minutes(times[0]||''),end=minutes(times[1]||'');if(start<0||end<=start)continue;rows.push({lesson:lesson,start:start,end:end,lane:0,lanes:1})}
        rows.sort((a,b)=>a.start-b.start)
        let cluster=[],clusterEnd=-1
        function finish(){
            let ends=[]
            for(let item of cluster){let lane=ends.findIndex(end=>end<=item.start);if(lane<0)lane=ends.length;item.lane=lane;ends[lane]=item.end}
            for(let item of cluster)item.lanes=ends.length
            cluster=[]
        }
        for(let item of rows){if(cluster.length&&item.start>=clusterEnd)finish();if(!cluster.length)clusterEnd=item.end;cluster.push(item);clusterEnd=Math.max(clusterEnd,item.end)}
        finish()
        return rows
    }
    readonly property int startHour: {let hour=0;for(let day of visibleDays)for(let event of events(day))hour=Math.min(hour,Math.floor(event.start/60));return hour}
    readonly property int endHour: {let hour=24;for(let day of visibleDays)for(let event of events(day))hour=Math.max(hour,Math.ceil(event.end/60));return hour}
    readonly property real hourHeight: 84*Theme.textScale
    property real scrollHourHeight:84
    onHourHeightChanged:{if(scrollHourHeight>0&&gridScroll&&gridScroll.contentItem)gridScroll.contentItem.contentY=gridScroll.contentItem.contentY*hourHeight/scrollHourHeight;scrollHourHeight=hourHeight}
    spacing:6
    Flow {Layout.fillWidth:true;Layout.preferredHeight:childrenRect.height;Layout.leftMargin:14;Layout.rightMargin:12;Layout.topMargin:10;Layout.bottomMargin:8;spacing:6
        Rectangle {implicitWidth:30;implicitHeight:30;radius:15;color:Theme.lesson;Label {anchors.centerIn:parent;text:"SP";color:Theme.teal;font.bold:true}}
        Label {text:I18n.t("Mijn planner");font.pixelSize:22*Theme.textScale;color:Theme.secondary;Layout.rightMargin:8}
        Capsule {text:I18n.t('Previous week');iconOnly:true;quiet:false;symbol:'chevronLeft';onClicked:calendar.weekOffset--}
        Capsule {text:I18n.t('Vandaag');onClicked:calendar.weekOffset=0}
        Capsule {text:I18n.t('Next week');iconOnly:true;quiet:false;symbol:'chevronRight';onClicked:calendar.weekOffset++}
        Capsule {id:dateRange;width:230*Theme.textScale;text:I18n.locale.toString(new Date(calendar.dates[0]+'T12:00:00'),'d MMM')+' – '+I18n.locale.toString(new Date(calendar.dates[calendar.dates.length-1]+'T12:00:00'),'d MMM yyyy')+' ▾';onClicked:weekChooser.open()
            PlannerMenu {id:weekChooser;objectName:'plannerWeekMenu';y:dateRange.height;Repeater {model:17;PlannerMenuItem {required property int index;text:(index-8===0?I18n.t('Deze week · '):'')+I18n.locale.toString(new Date(calendar.baseDate.getTime()+(index-8)*7*86400000),'d MMM yyyy');onTriggered:calendar.weekOffset=index-8}}}
        }
        TextField {width:Math.max(120,Math.min(200,calendar.width*.16));implicitHeight:28*Theme.textScale;text:calendar.app.searchText;onTextEdited:calendar.app.searchText=text;placeholderText:I18n.t('Zoeken in mijn planner…');Accessible.name:I18n.t('Zoeken in mijn planner');color:Theme.text;background:Rectangle {color:Theme.elevated;border.color:Theme.separator;radius:2}}
        GlassComboBox {model:[I18n.t('Alles tonen'),I18n.t('Met opdrachten')];currentIndex:calendar.assignmentsOnly?1:0;Accessible.name:I18n.t('Zichtbaarheid lessen');onActivated:calendar.assignmentsOnly=currentIndex===1}
        GlassComboBox {model:[I18n.t('7 dagen'),I18n.t('5 dagen'),I18n.t('1 dag')];currentIndex:[7,5,1].indexOf(calendar.dayCount);Accessible.name:I18n.t('Aantal dagen');onActivated:calendar.dayCount=[7,5,1][currentIndex]}
        Capsule {objectName:'timetableListToggle';text:calendar.listMode?I18n.t('Weekoverzicht'):I18n.t('Lessenlijst');onClicked:calendar.listMode=!calendar.listMode}
    }
    RowLayout {Layout.fillWidth:true;Layout.fillHeight:true;spacing:0;visible:!calendar.listMode
        ScrollView {id:gridScroll;objectName:'timetable';
            Component.onCompleted:Qt.callLater(function(){gridScroll.contentItem.contentY=8*calendar.hourHeight})
            Layout.fillWidth:true;Layout.fillHeight:true;clip:true
            contentWidth:Math.max(availableWidth,(calendar.width<950?650:0)*Theme.textScale);contentHeight:grid.implicitHeight
            Item {id:grid;width:gridScroll.contentWidth;implicitHeight:42*Theme.textScale+(calendar.endHour-calendar.startHour)*calendar.hourHeight
                Rectangle {anchors.fill:parent;color:Theme.elevated;border.color:Theme.separator}
                readonly property real rail:48*Theme.textScale
                readonly property real dayWidth:(width-rail)/calendar.dayCount
                Row {x:grid.rail;y:gridScroll.contentItem.contentY;z:6;height:42*Theme.textScale
                    Repeater {model:calendar.dates
                        Rectangle {required property string modelData;width:grid.dayWidth;height:parent.height;color:modelData===Qt.formatDate(new Date(),'yyyy-MM-dd')?Theme.calendarToday:Theme.elevated;border.color:Theme.separator
                            Label {anchors.centerIn:parent;text:I18n.locale.toString(new Date(parent.modelData+'T12:00:00'),'ddd d MMM');color:Theme.text;font.pixelSize:12*Theme.textScale;font.bold:true}
                        }
                    }
                }
                Repeater {model:calendar.endHour-calendar.startHour
                    Item {required property int index;y:42*Theme.textScale+index*calendar.hourHeight;width:grid.width;height:calendar.hourHeight
                        Label {x:4;y:4;text:(calendar.startHour+parent.index).toString().padStart(2,'0')+':00';color:Theme.secondary;font.pixelSize:11*Theme.textScale}
                        Rectangle {x:grid.rail;width:parent.width-x;height:1;color:Theme.gridLine}
                        Rectangle {x:grid.rail;y:parent.height/2;width:parent.width-x;height:1;color:Theme.gridLine}
                    }
                }
                Repeater {model:calendar.visibleDays
                    Item {id:dayColumn;required property var modelData;required property int index;x:grid.rail+index*grid.dayWidth;y:42*Theme.textScale;width:grid.dayWidth;height:grid.height-y
                        Rectangle {width:1;height:parent.height;color:Theme.gridLine}
                        Rectangle {objectName:'currentTimeLine';visible:dayColumn.modelData.date===Qt.formatDate(calendar.currentTime,'yyyy-MM-dd');x:0;y:(calendar.currentTime.getHours()+calendar.currentTime.getMinutes()/60-calendar.startHour)*calendar.hourHeight;width:parent.width;height:2;color:Theme.red;z:4
                            Rectangle {x:-3;y:-2;width:6;height:6;radius:3;color:Theme.red}
                        }
                        Repeater {model:calendar.events(dayColumn.modelData)
                            Button {id:lesson;required property var modelData
                                x:3+modelData.lane*(dayColumn.width-6)/modelData.lanes;y:(modelData.start-calendar.startHour*60)/60*calendar.hourHeight+2
                                readonly property real laneWidth:(dayColumn.width-6)/modelData.lanes-2
                                readonly property bool stackedFlag:flags.length>0 && laneWidth<110*Theme.textScale && height>=46*Theme.textScale
                                width:Math.max(10,laneWidth-(flags.length&&!stackedFlag?flagWidth+3*Theme.textScale:0));height:Math.max(36*Theme.textScale,(modelData.end-modelData.start)/60*calendar.hourHeight-4)
                                padding:6;clip:false;hoverEnabled:true
                                Accessible.name:modelData.lesson.title+', '+modelData.lesson.meta+I18n.t('. Open lesson details')
                                background:Rectangle {radius:3;color:lesson.down?Qt.tint(Theme.lesson,Theme.alpha(Theme.blue,.24)):lesson.hovered?Theme.selection:Theme.lesson;border.color:lesson.visualFocus?Theme.text:'transparent';border.width:lesson.visualFocus?2:0}
                                readonly property var flags:calendar.assignmentFlags(modelData.lesson)
                                readonly property real flagWidth:Math.min(24*Theme.textScale,((dayColumn.width-6)/modelData.lanes-2)*.4)
                                contentItem:Item {
                                    Column {anchors.fill:parent;anchors.bottomMargin:lesson.stackedFlag?22*Theme.textScale:0;clip:true;spacing:2
                                        Label {width:parent.width;text:lesson.modelData.lesson.title;textFormat:Text.PlainText;color:Theme.text;font.pixelSize:12*Theme.textScale;font.bold:true;elide:Text.ElideRight}
                                        Label {width:parent.width;text:lesson.modelData.lesson.meta;textFormat:Text.PlainText;color:Theme.text;font.pixelSize:10*Theme.textScale;wrapMode:Text.Wrap;maximumLineCount:3;elide:Text.ElideRight}
                                    }
                                }
                                Column {id:flagRow;x:lesson.stackedFlag?3:lesson.width+3*Theme.textScale;y:lesson.stackedFlag?lesson.height-22*Theme.textScale:0;width:lesson.flagWidth;spacing:3*Theme.textScale;visible:lesson.flags.length>0
                                    readonly property int capacity:lesson.stackedFlag?1:Math.max(1,Math.min(2,Math.floor(lesson.height/(22*Theme.textScale+spacing))))
                                    readonly property var displayed:lesson.flags.length<=capacity?lesson.flags:lesson.flags.slice(0,capacity-1).concat([{overflow:true,count:lesson.flags.length-capacity+1}])
                                    Repeater {model:flagRow.displayed
                                        Button {id:flag;objectName:'plannerAssignmentFlag';required property var modelData
                                            width:flagRow.width;height:22*Theme.textScale;padding:0;hoverEnabled:true
                                            Accessible.name:modelData.overflow?I18n.p('All lesson assignments','Alle opdrachten voor deze les'):I18n.p('Open assignment: ','Open opdracht: ')+modelData.title
                                            background:Rectangle {radius:5;color:flag.down?Theme.calendarToday:flag.hovered?Theme.selection:Theme.lesson;border.width:flag.visualFocus?2:0;border.color:Theme.text}
                                            contentItem:Label {text:flag.modelData.overflow?'+'+flag.modelData.count:calendar.flagLabel(flag.modelData);textFormat:Text.PlainText;color:Theme.text;font.bold:true;font.pixelSize:10*Theme.textScale;horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter;elide:Text.ElideRight}
                                            onClicked:if(modelData.overflow)calendar.app.openSection(lesson.modelData.lesson);else calendar.openAssignment(modelData,lesson.modelData.lesson)
                                            GlassToolTip {requested:flag.hovered||flag.visualFocus;text:flag.modelData.overflow?lesson.flags.map(task=>task.title).join('\n'):flag.modelData.title}
                                        }
                                    }
                                }
                                onClicked:calendar.app.openSection(modelData.lesson)
                                GlassToolTip {requested:lesson.hovered||lesson.visualFocus;text:lesson.modelData.lesson.title+'\n'+lesson.modelData.lesson.meta+'\n'+lesson.modelData.lesson.extra}
                            }
                        }
                    }
                }
            }
        }
        Rectangle {visible:calendar.width>1050;Layout.preferredWidth:calendar.width*.22;Layout.maximumWidth:420*Theme.textScale;Layout.fillHeight:true;color:Theme.elevated;border.color:Theme.separator
            ScrollView {id:upcomingScroll;anchors.fill:parent;anchors.margins:12;contentWidth:availableWidth;clip:true
                ColumnLayout {width:upcomingScroll.availableWidth;spacing:10
                    Label {text:I18n.t('Eigen to-do’s');color:Theme.text;font.bold:true;font.pixelSize:13*Theme.textScale;Layout.fillWidth:true;wrapMode:Text.Wrap}
                    Label {visible:calendar.upcoming.length===0;text:I18n.t('No assignments in this week. Lesson details and files remain available in the grid or lesson list.');color:Theme.secondary;Layout.fillWidth:true;wrapMode:Text.Wrap}
                    Repeater {model:calendar.upcoming
                        ColumnLayout {required property var modelData;required property int index;Layout.fillWidth:true;spacing:4
                            Label {visible:parent.index===0||calendar.upcoming[parent.index-1].day!==parent.modelData.day;text:I18n.locale.toString(new Date(parent.modelData.day+'T12:00:00'),'dddd d MMMM');color:Theme.text;font.pixelSize:12*Theme.textScale;font.bold:true;Layout.topMargin:12}
                            RowLayout {Layout.fillWidth:true;spacing:8
                                Rectangle {implicitWidth:32;implicitHeight:32;color:Theme.lesson;radius:2
                                    Label {anchors.centerIn:parent;text:(parent.parent.parent.modelData.task.kind||'T').slice(0,2).toUpperCase();color:Theme.teal;font.bold:true;font.pixelSize:11}
                                }
                                ColumnLayout {Layout.fillWidth:true;spacing:2
                                    Label {text:parent.parent.parent.modelData.task.title;textFormat:Text.PlainText;color:Theme.text;Layout.fillWidth:true;wrapMode:Text.Wrap;font.pixelSize:12*Theme.textScale}
                                    Label {text:parent.parent.parent.modelData.meta+' · '+parent.parent.parent.modelData.course;textFormat:Text.PlainText;color:Theme.secondary;font.pixelSize:10*Theme.textScale;Layout.fillWidth:true;elide:Text.ElideRight}
                                    TapHandler {enabled:parent.parent.parent.modelData.task.editable;onTapped:{let task=parent.parent.parent.modelData.task;calendar.app.showTask(task.id,task.title,tasks.taskNote(task.id))}}
                                }
                                TaskCheck {markSize:15;implicitWidth:20;implicitHeight:24;checked:tasks.completedIds.indexOf(parent.parent.modelData.task.id)>=0;enabled:parent.parent.modelData.task.editable;Accessible.name:I18n.t('Voltooien ')+parent.parent.modelData.task.title;onClicked:{let task=parent.parent.modelData.task;if(tasks.change(task.id,'done',checked))calendar.app.notify(checked?I18n.t('Task completed'):I18n.t('Task restored'));else checked=Qt.binding(function(){return tasks.completedIds.indexOf(task.id)>=0})}}
                            }
                        }
                    }
                    Label {text:I18n.t('Lessen zonder uur blijven beschikbaar in de lessenlijst.');color:Theme.secondary;Layout.fillWidth:true;wrapMode:Text.Wrap;font.pixelSize:12*Theme.textScale}
                }
            }
        }
    }
    SectionsView {app:calendar.app;section:3;visible:calendar.listMode;clip:true;Layout.fillWidth:true;Layout.fillHeight:true}
}
