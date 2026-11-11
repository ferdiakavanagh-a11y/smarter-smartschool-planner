import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ColumnLayout {
    id:view
    required property var app
    property bool offlineOnly:false
    readonly property var service:app.production?backend.features:null
    readonly property var resources:service?service.resources:({})
    readonly property var periods:resources.periods||[]
    property bool resetPending:false
    function requestTop(){if(visible){scrollMotion.stop();list.cancelFlick();resetPending=true}}
    onVisibleChanged:if(visible)requestTop()
    property string reportYear:'All school years'
    readonly property var years:['All school years'].concat([...new Set((resources.reports||[]).map(r=>r.schoolYear).filter(Boolean))])
    onYearsChanged:if(years.indexOf(reportYear)<0)reportYear='All school years'
    readonly property var rows: {
        if(!visible)return []
        if(offlineOnly)return service?service.downloadedFiles:[]
        return (resources.reports||[]).filter(r=>!reportYear||reportYear==='All school years'||r.schoolYear===reportYear)
    }
    spacing:12
    RowLayout {Layout.fillWidth:true;visible:!view.offlineOnly
        Label {text:'Available from Smartschool';textFormat:Text.PlainText;color:Theme.secondary;Layout.fillWidth:true;wrapMode:Text.Wrap}
        Capsule {objectName:'refreshResources';text:service&&service.featureBusy?'Loading…':'Refresh';symbol:'retry';enabled:!!service&&!service.featureBusy;onClicked:service.loadResources()}
    }
    ListView {
        id:list;objectName:'resourceList';Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:12;bottomMargin:16
        opacity:view.resetPending?0:1
        model:view.rows;reuseItems:true;boundsBehavior:Flickable.StopAtBounds;activeFocusOnTab:true
        ScrollBar.vertical:ScrollBar {}
        SmoothScroll {id:scrollMotion;view:list}
        property real previousOriginY:0
        onOriginYChanged:{let wasTop=Math.abs(contentY-previousOriginY)<2;previousOriginY=originY;if(wasTop&&view.visible&&!view.resetPending&&!moving&&!scrollMotion.active&&!scrollMotion.glide.running)contentY=originY}
        Connections {target:view.app
            function onAfterAnimating(){if(view.resetPending&&view.visible&&list.height>0){list.forceLayout();list.positionViewAtBeginning();view.resetPending=false}}
        }
        header:Column {
            width:list.width;spacing:12
            Repeater {model:view.offlineOnly?[]:Object.keys(view.resources.errors||{}).filter(k=>k==='reports'||k==='periods')
                Label {required property var modelData;width:parent.width;text:(({reports:'Report cards',periods:'Academic periods',courses:'Courses',support:'School support',homepage:'School homepage'})[modelData]||'School section')+': '+view.resources.errors[modelData];textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.orange}
            }
            Pane {width:parent.width;visible:!view.offlineOnly;padding:14
                background:Surface {radius:18}
                contentItem:ColumnLayout {spacing:10
                    RowLayout {Layout.fillWidth:true
                        Label {text:'School year';textFormat:Text.PlainText;color:Theme.secondary;Layout.preferredWidth:92*Theme.textScale;font.pixelSize:12*Theme.textScale}
                        GlassComboBox {objectName:'reportYearFilter';Layout.fillWidth:true;model:view.years;currentIndex:Math.max(0,view.years.indexOf(view.reportYear));Accessible.name:'Filter report cards by school year';onActivated:{view.reportYear=currentText;view.requestTop()}}
                    }
                    RowLayout {Layout.fillWidth:true
                        Label {text:'Grade period';textFormat:Text.PlainText;color:Theme.secondary;Layout.preferredWidth:92*Theme.textScale;font.pixelSize:12*Theme.textScale}
                        GlassComboBox {objectName:'resourcePeriodFilter';Layout.fillWidth:true;model:['All periods'].concat(view.periods.map(p=>(p.name||'Period')+(p.schoolYear?' · '+p.schoolYear:'')));currentIndex:view.service?Math.max(0,view.periods.findIndex(p=>p.name===view.service.selectedPeriod)+1):0;Accessible.name:'Choose academic period';onActivated:if(view.service)view.service.selectPeriod(currentIndex?view.periods[currentIndex-1].name:'')}
                    }
                }
            }
            Label {visible:view.rows.length===0;width:parent.width;text:view.offlineOnly?'No offline files. Download a message attachment or report to keep a local copy.':'No matching information. Press Refresh to check school access and availability.';textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.secondary}
            Item {width:1;height:12}
        }
        delegate:Column {
            id:row;required property var modelData;width:list.width
            DetailCard {width:parent.width;visible:!view.offlineOnly;title:row.modelData.name||'Report card'
                Label {text:[row.modelData.date,row.modelData.className,row.modelData.schoolYear].filter(Boolean).join(' · ');textFormat:Text.PlainText;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.secondary}
                RowLayout {visible:!!row.modelData.downloadable
                    Capsule {text:'View report';enabled:!!view.service&&!view.service.featureBusy;onClicked:view.service.viewReport(String(row.modelData.id))}
                    Capsule {text:'Download report';enabled:!!view.service&&!view.service.featureBusy;onClicked:view.service.downloadAttachment('report',String(row.modelData.id))}
                }
            }
            Capsule {objectName:'offlineFileEntry';visible:view.offlineOnly;width:parent.width;text:row.modelData.name||'Downloaded file';onClicked:fileSheet.showFile(row.modelData)}
        }
    }
    OfflineFileSheet {id:fileSheet;parent:view.app.contentItem;service:view.service}
}
