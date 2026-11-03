#include "/lib/common.glsl"
#include "/lib/bloom.glsl"
uniform sampler2D colortex0;
varying vec2 texcoord;
/* DRAWBUFFERS:5 */
void main() {
    vec3 bright=vec3(0.0);
#if BLOOM_QUALITY > 0
    // A zero strength removes bloom from the final image entirely, so the
    // sixteen-tap bright pass has nothing to contribute. The constant folds
    // away at compile time for the low-end profile.
    if (BLOOM_STRENGTH > 0.0) {
        for(int y=0;y<4;++y) for(int x=0;x<4;++x) {
            vec2 uv=texcoord+(vec2(x,y)-1.5)*pixelSize();
            bright+=brightPass(texture2D(colortex0,uv).rgb);
        }
        bright/=16.0;
    }
#endif
    gl_FragData[0]=vec4(bright,1.0);
}
