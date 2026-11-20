import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Icons.js" as Icons
import "ResultPalette.js" as ResultPalette
Item {
    id:view;objectName:'resultsLvsWorkspace'
    required property var app
    property int revision:0
    property string course:'All subjects'
    property string category:'notes'
    property bool reports:false
    property string schoolYear:'All school years'
    property var periodSelection:[]
    property var selected:({})
    readonly property bool grades:app.section===4
    readonly property bool resultMotion:grades&&!reports&&!Theme.fancy&&Theme.motion&&visible
    readonly property var service:app.production?backend.features:null
    function demoGroups(){
        if(app.datasetIndex===0)return []
        let items=[]
        for(let i=0;i<(grades?12:8);i++){
            let stamp='2026-'+(i<4?'11':'10')+'-'+String(20-i).padStart(2,'0')
            items.push(grades?{id:'demo-grade-'+i,kind:'grade',title:i%2?'Class participation':'Chapter review',course:['Mathematics','Sciences','Languages'][i%3],date:stamp,meta:stamp,extra:i%2?'14 / 20':'8 / 10',percentText:i%2?'70%':'80%',tone:'green',counts:true,period:'Term 1',teacher:'Demo tutor',schoolYear:'2026–2027',feedback:['Explain your reasoning and check the final step.'],body:'Synthetic result. No school account connected.'}:{id:'demo-note-'+i,kind:i<5?'notes':'absences',title:i<5?'Study progress':'Authorised absence',date:stamp,schoolYear:'2026–2027',description:'Synthetic school record. Keep using your planner to prepare the next steps.',category:I18n.t('Leerlingvolgsysteem'),author:'Demo tutor',part:'Morning',body:'Synthetic record. No school account connected.'})
        }
        return [{heading:I18n.t('Synthetic workspace'),items:items}]
    }
    readonly property var groups:{let r=revision,a=app.fixtureRevision;return app.production?backend.groups(grades?4:5,app.searchText,grades?course:'All subjects'):demoGroups()}
    readonly property var summaries:groups.filter(g=>g.items.some(i=>i.kind==='summary'))
    readonly property var allRows:{let all=[];for(let g of groups)for(let i of g.items)if(i.kind!=='summary')all.push(i);return all}
    readonly property var years:['All school years'].concat([...new Set(allRows.map(i=>i.schoolYear).filter(Boolean))].sort().reverse())
    readonly property var rows:allRows.filter(i=>(grades||i.kind===category)&&(!grades||schoolYear==='All school years'||i.schoolYear===schoolYear)&&(!grades||!periodSelection.length||periodSelection.indexOf(i.period)>=0)).sort((a,b)=>String(b.date||'').localeCompare(String(a.date||'')))
    readonly property var entry:rows.find(r=>r.id===selected.id)||rows[0]||({})
    readonly property var courses:['All subjects'].concat([...new Set(rows.map(r=>r.course).filter(Boolean))])
    readonly property var periods:service?service.resources.periods||[]:[]
    readonly property var averages:{
        let buckets={'Alle vakken':[]}
        for(let item of rows)if(item.counts&&typeof item.score==='number'&&typeof item.maximum==='number'&&item.maximum>0){buckets['Alle vakken'].push(item);if(!buckets[item.course])buckets[item.course]=[];buckets[item.course].push(item)}
        return Object.keys(buckets).map(name=>{let items=buckets[name],scale=Math.max(...items.map(i=>Math.max(Math.abs(i.score),i.maximum)),0),points=0,total=0;for(let i of items){points+=i.score/scale;total+=i.maximum/scale}return {name:name,value:total?Math.round(points/total*100)+'%':'—'}})
    }
    function year(item){return item.schoolYear||I18n.t('Schooljaar onbekend')}
    function month(item){let d=new Date((item.date||'')+'T12:00:00');return isNaN(d)?I18n.t('Datum onbekend'):d.toLocaleDateString(I18n.locale,'MMMM yyyy')}
    function dateLabel(item){let d=new Date((item.date||'')+'T12:00:00');return isNaN(d)?I18n.t('Datum onbekend'):d.toLocaleDateString(I18n.locale,'dddd d MMMM yyyy')}
    function open(item){selected=item;if(app.production)app.openSection(item)}
    function selectResult(item,pointer){
        let changed=entry.id!==item.id
        selected=item
        if(changed&&pointer&&resultMotion){
            if(!detailFade.running)detailBody.opacity=.92
            detailFade.start()
        }else if(!pointer||!resultMotion){detailFade.stop();detailBody.opacity=1}
    }
    onResultMotionChanged:if(!resultMotion&&detailBody){detailFade.stop();detailBody.opacity=1}
    function choosePeriod(name,checked){let chosen=periodSelection.slice();if(checked&&chosen.indexOf(name)<0)chosen.push(name);if(!checked)chosen=chosen.filter(p=>p!==name);if(service&&service.selectedPeriod)service.selectPeriod('');periodSelection=chosen;selected=({})}
    Connections {target:app;function onSectionChanged(){view.selected=({});view.reports=false} function onFixtureRevisionChanged(){view.selected=({});view.revision++}}
    Connections {target:app.production?backend:null;function onGroupsChanged(section){view.selected=({});view.revision++}}
    Rectangle {anchors.fill:parent;color:Theme.elevated}
    RowLayout {anchors.fill:parent;spacing:0
        Rectangle {Layout.preferredWidth:view.grades?(view.width>=1050*Theme.textScale?135*Theme.textScale:42):Math.min(230,view.width*.22);Layout.fillHeight:true;color:Theme.fill;border.color:Theme.separator
            ColumnLayout {anchors.fill:parent;anchors.margins:view.grades?3:10;spacing:3
                RowLayout {visible:!view.grades;Layout.fillWidth:true;Icon {name:'chevron';ink:Theme.secondary;width:14*Theme.textScale;height:width} Label {text:I18n.t('▾  Leerlingenbegeleiding').replace(/^▾\s*/, '');textFormat:Text.PlainText;color:Theme.text;Layout.fillWidth:true;wrapMode:Text.Wrap;font.bold:true}}
                RowLayout {visible:!view.grades;Layout.fillWidth:true;Layout.leftMargin:12;Icon {name:'chevron';ink:Theme.secondary;width:14*Theme.textScale;height:width} Label {text:I18n.t('   ▾  Schooldossier').replace(/^\s*▾\s*/, '');color:Theme.secondary;Layout.fillWidth:true;wrapMode:Text.Wrap}}
                Repeater {model:view.grades?[{name:I18n.t('Resultaten'),icon:'grades',kind:'results'},{name:I18n.t('Rapporten'),icon:'file',kind:'reports'}]:[{name:I18n.t('Notities'),icon:'file',kind:'notes'},{name:I18n.t('Afwezigheden'),icon:'clock',kind:'absences'}]
                    ItemDelegate {required property var modelData;Layout.fillWidth:true;implicitHeight:38*Theme.textScale;padding:5;text:modelData.name;Accessible.name:modelData.name;highlighted:view.grades?(view.reports===(modelData.kind==='reports')):view.category===modelData.kind
                        background:Rectangle {color:parent.highlighted?Theme.alpha(Theme.blue,.12):'transparent'}
                        contentItem:RowLayout {Icon {name:parent.parent.modelData.icon;ink:Theme.blue;Layout.alignment:Qt.AlignVCenter} Label {visible:!view.grades||view.width>=1050*Theme.textScale;text:parent.parent.text;color:Theme.text;wrapMode:Text.Wrap;font.pixelSize:13*Theme.textScale}}
                        onClicked:{if(view.grades)view.reports=modelData.kind==='reports';else view.category=modelData.kind;view.selected=({})}
                        GlassToolTip {requested:parent.hovered||parent.visualFocus;text:parent.modelData.name}
                    }
                }
                Item {Layout.fillHeight:true}
                Capsule {visible:!view.grades;text:I18n.t('Alles als gelezen markeren');Layout.fillWidth:true;onClicked:if(app.production)backend.markRead('*')}
            }
        }
        ColumnLayout {Layout.fillWidth:true;Layout.fillHeight:true;spacing:0
            RowLayout {visible:!view.grades||!view.reports;Layout.fillWidth:true;Layout.margins:14;spacing:12
                Label {text:view.grades?(view.reports?I18n.t('Rapporten'):I18n.t('Resultaten')):(view.category==='notes'?I18n.t('Leerlingennotities'):I18n.t('Afwezigheden'));textFormat:Text.PlainText;color:Theme.secondary;font.pixelSize:20*Theme.textScale}
                Rectangle {visible:view.grades;width:1;Layout.preferredHeight:30;color:Theme.separator}
                GlassComboBox {visible:view.grades&&!view.reports;objectName:'resultYearFilter';model:view.years.map(y=>y==='All school years'?I18n.t('Alle schooljaren'):y);currentIndex:Math.max(0,view.years.indexOf(view.schoolYear));Layout.maximumWidth:240;Accessible.name:I18n.t('Resultaten op schooljaar filteren');onActivated:view.schoolYear=view.years[currentIndex]}
                Item {visible:view.grades;Layout.fillWidth:true}
                Item {visible:!view.grades;Layout.fillWidth:true}
                Capsule {visible:view.grades&&!view.reports;text:I18n.t('Gemiddelden');onClicked:{averagePopup.pointerMotion=!visualFocus;averagePopup.open()}}
            }
            Popup {id:averagePopup;objectName:'resultAveragesPopup';parent:Overlay.overlay;x:Math.max(8,(parent.width-width)/2);y:80;width:Math.min(460,parent.width-20);padding:16;closePolicy:Popup.CloseOnEscape|Popup.CloseOnPressOutside
                property real reveal:0
                property bool pointerMotion:false
                readonly property bool animate:pointerMotion&&view.resultMotion
                onAboutToShow:if(!animate)reveal=1
                onClosed:{reveal=0;pointerMotion=false}
                enter:Transition {NumberAnimation {target:averagePopup;property:'reveal';to:1;duration:averagePopup.animate?160:0;easing.type:Easing.OutCubic}}
                exit:Transition {NumberAnimation {target:averagePopup;property:'reveal';to:0;duration:averagePopup.animate?120:0;easing.type:Easing.OutCubic}}
                background:Rectangle {opacity:averagePopup.reveal;radius:!Theme.fancy?8:0;color:Theme.elevated;border.color:Theme.separator}
                contentItem:ColumnLayout {opacity:averagePopup.reveal;Repeater {model:view.averages;Label {required property var modelData;text:(modelData.name==='Alle vakken'?I18n.t('Alle vakken'):modelData.name)+': '+modelData.value;color:Theme.text;Layout.fillWidth:true;wrapMode:Text.Wrap}}}
            }
            ResourcesView {visible:view.grades&&view.reports;Layout.fillWidth:true;Layout.fillHeight:true;Layout.leftMargin:16;Layout.rightMargin:16;Layout.bottomMargin:16;app:view.app}
            RowLayout {visible:view.grades&&!view.reports;Layout.fillWidth:true;Layout.fillHeight:true;spacing:0
                ColumnLayout {Layout.preferredWidth:Math.max(230,view.width*.39);Layout.fillHeight:true;spacing:0
                    RowLayout {Layout.fillWidth:true;Layout.margins:10;spacing:4
                        Item {Layout.fillWidth:true}
                        GlassComboBox {objectName:'resultsCourseFilter';leftPadding:8;Layout.fillWidth:true;Layout.minimumWidth:80;Layout.maximumWidth:Math.min(200,implicitWidth);readonly property var choices:app.production?backend.gradeCourses:view.courses;model:choices.map(c=>c==='All subjects'?I18n.t('Alle vakken'):c);currentIndex:Math.max(0,choices.indexOf(view.course));Accessible.name:I18n.t('Resultaten op vak filteren');onActivated:{view.course=choices[currentIndex];view.selected=({})}}
                        Capsule {id:periodButton;objectName:'resultsPeriodFilter';leftPadding:7;rightPadding:7;Layout.fillWidth:true;Layout.minimumWidth:80;Layout.maximumWidth:implicitWidth;text:view.periodSelection.length?view.periodSelection.length+I18n.t(' periodes ▾'):service&&service.selectedPeriod?service.selectedPeriod:I18n.t('Alle periodes ▾');onClicked:{periodPopup.pointerMotion=!visualFocus;periodPopup.open()}}
                    }
                    Popup {id:periodPopup;objectName:'resultPeriodsPopup';parent:Overlay.overlay;x:Math.max(8,Math.min(parent.width-width-8,periodButton.mapToItem(parent,0,periodButton.height).x));y:Math.min(parent.height-height-8,periodButton.mapToItem(parent,0,periodButton.height).y);width:260; padding:8;closePolicy:Popup.CloseOnEscape|Popup.CloseOnPressOutside
                        property real reveal:0
                        property bool pointerMotion:false
                        readonly property bool animate:pointerMotion&&view.resultMotion
                        onAboutToShow:if(!animate)reveal=1
                        onClosed:{reveal=0;pointerMotion=false}
                        enter:Transition {NumberAnimation {target:periodPopup;property:'reveal';to:1;duration:periodPopup.animate?160:0;easing.type:Easing.OutCubic}}
                        exit:Transition {NumberAnimation {target:periodPopup;property:'reveal';to:0;duration:periodPopup.animate?120:0;easing.type:Easing.OutCubic}}
                        background:Rectangle {opacity:periodPopup.reveal;radius:!Theme.fancy?8:0;color:Theme.elevated;border.color:Theme.separator}
                        contentItem:ColumnLayout {opacity:periodPopup.reveal;CheckBox {text:I18n.t('Alle periodes selecteren');checked:!view.periodSelection.length&&(!view.service||!view.service.selectedPeriod);onClicked:{view.periodSelection=[];if(view.service)view.service.selectPeriod('')}}
                            Repeater {model:view.periods;CheckBox {required property var modelData;text:modelData.name||I18n.t('Period');icon.source:Icons.url('cal',Theme.secondary.toString());icon.width:16*Theme.textScale;icon.height:16*Theme.textScale;checked:view.periodSelection.indexOf(modelData.name)>=0||!!view.service&&view.service.selectedPeriod===modelData.name;onClicked:view.choosePeriod(modelData.name,checked)}}
                        }
                    }
                    ListView {id:resultList;objectName:'chronologicalResults';Layout.fillWidth:true;Layout.fillHeight:true;clip:true;model:view.rows;spacing:12;leftMargin:14;rightMargin:14;topMargin:20;bottomMargin:20
                        ScrollBar.vertical:ScrollBar{} SmoothScroll {view:resultList}
                        delegate:Column {required property var modelData;required property int index;width:resultList.width-28;spacing:8
                            Label {visible:index===0||view.month(view.rows[index-1])!==view.month(modelData);text:view.month(modelData);color:Theme.blue;font.pixelSize:14*Theme.textScale;topPadding:index?24:6;bottomPadding:8}
                            ItemDelegate {id:resultRow;objectName:'chronologicalResultRow';width:parent.width;padding:7;implicitHeight:Math.max(72*Theme.textScale,contentItem.implicitHeight+14);hoverEnabled:true;Accessible.name:modelData.title+', '+modelData.extra+', '+modelData.meta;Accessible.selected:view.entry.id===modelData.id
                                background:Rectangle {radius:!Theme.fancy?8:5;color:Theme.highContrast?Theme.fill:ResultPalette.fill(modelData,Theme.dark);border.width:view.entry.id===modelData.id||resultRow.visualFocus?2:0;border.color:Theme.highContrast?Theme.text:ResultPalette.ink(modelData,Theme.dark)
                                    Rectangle {anchors.fill:parent;anchors.margins:2;radius:Math.max(0,parent.radius-2);color:Theme.text;opacity:Theme.fancy?0:resultRow.down?.08:resultRow.hovered?.035:0
                                        Behavior on opacity {NumberAnimation {duration:view.resultMotion&&!resultRow.down?120:0;easing.type:Easing.OutCubic}}
                                    }
                                }
                                contentItem:ColumnLayout {spacing:4
                                    RowLayout {Layout.fillWidth:true;ResultScore {entry:modelData;Layout.alignment:Qt.AlignTop}
                                        ColumnLayout {Layout.fillWidth:true;Layout.minimumWidth:0;Label {text:modelData.title;textFormat:Text.PlainText;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text;font.pixelSize:15*Theme.textScale} Label {text:view.dateLabel(modelData)+(modelData.counts===false?I18n.t(' · Telt niet mee'):'');textFormat:Text.PlainText;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.secondary;font.pixelSize:11*Theme.textScale}}
                                    }
                                    Item {Layout.fillWidth:true;implicitHeight:Math.max(scoreTag.implicitHeight,subjectTag.implicitHeight)
                                        Label {id:scoreTag;anchors.left:parent.left;width:parent.width*.3;text:modelData.extra||modelData.resultLabel||'';color:Theme.text;font.pixelSize:11*Theme.textScale;wrapMode:Text.Wrap}
                                        Label {id:subjectTag;anchors.right:parent.right;width:parent.width*.65;text:[modelData.course,modelData.period].filter(Boolean).join('  ·  ');textFormat:Text.PlainText;color:Theme.secondary;horizontalAlignment:Text.AlignRight;wrapMode:Text.Wrap;font.pixelSize:10*Theme.textScale}
                                    }
                                }
                                onClicked:view.selectResult(modelData,!visualFocus)
                            }
                        }
                        Label {visible:resultList.count===0;anchors.centerIn:parent;text:I18n.t('Geen overeenkomende resultaten');color:Theme.secondary}
                    }
                }
                Rectangle {width:1;Layout.fillHeight:true;color:Theme.separator}
                ScrollView {id:resultDetail;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;contentWidth:availableWidth
                    ColumnLayout {id:detailBody;objectName:'resultDetailContent';width:resultDetail.availableWidth;spacing:12
                        NumberAnimation {id:detailFade;objectName:'resultDetailFade';target:detailBody;property:'opacity';to:1;duration:140;easing.type:Easing.OutCubic}
                        Label {text:(view.entry.course?view.entry.course+'  ·  ':'')+(view.entry.title||I18n.t('Selecteer een resultaat'));textFormat:Text.PlainText;color:Theme.secondary;font.pixelSize:20*Theme.textScale;Layout.fillWidth:true;Layout.margins:18;wrapMode:Text.Wrap}
                        ResultScore {entry:view.entry;large:true;Layout.leftMargin:24;Layout.topMargin:8}
                        Label {text:I18n.t('Details');color:Theme.blue;Layout.leftMargin:24;Layout.topMargin:18}
                        Flow {Layout.fillWidth:true;Layout.margins:18;spacing:8
                            Repeater {model:[{icon:'schedule',text:view.entry.date?view.dateLabel(view.entry):''},{icon:'grades',text:view.entry.course},{icon:'file',text:view.entry.period},{icon:'user',text:view.entry.teacher},{icon:'folder',text:view.entry.className},{icon:'ok',text:view.entry.counts===false?I18n.t('Telt niet mee'):''}].filter(i=>i.text)
                                Rectangle {required property var modelData;width:Math.min(chip.implicitWidth+44,resultDetail.availableWidth-36);height:Math.max(28,chip.implicitHeight+12);radius:height/2;color:Theme.fill;Icon {anchors.left:parent.left;anchors.leftMargin:9;anchors.verticalCenter:parent.verticalCenter;name:modelData.icon;width:16;height:16;ink:Theme.blue} Label {id:chip;x:32;anchors.verticalCenter:parent.verticalCenter;width:Math.min(implicitWidth,parent.width-40);text:modelData.text;textFormat:Text.PlainText;color:Theme.text;font.pixelSize:12*Theme.textScale;wrapMode:Text.Wrap}}
                            }
                        }
                        Label {visible:!!(view.entry.feedback||[]).length;text:(view.entry.feedback||[]).join('\n\n');textFormat:Text.PlainText;color:Theme.text;Layout.fillWidth:true;Layout.margins:24;wrapMode:Text.Wrap}
                        Capsule {text:I18n.t('Details openen');enabled:!!view.entry.id;Layout.leftMargin:24;onClicked:view.open(view.entry)}
                        Item {height:20}
                    }
                }
            }
            LvsRecords {visible:!view.grades;Layout.fillWidth:true;Layout.fillHeight:true;Layout.margins:14;app:view.app;rows:view.rows;kind:view.category}
        }
    }
}
