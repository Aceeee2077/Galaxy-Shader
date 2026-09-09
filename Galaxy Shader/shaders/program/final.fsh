#include "/lib/common.glsl"
uniform sampler2D colortex0;
varying vec2 texcoord;
void main() {
    vec2 uv=texcoord, px=pixelSize();
    vec3 center=texture2D(colortex0,uv).rgb;
#if AA_QUALITY == 1
    vec3 nw=texture2D(colortex0,uv+px*vec2(-1,-1)).rgb;
    vec3 ne=texture2D(colortex0,uv+px*vec2(1,-1)).rgb;
    vec3 sw=texture2D(colortex0,uv+px*vec2(-1,1)).rgb;
    vec3 se=texture2D(colortex0,uv+px*vec2(1,1)).rgb;
    float lNW=luminance(nw), lNE=luminance(ne), lSW=luminance(sw), lSE=luminance(se), lC=luminance(center);
    float lo=min(lC,min(min(lNW,lNE),min(lSW,lSE))), hi=max(lC,max(max(lNW,lNE),max(lSW,lSE)));
    if(hi-lo>max(0.035,hi*0.10)) {
        vec2 dir=vec2(-((lNW+lNE)-(lSW+lSE)),(lNW+lSW)-(lNE+lSE));
        float reduce=max((lNW+lNE+lSW+lSE)*0.03125,0.0078125);
        dir=clamp(dir/(min(abs(dir.x),abs(dir.y))+reduce),-8.0,8.0)*px;
        vec3 a=0.5*(texture2D(colortex0,uv-dir/6.0).rgb+texture2D(colortex0,uv+dir/6.0).rgb);
        vec3 b=a*0.5+0.25*(texture2D(colortex0,uv-dir*0.5).rgb+texture2D(colortex0,uv+dir*0.5).rgb);
        float lb=luminance(b);
        center=lb<lo || lb>hi ? a : b;
    }
#endif
    gl_FragColor=vec4(center,1.0);
}
