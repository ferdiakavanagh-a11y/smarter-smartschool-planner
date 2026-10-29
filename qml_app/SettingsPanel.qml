// Local track lenses / press growth adapted from MacShell GlassSlider.qml and GlassSwitch.qml (MIT).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Sheet {
    id: panel
    required property var app
    required property var backdrop
    title: 'Settings'
    Label {textFormat:Text.PlainText; text: 'RENDERING'; color: Theme.secondary; font.pixelSize: 13; font.bold: true }
    LensBar { objectName: 'renderingPicker'; Layout.fillWidth: true; backdrop: panel.backdrop; labels: ['Fancy','Performance']; current: Theme.fancy ? 0 : 1; onPicked: i => {Theme.fancy=i===0;if(app.production)backend.chooseRendering(i===0?'fancy':'performance')} }
    Label {textFormat:Text.PlainText; Layout.fillWidth: true; wrapMode: Text.Wrap; text: Theme.fancy ? 'Full liquid lenses and an animated backdrop.' : 'The same colors, translucent glass and motion, with a static backdrop and lighter lenses.'; color: Theme.secondary }
    Label {textFormat:Text.PlainText; text: 'THEME'; color: Theme.secondary; font.pixelSize: 13; font.bold: true }
    LensBar { objectName: 'themePicker'; Layout.fillWidth: true; backdrop: panel.backdrop; labels: ['Vivid','Clear']; current: Theme.clear ? 1 : 0; onPicked: i => Theme.style=i===0 ? 'vivid' : 'clear' }
    Label {textFormat:Text.PlainText; text: 'MODE'; color: Theme.secondary; font.pixelSize: 13; font.bold: true }
    LensBar { objectName: 'schemePicker'; Layout.fillWidth: true; backdrop: panel.backdrop; labels: ['Auto','Light','Dark']; current: ['auto','light','dark'].indexOf(Theme.scheme); onPicked: i => Theme.scheme=['auto','light','dark'][i] }
    Label {textFormat:Text.PlainText; text: 'GLASS FROSTING'; color: Theme.secondary; font.pixelSize: 13; font.bold: true }
    GlassSlider { objectName:'glassSlider'; Layout.fillWidth:true; value:Theme.glassLevel; Accessible.name:'Liquid glass frosting'; Accessible.description:'From clear to frosted, independently of distortion.'; onMoved:Theme.glassLevel=value }
    RowLayout { Layout.fillWidth: true
        Label {textFormat:Text.PlainText;text:'Clear';color:Theme.secondary} Item {Layout.fillWidth:true} Label {textFormat:Text.PlainText;text:Math.round(Theme.glassLevel*100)+'%';color:Theme.secondary} Item {Layout.fillWidth:true} Label {textFormat:Text.PlainText;text:'Frosted';color:Theme.secondary}
    }
    Label {textFormat:Text.PlainText; text: 'DISTORTION'; color: Theme.secondary; font.pixelSize:13; font.bold:true }
    GlassSlider { objectName:'distortionSlider'; Layout.fillWidth:true; value:Theme.refractionLevel; Accessible.name:'Liquid glass distortion'; Accessible.description:'Changes lens refraction independently of frosting.'; onMoved:Theme.refractionLevel=value }
    RowLayout { Layout.fillWidth:true
        Label {textFormat:Text.PlainText;text:'None';color:Theme.secondary} Item {Layout.fillWidth:true} Label {textFormat:Text.PlainText;text:Math.round(Theme.refractionLevel*100)+'%';color:Theme.secondary} Item {Layout.fillWidth:true} Label {textFormat:Text.PlainText;text:'Strong';color:Theme.secondary}
    }
    Label {textFormat:Text.PlainText; text: 'BACKGROUND'; color: Theme.secondary; font.pixelSize: 13; font.bold: true }
    GlassComboBox { objectName: 'backgroundPicker'; Layout.fillWidth:true; model:['Satin','Soft colours','Tide','Dunes']; currentIndex:Theme.wallpaperIndex; Accessible.name:'Background'; onActivated:Theme.wallpaperIndex=currentIndex }
    Label {textFormat:Text.PlainText; text: 'TEXT SIZE'; color: Theme.secondary; font.pixelSize: 13; font.bold: true }
    LensBar { Layout.fillWidth: true; backdrop: panel.backdrop; labels: ['Small','Default','Large','135%']; current: Theme.textScale<1?0:Theme.textScale<1.1?1:Theme.textScale<1.3?2:3; onPicked: i => Theme.textScale=[.9,1,1.15,1.35][i] }
    Label {textFormat:Text.PlainText; text: 'ACCESSIBILITY'; color: Theme.secondary; font.pixelSize: 13; font.bold: true }
    Repeater {
        model: [{label:'Reduce motion',key:'reducedMotion'},{label:'Animated background (Fancy)',key:'animatedBackground'},{label:'High contrast',key:'highContrast'}]
        GlassSwitch {
            id: toggle; required property var modelData
            Layout.fillWidth: true; text: modelData.label; checked: Theme[modelData.key]
            Accessible.name: text; onToggled: Theme[modelData.key]=checked
        }
    }
    Label {textFormat:Text.PlainText;visible:app.production;text:'DATE CHECKER';color:Theme.secondary;font.bold:true}
    GlassSwitch {id:dateToggle;objectName:'dateCheckerSwitch';visible:app.production;Layout.fillWidth:true;text:'AI date checking'
        checked:app.production&&backend.checkerState.mode==='gemini'
        enabled:app.production&&(backend.checkerState.geminiAvailable||checked)
        onToggled:{backend.setDateChecker(checked?'gemini':'local');checked=Qt.binding(function(){return app.production&&backend.checkerState.mode==='gemini'})}
    }
    Label {textFormat:Text.PlainText;visible:app.production;Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.secondary
        text:dateToggle.checked?'Gemini checks assignment dates during sync. Verify dates marked with the sparkle icon.':app.production&&backend.checkerState.geminiAvailable?'Local date checking. Turn on to use Gemini during sync.':'Local date checking. Add a Gemini API key in login details to enable AI.'
    }
    Label {textFormat:Text.PlainText;visible:app.production;text:'ACCOUNT';color:Theme.secondary;font.bold:true}
    Label {textFormat:Text.PlainText;visible:app.production;text:app.production?backend.school:'';Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.text}
    Capsule {visible:app.production;text:'Change login details';enabled:!app.busy;onClicked:app.changeAccount()}
    Capsule {visible:app.production;text:'Copy sync diagnostics';onClicked:if(backend.copyDiagnostics())app.notify('Diagnostics copied')}
    Label {textFormat:Text.PlainText;visible:app.production;text:'Sync uses the selected date checker. Notes, pins and completed tasks are saved on this computer.';Layout.fillWidth:true;wrapMode:Text.Wrap;color:Theme.secondary}
    ColumnLayout {visible:!app.production;Layout.fillWidth:true
        Label {textFormat:Text.PlainText;text:'SYNTHETIC WORKSPACE';color:Theme.secondary}
        GlassComboBox {objectName:'datasetPicker';Layout.fillWidth:true;model:['Empty','Typical · 36 tasks','Stress · 1,000 tasks'];currentIndex:app.datasetIndex;onActivated:{app.datasetIndex=currentIndex;tasks.dataset([0,36,1000][currentIndex]);app.fixtureRevision++}}
    }
}
