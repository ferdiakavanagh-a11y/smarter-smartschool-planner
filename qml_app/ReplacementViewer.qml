import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtWebEngine
ColumnLayout {
    id:viewer
    property var service:null
    property string viewerError:''
    property bool awaitingPresentation:false
    property int presentationRevision:0
    function fail(message){presentationRevision++;awaitingPresentation=false;loadDeadline.stop();viewerError=message}
    function start(features){
        service=features
        service.configureReplacementProfile(privateProfile)
        service.loadReplacement()
    }
    WebEngineProfile {id:privateProfile;offTheRecord:true;httpCacheType:WebEngineProfile.MemoryHttpCache;persistentCookiesPolicy:WebEngineProfile.NoPersistentCookies}
    RowLayout {Layout.fillWidth:true
        Label {Layout.fillWidth:true;textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.secondary
            text:viewer.service&&viewer.service.replacementLoading?'Fetching the current presentation…':viewer.service&&viewer.service.replacementError?viewer.service.replacementError:viewer.viewerError||(viewer.awaitingPresentation?'Opening the presentation…':'Current presentation · Smartschool / Microsoft PowerPoint')}
        Capsule {text:'Refresh';symbol:'retry';enabled:!!viewer.service&&!viewer.service.featureBusy
            onClicked:{viewer.presentationRevision++;viewer.awaitingPresentation=false;loadDeadline.stop();web.stop();web.url='about:blank';viewer.viewerError='';viewer.service.loadReplacement()}}
    }
    Timer {id:loadDeadline;interval:45000;onTriggered:viewer.fail('The presentation did not finish opening. Press Refresh to fetch a fresh copy and retry.')}
    Timer {interval:500;repeat:true;running:viewer.awaitingPresentation
        onTriggered:{
            let revision=viewer.presentationRevision
            web.runJavaScript('window.__plannerPresentationReady === true',function(ready){
                if(ready&&viewer.awaitingPresentation&&revision===viewer.presentationRevision){viewer.awaitingPresentation=false;loadDeadline.stop();viewer.viewerError=''}
            })
        }
    }
    WebEngineView {
        id:web;objectName:'replacementWebView';Layout.fillWidth:true;Layout.fillHeight:true
        profile:privateProfile;backgroundColor:Theme.bg;audioMuted:true
        settings.pluginsEnabled:false
        settings.javascriptCanOpenWindows:false
        settings.localContentCanAccessFileUrls:false
        settings.localContentCanAccessRemoteUrls:false
        settings.fullScreenSupportEnabled:false
        onJavaScriptConsoleMessage:(level,message,line,source)=>{}
        onNewWindowRequested:request=>{}
        onContextMenuRequested:request=>{request.accepted=true}
        onFileDialogRequested:request=>{request.accepted=true;request.dialogReject()}
        onAuthenticationDialogRequested:request=>{request.accepted=true;request.dialogReject()}
        onJavaScriptDialogRequested:request=>{request.accepted=true;request.dialogReject()}
        onPermissionRequested:permission=>permission.deny()
        onCertificateError:error=>error.rejectCertificate()
        onRenderProcessTerminated:()=>viewer.fail('The presentation viewer stopped. Press Refresh to retry.')
        onLoadingChanged:info=>{if(info.status===WebEngineView.LoadFailedStatus)viewer.fail('The presentation could not load. Press Refresh to retry.')}
        Accessible.name:'Teacher replacement presentation'
    }
    Connections {target:viewer.service
        function onReplacementReady(html,base){viewer.presentationRevision++;viewer.viewerError='';viewer.awaitingPresentation=true;loadDeadline.restart();web.loadHtml(html,base)}
        function onChanged(){if(viewer.service&&!viewer.service.accountKey){web.stop();web.url='about:blank'}}
    }
    Component.onDestruction:if(viewer.service)viewer.service.closeReplacement()
}
