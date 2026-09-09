#include "/lib/common.glsl"
#include "/lib/bloom.glsl"
uniform sampler2D colortex5;
varying vec2 texcoord;
/* DRAWBUFFERS:6 */
void main() {
    gl_FragData[0]=vec4(gaussianBlur(colortex5,texcoord,vec2(pixelSize().x*4.0,0.0)),1.0);
}
