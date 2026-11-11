#version 440
layout(location=0) in vec2 qt_TexCoord0;
layout(location=0) out vec4 fragColor;
layout(std140,binding=0) uniform buf {
    mat4 qt_Matrix; float qt_Opacity; float phase;
    vec4 base; vec4 blue; vec4 purple; vec4 teal; vec4 warm; vec4 pink; float dark;
    float preset;
    float aspect;
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
            // Silk: quiet indigo sheets converging below the lower-left corner.
            vec3 body=mix(vec3(.52,.62,.76),vec3(.065,.074,.13),dark);
            vec3 light=mix(vec3(.96,.98,1.0),vec3(.28,.31,.47),dark);
            c=mix(vec3(.85,.90,.96),vec3(.045,.048,.085),dark);
            float bend=.40*sin(q.y*3.14159);
            c=fold(c,q.x-((1.0-q.y)*.22+bend),body,light,.30);
            c=fold(c,q.x-((1.0-q.y)*.83+bend),body*.84,light*.88,.24);
            c=fold(c,q.x-((1.0-q.y)*1.55+bend),body*.94,light,.27);
        }else if(preset<2.5){
            // Aurora: a sculpted luminous veil, with a quiet corner behind the heading.
            c=mix(mix(vec3(.86,.94,.96),vec3(.96,.98,.96),q.y),
                  mix(vec3(.012,.035,.075),vec3(.018,.055,.09),q.y),dark);
            float sweep=q.x-.32-.74*q.y+.28*q.y*q.y+.10*sin(q.y*3.6+.2);
            float veil=smoothstep(-.46,-.12,sweep)*(1.0-smoothstep(.28,.64,sweep));
            vec3 mint=mix(vec3(.64,.83,.88),vec3(.025,.14,.21),dark);
            vec3 azure=mix(vec3(.62,.76,.94),vec3(.05,.29,.42),dark);
            vec3 rim=mix(vec3(.94,1.0,.98),vec3(.14,.52,.56),dark);
            c=mix(c,mint,veil*.88);
            c=mix(c,azure,exp(-pow((sweep-.08)/.20,2.0))*.52);
            c=mix(c,rim,exp(-pow((sweep+.17)/.045,2.0))*.37);
            c=mix(c,mix(vec3(1.0,.91,.84),vec3(.18,.10,.13),dark),
                  exp(-pow((sweep-.52)/.14,2.0))*.18*smoothstep(.25,.95,q.y));
        }else{
            // Contour: broad frosted material, with gentle depth rather than graphic rings.
            c=mix(mix(vec3(.91,.94,.95),vec3(.80,.86,.89),q.y),
                  mix(vec3(.025,.035,.055),vec3(.045,.07,.09),q.y),dark);
            float bend=.20+.47*q.y+.13*sin(q.y*3.3-.25);
            float seam=q.x-bend;
            float face=smoothstep(-.012,.020,seam);
            vec3 body=mix(vec3(.76,.83,.86),vec3(.045,.075,.10),dark);
            vec3 pearl=mix(vec3(.98,.99,.98),vec3(.20,.29,.33),dark);
            c*=1.0-.12*exp(-abs(seam)/.035)*(1.0-face);
            vec3 frost=mix(body,pearl,exp(-max(seam,0.0)/.20)*.74);
            c=mix(c,frost,face*.88);
            c+=pearl*exp(-pow(seam/.018,2.0))*.028;
            float lower=q.y-(.84-.12*q.x+.025*sin(q.x*min(aspect,1.8)*3.0));
            c=mix(c,mix(vec3(.80,.85,.84),vec3(.055,.09,.105),dark),
                  smoothstep(-.035,.15,lower)*.48);
        }
        // Static sub-pixel dither prevents banding without visible texture or temporal noise.
        float noise=fract(sin(dot(floor(p*vec2(1200,800)),vec2(12.9898,78.233)))*43758.5453)-.5;
        c+=noise/255.0;
    }
    c*=1.0-.16*dark*blob(vec2(p.x,p.y*2.5),vec2(.5,2.35),.52);
    fragColor=vec4(c,1.0)*qt_Opacity;
}
