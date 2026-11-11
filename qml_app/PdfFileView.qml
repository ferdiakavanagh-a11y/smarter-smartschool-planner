import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtQuick.Pdf
ColumnLayout {
    id:view
    required property url source
    property int page:0
    property real zoom:1
    property bool fitWidth:true
    property bool canSave:false
    signal saveRequested()
    property bool passwordNeeded:false
    property bool showText:false
    readonly property bool ready:pdf.status===PdfDocument.Ready
    readonly property int pageCount:pdf.pageCount
    readonly property int renderStatus:image.status
    readonly property size renderSize:image.sourceSize
    readonly property size pointSize:ready?pdf.pagePointSize(page):Qt.size(1,1)
    readonly property bool validPage:ready&&pointSize.width>0&&pointSize.height>0&&Number.isFinite(pointSize.width)&&Number.isFinite(pointSize.height)
    readonly property real fitScale:validPage?(fitWidth?Math.max(1,pan.width-24)/pointSize.width:Math.min(Math.max(1,pan.width-24)/pointSize.width,Math.max(1,pan.height-24)/pointSize.height)):1
    spacing:12
    function changePage(value){
        if(!ready)return
        page=Math.max(0,Math.min(pdf.pageCount-1,value))
        pan.cancelFlick();scrollMotion.stop();pan.contentX=0;pan.contentY=0
    }
    function changeZoom(value){
        let centerX=(pan.contentX+pan.width/2-image.x)/Math.max(1,image.width)
        let centerY=(pan.contentY+pan.height/2-image.y)/Math.max(1,image.height)
        zoom=Math.max(.5,Math.min(4,value))
        pan.cancelFlick();scrollMotion.stop()
        Qt.callLater(function(){
            pan.contentX=Math.max(0,Math.min(Math.max(0,pan.contentWidth-pan.width),image.x+image.width*centerX-pan.width/2))
            pan.contentY=Math.max(0,Math.min(Math.max(0,pan.contentHeight-pan.height),image.y+image.height*centerY-pan.height/2))
        })
    }
    function unlock(){pdf.password=password.text;password.text=''}
    onSourceChanged:{page=0;zoom=1;fitWidth=true;passwordNeeded=false;showText=false;pdf.password='';password.text=''}
    onPageChanged:if(showText)Qt.callLater(pageText.selectAll)
    PdfSelection {id:pageText;visible:false;document:pdf;page:view.page}
    PdfDocument {id:pdf;objectName:'pdfDocument';source:view.source
        onPasswordRequired:{view.passwordNeeded=true;Qt.callLater(function(){if(view.visible&&view.passwordNeeded)password.forceActiveFocus()})}
        onStatusChanged:if(status===PdfDocument.Ready){view.passwordNeeded=false;view.page=Math.min(view.page,Math.max(0,pageCount-1))}
    }
    ColumnLayout {Layout.fillWidth:true;visible:view.passwordNeeded;spacing:8
        Label {Layout.fillWidth:true;text:'A password is needed to open this PDF.';textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.text}
        RowLayout {Layout.fillWidth:true
            TextField {id:password;objectName:'pdfPassword';Layout.fillWidth:true;implicitHeight:44;echoMode:TextInput.Password
                Accessible.name:'PDF password';placeholderText:'PDF password';color:Theme.text;placeholderTextColor:Theme.secondary;selectByMouse:true
                onAccepted:if(text.length)view.unlock()
                background:Surface {radius:12}
            }
            Capsule {objectName:'pdfUnlock';text:'Open PDF';enabled:password.text.length>0;onClicked:view.unlock()}
        }
    }
    Item {id:pageArea;Layout.fillWidth:true;Layout.fillHeight:true
    Flickable {id:pan;objectName:'pdfViewport';anchors.fill:parent;clip:true
        visible:view.validPage&&!view.passwordNeeded&&!view.showText
        contentWidth:Math.max(width,image.width+24);contentHeight:Math.max(height,image.height+24)
        boundsBehavior:Flickable.StopAtBounds;acceptedButtons:Qt.LeftButton;activeFocusOnTab:true
        Accessible.role:Accessible.Pane;Accessible.name:'PDF page '+(view.page+1)+' of '+pdf.pageCount
        Accessible.description:'Use Previous and Next to browse pages, and the zoom controls to enlarge them.'
        ScrollBar.vertical:ScrollBar {}
        ScrollBar.horizontal:ScrollBar {}
        SmoothScroll {id:scrollMotion;view:pan}
        Keys.onPressed:event=>{
            if(event.key===Qt.Key_PageDown){view.changePage(view.page+1);event.accepted=true}
            else if(event.key===Qt.Key_PageUp){view.changePage(view.page-1);event.accepted=true}
        }
        Rectangle {x:image.x;y:image.y;width:image.width;height:image.height;color:'white'}
        PdfPageImage {id:image;objectName:'pdfPageImage';document:pdf;currentFrame:view.page;asynchronous:true;cache:false
            width:view.validPage?Math.max(1,view.pointSize.width*view.fitScale*view.zoom):1;height:view.validPage?Math.max(1,view.pointSize.height*view.fitScale*view.zoom):1
            x:(pan.contentWidth-width)/2;y:(pan.contentHeight-height)/2
            readonly property real rasterScale:Math.min(Math.max(1,Screen.devicePixelRatio),4096/Math.max(width,height,1))
            sourceSize:Qt.size(Math.min(4096,Math.max(1,Math.ceil(width*rasterScale))),Math.min(4096,Math.max(1,Math.ceil(height*rasterScale))))
            fillMode:Image.PreserveAspectFit
        }
    }
    // Status feedback must not resize the page and trigger a render/layout feedback loop.
    ScrollView {anchors.fill:parent;visible:view.showText&&view.ready
        TextArea {objectName:'pdfPageText';text:pageText.text||'This page has no selectable text.';textFormat:TextEdit.PlainText;readOnly:true;selectByMouse:true;wrapMode:TextEdit.Wrap;color:Theme.text;Accessible.name:'PDF page text'}
    }
    Label {anchors.centerIn:parent;width:parent.width-32;horizontalAlignment:Text.AlignHCenter;visible:!view.passwordNeeded&&(pdf.status===PdfDocument.Error||view.ready&&!view.validPage||!view.showText&&image.status===Image.Error)
        text:'This PDF page could not be displayed. Download the file again, or try another page.';textFormat:Text.PlainText;wrapMode:Text.Wrap;color:Theme.orange;padding:12
        background:Rectangle {color:Theme.elevated;radius:12}}
    Label {anchors.centerIn:parent;visible:!view.passwordNeeded&&(pdf.status===PdfDocument.Loading||!view.showText&&view.ready&&image.status===Image.Loading)
        text:'Loading PDF…';textFormat:Text.PlainText;color:Theme.secondary;padding:12
        background:Rectangle {color:Theme.elevated;radius:12}}
    }
    Item {objectName:'pdfToolbar';Layout.fillWidth:true;implicitHeight:toolbar.implicitHeight+16
        Surface {anchors.fill:parent;radius:22}
        Flow {id:toolbar;x:8;y:8;width:parent.width-16;spacing:12
            Row {spacing:8;visible:view.ready
                Capsule {objectName:'pdfPrevious';text:'Previous';visible:pdf.pageCount>1;enabled:view.page>0;onClicked:view.changePage(view.page-1)}
                Label {objectName:'pdfPageCount';anchors.verticalCenter:parent.verticalCenter;textFormat:Text.PlainText;text:'Page '+(view.page+1)+' of '+pdf.pageCount;color:Theme.text;font.pixelSize:13*Theme.textScale}
                Capsule {objectName:'pdfNext';text:'Next';visible:pdf.pageCount>1;enabled:view.page+1<pdf.pageCount;onClicked:view.changePage(view.page+1)}
            }
            Row {spacing:8;visible:view.ready
                Capsule {objectName:'pdfZoomOut';text:'−';Accessible.name:'Zoom out';enabled:!view.showText&&view.zoom>.5;onClicked:view.changeZoom(view.zoom/1.25)}
                Capsule {objectName:'pdfFit';text:view.fitWidth?'Fit page':'Page width';selectorMaterial:true;enabled:!view.showText
                    onClicked:{view.fitWidth=!view.fitWidth;view.changeZoom(1);Qt.callLater(function(){pan.contentX=0;pan.contentY=0})}}
                Capsule {objectName:'pdfZoomIn';text:'+';Accessible.name:'Zoom in';enabled:!view.showText&&view.zoom<4;onClicked:view.changeZoom(view.zoom*1.25)}
                Capsule {objectName:'pdfText';text:view.showText?'Page image':'Page text';selected:view.showText;onClicked:{view.showText=!view.showText;if(view.showText)pageText.selectAll()}}
            }
            Capsule {objectName:'pdfSave';text:'Save as';visible:view.canSave;onClicked:view.saveRequested()}
        }
    }
}
