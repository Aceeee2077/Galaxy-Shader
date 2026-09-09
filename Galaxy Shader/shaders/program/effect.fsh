#include "/lib/common.glsl"
uniform sampler2D texture;
varying vec2 vTex, vLight;
varying vec4 vColor;
varying vec3 vPlayer, vNormal, vTangent, vBitangent;
varying float vId;
/* DRAWBUFFERS:0 */
void main() {
    vec4 c=texture2D(texture,vTex)*vColor;
#ifdef BASIC
    c=vColor;
#endif
    if(c.a<0.001) discard;
    gl_FragData[0]=vec4(toLinear(c.rgb)*1.4,c.a);
}
