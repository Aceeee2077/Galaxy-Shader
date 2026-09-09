#include "/lib/common.glsl"
#include "/lib/tonemap.glsl"
#include "/lib/camera_effects.glsl"
uniform sampler2D colortex5;
varying vec2 texcoord;
/* DRAWBUFFERS:0 */
void main() {
    vec3 hdr=cameraEffects(texcoord);
#if BLOOM_QUALITY > 0
    hdr+=texture2D(colortex5,texcoord).rgb*(0.035*float(BLOOM_QUALITY));
#endif
    gl_FragData[0]=vec4(gradeColor(hdr),1.0);
}
