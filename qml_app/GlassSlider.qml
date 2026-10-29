// Lens knob and track adapted from MacShell GlassSlider.qml (MIT).
import QtQuick
import QtQuick.Controls
Slider {
    id: glassSlider
    implicitHeight:44; from:0; to:1; stepSize:0; snapMode:Slider.NoSnap
    // MacShell's knob bends its own track and grows while held; native Slider keeps keyboard/drag behavior.
    background: Item {id:sliderTrack;x:glassSlider.leftPadding;y:0;width:glassSlider.availableWidth;height:glassSlider.height
        Rectangle {y:(parent.height-height)/2;width:parent.width;height:6;radius:3
        gradient: Gradient { orientation: Gradient.Horizontal; GradientStop {position:0;color:Theme.teal} GradientStop {position:.5;color:Theme.blue} GradientStop {position:1;color:Theme.purple} } }
    }
    ShaderEffectSource {id:sliderSource;x:sliderTrack.x;y:sliderTrack.y;width:sliderTrack.width;height:sliderTrack.height;sourceItem:glassSlider.visible&&Theme.active?sliderTrack:null;visible:false;live:glassSlider.visible&&Theme.active;mipmap:true;smooth:true}
    handle: Item { x: glassSlider.leftPadding+glassSlider.visualPosition*(glassSlider.availableWidth-width); y:(glassSlider.height-height)/2; implicitWidth:32+10*pressT; implicitHeight:26+6*pressT
        property real pressT:glassSlider.pressed&&Theme.motion?1:0
        Behavior on pressT{enabled:Theme.motion;NumberAnimation{duration:glassSlider.pressed?140:240;easing.type:Easing.OutCubic}}
        SelectorLens {anchors.fill:parent;backdrop:sliderSource;radius:9+parent.pressT*3;fancy:Theme.fancy}
        Rectangle {anchors.fill:parent;radius:10;color:'transparent';border.color:glassSlider.visualFocus?Theme.text:'transparent';border.width:2}
    }
}
