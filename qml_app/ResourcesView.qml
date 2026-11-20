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
    function requestTop(){if(visible){scrollMotion.stop();list.cancelFlick();resetPending=true;Qt.callLater(function(){if(view.visible){list.forceLayout();list.positionViewAtBeginning()}view.resetPending=false})}}
    onVisibleChanged:if(visible)requestTop()
    property string reportYear:'All school years'
    readonly property var years:['All school years'].concat([...new Set((resources.reports||[]).map(r=>r.schoolYear).filter(Boolean))])
    onYearsChanged:if(years.indexOf(reportYear)<0)reportYear='All school years'
    readonly property var rows: {
        if(offlineOnly)return service?service.downloadedFiles:[]
        return (resources.reports||[]).filter(r=>!reportYear||reportYear==='All school years'||r.schoolYear===reportYear).slice().sort((a,b)=>String(b.schoolYear||'').localeCompare(String(a.schoolYear||''))||String(b.date||'').localeCompare(String(a.date||'')))
    }
    spacing:Theme.smartschool?4:12
    RowLayout {Layout.fillWidth:true;visible:!view.offlineOnly
        Label {text:Theme.smartschool?I18n.t('Rapporten'):I18n.t('Available from Smartschool');textFormat:Text.PlainText;color:Theme.secondary;Layout.fillWidth:!Theme.smartschool;wrapMode:Text.Wrap;font.pixelSize:(Theme.smartschool?20:14)*Theme.textScale;Layout.rightMargin:Theme.smartschool?12:0}
        GlassComboBox {visible:Theme.smartschool;objectName:Theme.smartschool?'reportYearFilter':'compactReportYearFilter';Layout.fillWidth:true;Layout.preferredWidth:180;Layout.maximumWidth:240;model:view.years.map(y=>y==='All school years'?I18n.t('Alle schooljaren'):y);currentIndex:Math.max(0,view.years.indexOf(view.reportYear));Accessible.name:I18n.t('Rapporten op schooljaar filteren');onActivated:{view.reportYear=view.years[currentIndex];view.requestTop()}}
        GlassComboBox {visible:Theme.smartschool;objectName:Theme.smartschool?'resourcePeriodFilter':'compactResourcePeriodFilter';Layout.fillWidth:true;Layout.preferredWidth:180;Layout.maximumWidth:240;model:[I18n.t('Alle periodes')].concat(view.periods.map(p=>(p.name||I18n.t('Periode'))+(p.schoolYear?' · '+p.schoolYear:'')));currentIndex:view.service?Math.max(0,view.periods.findIndex(p=>p.name===view.service.selectedPeriod)+1):0;Accessible.name:I18n.t('Schoolperiode kiezen');onActivated:if(view.service)view.service.selectPeriod(currentIndex?view.periods[currentIndex-1].name:'')}
        Item {visible:Theme.smartschool;Layout.fillWidth:true}
        Capsule {objectName:'refreshResources';text:service&&service.featureBusy?(Theme.smartschool?I18n.t('Laden…'):I18n.t('Loading…')):(Theme.smartschool?I18n.t('Vernieuwen'):I18n.t('Refresh'));symbol:'retry';enabled:!!service&&!service.featureBusy;onClicked:service.loadResources()}
    }
    ListView {
        id:list;objectName:'resourceList';Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:12;bottomMargin:16
        model:view.rows;reuseItems:true;boundsBehavior:Flickable.StopAtBounds;activeFocusOnTab:true
        ScrollBar.vertical:ScrollBar {}
        SmoothScroll {id:scrollMotion;view:list}
        property real previousOriginY:0
        onOriginYChanged:{let wasTop=Math.abs(contentY-previousOriginY)<2;previousOriginY=originY;if(wasTop&&view.visible&&!view.resetPending&&!moving&&!scrollMotion.active&&!scrollMotion.glide.running)contentY=originY}
        header:Column {
            width:list.width;spacing:Theme.smartschool?0:12
            Repeater {model:view.offlineOnly?[]:Object.keys(view.resources.errors||{}).filter(k=>k==='reports'||k==='periods')
                Label {required property var modelData;width:parent.width;text:(({reports:I18n.t('Report cards'),periods:I18n.t('Academic periods'),courses:I18n.t('Courses'),support:I18n.t('School support'),homepage:I18n.t('School homepage')})[modelData]||I18n.t('School section'))+': '+I18n.t(view.resources.errors[modelData]);textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.orange}
            }
            Pane {width:parent.width;visible:!view.offlineOnly&&!Theme.smartschool;padding:14
                background:Surface {radius:Theme.fancy?18:3}
                contentItem:ColumnLayout {spacing:10
                    RowLayout {Layout.fillWidth:true
                        Label {text:Theme.smartschool?I18n.t('Schooljaar'):I18n.t('School year');textFormat:Text.PlainText;color:Theme.secondary;Layout.preferredWidth:92*Theme.textScale;font.pixelSize:12*Theme.textScale}
                        GlassComboBox {objectName:Theme.smartschool?'legacyReportYearFilter':'reportYearFilter';Layout.fillWidth:true;model:view.years.map(y=>Theme.smartschool&&y==='All school years'?I18n.t('Alle schooljaren'):y);currentIndex:Math.max(0,view.years.indexOf(view.reportYear));Accessible.name:I18n.t('Filter report cards by school year');onActivated:{view.reportYear=view.years[currentIndex];view.requestTop()}}
                    }
                    RowLayout {Layout.fillWidth:true
                        Label {text:Theme.smartschool?I18n.t('Periode'):I18n.t('Grade period');textFormat:Text.PlainText;color:Theme.secondary;Layout.preferredWidth:92*Theme.textScale;font.pixelSize:12*Theme.textScale}
                        GlassComboBox {objectName:Theme.smartschool?'legacyResourcePeriodFilter':'resourcePeriodFilter';Layout.fillWidth:true;model:[Theme.smartschool?I18n.t('Alle periodes'):I18n.t('All periods')].concat(view.periods.map(p=>(p.name||I18n.t('Periode'))+(p.schoolYear?' · '+p.schoolYear:'')));currentIndex:view.service?Math.max(0,view.periods.findIndex(p=>p.name===view.service.selectedPeriod)+1):0;Accessible.name:I18n.t('Choose academic period');onActivated:if(view.service)view.service.selectPeriod(currentIndex?view.periods[currentIndex-1].name:'')}
                    }
                }
            }
            Label {visible:view.rows.length===0;width:parent.width;text:view.offlineOnly?I18n.t('No offline files. Download a message attachment or report to keep a local copy.'):I18n.t('No matching information. Press Refresh to check school access and availability.');textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.secondary}
            Item {width:1;height:Theme.smartschool?0:12}
        }
        delegate:Column {
            id:row;required property var modelData;required property int index;width:list.width;spacing:8
            Label {visible:!Theme.fancy&&!view.offlineOnly&&(row.index===0||view.rows[row.index-1].schoolYear!==row.modelData.schoolYear);text:row.modelData.schoolYear||I18n.t('Schooljaar onbekend');textFormat:Text.PlainText;color:Theme.blue;topPadding:4;bottomPadding:4;font.pixelSize:12*Theme.textScale}
            Rectangle {objectName:'reportDocumentRow';visible:!Theme.fancy&&!view.offlineOnly;width:parent.width;height:Math.max(44*Theme.textScale,reportContent.implicitHeight+18);color:Theme.fill
                RowLayout {id:reportContent;anchors.fill:parent;anchors.margins:9;spacing:12
                    Icon {name:'file';width:22;height:22;ink:Theme.blue}
                    ColumnLayout {Layout.fillWidth:true;spacing:3;Label {text:row.modelData.name||I18n.t('Report card');textFormat:Text.PlainText;color:Theme.text;Layout.fillWidth:true;wrapMode:Text.Wrap;font.underline:true;font.pixelSize:13*Theme.textScale} Label {visible:!row.modelData.downloadable;text:I18n.t('Saved report information · file unavailable');color:Theme.secondary;Layout.fillWidth:true;wrapMode:Text.Wrap;font.pixelSize:11*Theme.textScale}}
                    Label {text:row.modelData.className||'';textFormat:Text.PlainText;color:Theme.secondary;Layout.preferredWidth:Math.max(50,parent.width*.12);wrapMode:Text.Wrap;font.pixelSize:12*Theme.textScale}
                    Label {text:row.modelData.date||'';textFormat:Text.PlainText;color:Theme.secondary;Layout.preferredWidth:Math.max(80,parent.width*.17);wrapMode:Text.Wrap;font.pixelSize:12*Theme.textScale}
                    Capsule {text:Theme.smartschool?I18n.t('Bekijken'):I18n.t('View');visible:!!row.modelData.downloadable;enabled:!!view.service&&!view.service.featureBusy;onClicked:view.service.viewReport(String(row.modelData.id))}
                    Capsule {text:I18n.t('Download');visible:!!row.modelData.downloadable;enabled:!!view.service&&!view.service.featureBusy;onClicked:view.service.downloadAttachment('report',String(row.modelData.id))}
                }
            }
            DetailCard {width:parent.width;visible:Theme.fancy&&!view.offlineOnly;title:row.modelData.name||I18n.t('Report card')
                Label {text:[row.modelData.date,row.modelData.className,row.modelData.schoolYear].filter(Boolean).join(' · ');textFormat:Text.PlainText;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.secondary}
                RowLayout {visible:!!row.modelData.downloadable
                    Capsule {text:I18n.t('View report');enabled:!!view.service&&!view.service.featureBusy;onClicked:view.service.viewReport(String(row.modelData.id))}
                    Capsule {text:I18n.t('Download report');enabled:!!view.service&&!view.service.featureBusy;onClicked:view.service.downloadAttachment('report',String(row.modelData.id))}
                }
            }
            Capsule {objectName:'offlineFileEntry';visible:view.offlineOnly;width:parent.width;text:row.modelData.name||I18n.t('Downloaded file');onClicked:fileSheet.showFile(row.modelData)}
        }
    }
    OfflineFileSheet {id:fileSheet;parent:view.app.contentItem;service:view.service}
}
