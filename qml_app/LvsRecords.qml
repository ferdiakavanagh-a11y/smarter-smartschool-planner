import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Rectangle {
    id:view;objectName:'lvsRecords';required property var app
    property var rows:[]
    property var collapsedNotes: ({})
    function toggleNote(id) {
        let next = Object.assign({}, collapsedNotes)
        if (next[id]) delete next[id]
        else next[id] = true
        collapsedNotes = next
    }
    property string kind:'notes'
    readonly property var noteDetails:app.production?backend.noteDetails:({})
    color:Theme.elevated;border.color:Theme.separator;radius:8
    function validDate(item){let stamp=String(item.date||'');return /^\d{4}-\d{2}-\d{2}/.test(stamp)&&!isNaN(new Date(stamp.slice(0,10)+'T12:00:00'))}
    readonly property var dated:kind==='absences'?rows.filter(validDate):[]
    function buckets(mode){let groups=Object.create(null);for(let item of dated){let d=new Date(item.date.slice(0,10)+'T12:00:00'),key=mode===2?(item.code||I18n.t('Unknown')):mode===1?String((d.getDay()+6)%7):item.date.slice(0,7);if(!groups[key])groups[key]={month:d.getFullYear()*12+d.getMonth(),name:mode===2?key:mode===1?d.toLocaleDateString(I18n.locale,'ddd'):d.toLocaleDateString(I18n.locale,'MMM yyyy'),count:0};groups[key].count++}return Object.keys(groups).sort().map(k=>groups[k])}
    ListView {
        id:scroll
        anchors.fill:parent;anchors.margins:12;clip:true
        model:view.rows
        reuseItems:true
        ScrollBar.vertical:ScrollBar {}
        SmoothScroll {view:scroll}
        header:ColumnLayout {width:scroll.width;spacing:8
            Label {text:view.kind==='notes'?I18n.t('Leerlingvolgsysteem'):I18n.t('Afwezigheden');color:Theme.secondary;Layout.alignment:Qt.AlignHCenter;font.pixelSize:13*Theme.textScale}
            GridLayout {id:charts;visible:view.kind==='absences'&&view.dated.length>0;Layout.fillWidth:true;columns:view.width<540*Theme.textScale?1:2;columnSpacing:10;rowSpacing:10
                Repeater {model:[0,1,2]
                    Rectangle {id:chart;required property int modelData;readonly property var bars:view.buckets(modelData);readonly property int maximum:Math.max(...bars.map(i=>i.count),1);Layout.columnSpan:modelData===2?charts.columns:1;Layout.fillWidth:true;implicitHeight:170*Theme.textScale;color:Theme.elevated;border.color:Theme.separator
                        ColumnLayout {anchors.fill:parent;anchors.margins:10;Label {text:[I18n.t('Aantal registraties per maand'),I18n.t('Aantal registraties per weekdag'),I18n.t('Aantal registraties per code')][chart.modelData];color:Theme.text;font.bold:true;font.pixelSize:12*Theme.textScale;Layout.fillWidth:true;wrapMode:Text.Wrap}
                            ListView {
                                id:months;objectName:"absenceMonthAxis"
                                visible:chart.modelData===0
                                Layout.fillWidth:true;Layout.fillHeight:true
                                orientation:ListView.Horizontal;clip:true
                                readonly property var counts:{
                                    let result={}
                                    for (let bar of chart.bars) result[bar.month]=bar.count
                                    return result
                                }
                                readonly property int first:chart.bars.length?chart.bars[0].month:0
                                model:visible&&chart.bars.length?chart.bars[chart.bars.length-1].month-first+1:0
                                ScrollBar.horizontal:ScrollBar {}
                                delegate:ColumnLayout {
                                    required property int index
                                    readonly property int month:months.first+index
                                    readonly property int count:months.counts[month]||0
                                    width:Math.max(72*Theme.textScale,months.width/Math.max(1,months.count));height:months.height
                                    spacing:2
                                    Item {
                                        Layout.fillWidth:true;Layout.fillHeight:true
                                        Rectangle {
                                            anchors.bottom:parent.bottom;anchors.horizontalCenter:parent.horizontalCenter
                                            visible:parent.parent.count>0;width:Math.min(38,parent.width);height:parent.height*parent.parent.count/chart.maximum;color:Theme.blue
                                        }
                                        Label {anchors.horizontalCenter:parent.horizontalCenter;anchors.bottom:parent.bottom;text:parent.parent.count||'\u2014';color:Theme.text}
                                    }
                                    Label {Layout.alignment:Qt.AlignHCenter;Layout.bottomMargin:8;text:new Date(Math.floor(month/12),month%12,1).toLocaleDateString(I18n.locale,'MMM yyyy');color:Theme.secondary;font.pixelSize:11*Theme.textScale}
                                }
                            }
                            RowLayout {visible:chart.modelData!==0;Layout.fillWidth:true;Layout.fillHeight:true;spacing:5
                                Repeater {model:chart.bars
                                    ColumnLayout {required property var modelData;Layout.fillWidth:true;Layout.fillHeight:true;spacing:4
                                        Item {Layout.fillHeight:true;Layout.fillWidth:true;Rectangle {visible:chart.modelData!==0;anchors.bottom:parent.bottom;anchors.horizontalCenter:parent.horizontalCenter;width:Math.min(38,parent.width);height:Math.max(8,parent.height*modelData.count/chart.maximum);color:chart.modelData===2?Theme.orange:Theme.blue} Label {anchors.bottom:parent.bottom;anchors.horizontalCenter:parent.horizontalCenter;text:String(modelData.count);color:Theme.text;font.pixelSize:11*Theme.textScale}}
                                        Label {text:modelData.name;color:Theme.secondary;font.pixelSize:10*Theme.textScale;Layout.fillWidth:true;horizontalAlignment:Text.AlignHCenter;elide:Text.ElideRight}
                                    }
                                }
                            }
                        }
                    }
                }
            }
            Label {visible:view.kind==='absences'&&view.dated.length>0;text:I18n.p('Charts show saved, dated records. A dash means no record is available for that month.','De grafieken tonen opgeslagen registraties met een datum. Een streepje betekent dat er voor die maand geen registratie beschikbaar is.');color:Theme.secondary;font.pixelSize:11*Theme.textScale;Layout.fillWidth:true;wrapMode:Text.Wrap}
            Label {visible:scroll.count===0;text:I18n.t('Geen overeenkomende registraties');color:Theme.secondary;Layout.fillWidth:true;padding:20}
        }
        delegate:ColumnLayout {
            id:record;required property var modelData;required property int index
            readonly property bool expanded:!view.collapsedNotes[modelData.id]
            width:scroll.width;spacing:0
            readonly property var detail:view.noteDetails[modelData.id]||({})
            Label {visible:index===0||view.rows[index-1].schoolYear!==modelData.schoolYear;text:modelData.schoolYear||I18n.t('Schooljaar onbekend');color:Theme.text;font.bold:true;font.pixelSize:13*Theme.textScale;Layout.fillWidth:true;topPadding:18;bottomPadding:5}
            Rectangle {visible:index===0||view.rows[index-1].schoolYear!==modelData.schoolYear;Layout.fillWidth:true;implicitHeight:3;color:Theme.separator}
            ItemDelegate {visible:view.kind==='notes';Layout.fillWidth:true;implicitHeight:Math.max(34*Theme.textScale,contentItem.implicitHeight+14);padding:7;Accessible.name:record.modelData.title+(record.modelData.unread?I18n.t(', unread'):'')
                background:Rectangle {color:Theme.fill;border.color:Theme.separator}
                contentItem:RowLayout {Icon {name:record.expanded?'chevron':'chevronRight';ink:Theme.secondary;width:14*Theme.textScale;height:width} Label {text:record.modelData.title;textFormat:Text.PlainText;color:Theme.text;Layout.fillWidth:true;wrapMode:Text.Wrap;font.bold:true;font.pixelSize:15*Theme.textScale} Label {text:[record.modelData.author,record.modelData.date].filter(Boolean).join(' · ');textFormat:Text.PlainText;color:Theme.secondary;Layout.maximumWidth:parent.width*.4;wrapMode:Text.Wrap;font.pixelSize:11*Theme.textScale}}
                onClicked:{view.toggleNote(record.modelData.id);if(app.production)backend.markRead(record.modelData.id)}
            }
            Rectangle {visible:view.kind==='notes'&&record.expanded;Layout.fillWidth:true;implicitHeight:noteContent.implicitHeight+20;color:Theme.elevated;border.color:Theme.separator
                ColumnLayout {id:noteContent;anchors.left:parent.left;anchors.right:parent.right;anchors.margins:10;y:10;spacing:12
                    RowLayout {Layout.fillWidth:true;Layout.alignment:Qt.AlignTop;Label {text:I18n.t('Type');color:Theme.text;font.bold:true;font.pixelSize:12*Theme.textScale;Layout.preferredWidth:Math.min(130,view.width*.17);Layout.alignment:Qt.AlignTop} Label {text:record.modelData.category||I18n.t('Leerlingennotitie');textFormat:Text.PlainText;color:Theme.text;Layout.fillWidth:true;wrapMode:Text.Wrap}}
                    RowLayout {Layout.fillWidth:true;Layout.alignment:Qt.AlignTop;Label {text:I18n.t('Melding');color:Theme.text;font.bold:true;font.pixelSize:12*Theme.textScale;Layout.preferredWidth:Math.min(130,view.width*.17);Layout.alignment:Qt.AlignTop} TextArea {text:record.detail.bodyHtml||record.detail.body||record.modelData.description||(app.production&&backend.notesLoading?I18n.t('Loading note…'):record.detail.body!==undefined?I18n.p('No note text','Geen notitietekst'):I18n.p('Note unavailable','Notitie niet beschikbaar'));textFormat:record.detail.bodyHtml?TextEdit.RichText:TextEdit.PlainText;color:Theme.text;readOnly:true;selectByMouse:true;wrapMode:TextEdit.Wrap;Layout.fillWidth:true;padding:0;background:Item{}}}
                    Repeater {model:record.detail.links||[];ColumnLayout {required property var modelData;Layout.fillWidth:true
                        Label {visible:!parent.modelData.url;text:I18n.t('Bijlage: ')+(parent.modelData.name||I18n.t('Document'));textFormat:Text.PlainText;color:Theme.secondary;Layout.fillWidth:true;wrapMode:Text.Wrap}
                        Capsule {visible:!!parent.modelData.url;text:parent.modelData.name||I18n.t('Bijlage openen');enabled:app.production&&!backend.features.featureBusy;onClicked:if(parent.modelData.downloadable)backend.features.viewLinkedFile(parent.modelData.url);else backend.openExternal(parent.modelData.url)}
                    }}
                    RowLayout {Layout.fillWidth:true;Label {text:I18n.t('Dossier');color:Theme.text;font.bold:true;font.pixelSize:12*Theme.textScale;Layout.preferredWidth:Math.min(130,view.width*.17)} Capsule {text:record.detail.body?I18n.t('Notitie vernieuwen'):I18n.t('Notitie openen');onClicked:if(app.production)backend.openNote(record.modelData.id.slice(6))} Item {Layout.fillWidth:true}}
                }
            }
            ItemDelegate {visible:view.kind==='absences';objectName:'absenceTableRow';Layout.fillWidth:true;implicitHeight:Math.max(40*Theme.textScale,contentItem.implicitHeight+14);padding:7;Accessible.name:[record.modelData.date,record.modelData.title,record.modelData.part].filter(Boolean).join(', ')
                background:Rectangle {color:parent.hovered?Theme.fill:Theme.elevated}
                contentItem:RowLayout {spacing:12
                    Label {text:record.modelData.date||I18n.t('Datum onbekend');color:Theme.secondary;Layout.preferredWidth:100*Theme.textScale;wrapMode:Text.Wrap;font.pixelSize:12*Theme.textScale}
                    Label {text:record.modelData.part||'—';color:Theme.secondary;Layout.preferredWidth:50*Theme.textScale;wrapMode:Text.Wrap;font.pixelSize:12*Theme.textScale}
                    Rectangle {width:24;height:24;radius:12;color:Theme.blue;Label {anchors.centerIn:parent;text:record.modelData.code||'•';color:'white';font.pixelSize:12}}
                    Label {text:record.modelData.description||record.modelData.title;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text;font.pixelSize:12*Theme.textScale}
                    Label {text:record.modelData.status||record.modelData.category||'';Layout.maximumWidth:parent.width*.2;wrapMode:Text.Wrap;color:Theme.secondary;font.pixelSize:12*Theme.textScale}
                }
                onClicked:app.openSection(record.modelData)
            }
        }
        footer:Item {width:scroll.width;height:16}
    }
}
