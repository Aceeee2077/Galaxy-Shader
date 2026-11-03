#include "/lib/common.glsl"
#include "/lib/bloom.glsl"
uniform sampler2D colortex6;
varying vec2 texcoord;
/* DRAWBUFFERS:5 */
void main() {
    vec3 bloom=vec3(0.0);
#if BLOOM_QUALITY > 0
    // Same early-out as the horizontal pass: a zero strength means the result is
    // multiplied away in composite4, so the blur taps are pure waste.
    if (BLOOM_STRENGTH > 0.0)
        bloom=gaussianBlur(colortex6,texcoord,vec2(0.0,pixelSize().y*4.0));
#endif
    gl_FragData[0]=vec4(bloom,1.0);
}
