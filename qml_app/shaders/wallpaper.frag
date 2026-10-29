#version 440
layout(location=0) in vec2 qt_TexCoord0;
layout(location=0) out vec4 fragColor;
layout(std140,binding=0) uniform buf {
    mat4 qt_Matrix; float qt_Opacity; float phase;
    vec4 base; vec4 blue; vec4 purple; vec4 teal; vec4 warm; vec4 pink; float dark;
    float preset;
};
float blob(vec2 p,vec2 c,float radius){vec2 d=(p-c)/radius;return exp(-dot(d,d)*2.8);}
vec3 pigment(vec3 color){return mix(mix(base.rgb,color,.57),color*.24+base.rgb*.65,dark);}
// Analytic folds: broad reflected light, a soft contact shadow and an antialiased lip.
vec3 fold(vec3 behind,float d,vec3 body,vec3 light,float breadth){
    float aa=max(fwidth(d),.0008);
    float mask=smoothstep(-aa,aa,d);
    behind*=1.0-.30*exp(-abs(d)/.025)*(1.0-mask);
    vec3 face=mix(body,light,exp(-max(d,0.0)/breadth)*.72);
    face+=light*exp(-pow((d-.10)/.19,2.0))*.09;
    vec3 result=mix(behind,face,mask);
    return result+light*exp(-abs(d)/max(aa*1.4,.0012))*.20;
}
void main(){
    vec2 p=qt_TexCoord0;
    vec2 drift=vec2(sin(phase),cos(phase))*.045;
    vec3 c=base.rgb;
    if(preset>.5 && preset<1.5){
        // Soft colours follows the five blurred colour fields in the original HTML UI.
        float soft=step(.5,preset);
        float amount=mix(.28,.48,soft);
        vec3 glow=blue.rgb*blob(p,vec2(.03,.10)+drift,.52)
            +purple.rgb*blob(p,vec2(.98,.28)-drift,.48)
            +teal.rgb*blob(p,vec2(.36,1.0)-drift.yx,.50)
            +warm.rgb*blob(p,vec2(.82,.94)+drift,.42)
            +pink.rgb*blob(p,vec2(.53,.53)+drift.yx,.32)*mix(.08,.6,soft);
        if(dark>.5) c+=glow*amount;
        else {
            c=mix(c,blue.rgb,blob(p,vec2(.03,.2)+drift,.52)*.62);
            c=mix(c,purple.rgb,blob(p,vec2(.98,.3)-drift,.48)*.52);
            c=mix(c,teal.rgb,blob(p,vec2(.3,1.0)-drift.yx,.50)*.55);
            c=mix(c,warm.rgb,blob(p,vec2(.84,.94)+drift,.42)*.5);
            c=mix(c,pink.rgb,blob(p,vec2(.53,.53)+drift.yx,.32)*soft*.55);
        }
    }else{
        vec2 q=p+vec2(sin(phase),cos(phase)-1.0)*.012;
        if(preset<.5){
            // Satin: quiet indigo sheets converging below the lower-left corner.
            vec3 body=mix(vec3(.52,.62,.76),vec3(.065,.074,.13),dark);
            vec3 light=mix(vec3(.96,.98,1.0),vec3(.28,.31,.47),dark);
            c=mix(vec3(.85,.90,.96),vec3(.045,.048,.085),dark);
            float bend=.40*sin(q.y*3.14159);
            c=fold(c,q.x-((1.0-q.y)*.22+bend),body,light,.30);
            c=fold(c,q.x-((1.0-q.y)*.83+bend),body*.84,light*.88,.24);
            c=fold(c,q.x-((1.0-q.y)*1.55+bend),body*.94,light,.27);
        }else if(preset<2.5){
            // Tide: translucent blue crests, with a pale horizon in light mode.
            c=mix(mix(vec3(.37,.72,.91),vec3(.92,.94,.84),smoothstep(.0,.75,q.y)),
                  mix(vec3(.025,.08,.16),vec3(.055,.17,.23),q.y),dark);
            vec3 body=mix(vec3(.29,.58,.80),vec3(.025,.085,.17),dark);
            vec3 light=mix(vec3(.82,.98,1.0),vec3(.10,.36,.49),dark);
            float wave=.60-.24*q.x+.13*sin(q.x*4.0-.55);
            c=fold(c,q.y-wave,body,light,.19);
            c=fold(c,q.y-(wave+.22+.09*cos(q.x*3.0)),body*.86,light*.83,.15);
            c=fold(c,q.y-(.98-.32*q.x+.12*sin(q.x*4.0+1.0)),body*.96,light,.14);
        }else{
            // Dunes: warm pearl and mauve, lit like a softly folded sheet.
            c=mix(vec3(.93,.87,.85),vec3(.085,.061,.10),dark);
            vec3 body=mix(vec3(.76,.62,.65),vec3(.12,.075,.135),dark);
            vec3 light=mix(vec3(1.0,.96,.86),vec3(.36,.22,.32),dark);
            float sweep=q.y+.42*q.x+.15*sin(q.x*3.3);
            c=fold(c,sweep-.46,body,light,.24);
            c=fold(c,sweep-.83,body*.90,light*.92,.25);
            c=fold(c,sweep-1.20,body*.86,light,.21);
        }
        // Static sub-pixel dither prevents banding without visible texture or temporal noise.
        float noise=fract(sin(dot(floor(p*vec2(1200,800)),vec2(12.9898,78.233)))*43758.5453)-.5;
        c+=noise/255.0;
    }
    c*=1.0-.16*dark*blob(vec2(p.x,p.y*2.5),vec2(.5,2.35),.52);
    fragColor=vec4(c,1.0)*qt_Opacity;
}
