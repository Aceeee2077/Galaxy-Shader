#include "/lib/common.glsl"
#include "/lib/bloom.glsl"
uniform sampler2D colortex6;
varying vec2 texcoord;
/* DRAWBUFFERS:5 */
void main() {
    gl_FragData[0]=vec4(gaussianBlur(colortex6,texcoord,vec2(0.0,pixelSize().y*4.0)),1.0);
}
