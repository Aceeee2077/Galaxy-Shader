#include "/lib/common.glsl"
#include "/lib/bloom.glsl"
uniform sampler2D colortex5;
varying vec2 texcoord;
/* DRAWBUFFERS:6 */
void main() {
    vec3 bloom=vec3(0.0);
#if BLOOM_QUALITY > 0
    // With bloom switched off by strength there is nothing to blur; skip the
    // five-tap horizontal pass instead of writing zeros over it.
    if (BLOOM_STRENGTH > 0.0)
        bloom=gaussianBlur(colortex5,texcoord,vec2(pixelSize().x*4.0,0.0));
#endif
    gl_FragData[0]=vec4(bloom,1.0);
}
