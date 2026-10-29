import QtQuick
WheelHandler {
    id: wheel
    required property Flickable view
    property bool horizontal: false
    property int edge: 0
    parent: view
    target: null
    acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
    enabled: view.visible && Theme.active
    onEnabledChanged: if (!enabled) stop()
    function stop() { glide.stop(); edge=0 }
    function settleEdge() {
        // Virtualized lists can revise origin/content size while the wheel is moving.
        if (!edge) return
        if (!horizontal && view.positionViewAtBeginning) {
            if (edge<0) view.positionViewAtBeginning()
            else { view.positionViewAtEnd(); view.contentY+=view.bottomMargin }
        } else {
            let start=horizontal?view.originX-view.leftMargin:view.originY-view.topMargin
            let end=horizontal?view.originX+view.contentWidth-view.width+view.rightMargin:view.originY+view.contentHeight-view.height+view.bottomMargin
            view[horizontal?'contentX':'contentY']=edge<0?start:Math.max(start,end)
        }
    }
    property NumberAnimation glide: NumberAnimation {
        target: wheel.view; property: wheel.horizontal ? 'contentX' : 'contentY'
        duration: 180; easing.type: Easing.OutCubic
        onFinished: wheel.settleEdge()
    }
    property PointHandler press: PointHandler {
        parent: wheel.view
        onActiveChanged: if (active) wheel.stop()
    }
    property Connections interruption: Connections {
        target: wheel.view; ignoreUnknownSignals: true
        function onDraggingChanged() { if (wheel.view.dragging) wheel.stop() }
        function onCurrentIndexChanged() { wheel.stop() }
        function onCountChanged() { wheel.stop() }
        function onModelChanged() { wheel.stop() }
        function onHeightChanged() { if (!wheel.glide.running) wheel.settleEdge() }
        function onContentHeightChanged() { if (!wheel.glide.running && wheel.edge) Qt.callLater(wheel.settleEdge) }
    }
    property Connections motion: Connections {
        target: Theme
        function onReducedMotionChanged() { wheel.stop() }
    }
    onWheel: event => {
        let pixel = horizontal ? (event.pixelDelta.x || event.pixelDelta.y) : event.pixelDelta.y
        let angle = horizontal ? (event.angleDelta.x || event.angleDelta.y) : event.angleDelta.y
        if ((!pixel && !angle) || event.modifiers & Qt.ControlModifier) { event.accepted=false; return }
        let key=horizontal?'contentX':'contentY', current=view[key]
        let start=horizontal?view.originX-view.leftMargin:view.originY-view.topMargin
        let end=Math.max(start,horizontal?view.originX+view.contentWidth-view.width+view.rightMargin:view.originY+view.contentHeight-view.height+view.bottomMargin)
        let delta=pixel || angle/120*72*Theme.textScale
        // Repeated notches accumulate; reversing direction immediately discards pending travel.
        let base=glide.running && (glide.to-current)*delta<0 ? glide.to : current
        stop(); view.cancelFlick()
        let next=Math.max(start,Math.min(end,(pixel?current:base)-delta))
        edge=next<=start?-1:next>=end?1:0
        if (pixel || !Theme.motion) { view[key]=next; settleEdge() }
        else { glide.from=current; glide.to=next; glide.start() }
        event.accepted=true
    }
}
