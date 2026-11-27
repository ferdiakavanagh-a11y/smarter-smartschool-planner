import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Sheet {
    id:details
    required property var app
    property alias bodyText:detailsText.text
    readonly property bool lessonDetails:app.sectionInfo.kind==='lesson'
    readonly property var links:app.sectionInfo.links||[]
    readonly property var contentLinks:lessonDetails?links.filter(link=>!link.lessonPage):links
    readonly property var lessonPage:lessonDetails?links.find(link=>link.lessonPage):null
    width:Math.min((lessonDetails?(Theme.fancy?800:940):560)*Theme.textScale,parent.width-24)
    height:Math.min(implicitHeight+(lessonDetails?64*Theme.textScale:0),parent.height*.86)
    headerColor:lessonDetails&&!Theme.fancy?Theme.lesson:Theme.elevated
    footer:lessonDetails?lessonFooter:null
    Component {id:lessonFooter
        Pane {padding:Theme.fancy?16:10;background:Rectangle {color:Theme.fancy?"transparent":Theme.elevated;Rectangle {width:parent.width;height:1;color:Theme.separator;visible:!Theme.fancy}}
            contentItem:RowLayout {Item {Layout.fillWidth:true}
                Capsule {visible:!!details.lessonPage;text:details.lessonPage?details.lessonPage.name:'';symbol:'ext';onClicked:backend.openExternal(details.lessonPage.url)}
                Capsule {primary:true;text:I18n.t('Close');onClicked:details.dismiss()}
            }
        }
    }
    GridLayout {Layout.fillWidth:true;columns:details.lessonDetails&&details.width>=680*Theme.textScale?2:1;columnSpacing:18;rowSpacing:12
        ColumnLayout {Layout.fillWidth:true;Layout.preferredWidth:details.lessonDetails?details.width*.6:-1;Layout.minimumWidth:0;Layout.alignment:Qt.AlignTop;spacing:12
            ColumnLayout {objectName:'emptyLessonContent';visible:details.lessonDetails&&!detailsText.text.trim()&&!details.contentLinks.length&&!(app.sectionInfo.assignments||[]).length
                Layout.fillWidth:true;Layout.preferredHeight:(parent.parent.columns===2?230:108)*Theme.textScale;spacing:8
                Item {Layout.fillHeight:true}
                Icon {name:'file';ink:Theme.teal;Layout.alignment:Qt.AlignHCenter;implicitWidth:36*Theme.textScale;implicitHeight:implicitWidth}
                Label {text:I18n.p('There is no content for this lesson.','Er is geen inhoud bij deze les.');Layout.fillWidth:true;wrapMode:Text.Wrap;horizontalAlignment:Text.AlignHCenter;color:Theme.secondary}
                Item {Layout.fillHeight:true}
            }
            Label {textFormat:Text.PlainText;id:detailsText;visible:text.length>0;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text;font.pixelSize:16*Theme.textScale}
            Capsule {visible:app.production&&app.detailToken.startsWith('notes:');text:I18n.t('Reload note');onClicked:{detailsText.text=I18n.t('Loading note…');backend.openNote(app.detailToken.slice(6))}}
            Capsule {visible:app.production&&backend.school!==''&&app.sectionInfo.kind!=='lesson';text:I18n.t('Open Smartschool');onClicked:backend.openExternal('https://'+backend.school.replace(/^https?:\/\//,''))}
            Repeater {model:app.production?details.contentLinks:[];Capsule {required property var modelData;Layout.fillWidth:true;text:modelData.name||I18n.t('Open link');enabled:!!modelData.url&&!backend.features.featureBusy;onClicked:if(modelData.downloadable)backend.features.viewLinkedFile(modelData.url);else backend.openExternal(modelData.url)}}
            Repeater {model:app.production?(app.sectionInfo.assignments||[]):[]
                ColumnLayout {id:assignmentDetail;required property var modelData;Layout.fillWidth:true
                    LessonAssignment {app:details.hostWindow;modelData:assignmentDetail.modelData;onOpened:details.close()}
                    Label {text:assignmentDetail.modelData.body||'';visible:text.length>0;textFormat:Text.PlainText;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text}
                    Repeater {model:assignmentDetail.modelData.links||[]
                        Capsule {required property var modelData;Layout.fillWidth:true;text:modelData.name||I18n.t('Open link');enabled:!!modelData.url&&!backend.features.featureBusy;onClicked:if(modelData.downloadable)backend.features.viewLinkedFile(modelData.url);else backend.openExternal(modelData.url)}
                    }
                }
            }
        }
        Pane {visible:details.lessonDetails;Layout.fillWidth:true;Layout.minimumWidth:0;Layout.preferredWidth:parent.columns===2?details.width*.34:0;Layout.alignment:Qt.AlignTop;padding:16
            background:Surface {radius:Theme.fancy?18:6;backdrop:null;border.color:Theme.fancy?Theme.rim:Theme.separator}
            contentItem:ColumnLayout {spacing:9
                Label {text:app.sectionInfo.title||'';visible:text.length>0;Layout.fillWidth:true;wrapMode:Text.Wrap;textFormat:Text.PlainText;color:Theme.text;font.bold:true}
                Label {text:app.sectionInfo.schedule||'';Layout.fillWidth:true;wrapMode:Text.Wrap;textFormat:Text.PlainText;color:Theme.secondary;lineHeight:1.25}
            }
        }
    }
}
