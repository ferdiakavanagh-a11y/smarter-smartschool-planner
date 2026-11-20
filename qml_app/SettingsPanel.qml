// Local track lenses / press growth adapted from MacShell GlassSlider.qml and GlassSwitch.qml (MIT).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Sheet {
    id: panel
    required property var app
    required property var backdrop
    title:I18n.t(Theme.fancy?'Settings':'Instellingen')
    width:Math.min((Theme.fancy?560:760)*Theme.textScale,parent.width-28)
    Label {text:I18n.p('LANGUAGE','TAAL');color:Theme.secondary;font.bold:true;Layout.topMargin:6}
    LensBar {objectName:'languagePicker';backdrop:panel.backdrop;Layout.fillWidth:true;labels:['English','Nederlands'];current:I18n.language==='nl'?1:0;onPicked:i=>I18n.language=i===1?'nl':'en'}
    GridLayout {columns:!Theme.fancy&&panel.width>650?2:1;Layout.fillWidth:true;columnSpacing:18;rowSpacing:18
    GroupBox {Layout.fillWidth:true;Layout.alignment:Qt.AlignTop;title:I18n.t(Theme.fancy?'Appearance':'Weergave en leesbaarheid');padding:20
        background:Rectangle {objectName:'settingsGroupBackground';color:Theme.fancy&&!Theme.highContrast?'transparent':Theme.elevated;border.color:Theme.fancy&&!Theme.highContrast?Theme.alpha(Theme.text,.12):Theme.separator;radius:8}
        label:Label {text:parent.title;color:Theme.text;font.pixelSize:12*Theme.textScale;font.bold:true;x:12;y:0}
        ColumnLayout {width:parent.width;spacing:16
    Label {textFormat:Text.PlainText; text:I18n.t(Theme.fancy?'RENDERING':'WEERGAVE'); color: Theme.secondary; font.pixelSize: 13; font.bold: true }
    LensBar { objectName: 'renderingPicker'; Layout.fillWidth: true; backdrop: panel.backdrop; labels:(['Liquid Glass','Smartschool']).map(value=>I18n.t(value)); current: Theme.fancy ? 0 : 1; onPicked: i => {Theme.fancy=i===0;if(app.production)backend.chooseRendering(i===0?'fancy':'performance')} }
    Label {textFormat:Text.PlainText; Layout.fillWidth: true; wrapMode: Text.Wrap; text:I18n.t(Theme.fancy ? 'Full liquid lenses and an animated backdrop.' : 'Compacte werkruimte met dekkende panelen en een koperkleurig accent.'); color: Theme.secondary }
    Label {visible:Theme.fancy;textFormat:Text.PlainText; text:I18n.t('THEME'); color: Theme.secondary; font.pixelSize: 13; font.bold: true }
    LensBar { objectName: 'themePicker'; visible:Theme.fancy; Layout.fillWidth: true; backdrop: panel.backdrop; labels:(['Vivid','Clear']).map(value=>I18n.t(value)); current: Theme.clear ? 1 : 0; onPicked: i => Theme.style=i===0 ? 'vivid' : 'clear' }
    Label {textFormat:Text.PlainText; text:I18n.t(Theme.fancy?'MODE':'KLEURMODUS'); color: Theme.secondary; font.pixelSize: 13; font.bold: true }
    LensBar { objectName: 'schemePicker'; Layout.fillWidth: true; backdrop: panel.backdrop; labels:(Theme.fancy?['Auto','Light','Dark']:['Automatisch','Licht','Donker']).map(value=>I18n.t(value)); current: ['auto','light','dark'].indexOf(Theme.scheme); onPicked: i => Theme.scheme=['auto','light','dark'][i] }
    Label {visible:Theme.fancy;textFormat:Text.PlainText; text:I18n.t('GLASS FROSTING'); color: Theme.secondary; font.pixelSize: 13; font.bold: true }
    GlassSlider { objectName:'glassSlider';visible:Theme.fancy; Layout.fillWidth:true; value:Theme.glassLevel; Accessible.name:I18n.t('Liquid glass frosting'); Accessible.description:I18n.t('From clear to frosted, independently of distortion.'); onMoved:Theme.glassLevel=value }
    RowLayout { visible:Theme.fancy; Layout.fillWidth: true
        Label {textFormat:Text.PlainText;text:I18n.t('Clear');color:Theme.secondary} Item {Layout.fillWidth:true} Label {textFormat:Text.PlainText;text:I18n.t(Math.round(Theme.glassLevel*100)+'%');color:Theme.secondary} Item {Layout.fillWidth:true} Label {textFormat:Text.PlainText;text:I18n.t('Frosted');color:Theme.secondary}
    }
    Label {visible:Theme.fancy;textFormat:Text.PlainText; text:I18n.t('DISTORTION'); color: Theme.secondary; font.pixelSize:13; font.bold:true }
    GlassSlider { objectName:'distortionSlider';visible:Theme.fancy; Layout.fillWidth:true; value:Theme.refractionLevel; Accessible.name:I18n.t('Liquid glass distortion'); Accessible.description:I18n.t('Changes lens refraction independently of frosting.'); onMoved:Theme.refractionLevel=value }
    RowLayout { visible:Theme.fancy; Layout.fillWidth:true
        Label {textFormat:Text.PlainText;text:I18n.t('None');color:Theme.secondary} Item {Layout.fillWidth:true} Label {textFormat:Text.PlainText;text:I18n.t(Math.round(Theme.refractionLevel*100)+'%');color:Theme.secondary} Item {Layout.fillWidth:true} Label {textFormat:Text.PlainText;text:I18n.t('Strong');color:Theme.secondary}
    }
    Label {visible:Theme.fancy;textFormat:Text.PlainText; text:I18n.t('BACKGROUND'); color: Theme.secondary; font.pixelSize: 13; font.bold: true }
    GlassComboBox { objectName: 'backgroundPicker';visible:Theme.fancy; Layout.fillWidth:true; model:['Silk','Soft colours','Aurora','Contour'].map(value=>I18n.t(value)); currentIndex:Theme.wallpaperIndex; Accessible.name:I18n.t('Background'); onActivated:Theme.wallpaperIndex=currentIndex }
    Label {textFormat:Text.PlainText; text:I18n.t(Theme.fancy?'TEXT SIZE':'TEKSTGROOTTE'); color: Theme.secondary; font.pixelSize: 13; font.bold: true }
    LensBar { Layout.fillWidth: true; backdrop: panel.backdrop; labels:(Theme.fancy?['Small','Default','Large','135%']:['Klein','Normaal','Groot','135%']).map(value=>I18n.t(value)); current: Theme.textScale<1?0:Theme.textScale<1.1?1:Theme.textScale<1.3?2:3; onPicked: i => Theme.textScale=[.9,1,1.15,1.35][i] }
        }
    }
    GroupBox {id:accessGroup;Layout.fillWidth:true;Layout.alignment:Qt.AlignTop;title:I18n.t(Theme.fancy?'Accessibility':'Toegankelijkheid');padding:20
        background:Rectangle {objectName:'settingsGroupBackground';color:Theme.fancy&&!Theme.highContrast?'transparent':Theme.elevated;border.color:Theme.fancy&&!Theme.highContrast?Theme.alpha(Theme.text,.12):Theme.separator;radius:8}
        label:Label {text:parent.title;color:Theme.text;font.pixelSize:12*Theme.textScale;font.bold:true;x:12;y:0}
        ColumnLayout {width:parent.width;spacing:8
    Label {textFormat:Text.PlainText; visible:Theme.fancy;text:I18n.t('ACCESSIBILITY'); color: Theme.secondary; font.pixelSize: 13; font.bold: true }
    Repeater {
        model: [{label:'Reduce motion',key:'reducedMotion'},{label:'Animated background (Liquid Glass)',key:'animatedBackground'},{label:'High contrast',key:'highContrast'}]
        GlassSwitch {
            id: toggle; required property var modelData
            visible:Theme.fancy||modelData.key!=='animatedBackground';Layout.fillWidth: true; text:I18n.t(Theme.fancy?modelData.label:({'reducedMotion':'Minder beweging','animatedBackground':'Bewegende achtergrond','highContrast':'Hoog contrast'})[modelData.key]); checked: Theme[modelData.key]
            Accessible.name: text; onToggled: Theme[modelData.key]=checked
        }
    }
        }
    }
    }
    GroupBox {visible:app.production;Layout.fillWidth:true;title:I18n.t(Theme.fancy?'Account':'Account en bestanden');padding:20
        background:Rectangle {objectName:'settingsGroupBackground';color:Theme.fancy&&!Theme.highContrast?'transparent':Theme.elevated;border.color:Theme.fancy&&!Theme.highContrast?Theme.alpha(Theme.text,.12):Theme.separator;radius:8}
        label:Label {text:parent.title;color:Theme.text;font.pixelSize:12*Theme.textScale;font.bold:true;x:12;y:0}
        ColumnLayout {width:parent.width;spacing:8
    Label {id:accountHeading;textFormat:Text.PlainText;visible:app.production;text:I18n.t(Theme.fancy?'DATE CHECKER':'DATUMCONTROLE');color:Theme.secondary;font.bold:true}
    GlassSwitch {id:dateToggle;objectName:'dateCheckerSwitch';visible:app.production;Layout.fillWidth:true;text:I18n.t(Theme.fancy?'AI date checking':'Datums controleren met AI')
        checked:app.production&&backend.checkerState.mode==='gemini'
        enabled:app.production&&(backend.checkerState.geminiAvailable||checked)
        onToggled:{backend.setDateChecker(checked?'gemini':'local');checked=Qt.binding(function(){return app.production&&backend.checkerState.mode==='gemini'})}
    }
    Label {textFormat:Text.PlainText;visible:app.production;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.secondary
        text:I18n.t(!Theme.fancy?(dateToggle.checked?'Gemini controleert datums tijdens synchronisatie. Controleer datums met het sterretje.':app.production&&backend.checkerState.geminiAvailable?'Lokale datumcontrole. Schakel AI in om Gemini te gebruiken.':'Lokale datumcontrole. Voeg een Gemini API-sleutel toe bij de aanmeldgegevens.'):dateToggle.checked?'Gemini checks assignment dates during sync. Verify dates marked with the sparkle icon.':app.production&&backend.checkerState.geminiAvailable?'Local date checking. Turn on to use Gemini during sync.':'Local date checking. Add a Gemini API key in login details to enable AI.')
    }
    Label {textFormat:Text.PlainText;visible:app.production;text:I18n.t('ACCOUNT');color:Theme.secondary;font.bold:true}
    Capsule {objectName:'offlineFilesButton';visible:app.production;text:I18n.t(Theme.fancy?'Offline files':'Offline bestanden');symbol:'file';onClicked:app.showOfflineFiles()}
    Label {textFormat:Text.PlainText;visible:app.production;text:app.production?backend.school:'';Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text}
    Capsule {visible:app.production;text:I18n.t(Theme.fancy?'Change login details':'Aanmeldgegevens wijzigen');enabled:!app.busy;onClicked:app.changeAccount()}
    Capsule {visible:app.production;text:I18n.t(Theme.fancy?'Copy sync diagnostics':'Diagnose synchronisatie kopiëren');onClicked:if(backend.copyDiagnostics())app.notify('Diagnostics copied')}
    Label {textFormat:Text.PlainText;visible:app.production;text:I18n.t(Theme.fancy?'Sync uses the selected date checker. Notes, pins and completed tasks are saved on this computer.':'Synchronisatie gebruikt de gekozen datumcontrole. Notities, vastgezette en voltooide taken worden op deze computer bewaard.');Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.secondary}
        }
    }
    ColumnLayout {visible:!app.production;Layout.fillWidth:true
        Label {textFormat:Text.PlainText;text:I18n.t('SYNTHETIC WORKSPACE');color:Theme.secondary}
        GlassComboBox {objectName:'datasetPicker';Layout.fillWidth:true;model:['Empty','Typical · 36 tasks','Stress · 1,000 tasks'].map(value=>I18n.t(value));currentIndex:app.datasetIndex;onActivated:{app.datasetIndex=currentIndex;tasks.dataset([0,36,1000][currentIndex]);app.fixtureRevision++}}
    }
}
