uniform sampler2D colortex0, colortex3, colortex5, colortex7, depthtex0;
#include "/lib/common.glsl"
#include "/lib/tonemap.glsl"
#include "/lib/camera_effects.glsl"
#include "/lib/taa.glsl"
varying vec2 texcoord;
/* DRAWBUFFERS:07 */
void main() {
    vec4 temporal=resolveTemporal(texcoord);
    vec3 hdr=cameraEffects(texcoord,temporal.rgb);
#if BLOOM_QUALITY > 0
    hdr+=texture2D(colortex5,texcoord).rgb*(0.035*float(BLOOM_QUALITY));
#endif
    gl_FragData[0]=vec4(gradeColor(hdr),1.0);
    gl_FragData[1]=temporal;
}
