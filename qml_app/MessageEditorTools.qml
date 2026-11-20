import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: tools
    required property var editor
    required property var service
    signal edited()
    spacing:0
    enabled:!!service&&!service.sending&&!service.deliveryLocked
    function format(action,value){service.formatting.apply(editor.textDocument,editor.selectionStart,editor.selectionEnd,action,value||'');edited();editor.forceActiveFocus()}
    component FormatButton: ToolButton {
        id:formatControl
        property string command:''
        property string symbol:''
        property string value:''
        property string description:text
        implicitHeight:32*Theme.textScale; implicitWidth:34*Theme.textScale; focusPolicy:Qt.NoFocus
        Accessible.name:description; GlassToolTip {requested:formatControl.hovered||formatControl.visualFocus;text:formatControl.description}
        contentItem:Item {Label {anchors.fill:parent;visible:!formatControl.symbol;text:formatControl.text;color:Theme.text;font.pixelSize:17*Theme.textScale;horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter} Icon {anchors.centerIn:parent;visible:!!formatControl.symbol;name:formatControl.symbol;ink:Theme.text}}
        onClicked:tools.format(command,value)
    }
    Rectangle {Layout.fillWidth:true;implicitHeight:32*Theme.textScale;color:Theme.fill;border.color:Theme.separator
        RowLayout {anchors.fill:parent;spacing:0
            ToolButton {text:I18n.t('Bewerken');onClicked:editMenu.open();PlannerMenu {id:editMenu
                PlannerMenuItem {text:I18n.t('Ongedaan maken');enabled:tools.editor.canUndo;onTriggered:{tools.editor.undo();tools.edited()}}
                PlannerMenuItem {text:I18n.t('Opnieuw');enabled:tools.editor.canRedo;onTriggered:{tools.editor.redo();tools.edited()}}
                PlannerMenuItem {text:I18n.t('Kopiëren');onTriggered:tools.editor.copy()}
                PlannerMenuItem {text:I18n.t('Plakken');onTriggered:tools.editor.pasteSanitized()}
                PlannerMenuItem {text:I18n.t('Alles selecteren');onTriggered:tools.editor.selectAll()}}}
            ToolButton {text:I18n.t('Opmaak');onClicked:formatMenu.open();PlannerMenu {id:formatMenu
                PlannerMenuItem {text:I18n.t('Vet');onTriggered:tools.format('bold')}
                PlannerMenuItem {text:I18n.t('Cursief');onTriggered:tools.format('italic')}
                PlannerMenuItem {text:I18n.t('Onderstrepen');onTriggered:tools.format('underline')}
                PlannerMenuItem {text:I18n.t('Opmaak wissen');onTriggered:tools.format('clear')}}}
            ToolButton {text:I18n.t('Tabel');onClicked:tableMenu.open();PlannerMenu {id:tableMenu;PlannerMenuItem {text:I18n.t('Tabel invoegen (2 × 2)');onTriggered:tools.format('table')}}}
            ToolButton {text:I18n.t('Invoegen');onClicked:insertMenu.open();PlannerMenu {id:insertMenu
                PlannerMenuItem {text:I18n.t('Link');onTriggered:linkDialog.open()}
                PlannerMenuItem {text:I18n.t('Datum');onTriggered:{tools.editor.insert(tools.editor.cursorPosition,Qt.formatDate(new Date(),'dd/MM/yyyy'));tools.edited()}}
                PlannerMenuItem {text:'☺';onTriggered:{tools.editor.insert(tools.editor.cursorPosition,'☺');tools.edited()}}}}
            ToolButton {text:I18n.t('Beeld');onClicked:viewMenu.open();PlannerMenu {id:viewMenu
                PlannerMenuItem {text:I18n.t('Tekst vergroten');onTriggered:tools.editor.font.pixelSize=Math.min(32,tools.editor.font.pixelSize+2)}
                PlannerMenuItem {text:I18n.t('Tekst verkleinen');onTriggered:tools.editor.font.pixelSize=Math.max(10,tools.editor.font.pixelSize-2)}}}
            Item {Layout.fillWidth:true}
        }
    }
    Rectangle {Layout.fillWidth:true;implicitHeight:fontTools.implicitHeight;color:Theme.fill;border.color:Theme.separator
        Flow {id:fontTools;width:parent.width;spacing:0
            GlassComboBox {width:145*Theme.textScale;height:36*Theme.textScale;model:['Open Sans','Arial','Georgia','Courier New'];Accessible.name:I18n.t('Lettertype');onActivated:tools.format('font',currentText)}
            GlassComboBox {width:80*Theme.textScale;height:36*Theme.textScale;model:['10','12','14','16','18','24'];currentIndex:2;Accessible.name:I18n.t('Tekstgrootte');onActivated:tools.format('size',currentText)}
            FormatButton {text:'B';command:'bold';description:I18n.t('Vet')}
            FormatButton {text:'I';command:'italic';description:I18n.t('Cursief')}
            FormatButton {text:'U';command:'underline';description:I18n.t('Onderstrepen')}
            FormatButton {text:'A';command:'color';value:'#234b86';description:I18n.t('Tekstkleur blauw')}
            ToolButton {implicitHeight:32*Theme.textScale;contentItem:Item {Icon {anchors.centerIn:parent;name:'link'}} Accessible.name:I18n.t('Link invoegen');onClicked:linkDialog.open()}
            FormatButton {symbol:'unlink';command:'unlink';description:I18n.t('Link verwijderen')}
            ToolButton {implicitHeight:32*Theme.textScale;contentItem:Item {Icon {anchors.centerIn:parent;name:'smile'}} Accessible.name:I18n.t('Glimlach invoegen');onClicked:{tools.editor.insert(tools.editor.cursorPosition,'☺');tools.edited()}}
        }
    }
    Rectangle {Layout.fillWidth:true;implicitHeight:34*Theme.textScale;color:Theme.fill;border.color:Theme.separator
        Row {anchors.fill:parent
            FormatButton {symbol:'alignLeft';command:'left';description:I18n.t('Links uitlijnen')}
            FormatButton {symbol:'alignCenter';command:'center';description:I18n.t('Centreren')}
            FormatButton {symbol:'alignRight';command:'right';description:I18n.t('Rechts uitlijnen')}
            FormatButton {symbol:'justify';command:'justify';description:I18n.t('Uitvullen')}
            FormatButton {symbol:'indent';command:'indent';description:I18n.t('Inspringen')}
            FormatButton {symbol:'outdent';command:'outdent';description:I18n.t('Uitspringen')}
            FormatButton {symbol:'bullets';command:'bullets';description:I18n.t('Opsomming')}
            FormatButton {symbol:'numbers';command:'numbers';description:I18n.t('Genummerde lijst')}
        }
    }
    Dialog {id:linkDialog;title:I18n.t('Link invoegen');modal:true;focus:true
        padding:14
        background:Rectangle {color:Theme.elevated;border.color:Theme.separator;radius:8}
        header:Label {text:linkDialog.title;padding:14;color:Theme.text;font.bold:true}
        footer:DialogButtonBox {
            background:Rectangle {color:Theme.elevated;radius:8}
            Capsule {text:I18n.p('Cancel','Annuleren');DialogButtonBox.buttonRole:DialogButtonBox.RejectRole}
            Capsule {text:I18n.p('Insert link','Link invoegen');primary:true;DialogButtonBox.buttonRole:DialogButtonBox.AcceptRole}
        }
        TextField {
            id:link;placeholderText:'https://';Accessible.name:I18n.t('Linkadres');selectByMouse:true
            color:Theme.text;placeholderTextColor:Theme.secondary
            background:Rectangle {radius:5;color:Theme.fill;border.color:link.activeFocus?Theme.blue:Theme.separator}
        }
        onAccepted:tools.format('link',link.text)
    }
}
