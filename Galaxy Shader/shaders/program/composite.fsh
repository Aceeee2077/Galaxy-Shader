#include "/lib/common.glsl"
#include "/lib/clouds.glsl"
#include "/lib/fog.glsl"
#include "/lib/volumetrics.glsl"
uniform sampler2D colortex0, colortex3, depthtex0;
varying vec2 texcoord;
/* DRAWBUFFERS:0 */
void main() {
    float d=texture2D(depthtex0,texcoord).r;
    bool sky=skyDepth(d)>0.5;
    vec3 player=playerPosition(viewPosition(texcoord,d));
    if(sky) player=safeNormalize(player)*far;
    vec3 color=texture2D(colortex0,texcoord).rgb;
    float hand=texture2D(colortex3,texcoord).b;
    if(hand<0.5) {
        // The procedural sky already includes its atmospheric path.
        if(!sky || isEyeInWater!=0) color=applyFog(color,player,sky);
        color+=volumetricLight(player);
    }
    gl_FragData[0]=vec4(max(color,vec3(0.0)),1.0);
}
