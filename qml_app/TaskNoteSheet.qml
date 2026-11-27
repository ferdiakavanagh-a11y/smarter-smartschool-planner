import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Sheet {
    required property var app
    property alias editorText:noteText.text
    function focusEditor(){noteText.forceActiveFocus()}
    id:notes;objectName:'noteDialog';property string taskId:'';property string taskTitle:''
    title:Theme.fancy?I18n.t('Task details'):notes.taskTitle
    headingColor:Theme.fancy?Theme.elevated:Theme.lesson
    width:Theme.fancy?Math.min(820*Theme.textScale,parent.width-24):app.width>1150?Math.min(1180*Theme.textScale,app.width-470):parent.width-28
    x:!Theme.fancy&&app.width>1150?app.width-width-48:(parent.width-width)/2
    implicitHeight:parent.height*.9
    readonly property var taskDate:(app.taskInfo.facts||[]).find(f=>f.label==='Due')
    readonly property var contextDays:{let revision=app.fixtureRevision;return visible&&!Theme.fancy&&app.width>1150&&app.production?backend.groups(3,'','All subjects'):[]}
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
                            TaskCheck {markSize:18;checked:!!tasks&&tasks.completedIds.indexOf(notes.taskId)>=0;Accessible.name:I18n.t('Opdracht voltooien');onClicked:if(tasks.change(notes.taskId,'done',checked))app.notify(checked?'Taak voltooid':'Taak hersteld');else checked=Qt.binding(function(){return tasks.completedIds.indexOf(notes.taskId)>=0})}
                            Label {text:I18n.t('Opdracht voltooid');color:Theme.text;font.pixelSize:11*Theme.textScale;Layout.fillWidth:true;wrapMode:Text.Wrap}
                        }
                        Capsule {text:I18n.t('Focus');symbol:'focus';onClicked:if(notes.beforeClose()){const id=notes.taskId,title=notes.taskTitle;notes.close();app.openFocus(id,title,tasks.completedIds.includes(id))}}
                    }
                    Label {visible:!!app.taskInfo.status;text:I18n.t(app.taskInfo.status||'');color:Theme.orange;Layout.fillWidth:true;wrapMode:Text.Wrap;font.pixelSize:11*Theme.textScale}
                    Capsule {text:I18n.t('Bronbericht openen');visible:app.production&&!!app.taskInfo.messageId;enabled:app.production&&!backend.features.featureBusy;Layout.fillWidth:true;onClicked:if(notes.beforeClose()){notes.close();app.openSourceMessage(app.taskInfo.messageId)}}
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
}
