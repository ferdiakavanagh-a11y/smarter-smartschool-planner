import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Sheet {
    id:sheet
    required property var app
    property string collection:'missed'
    title:collection==='missed'?'Missed assignments':'Completed assignments'
    width:Math.min(760*Theme.textScale,parent.width-24)
    implicitHeight:Math.min(660*Theme.textScale,parent.height*.86)
    readonly property var entries:collection==='missed'?tasks.missedTasks:tasks.completedTasks
    ListModel {id:rows;dynamicRoles:true}
    function reconcile(){
        if(!rows)return
        if(list)list.rememberPositions()
        let wanted=sheet.entries,ids=new Set(wanted.map(task=>task.taskId))
        for(let i=rows.count-1;i>=0;i--)if(!ids.has(rows.get(i).taskId))rows.remove(i)
        for(let i=0;i<wanted.length;i++){
            let found=-1
            for(let j=i;j<rows.count;j++)if(rows.get(j).taskId===wanted[i].taskId){found=j;break}
            if(found<0)rows.insert(i,wanted[i])
            else {
                if(found!==i)rows.move(found,i,1)
                rows.set(i,wanted[i])
            }
        }
        if(list)Qt.callLater(list.restorePositions)
    }
    onEntriesChanged:reconcile()
    Component.onCompleted:reconcile()
    Label {Layout.fillWidth:true;textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.secondary
        text:sheet.entries.length?sheet.entries.length+(sheet.entries.length===1?' assignment':' assignments'):
             sheet.collection==='missed'?'All caught up. No missed assignments.':'No completed assignments yet.'}
    ListView {
        id:list;objectName:'collectionList';Layout.fillWidth:true
        Layout.preferredHeight:Math.max(120,sheet.scrollView.height-66)
        model:rows;clip:true;spacing:12;reuseItems:true;activeFocusOnTab:true
        property var reflowPositions:({})
        property bool reflowQueued:false
        function settleReflow(){
            reflowQueued=false;reflowPositions=({})
            for(let item of contentItem.children)if(typeof item.settleReflow==='function')item.settleReflow()
        }
        function rememberPositions(){
            if(reflowQueued)return
            reflowQueued=true
            let positions={}
            for(let item of contentItem.children)if(item.motionKey!==undefined&&!item.retiring)
                positions[item.motionKey]=item.mapToItem(list,0,0).y
            reflowPositions=positions
        }
        function restorePositions(){
            if(!reflowQueued)return
            reflowQueued=false;forceLayout()
            for(let item of contentItem.children)if(item.motionKey!==undefined&&!item.retiring&&reflowPositions[item.motionKey]!==undefined)
                item.reflowFrom(reflowPositions[item.motionKey])
            reflowPositions=({})
        }
        Connections {target:Theme;function onMotionChanged(){if(!Theme.motion)list.settleReflow()}}
        add:Transition {ParallelAnimation {
            NumberAnimation {property:'opacity';from:0;to:1;duration:Theme.motion?160:80;easing.type:Easing.OutCubic}
            NumberAnimation {property:'scale';from:Theme.motion?.98:1;to:1;duration:Theme.motion?220:0;easing.type:Easing.OutCubic}
        }}
        remove:Transition {enabled:list.count>0;ParallelAnimation {
            NumberAnimation {property:'opacity';to:0;duration:Theme.motion?180:80;easing.type:Easing.InCubic}
            NumberAnimation {property:'scale';to:Theme.motion?.98:1;duration:Theme.motion?220:0;easing.type:Easing.OutCubic}
        }}
        boundsBehavior:Flickable.StopAtBounds
        ScrollBar.vertical:ScrollBar {}
        SmoothScroll {view:list}
        Accessible.name:sheet.title
        delegate:Pane {
            id:entry;objectName:'collectionEntry-'+taskId;required property int index;required property string taskId;required property string title;required property string course;required property string kind;required property string note;required property string due;required property bool done;width:list.width;padding:16
            property bool retiring:false
            property bool pooled:false
            property string motionKey:'task:'+taskId
            property real reflowY:0
            function settleReflow(){rowMotion.stop();reflowY=0}
            function reflowFrom(previousY){rowMotion.stop();reflowY+=previousY-mapToItem(list,0,0).y;if(Theme.motion)rowMotion.start();else reflowY=0}
            transform:Translate {y:entry.reflowY}
            NumberAnimation {id:rowMotion;target:entry;property:'reflowY';to:0;duration:240;easing.type:Easing.OutCubic}
            enabled:!retiring&&!pooled&&index>=0
            opacity:pooled?0:1
            ListView.onRemove:{retiring=true;if(list.count===0){ListView.delayRemove=true;removal.start()}}
            ParallelAnimation {id:removal
                NumberAnimation {target:entry;property:'opacity';to:0;duration:Theme.motion?180:80;easing.type:Easing.InCubic}
                NumberAnimation {target:entry;property:'scale';to:Theme.motion?.98:1;duration:Theme.motion?220:0;easing.type:Easing.OutCubic}
                onFinished:entry.ListView.delayRemove=false
            }
            ListView.onPooled:{pooled=true;rowMotion.stop();reflowY=0;removal.stop();ListView.delayRemove=false}
            ListView.onReused:{rowMotion.stop();reflowY=0;removal.stop();ListView.delayRemove=false;retiring=false;opacity=Qt.binding(function(){return entry.pooled?0:1});scale=1;pooled=false}
            background:Surface {radius:16;refraction:28+8*(1-entry.scale)}
            contentItem:RowLayout {spacing:12
                TaskCheck {objectName:'collection-done-'+entry.taskId;Layout.alignment:Qt.AlignTop
                    checked:entry.done;Accessible.name:(checked?'Restore ':'Complete ')+entry.title
                    onClicked:{let id=entry.taskId,target=!entry.done,host=sheet.app;if(tasks.change(id,'done',target))host.notify(target?'Task completed':'Task restored');else checked=Qt.binding(function(){return entry.done})}}
                ColumnLayout {Layout.fillWidth:true;spacing:4
                    Label {Layout.fillWidth:true;textFormat:Text.PlainText;text:entry.course+' · '+entry.kind;wrapMode:Text.Wrap;color:Theme.secondary;font.pixelSize:12*Theme.textScale}
                    Label {Layout.fillWidth:true;textFormat:Text.PlainText;text:entry.title;wrapMode:Text.Wrap;color:Theme.text;font.weight:Font.DemiBold}
                    Label {Layout.fillWidth:true;textFormat:Text.PlainText;text:'Due '+Qt.formatDate(new Date(entry.due+'T12:00:00'),'ddd, d MMM yyyy');wrapMode:Text.Wrap;color:Theme.secondary;font.pixelSize:12*Theme.textScale}
                }
                Capsule {text:'Details';onClicked:sheet.app.showTask(entry.taskId,entry.title,entry.note)}
            }
        }
    }
    onAboutToShow:{account=app.production?backend.features.accountKey:'';Qt.callLater(list.positionViewAtBeginning)}
    Connections {target:sheet.app.production?backend.features:null
        function onChanged(){if(sheet.visible&&sheet.account!==backend.features.accountKey)sheet.close()}
    }
    property string account:''
}
